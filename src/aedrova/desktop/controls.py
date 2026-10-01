"""Themed, keyboard-accessible choices, including macOS popup menus."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPainterPath, QPalette, QPen
from PySide6.QtWidgets import QComboBox, QFileDialog, QListView, QStyleFactory


class ChoiceBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._choice_style = QStyleFactory.create("Fusion")
        self.setStyle(self._choice_style)
        self.setView(QListView(self))
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMaxVisibleItems(8)
        self.view().setSpacing(3)
        self.view().setTextElideMode(Qt.TextElideMode.ElideRight)

    def paintEvent(self, event):  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(self.palette().color(QPalette.ColorRole.Text), 1.4))
        x, y = self.width() - 20, self.height() / 2
        path = QPainterPath()
        path.moveTo(x - 3.5, y - 1.5)
        path.lineTo(x, y + 2)
        path.lineTo(x + 3.5, y - 1.5)
        painter.drawPath(path)


def choose_project(parent, initial=""):
    return QFileDialog.getExistingDirectory(
        parent,
        "Choose your project folder",
        initial,
        QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontUseNativeDialog,
    )
