"""Themed, keyboard-accessible choices, including macOS popup menus."""

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter, QPainterPath, QPalette, QPen, QRegion
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QListView,
    QMenu,
    QProxyStyle,
    QStyle,
    QStyleFactory,
    QVBoxLayout,
)


def _round_popup(widget):
    """Clip the native popup window too; CSS only rounds its painted content."""
    path = QPainterPath()
    path.addRoundedRect(QRectF(widget.rect()), 16, 16)
    widget.setMask(QRegion(path.toFillPolygon().toPolygon()))


class _PopupStyle(QProxyStyle):
    """Qt paints the combo's private container as a menu even with NoFrame."""

    def pixelMetric(self, metric, option=None, widget=None):  # noqa: N802
        if metric == QStyle.PixelMetric.PM_MenuPanelWidth:
            return 0
        return super().pixelMetric(metric, option, widget)

    def drawPrimitive(self, element, option, painter, widget=None):  # noqa: N802
        if widget is not None and widget.objectName() == "ChoicePopup" and element in (
            QStyle.PrimitiveElement.PE_PanelMenu,
            QStyle.PrimitiveElement.PE_FrameWindow,
        ):
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(widget.palette().brush(QPalette.ColorRole.Base))
            painter.drawRoundedRect(QRectF(option.rect), 16, 16)
            return
        super().drawPrimitive(element, option, painter, widget)


class AppDialog(QDialog):
    """Keep child windows in the app's palette, including subsequent theme changes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_WindowPropagation, True)
        if parent is not None:
            self.setFont(parent.font())

    def set_loading(self, target, active, kind="form"):
        from aedrova.desktop.loading import set_loading

        set_loading(self, target, active, kind)


class ChoiceBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._choice_style = QStyleFactory.create("Fusion")
        self._popup_style = _PopupStyle(QStyleFactory.create("Fusion"))
        self.setStyle(self._choice_style)
        self.setView(QListView(self))
        self.view().setObjectName("ChoiceList")
        self.view().setFrameShape(QFrame.Shape.NoFrame)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMaxVisibleItems(8)
        self.view().setSpacing(3)
        self.view().setTextElideMode(Qt.TextElideMode.ElideRight)
        self.setMinimumHeight(44)

    def showPopup(self):  # noqa: N802
        popup = self.view().window()
        popup.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        popup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        super().showPopup()
        # Qt owns a separate popup frame outside the list view. Remove its
        # platform outline as well as the list's frame, in both themes.
        popup = self.view().window()
        popup.setObjectName("ChoicePopup")
        popup.setStyle(self._popup_style)
        popup.setContentsMargins(0, 0, 0, 0)
        if isinstance(popup, QFrame):
            popup.setFrameShape(QFrame.Shape.NoFrame)
            popup.setLineWidth(0)
        popup.style().unpolish(popup)
        popup.style().polish(popup)
        _round_popup(popup)

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
        QFileDialog.Option.ShowDirsOnly,
    )


class AppMenu(QMenu):
    """Use the app's styled popup renderer rather than macOS native menu fallbacks."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._menu_style = QStyleFactory.create("Fusion")
        self.setStyle(self._menu_style)
        self.setObjectName("AppMenu")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMinimumWidth(220)
        self.setSeparatorsCollapsible(True)
        self.setAttribute(Qt.WidgetAttribute.WA_WindowPropagation, True)

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        _round_popup(self)

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        _round_popup(self)


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
