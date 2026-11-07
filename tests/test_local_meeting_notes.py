from pathlib import Path
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget

from aedrova.desktop.local_meeting_notes import LocalMeetingNotes
from aedrova.meetings.local_capture import LocalCapture, validate_chunk
from aedrova.meetings.local_speech import draft_notes, render_transcript


def test_capture_requires_consent_before_any_native_process(qtbot):
    capture = LocalCapture()
    with pytest.raises(PermissionError):
        capture.start(consent=False)
    assert not capture.active
    assert capture.temporary is None


def test_chunk_rejects_traversal_symlinks_size_and_bad_offsets(tmp_path):
    name = "computer-00000000-0000-0000-0000-000000000000.wav"
    path = tmp_path / name
    path.write_bytes(b"wave")
    event = {"file": name, "source": "computer", "offset": 1.0}
    assert validate_chunk(tmp_path, event) == path
    for change in (
        {"file": "../outside.wav"},
        {"offset": -1},
        {"offset": float("nan")},
        {"source": "other"},
        {"offset": 9000},
    ):
        with pytest.raises(ValueError):
            validate_chunk(tmp_path, {**event, **change})
    path.unlink()
    outside = tmp_path / "outside"
    outside.write_bytes(b"private")
    path.symlink_to(outside)
    with pytest.raises(ValueError):
        validate_chunk(tmp_path, event)


def rows():
    return [
        {
            "source": "computer",
            "offset": 15,
            "start": 1,
            "end": 3,
            "text": "We agreed to review Friday.",
        },
        {"source": "microphone", "offset": 0, "start": 2, "end": 4, "text": "Hello everyone."},
    ]


def test_transcript_is_chronological_and_notes_do_not_invent_speakers_or_decisions():
    text = render_transcript(rows())
    assert text.startswith("[00:02] Microphone: Hello everyone.")
    assert "[00:16] Computer audio: We agreed" in text
    assert draft_notes(rows()) == "• We agreed to review Friday."


class Capture(QObject):
    status = Signal(str)
    segment = Signal(dict)
    finished = Signal()
    active = False
    started = False
    discarded = False

    def start(self, *, consent):
        assert consent
        self.active = self.started = True

    def stop(self):
        self.active = False
        self.finished.emit()

    def discard(self):
        self.discarded = True


@pytest.fixture
def notes(qtbot, monkeypatch):
    monkeypatch.setattr("aedrova.desktop.local_meeting_notes.ready", lambda: True)
    monkeypatch.setattr(LocalMeetingNotes, "detect", lambda self: None)
    window = QWidget()
    window.workspace_id, window.channel_id = "workspace", "channel"
    uploads = []

    def upload(identifier, channel, path, parent, **kwargs):
        uploads.append((identifier, channel, Path(path).read_text()))
        return "message-id"

    service = SimpleNamespace(upload_attachment=upload)
    account_capture = Capture(window)
    account = SimpleNamespace(service=service, session_closed=account_capture.finished)
    window.account_dialog = account
    queued = []
    window.connected = SimpleNamespace(
        active=True,
        refresh=lambda: None,
        enqueue=lambda key, op, done, **kwargs: queued.append((op, done)) or True,
    )
    capture = Capture()
    dialog = LocalMeetingNotes(window, capture=capture)
    qtbot.addWidget(window)
    qtbot.addWidget(dialog)
    dialog.show()
    return window, dialog, capture, queued, uploads


def test_no_recording_or_upload_on_open_and_review_before_confirm(notes):
    _, dialog, capture, queued, uploads = notes
    assert not capture.started and not queued and not uploads
    assert not dialog.start.isEnabled()
    dialog.consent.setChecked(True)
    dialog.begin()
    assert capture.started and not dialog.confirm.isEnabled()
    for row in rows():
        capture.segment.emit(row)
    capture.stop()
    assert dialog.confirm.isEnabled()
    assert not queued and not uploads
    dialog.notes.setPlainText("Reviewed: follow up Friday")
    dialog.share()
    assert len(queued) == 1 and not uploads
    op, done = queued.pop()
    done(op())
    assert len(uploads) == 1 and uploads[0][1] == "channel"
    assert "Reviewed: follow up Friday" in uploads[0][2]
    assert "Reviewed transcript" in uploads[0][2]
    assert not dialog.confirm.isEnabled()
    dialog.reject()
    assert capture.discarded


def test_changed_destination_does_not_share(notes):
    window, dialog, capture, queued, uploads = notes
    dialog.consent.setChecked(True)
    dialog.rows = rows()
    dialog.review()
    window.channel_id = "another-channel"
    dialog.share()
    assert not queued and not uploads
    assert "original" in dialog.status.text()
