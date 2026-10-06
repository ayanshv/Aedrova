import time

import httpx
import pytest
from test_meeting_calls import Backend, Worker

from aedrova.desktop.meeting_call import AudioCall
from aedrova.meetings.access import MeetingClient, MeetingRequestError
from aedrova.meetings.devices import DeviceCheck


def test_phone_interface_has_no_video_views_and_keeps_mute_hangup(qtbot):
    backend, worker = Backend(), Worker()
    call = AudioCall(None, worker, devices=DeviceCheck(backend=backend), channel_name="General")
    qtbot.addWidget(call)
    call.show()
    assert call.gallery.isHidden() and call.stage.isHidden() and call.view_choice.isHidden()
    assert call.controls["camera"].isHidden() and call.controls["screen"].isHidden()
    assert call.leave_button.text() == "Hang up"
    worker.state.emit("Connected")
    assert backend.permissions == ["microphone"]
    call.audio_started = time.monotonic() - 65
    call.update_duration()
    assert call.duration.text() == "01:05"
    worker.roster.emit(
        [{"id": "self", "name": "You"}, {"id": "peer", "name": "Maya", "microphone_on": True}]
    )
    assert set(call.audio_cards) == {"self", "peer"}
    worker.speaker.emit("peer") if hasattr(worker, "speaker") else call.speaker_changed("peer")
    assert call.audio_cards["peer"].property("speaking")
    worker.ended.emit()
    assert call.duration.text() == "Call ended" and not call.duration_timer.isActive()
    call.reject()
    assert worker.stopped


@pytest.mark.parametrize(
    "status,expected",
    [
        (401, "Sign in again"),
        (403, "Sign in again"),
        (404, "not configured"),
        (503, "temporarily unavailable"),
    ],
)
def test_meeting_http_failures_are_clear_and_never_echo_credentials(monkeypatch, status, expected):
    original = httpx.Client
    transport = httpx.MockTransport(
        lambda request: httpx.Response(status, json={"error": "secret-token"})
    )
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: original(transport=transport, **kwargs))
    client = MeetingClient("http://127.0.0.1:8090", "secret-token")
    with pytest.raises(MeetingRequestError) as error:
        client.request("/api/meetings/channel/example")
    assert expected in str(error.value) and "secret-token" not in str(error.value)


def test_unreachable_service_reports_connection_without_ai_message(monkeypatch):
    original = httpx.Client

    def fail(request):
        raise httpx.ConnectError("private-token", request=request)

    monkeypatch.setattr(
        httpx, "Client", lambda **kwargs: original(transport=httpx.MockTransport(fail), **kwargs)
    )
    with pytest.raises(MeetingRequestError, match="Cannot reach the meeting service") as error:
        MeetingClient("http://127.0.0.1:8090", "secret-token").request(
            "/api/meetings/channel/example"
        )
    assert "private-token" not in str(error.value) and "AI" not in str(error.value)
