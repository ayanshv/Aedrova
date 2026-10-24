import asyncio
from types import SimpleNamespace
from unittest.mock import Mock

from livekit import rtc
from PySide6.QtCore import QPointF
from PySide6.QtGui import QColor, QImage
from test_meeting_calls import Backend, Worker

from aedrova.desktop.meeting_call import MeetingCall
from aedrova.desktop.meeting_presentation import SharingCanvas, annotate, camera_look
from aedrova.meetings.call import CallWorker
from aedrova.meetings.devices import DeviceCheck


def image(color="red"):
    frame = QImage(640, 360, QImage.Format.Format_RGBA8888)
    frame.fill(QColor(color))
    return frame


def call(qtbot):
    worker = Worker()
    worker.frame = Mock()
    devices = DeviceCheck(backend=Backend())
    dialog = MeetingCall(None, worker, devices=devices)
    qtbot.addWidget(dialog)
    dialog.call_state("Connected")
    return worker, dialog


def test_camera_looks_are_local_bounded_and_do_not_modify_input(qapp):
    original = image()
    grey = camera_look(original, monochrome=True)
    pixel = grey.pixelColor(10, 10)
    assert pixel.red() == pixel.green() == pixel.blue()
    assert original.pixelColor(10, 10) == QColor("red")
    assert camera_look(original, light=100) == camera_look(original, light=25)
    assert camera_look(original, light=25).pixelColor(10, 10).green() > 0


def test_mirroring_changes_only_preview_not_outgoing_camera(qtbot):
    worker, dialog = call(qtbot)
    dialog.states["camera"] = True
    original = image("black")
    original.setPixelColor(0, 0, QColor("red"))
    dialog.mirror_preview = True
    dialog.local_frame("camera", original)
    sent = worker.frame.call_args.args[1]
    assert sent.pixelColor(0, 0) == QColor("red")
    assert dialog.last_images["self/camera"].pixelColor(639, 0) == QColor("red")


def test_annotations_reach_shared_frames_and_clear_on_stop(qtbot):
    worker, dialog = call(qtbot)
    dialog.states["screen"] = True
    dialog.local_frame("screen", image("black"))
    dialog.set_annotating(True)
    dialog.annotation_point((0.2, 0.5), True)
    dialog.annotation_point((0.8, 0.5), False)
    assert worker.frame.call_args.args[0] == "screen"
    sent = worker.frame.call_args.args[1]
    assert sent.pixelColor(320, 180) != QColor("black")
    dialog.clear_annotations()
    assert worker.frame.call_args.args[1].pixelColor(320, 180) == QColor("black")
    dialog.strokes.append(("#2979FF", [(0, 0)]))
    dialog.disable("screen")
    assert not dialog.strokes and dialog.share_base is None
    before = worker.frame.call_count
    dialog.local_frame("screen", image())
    assert worker.frame.call_count == before


def test_annotation_only_on_own_active_screen_and_normalized_canvas(qtbot):
    _, dialog = call(qtbot)
    dialog.annotating = True
    dialog.annotation_point((0.5, 0.5), True)
    assert not dialog.strokes
    dialog.states["screen"] = True
    dialog.focused = "someone/screen"
    dialog.annotation_point((0.5, 0.5), True)
    assert not dialog.strokes
    canvas = SharingCanvas("test")
    qtbot.addWidget(canvas)
    canvas.resize(640, 640)
    canvas.display(image())
    assert canvas.normalized(QPointF(320, 320)) == (0.5, 0.5)
    assert canvas.normalized(QPointF(320, 10)) is None
    assert annotate(image(), []) == image()


def test_pause_stops_capture_and_waits_for_unpublish_before_resume(qtbot):
    worker, dialog = call(qtbot)
    dialog.states["screen"] = True
    dialog.local_frame("screen", image())
    dialog.pause_share()
    assert dialog.share_paused and not dialog.states["screen"]
    assert not dialog.pause_share_button.isEnabled()
    assert ("screen", False) in worker.calls
    dialog.media_state("screen", True)  # Late publish receipt cannot undo pause.
    assert dialog.share_paused and not dialog.states["screen"]
    dialog.media_state("screen", False)
    assert dialog.share_paused and dialog.pause_share_button.isEnabled()
    dialog.toggle = Mock()
    dialog.pause_share()
    dialog.toggle.assert_called_once_with("screen")
    assert not dialog.share_paused


def test_pinned_video_wins_over_speaker_and_can_be_unpinned(qtbot):
    _, dialog = call(qtbot)
    dialog.render_roster([dict(id="self", name="You"), dict(id="peer", name="Jordan")])
    dialog.pin_video("peer/camera")
    dialog.speaker_changed("self")
    assert dialog.focused == "peer/camera" and dialog.stage.isVisibleTo(dialog)
    dialog.pin_video("peer/camera")
    assert dialog.pinned_key is None
    dialog.set_self_view(False)
    assert not dialog.tiles["self/camera"][0].isVisibleTo(dialog)


def test_disabling_incoming_video_clears_mailbox_and_only_unsubscribes_video(qapp):
    worker = CallWorker(None, workspace="w", channel="c", user="self")
    video = SimpleNamespace(kind=rtc.TrackKind.KIND_VIDEO, set_subscribed=Mock())
    audio = SimpleNamespace(kind=rtc.TrackKind.KIND_AUDIO, set_subscribed=Mock())
    worker.room = SimpleNamespace(remote_participants={"peer": SimpleNamespace(
        track_publications={"v": video, "a": audio})})
    worker.frames = {"peer/camera": image(), "camera": image()}

    async def run():
        worker.lock = asyncio.Lock()
        await worker._media("receive_video", False)
        assert not worker.receive_video and "peer/camera" not in worker.frames
        assert "camera" in worker.frames
        video.set_subscribed.assert_called_with(False)
        audio.set_subscribed.assert_not_called()
        await worker._media("receive_video", True)
        video.set_subscribed.assert_called_with(True)

    asyncio.run(run())


def test_disabling_incoming_video_clears_local_ui_and_ignores_queued_frames(qtbot):
    worker, dialog = call(qtbot)
    dialog.render_roster([dict(id="self", name="You"), dict(id="peer", name="Jordan")])
    worker.take_remote_frames = lambda: {"peer/camera": image()}
    dialog.remote_frames()
    assert "peer/camera" in dialog.last_images
    dialog.set_receive_video(False)
    dialog.remote_frames()
    assert "peer/camera" not in dialog.last_images
    assert ("receive_video", False) in worker.calls


def test_native_window_capture_binds_window_session_and_rejects_invalid(qapp, monkeypatch):
    import aedrova.meetings.devices as devices

    class Window:
        def __init__(self, valid=True):
            self.valid = valid

        def isValid(self):  # noqa: N802
            return self.valid

    source, session, sink = Mock(), Mock(), Mock()
    source.error.return_value.value = 0
    monkeypatch.setattr(devices, "QCapturableWindow", Window)
    monkeypatch.setattr(devices, "QWindowCapture", lambda parent: source)
    monkeypatch.setattr(devices, "QMediaCaptureSession", lambda parent: session)
    monkeypatch.setattr(devices, "QVideoSink", lambda parent: sink)
    backend = devices.NativeDevices.__new__(devices.NativeDevices)
    backend.parent = None
    window = Window()
    handle = backend.start("screen", window, Mock(), Mock(), Mock())
    source.setWindow.assert_called_once_with(window)
    session.setWindowCapture.assert_called_once_with(source)
    session.setScreenCapture.assert_not_called()
    source.start.assert_called_once()
    handle.stop()
    source.stop.assert_called_once()
    import pytest

    with pytest.raises(RuntimeError, match="no longer available"):
        backend.start("screen", Window(False), Mock(), Mock(), Mock())


def test_annotation_limits_do_not_extend_an_earlier_stroke(qtbot):
    _, dialog = call(qtbot)
    dialog.states["screen"] = True
    dialog.focused = "self/screen"
    dialog.annotating = True
    dialog.strokes = [("#2979FF", [(0.1, 0.1)]) for _ in range(64)]
    dialog.annotation_point((0.3, 0.3), True)
    dialog.annotation_point((0.4, 0.4), False)
    assert len(dialog.strokes) == 64 and len(dialog.strokes[-1][1]) == 1
    dialog.clear_annotations()
    dialog.annotation_point((0.4, 0.4), True)
    assert len(dialog.strokes) == 1


def test_opening_presentation_starts_no_capture_or_network(qtbot):
    worker, backend = Worker(), Backend()
    dialog = MeetingCall(None, worker, devices=DeviceCheck(backend=backend))
    qtbot.addWidget(dialog)
    dialog.show_presentation()
    assert not worker.started and not worker.calls and not backend.permissions
    dialog.reject()
    assert not dialog.presentation_dialog.isVisible()


def test_new_remote_publication_respects_disabled_video_and_handles_race(qapp):
    worker = CallWorker(None, workspace="w", channel="c", user="self")
    worker.receive_video = False
    worker._roster = Mock()
    video = SimpleNamespace(kind=rtc.TrackKind.KIND_VIDEO, set_subscribed=Mock())
    worker._published(video, None)
    video.set_subscribed.assert_called_once_with(False)
    video.set_subscribed.side_effect = RuntimeError("private provider detail")
    messages = []
    worker.problem.connect(messages.append)
    worker._published(video, None)
    assert messages == ["Could not update incoming video. Retry this setting."]
