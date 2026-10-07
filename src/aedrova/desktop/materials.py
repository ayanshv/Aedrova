"""Qt-rendered frosted materials and spring motion. No browser or external assets."""

from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QEvent,
    QObject,
    QPoint,
    QPropertyAnimation,
    QRectF,
    Qt,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsBlurEffect,
    QGraphicsEffect,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGridLayout,
    QPushButton,
    QWidget,
)

from aedrova.desktop.theme import LIGHT


def system_font(size=14, weight=QFont.Weight.Normal, tracking=0.0):
    result = QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont)
    result.setPixelSize(size)
    result.setWeight(weight)
    result.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, tracking)
    return result


class Backdrop(QWidget):
    """A cached, genuinely blurred in-app backdrop, never a screen capture.

    Glass surfaces sample this artwork only. This is not the macOS Liquid Glass API
    and does not claim to refract other applications or content behind this window.
    """

    def __init__(self):
        super().__init__()
        self.theme = LIGHT
        self.reduced_transparency = False
        self._cache_key = None
        self.blurred = QImage()

    def invalidate(self):
        self._cache_key = None
        self.update()

    def texture(self):
        key = (self.size(), self.theme.name, self.reduced_transparency)
        if key == self._cache_key:
            return self.blurred
        self._cache_key = key
        # Quarter-resolution artwork, blurred once per size/theme change, not per frame.
        width, height = max(1, self.width() // 4), max(1, self.height() // 4)
        source = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        source.fill(QColor(self.theme.canvas))
        if not self.reduced_transparency:
            painter = QPainter(source)
            painter.setPen(Qt.PenStyle.NoPen)
            for x, y, radius, alpha, tint in (
                (width * 0.04, height * 0.90, width * 0.28, 25, "#83B7F5"),
                (width * 0.94, height * 0.06, width * 0.25, 24, "#88B0EF"),
                (width * 0.52, height * 0.98, width * 0.23, 16, "#80AEED"),
            ):
                glow = QRadialGradient(x, y, radius)
                color = QColor(tint)
                color.setAlpha(alpha if self.theme.name == "light" else alpha + 10)
                glow.setColorAt(0, color)
                color.setAlpha(0)
                glow.setColorAt(1, color)
                painter.setBrush(glow)
                painter.drawEllipse(QRectF(x - radius, y - radius, radius * 2, radius * 2))
            painter.end()
            scene = QGraphicsScene()
            item = QGraphicsPixmapItem(QPixmap.fromImage(source))
            blur = QGraphicsBlurEffect()
            blur.setBlurRadius(8)  # 32 logical px at the final scale.
            blur.setBlurHints(QGraphicsBlurEffect.BlurHint.QualityHint)
            item.setGraphicsEffect(blur)
            scene.addItem(item)
            result = QImage(source.size(), source.format())
            result.fill(QColor(self.theme.canvas))
            painter = QPainter(result)
            scene.render(painter, QRectF(0, 0, width, height), QRectF(0, 0, width, height))
            painter.end()
            source = result
        self.blurred = source
        return source

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        painter.drawImage(self.rect(), self.texture())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        # Wide ambient shadow, painted behind surfaces so children stay crisp.
        for panel in self.findChildren(GlassFrame):
            if panel.layer not in ("main", "sidebar") or not panel.isVisible():
                continue
            rect = QRectF(panel.mapTo(self, QPoint()), panel.size())
            for spread in range(9, 0, -3):
                painter.setBrush(QColor(0, 0, 0, 2 if self.theme.name == "light" else 3))
                painter.drawRoundedRect(
                    rect.adjusted(-spread, 5 - spread, spread, spread + 5), 24 + spread, 24 + spread
                )


class GlassFrame(QFrame):
    def __init__(self, *, layer="surface", radius=12):
        super().__init__()
        self.layer = layer
        self.radius = radius
        self.theme = LIGHT
        self.reduced_transparency = False
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(rect, self.radius, self.radius)
        painter.setClipPath(path)
        root = self.window().centralWidget() if hasattr(self.window(), "centralWidget") else None
        if isinstance(root, Backdrop) and not self.reduced_transparency:
            origin = self.mapTo(root, QPoint())
            texture = root.texture()
            sx, sy = (
                texture.width() / max(1, root.width()),
                texture.height() / max(1, root.height()),
            )
            source = QRectF(origin.x() * sx, origin.y() * sy, self.width() * sx, self.height() * sy)
            painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
            painter.drawImage(rect, texture, source)
        dark = self.theme.name == "dark"
        fill = QColor("#1C1C1E" if dark else "#FFFFFF")
        fill.setAlpha(255 if self.reduced_transparency else (232 if self.layer == "main" else 190))
        painter.fillPath(path, fill)
        if not self.reduced_transparency:
            sheen = QLinearGradient(0, 0, self.width() * 0.7, self.height())
            sheen.setColorAt(0, QColor(255, 255, 255, 8 if dark else 65))
            sheen.setColorAt(0.5, QColor(255, 255, 255, 0))
            painter.fillPath(path, sheen)
        painter.setClipping(False)
        edge = QLinearGradient(0, 0, 0, max(1, self.height()))
        edge.setColorAt(0, QColor(255, 255, 255, 38 if dark else 230))
        edge.setColorAt(0.35, QColor(255, 255, 255, 18) if dark else QColor(0, 0, 0, 14))
        edge.setColorAt(1, QColor(255, 255, 255, 22) if dark else QColor(0, 0, 0, 10))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(edge, 1))
        painter.drawRoundedRect(rect, self.radius, self.radius)


class ScaleEffect(QGraphicsEffect):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scale = 1.0

    def get_scale(self):
        return self._scale

    def set_scale(self, value):
        self._scale = value
        self.update()

    scale = Property(float, get_scale, set_scale)

    def boundingRectFor(self, rect):  # noqa: N802
        padding = max(5.0, rect.width() * 0.02, rect.height() * 0.02)
        return rect.adjusted(-padding, -padding, padding, padding)

    def draw(self, painter):
        offset = QPoint()
        pixmap = self.sourcePixmap(Qt.CoordinateSystem.LogicalCoordinates, offset)
        center = self.sourceBoundingRect().center()
        painter.save()
        painter.translate(center)
        painter.scale(self._scale, self._scale)
        painter.translate(-center)
        painter.drawPixmap(offset, pixmap)
        painter.restore()


class SpringMotion(QObject):
    def __init__(self, widget):
        super().__init__(widget)
        self.widget = widget
        self.effect = ScaleEffect(widget)
        widget.setGraphicsEffect(self.effect)
        self.animation = QPropertyAnimation(self.effect, b"scale", self)
        self.enabled = True
        widget.installEventFilter(self)
        widget.pressed.connect(lambda: self.animate(0.97, False))
        widget.released.connect(lambda: self.animate(1.015 if widget.underMouse() else 1.0, True))

    def animate(self, target, spring=False):
        self.animation.stop()
        if not self.enabled:
            self.effect.set_scale(1.0)
            return
        self.animation.setDuration(230 if spring else 150)
        self.animation.setStartValue(self.effect.get_scale())
        self.animation.setEndValue(target)
        self.animation.setEasingCurve(
            QEasingCurve.Type.OutBack if spring else QEasingCurve.Type.InOutSine
        )
        self.animation.start()

    def set_enabled(self, enabled):
        self.enabled = enabled
        if not enabled:
            self.animation.stop()
            self.effect.set_scale(1.0)

    def eventFilter(self, watched, event):  # noqa: N802
        if (
            event.type() == QEvent.Type.Enter
            and self.widget.isEnabled()
            and not self.widget.isDown()
        ):
            self.animate(1.015)
        elif event.type() == QEvent.Type.Leave and not self.widget.isDown():
            self.animate(1.0)
        elif event.type() == QEvent.Type.EnabledChange and not self.widget.isEnabled():
            self.animate(1.0)
        return False


class SpringButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.motion = SpringMotion(self)
        self.motion.set_enabled(not bool(QApplication.instance().property("reduceMotion")))


class DocumentTile(SpringButton):
    """A full-surface interactive document tile, not nested buttons inside a card."""

    def __init__(self, title, subtitle, number):
        super().__init__()
        self.title, self.subtitle, self.number = title, subtitle, number
        self.theme = LIGHT
        self.setAccessibleName(f"Open {title}")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(230)
        self.setMinimumWidth(220)

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = self.theme
        r = QRectF(self.rect()).adjusted(2, 2, -2, -2)
        painter.setPen(QColor(t.border))
        painter.setBrush(QColor(t.surface))
        painter.drawRoundedRect(r, 24, 24)
        painter.setPen(QColor(t.muted))
        painter.setFont(system_font(11, QFont.Weight.Medium))
        painter.drawText(QRectF(26, 23, 180, 18), f"{self.number}  /  REFERENCE")
        painter.setPen(QPen(QColor(t.secondary), 1.4))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(28, 60, 40, 48), 6, 6)
        for y, length in ((73, 21), (81, 21), (89, 14)):
            painter.drawLine(37, y, 37 + length, y)
        painter.setPen(QColor(t.text))
        painter.setFont(system_font(21, QFont.Weight.DemiBold, -0.5))
        title = painter.fontMetrics().elidedText(
            self.title, Qt.TextElideMode.ElideRight, self.width() - 54
        )
        painter.drawText(QRectF(26, 131, self.width() - 52, 30), title)
        painter.setPen(QColor(t.muted))
        painter.setFont(system_font(13))
        painter.drawText(
            QRectF(26, 167, self.width() - 80, 42), Qt.TextFlag.TextWordWrap, self.subtitle
        )
        painter.setPen(QColor(t.accent))
        painter.setFont(system_font(20))
        painter.drawText(QRectF(self.width() - 50, self.height() - 47, 24, 24), "↗")
        if self.hasFocus():
            painter.setPen(QPen(QColor(t.accent), 2))
            painter.drawRoundedRect(r.adjusted(2, 2, -2, -2), 22, 22)


class AdaptiveBento(QWidget):
    """Reflow into a single column at compact desktop widths."""

    def __init__(self, tiles, *, asymmetric=False):
        super().__init__()
        self.tiles = tiles
        self.asymmetric = asymmetric
        self.columns = None
        self.grid = QGridLayout(self)
        self.grid.setContentsMargins(0, 0, 0, 0)
        self.grid.setSpacing(20)
        self._reflow(1)

    def _reflow(self, columns):
        if columns == self.columns:
            return
        self.columns = columns
        for tile in self.tiles:
            self.grid.removeWidget(tile)
        self.grid.setColumnStretch(0, 3 if self.asymmetric and columns == 2 else 1)
        self.grid.setColumnStretch(1, 2 if self.asymmetric and columns == 2 else 0)
        if columns == 1:
            for row, tile in enumerate(self.tiles):
                self.grid.addWidget(tile, row, 0, 1, 2)
        elif self.asymmetric:
            self.grid.addWidget(self.tiles[0], 0, 0, 2, 1)
            self.grid.addWidget(self.tiles[1], 0, 1)
            self.grid.addWidget(self.tiles[2], 1, 1)
        else:
            for column, tile in enumerate(self.tiles):
                self.grid.addWidget(tile, 0, column)

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self._reflow(2 if self.width() >= (720 if self.asymmetric else 550) else 1)
