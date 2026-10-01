"""Exercise loopback callbacks and PKCE with no Google account or external requests."""

import json
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
from urllib.request import urlopen

import httpx
import pytest

from aedrova.identity.oauth import google_sign_in
from aedrova.identity.service import Connection, IdentityService
from supabase import ClientOptions, create_client


class FakeService:
    def __init__(self):
        self.exchanged = []

    def google_authorization_url(self, redirect):
        self.redirect = redirect
        return "https://example.supabase.co/auth/v1/authorize"

    def finish_google_sign_in(self, code):
        self.exchanged.append(code)
        return "signed-in-user"


def test_loopback_ignores_wrong_path_and_exchanges_only_valid_code():
    service = FakeService()
    opened = Event()
    with ThreadPoolExecutor() as pool:
        future = pool.submit(
            google_sign_in, service, opener=lambda _: opened.set() or True, port=0, timeout=3
        )
        assert opened.wait(2)
        origin = service.redirect.rsplit("/auth/", 1)[0]
        with pytest.raises(HTTPError) as wrong:
            urlopen(origin + "/wrong?code=attacker", timeout=2)
        assert wrong.value.code == 404
        assert not service.exchanged
        with urlopen(service.redirect + "?code=valid-code", timeout=2) as response:
            assert response.headers["Cache-Control"] == "no-store"
            assert response.headers["Content-Type"] == "text/html; charset=utf-8"
            assert "default-src 'none'" in response.headers["Content-Security-Policy"]
            body = response.read()
            assert b"valid-code" not in body
            assert b"Your space is waiting." in body
        assert future.result(3) == "signed-in-user"
    assert service.exchanged == ["valid-code"]


@pytest.mark.parametrize("query", ["?error=access_denied", "?code=a&code=b"])
def test_denied_or_ambiguous_callback_never_exchanges(query):
    service, opened, cancel = FakeService(), Event(), Event()
    with ThreadPoolExecutor() as pool:
        future = pool.submit(
            google_sign_in,
            service,
            cancel,
            opener=lambda _: opened.set() or True,
            port=0,
            timeout=2,
        )
        assert opened.wait(2)
        try:
            with urlopen(service.redirect + query, timeout=2):
                pass
        except HTTPError as error:
            assert error.code == 400
            cancel.set()
        with pytest.raises((PermissionError, InterruptedError)):
            future.result(3)
    assert service.exchanged == []


def test_browser_failure_and_timeout_release_listener():
    with pytest.raises(RuntimeError):
        google_sign_in(FakeService(), opener=lambda _: False, port=0)
    with pytest.raises(TimeoutError):
        google_sign_in(FakeService(), opener=lambda _: True, port=0, timeout=0.01)


def test_pkce_authorization_and_exchange_use_matching_memory_verifier():
    requests = []
    user = {
        "id": "00000000-0000-0000-0000-000000000001",
        "email": "a@example.com",
        "aud": "authenticated",
        "app_metadata": {},
        "user_metadata": {},
        "created_at": "2026-09-27T00:00:00Z",
    }

    def respond(request):
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "access_token": "access",
                "refresh_token": "refresh",
                "expires_in": 3600,
                "token_type": "bearer",
                "user": user,
            },
        )

    key = "sb_publishable_abcdefghijk1234567890"
    client = create_client(
        "https://example.supabase.co",
        key,
        options=ClientOptions(
            flow_type="pkce",
            persist_session=False,
            auto_refresh_token=False,
            httpx_client=httpx.Client(transport=httpx.MockTransport(respond)),
        ),
    )
    service = IdentityService(Connection("https://example.supabase.co", key), client=client)
    url = service.google_authorization_url("http://127.0.0.1:43827/auth/random")
    query = parse_qs(urlsplit(url).query)
    assert query["provider"] == ["google"]
    assert query["code_challenge_method"] == ["s256"]
    assert "code_verifier" not in query
    assert service.finish_google_sign_in("callback-code").email == "a@example.com"
    body = json.loads(requests[-1].content)
    assert body["auth_code"] == "callback-code"
    import base64
    import hashlib

    challenge = base64.urlsafe_b64encode(hashlib.sha256(body["code_verifier"].encode()).digest())
    assert challenge.decode().rstrip("=") == query["code_challenge"][0]
    assert client.auth._storage.get_item(f"{client.auth._storage_key}-code-verifier") is None


def test_cancellation_before_browser_launch_opens_nothing():
    cancel = Event()
    cancel.set()
    with pytest.raises(InterruptedError):
        google_sign_in(
            FakeService(),
            cancel,
            port=0,
            opener=lambda _: pytest.fail("Browser opened after cancellation"),
        )


def test_cancellation_during_exchange_discards_late_session():
    cancel, opened = Event(), Event()

    class LateService(FakeService):
        signed_out = False

        def finish_google_sign_in(self, code):
            cancel.set()
            return "user"

        def sign_out(self):
            self.signed_out = True

    service = LateService()
    with ThreadPoolExecutor() as pool:
        future = pool.submit(
            google_sign_in,
            service,
            cancel,
            opener=lambda _: opened.set() or True,
            port=0,
            timeout=3,
        )
        assert opened.wait(2)
        with urlopen(service.redirect + "?code=valid-code", timeout=2):
            pass
        with pytest.raises(InterruptedError):
            future.result(3)
    assert service.signed_out


def test_callback_rejects_foreign_host_and_oversized_query():
    from urllib.request import Request

    cancel, opened, service = Event(), Event(), FakeService()
    with ThreadPoolExecutor() as pool:
        future = pool.submit(
            google_sign_in,
            service,
            cancel,
            opener=lambda _: opened.set() or True,
            port=0,
            timeout=3,
        )
        assert opened.wait(2)
        requests = [
            Request(service.redirect + "?code=bad", headers={"Host": "evil.example"}),
            Request(service.redirect + "?code=" + "x" * 9000),
        ]
        try:
            for request in requests:
                with pytest.raises(HTTPError):
                    urlopen(request, timeout=2)
        finally:
            cancel.set()
        with pytest.raises(InterruptedError):
            future.result(3)
    assert not service.exchanged


def test_cancellation_interrupts_incomplete_http_headers():
    import socket

    service, cancel, opened = FakeService(), Event(), Event()
    with ThreadPoolExecutor() as pool:
        future = pool.submit(
            google_sign_in,
            service,
            cancel,
            opener=lambda _: opened.set() or True,
            port=0,
            timeout=10,
        )
        assert opened.wait(2)
        url = urlsplit(service.redirect)
        with socket.create_connection((url.hostname, url.port), timeout=2) as client:
            client.sendall(f"GET {url.path} HTTP/1.1\r\nHost: ".encode())
            cancel.set()
            with pytest.raises(InterruptedError):
                future.result(2)
    assert service.exchanged == []


def test_callback_page_is_branded_self_contained_and_has_safe_error_variant():
    from aedrova.identity.callback_page import CSP, render_callback

    for success in (True, False):
        page = render_callback(success).decode()
        assert "<title>Aedrova" in page
        assert "data:image/png;base64," in page
        assert "prefers-color-scheme:dark" in page
        assert "prefers-reduced-motion" in page
        assert "<script" not in page
        assert "https://" not in page
    assert "Your space is waiting." in render_callback(True).decode()
    assert "Sign-in was not completed." in render_callback(False).decode()
    assert "default-src 'none'" in CSP
    assert "frame-ancestors 'none'" in CSP
