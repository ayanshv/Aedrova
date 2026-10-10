"""Keyboard-accessible discrete sliders with semantic values, not raw AI parameters."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QSlider, QVBoxLayout, QWidget


class ChoiceSlider(QWidget):
    currentIndexChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(5)
        self.caption = QLabel()
        self.caption.setWordWrap(True)
        self.caption.setProperty("role", "muted")
        column.addWidget(self.caption)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(1)
        self.slider.setSingleStep(1)
        self.slider.valueChanged.connect(self.changed)
        self.setFocusProxy(self.slider)
        column.addWidget(self.slider)
        ends = QHBoxLayout()
        self.first, self.last = QLabel(), QLabel()
        for text in (self.first, self.last):
            text.setProperty("role", "muted")
        ends.addWidget(self.first)
        ends.addStretch()
        ends.addWidget(self.last)
        column.addLayout(ends)
        self.setMinimumHeight(68)

    def addItem(self, text, value=None):  # noqa: N802
        self.items.append((text, text if value is None else value))
        self.slider.setMaximum(len(self.items) - 1)
        self.changed(self.slider.value())

    def changed(self, index):
        if not self.items:
            return
        self.caption.setText(self.items[index][0])
        self.first.setText(self.items[0][0].split(" · ")[0])
        self.last.setText(self.items[-1][0].split(" · ")[0])
        self.slider.setAccessibleDescription(self.items[index][0])
        self.currentIndexChanged.emit(index)

    def currentData(self):  # noqa: N802
        return self.items[self.slider.value()][1] if self.items else None

    def currentText(self):  # noqa: N802
        return self.items[self.slider.value()][0] if self.items else ""

    def findData(self, value):  # noqa: N802
        return next((i for i, (_, data) in enumerate(self.items) if data == value), -1)

    def setCurrentIndex(self, index):  # noqa: N802
        if 0 <= index < len(self.items):
            self.slider.setValue(index)

    def count(self):
        return len(self.items)

    def setAccessibleName(self, name):  # noqa: N802
        super().setAccessibleName(name)
        self.slider.setAccessibleName(name)
