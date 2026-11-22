"""Themed, keyboard-accessible choices, including macOS popup menus."""

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QPainter, QPainterPath, QPalette, QPen, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListView,
    QMenu,
    QProxyStyle,
    QStyle,
    QStyleFactory,
    QVBoxLayout,
)


class _PopupStyle(QProxyStyle):
    """Qt paints the combo's private container as a menu even with NoFrame."""

    def pixelMetric(self, metric, option=None, widget=None):  # noqa: N802
        if metric == QStyle.PixelMetric.PM_MenuPanelWidth:
            return 0
        return super().pixelMetric(metric, option, widget)

    def drawPrimitive(self, element, option, painter, widget=None):  # noqa: N802
        if (
            widget is not None
            and widget.objectName() == "ChoicePopup"
            and element
            in (
                QStyle.PrimitiveElement.PE_PanelMenu,
                QStyle.PrimitiveElement.PE_FrameWindow,
            )
        ):


            return
        super().drawPrimitive(element, option, painter, widget)


class AppDialog(QDialog):
    """Keep child windows in the app's palette, including subsequent theme changes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_WindowPropagation, True)
        if parent is not None:
            self.setFont(parent.font())

    def showEvent(self, event):  # noqa: N802
        first = not getattr(self, "shown_once", False)
        self.shown_once = True
        super().showEvent(event)
        if first:
            from aedrova.desktop.motion import BASE, appear_window

            appear_window(
                self, getattr(self, "appear_ms", BASE + 80), rise=getattr(self, "appear_rise", 10)
            )

    def set_loading(self, target, active, kind="form"):
        from aedrova.desktop.loading import set_loading

        set_loading(self, target, active, kind)


class ChoiceBox(QComboBox):
    fit_popup_labels = False

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

    def setCurrentText(self, text):  # noqa: N802

        for index, pair in enumerate(self.property("i18n_items") or []):
            if pair[0] == text:
                self.setCurrentIndex(index)
                return
        super().setCurrentText(text)

    def showPopup(self):  # noqa: N802
        from aedrova.desktop.popup_depth import PADDING, PopupDepth

        popup = self.view().window()
        popup.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        popup.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, True)
        popup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        popup.setObjectName("ChoicePopup")
        popup.setStyle(self._popup_style)
        popup.setPalette(self.palette())
        popup.clearMask()
        popup.setContentsMargins(0, 0, 0, 0)
        layout = popup.layout()
        if layout:
            layout.setContentsMargins(0, 0, 0, 0)
        if isinstance(popup, QFrame):
            popup.setFrameShape(QFrame.Shape.NoFrame)
            popup.setLineWidth(0)
        self.view().viewport().setAutoFillBackground(False)
        if not hasattr(self, "_depth"):
            self._depth = PopupDepth(popup)
        self._depth.hide()
        super().showPopup()
        geometry = popup.geometry()
        left, top, right, bottom = PADDING
        if layout:
            layout.setContentsMargins(left, top, right, bottom)
        else:
            popup.setContentsMargins(left, top, right, bottom)
        geometry.adjust(-left, -top, right, bottom)
        available = popup.screen().availableGeometry()
        width = geometry.width()
        if self.fit_popup_labels:
            view = self.view()
            content_width = view.sizeHintForColumn(0) + 2 * (view.spacing() + view.frameWidth())
            if self.count() > self.maxVisibleItems():
                content_width += view.verticalScrollBar().sizeHint().width()
            width = max(width, content_width + left + right)
        geometry.setWidth(min(width, available.width()))
        geometry.setHeight(min(geometry.height(), available.height()))
        geometry.moveLeft(
            max(available.left(), min(geometry.left(), available.right() - geometry.width() + 1))
        )
        geometry.moveTop(
            max(available.top(), min(geometry.top(), available.bottom() - geometry.height() + 1))
        )
        popup.setGeometry(geometry)
        self._depth.setGeometry(popup.rect())
        self._depth.show()
        self._depth.lower()

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


class PermissionChoice(ChoiceBox):
    fit_popup_labels = True

    def __init__(self):
        super().__init__()
        from aedrova.agents.permissions import MODES
        from aedrova.desktop.icons import icon

        self.setObjectName("AgentPermissions")
        self.setAccessibleName("Aedrova agent permissions")
        self.setSizeAdjustPolicy(self.SizeAdjustPolicy.AdjustToContents)
        self.setProperty("permissionMode", "ask")
        names = ["permission_ask", "permission_auto", "permission_full"]
        self.setProperty("itemIconNames", names)
        self.setIconSize(QSize(16, 16))
        color = self.palette().windowText().color().name()
        for name, (value, (title, description)) in zip(names, MODES.items(), strict=True):
            self.addItem(icon(name, color), title, value)
            self.setItemData(self.count() - 1, description, Qt.ItemDataRole.ToolTipRole)
        self.setToolTip(MODES["ask"][1])

    def sizeHint(self):  # noqa: N802
        size = super().sizeHint()
        label_width = max(
            self.fontMetrics().horizontalAdvance(self.itemText(i)) for i in range(self.count())
        )
        size.setWidth(max(size.width(), label_width + self.iconSize().width() + 58))
        return size

    def minimumSizeHint(self):  # noqa: N802
        return self.sizeHint()


class CodingProviderChoice(QFrame):
    """Aedrova identity with the existing provider-setting interface."""

    currentIndexChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        from aedrova.desktop.brand import brand_image

        self.setAccessibleName("Aedrova agent")
        self.setMinimumHeight(44)
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 8, 0, 8)
        row.setSpacing(10)
        mark = QLabel(self)
        mark.setPixmap(QPixmap.fromImage(brand_image()).scaled(
            28, 28, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        ))
        row.addWidget(mark)
        row.addWidget(QLabel("Aedrova", self))
        row.addStretch(1)

    def currentIndex(self):
        return 0

    def currentData(self):
        return "codex"

    def currentText(self):
        return "Aedrova"

    def findData(self, value):
        return 0 if value in {"codex", "claude_code", "auto"} else -1

    def setCurrentIndex(self, index):
        pass


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
        self.setWindowFlag(Qt.WindowType.NoDropShadowWindowHint, True)
        self.setMinimumWidth(220)
        self.setSeparatorsCollapsible(True)
        self.setAttribute(Qt.WidgetAttribute.WA_WindowPropagation, True)

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self.clearMask()

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self.clearMask()

    def paintEvent(self, event):  # noqa: N802
        from aedrova.desktop.popup_depth import paint_depth

        painter = QPainter(self)
        paint_depth(painter, self.rect(), self)
        painter.end()
        super().paintEvent(event)


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
    from aedrova.localization import choice_source

    return choice_source(choice), accepted
