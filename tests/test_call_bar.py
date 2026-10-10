from test_connected import setup
from test_meeting_activity import active
from test_meeting_calls import Backend, Worker

from aedrova.desktop.meeting_activity import update_meeting_ui
from aedrova.desktop.meeting_call import MeetingCall
from aedrova.meetings.devices import DeviceCheck


def test_call_bar_replaces_meeting_tab_and_routes_modes(qtbot, tmp_path, monkeypatch):
    from aedrova.desktop import meeting_call

    window, _ = setup(qtbot, tmp_path)
    assert [b.text() for b in window.tab_buttons] == ["Conversation", "Project", "Work", "Files"]
    assert window.pages.count() == 5
    assert window.pages.widget(4) is window.pulse_page
    calls = []
    monkeypatch.setattr(meeting_call, "open_channel_call", lambda owner, **kw: calls.append(kw))
    window.call_buttons["phone"].click()
    window.call_buttons["camera"].click()
    assert calls == [{"mode": "audio"}, {"mode": "video"}]
    window.account_dialog.snapshot["meeting_activity"] = {
        "meetings": [active(window)],
        "preferences": [],
    }
    update_meeting_ui(window)
    assert window.call_count.text() == "2"
    assert window.call_buttons["camera"].accessibleName() == "Join video call"
    window.account_dialog.snapshot["meeting_activity"]["meetings"] = []
    update_meeting_ui(window)
    assert window.call_count.isHidden()
    assert window.call_buttons["phone"].toolTip() == "Start audio call"
    window.open_meeting_hub()
    assert window.meeting_hub.isVisible()
    assert window.meeting_action_layout.count() == 1


def test_audio_call_requests_only_microphone_and_respects_mute(qtbot):
    backend, worker = Backend(), Worker()
    call = MeetingCall(None, worker, devices=DeviceCheck(backend=backend), initial_mode="audio")
    qtbot.addWidget(call)
    call.show()
    worker.state.emit("Connected")
    assert backend.permissions == ["microphone"] and not call.states["camera"]
    backend.pending(True)
    assert ("microphone", True) in worker.calls
    call.toggle("microphone")
    worker.state.emit("Reconnected")
    assert backend.permissions == ["microphone"] and not call.states["microphone"]


def test_video_call_requests_camera_after_connect_only(qtbot):
    backend, worker = Backend(), Worker()
    call = MeetingCall(None, worker, devices=DeviceCheck(backend=backend), initial_mode="video")
    qtbot.addWidget(call)
    call.show()
    assert not backend.permissions
    requested = []
    original = call.toggle

    def toggle(kind):
        requested.append(kind)
        original(kind)

    call.toggle = toggle
    worker.state.emit("Connected")
    assert requested == ["microphone", "camera"]
    assert not call.states["camera"]  # no camera exists in fake backend


def test_header_call_joins_automatically_and_closed_dialog_cannot_start(
    qtbot, tmp_path, monkeypatch
):
    from types import SimpleNamespace

    from aedrova.desktop import meeting_call

    window, service = setup(qtbot, tmp_path)
    worker = Worker()
    service.client = SimpleNamespace(
        auth=SimpleNamespace(get_session=lambda: SimpleNamespace(access_token="test-token"))
    )
    monkeypatch.setattr(meeting_call, "application_origin", lambda: "https://meetings.example.com")
    monkeypatch.setattr(meeting_call, "CallWorker", lambda *args, **kw: worker)
    monkeypatch.setattr(meeting_call, "DeviceCheck", lambda owner: DeviceCheck(backend=Backend()))
    meeting_call.open_channel_call(window, mode="audio")
    qtbot.waitUntil(lambda: worker.started)
    assert window.meeting_call.initial_mode == "audio"
    window.meeting_call.reject()
    worker.started = False
    window.meeting_call.join_call()
    assert not worker.started
