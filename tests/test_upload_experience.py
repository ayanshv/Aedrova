"""Uploads must not block chat, misreport progress or publish cancelled content."""

from threading import Event
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from test_connected import setup

from aedrova.desktop.upload_progress import UploadProgress
from aedrova.identity.transfers import UploadCancelled, UploadReader


def test_multipart_progress_measures_bytes_and_cancellation_stops_next_chunk():
    cancel, updates = Event(), []
    with UploadReader(b"abcdefgh", cancel.is_set, updates.append) as stream:
        assert stream.read(2) == b"ab"
        assert updates == ["Uploading · 25%"]
        assert stream.read(2) == b"cd"
        assert updates[-1] == "Uploading · 50%"
        cancel.set()
        with pytest.raises(UploadCancelled):
            stream.read(2)
        assert stream.tell() == 4
    assert updates == ["Uploading · 25%", "Uploading · 50%"]


def test_slow_isolated_upload_does_not_block_sending_chat(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    qtbot.waitUntil(lambda: not window.account_dialog.busy)
    entered, release = Event(), Event()
    closed, sends = Mock(), []

    def transfer(*args, **kwargs):
        entered.set()
        assert release.wait(5)
        return "uploaded-message"

    clone = SimpleNamespace(upload_attachment=transfer, close_context=closed)
    service.fork_for_context = lambda: clone
    service.rpc = lambda name, params: sends.append(name) or "chat-message"
    source = tmp_path / "brief.txt"
    source.write_text("Team brief")
    try:
        assert window.connected.upload(str(source))
        qtbot.waitUntil(entered.is_set)
        window.composer.editor.setPlainText("Keep talking while the file uploads")
        window.send_message("Keep talking while the file uploads")
        qtbot.waitUntil(lambda: "send_message" in sends)
        assert not release.is_set()
        assert window.composer.editor.toPlainText() == ""
    finally:
        release.set()
        qtbot.waitUntil(lambda: not window.connected.upload_jobs)
    closed.assert_called_once()


def test_cancelled_queued_upload_never_opens_an_isolated_session(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    qtbot.waitUntil(lambda: not window.account_dialog.busy)
    factory = Mock()
    service.fork_for_context = factory
    source = tmp_path / "brief.txt"
    source.write_text("Team brief")
    # Hold the account queue long enough to cancel before preparation starts.
    window.account_dialog.busy = True
    window.connected.upload(str(source))
    window.composer.findChildren(UploadProgress)[0].cancel()
    window.account_dialog.busy = False
    window.connected.refresh()
    qtbot.waitUntil(lambda: not window.connected.pending)
    factory.assert_not_called()


def test_completed_status_ignores_late_transfer_updates(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    progress = UploadProgress(window.composer, "brief.txt")
    progress.progress("Uploading · 43%")
    assert progress.meter.maximum() == 100 and progress.meter.value() == 43
    progress.complete("Shared · verified securely", success=True)
    progress.progress("Uploading · 99%")
    assert progress.state.text() == "Shared ✓"
    assert not progress.meter.isVisible()


def test_upload_wake_is_throttled_and_never_sends_user_data(monkeypatch):
    from aedrova.identity import media

    requests = []
    real_client = __import__("httpx").Client
    httpx = __import__("httpx")
    origin = "https://aedrova-beta-staging.onrender.com"
    media._warm_at.pop(origin, None)

    def reply(request):
        requests.append(request)
        return httpx.Response(200)

    class ImmediateThread:
        def __init__(self, *, target, **kwargs):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(media, "Thread", ImmediateThread)
    monkeypatch.setattr(
        media.httpx,
        "Client",
        lambda **kwargs: real_client(transport=httpx.MockTransport(reply), **kwargs),
    )
    media.warm_upload_verifier(origin)
    media.warm_upload_verifier(origin)
    assert len(requests) == 1
    assert requests[0].url.path == "/health"
    assert "authorization" not in requests[0].headers and not requests[0].content
    with pytest.raises(ValueError):
        media.warm_upload_verifier("http://untrusted.test")


def test_mid_transfer_cancellation_never_calls_publication(tmp_path):
    from aedrova.identity.service import Connection, IdentityService

    cancel, calls = Event(), []
    source = tmp_path / "notes.txt"
    source.write_bytes(b"a" * 100000)

    def upload(path, stream, options):
        assert stream.read(65536)
        cancel.set()
        stream.read(65536)

    bucket = SimpleNamespace(upload=upload, remove=lambda _: calls.append("remove"))
    client = SimpleNamespace(storage=SimpleNamespace(from_=lambda _: bucket))
    service = IdentityService(
        Connection("https://project.test", "sb_publishable_abcdefghijk"), client=client
    )

    def rpc(name, params):
        calls.append(name)
        return "workspace/channel/file"

    service.rpc = rpc
    assert service.upload_attachment("file", "channel", source, cancelled=cancel.is_set) is None
    assert calls == ["reserve_attachment", "remove", "abandon_attachment"]


def test_logout_during_preparation_closes_clone_without_starting_transfer(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    qtbot.waitUntil(lambda: not window.account_dialog.busy)
    entered, release = Event(), Event()
    clone = SimpleNamespace(upload_attachment=Mock(), close_context=Mock())

    def factory():
        entered.set()
        assert release.wait(5)
        return clone

    service.fork_for_context = factory
    source = tmp_path / "brief.txt"
    source.write_text("Team brief")
    try:
        window.connected.upload(str(source))
        qtbot.waitUntil(entered.is_set)
        window.connected.disconnect()
    finally:
        release.set()
        qtbot.waitUntil(lambda: not window.account_dialog.busy)
    clone.close_context.assert_called_once()
    clone.upload_attachment.assert_not_called()
    assert not window.connected.cache and not window.connected.files


def test_picker_accepts_multiple_files_in_one_selection(qtbot, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QFileDialog

    window, service = setup(qtbot, tmp_path)
    qtbot.waitUntil(lambda: not window.account_dialog.busy)
    files = [tmp_path / "brief.txt", tmp_path / "notes.txt"]
    for path in files:
        path.write_text("Team note")
    uploaded = []
    service.upload_attachment = lambda *a, **kw: uploaded.append(a[2]) or "message"
    monkeypatch.setattr(QFileDialog, "getOpenFileNames", lambda *a: (list(map(str, files)), ""))
    window.connected.upload()
    assert not uploaded
    window.composer._submit()
    qtbot.waitUntil(lambda: len(uploaded) == 2 and not window.connected.pending)
    assert uploaded == list(map(str, files))


@pytest.mark.parametrize("voice", [False, True])
def test_media_echo_precedes_transfer_and_receipt_reconciles(qtbot, tmp_path, voice):
    from test_connected import row

    window, service = setup(qtbot, tmp_path)
    qtbot.waitUntil(lambda: not window.account_dialog.busy)
    entered, release = Event(), Event()
    captured = []

    def transfer(identifier, *args, **kwargs):
        captured.append(identifier)
        entered.set()
        assert release.wait(5)
        return "verified-message"

    service.fork_for_context = lambda: SimpleNamespace(
        upload_attachment=transfer, close_context=lambda: None
    )
    source = tmp_path / ("voice-message-1s.wav" if voice else "brief.txt")
    source.write_bytes(b"local preview")
    try:
        assert window.connected.upload(str(source), voice_data=b"audio" if voice else None)
        local = window.channel.messages[-1]
        assert local.id.startswith("upload-")
        assert local.attachment == source.name
        assert not local.attachment_id  # Unverified bytes cannot be downloaded/shared.
        assert local.delivery == "Sending…"
        qtbot.waitUntil(entered.is_set)
        assert not release.is_set()
    finally:
        release.set()
        qtbot.waitUntil(lambda: not window.connected.upload_jobs)
    assert not any(m.id.startswith("upload-") for m in window.channel.messages)
    assert sum(m.id == "verified-message" for m in window.channel.messages) == 1
    assert window.channel.messages[-1].delivery == ""
    # A later realtime receipt replaces the acknowledgement rather than duplicating it.
    message = row("verified-message")
    window.connected.cache.setdefault("c", {})[message["id"]] = message
    window.connected.apply(service.snapshot(), [message], "w", "c")
    assert sum(m.id == "verified-message" for m in window.channel.messages) == 1
    assert not window.connected.outbox


@pytest.mark.parametrize("failure", [ValueError("Invalid file"), RuntimeError("offline")])
def test_failed_media_echo_is_explicit_and_removable(qtbot, tmp_path, failure):
    window, service = setup(qtbot, tmp_path)
    qtbot.waitUntil(lambda: not window.account_dialog.busy)

    def transfer(*args, **kwargs):
        raise failure

    service.fork_for_context = lambda: SimpleNamespace(
        upload_attachment=transfer, close_context=lambda: None
    )
    source = tmp_path / "brief.txt"
    source.write_text("Original remains available")
    assert window.connected.upload(str(source))
    qtbot.waitUntil(lambda: not window.connected.pending)
    local = next(m for m in window.channel.messages if m.id.startswith("upload-"))
    assert local.delivery.startswith(
        "Not sent" if isinstance(failure, ValueError) else "Delivery unconfirmed"
    )
    window.connected.dismiss_local_message(local.id)
    assert not any(m.id == local.id for m in window.channel.messages)
    assert source.exists()


def test_voice_card_has_no_redundant_body_label(qtbot, tmp_path):
    from aedrova.desktop.state import Message

    window, _ = setup(qtbot, tmp_path)
    voice = Message(
        "voice",
        "You",
        "Y",
        "12:00",
        "Shared a file: voice-message-1s.wav",
        attachment="voice-message-1s.wav",
        attachment_id="verified",
        mine=True,
    )
    text = window.messages.delegate.document(voice, 400).toPlainText()
    assert not text.strip()
