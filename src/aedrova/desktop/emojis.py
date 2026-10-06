"""Offline searchable Unicode emoji picker shared by composer and reactions."""

import json
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QFrame, QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout

from aedrova.desktop.controls import AppDialog

QUICK_EMOJI = ("👍", "❤️", "😂", "🎉", "👀")


@lru_cache(maxsize=1)
def catalog():
    return json.loads((Path(__file__).parent / "assets/emoji.json").read_text())


class EmojiPicker(AppDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose an emoji")
        self.resize(440, 480)
        self.selected = ""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search emoji, e.g. heart or thumbs up")
        self.search.setAccessibleName("Search all emoji")
        layout.addWidget(self.search)
        self.grid = QListWidget()
        self.grid.setObjectName("EmojiGrid")
        self.grid.setFrameShape(QFrame.Shape.NoFrame)
        self.grid.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.grid.setViewMode(QListWidget.ViewMode.IconMode)
        self.grid.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.grid.setMovement(QListWidget.Movement.Static)
        self.grid.setGridSize(QSize(52, 48))
        self.grid.setWordWrap(False)
        self.grid.setAccessibleName("Emoji results")
        layout.addWidget(self.grid)
        self.search.textChanged.connect(self.filter)
        self.grid.itemClicked.connect(self.choose)
        self.grid.itemActivated.connect(self.choose)
        self.filter("")

    def filter(self, query):
        self.grid.clear()
        words = query.casefold().split()
        for emoji, name, group in catalog():
            if all(w in (name + " " + group + " " + emoji).casefold() for w in words):
                item = QListWidgetItem(emoji)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setToolTip(name)
                item.setData(Qt.ItemDataRole.UserRole, emoji)
                self.grid.addItem(item)

    def choose(self, item):
        self.selected = item.data(Qt.ItemDataRole.UserRole)
        self.accept()


def pick_emoji(parent):
    picker = EmojiPicker(parent)
    return picker.selected if picker.exec() else ""
