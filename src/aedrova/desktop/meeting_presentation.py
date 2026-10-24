"""Local presentation controls. No remote-control grants or background segmentation."""

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from aedrova.desktop.controls import AppDialog, ChoiceBox
from aedrova.desktop.dialogs import button, label
from aedrova.desktop.meeting_setup import FramePreview

COLORS = {"Blue": "#2979FF", "Coral": "#F26C54", "Gold": "#E0A028"}


def camera_look(image, *, monochrome=False, light=0):
    if not monochrome and not light:
        return image
    result = image.copy()
    if monochrome:
        result = result.convertToFormat(QImage.Format.Format_Grayscale8).convertToFormat(
            QImage.Format.Format_RGBA8888)
    if light:
        painter = QPainter(result)
        painter.setOpacity(max(0, min(25, light)) / 100)
        painter.fillRect(result.rect(), Qt.GlobalColor.white)
        painter.end()
    return result


def annotate(image, strokes):
    if not strokes:
        return image
    result = image.copy()
    painter = QPainter(result)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    for color, points in strokes[:64]:
        if not points:
            continue
        pen = QPen(QColor(color), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                   Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        path = QPainterPath(QPointF(points[0][0] * result.width(), points[0][1] * result.height()))
        for x, y in points[1:2048]:
            path.lineTo(x * result.width(), y * result.height())
        if len(points) == 1:
            painter.drawPoint(path.currentPosition())
        else:
            painter.drawPath(path)
    painter.end()
    return result


class SharingCanvas(FramePreview):
    point = Signal(object, bool)

    def __init__(self, text):
        super().__init__(text)
        self.drawing = False
        self.dragging = False

    def normalized(self, position):
        if self.image.isNull():
            return None
        size = self.image.size().scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
        if not size.width() or not size.height():
            return None
        left, top = (self.width() - size.width()) / 2, (self.height() - size.height()) / 2
        x, y = (position.x() - left) / size.width(), (position.y() - top) / size.height()
        return (x, y) if 0 <= x <= 1 and 0 <= y <= 1 else None

    def mousePressEvent(self, event):  # noqa: N802
        point = self.normalized(event.position())
        self.dragging = (self.drawing and event.button() == Qt.MouseButton.LeftButton
                         and point is not None)
        if self.dragging:
            self.point.emit(point, True)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):  # noqa: N802
        point = self.normalized(event.position())
        if self.dragging and self.drawing and point is not None:
            self.point.emit(point, False)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):  # noqa: N802
        self.dragging = False
        super().mouseReleaseEvent(event)


class MeetingPresentation(AppDialog):
    def __init__(self, call):
        super().__init__(call)
        self.setWindowTitle("Presentation · Aedrova")
        self.resize(520, 590)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        outer = layout
        outer.addWidget(label("Make the call yours.", "title"))
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(14)
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)
        layout.addWidget(label("These choices apply to this call. Camera adjustments and your "
                               "screen annotations are visible to the other participants.",
                               "muted", wrap=True))
        layout.addWidget(label("Your view", "section"))
        self.receive = QCheckBox("Receive participant video")
        self.receive.setChecked(call.receive_video)
        self.receive.toggled.connect(call.set_receive_video)
        layout.addWidget(self.receive)
        self.self_view = QCheckBox("Show my camera preview")
        self.self_view.setChecked(call.show_self)
        self.self_view.toggled.connect(call.set_self_view)
        layout.addWidget(self.self_view)
        self.mirror = QCheckBox("Mirror my camera preview only")
        self.mirror.setChecked(call.mirror_preview)
        self.mirror.toggled.connect(lambda checked: setattr(call, "mirror_preview", checked))
        layout.addWidget(self.mirror)
        layout.addWidget(label("Camera", "section"))
        self.look = ChoiceBox(self)
        self.look.addItems(["Natural", "Monochrome"])
        self.look.setCurrentIndex(int(call.monochrome))
        self.look.setAccessibleName("Camera color treatment")
        self.look.currentIndexChanged.connect(lambda index: setattr(call, "monochrome", index == 1))
        layout.addWidget(self.look)
        self.light_label = label("Soft light · " + str(call.soft_light) + "%", "muted")
        layout.addWidget(self.light_label)
        self.light = QSlider(Qt.Orientation.Horizontal)
        self.light.setRange(0, 25)
        self.light.setValue(call.soft_light)
        self.light.setAccessibleName("Camera soft light strength")
        self.light.valueChanged.connect(lambda value: self.lighting(call, value))
        layout.addWidget(self.light)
        layout.addWidget(label("Your shared screen", "section"))
        self.draw = QCheckBox("Draw on my shared screen")
        self.draw.setChecked(call.annotating)
        self.draw.toggled.connect(call.set_annotating)
        layout.addWidget(self.draw)
        row = QHBoxLayout()
        self.color = ChoiceBox(self)
        for name, value in COLORS.items():
            self.color.addItem(name, value)
        self.color.setCurrentIndex(self.color.findData(call.annotation_color))
        self.color.setAccessibleName("Screen annotation color")
        self.color.currentIndexChanged.connect(
            lambda _: setattr(call, "annotation_color", self.color.currentData()))
        row.addWidget(self.color)
        clear = button("Clear drawings", role="outline")
        clear.clicked.connect(call.clear_annotations)
        row.addWidget(clear)
        layout.addLayout(row)
        layout.addWidget(label("Draw in the large preview while sharing your own screen. "
                               "Pause sharing stops capture and removes the shared track; "
                               "resume requests capture again. Audio stays connected.",
                               "muted", wrap=True))
        done = button("Done", role="primary")
        done.clicked.connect(self.accept)
        outer.addWidget(done)
        call.finished.connect(self.reject)

    def lighting(self, call, value):
        call.soft_light = value
        self.light_label.setText("Soft light · " + str(value) + "%")
