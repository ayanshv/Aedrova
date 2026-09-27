from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from aedrova.desktop.materials import SpringButton, system_font


def label(text, role="", *, wrap=False):
    widget = QLabel(text)
    if role in ("display", "heading"):
        widget.setFont(system_font(34 if role == "display" else 32, QFont.Weight.DemiBold, -0.9))
    elif role == "title":
        widget.setFont(system_font(20, QFont.Weight.DemiBold, -0.35))
    widget.setTextFormat(Qt.TextFormat.PlainText)
    widget.setWordWrap(wrap)
    if role:
        widget.setProperty("role", role)
    return widget


def button(text, accessible="", role=""):
    widget = SpringButton(text)
    widget.setAccessibleName(accessible or text)
    widget.setCursor(Qt.CursorShape.PointingHandCursor)
    if role:
        widget.setProperty("role", role)
    return widget


class CreateDialog(QDialog):
    def __init__(self, parent, *, workspace, create):
        super().__init__(parent)
        self.create = create
        self.result_object = None
        self.setWindowTitle("Create workspace" if workspace else "Create channel")
        self.setModal(True)
        self.setFixedWidth(480)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 30, 32, 30)
        layout.setSpacing(14)
        layout.addWidget(label(self.windowTitle(), "title"))
        layout.addWidget(
            label(
                "Make room for your next idea." if workspace else "Give this conversation a home.",
                "muted",
            )
        )
        self.name = QLineEdit()
        self.name.setMaxLength(32)
        self.name.setPlaceholderText("e.g. Northstar Labs" if workspace else "e.g. launch-planning")
        self.name.setAccessibleName("Workspace name" if workspace else "Channel name")
        caption = label("Name")
        caption.setBuddy(self.name)
        layout.addWidget(caption)
        layout.addWidget(self.name)
        self.topic = QLineEdit()
        self.topic.setMaxLength(120)
        self.topic.setPlaceholderText("What is this channel for?")
        self.topic.setAccessibleName("Channel topic")
        if not workspace:
            topic_label = label("Topic · optional")
            topic_label.setBuddy(self.topic)
            layout.addWidget(topic_label)
            layout.addWidget(self.topic)
        else:
            self.topic.hide()
        layout.addWidget(
            label(
                "Local preview only. This space resets when you close the app.", "muted", wrap=True
            )
        )
        self.error = label("", "error", wrap=True)
        self.error.hide()
        layout.addWidget(self.error)
        actions = QHBoxLayout()
        actions.addStretch()
        cancel = button("Cancel")
        cancel.clicked.connect(self.reject)
        actions.addWidget(cancel)
        self.submit = button("Create workspace" if workspace else "Create channel", role="primary")
        self.submit.setDefault(True)
        self.submit.clicked.connect(self.save)
        actions.addWidget(self.submit)
        layout.addLayout(actions)

    def save(self):
        try:
            self.result_object = self.create(self.name.text(), self.topic.text())
        except ValueError as exc:
            self.error.setText(str(exc))
            self.error.show()
            self.name.setFocus()
            return
        self.accept()


class SwitcherDialog(QDialog):
    chosen = Signal(str, str)

    def __init__(self, parent, store):
        super().__init__(parent)
        self.store = store
        self.setWindowTitle("Jump to a conversation")
        self.setModal(True)
        self.resize(560, 430)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(12)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Find a channel, person, or workspace…")
        self.search.setAccessibleName("Search channels and workspaces")
        self.search.installEventFilter(self)
        layout.addWidget(self.search)
        self.results = QListWidget()
        self.results.setObjectName("Switcher")
        self.results.setAccessibleName("Conversation search results")
        layout.addWidget(self.results)
        self.empty = label("No conversations match your search.", "muted")
        layout.addWidget(self.empty)
        layout.addWidget(label("↑ ↓ to navigate     ↵ to open     esc to close", "muted"))
        self.search.textChanged.connect(self.filter)
        self.search.returnPressed.connect(self.choose_current)
        self.results.itemActivated.connect(lambda _: self.choose_current())
        self.results.itemClicked.connect(lambda _: self.choose_current())
        self.filter("")

    def filter(self, query):
        self.results.clear()
        query = query.strip().casefold()
        for workspace in self.store.workspaces:
            for channel in workspace.channels:
                prefix = "" if channel.direct else "# "
                text = f"{prefix}{channel.name}   /   {workspace.name}"
                if query in text.casefold():
                    item = QListWidgetItem(text)
                    item.setData(Qt.ItemDataRole.UserRole, (workspace.id, channel.id))
                    self.results.addItem(item)
        self.empty.setVisible(self.results.count() == 0)
        if self.results.count():
            self.results.setCurrentRow(0)

    def choose_current(self):
        item = self.results.currentItem()
        if item:
            self.chosen.emit(*item.data(Qt.ItemDataRole.UserRole))
            self.accept()

    def eventFilter(self, watched, event):  # noqa: N802
        if watched is self.search and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
                delta = 1 if event.key() == Qt.Key.Key_Down else -1
                row = min(max(0, self.results.currentRow() + delta), self.results.count() - 1)
                self.results.setCurrentRow(row)
                return True
        return super().eventFilter(watched, event)
