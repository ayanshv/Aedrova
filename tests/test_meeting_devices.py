import math
import struct

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QPushButton

from aedrova.desktop.meeting_setup import MeetingSetup
from aedrova.meetings.audio import audio_level, speaker_tone
from aedrova.meetings.devices import DeviceCheck


class Device:
    def description(self):
        return 'Test device'

    def name(self):
        return 'Test screen'


class Handle:
    def __init__(self):
        self.stopped = False

    def stop(self):
        self.stopped = True


class Backend:
    def __init__(self, *, delayed=False, allowed=True, empty=False, broken=False):
        self.delayed, self.allowed, self.empty, self.broken = delayed, allowed, empty, broken
        self.requests, self.started = [], []
        self.pending = None

    def list(self, kind):
        return [] if self.empty else [Device()]

    def permission(self, kind, callback):
        self.requests.append(kind)
        if self.delayed:
            self.pending = callback
        else:
            callback(self.allowed)

    def start(self, kind, device, frame, level, failed):
        if self.broken:
            raise RuntimeError('Sensitive native/provider details')
        handle = Handle()
        self.started.append((kind, handle, frame, level, failed))
        return handle


def setup(qtbot, **kwargs):
    backend = Backend(**kwargs)
    check = DeviceCheck(backend=backend)
    dialog = MeetingSetup(check=check)
    qtbot.addWidget(dialog)
    dialog.show()
    return backend, check, dialog


def test_opening_setup_never_requests_permission_or_captures(qtbot):
    backend, check, dialog = setup(qtbot)
    assert not backend.requests and not backend.started and not check.handles
    assert dialog.level.value() == 0
    assert dialog.camera_preview.image.isNull() and dialog.screen_preview.image.isNull()


@pytest.mark.parametrize('kind', ['camera', 'microphone', 'screen', 'speaker'])
def test_user_action_starts_only_selected_device_and_stop_releases_it(qtbot, kind):
    backend, check, dialog = setup(qtbot)
    qtbot.mouseClick(dialog.actions[kind], Qt.MouseButton.LeftButton)
    assert backend.requests == [kind] and len(backend.started) == 1
    assert kind in check.handles
    qtbot.mouseClick(dialog.actions[kind], Qt.MouseButton.LeftButton)
    assert backend.started[0][1].stopped and not check.handles


def test_closing_during_permission_prompt_cannot_start_capture(qtbot):
    backend, check, dialog = setup(qtbot, delayed=True)
    qtbot.mouseClick(dialog.actions['camera'], Qt.MouseButton.LeftButton)
    dialog.reject()
    backend.pending(True)
    assert check.closed and not backend.started


def test_cancelled_permission_cannot_resurrect_a_check(qtbot):
    backend, check, dialog = setup(qtbot, delayed=True)
    qtbot.mouseClick(dialog.actions['camera'], Qt.MouseButton.LeftButton)
    old = backend.pending
    qtbot.mouseClick(dialog.actions['camera'], Qt.MouseButton.LeftButton)
    old(True)
    assert not backend.started and dialog.states['camera'] == 'off'


def test_permission_denial_and_device_failure_do_not_expose_native_details(qtbot):
    for options in ({'allowed': False}, {'broken': True}):
        backend, check, dialog = setup(qtbot, **options)
        qtbot.mouseClick(dialog.actions['microphone'], Qt.MouseButton.LeftButton)
        assert not check.handles and dialog.states['microphone'] == 'off'
        assert 'Privacy & Security' in dialog.status.text()
        assert 'Sensitive' not in dialog.status.text()
        dialog.reject()


def test_close_clears_previews_levels_and_all_resources(qtbot):
    backend, check, dialog = setup(qtbot)
    for kind in ('camera', 'microphone', 'screen'):
        qtbot.mouseClick(dialog.actions[kind], Qt.MouseButton.LeftButton)
    image = QImage(64, 48, QImage.Format.Format_RGBA8888)
    image.fill(Qt.GlobalColor.red)
    backend.started[0][2](image)
    backend.started[1][3](60)
    backend.started[2][2](image)
    assert not dialog.camera_preview.image.isNull() and dialog.level.value() == 60
    dialog.accept()
    assert all(handle.stopped for _, handle, *_ in backend.started)
    assert dialog.camera_preview.image.isNull() and dialog.screen_preview.image.isNull()
    assert dialog.level.value() == 0
    # Delayed frames from stopped handles cannot repopulate the hidden dialog.
    backend.started[0][2](image)
    backend.started[1][3](99)
    assert dialog.camera_preview.image.isNull() and dialog.level.value() == 0


def test_unplugging_stops_capture_and_refreshes_available_devices(qtbot):
    backend, check, dialog = setup(qtbot)
    qtbot.mouseClick(dialog.actions['camera'], Qt.MouseButton.LeftButton)
    backend.empty = True
    check.devices_changed()
    assert backend.started[0][1].stopped
    assert all(not action.isEnabled() for action in dialog.actions.values())


def test_speaker_test_finishes_automatically(qtbot):
    backend, check, dialog = setup(qtbot)
    qtbot.mouseClick(dialog.actions['speaker'], Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: 'speaker' not in check.handles, timeout=2000)
    assert backend.started[0][1].stopped


def test_empty_inventory_has_no_inert_start_buttons(qtbot):
    backend, check, dialog = setup(qtbot, empty=True)
    assert all(not control.isEnabled() for control in dialog.actions.values())
    assert all(not choice.isEnabled() for choice in dialog.choices.values())


def test_stop_all_does_not_close_setup(qtbot):
    backend, check, dialog = setup(qtbot)
    qtbot.mouseClick(dialog.actions['camera'], Qt.MouseButton.LeftButton)
    stop = next(b for b in dialog.findChildren(QPushButton) if b.text() == 'Stop all')
    qtbot.mouseClick(stop, Qt.MouseButton.LeftButton)
    assert not check.closed and not check.handles and dialog.isVisible()


@pytest.mark.parametrize('kind', ['UInt8', 'Int16', 'Int32', 'Float'])
def test_meter_and_tone_support_real_device_formats(kind):
    tone = speaker_tone(48000, 2, kind)
    assert 0 < audio_level(tone[:65536], kind) <= 12
    silence = bytes([128]) * 64 if kind == 'UInt8' else bytes(64)
    assert audio_level(silence, kind) == 0


def test_meter_bounds_noise_and_rejects_nonfinite_samples():
    assert audio_level(struct.pack('<fff', math.nan, math.inf, -math.inf), 'Float') == 0
    assert audio_level(struct.pack('<ff', 50, -50), 'Float') == 100
    assert audio_level(b'\xff', 'Int16') == 0
    assert audio_level(b'anything', 'unknown') == 0


@pytest.mark.parametrize('args', [(1000, 1, 'Int16'), (48000, 50, 'Float'),
                                  (48000, 1, 'unknown'), (48000, 1, 'Float', 20)])
def test_speaker_test_rejects_unbounded_or_unsupported_formats(args):
    with pytest.raises(ValueError):
        speaker_tone(*args)


def test_native_capture_releases_resources_even_if_stop_fails():
    from aedrova.meetings.devices import Capture

    class Resource:
        deleted = False

        def deleteLater(self):  # noqa: N802
            self.deleted = True

        def stop(self):
            raise RuntimeError("Device disappeared")

    source, sink = Resource(), Resource()
    with pytest.raises(RuntimeError):
        Capture(source, (sink,)).stop()
    assert source.deleted and sink.deleted


def test_vanished_device_does_not_interrupt_stop_all(qtbot):
    _, check, dialog = setup(qtbot)
    other = Handle()

    class Vanished:
        def stop(self):
            raise RuntimeError("Qt device deleted")

    check.handles.update(camera=Vanished(), microphone=other)
    dialog.close()
    assert other.stopped and not check.handles


def test_screen_permission_checks_before_prompt_and_denial_is_returned(monkeypatch):
    from types import SimpleNamespace

    from aedrova.meetings import permissions

    monkeypatch.setattr(permissions.sys, 'platform', 'darwin')

    class Function:
        def __init__(self, result):
            self.result, self.calls = result, 0

        def __call__(self):
            self.calls += 1
            return self.result

    check, request = Function(True), Function(False)
    library = SimpleNamespace(CGPreflightScreenCaptureAccess=check,
                              CGRequestScreenCaptureAccess=request)
    assert permissions.screen_access(library=library)
    assert check.calls == 1 and request.calls == 0
    check.result = False
    assert not permissions.screen_access(library=library)
    assert request.calls == 1


def test_screen_without_frames_times_out_and_stops_capture(qtbot):
    backend, check, dialog = setup(qtbot)
    dialog.actions['screen'].click()
    check.watchdogs['screen'].setInterval(1)
    qtbot.waitUntil(lambda: 'screen' not in check.handles)
    assert backend.started[0][1].stopped
    assert 'permission was granted' in dialog.status.text()
    assert 'System Settings' not in dialog.status.text()
    assert not check.watchdogs


def test_first_valid_frame_cancels_watchdog_and_null_frame_does_not(qtbot):
    backend, check, dialog = setup(qtbot)
    dialog.actions['screen'].click()
    callback = backend.started[0][2]
    callback(QImage())
    assert 'screen' in check.watchdogs
    callback(QImage(20, 20, QImage.Format.Format_RGBA8888))
    assert 'screen' not in check.watchdogs and not dialog.screen_preview.image.isNull()
    dialog.close()
    assert not check.watchdogs


def test_screen_denial_explains_stale_build_without_starting_capture(qtbot):
    backend, check, dialog = setup(qtbot, allowed=False)
    dialog.actions['screen'].click()
    assert not backend.started and not check.handles
    assert 'has not granted screen access' in dialog.status.text()
    assert 'remove the old Aedrova entry' in dialog.status.text()


def test_setup_inherits_explicit_workspace_palette(qtbot):
    from PySide6.QtGui import QPalette
    from PySide6.QtWidgets import QWidget

    from aedrova.desktop.theme import DARK
    parent = QWidget()
    parent.theme = DARK
    qtbot.addWidget(parent)
    dialog = MeetingSetup(parent, check=DeviceCheck(backend=Backend()))
    qtbot.addWidget(dialog)
    assert dialog.palette().color(QPalette.ColorRole.AlternateBase).name() == DARK.surface.lower()
