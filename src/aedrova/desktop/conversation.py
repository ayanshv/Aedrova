"""Virtualized variable-height messages and keyboard-first composer."""

import re
from collections import OrderedDict
from math import ceil

from PySide6.QtCore import (
    QAbstractListModel,
    QEvent,
    QPersistentModelIndex,
    QPoint,
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
    QPalette,
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
)

from aedrova.desktop.controls import AppMenu
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


class MessageDelegate(QStyledItemDelegate):
    def __init__(self, view):
        super().__init__(view)
        self.view = view
        self.theme = LIGHT
        self.documents = OrderedDict()

    def document(self, message, width):
        width = max(80, width)
        key = (message.id, message.body, width)
        if key not in self.documents:
            document = QTextDocument()
            document.setDefaultFont(font(14))
            document.setDocumentMargin(0)
            document.setPlainText(message.body)
            document.setTextWidth(width)
            self.documents[key] = document
            if len(self.documents) > 512:
                self.documents.popitem(last=False)
        self.documents.move_to_end(key)
        return self.documents[key]

    def sizeHint(self, option, index):  # noqa: N802
        message = index.data(MESSAGE_ROLE)
        width = self.view.viewport().width()
        document = self.document(message, width - 94)
        extra = (58 if message.attachment else 0) + (
            26 if message.replies and self.view.allow_threads else 0
        )
        header = QFontMetrics(font(14, True)).height() + 6
        return QSize(width, 18 + header + ceil(document.size().height()) + extra + 22)

    def paint(self, painter: QPainter, option, index):
        message = index.data(MESSAGE_ROLE)
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
        x += 46
        header_height = QFontMetrics(font(14, True)).height() + 6
        available = max(0, rect.width() - 94)
        badge_width = 76 if message.decision else 0
        timestamp = message.delivery or message.time
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
        painter.restore()


class MessageView(QListView):
    thread_requested = Signal(str)

    def __init__(self, parent=None, *, allow_threads=True):
        super().__init__(parent)
        self._scroll_target = None
        self._scroll_hint = QListView.ScrollHint.EnsureVisible
        self._scroll_timer = QTimer(self)
        self._scroll_timer.setSingleShot(True)
        self._scroll_timer.timeout.connect(self._finish_scroll)
        self.verticalScrollBar().rangeChanged.connect(lambda *_: self._scroll_timer.start(0))
        self.allow_threads = allow_threads
        self.setObjectName("Messages")
        self.setAccessibleName("Conversation messages")
        self.setAccessibleDescription(
            "Use arrow keys to select a message and Return to open its thread."
        )
        self.setMouseTracking(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollMode(QListView.ScrollMode.ScrollPerPixel)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setLayoutMode(QListView.LayoutMode.Batched)
        self.setBatchSize(100)
        self.conversation_model = ConversationModel(parent=self, allow_threads=allow_threads)
        self.setModel(self.conversation_model)
        self.delegate = MessageDelegate(self)
        self.setItemDelegate(self.delegate)
        self.clicked.connect(self._request_thread)
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)

    def _request_thread(self, index):
        if self.allow_threads and index.isValid():
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
        if self.allow_threads:
            menu.addAction("Reply in thread", lambda: self._request_thread(index))
        menu.addAction("Copy message", self.copy_current)
        menu.exec(self.viewport().mapToGlobal(position))

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
        if self.viewport().rect().intersects(self.visualRect(index)):
            self._scroll_target = None

    def wheelEvent(self, event):  # noqa: N802
        self._scroll_target = None
        super().wheelEvent(event)

    def set_theme(self, theme: Theme):
        self.delegate.theme = theme
        self.viewport().update()

    def show_messages(self, messages):
        if self.conversation_model.messages == list(messages):
            return
        bar = self.verticalScrollBar()
        at_bottom = bar.value() >= bar.maximum() - 4
        index = self.indexAt(QPoint(self.viewport().width() // 2, 1))
        anchor = index.data(MESSAGE_ROLE).id if index.isValid() else None
        offset = self.visualRect(index).top() if index.isValid() else 0
        self._scroll_target = None
        self.conversation_model.replace(messages)
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

    def mention_start(self):
        cursor = self.editor.textCursor()
        if cursor.hasSelection():
            return None
        prefix = (
            self.editor.toPlainText()
            .encode("utf-16-le")[: cursor.position() * 2]
            .decode("utf-16-le")
        )
        match = re.search(r"(?<!\S)@([A-Za-z]*)$", prefix)
        if match and "aedrova".startswith(match[1].lower()):
            return len(prefix[: match.start()].encode("utf-16-le")) // 2
        return None

    def update_suggestion(self):
        self.suggestion.setVisible(self.mention_start() is not None)

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
        cursor.insertText("@Aedrova ")
        self.editor.setTextCursor(cursor)
        self.editor.setFocus()
        self.suggestion.hide()

    def insert_mention(self):
        cursor = self.editor.textCursor()
        before = self.editor.toPlainText().encode("utf-16-le")[: cursor.selectionStart() * 2]
        prefix = before.decode("utf-16-le")
        separator = " " if prefix and not prefix[-1].isspace() else ""
        cursor.insertText(separator + "@Aedrova ")
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
            self.submitted.emit(text)

    def clear(self):
        self.editor.clear()
        QTimer.singleShot(0, self.editor.setFocus)
