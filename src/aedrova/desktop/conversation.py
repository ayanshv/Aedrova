"""Virtualized variable-height messages and keyboard-first composer."""

import re
from collections import OrderedDict
from html import escape
from math import ceil
from urllib.parse import urlsplit

from PySide6.QtCore import (
    QAbstractListModel,
    QEvent,
    QPersistentModelIndex,
    QPoint,
    QPointF,
    QRectF,
    QSize,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QAbstractTextDocumentLayout,
    QColor,
    QFont,
    QFontMetrics,
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
    QPlainTextEdit,
    QStyle,
    QStyledItemDelegate,
    QVBoxLayout,
    QWidget,
)

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
            return (
                f"{message.author}, {message.time}. {decision}{message.body}. "
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
                self.dataChanged.emit(index, index, [])
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


class MessageDelegate(QStyledItemDelegate):
    def __init__(self, view):
        super().__init__(view)
        self.view = view
        self.theme = LIGHT
        self.documents = OrderedDict()

    def document(self, message, width):
        width = max(80, width)
        key = (message.id, message.body, width, self.theme.name)
        if key not in self.documents:
            document = SafeDocument()
            document.setDefaultFont(font(14))
            document.setDefaultStyleSheet(
                "a { color: " + self.theme.accent + "; } pre { white-space: pre-wrap; }"
            )
            document.setDocumentMargin(0)
            text = re.sub(r"<@([a-f0-9-]{36})\|([^>\n]{1,80})>", lambda m: "@" + m[2], message.body)
            document.setMarkdown(escape(text, quote=False))
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
                block_format.setTopMargin(3)
                block_format.setBottomMargin(4)
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

    def sizeHint(self, option, index):  # noqa: N802
        message = index.data(MESSAGE_ROLE)
        width = self.view.viewport().width()
        if message.id == getattr(self.view, "agent_message_id", None):
            return QSize(width, self.view.agent_feed.content_height(width))
        document = self.document(message, width - 94)
        extra = (58 if message.attachment else 0) + (
            26 if message.replies and self.view.allow_threads else 0
        )
        header = QFontMetrics(font(14, True)).height() + 6
        chips = reaction_chips(message, width, 0)
        reaction_height = int(chips[-1][0].bottom()) + 8 if chips else 0
        return QSize(
            width, 18 + header + ceil(document.size().height()) + extra + 22 + reaction_height
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
        selected = option.state & QStyle.StateFlag.State_Selected
        hovered = option.state & QStyle.StateFlag.State_MouseOver
        if selected or hovered:
            painter.fillRect(rect, QColor(t.surface))
        if selected and option.state & QStyle.StateFlag.State_HasFocus:
            painter.setPen(QColor(t.accent))
            painter.drawRoundedRect(QRectF(rect).adjusted(3, 1, -3, -1), 5, 5)
        x, y = rect.x() + 28, rect.y() + 18
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(t.avatars[message.tone % len(t.avatars)]))
        painter.drawRoundedRect(QRectF(x, y, 34, 34), 12, 12)
        painter.setPen(QColor(t.text))
        painter.setFont(font(11, True))
        painter.drawText(QRectF(x, y, 34, 34), Qt.AlignmentFlag.AlignCenter, message.initials)
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
        timestamp = message.delivery or (
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
                QFontMetrics(font(14, True)).horizontalAdvance(message.author) + 4,
                available - time_width - badge_width - 12,
            ),
        )
        line_flags = Qt.AlignmentFlag.AlignVCenter | Qt.TextFlag.TextSingleLine
        painter.setFont(font(14, True))
        painter.drawText(
            QRectF(x, y, name_width, header_height - 6),
            line_flags,
            painter.fontMetrics().elidedText(
                message.author, Qt.TextElideMode.ElideRight, int(name_width)
            ),
        )
        painter.setFont(font(11))
        painter.setPen(QColor(t.muted))
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
        painter.translate(x, y + header_height)
        context = QAbstractTextDocumentLayout.PaintContext()
        context.palette.setColor(QPalette.ColorRole.Text, QColor(t.secondary))
        document.documentLayout().draw(painter, context)
        painter.restore()
        bottom = y + header_height + document.size().height()
        if message.attachment:
            painter.setPen(QColor(t.border))
            painter.setBrush(QColor(t.surface))
            card_width = min(350, rect.width() - 96)
            painter.drawRoundedRect(QRectF(x, bottom + 10, card_width, 44), 12, 12)
            painter.setPen(QColor(t.accent))
            painter.setFont(font(10, True))
            painter.drawText(QRectF(x + 12, bottom + 23, 30, 18), "FILE")
            painter.setFont(font(11))
            painter.setPen(QColor(t.secondary))
            elided = painter.fontMetrics().elidedText(
                message.attachment,
                Qt.TextElideMode.ElideRight,
                int(card_width - 60),
            )
            painter.drawText(QRectF(x + 48, bottom + 23, card_width - 55, 18), elided)
            bottom += 58
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
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setLayoutMode(QListView.LayoutMode.Batched)
        self.setBatchSize(100)
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
            control.setFixedSize(32, 30)
            control.setAccessibleName("React " + emoji)
            control.clicked.connect(
                lambda checked=False, e=emoji: self.react(self.hover_message, e)
            )
            bar.addWidget(control)
        more = SpringButton("+")
        more.setFixedSize(32, 30)
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

    def mouseReleaseEvent(self, event):  # noqa: N802
        self._click_position = event.position().toPoint()
        super().mouseReleaseEvent(event)

    def _clicked_message(self, index):
        if not index.isValid():
            return
        message = index.data(MESSAGE_ROLE)
        rect = self.visualRect(index)
        document = self.delegate.document(message, rect.width() - 94)
        top = rect.top() + 18 + QFontMetrics(font(14, True)).height() + 6
        top += document.size().height() + (58 if message.attachment else 0)
        top += 30 if message.replies and self.allow_threads else 8
        point = getattr(self, "_click_position", QPoint(-1, -1))
        for box, reaction, _ in reaction_chips(message, rect.width(), top):
            if box.contains(point):
                self.react(message.id, reaction["emoji"])
                return
        body_top = rect.top() + 18 + QFontMetrics(font(14, True)).height() + 6
        link = document.documentLayout().anchorAt(QPointF(point.x() - 74, point.y() - body_top))
        if link and urlsplit(link).scheme in ("https", "http"):
            self.link_requested.emit(link)
            return
        if (
            message.attachment_id
            and body_top + document.size().height()
            <= point.y()
            <= body_top + document.size().height() + 58
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
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._request_thread(self.currentIndex())
            event.accept()
        elif event.matches(QKeySequence.StandardKey.Copy):
            self.copy_current()
            event.accept()
        else:
            super().keyPressEvent(event)

    def copy_current(self):
        if self.currentIndex().isValid():
            QApplication.clipboard().setText(self.currentIndex().data(MESSAGE_ROLE).body)

    def _context_menu(self, position):
        index = self.indexAt(position)
        if not index.isValid():
            return
        self.setCurrentIndex(index)
        menu = AppMenu(self)
        if self.allow_threads and index.data(MESSAGE_ROLE).id != self.agent_message_id:
            menu.addAction("Reply in thread", lambda: self._request_thread(index))
        message = index.data(MESSAGE_ROLE)
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
                    "Open attachment…", lambda: self.action_requested.emit("attachment", message.id)
                )
            if message.mine:
                menu.addAction(
                    "Edit message…", lambda: self.action_requested.emit("edit", message.id)
                )
                menu.addAction(
                    "Delete / unsend message", lambda: self.unsend_requested.emit(message.id)
                )
        menu.addAction("Copy message", self.copy_current)
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
        super().wheelEvent(event)

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
        self.ai_teammates = []
        self.people = []
        self.mention_tokens = {}
        self.mention_choice = None
        layout = QVBoxLayout(self)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        layout.setContentsMargins(12, 8, 12, 10)
        layout.setSpacing(0)
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
        layout.addWidget(self.suggestion)
        layout.addWidget(self.editor)
        bottom = QHBoxLayout()
        self.mention = SpringButton("@")
        self.mention.setProperty("role", "icon")
        self.mention.setFixedSize(30, 29)
        self.mention.setAccessibleName("Mention Aedrova")
        self.mention.setToolTip("Insert @Aedrova · ask your agent to build")
        self.mention.clicked.connect(self.insert_mention)
        bottom.addWidget(self.mention)
        self.emoji = SpringButton("☺")
        self.emoji.setProperty("role", "icon")
        self.emoji.setFixedSize(30, 29)
        self.emoji.setAccessibleName("Insert emoji")
        self.emoji.setToolTip("Choose an emoji")
        self.emoji.clicked.connect(self.insert_emoji)
        bottom.addWidget(self.emoji)
        self.hint = QLabel("Shift ↵ for a new line")
        self.hint.setProperty("role", "muted")
        bottom.addWidget(self.hint)
        bottom.addStretch()
        self.send = SpringButton("Reply ↑" if thread else "Send ↑")
        self.send.setProperty("role", "primary")
        self.send.setAccessibleName("Send thread reply" if thread else "Send message")
        self.send.setToolTip("Send reply · Return" if thread else "Send message · Return")
        self.send.setEnabled(False)
        self.send.clicked.connect(self._submit)
        self.editor.submitted.connect(self._submit)
        self.editor.textChanged.connect(self._changed)
        bottom.addWidget(self.send)
        layout.addLayout(bottom)

    def insert_emoji(self):
        emoji = pick_emoji(self)
        if emoji:
            self.editor.textCursor().insertText(emoji)
            self.editor.setFocus()

    def _focus_changed(self, focused):
        self.setProperty("focused", focused)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

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
        self.mention.setAccessibleName("Mention " + self.agent_name)
        self.mention.setToolTip(f"Insert {mention} · ask your agent to build")
        self.update_suggestion()

    def mention_start(self):
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            return None
        prefix = (
            self.editor.toPlainText()
            .encode("utf-16-le")[: cursor.position() * 2]
            .decode("utf-16-le")
        )
        match = re.search(r"(?<!\S)@([^@\n]*)$", prefix)
        self.mention_choice = None
        if match:
            choices = (
                [
                    (self.agent_name, "@" + self.agent_name),
                    ("channel", "@channel"),
                    ("everyone", "@everyone"),
                ]
                + [
                    (r["config"]["name"], "<@ai:" + r["id"] + "|" + r["config"]["name"] + ">")
                    for r in self.ai_teammates
                    if not r["paused"]
                ]
                + [
                    (p["display_name"], "<@" + p["user_id"] + "|" + p["display_name"] + ">")
                    for p in self.people
                ]
                + [
                    (p["username"], "<@" + p["user_id"] + "|" + p["username"] + ">")
                    for p in self.people
                    if p.get("username")
                ]
            )
            hits = [
                (name, token)
                for name, token in choices
                if name.casefold().startswith(match[1].casefold())
            ]
            if hits:
                self.mention_choice = hits[0]
        if match and self.mention_choice:
            return len(prefix[: match.start()].encode("utf-16-le")) // 2
        return None

    def update_suggestion(self):
        self.suggestion.setVisible(self.mention_start() is not None)
        if self.mention_choice:
            suffix = " · AI teammate" if self.mention_choice[1].startswith("<@ai:") else ""
            self.suggestion.setText("@" + self.mention_choice[0] + suffix + "    ·    Tab or ↵")

    def completion_key(self, event):
        if self.suggestion.isHidden():
            return False
        if event.key() == Qt.Key.Key_Escape:
            self.suggestion.hide()
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
        cursor = self.editor.textCursor()
        cursor.setPosition(start, QTextCursor.MoveMode.KeepAnchor)
        name, token = self.mention_choice
        if token.startswith("<@"):
            self.mention_tokens[name] = token
        cursor.insertText("@" + name + " ")
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()
        self.suggestion.hide()

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
        self.send.setEnabled(bool(text) and len(text) <= 10_000)
        if len(text) > 10_000:
            self.hint.setText("Limit: 10,000 characters")
        else:
            self.hint.setText("Shift ↵ for a new line")

    def _submit(self):
        text = self.editor.toPlainText().strip()
        if text and len(text) <= 10_000:
            for name, token in self.mention_tokens.items():
                text = re.sub(
                    r"(?<!\S)@" + re.escape(name) + r"(?=$|[\s.,!?])", lambda _, t=token: t, text
                )
            self.submitted.emit(text)

    def clear(self):
        self.editor.clear()
        QTimer.singleShot(0, self.editor.setFocus)
