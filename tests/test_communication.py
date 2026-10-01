"""Milestone 4 history, reconnect, attachment, and private realtime contracts."""

import asyncio

import httpx
import pytest
from test_connected import row, setup, snapshot

from aedrova.identity.errors import retryable
from aedrova.identity.realtime import RealtimeWakeups
from aedrova.identity.transfers import MAX_BYTES, read_upload, save_download


def test_attachment_limits_digest_and_atomic_save(tmp_path):
    source = tmp_path / "notes.txt"
    source.write_bytes(b"abc")
    name, data, digest = read_upload(source)
    assert name == "notes.txt"
    assert digest == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    destination = tmp_path / "saved.txt"
    destination.write_bytes(b"old")
    save_download(destination, data)
    assert destination.read_bytes() == b"abc"
    assert not list(tmp_path.glob(".aedrova-*"))
    source.write_bytes(b"")
    with pytest.raises(ValueError):
        read_upload(source)
    with source.open("wb") as f:
        f.truncate(MAX_BYTES + 1)
    with pytest.raises(ValueError):
        read_upload(source)


def test_retry_classification():
    assert retryable(httpx.ConnectError("offline"))
    assert not retryable(PermissionError("forbidden"))
    assert not retryable(ValueError("bad input"))


def test_private_realtime_contract(qtbot):
    calls = []
    watcher = RealtimeWakeups()

    class Client:
        def __init__(self, url, **kwargs):
            calls.append(("init", url, kwargs))

        async def connect(self):
            pass

        async def set_auth(self, token):
            calls.append(("auth", token))

        def channel(self, topic, config):
            calls.append(("channel", topic, config))
            return self

        def on_broadcast(self, event, callback):
            calls.append(("event", event))
            return self

        async def subscribe(self, callback):
            watcher.stop()

        async def close(self):
            calls.append(("closed",))

    watcher.factory = Client
    watcher.credentials = ("https://project.test", "public", "session", "user-id")
    asyncio.run(watcher.listen())
    assert ("auth", "session") in calls
    assert ("channel", "user:user-id", {"config": {"private": True}}) in calls
    assert calls[-1] == ("closed",)


def test_older_history_and_thread_pages_are_merged(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    newest = dict(row(), sequence=200)
    older = dict(row("older"), sequence=100)
    reply = dict(row("reply", "m"), sequence=201)

    def page(channel, **kwargs):
        if kwargs.get("parent"):
            return [] if kwargs.get("after") else [reply]
        if kwargs.get("before"):
            return [older]
        return [] if kwargs.get("after") else [newest]

    service.message_page = page
    window.connected.refresh()
    qtbot.waitUntil(lambda: bool(window.channel.messages) and not window.account_dialog.busy)
    window.connected.load_older()
    qtbot.waitUntil(
        lambda: "older" in window.connected.cache.get("c", {}) and not window.account_dialog.busy
    )
    window.connected.refresh()
    qtbot.waitUntil(lambda: len(window.channel.messages) == 2 and not window.account_dialog.busy)
    window.open_thread("m")
    window.connected.refresh()
    qtbot.waitUntil(
        lambda: bool(window.channel.messages[-1].replies) and not window.account_dialog.busy
    )
    assert window.channel.messages[-1].replies[0].id == "reply"
    assert ("c", None) in window.connected.history_done


def test_queued_send_retries_same_id_after_transient_failure(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    attempts = []

    def rpc(name, parameters):
        if name != "send_message":
            return None
        attempts.append(parameters["p_id"])
        if len(attempts) == 1:
            raise httpx.ConnectError("offline")
        return parameters["p_id"]

    service.rpc = rpc
    window.composer.editor.setPlainText("Reliable")
    window.send_message("Reliable")
    qtbot.waitUntil(lambda: len(attempts) == 1 and not window.account_dialog.busy)
    assert window.connected.queue
    assert window.composer.editor.toPlainText() == "Reliable"
    window.connected.retry_at = 0
    window.connected.refresh()
    qtbot.waitUntil(lambda: len(attempts) == 2 and not window.account_dialog.busy)
    assert attempts[0] == attempts[1]
    assert window.composer.editor.toPlainText() == ""


def test_dm_maps_to_existing_list_and_unread_data(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    data = snapshot()
    data["directory"] = [{"workspace_id": "w", "user_id": "other", "display_name": "Morgan"}]
    data["channels"].append(
        {
            "id": "dm",
            "workspace_id": "w",
            "private": True,
            "name": "internal",
            "kind": "dm",
            "dm_low": "other",
            "dm_high": "u",
        }
    )
    data["unread"] = [{"channel_id": "dm", "unread": 3}]
    window.connected.apply(data, [], "w", "c")
    assert window.dm_list.count() == 1
    assert "Morgan" in window.dm_list.item(0).text()
    assert "(3)" in window.dm_list.item(0).text()


def test_revoked_channel_clears_cached_history(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    window.connected.refresh()
    qtbot.waitUntil(lambda: not window.account_dialog.busy)
    data = snapshot()
    data["channels"] = []
    service.snapshot = lambda: data
    window.connected.refresh()
    qtbot.waitUntil(lambda: not window.account_dialog.busy)
    assert "c" not in window.connected.cache
    assert not window.composer.isEnabled()


def test_private_download_is_bounded_and_verifies_digest(monkeypatch):
    import hashlib
    from types import SimpleNamespace

    from aedrova.identity.service import Connection, IdentityService

    record = {
        "id": "file",
        "object_path": "/".join(["a" * 36] * 3),
        "byte_size": 3,
        "sha256": hashlib.sha256(b"abc").hexdigest(),
        "message_id": "message",
    }

    class Query:
        def select(self, *a):
            return self

        def eq(self, *a):
            return self

        def execute(self):
            return SimpleNamespace(data=[record])

    fake = SimpleNamespace(
        table=lambda _: Query(),
        auth=SimpleNamespace(
            get_session=lambda: SimpleNamespace(access_token="session"),
            get_user=lambda: SimpleNamespace(user=SimpleNamespace(id="u")),
        ),
    )
    service = IdentityService(
        Connection("https://project.test", "sb_publishable_abcdefghijk"), client=fake
    )
    service.user = SimpleNamespace(id="u")
    real_client = httpx.Client
    requests = []

    def respond(request):
        requests.append(request)
        return httpx.Response(200, content=b"abc")

    monkeypatch.setattr(
        httpx,
        "Client",
        lambda **kwargs: real_client(transport=httpx.MockTransport(respond), **kwargs),
    )
    assert service.download_attachment("file") == b"abc"
    assert requests[-1].headers["Authorization"] == "Bearer session"
    record["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="integrity"):
        service.download_attachment("file")
    record["byte_size"] = 2
    with pytest.raises(ValueError, match="exceeded"):
        service.download_attachment("file")


def test_upload_lost_response_finalizes_same_reservation(tmp_path):
    from types import SimpleNamespace

    from aedrova.identity.service import Connection, IdentityService

    path = tmp_path / "notes.txt"
    path.write_bytes(b"abc")
    uploads, operations = [], []

    def upload(*args):
        uploads.append(args)
        raise httpx.ReadTimeout("response lost")

    fake = SimpleNamespace(storage=SimpleNamespace(from_=lambda _: SimpleNamespace(upload=upload)))
    service = IdentityService(
        Connection("https://project.test", "sb_publishable_abcdefghijk"), client=fake
    )

    def rpc(name, params):
        operations.append((name, params))
        return "workspace/channel/file" if name == "reserve_attachment" else "message-id"

    service.rpc = rpc
    assert service.upload_attachment("stable-id", "channel", path) == "message-id"
    assert [x[0] for x in operations] == ["reserve_attachment", "finish_attachment"]
    assert operations[0][1]["p_id"] == operations[1][1]["p_id"] == "stable-id"
    assert uploads[0][2]["upsert"] == "false"


def test_direct_message_action_uses_selected_teammate(qtbot, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QInputDialog

    window, service = setup(qtbot, tmp_path)
    data = snapshot()
    data["directory"] = [{"workspace_id": "w", "user_id": "peer", "display_name": "Morgan"}]
    service.snapshot = lambda: data
    calls = []

    def rpc(name, params):
        if name == "start_direct_message":
            calls.append(params)
            data["channels"].append(
                {
                    "id": "dm",
                    "workspace_id": "w",
                    "name": "internal",
                    "private": True,
                    "kind": "dm",
                    "dm_low": "peer",
                    "dm_high": "u",
                }
            )
            return "dm"

    service.rpc = rpc
    monkeypatch.setattr(QInputDialog, "getItem", lambda *a: ("Morgan · peer", True))
    window.connected.start_dm()
    qtbot.waitUntil(lambda: window.channel_id == "dm" and not window.account_dialog.busy)
    assert calls == [{"p_workspace": "w", "p_user": "peer"}]
    assert window.channel.name == "Morgan"


def test_attachment_picker_and_save_action(qtbot, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QFileDialog

    window, service = setup(qtbot, tmp_path)
    source, destination = tmp_path / "source.txt", tmp_path / "download.txt"
    source.write_bytes(b"abc")
    uploads = []

    def upload(*args):
        uploads.append(args)
        return "message"

    service.upload_attachment = upload
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a: (str(source), ""))
    window.connected.upload()
    qtbot.waitUntil(lambda: bool(uploads) and not window.account_dialog.busy)
    assert uploads[0][1:3] == ("c", str(source))
    file = {"id": "file", "message_id": "m", "channel_id": "c", "filename": "notes.txt"}
    service.attachments_for = lambda _: [file]
    window.connected.last_view = None
    window.connected.refresh()
    qtbot.waitUntil(
        lambda: (
            bool(window.channel.messages)
            and window.channel.messages[0].attachment_id == "file"
            and not window.account_dialog.busy
        )
    )
    window.messages.setCurrentIndex(window.messages.model().index(0, 0))
    service.download_attachment = lambda _: b"abc"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *a: (str(destination), ""))
    window.connected.download()
    qtbot.waitUntil(lambda: destination.exists() and not window.account_dialog.busy)
    assert destination.read_bytes() == b"abc"
