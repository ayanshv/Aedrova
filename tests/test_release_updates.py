"""Read-only checks never accept preview, mismatched or malformed releases."""

import json
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import pytest

from aedrova.delivery.releases import check_release, validate_release, version_tuple


def release(**changes):
    return {
        "version": "0.1.1",
        "public_release": True,
        "architecture": "arm64",
        "minimum_macos": "14.0",
        "sha256": "a" * 64,
        **changes,
    }


@pytest.mark.parametrize(
    "changes",
    [
        {"public_release": False},
        {"version": "javascript:alert(1)"},
        {"architecture": "x86_64"},
        {"sha256": "bad"},
        {"minimum_macos": ""},
    ],
)
def test_invalid_release_rejected(changes):
    with pytest.raises(ValueError):
        validate_release(release(**changes), machine="arm64", macos="15.0")


def test_version_comparison_and_mac_compatibility():
    assert version_tuple("0.1.10") > version_tuple("0.1.2")
    assert validate_release(release(), machine="arm64", macos="14.0")["version"] == "0.1.1"
    with pytest.raises(ValueError, match="newer macOS"):
        validate_release(release(), machine="arm64", macos="13.6")


def test_untrusted_update_origins_do_not_make_network_requests():
    with pytest.raises(ValueError, match="verified"):
        check_release("http://untrusted.example")


@pytest.mark.parametrize("value", [[], None, "invalid", 7])
def test_invalid_metadata_shape(value):
    with pytest.raises(ValueError, match="invalid"):
        validate_release(value)


@pytest.mark.parametrize(
    "origin",
    [
        "https://user:secret@example.com",
        "https://example.com/path",
        "https://example.com?token=secret",
        "https:///",
    ],
)
def test_update_origin_cannot_contain_credentials_or_paths(origin):
    with pytest.raises(ValueError, match="verified"):
        check_release(origin)


@pytest.mark.parametrize(
    "changes", [{"architecture": []}, {"sha256": None}, {"minimum_macos": 14}]
)
def test_invalid_field_types_have_readable_errors(changes):
    with pytest.raises(ValueError):
        validate_release(release(**changes))


@contextmanager
def release_server(body, status=200, location=None):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            assert self.path == "/api/release"
            self.send_response(status)
            if location:
                self.send_header("Location", location)
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_update_check_over_http_accepts_compatible_new_version(monkeypatch):
    monkeypatch.setattr("aedrova.delivery.releases.platform.machine", lambda: "arm64")
    monkeypatch.setattr("aedrova.delivery.releases.platform.mac_ver", lambda: ("15.0", (), ""))
    with release_server(json.dumps(release()).encode()) as origin:
        assert check_release(origin)["version"] == "0.1.1"


@pytest.mark.parametrize(
    "body,status,error",
    [
        (b"unavailable", 503, "not ready"),
        (b"not json", 200, "current app is unchanged"),
        (b" " * 16385, 200, "larger than expected"),
        (json.dumps(release(public_release=False)).encode(), 200, "not ready"),
        (json.dumps(release(architecture="unsupported")).encode(), 200, "architecture"),
    ],
)
def test_update_check_over_http_fails_closed(body, status, error):
    with release_server(body, status) as origin, pytest.raises(ValueError, match=error):
        check_release(origin)


def test_release_redirect_cannot_contact_another_server():
    with release_server(b"", 302, "http://127.0.0.1:1/api/release") as origin:
        with pytest.raises(ValueError, match="unexpected address"):
            check_release(origin)
