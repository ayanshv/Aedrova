"""One private-conversation picker, with stable identities and local search."""

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from aedrova.desktop.controls import AppDialog
from aedrova.desktop.dialogs import button, label


class ConversationPicker(AppDialog):
    def __init__(self, parent, people, buds):
        super().__init__(parent)
        self.setWindowTitle("Aedrova · New conversation")
        self.resize(440, 520)
        self.setMinimumSize(380, 400)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        layout.addWidget(label("Start a conversation", "title"))
        layout.addWidget(
            label(
                "Choose a teammate or a Bud. Bud chats are only visible to you.", "muted", wrap=True
            )
        )
        self.search = QLineEdit()
        self.search.setPlaceholderText("Find a person or Bud…")
        self.search.setAccessibleName("Find a conversation")
        layout.addWidget(self.search)
        self.list = QListWidget()
        self.list.setObjectName("ConversationRecipients")
        self.list.setAccessibleName("People and Buds")
        layout.addWidget(self.list, 1)
        self.empty = label("No matches. Try another name.", "muted", wrap=True)
        layout.addWidget(self.empty)
        actions = QHBoxLayout()
        cancel = button("Cancel", role="outline")
        cancel.clicked.connect(self.reject)
        self.start = button("Message", role="primary")
        self.start.clicked.connect(self.accept)
        actions.addWidget(cancel)
        actions.addWidget(self.start)
        layout.addLayout(actions)
        self.entries = [
            (
                "People",
                p["display_name"],
                "person",
                p["user_id"],
                p.get("email") or p["user_id"][:8],
            )
            for p in people
        ]
        self.entries += [
            ("Buds", b["name"], "bud", b["id"], b.get("role") or "AI teammate") for b in buds
        ]
        from aedrova.desktop.bud_art import appearance, sprite

        self.icons = {b["id"]: QIcon(sprite(appearance(b), b.get("color", ""))) for b in buds}
        self.list.setIconSize(QSize(42, 42))
        self.search.textChanged.connect(self.filter)
        self.list.currentItemChanged.connect(
            lambda *_: self.start.setEnabled(self.selection() is not None)
        )
        self.list.itemActivated.connect(lambda _: self.accept() if self.selection() else None)
        self.filter()
        self.search.setFocus()

    def filter(self, *_):
        selected = self.selection()
        self.list.clear()
        query = self.search.text().strip().casefold()
        section = None
        first = None
        for group, name, kind, identifier, detail in self.entries:
            if query and query not in (name + " " + detail).casefold():
                continue
            if section != group:
                header = QListWidgetItem(group)
                header.setFlags(Qt.ItemFlag.NoItemFlags)
                header.setSizeHint(QSize(0, 32))
                self.list.addItem(header)
                section = group
            item = QListWidgetItem(name + "\n" + detail)
            item.setData(Qt.ItemDataRole.UserRole, (kind, identifier))
            if kind == "bud":
                item.setIcon(self.icons[identifier])
            item.setSizeHint(QSize(0, 56))
            self.list.addItem(item)
            if first is None or selected == (kind, identifier):
                first = item
        if first is not None:
            self.list.setCurrentItem(first)
        self.empty.setVisible(first is None)
        self.start.setEnabled(first is not None)

    def selection(self):
        item = self.list.currentItem()
        value = item.data(Qt.ItemDataRole.UserRole) if item else None
        return tuple(value) if value else None


def choose_conversation(parent, people, buds):
    dialog = ConversationPicker(parent, people, buds)
    return dialog.selection() if dialog.exec() == QDialog.DialogCode.Accepted else None
