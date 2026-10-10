import asyncio
import threading
from types import SimpleNamespace

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor, QImage

from aedrova.desktop.meeting_call import MeetingCall, encode_image
from aedrova.meetings.call import CallWorker
from aedrova.meetings.devices import DeviceCheck


class Backend:
    def __init__(self):
        self.permissions = []
        self.pending = None

    def list(self, _):
        return []

    def permission(self, kind, callback):
        self.permissions.append(kind)
        self.pending = callback


class Worker(QObject):
    state = Signal(str)
    roster = Signal(object)
    problem = Signal(str)
    media = Signal(str, bool)
    ended = Signal()
    user = 'self'

    def __init__(self):
        super().__init__()
        self.calls = []
        self.stopped = False
        self.started = False

    def command(self, kind, enabled):
        self.calls.append((kind, enabled))

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True

    def clear_frame(self, kind):
        pass

    def take_remote_frames(self):
        return {}


def setup(qtbot):
    backend, worker = Backend(), Worker()
    dialog = MeetingCall(None, worker, devices=DeviceCheck(backend=backend))
    qtbot.addWidget(dialog)
    dialog.show()
    return backend, worker, dialog


def test_open_call_starts_no_network_or_devices(qtbot):
    backend, worker, dialog = setup(qtbot)
    assert not worker.started and not backend.permissions
    assert not any(c.isEnabled() for c in dialog.controls.values())
    dialog.join.click()
    assert worker.started
    assert not backend.permissions


def test_late_microphone_permission_cannot_start_after_close(qtbot):
    backend, worker, dialog = setup(qtbot)
    worker.state.emit('Connected · devices are off')
    dialog.controls['microphone'].click()
    assert backend.permissions == ['microphone']
    dialog.reject()
    backend.pending(True)
    assert worker.stopped and ('microphone', True) not in worker.calls


def test_microphone_cancel_invalidates_pending_permission(qtbot):
    backend, worker, dialog = setup(qtbot)
    worker.state.emit('Connected')
    dialog.toggle('microphone')
    dialog.toggle('microphone')
    backend.pending(True)
    assert ('microphone', True) not in worker.calls


def test_worker_off_event_does_not_command_infinite_feedback(qtbot):
    _, worker, dialog = setup(qtbot)
    worker.media.emit('camera', False)
    assert not worker.calls


def test_reconnection_pauses_devices_without_enabling_on_resume(qtbot):
    backend, worker, dialog = setup(qtbot)
    worker.state.emit('Connected')
    dialog.toggle('microphone')
    backend.pending(True)
    worker.media.emit('microphone', True)
    worker.state.emit('Reconnecting… devices paused')
    assert not any(dialog.states.values())
    count = len(worker.calls)
    worker.state.emit('Reconnected · enable your devices when ready')
    assert len(worker.calls) == count
    assert dialog.controls['microphone'].text() == 'Muted'


def test_departure_removes_video_tile_and_close_clears_all(qtbot):
    _, worker, dialog = setup(qtbot)
    worker.roster.emit([{'id': 'self', 'name': 'You'}, {'id': 'other', 'name': '<b>Team</b>'}])
    assert 'other/camera' in dialog.tiles
    worker.roster.emit([{'id': 'self', 'name': 'You'}])
    assert 'other/camera' not in dialog.tiles
    dialog.close()
    assert worker.stopped and not dialog.timer.isActive()


def test_encoding_preserves_aspect_and_bounds_memory():
    image = QImage(100, 100, QImage.Format.Format_RGBA8888)
    image.fill(QColor('red'))
    frame = encode_image(image)
    assert frame.width() == 640 and frame.height() == 360
    assert frame.bytesPerLine() == 640 * 4
    assert frame.pixelColor(0, 0) == QColor('black')
    assert frame.pixelColor(320, 180) == QColor('red')


def test_latest_frame_mailbox_is_bounded_and_stop_discards(qapp):
    worker = CallWorker(None, workspace='w', channel='c', user='u')
    worker.connected = True
    for _ in range(100):
        worker.frame('camera', QImage(640, 360, QImage.Format.Format_RGBA8888))
    assert len(worker.frames) == 1
    worker.stop()
    worker.frame('camera', QImage())
    assert not worker.frames


def test_join_cancelled_before_authorization_never_initializes_rtc(qapp, monkeypatch):
    from aedrova.meetings import call
    client = SimpleNamespace(start=lambda _: 'm', join=lambda *a, **k: None, leave=lambda _: None)
    worker = CallWorker(client, workspace='w', channel='c', user='u')
    worker.stop()
    monkeypatch.setattr(call.rtc, 'Room', lambda: (_ for _ in ()).throw(AssertionError()))
    asyncio.run(worker._run())
    assert worker.audio is None and worker.room is None


def test_reconnecting_releases_microphone_and_clears_queued_frames(qapp):
    closed = []
    worker = CallWorker(None, workspace='w', channel='c', user='u')
    worker.microphone = SimpleNamespace(close=lambda: closed.append(True))
    worker.connected = True
    worker.frames['camera'] = QImage()
    worker._reconnecting()
    assert closed and worker.microphone is None and not worker.connected and not worker.frames


def test_cleanup_disconnects_even_when_leave_service_is_unavailable(qapp):
    calls = []
    async def disconnected():
        calls.append('disconnect')
    client = SimpleNamespace(leave=lambda _: (_ for _ in ()).throw(RuntimeError('offline')))
    worker = CallWorker(client, workspace='w', channel='c', user='u')
    worker.room = SimpleNamespace(disconnect=disconnected)
    worker.audio = SimpleNamespace(close=lambda: calls.append('audio closed'))
    worker.microphone = SimpleNamespace(close=lambda: calls.append('mic closed'))
    worker.meeting = 'm'
    asyncio.run(worker._cleanup())
    assert calls == ['mic closed', 'disconnect', 'audio closed']
    assert worker.audio is None and worker.microphone is None


def test_stopped_worker_accepts_no_new_commands(qapp):
    worker = CallWorker(None, workspace='w', channel='c', user='u')
    worker.loop = SimpleNamespace(is_closed=lambda: True,
                                  call_soon_threadsafe=lambda *a: (_ for _ in ()).throw(
        AssertionError('Queued after shutdown')))
    worker.stop_requested = threading.Event()
    worker.stop()
    worker.command('microphone', True)


def test_gallery_speaker_view_and_participants_controls_are_real(qtbot):
    _, worker, dialog = setup(qtbot)
    assert not dialog.stage.isVisible() and not dialog.participant_panel.isVisible()
    dialog.view_choice.setCurrentIndex(1)
    assert dialog.stage.isVisible()
    dialog.participants_button.click()
    assert dialog.participant_panel.isVisible()
    worker.roster.emit([{'id': 'self', 'name': 'You'}, {'id': 'other', 'name': 'Sam'}])
    assert dialog.participants_button.text() == 'Participants (2)'
    dialog.settings_button.click()
    assert dialog.device_panel.isVisible()


def test_screen_share_spotlights_and_unsubscribe_returns_to_gallery(qtbot):
    _, worker, dialog = setup(qtbot)
    worker.roster.emit([{'id': 'self', 'name': 'You'}, {'id': 'other', 'name': 'Sam'}])
    image = QImage(640, 360, QImage.Format.Format_RGBA8888)
    worker.take_remote_frames = lambda: {'other/screen': image}
    dialog.remote_frames()
    assert dialog.focused == 'other/screen' and dialog.stage.isVisible()
    worker.media.emit('other/screen', False)
    assert not dialog.stage.isVisible() and dialog.stage.image.isNull()


def test_muting_microphone_does_not_clear_camera_preview(qtbot):
    _, worker, dialog = setup(qtbot)
    worker.state.emit('Connected')
    image = QImage(640, 360, QImage.Format.Format_RGBA8888)
    dialog.tiles['self/camera'][1].display(image)
    dialog.disable('microphone')
    assert not dialog.tiles['self/camera'][1].image.isNull()


def test_close_discards_spotlight_images_and_cannot_restart(qtbot):
    _, _, dialog = setup(qtbot)
    dialog.last_images['self/camera'] = QImage(20, 20, QImage.Format.Format_RGBA8888)
    dialog.view_choice.setCurrentIndex(1)
    assert not dialog.stage.image.isNull()
    dialog.close()
    assert not dialog.last_images and dialog.stage.image.isNull()


def test_compact_toolbar_wraps_without_clipping_labels(qtbot):
    _, _, dialog = setup(qtbot)
    dialog.resize(640, 560)
    qtbot.waitUntil(lambda: dialog.width() == 640)
    assert dialog.toolbar_layout.rowCount() >= 2
    for control in dialog.toolbar_buttons:
        assert control.fontMetrics().horizontalAdvance(control.text()) + 20 <= control.width()


def test_failed_call_preserves_phase_and_never_exposes_error_payload(qapp):
    def fail(_):
        raise RuntimeError('private-token-private-url')
    worker = CallWorker(SimpleNamespace(start=fail), workspace='w', channel='c', user='u')
    states, problems = [], []
    worker.state.connect(states.append)
    worker.problem.connect(problems.append)
    asyncio.run(worker._run())
    assert 'channel access' in states[-1]
    assert states[-1] == problems[-1]
    assert 'private' not in ' '.join(states + problems)


def test_camera_fills_frame_without_bars_and_screen_keeps_edges():
    image = QImage(100, 100, QImage.Format.Format_RGBA8888)
    image.fill(QColor('red'))
    camera = encode_image(image, fill=True)
    assert camera.pixelColor(0, 0) == QColor('red')
    assert camera.pixelColor(639, 359) == QColor('red')
    screen = encode_image(image)
    assert screen.pixelColor(0, 0) == QColor('black')
    assert screen.pixelColor(320, 180) == QColor('red')


def test_toolbar_reports_current_state_and_tooltip_explains_action(qtbot):
    _, worker, dialog = setup(qtbot)
    for kind, off, on, action in [('microphone', 'Muted', 'Unmuted', 'Mute microphone'),
                                  ('camera', 'Camera off', 'Camera on', 'Turn camera off')]:
        assert dialog.controls[kind].text() == off
        worker.media.emit(kind, True)
        assert dialog.controls[kind].text() == on
        assert dialog.controls[kind].toolTip() == action
        assert dialog.controls[kind].accessibleName() == on
        worker.media.emit(kind, False)
        assert dialog.controls[kind].text() == off


def test_camera_tiles_fill_but_screen_tiles_do_not_crop(qtbot):
    _, _, dialog = setup(qtbot)
    assert dialog.tile('self/camera', 'You')[1].fill
    assert not dialog.tile('self/screen', 'Screen')[1].fill
