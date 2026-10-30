"""Virtualized variable-height messages and keyboard-first composer."""

import re
from collections import OrderedDict
from datetime import datetime
from html import escape
from math import ceil
from urllib.parse import urlsplit

from PySide6.QtCore import (
    QAbstractListModel,
    QEasingCurve,
    QEvent,
    QPersistentModelIndex,
    QPoint,
    QPointF,
    QRectF,
    QSize,
    Qt,
    QTimer,
    QVariantAnimation,
    Signal,
)
from PySide6.QtGui import (
    QAbstractTextDocumentLayout,
    QColor,
    QFont,
    QFontMetrics,
    QIcon,
    QKeySequence,
    QPainter,
    QPainterPath,
    QPalette,
    QTextBlockFormat,
    QTextCursor,
    QTextDocument,
)
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QListView,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QStyle,
    QStyledItemDelegate,
    QVBoxLayout,
    QWidget,
)

from aedrova.desktop.attachment_previews import preview_height
from aedrova.desktop.controls import AppMenu
from aedrova.desktop.emojis import QUICK_EMOJI, pick_emoji
from aedrova.desktop.materials import SpringButton, system_font
from aedrova.desktop.theme import LIGHT, Theme

MESSAGE_ROLE = Qt.ItemDataRole.UserRole + 1


def font(size=13, bold=False):
    result = system_font(size)
    result.setWeight(QFont.Weight.DemiBold if bold else QFont.Weight.Normal)
    return result


class ConversationModel(QAbstractListModel):
    def __init__(self, messages=None, parent=None, *, allow_threads=True):
        super().__init__(parent)
        self.messages = list(messages or [])
        self.allow_threads = allow_threads

    def rowCount(self, parent=None):  # noqa: N802
        return 0 if parent is not None and parent.isValid() else len(self.messages)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self.messages):
            return None
        message = self.messages[index.row()]
        if role == MESSAGE_ROLE:
            return message
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.AccessibleTextRole):
            decision = "Confirmed decision. " if message.decision else ""
            view = self.parent()
            body = view.display_body(message) if hasattr(view, "display_body") else message.body
            return (
                f"{message.author}, {message.time}. {decision}{body}. "
                f"{message.attachment} {len(message.replies)} replies."
            )
        if role == Qt.ItemDataRole.AccessibleDescriptionRole:
            return (
                "Press Return to open the thread, or use the context menu to copy the message."
                if self.allow_threads
                else "Use the context menu to copy the message."
            )
        return None

    def replace(self, messages):
        self.beginResetModel()
        self.messages = list(messages)
        self.endResetModel()

    def append(self, message):
        row = len(self.messages)
        self.beginInsertRows(self.index(-1, -1), row, row)
        self.messages.append(message)
        self.endInsertRows()

    def refresh(self, message_id):
        for row, message in enumerate(self.messages):
            if message.id == message_id:
                index = self.index(row)
                self.dataChanged.emit(index, self.index(min(row + 1, len(self.messages) - 1)), [])
                break


def reaction_chips(message, width, top):
    x, y = 74, top
    result = []
    for reaction in message.reactions:
        text = f"{reaction['emoji']} {reaction['count']}"
        size = max(52, QFontMetrics(font(12)).horizontalAdvance(text) + 22)
        if x + size > width - 20 and x > 74:
            x, y = 74, y + 34
        result.append((QRectF(x, y, size, 28), reaction, text))
        x += size + 6
    return result


def message_urls(body):
    return list(dict.fromkeys(re.findall(r"https?://[^\s<>\)]+", body)))[:3]


class SafeDocument(QTextDocument):
    def loadResource(self, resource_type, url):
        # Markdown must never fetch external images or read local files.
        return None


def markdown_document(text):
    document = SafeDocument()
    document.setMarkdown(text, QTextDocument.MarkdownFeature.MarkdownNoHTML)
    return document


def markdown_html(text):
    document = markdown_document(text)
    # QTextDocument can retain image tags in its HTML export even when loading
    # the resource was refused. Strip them before handing the result to QLabel.
    return re.sub(r"<img\b[^>]*>", "", document.toHtml(), flags=re.IGNORECASE)


class MessageDelegate(QStyledItemDelegate):
    def __init__(self, view):
        super().__init__(view)
        self.view = view
        self.theme = LIGHT
        self.documents = OrderedDict()

    def document(self, message, width):
        width = max(80, min(880, width))
        display = self.view.display_body(message)
        hint = self.view.translation_hint(message)
        key = (message.id, display, hint, width, self.theme.name)
        if key not in self.documents:
            document = SafeDocument()
            document.setDefaultFont(font(14))
            document.setDefaultStyleSheet(
                "a { color: " + self.theme.accent + "; } pre { white-space: pre-wrap; }"
            )
            document.setDocumentMargin(0)
            text = re.sub(
                r"<@(?:dot:|ai:)?([a-f0-9-]{36})\|([^>\n]{1,80})>",
                lambda m: "@" + m[2],
                display,
            )
            voice_only = message.attachment.lower().endswith(".wav") and message.body.startswith(
                "Shared a file:"
            )
            if voice_only:
                text = ""
                hint = ""
            if hint:
                text += "\n\n_" + hint + "_"
            document.setMarkdown(text, QTextDocument.MarkdownFeature.MarkdownNoHTML)
            previews = ""
            for url in message_urls(message.body):
                parsed = urlsplit(url)
                if parsed.hostname:
                    title = parsed.hostname + (parsed.path[:70] if parsed.path != "/" else "")
                    previews += (
                        '<p style="margin-top:12px;">↗ <a href="'
                        + escape(url, quote=True)
                        + '">'
                        + escape(title)
                        + "</a><br><small>Link preview</small></p>"
                    )
            if previews:
                preview_cursor = QTextCursor(document)
                preview_cursor.movePosition(QTextCursor.MoveOperation.End)
                preview_cursor.insertHtml(previews)
            block = document.begin()
            anchor_ranges = []
            while block.isValid():
                cursor = QTextCursor(block)
                block_format = block.blockFormat()
                block_format.setLineHeight(
                    135, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value
                )
                block_format.setTopMargin(1)
                block_format.setBottomMargin(2)
                block_format.setNonBreakableLines(False)
                cursor.setBlockFormat(block_format)
                fragments = block.begin()
                while not fragments.atEnd():
                    fragment = fragments.fragment()
                    if fragment.isValid() and fragment.charFormat().isAnchor():
                        anchor_ranges.append((fragment.position(), fragment.length()))
                    fragments += 1
                block = block.next()
            for start, length in anchor_ranges:
                cursor = QTextCursor(document)
                cursor.setPosition(start)
                cursor.setPosition(start + length, QTextCursor.MoveMode.KeepAnchor)
                style = cursor.charFormat()
                style.setForeground(QColor(self.theme.accent))
                cursor.mergeCharFormat(style)
            document.setTextWidth(width)
            self.documents[key] = document
            if len(self.documents) > 512:
                self.documents.popitem(last=False)
        self.documents.move_to_end(key)
        return self.documents[key]

    def grouped(self, index):
        """Group nearby messages by actual sender, without merging their data or actions."""
        if index.row() == 0:
            return False
        message = index.data(MESSAGE_ROLE)
        previous = index.model().index(index.row() - 1, 0).data(MESSAGE_ROLE)
        if (
            not previous
            or message.unsent
            or previous.unsent
            or message.decision
            or (message.delivery and message.delivery not in {"Sending…", "Retrying…"})
            or message.edited
            or message.saved
            or message.pinned
        ):
            return False
        if message.id == getattr(self.view, "agent_message_id", None) or previous.id == getattr(
            self.view, "agent_message_id", None
        ):
            return False
        if (message.sender_id or message.author) != (previous.sender_id or previous.author):
            return False
        for pattern in ("%Y-%m-%d %H:%M", "%H:%M", "%I:%M %p"):
            try:
                delta = (
                    datetime.strptime(message.time, pattern)
                    - datetime.strptime(previous.time, pattern)
                ).total_seconds()
                return 0 <= delta <= 300
            except ValueError:
                continue
        return False

    def body_offset(self, index):
        return 5 if self.grouped(index) else 14 + QFontMetrics(font(14, True)).height() + 6

    def sizeHint(self, option, index):  # noqa: N802
        message = index.data(MESSAGE_ROLE)
        width = self.view.viewport().width()
        if message.id == getattr(self.view, "agent_message_id", None):
            return QSize(width, self.view.agent_feed.content_height(width))
        document = self.document(message, width - 94)
        extra = (preview_height(message.attachment) if message.attachment else 0) + (
            26 if message.replies and self.view.allow_threads else 0
        )
        chips = reaction_chips(message, width, 0)
        reaction_height = int(chips[-1][0].bottom()) + 8 if chips else 0
        return QSize(
            width,
            self.body_offset(index) + ceil(document.size().height()) + extra + 10 + reaction_height,
        )

    def paint(self, painter: QPainter, option, index):
        message = index.data(MESSAGE_ROLE)
        if message.id == getattr(self.view, "agent_message_id", None):
            return
        t = self.theme
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = option.rect
        painter.setClipRect(rect)
        animation = self.view.send_animations.get(message.id)
        if animation is not None:
            progress = float(animation.currentValue() or 0)
            scale = 0.96 + 0.04 * progress
            origin = QRectF(rect).bottomRight()
            painter.translate(origin.x(), origin.y() + 12 * (1 - progress))
            painter.scale(scale, scale)
            painter.translate(-origin.x(), -origin.y())
            painter.setOpacity(0.4 + 0.6 * progress)
        selected = option.state & QStyle.StateFlag.State_Selected
        hovered = option.state & QStyle.StateFlag.State_MouseOver
        if (selected or hovered) and t.name == "light":
            painter.fillRect(rect, QColor(t.surface))
        if selected and t.name == "dark":
            painter.fillRect(
                QRectF(rect.x() + 8, rect.y() + 12, 2, rect.height() - 24), QColor(t.accent)
            )
        if selected and option.state & QStyle.StateFlag.State_HasFocus:
            painter.setPen(QColor(t.accent))
            focus = QRectF(rect).adjusted(3, 1, -3, -1)
            if t.name == "dark":
                focus = QRectF(rect).adjusted(20, 3, -20, -3)
                focus.setWidth(min(focus.width(), 920))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(focus, 7, 7)
        grouped = self.grouped(index)
        x, y = rect.x() + 74, rect.y() + self.body_offset(index)
        if grouped and hovered:
            painter.setPen(QColor(t.secondary))
            painter.setFont(font(9))
            painter.drawText(
                QRectF(rect.x() + 10, rect.y() + 5, 54, 18),
                Qt.AlignmentFlag.AlignCenter,
                message.time[-5:],
            )
        if not grouped:
            x, y = rect.x() + 28, rect.y() + 14
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(t.avatars[message.tone % len(t.avatars)]))
            painter.drawRoundedRect(QRectF(x, y, 34, 34), 12, 12)
            painter.setPen(QColor(t.text))
            painter.setFont(font(11, True))
            painter.drawText(QRectF(x, y, 34, 34), Qt.AlignmentFlag.AlignCenter, message.initials)
            if message.agent:
                from aedrova.desktop.brand import brand_image

                painter.drawImage(QRectF(x, y, 34, 34), brand_image())
            photo = getattr(self.view, "avatar_images", {}).get(
                getattr(self.view, "avatar_paths", {}).get(message.sender_id)
            )
            if photo is not None and not photo.isNull():
                painter.save()
                clip = QPainterPath()
                clip.addRoundedRect(QRectF(x, y, 34, 34), 12, 12)
                painter.setClipPath(clip)
                painter.drawPixmap(int(x), int(y), 34, 34, photo)
                painter.restore()
            x += 46
            header_height = QFontMetrics(font(14, True)).height() + 6
            available = max(0, rect.width() - 94)
            badge_width = 76 if message.decision else 0
            delivery = message.delivery
            timestamp = delivery or (
                message.time
                + (" · edited" if message.edited else "")
                + (" · pinned" if message.pinned else "")
                + (" · saved" if message.saved else "")
            )
            time_metrics = QFontMetrics(font(11))
            time_width = min(
                time_metrics.horizontalAdvance(timestamp) + 2,
                max(0, int((available - badge_width) * 0.65)),
            )
            name_width = max(
                0,
                min(
                    QFontMetrics(font(14, True)).horizontalAdvance(
                        message.author + (" · AI" if message.agent else "")
                    )
                    + 4,
                    available - time_width - badge_width - 12,
                ),
            )
            line_flags = Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextSingleLine
            painter.setFont(font(14, True))
            painter.drawText(
                QRectF(x, y, name_width, header_height - 6),
                line_flags,
                painter.fontMetrics().elidedText(
                    message.author + (" · AI" if message.agent else ""),
                    Qt.TextElideMode.ElideRight,
                    int(name_width),
                ),
            )
            painter.setFont(font(11))
            painter.setPen(QColor(t.secondary))
            painter.drawText(
                QRectF(x + name_width + 12, y, time_width, header_height - 6),
                line_flags,
                time_metrics.elidedText(timestamp, Qt.TextElideMode.ElideRight, int(time_width)),
            )
            if message.decision:
                bx = x + name_width + time_width + 20
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(t.surface))
                painter.drawRoundedRect(QRectF(bx, y, 66, header_height - 6), 8, 8)
                painter.setPen(QColor(t.muted))
                painter.setFont(font(9, True))
                painter.drawText(
                    QRectF(bx, y, 66, header_height - 6),
                    Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextSingleLine,
                    "DECISION",
                )
        document = self.document(message, rect.width() - 94)
        painter.save()
        painter.translate(rect.x() + 74, rect.y() + self.body_offset(index))
        self.view.paint_text_selection(painter, message, document)
        context = QAbstractTextDocumentLayout.PaintContext()
        context.palette.setColor(
            QPalette.ColorRole.Text, QColor(t.text if t.name == "dark" else t.secondary)
        )
        document.documentLayout().draw(painter, context)
        painter.restore()
        x = rect.x() + 74
        bottom = rect.y() + self.body_offset(index) + document.size().height()
        if message.attachment:
            voice = message.attachment.lower().endswith(".wav")
            playback = getattr(self.view, "voice_playback", {})
            active = playback.get("id") == message.attachment_id
            painter.setPen(QColor(t.border))
            painter.setBrush(QColor(t.surface))
            card_width = min(350, rect.width() - 96)
            height = preview_height(message.attachment)
            painter.drawRoundedRect(QRectF(x, bottom + 10, card_width, height - 14), 12, 12)
            painter.setPen(QColor(t.accent))
            painter.setFont(font(10, True))
            painter.drawText(
                QRectF(x + 12, bottom + 23, 30, 18),
                ("Ⅱ" if active and playback.get("playing") else "▶") if voice else "FILE",
            )
            painter.setFont(font(11))
            painter.setPen(QColor(t.secondary))
            elided = painter.fontMetrics().elidedText(
                (
                    (
                        f"{playback.get('position', 0) // 1000}s / "
                        f"{playback.get('duration', 0) // 1000}s"
                        if active
                        else "Play"
                    )
                    if voice
                    else message.attachment
                ),
                Qt.TextElideMode.ElideRight,
                int(card_width - 60),
            )
            painter.drawText(QRectF(x + 48, bottom + 23, card_width - 55, 18), elided)
            if height > 58:
                preview = getattr(self.view, "attachment_previews", {}).get(message.attachment_id)
                area = QRectF(x + 12, bottom + 48, card_width - 24, height - 58)
                from PySide6.QtGui import QPixmap

                if isinstance(preview, QPixmap):
                    scaled = preview.scaled(
                        area.size().toSize(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                    # A neutral matte makes transparent dark artwork legible without
                    # recoloring the user's image or changing its pixels.
                    painter.fillRect(
                        QRectF(
                            area.x(),
                            area.y() + (area.height() - scaled.height()) / 2,
                            scaled.width(),
                            scaled.height(),
                        ),
                        QColor(t.preview),
                    )
                    painter.drawPixmap(
                        int(area.x()), int(area.y() + (area.height() - scaled.height()) / 2), scaled
                    )
                else:
                    if preview is None:
                        placeholder = QColor(t.secondary)
                        placeholder.setAlpha(30)
                        painter.setPen(Qt.PenStyle.NoPen)
                        painter.setBrush(placeholder)
                        for line, fraction in enumerate((0.88, 0.7, 0.48)):
                            painter.drawRoundedRect(
                                QRectF(area.x(), area.y() + line * 16, area.width() * fraction, 7),
                                3,
                                3,
                            )
                    else:
                        painter.setFont(font(10))
                        painter.drawText(area, Qt.TextFlag.TextWordWrap, preview)
            bottom += height
        if message.replies and self.view.allow_threads:
            painter.setFont(font(11, True))
            painter.setPen(QColor(t.accent))
            count = len(message.replies)
            painter.drawText(
                QRectF(x, bottom + 7, rect.width() - 94, 20),
                f"{count} {'reply' if count == 1 else 'replies'}  →  Open thread",
            )
        if message.reactions:
            chip_top = bottom + (30 if message.replies and self.view.allow_threads else 8)
            for box, reaction, text in reaction_chips(message, rect.width(), chip_top):
                box.translate(rect.x(), 0)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(t.accent_bg if reaction.get("mine") else t.surface))
                painter.drawRoundedRect(box, 12, 12)
                painter.setPen(QColor(t.accent_text if reaction.get("mine") else t.secondary))
                painter.setFont(font(12))
                painter.drawText(box, Qt.AlignmentFlag.AlignCenter, text)
        painter.restore()


class MessageView(QListView):
    thread_requested = Signal(str)
    reaction_requested = Signal(str, str, bool)
    unsend_requested = Signal(str)
    action_requested = Signal(str, str)
    files_dropped = Signal(list)
    link_requested = Signal(str)

    def __init__(self, parent=None, *, allow_threads=True):
        super().__init__(parent)
        self._scroll_target = None
        self._wheel_remainder = 0.0
        self._scroll_hint = QListView.ScrollHint.EnsureVisible
        self._scroll_timer = QTimer(self)
        self._scroll_timer.setSingleShot(True)
        self._scroll_timer.timeout.connect(self._finish_scroll)
        self.verticalScrollBar().rangeChanged.connect(lambda *_: self._scroll_timer.start(0))
        self.agent_feed = None
        self.agent_message_id = None
        self.agent_visible = False
        self.agent_anchor = None
        self.source_messages = []
        self.text_selection = None  # message ID, UTF-16 anchor, UTF-16 position
        self.selecting_text = False
        self.allow_threads = allow_threads
        self.setObjectName("Messages")
        self.setAccessibleName("Conversation messages")
        self.setAccessibleDescription(
            "Use arrow keys to select a message and Return to open its thread."
        )
        self.setMouseTracking(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QListView.DragDropMode.DropOnly)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollMode(QListView.ScrollMode.ScrollPerPixel)
        self.verticalScrollBar().setSingleStep(16)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setLayoutMode(QListView.LayoutMode.Batched)
        self.setBatchSize(100)
        self.send_animations = {}
        self.conversation_model = ConversationModel(parent=self, allow_threads=allow_threads)
        self.setModel(self.conversation_model)
        self.delegate = MessageDelegate(self)
        self.setItemDelegate(self.delegate)
        self.clicked.connect(self._clicked_message)
        self.reaction_bar = QFrame(self.viewport())
        self.reaction_bar.setObjectName("ReactionBar")
        bar = QHBoxLayout(self.reaction_bar)
        bar.setContentsMargins(6, 4, 6, 4)
        bar.setSpacing(2)
        self.hover_message = None
        for emoji in QUICK_EMOJI:
            control = SpringButton(emoji)
            control.setFixedSize(32, 32)
            control.setAccessibleName("React " + emoji)
            control.clicked.connect(
                lambda checked=False, e=emoji: self.react(self.hover_message, e)
            )
            bar.addWidget(control)
        more = SpringButton("+")
        more.setFixedSize(32, 32)
        more.setAccessibleName("React with any emoji")
        more.setToolTip("Choose any emoji")
        more.clicked.connect(self.pick_reaction)
        bar.addWidget(more)
        self.reaction_bar.hide()
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and all(u.isLocalFile() for u in event.mimeData().urls()):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        self.dragEnterEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
            if paths:
                self.files_dropped.emit(paths)
                event.acceptProposedAction()

    def text_hit(self, point, *, clamp=False):
        index = self.indexAt(point)
        if not index.isValid() or index.data(MESSAGE_ROLE).id == self.agent_message_id:
            return None
        rect = self.visualRect(index)
        document = self.delegate.document(index.data(MESSAGE_ROLE), rect.width() - 94)
        local = QPointF(
            point.x() - rect.x() - 74, point.y() - rect.top() - self.delegate.body_offset(index)
        )
        if not clamp and not QRectF(0, 0, document.textWidth(), document.size().height()).contains(
            local
        ):
            return None
        position = document.documentLayout().hitTest(local, Qt.HitTestAccuracy.FuzzyHit)
        return index, document, max(0, min(position, document.characterCount() - 1))

    def mousePressEvent(self, event):  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton:
            hit = self.text_hit(event.position().toPoint())
            self.selecting_text = hit is not None
            if hit:
                index, _, position = hit
                anchor = (
                    self.text_selection[1]
                    if self.text_selection
                    and self.text_selection[0] == index.data(MESSAGE_ROLE).id
                    and event.modifiers() & Qt.KeyboardModifier.ShiftModifier
                    else position
                )
                self.text_selection = (index.data(MESSAGE_ROLE).id, anchor, position)
            else:
                self.text_selection = None
            self.viewport().update()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):  # noqa: N802
        hit = self.text_hit(event.position().toPoint())
        if hit and event.button() == Qt.MouseButton.LeftButton:
            index, document, position = hit
            cursor = QTextCursor(document)
            cursor.setPosition(position)
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
            self.text_selection = (index.data(MESSAGE_ROLE).id, cursor.anchor(), cursor.position())
            self.selecting_text = True
            self.viewport().update()
            event.accept()
            return
        super().mouseDoubleClickEvent(event)

    def selection_cursor(self):
        if not self.text_selection:
            return None
        identifier, anchor, position = self.text_selection
        for row, message in enumerate(self.model().messages):
            if message.id == identifier:
                index = self.model().index(row)
                document = self.delegate.document(message, self.visualRect(index).width() - 94)
                cursor = QTextCursor(document)
                cursor.setPosition(min(anchor, document.characterCount() - 1))
                cursor.setPosition(
                    min(position, document.characterCount() - 1), QTextCursor.MoveMode.KeepAnchor
                )
                return cursor
        self.text_selection = None
        return None

    def paint_text_selection(self, painter, message, document):
        if not self.text_selection or self.text_selection[0] != message.id:
            return
        start, end = sorted(self.text_selection[1:])
        if start == end:
            return
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(self.delegate.theme.accent_bg))
        block = document.findBlock(start)
        while block.isValid() and block.position() < end:
            bounds = document.documentLayout().blockBoundingRect(block)
            layout = block.layout()
            for n in range(layout.lineCount()):
                line = layout.lineAt(n)
                first = max(start - block.position(), line.textStart())
                last = min(end - block.position(), line.textStart() + line.textLength())
                if first >= last:
                    continue
                x1, x2 = line.cursorToX(first)[0], line.cursorToX(last)[0]
                painter.drawRoundedRect(
                    QRectF(
                        bounds.x() + min(x1, x2) - 2,
                        bounds.y() + line.y() - 1,
                        abs(x2 - x1) + 4,
                        line.height() + 2,
                    ),
                    3,
                    3,
                )
            block = block.next()

    def mouseReleaseEvent(self, event):  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and self.selecting_text:
            self.selecting_text = False
            cursor = self.selection_cursor()
            if cursor and cursor.hasSelection():
                event.accept()
                return
            # Links keep their normal single-click behavior; ordinary body clicks
            # place a text caret instead of unexpectedly opening a thread.
            hit = self.text_hit(event.position().toPoint())
            if hit:
                index, document, _ = hit
                rect = self.visualRect(index)
                link = document.documentLayout().anchorAt(
                    QPointF(
                        event.position().x() - rect.x() - 74,
                        event.position().y() - rect.y() - self.delegate.body_offset(index),
                    )
                )
                if link and urlsplit(link).scheme in ("https", "http"):
                    self.link_requested.emit(link)
            event.accept()
            return
        self._click_position = event.position().toPoint()
        super().mouseReleaseEvent(event)

    def _clicked_message(self, index):
        if not index.isValid():
            return
        message = index.data(MESSAGE_ROLE)
        rect = self.visualRect(index)
        document = self.delegate.document(message, rect.width() - 94)
        top = rect.top() + self.delegate.body_offset(index)
        top += document.size().height() + (
            preview_height(message.attachment) if message.attachment else 0
        )
        top += 30 if message.replies and self.allow_threads else 8
        point = getattr(self, "_click_position", QPoint(-1, -1))
        for box, reaction, _ in reaction_chips(message, rect.width(), top):
            if box.contains(point):
                self.react(message.id, reaction["emoji"])
                return
        body_top = rect.top() + self.delegate.body_offset(index)
        link = document.documentLayout().anchorAt(QPointF(point.x() - 74, point.y() - body_top))
        if link and urlsplit(link).scheme in ("https", "http"):
            self.link_requested.emit(link)
            return
        if (
            message.attachment_id
            and body_top + document.size().height()
            <= point.y()
            <= body_top + document.size().height() + preview_height(message.attachment)
        ):
            self.action_requested.emit("attachment", message.id)
            return
        self._request_thread(index)

    def react(self, identifier, emoji):
        message = next((m for m in self.model().messages if m.id == identifier), None)
        if not message or message.unsent or message.delivery or identifier == self.agent_message_id:
            return
        mine = next((r.get("mine", False) for r in message.reactions if r["emoji"] == emoji), False)
        self.reaction_requested.emit(identifier, emoji, not mine)

    def pick_reaction(self):
        identifier = self.hover_message
        self.reaction_bar.hide()
        emoji = pick_emoji(self)
        if emoji:
            self.react(identifier, emoji)

    def mouseMoveEvent(self, event):  # noqa: N802
        if (
            self.selecting_text
            and self.text_selection
            and event.buttons() & Qt.MouseButton.LeftButton
        ):
            hit = self.text_hit(event.position().toPoint(), clamp=True)
            if hit and hit[0].data(MESSAGE_ROLE).id == self.text_selection[0]:
                self.text_selection = (*self.text_selection[:2], hit[2])
                self.viewport().update()
            self.reaction_bar.hide()
            return
        super().mouseMoveEvent(event)
        index = self.indexAt(event.position().toPoint())
        if not index.isValid():
            self.reaction_bar.hide()
            return
        message = index.data(MESSAGE_ROLE)
        if message.unsent or message.delivery or message.id == self.agent_message_id:
            self.reaction_bar.hide()
            return
        self.hover_message = message.id
        self.reaction_bar.adjustSize()
        self.reaction_bar.move(
            max(0, self.viewport().width() - self.reaction_bar.width() - 16),
            max(0, self.visualRect(index).top() + 4),
        )
        self.reaction_bar.show()
        self.reaction_bar.raise_()

    def leaveEvent(self, event):  # noqa: N802
        if not self.reaction_bar.underMouse():
            self.reaction_bar.hide()
        super().leaveEvent(event)

    def _request_thread(self, index):
        if (
            self.allow_threads
            and index.isValid()
            and index.data(MESSAGE_ROLE).id != self.agent_message_id
        ):
            self.thread_requested.emit(index.data(MESSAGE_ROLE).id)

    def keyPressEvent(self, event):  # noqa: N802
        moves = {
            Qt.Key.Key_Left: QTextCursor.MoveOperation.PreviousCharacter,
            Qt.Key.Key_Right: QTextCursor.MoveOperation.NextCharacter,
            Qt.Key.Key_Up: QTextCursor.MoveOperation.Up,
            Qt.Key.Key_Down: QTextCursor.MoveOperation.Down,
            Qt.Key.Key_Home: QTextCursor.MoveOperation.StartOfLine,
            Qt.Key.Key_End: QTextCursor.MoveOperation.EndOfLine,
        }
        if (
            self.text_selection
            and event.key() in moves
            and (event.modifiers() & Qt.KeyboardModifier.ShiftModifier)
        ):
            cursor = self.selection_cursor()
            if cursor:
                cursor.movePosition(moves[event.key()], QTextCursor.MoveMode.KeepAnchor)
                self.text_selection = (self.text_selection[0], cursor.anchor(), cursor.position())
                self.viewport().update()
                event.accept()
                return
        if event.matches(QKeySequence.StandardKey.SelectAll) and self.currentIndex().isValid():
            index = self.currentIndex()
            document = self.delegate.document(
                index.data(MESSAGE_ROLE), self.visualRect(index).width() - 94
            )
            self.text_selection = (index.data(MESSAGE_ROLE).id, 0, document.characterCount() - 1)
            self.viewport().update()
            event.accept()
        elif event.key() == Qt.Key.Key_Escape and self.text_selection:
            self.text_selection = None
            self.viewport().update()
            event.accept()
        elif event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._request_thread(self.currentIndex())
            event.accept()
        elif event.matches(QKeySequence.StandardKey.Copy):
            self.copy_current()
            event.accept()
        else:
            if event.key() in moves:
                self.text_selection = None
                self.viewport().update()
            super().keyPressEvent(event)

    def copy_current(self):
        cursor = self.selection_cursor()
        if cursor and cursor.hasSelection():
            QApplication.clipboard().setText(cursor.selectedText().replace("\u2029", "\n"))
            return
        if self.currentIndex().isValid():
            QApplication.clipboard().setText(
                self.display_body(self.currentIndex().data(MESSAGE_ROLE))
            )

    def _context_menu(self, position):
        index = self.indexAt(position)
        if not index.isValid():
            return
        self.setCurrentIndex(index)
        if self.text_selection and self.text_selection[0] != index.data(MESSAGE_ROLE).id:
            self.text_selection = None
        menu = AppMenu(self)
        if (
            self.allow_threads
            and not index.data(MESSAGE_ROLE).delivery
            and index.data(MESSAGE_ROLE).id != self.agent_message_id
        ):
            menu.addAction("Reply in thread", lambda: self._request_thread(index))
        message = index.data(MESSAGE_ROLE)
        if message.mine and message.delivery == "Sending…" and message.id.startswith("upload-"):
            menu.addAction(
                "Cancel upload",
                lambda: self.action_requested.emit("cancel-local", message.id),
            )
        if message.mine and message.delivery and message.delivery not in {"Sending…", "Retrying…"}:
            menu.addAction(
                "Remove local message",
                lambda: self.action_requested.emit("dismiss-local", message.id),
            )
        if not message.unsent and not message.delivery and message.id != self.agent_message_id:
            reactions = AppMenu(menu)
            reactions.setTitle("React")
            for emoji in QUICK_EMOJI:
                reactions.addAction(emoji, lambda checked=False, e=emoji: self.react(message.id, e))
            reactions.addAction("+ Any emoji…", lambda: self._choose_for(message.id))
            menu.addMenu(reactions)
            if message_urls(message.body):
                menu.addAction(
                    "Preview link…", lambda: self.link_requested.emit(message_urls(message.body)[0])
                )
            menu.addSeparator()
            for action, title in [
                ("quote", "Quote message"),
                ("saved", "Remove from saved" if message.saved else "Save for later"),
                ("pinned", "Unpin message" if message.pinned else "Pin message"),
                ("forward", "Forward / share…"),
                ("link", "Copy link to message"),
                ("unread", "Mark unread"),
                ("profile", "View profile"),
            ]:
                menu.addAction(
                    title, lambda checked=False, a=action: self.action_requested.emit(a, message.id)
                )
            if message.attachment_id:
                menu.addAction(
                    "Play / pause voice message"
                    if message.attachment.lower().endswith(".wav")
                    else "Open attachment…",
                    lambda: self.action_requested.emit("attachment", message.id),
                )
            if message.mine:
                menu.addAction(
                    "Edit message…", lambda: self.action_requested.emit("edit", message.id)
                )
                menu.addAction(
                    "Delete / unsend message", lambda: self.unsend_requested.emit(message.id)
                )
        cursor = self.selection_cursor()
        if cursor and cursor.hasSelection():
            menu.addAction("Copy selection", self.copy_current)
        localizer = self.reader_localizer()
        if localizer and localizer.enabled:
            title = "Show translation" if message.id in localizer.originals else "Show original"
            menu.addAction(
                localizer.text(title, interface=True), lambda: self.toggle_original(message.id)
            )
            menu.addAction(
                localizer.text("Copy original", interface=True),
                lambda: QApplication.clipboard().setText(message.body),
            )
        menu.addAction(
            "Copy message", lambda: QApplication.clipboard().setText(self.display_body(message))
        )
        menu.exec(self.viewport().mapToGlobal(position))

    def _choose_for(self, identifier):
        emoji = pick_emoji(self)
        if emoji:
            self.react(identifier, emoji)

    def scrollTo(self, index, hint=QListView.ScrollHint.EnsureVisible):  # noqa: N802
        # Batched layout may not have reached this row yet. Retry when its range grows.
        self._scroll_target = QPersistentModelIndex(index)
        self._scroll_hint = hint
        super().scrollTo(index, hint)
        self._scroll_timer.start(0)

    def scrollToBottom(self):  # noqa: N802
        if self.model() is not None and self.model().rowCount():
            self.scrollTo(
                self.model().index(self.model().rowCount() - 1),
                QListView.ScrollHint.PositionAtBottom,
            )

    def _finish_scroll(self):
        if self._scroll_target is None:
            return
        if not self._scroll_target.isValid():
            self._scroll_target = None
            return
        index = self.model().index(self._scroll_target.row())
        super().scrollTo(index, self._scroll_hint)
        if (
            self._scroll_hint == QListView.ScrollHint.PositionAtBottom
            and self.visualRect(index).height() > self.viewport().height()
        ):
            self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
        if self.viewport().rect().intersects(self.visualRect(index)):
            self._scroll_target = None

    def wheelEvent(self, event):  # noqa: N802
        self._scroll_target = None
        # Variable-height messages make Qt's automatic wheel step enormous.
        # Keep native trackpad momentum/phases, with gentler pixel movement;
        # conventional wheels get a bounded 40 px step per notch.
        pixel, angle = event.pixelDelta(), event.angleDelta()
        if event.modifiers() & (
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier
        ):
            super().wheelEvent(event)
            return
        if abs(pixel.x()) > abs(pixel.y()) or (pixel.isNull() and abs(angle.x()) > abs(angle.y())):
            event.ignore()
            return
        delta = pixel.y() * 0.55 if not pixel.isNull() else angle.y() / 120 * 40
        if delta:
            if delta * self._wheel_remainder < 0:
                self._wheel_remainder = 0.0
            self._wheel_remainder += delta
            movement = int(self._wheel_remainder)
            self._wheel_remainder -= movement
            bar = self.verticalScrollBar()
            bar.setValue(bar.value() - movement)
            if bar.value() in (bar.minimum(), bar.maximum()):
                self._wheel_remainder = 0.0
            self.reaction_bar.hide()
            event.accept()
        elif event.phase() == Qt.ScrollPhase.ScrollEnd:
            self._wheel_remainder = 0.0
            event.accept()
        else:
            super().wheelEvent(event)

    def animate_sent(self, identifier):
        """A short, compositor-free message pop; reduced motion stays instantaneous."""
        if getattr(self.window(), "reduced_motion", False):
            return
        if identifier in self.send_animations:
            return
        animation = QVariantAnimation(self)
        animation.setDuration(260)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.valueChanged.connect(lambda _: self.viewport().update())
        self.send_animations[identifier] = animation

        def finished():
            self.send_animations.pop(identifier, None)
            animation.deleteLater()
            self.viewport().update()

        animation.finished.connect(finished)
        animation.start()

    def set_theme(self, theme: Theme):
        self.delegate.theme = theme
        self.viewport().update()

    def attach_agent_feed(self, feed):
        self.agent_feed = feed
        feed.make_inline()
        feed.changed.connect(self.refresh_agent)

    def set_agent_visible(self, visible):
        self.agent_visible = visible
        self.show_messages(self.source_messages)

    def refresh_agent(self):
        if not self.agent_feed.toPlainText():
            self.agent_message_id = None
            self.agent_anchor = None
            self.agent_visible = False
        elif not self.agent_message_id:
            from uuid import uuid4

            self.agent_message_id = "agent-" + str(uuid4())
            self.agent_anchor = self.source_messages[-1].id if self.source_messages else None
        self.show_messages(self.source_messages, force=True)

    def reader_localizer(self):
        node = self
        while node is not None:
            value = getattr(node, "localizer", None)
            if value is not None:
                return value
            node = node.parentWidget()
        return None

    def display_body(self, message):
        localizer = self.reader_localizer()
        if not localizer or message.id in localizer.originals or message.unsent:
            return message.body
        return localizer.text(message.body)

    def translation_hint(self, message):
        localizer = self.reader_localizer()
        if not localizer or not localizer.enabled or message.unsent:
            return ""
        from aedrova.localization import LANGUAGES

        translated = self.display_body(message)
        if translated != message.body:
            return (
                localizer.text("Translated", interface=True) + " · " + LANGUAGES[localizer.language]
            )
        if message.id in localizer.originals:
            return localizer.text("Original text", interface=True)
        state = localizer.translation_state(message.body)
        if state == "original":
            return localizer.text("Original text", interface=True)
        if state == "pending" and localizer.language != "en":
            return localizer.text("Translating…", interface=True)
        return ""

    def toggle_original(self, identifier):
        localizer = self.reader_localizer()
        if localizer:
            if identifier in localizer.originals:
                localizer.originals.remove(identifier)
            else:
                localizer.originals.add(identifier)
            self.show_messages(self.source_messages, force=True)

    def show_messages(self, messages, *, force=False):
        from aedrova.desktop.state import Message

        self.reaction_bar.hide()
        self.source_messages = list(messages)
        rows = list(messages)
        if self.agent_visible and self.agent_message_id and self.agent_feed.toPlainText():
            position = next(
                (i + 1 for i, m in enumerate(rows) if m.id == self.agent_anchor),
                len(rows) if self.agent_anchor else 0,
            )
            rows.insert(
                position,
                Message(
                    self.agent_message_id,
                    self.agent_feed.author_name,
                    "",
                    "",
                    self.agent_feed.toPlainText(),
                ),
            )
        if not force and self.conversation_model.messages == rows:
            return
        bar = self.verticalScrollBar()
        at_bottom = bar.value() >= bar.maximum() - 4
        index = self.indexAt(QPoint(self.viewport().width() // 2, 1))
        anchor = index.data(MESSAGE_ROLE).id if index.isValid() else None
        offset = self.visualRect(index).top() if index.isValid() else 0
        self._scroll_target = None
        if self.agent_feed:
            # Qt owns index widgets and deletes them on model reset. Detach the live
            # transcript first so ordinary realtime refreshes cannot destroy it.
            self.agent_feed.hide()
            self.agent_feed.setParent(self)
        if self.agent_feed and self.agent_visible:
            self.agent_feed.content_height(self.viewport().width())
        old = self.conversation_model.messages
        append_only = (
            not force
            and not self.agent_visible
            and len(rows) > len(old)
            and rows[: len(old)] == old
        )
        if append_only:
            for message in rows[len(old) :]:
                self.conversation_model.append(message)
        else:
            self.conversation_model.replace(rows)
        if self.agent_visible and self.agent_message_id:
            for row, message in enumerate(rows):
                if message.id == self.agent_message_id:
                    holder = QWidget()
                    layout = QVBoxLayout(holder)
                    layout.setContentsMargins(0, 0, 0, 0)
                    layout.addWidget(self.agent_feed)
                    self.setIndexWidget(self.model().index(row), holder)
                    self.agent_feed.show()
                    break
        # Inline agent height may change drastically at completion. Recalculate
        # the list range after attaching its widget, before restoring scrolling.
        self.doItemsLayout()
        if at_bottom:
            self.scrollToBottom()
        elif anchor:
            for row, message in enumerate(self.conversation_model.messages):
                if message.id == anchor:
                    index = self.model().index(row)
                    self.doItemsLayout()
                    bar.setValue(bar.value() + self.visualRect(index).top() - offset)
                    break

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self.scheduleDelayedItemsLayout()


class MessageEditor(QPlainTextEdit):
    files_dropped = Signal(list)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and all(u.isLocalFile() for u in event.mimeData().urls()):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        self.dragEnterEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasUrls() and all(u.isLocalFile() for u in event.mimeData().urls()):
            self.files_dropped.emit([u.toLocalFile() for u in event.mimeData().urls()])
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    submitted = Signal()
    focus_changed = Signal(bool)
    completion = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabChangesFocus(True)

    def focusInEvent(self, event):  # noqa: N802
        super().focusInEvent(event)
        self.focus_changed.emit(True)

    def focusOutEvent(self, event):  # noqa: N802
        super().focusOutEvent(event)
        self.focus_changed.emit(False)

    def event(self, event):
        # QWidget handles Tab traversal before keyPressEvent. Complete an active
        # mention here, while keeping ordinary Tab/Shift Tab focus navigation.
        if (
            event.type() == QEvent.Type.KeyPress
            and event.key() == Qt.Key.Key_Tab
            and self.completion
            and self.completion(event)
        ):
            return True
        return super().event(event)

    def keyPressEvent(self, event):  # noqa: N802
        if self.completion and self.completion(event):
            return
        if (
            event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
            and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ):
            if not event.isAutoRepeat():
                self.submitted.emit()
            event.accept()
        else:
            super().keyPressEvent(event)


class Composer(QFrame):
    submitted = Signal(str)

    def __init__(self, parent=None, *, thread=False):
        super().__init__(parent)
        self.setObjectName("Composer")
        self.thread = thread
        self.agent_name = "Aedrova"
        self.ai_teammates = []  # Legacy fixture compatibility; no production routing.
        self.dots = []
        self.people = []
        self.mention_tokens = {}
        self.mention_choice = None
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)
        self.command_cue = QLabel(
            ("IN THIS THREAD" if thread else "TO YOUR TEAM") + "  ·  @Aedrova to build"
        )
        self.command_cue.setObjectName("ComposerCue")
        layout.addWidget(self.command_cue)
        self.editor = MessageEditor()
        self.editor.setObjectName("ComposerEditor")
        self.editor.focus_changed.connect(self._focus_changed)
        self.editor.setAccessibleName("Thread reply" if thread else "Message composer")
        self.editor.setAccessibleDescription("Return sends. Shift Return adds a new line.")
        self.editor.setFixedHeight(67)
        self.editor.document().documentLayout().documentSizeChanged.connect(self._resize_editor)
        self.suggestion = SpringButton("@Aedrova    ·    Tab or ↵")
        self.suggestion.setProperty("role", "outline")
        self.suggestion.setAccessibleName("Complete mention @Aedrova. Tab or Return.")
        self.suggestion.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.suggestion.hide()
        self.suggestion.clicked.connect(self.complete_mention)
        self.editor.completion = self.completion_key
        self.editor.cursorPositionChanged.connect(self.update_suggestion)
        self.mention_list = QListWidget(self)
        self.mention_list.setObjectName("MentionPicker")
        self.mention_list.setAccessibleName(
            "Mention suggestions. Agents, Buds, people and channel."
        )
        self.mention_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.mention_list.setIconSize(QSize(30, 30))
        self.mention_list.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.mention_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.mention_list.hide()
        self.mention_list.currentItemChanged.connect(self._select_mention)
        self.mention_list.itemClicked.connect(lambda _: self.complete_mention())
        layout.addWidget(self.suggestion)
        layout.addWidget(self.editor)
        bottom = QHBoxLayout()
        self.mention = SpringButton("@")
        self.mention.setProperty("role", "icon")
        self.mention.setFixedHeight(30)
        self.mention.setMaximumWidth(180)
        self.mention.setText("Ask Aedrova")
        self.mention.setAccessibleName("Mention Aedrova")
        self.mention.setToolTip("Insert @Aedrova · ask your agent to build")
        self.mention.clicked.connect(self.insert_mention)
        from aedrova.agents.permissions import MODES
        from aedrova.desktop.controls import ChoiceBox

        self.permissions = ChoiceBox()
        self.permissions.setObjectName("AgentPermissions")
        self.permissions.setAccessibleName("Aedrova agent permissions")
        self.permissions.setMaximumWidth(175)
        self.permissions.setMinimumHeight(30)
        self.permissions.setFixedHeight(30)
        for value, (title, description) in MODES.items():
            self.permissions.addItem(title, value)
            self.permissions.setItemData(
                self.permissions.count() - 1, description, Qt.ItemDataRole.ToolTipRole
            )
        self.permissions.setToolTip(MODES["ask"][1])
        bottom.addWidget(self.permissions)
        bottom.addWidget(self.mention)
        self.emoji = SpringButton("☺")
        self.emoji.setProperty("role", "icon")
        self.emoji.setFixedSize(30, 29)
        self.emoji.setAccessibleName("Insert emoji")
        self.emoji.setToolTip("Choose an emoji")
        self.emoji.clicked.connect(self.insert_emoji)
        bottom.addWidget(self.emoji)
        self.hint = QLabel("↵ send  ·  ⇧↵ new line")
        self.hint.setProperty("role", "muted")
        bottom.addWidget(self.hint)
        bottom.addStretch()
        self.send = SpringButton("Reply" if thread else "Send")
        self.send.setProperty("role", "primary")
        self.send.setAccessibleName("Send thread reply" if thread else "Send message")
        self.send.setToolTip("Send reply · Return" if thread else "Send message · Return")
        self.send.setEnabled(False)
        self.send.clicked.connect(self._submit)
        self.editor.submitted.connect(self._submit)
        self.editor.textChanged.connect(self._changed)
        bottom.addWidget(self.send)
        layout.addLayout(bottom)
        from aedrova.desktop.icons import assign

        for control, name in ((self.mention, "mention"), (self.emoji, "smile")):
            assign(control, name)
            if control is not self.mention:
                control.setText("")
        assign(self.send, "send")

    def insert_emoji(self):
        emoji = pick_emoji(self)
        if emoji:
            self.editor.textCursor().insertText(emoji)
            self.editor.setFocus()

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        if hasattr(self, "hint"):
            self.hint.setVisible(self.width() >= 650)
            self.mention.setText("Ask " + self.agent_name if self.width() >= 500 else "")
            self._position_mentions()

    def moveEvent(self, event):  # noqa: N802
        super().moveEvent(event)
        if hasattr(self, "mention_list"):
            self._position_mentions()

    def hideEvent(self, event):  # noqa: N802
        if hasattr(self, "mention_list"):
            self.mention_list.hide()
            self.suggestion.hide()
        super().hideEvent(event)

    def _position_mentions(self):
        if self.mention_list.isHidden():
            return
        host = self.window()
        anchor = self.mapTo(host, QPoint(0, 0))
        height = self.mention_list.height()
        self.mention_list.setGeometry(
            anchor.x(), max(0, anchor.y() - height - 6), self.width(), height
        )
        self.mention_list.raise_()

    def _focus_changed(self, focused):
        self.setProperty("focused", focused)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
        if not focused:
            self.mention_list.hide()
            self.suggestion.hide()

    def _resize_editor(self, size):
        # QPlainTextDocumentLayout reports height in visual lines, including wrapping.
        height = min(
            134, max(67, ceil(size.height() * self.editor.fontMetrics().lineSpacing()) + 12)
        )
        if self.editor.height() != height:
            self.editor.setFixedHeight(height)

    def set_agent_name(self, name):
        self.agent_name = (name or "").strip() or "Aedrova"
        mention = "@" + self.agent_name
        self.suggestion.setText(f"{mention}    ·    Tab or ↵")
        self.suggestion.setAccessibleName(f"Complete mention {mention}. Tab or Return.")
        self.mention.setText("Ask " + self.agent_name)
        self.command_cue.setText(
            ("IN THIS THREAD" if self.thread else "TO YOUR TEAM")
            + "  ·  @"
            + self.agent_name
            + " to build"
        )
        self.mention.setAccessibleName("Mention " + self.agent_name)
        self.mention.setToolTip(f"Insert {mention} · ask your agent to build")
        self.update_suggestion()

    def mention_entries(self):
        """One catalog for typed completion and the toolbar; preserve routing tokens."""
        entries = [("Agents", self.agent_name, "@" + self.agent_name, "Build with your team", None)]
        entries += [
            (
                "Agents",
                r["config"]["name"],
                "<@ai:" + r["id"] + "|" + r["config"]["name"] + ">",
                r["config"].get("role", "AI teammate"),
                None,
            )
            for r in self.ai_teammates
            if not r["paused"]
        ]
        entries += [
            (
                "Buds",
                r["name"],
                "<@dot:" + r["id"] + "|" + r["name"] + ">",
                r.get("role", "Your AI teammate"),
                r,
            )
            for r in self.dots
        ]
        entries += [
            (
                "People",
                p["display_name"],
                "<@" + p["user_id"] + "|" + p["display_name"] + ">",
                p.get("custom_status") or p.get("availability", "Teammate"),
                p,
            )
            for p in self.people
        ]
        entries += [
            ("Notify channel", n, "@" + n, d, None)
            for n, d in (("channel", "Notify this channel"), ("everyone", "Notify everyone"))
        ]
        return entries

    def _mention_match(self):
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            return None, ""
        prefix = (
            self.editor.toPlainText()
            .encode("utf-16-le")[: cursor.position() * 2]
            .decode("utf-16-le")
        )
        match = re.search(r"(?<!\S)@([^@\n]*)$", prefix)
        if not match:
            return None, ""
        return len(prefix[: match.start()].encode("utf-16-le")) // 2, match[1].casefold()

    def mention_start(self):
        start, _ = self._mention_match()
        return start if self.mention_choice else None

    def _select_mention(self, item, previous=None):
        choice = item.data(Qt.ItemDataRole.UserRole) if item else None
        if not choice:
            return
        self.mention_choice = choice
        suffix = " · Bud" if choice[1].startswith("<@dot:") else ""
        self.suggestion.setText("@" + choice[0] + suffix + "    ·    Tab or ↵")
        self.suggestion.setAccessibleName("Insert @" + choice[0] + ". Tab or Return.")

    def update_suggestion(self):
        start, query = self._mention_match()
        selected = self.mention_choice
        self.mention_list.blockSignals(True)
        self.mention_list.clear()
        self.mention_choice = None
        if start is None:
            self.mention_list.blockSignals(False)
            self.mention_list.hide()
            self.suggestion.hide()
            return
        first = chosen = None
        group = None
        for section, name, token, detail, config in self.mention_entries():
            aliases = [name, (config or {}).get("username", "")]
            if query and not any(query in str(alias).casefold() for alias in aliases):
                continue
            if section == "People" and query and query not in name.casefold():
                # Preserve the existing username mention syntax when searching by handle.
                name = config["username"]
                token = "<@" + config["user_id"] + "|" + name + ">"
            if group != section:
                header = QListWidgetItem(section)
                header.setFlags(Qt.ItemFlag.NoItemFlags)
                header.setSizeHint(QSize(0, 24))
                self.mention_list.addItem(header)
                group = section
            item = QListWidgetItem("@" + name + "  ·  " + str(detail or "Teammate"))
            item.setData(Qt.ItemDataRole.UserRole, (name, token))
            item.setToolTip("@" + name + " · " + str(detail or "Teammate"))
            item.setSizeHint(QSize(0, 38))
            if section == "Buds":
                from aedrova.desktop.bud_art import appearance, sprite

                item.setIcon(QIcon(sprite(appearance(config), str(config.get("color", "")))))
            self.mention_list.addItem(item)
            if first is None:
                first = item
            if selected == (name, token):
                chosen = item
        self.mention_list.blockSignals(False)
        visible = start is not None and first is not None
        if self.mention_list.parentWidget() is not self.window():
            self.mention_list.setParent(self.window())
        self.mention_list.setVisible(visible)
        self.suggestion.setVisible(visible)
        if visible:
            self.mention_list.setFixedHeight(
                min(
                    224,
                    sum(
                        self.mention_list.item(i).sizeHint().height()
                        for i in range(self.mention_list.count())
                    )
                    + 8,
                )
            )
            self._position_mentions()
            self.mention_list.setCurrentItem(chosen or first)
            self._select_mention(chosen or first)

    def completion_key(self, event):
        if self.suggestion.isHidden():
            return False
        if event.key() == Qt.Key.Key_Escape:
            self.suggestion.hide()
            self.mention_list.hide()
        elif event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down) and not event.modifiers():
            rows = [
                i
                for i in range(self.mention_list.count())
                if self.mention_list.item(i).data(Qt.ItemDataRole.UserRole)
            ]
            current = rows.index(self.mention_list.currentRow())
            step = 1 if event.key() == Qt.Key.Key_Down else -1
            self.mention_list.setCurrentRow(rows[(current + step) % len(rows)])
        elif (
            event.key() in (Qt.Key.Key_Tab, Qt.Key.Key_Return, Qt.Key.Key_Enter)
            and not event.modifiers()
        ):
            self.complete_mention()
        else:
            return False
        event.accept()
        return True

    def complete_mention(self):
        start = self.mention_start()
        if start is None:
            return
        name, token = self.mention_choice
        cursor = self.editor.textCursor()
        cursor.setPosition(start, QTextCursor.MoveMode.KeepAnchor)
        if token.startswith("<@"):
            self.mention_tokens[name] = token
        cursor.insertText("@" + name + " ")
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()
        self.suggestion.hide()
        self.mention_list.hide()

    def insert_mention(self):
        cursor = self.editor.textCursor()
        before = self.editor.toPlainText().encode("utf-16-le")[: cursor.selectionStart() * 2]
        prefix = before.decode("utf-16-le")
        separator = " " if prefix and not prefix[-1].isspace() else ""
        cursor.insertText(separator + "@" + self.agent_name + " ")
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()

    def _changed(self):
        self.update_suggestion()
        text = self.editor.toPlainText().strip()
        self.send.setEnabled(
            (bool(text) or bool(getattr(self, "attachment_drafts", []))) and len(text) <= 10_000
        )
        if len(text) > 10_000:
            self.hint.setText("Limit: 10,000 characters")
        else:
            self.hint.setText("↵ send  ·  ⇧↵ new line")

    def _submit(self):
        for card, publish in list(getattr(self, "attachment_drafts", [])):
            publish()
            card.deleteLater()
        self.attachment_drafts = []
        self._changed()
        text = self.submission_text()
        if text and len(text) <= 10_000:
            if hasattr(self, "dictation"):
                self.dictation.cancel()
            self.submission = (text, self.editor.document().revision())
            self.submitted.emit(text)

    def submission_text(self):
        text = self.editor.toPlainText().strip()
        for name, token in self.mention_tokens.items():
            text = re.sub(
                r"(?<!\S)@" + re.escape(name) + r"(?=$|[\s.,!?])", lambda _, t=token: t, text
            )
        return text

    def clear_submission(self, text):
        """Clear only the accepted revision, comparing the actual wire mentions."""
        sent = getattr(self, "submission", None)
        if self.submission_text() != text.strip():
            return False
        if sent and sent != (text.strip(), self.editor.document().revision()):
            return False
        self.clear()
        return True

    def clear(self):
        self.submission = None
        self.editor.clear()
        QTimer.singleShot(0, self.editor.setFocus)
