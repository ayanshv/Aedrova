"""A live call rides out brief network trouble and long sessions, but not refused access."""

import asyncio
import base64
import json
import threading
import time
from types import SimpleNamespace

import pytest

from aedrova.desktop.meeting_call import fresh_token_source, token_expiry
from aedrova.meetings.access import (
    MeetingClient,
    MeetingRequestError,
    RetryableMeetingError,
)
from aedrova.meetings.call import CallWorker


def beats(outcomes):
    """Run the heartbeat against scripted pulse results until it stops or raises."""
    stop = threading.Event()
    seen = []

    def pulse(_):
        outcome = outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        seen.append(outcome)
        if not outcomes:
            stop.set()
        return outcome

    fake = SimpleNamespace(
        stop_requested=stop,
        cleaning=False,
        meeting="m",
        client=SimpleNamespace(pulse=pulse),
        update_consent=lambda snapshot: None,
    )
    asyncio.run(CallWorker._heartbeat(fake))
    return seen


@pytest.fixture(autouse=True)
def quick(monkeypatch):
    real = asyncio.sleep

    async def fast(delay):
        await real(0)

    monkeypatch.setattr("aedrova.meetings.call.asyncio.sleep", fast)


def test_two_missed_beats_do_not_end_the_call():
    blip = RetryableMeetingError("Cannot reach the meeting service.")
    assert beats([blip, blip, {"ok": 1}]) == [{"ok": 1}]


def test_three_misses_in_a_row_end_the_call():
    blip = RetryableMeetingError("Cannot reach the meeting service.")
    with pytest.raises(MeetingRequestError):
        beats([blip, blip, blip])


def test_refused_access_ends_the_call_at_once():
    with pytest.raises(MeetingRequestError, match="Cannot access"):
        beats([MeetingRequestError("Cannot access this call."), {"ok": 1}])


def make_token(expires):
    body = base64.urlsafe_b64encode(json.dumps({"exp": expires}).encode()).decode().rstrip("=")
    return f"h.{body}.s"


def test_token_expiry_reads_the_claim_and_fails_closed():
    assert token_expiry(make_token(1234)) == 1234
    assert token_expiry("not-a-token") == 0


def test_token_is_refreshed_before_it_runs_out_and_not_before():
    calls = []

    class Clone:
        def realtime_credentials(self):
            calls.append("fetch")
            return None, None, make_token(time.time() + 3600), "user-1"

        def close_context(self):
            calls.append("close")

    service = SimpleNamespace(fork_for_context=lambda: Clone())
    healthy = make_token(time.time() + 3000)
    assert fresh_token_source(service, "user-1", healthy)() == healthy
    assert calls == []
    expiring = make_token(time.time() + 30)
    refreshed = fresh_token_source(service, "user-1", expiring)()
    assert refreshed != expiring and calls == ["fetch", "close"]


def test_other_account_token_is_never_adopted():
    class Clone:
        def realtime_credentials(self):
            return None, None, make_token(time.time() + 3600), "someone-else"

        def close_context(self):
            pass

    service = SimpleNamespace(fork_for_context=lambda: Clone())
    expiring = make_token(time.time() + 30)
    assert fresh_token_source(service, "user-1", expiring)() == expiring


def test_client_sends_the_refreshed_token(monkeypatch):
    sent = []

    class Response:
        status_code = 200

        def json(self):
            return {}

    class Http:
        def __init__(self, **_):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def request(self, method, url, headers, json):
            sent.append(headers["Authorization"])
            return Response()

    monkeypatch.setattr("aedrova.meetings.access.httpx.Client", Http)
    tokens = iter(["first", "second"])
    client = MeetingClient("https://aedrova.com", "first", token_source=lambda: next(tokens))
    client.pulse("m")
    client.pulse("m")
    assert sent == ["Bearer first", "Bearer second"]
