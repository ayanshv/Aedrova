"""Soft native popup depth, painted inside transparent, unclipped window margins."""

from PySide6.QtCore import QEvent, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPalette
from PySide6.QtWidgets import QApplication, QWidget

PADDING = (24, 20, 24, 28)


def surface_color(widget):
    owner = widget
    while owner is not None:
        theme = getattr(owner, "theme", None)
        if theme is not None and hasattr(theme, "elevated"):
            return QColor(theme.bg if theme.name == "light" else theme.elevated)
        owner = owner.parentWidget()
    # QComboBox's Fusion style resets ToolTipBase to system yellow. Resolve the
    # owning surface rather than using that unrelated native tooltip palette.
    owner = widget.parentWidget()
    while owner is not None:
        color = owner.palette().color(QPalette.ColorRole.Window)
        if color.alpha():
            return color
        owner = owner.parentWidget()
    return QApplication.palette().color(QPalette.ColorRole.Window)


def paint_depth(painter, rect, widget):
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    surface = QRectF(rect).adjusted(20, 16, -20, -24)
    fill = surface_color(widget)
    dark = fill.lightnessF() < 0.5
    painter.setPen(Qt.PenStyle.NoPen)
    # Finite feathered layers avoid a live blur effect and its clipped bounds.
    for spread in range(16, 0, -1):
        alpha = (5 if dark else 3) * (1 - spread / 17) ** 1.6
        painter.setBrush(QColor(0, 0, 0, round(alpha)))
        painter.drawRoundedRect(
            surface.translated(0, 5).adjusted(-spread, -spread, spread, spread),
            14 + spread,
            14 + spread,
        )
    painter.setBrush(fill)
    painter.drawRoundedRect(surface, 14, 14)


class PopupDepth(QWidget):
    """Background for Qt's private combo container; input stays with its list."""

    def __init__(self, popup):
        super().__init__(popup)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        popup.installEventFilter(self)
        self.setGeometry(popup.rect())

    def eventFilter(self, watched, event):  # noqa: N802
        if event.type() in (QEvent.Type.Resize, QEvent.Type.PaletteChange):
            self.setGeometry(watched.rect())
            self.update()
        return False

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        paint_depth(painter, self.rect(), self.parentWidget())
