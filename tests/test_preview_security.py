"""The isolated preview must bound clients before creating worker threads."""

import http.client
import socket

from aedrova.delivery.preview import StaticPreview


def test_preview_refuses_excess_connections_and_recovers(tmp_path):
    (tmp_path / "index.html").write_text("<h1>Preview</h1>")
    preview = StaticPreview(tmp_path)
    try:
        for _ in range(8):
            assert preview.server.slots.acquire(blocking=False)
        with socket.create_connection(preview.server.server_address, timeout=1) as extra:
            assert extra.recv(1) == b""
        for _ in range(8):
            preview.server.slots.release()
        connection = http.client.HTTPConnection(*preview.server.server_address, timeout=2)
        connection.request("GET", "/")
        response = connection.getresponse()
        assert response.status == 200 and b"Preview" in response.read()
        connection.close()
    finally:
        preview.close()


def test_idle_preview_connections_expire_and_duplicate_host_is_denied(tmp_path):
    (tmp_path / "index.html").write_text("<h1>Preview</h1>")
    preview = StaticPreview(tmp_path)
    try:
        with socket.create_connection(preview.server.server_address, timeout=4) as idle:
            assert idle.recv(1) == b""
        with socket.create_connection(preview.server.server_address, timeout=2) as client:
            host = f"127.0.0.1:{preview.server.server_port}"
            client.sendall(
                f"GET / HTTP/1.1\r\nHost: {host}\r\nHost: untrusted.example\r\n\r\n".encode()
            )
            assert b"403" in client.recv(4096).split(b"\r\n", 1)[0]
    finally:
        preview.close()
