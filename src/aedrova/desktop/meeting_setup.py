"""Themed local preflight. Opening it never enables a device or joins a call."""

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QProgressBar,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from aedrova.desktop.brand import BrandMark
from aedrova.desktop.controls import AppDialog, ChoiceBox
from aedrova.desktop.dialogs import button, label
from aedrova.desktop.theme import palette
from aedrova.meetings.devices import DeviceCheck


class FramePreview(QWidget):
    def __init__(self, text, parent=None, *, fill=False):
        super().__init__(parent)
        self.text, self.image = text, QImage()
        self.fill = fill
        self.setMinimumHeight(160)
        self.setAccessibleName(text)

    def sizeHint(self):  # noqa: N802
        return QSize(320, 180)

    def display(self, image):
        self.image = image
        self.update()

    def clear(self):
        self.image = QImage()
        self.update()

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Stylesheet palettes may substitute AlternateBase on nested scroll widgets.
        owner = self.window().parentWidget()
        theme = getattr(owner, 'theme', None)
        background = QColor(theme.surface) if theme else self.palette().color(
            QPalette.ColorRole.AlternateBase)
        canvas = QColor(theme.bg) if theme else self.palette().color(QPalette.ColorRole.Window)
        painter.fillRect(self.rect(), canvas)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(background)
        painter.drawRoundedRect(self.rect(), 10, 10)
        if self.image.isNull():
            painter.setPen(self.palette().color(QPalette.ColorRole.PlaceholderText))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.text)
            return
        clip = QPainterPath()
        clip.addRoundedRect(self.rect(), 10, 10)
        painter.setClipPath(clip)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        mode = Qt.AspectRatioMode.KeepAspectRatioByExpanding if self.fill else (
            Qt.AspectRatioMode.KeepAspectRatio)
        size = self.image.size().scaled(self.size(), mode)
        x, y = (self.width() - size.width()) // 2, (self.height() - size.height()) // 2
        from PySide6.QtCore import QRect
        painter.drawImage(QRect(x, y, size.width(), size.height()), self.image)


class MeetingSetup(AppDialog):
    def __init__(self, parent=None, *, check=None):
        super().__init__(parent)
        if parent is not None and hasattr(parent, 'theme'):
            self.setPalette(palette(parent.theme))
        self.setWindowTitle('Aedrova · Meeting setup')
        self.setMinimumSize(560, 580)
        self.resize(760, 810)
        self.check = check or DeviceCheck(self)
        self.choices, self.actions, self.states = {}, {}, {}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)
        heading = QHBoxLayout()
        heading.addWidget(BrandMark(46))
        heading.addWidget(label('Make yourself comfortable.', 'title'), 1)
        layout.addLayout(heading)
        layout.addWidget(label('Check your devices before your next conversation.', 'muted'))
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        content = QWidget()
        content.setObjectName("AccountPage")
        scroll.setWidget(content)
        scroll.viewport().setAutoFillBackground(False)
        body = QVBoxLayout(content)
        body.setContentsMargins(0, 0, 8, 0)
        body.setSpacing(16)
        previews = QGridLayout()
        self.camera_preview = FramePreview('Camera is off', fill=True)
        self.screen_preview = FramePreview('Screen preview is off')
        previews.addWidget(self.camera_preview, 0, 0)
        previews.addWidget(self.screen_preview, 0, 1)
        body.addLayout(previews)
        self.level = QProgressBar()
        self.level.setRange(0, 100)
        self.level.setValue(0)
        self.level.setTextVisible(False)
        self.level.setFixedHeight(6)
        self.level.setAccessibleName('Microphone input level')
        for kind, title, action in [('camera', 'Camera', 'Preview camera'),
                                    ('microphone', 'Microphone', 'Check microphone'),
                                    ('speaker', 'Speakers or headphones', 'Play test sound'),
                                    ('screen', 'Screen', 'Preview screen')]:
            body.addWidget(label(title, 'muted'))
            row = QHBoxLayout()
            choice = ChoiceBox(self)
            choice.setAccessibleName('Meeting ' + title.lower())
            control = button(action, role='outline')
            control.setMinimumWidth(155)
            control.setAutoDefault(False)
            row.addWidget(choice, 1)
            row.addWidget(control)
            body.addLayout(row)
            self.choices[kind], self.actions[kind] = choice, control
            control.clicked.connect(lambda checked=False, kind=kind: self.toggle(kind))
            choice.currentIndexChanged.connect(lambda _, kind=kind: self.check.stop(kind))
            if kind == 'microphone':
                body.addWidget(self.level)
        body.addWidget(label('Local device check · nothing is shared or saved.',
                             'muted', wrap=True))
        body.addWidget(label('Calls and consented transcription are being connected. '
                             'This screen checks your devices; it does not join a meeting.',
                             'muted', wrap=True))
        body.addStretch()
        layout.addWidget(scroll, 1)
        self.status = label('All devices are off. Choose a check when you’re ready.',
                            'muted', wrap=True)
        self.status.setAccessibleName('Meeting setup status')
        layout.addWidget(self.status)
        footer = QHBoxLayout()
        stop = button('Stop all', role='outline')
        stop.clicked.connect(self.check.stop_all)
        footer.addWidget(stop)
        footer.addStretch()
        done = button('Done', role='primary')
        done.setAutoDefault(False)
        done.clicked.connect(self.accept)
        footer.addWidget(done)
        layout.addLayout(footer)
        self.check.frame.connect(self.frame)
        self.check.level.connect(self.level.setValue)
        self.check.changed.connect(self.state_changed)
        self.check.problem.connect(self.status.setText)
        self.check.inventory_changed.connect(self.populate)
        self.finished.connect(self.check.close)
        QApplication.instance().aboutToQuit.connect(self.check.close)
        self.populate()

    def populate(self):
        for kind, choice in self.choices.items():
            choice.blockSignals(True)
            choice.clear()
            for device in self.check.backend.list(kind):
                description = device.name() if kind == 'screen' else device.description()
                choice.addItem(description or kind.capitalize(), device)
            available = choice.count() > 0
            if not available:
                choice.addItem('No device available', None)
            choice.setEnabled(available)
            self.actions[kind].setEnabled(available)
            choice.blockSignals(False)

    def toggle(self, kind):
        if self.states.get(kind) in {'active', 'starting', 'permission'}:
            self.check.stop(kind)
            return
        device = self.choices[kind].currentData()
        if device is not None:
            self.status.setText('Checking ' + kind + '…')
            self.check.start(kind, device)

    def frame(self, kind, image):
        if kind == 'camera':
            self.camera_preview.display(image)
        elif kind == 'screen':
            self.screen_preview.display(image)

    def state_changed(self, kind, state):
        self.states[kind] = state
        control = self.actions.get(kind)
        if not control:
            return
        names = {'camera': 'Preview camera', 'microphone': 'Check microphone',
                 'speaker': 'Play test sound', 'screen': 'Preview screen'}
        control.setText('Cancel request' if state == 'permission' else
                        ('Stop ' + kind if state in {'active', 'starting'} else names[kind]))
        control.setAccessibleName(control.text())
        self.choices[kind].setEnabled(state == 'off' and
                                     self.choices[kind].currentData() is not None)
        if state == 'off':
            if kind == 'camera':
                self.camera_preview.clear()
            elif kind == 'screen':
                self.screen_preview.clear()
        if state == 'starting':
            self.status.setText('Starting ' + kind + ' preview…')
        elif state == 'active':
            self.status.setText(kind.capitalize() + ' check is active · local only.')
        elif not any(value != 'off' for value in self.states.values()):
            self.status.setText('All devices are off.')

    def hideEvent(self, event):  # noqa: N802
        self.check.close()
        super().hideEvent(event)


def open_meeting_setup(window):
    dialog = getattr(window, 'meeting_setup', None)
    if dialog and dialog.isVisible():
        dialog.raise_()
        dialog.activateWindow()
        return
    window.meeting_setup = MeetingSetup(window)
    account = getattr(window, 'account_dialog', None)
    if account:
        account.session_closed.connect(window.meeting_setup.reject)
    window.meeting_setup.open()
