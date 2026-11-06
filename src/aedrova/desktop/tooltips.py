"""Borderless tooltips using the same painted depth as native dropdowns."""

from PySide6.QtCore import QEvent, QObject, QPoint, Qt, QTimer
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QAbstractItemView, QApplication, QLabel, QVBoxLayout, QWidget

from aedrova.desktop.popup_depth import paint_depth


class Tooltip(QWidget):
    def __init__(self):
        super().__init__(
            None,
            Qt.WindowType.ToolTip
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.NoDropShadowWindowHint,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setObjectName("DepthTooltip")
        self.setStyleSheet("QWidget#DepthTooltip { background: transparent; border: none; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 32)
        self.text = QLabel()
        self.text.setTextFormat(Qt.TextFormat.PlainText)
        self.text.setWordWrap(True)
        self.text.setMaximumWidth(340)
        layout.addWidget(self.text)

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        paint_depth(painter, self.rect(), self)


class Tooltips(QObject):
    def __init__(self, app):
        super().__init__(app)
        self.tip = Tooltip()
        self.owner = None
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide)
        app.installEventFilter(self)
        app.aboutToQuit.connect(self.tip.close)

    def hide(self):
        self.timer.stop()
        self.tip.hide()
        self.owner = None

    def eventFilter(self, watched, event):  # noqa: N802
        kind = event.type()
        if kind == QEvent.Type.ToolTip and isinstance(watched, QWidget):
            text = watched.toolTip()
            view = watched.parentWidget()
            if isinstance(view, QAbstractItemView) and watched is view.viewport():
                text = view.indexAt(event.pos()).data(Qt.ItemDataRole.ToolTipRole) or text
            if not text:
                self.hide()
                return False
            owner = watched
            while owner is not None and not hasattr(owner, "theme"):
                owner = owner.parentWidget()
            if owner is None:
                return False
            self.owner = watched
            self.tip.theme = owner.theme
            self.tip.setFont(watched.font())
            self.tip.text.setStyleSheet(
                f"background: transparent; border: none; color: {owner.theme.text};"
                "font-size: 12px; padding: 0;"
            )
            self.tip.text.setText(text)
            metrics = self.tip.text.fontMetrics()
            width = max((metrics.horizontalAdvance(line) for line in text.splitlines()), default=80)
            self.tip.text.setFixedWidth(min(340, max(80, width + 2)))
            self.tip.layout().activate()
            self.tip.adjustSize()
            screen = QApplication.screenAt(event.globalPos()) or watched.screen()
            bounds = screen.availableGeometry()
            point = event.globalPos() + QPoint(-12, 8)
            x = max(bounds.left(), min(point.x(), bounds.right() - self.tip.width() + 1))
            y = point.y()
            if y + self.tip.height() > bounds.bottom():
                y = event.globalPos().y() - self.tip.height() - 4
            self.tip.move(x, max(bounds.top(), y))
            self.tip.show()
            self.timer.start(
                max(1500, watched.toolTipDuration()) if watched.toolTipDuration() > 0 else 7000
            )
            event.accept()
            return True
        if self.owner is not None and (
            kind
            in (
                QEvent.Type.MouseButtonPress,
                QEvent.Type.KeyPress,
                QEvent.Type.Wheel,
                QEvent.Type.WindowDeactivate,
            )
            or watched is self.owner
            and kind in (QEvent.Type.Leave, QEvent.Type.Hide, QEvent.Type.Destroy)
        ):
            self.hide()
        return False


def install_tooltips():
    app = QApplication.instance()
    if not hasattr(app, "aedrova_tooltips"):
        app.aedrova_tooltips = Tooltips(app)
