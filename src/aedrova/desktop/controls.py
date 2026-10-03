"""Themed, keyboard-accessible choices, including macOS popup menus."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QPainterPath, QPalette, QPen
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QListView,
    QMenu,
    QStyleFactory,
    QVBoxLayout,
)


class AppDialog(QDialog):
    """Keep child windows in the app's palette, including subsequent theme changes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_WindowPropagation, True)
        if parent is not None:
            self.setFont(parent.font())


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
        self.setMinimumHeight(44)

    def paintEvent(self, event):  # noqa: N802
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        group = QPalette.ColorGroup.Active if self.isEnabled() else QPalette.ColorGroup.Disabled
        painter.setPen(QPen(self.palette().color(group, QPalette.ColorRole.Text), 1.4))
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


class AppMenu(QMenu):
    """Use the app's styled popup renderer rather than macOS native menu fallbacks."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._menu_style = QStyleFactory.create("Fusion")
        self.setStyle(self._menu_style)
        self.setObjectName("AppMenu")
        self.setMinimumWidth(220)
        self.setSeparatorsCollapsible(True)
        self.setAttribute(Qt.WidgetAttribute.WA_WindowPropagation, True)


def choose_teammate(parent, names):
    from aedrova.desktop.dialogs import button, label

    dialog = AppDialog(parent)
    dialog.setWindowTitle("Aedrova · Direct message")
    dialog.setMinimumWidth(380)
    layout = QVBoxLayout(dialog)
    layout.setContentsMargins(24, 24, 24, 24)
    layout.setSpacing(16)
    layout.addWidget(label("Start a conversation", "title"))
    choice = ChoiceBox(dialog)
    choice.setAccessibleName("Choose a teammate")
    choice.addItems(names)
    layout.addWidget(choice)
    actions = QHBoxLayout()
    cancel = button("Cancel", role="outline")
    cancel.clicked.connect(dialog.reject)
    start = button("Message", role="primary")
    start.clicked.connect(dialog.accept)
    actions.addWidget(cancel)
    actions.addWidget(start)
    layout.addLayout(actions)
    accepted = dialog.exec() == QDialog.DialogCode.Accepted
    return choice.currentText(), accepted
