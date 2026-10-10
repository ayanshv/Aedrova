"""Explicit local device access; no network, recorder or file output."""

from dataclasses import dataclass

from PySide6.QtCore import (
    QBuffer,
    QCameraPermission,
    QIODevice,
    QMicrophonePermission,
    QObject,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtMultimedia import (
    QAudioSink,
    QAudioSource,
    QCamera,
    QMediaCaptureSession,
    QMediaDevices,
    QScreenCapture,
    QVideoSink,
)
from PySide6.QtWidgets import QApplication

from aedrova.meetings.audio import audio_level, speaker_tone
from aedrova.meetings.permissions import screen_access


@dataclass
class Capture:
    source: object
    resources: tuple = ()

    def stop(self):
        try:
            self.source.stop()
        finally:
            for resource in self.resources:
                if isinstance(resource, QBuffer):
                    resource.close()
            for resource in (self.source, *self.resources):
                resource.deleteLater()


class NativeDevices:
    def __init__(self, parent):
        self.parent = parent
        self.inventory = QMediaDevices(parent)

    def list(self, kind):
        return {'camera': QMediaDevices.videoInputs, 'microphone': QMediaDevices.audioInputs,
                'speaker': QMediaDevices.audioOutputs,
                'screen': QApplication.screens}[kind]()

    def permission(self, kind, callback):
        if kind == 'screen':
            callback(screen_access())
            return
        if kind not in {'camera', 'microphone'}:
            callback(True)
            return
        permission = QCameraPermission() if kind == 'camera' else QMicrophonePermission()
        app = QApplication.instance()
        state = app.checkPermission(permission)
        if state == Qt.PermissionStatus.Undetermined:
            app.requestPermission(permission, self.parent,
                                  lambda result: callback(result.status()
                                                          == Qt.PermissionStatus.Granted))
        else:
            callback(state == Qt.PermissionStatus.Granted)

    def start(self, kind, device, frame, level, failed):
        if kind in {'camera', 'screen'}:
            source = (QCamera(device, self.parent) if kind == 'camera'
                      else QScreenCapture(self.parent))
            session, sink = QMediaCaptureSession(self.parent), QVideoSink(self.parent)
            if kind == 'camera':
                session.setCamera(source)
            else:
                source.setScreen(device)
                session.setScreenCapture(source)
            session.setVideoSink(sink)
            def received(value):
                image = value.toImage()
                if not image.isNull():
                    frame(image.copy())

            sink.videoFrameChanged.connect(received)
            source.errorOccurred.connect(lambda *_: failed())
            handle = Capture(source, (sink, session))
            try:
                source.start()
                if source.error().value:
                    raise RuntimeError('Video capture could not start')
            except Exception:
                handle.stop()
                raise
            return handle
        fmt = device.preferredFormat()
        if not device.isFormatSupported(fmt):
            raise RuntimeError('Unsupported audio device format')
        if kind == 'microphone':
            source = QAudioSource(device, fmt, self.parent)
            source.setBufferSize(65536)
            handle = Capture(source)
            try:
                io = source.start()
                if io is None or source.error().value:
                    raise RuntimeError('Microphone could not start')
            except Exception:
                handle.stop()
                raise
            io.readyRead.connect(lambda: level(audio_level(bytes(io.read(65536)),
                                                           fmt.sampleFormat().name)))
            source.stateChanged.connect(lambda _: failed() if source.error().value else None)
            return Capture(source)
        tone = speaker_tone(fmt.sampleRate(), fmt.channelCount(), fmt.sampleFormat().name)
        source, buffer = QAudioSink(device, fmt, self.parent), QBuffer(self.parent)
        buffer.setData(tone)
        buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        source.setVolume(.5)
        source.stateChanged.connect(lambda _: failed() if source.error().value else None)
        handle = Capture(source, (buffer,))
        try:
            source.start(buffer)
            if source.error().value:
                raise RuntimeError('Speaker could not start')
        except Exception:
            handle.stop()
            raise
        return handle


class DeviceCheck(QObject):
    frame = Signal(str, object)
    level = Signal(int)
    changed = Signal(str, str)
    problem = Signal(str)
    inventory_changed = Signal()

    def __init__(self, parent=None, *, backend=None):
        super().__init__(parent)
        self.backend = backend or NativeDevices(self)
        self.handles = {}
        self.epochs = {}
        self.watchdogs = {}
        self.closed = False
        self.speaker_timer = QTimer(self)
        self.speaker_timer.setSingleShot(True)
        self.speaker_timer.timeout.connect(lambda: self.stop('speaker'))
        inventory = getattr(self.backend, 'inventory', None)
        if inventory:
            for signal in (inventory.videoInputsChanged, inventory.audioInputsChanged,
                           inventory.audioOutputsChanged):
                signal.connect(self.devices_changed)
        QApplication.instance().aboutToQuit.connect(self.close)

    def devices_changed(self):
        self.stop_all()
        self.inventory_changed.emit()

    def start(self, kind, device):
        if kind not in {'camera', 'microphone', 'speaker', 'screen'}:
            raise ValueError('Unknown device check')
        if self.closed:
            return
        self.stop(kind)
        epoch = self.epochs[kind]
        self.changed.emit(kind, 'permission')

        def current():
            return not self.closed and self.epochs.get(kind) == epoch

        def failed(*, denied=False):
            if current():
                self.stop(kind)
                if kind == 'screen' and denied:
                    message = (
                        'macOS has not granted screen access to this Aedrova build. In '
                        'System Settings → Privacy & Security → Screen & System Audio Recording, '
                        'remove the old Aedrova entry and add this app again, then quit and '
                        'reopen it. Nothing is being shared.')
                elif kind == 'screen':
                    message = ('Screen capture could not deliver a frame. Screen permission '
                               'was granted; stop the preview and retry. Nothing is being shared.')
                else:
                    message = (f'{kind.capitalize()} unavailable. Check the device and '
                               'macOS System Settings → Privacy & Security.')
                self.problem.emit(message)

        seen_frame = False

        def received(image):
            nonlocal seen_frame
            if current() and not image.isNull():
                if not seen_frame:
                    seen_frame = True
                    self.changed.emit(kind, 'active')
                timer = self.watchdogs.pop(kind, None)
                if timer:
                    timer.stop()
                    timer.deleteLater()
                self.frame.emit(kind, image)

        def granted(allowed):
            if not current():
                return
            if not allowed:
                failed(denied=True)
                return
            try:
                if kind in {'camera', 'screen'}:
                    timer = QTimer(self)
                    timer.setSingleShot(True)
                    timer.timeout.connect(failed)
                    self.watchdogs[kind] = timer
                    timer.start(8000)
                handle = self.backend.start(kind, device,
                    received,
                    lambda value: self.level.emit(value) if current() else None, failed)
                if not current():
                    handle.stop()
                    return
                self.handles[kind] = handle
                self.changed.emit(kind, 'starting' if kind in {'camera', 'screen'}
                                  and not seen_frame else 'active')
                if kind == 'speaker':
                    self.speaker_timer.start(1000)
            except Exception:
                failed()
        try:
            self.backend.permission(kind, granted)
        except Exception:
            failed()

    def stop(self, kind):
        self.epochs[kind] = self.epochs.get(kind, 0) + 1
        timer = self.watchdogs.pop(kind, None)
        if timer:
            timer.stop()
            timer.deleteLater()
        handle = self.handles.pop(kind, None)
        if handle:
            try:
                handle.stop()
            except RuntimeError:
                # A vanished Qt device must not prevent the other devices stopping.
                pass
        if kind == 'speaker':
            self.speaker_timer.stop()
        if kind == 'microphone':
            self.level.emit(0)
        self.changed.emit(kind, 'off')

    def stop_all(self):
        for kind in ('camera', 'microphone', 'speaker', 'screen'):
            self.stop(kind)

    def close(self):
        self.closed = True
        self.stop_all()
