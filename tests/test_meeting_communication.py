import asyncio
import time
from types import SimpleNamespace
from unittest.mock import Mock

from PySide6.QtCore import QObject, Signal

from aedrova.desktop.meeting_communication import MeetingCaptions, MeetingChat
from aedrova.desktop.meeting_privacy import MeetingPrivacy
from aedrova.desktop.meeting_transcript import TranscriptReview
from aedrova.meetings.call import CallWorker


def snapshot():
    return dict(
        id="meeting",
        revision=1,
        participants=[
            dict(user_id="u", transcription=True, ai_context=False),
        ],
    )


def test_channel_chat_uses_fixed_channel_and_idempotent_retry(qtbot):
    calls = []
    fail = [True]

    def rpc(name, data):
        calls.append((name, data))
        if fail[0]:
            raise TimeoutError()

    service = SimpleNamespace(
        user=SimpleNamespace(id="u"), rpc=rpc, message_page=lambda *a, **k: []
    )
    dialog = MeetingChat(None, service, "channel", "u")
    qtbot.addWidget(dialog)
    qtbot.waitUntil(lambda: not dialog.busy)
    dialog.timer.stop()
    dialog.editor.setPlainText("hello team")
    dialog.submit()
    qtbot.waitUntil(lambda: not dialog.busy)
    assert dialog.editor.toPlainText() == "hello team"
    fail[0] = False
    dialog.submit()
    qtbot.waitUntil(lambda: not dialog.busy and not dialog.editor.toPlainText())
    assert calls[0] == calls[1]
    assert calls[0][1]["p_channel"] == "channel"
    dialog.reject()
    assert not dialog.pending


def test_channel_chat_clears_text_on_revocation_and_stops_on_account_change(qtbot):
    service = SimpleNamespace(
        user=SimpleNamespace(id="u"),
        message_page=lambda *a, **k: [
            dict(channel_id="c", sender_id="u", body="private"),
        ],
    )
    dialog = MeetingChat(None, service, "c", "u")
    qtbot.addWidget(dialog)
    qtbot.waitUntil(lambda: not dialog.busy)
    assert "private" in dialog.text.toPlainText()
    dialog.loaded(dict(error="Access denied"))
    assert not dialog.text.toPlainText()
    dialog.loaded(dict(value=[dict(channel_id="other", sender_id="u", body="wrong")]))
    assert not dialog.text.toPlainText()
    service.user.id = "another"
    dialog.refresh()
    assert dialog.closed and not dialog.timer.isActive()


def test_caption_result_discarded_when_consent_changes_in_flight(qtbot):
    import threading

    entered, release = threading.Event(), threading.Event()

    def captions(_):
        entered.set()
        release.wait(2)
        return [dict(meeting_id="meeting", speaker_id="u", body="private speech")]

    worker = SimpleNamespace(
        snapshot=snapshot(),
        snapshot_at=time.monotonic(),
        connected=True,
        text_available=True,
        meeting="meeting",
        client=SimpleNamespace(captions=captions),
    )
    dialog = MeetingCaptions(None, worker, people=lambda: {"u"}, names=lambda: {"u": "You"})
    qtbot.addWidget(dialog)
    qtbot.waitUntil(entered.is_set)
    worker.snapshot["participants"][0]["transcription"] = False
    release.set()
    qtbot.waitUntil(lambda: not dialog.busy)
    assert not dialog.text.toPlainText()
    dialog.reject()


def test_caption_view_is_read_only_and_clears_on_stale_snapshot(qtbot):
    client = SimpleNamespace(
        captions=lambda _: [
            dict(meeting_id="meeting", speaker_id="u", body="Unreviewed speech"),
        ]
    )
    worker = SimpleNamespace(
        snapshot=snapshot(),
        snapshot_at=time.monotonic(),
        connected=True,
        text_available=True,
        meeting="meeting",
        client=client,
    )
    dialog = MeetingCaptions(None, worker, people=lambda: {"u"}, names=lambda: {"u": "You"})
    qtbot.addWidget(dialog)
    qtbot.waitUntil(lambda: not dialog.busy)
    assert dialog.text.isReadOnly() and "Unreviewed speech" in dialog.text.toPlainText()
    dialog.size.setCurrentIndex(2)
    assert dialog.text.font().pixelSize() == 22
    worker.snapshot_at -= 11
    dialog.check_consent()
    assert not dialog.text.toPlainText()
    dialog.reject()
    assert not dialog.timer.isActive() and not dialog.guard.isActive()


class PrivacyWorker(QObject):
    privacy_result = Signal(str, str, bool)
    user = "u"
    speech_available = False

    def __init__(self):
        super().__init__()
        self.command = Mock()


def test_privacy_waits_for_ack_failure_retry_and_success(qtbot):
    worker = PrivacyWorker()
    dialog = MeetingPrivacy(None, worker, snapshot())
    qtbot.addWidget(dialog)
    dialog.save(worker)
    assert not dialog.closed and dialog.pending == "consent"
    dialog.save(worker)
    assert worker.command.call_count == 1
    worker.privacy_result.emit(dialog.request_id, "withdraw_text", True)
    assert not dialog.closed
    worker.privacy_result.emit(dialog.request_id, "consent", False)
    assert not dialog.closed and not dialog.pending
    assert "Could not verify" in dialog.feedback.text()
    dialog.save(worker)
    worker.privacy_result.emit(dialog.request_id, "consent", True)
    assert dialog.closed


def test_worker_privacy_error_does_not_emit_unknown_media_kind(qapp):
    client = SimpleNamespace(consent=Mock(side_effect=PermissionError()))
    worker = CallWorker(client, workspace="w", channel="c", user="u")
    result, media = [], []
    worker.privacy_result.connect(lambda *args: result.append(args))
    worker.media.connect(lambda *args: media.append(args))

    async def run():
        worker.lock = asyncio.Lock()
        await worker._media("consent", dict(transcription=False, ai_context=False))

    asyncio.run(run())
    assert result == [("", "consent", False)] and not media


def test_transcript_edits_survive_selection_search_and_review(qtbot):
    rows = [
        dict(id=str(i), body=f"Original {i}", speaker_id="u", offset_ms=0, review_version=0)
        for i in range(2)
    ]
    saved = []
    client = SimpleNamespace(transcript=lambda *a: rows, review=lambda *a: saved.append(a))
    dialog = TranscriptReview(None, client, meeting="meeting")
    qtbot.addWidget(dialog)
    qtbot.waitUntil(lambda: not dialog.busy)
    dialog.edit.setPlainText("Corrected first")
    dialog.sources.setCurrentRow(1)
    dialog.edit.setPlainText("Corrected second")
    dialog.sources.setCurrentRow(0)
    assert dialog.edit.toPlainText() == "Corrected first"
    dialog.review()
    qtbot.waitUntil(lambda: not dialog.busy)
    assert saved == [("0", 0, "Corrected first", False)]
    assert "1" in dialog.drafts
    dialog.sources.setCurrentRow(1)
    assert dialog.edit.toPlainText() == "Corrected second"
    dialog.search.setText("original 0")
    assert dialog.sources.item(1).isHidden()
    dialog.finish()
    assert not dialog.drafts and not dialog.edit.toPlainText()


def test_late_privacy_ack_does_not_close_a_new_request(qtbot):
    worker = PrivacyWorker()
    dialog = MeetingPrivacy(None, worker, snapshot())
    qtbot.addWidget(dialog)
    dialog.save(worker)
    old = dialog.request_id
    dialog.completed(old, "consent", False)
    dialog.save(worker)
    worker.privacy_result.emit(old, "consent", True)
    assert not dialog.closed and dialog.pending == "consent"
    dialog.reject()


def test_closing_call_clears_channel_chat_and_pending_draft(qtbot):
    from test_meeting_calls import Backend, Worker

    from aedrova.desktop.meeting_call import MeetingCall
    from aedrova.meetings.devices import DeviceCheck

    worker = Worker()
    service = SimpleNamespace(user=SimpleNamespace(id="self"), message_page=lambda *a, **k: [])
    call = MeetingCall(None, worker, devices=DeviceCheck(backend=Backend()),
        channel_chat=dict(service=service, channel="c", user="self"))
    qtbot.addWidget(call)
    call.call_state("Connected")
    call.show_chat()
    chat = call.text_dialogs["chat"]
    qtbot.waitUntil(lambda: not chat.busy)
    chat.editor.setPlainText("local draft")
    worker.ended.emit()
    assert chat.closed and not chat.editor.toPlainText() and not call.text_dialogs
    assert not call.chat_button.isEnabled()
    call.reject()
