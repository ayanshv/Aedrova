"""Meeting evidence permissions, withdrawal races and explicit UI choices."""
import json
import os
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication
from test_builds import service

from aedrova.agents.context import gather
from aedrova.agents.retrieval import ContextIndex, validate_citations
from aedrova.desktop.meeting_privacy import MeetingPrivacy
from aedrova.meetings.access import MeetingClient
from aedrova.meetings.consent import CapturePermit


def segment():
    return dict(id="segment", channel_id="c", meeting_id="meeting", speaker_id="u",
                body="Launch meeting evidence", created_at="2026-10-03T00:00:00Z",
                offset_ms=250, source="participant_text", ai_allowed=True)


def source_context(row):
    return SimpleNamespace(channel_ids={"c"}, text=json.dumps({"meeting_text": row}))


def test_attribution_and_citations():
    context = source_context(segment())
    index = ContextIndex(context)
    evidence = index.sources[0]
    assert evidence.speaker == "u" and evidence.meeting == "meeting"
    assert evidence.offset_ms == 250 and evidence.decision == "participant_text"
    assert validate_citations(context, "Use [meeting:segment].") == ["meeting:segment"]


@pytest.mark.parametrize("field,value", [("channel_id", "private"),
                                         ("ai_allowed", False), ("source", "provider")])
def test_untrusted_meeting_evidence_rejected(field, value):
    row = segment()
    row[field] = value
    with pytest.raises(PermissionError):
        ContextIndex(source_context(row))


def test_disabled_feature_never_queries_unapplied_migration():
    source = service()
    source.meeting_context_enabled = False
    def forbidden(channel):
        raise AssertionError("Disabled feature queried meeting SQL")
    source.meeting_context = forbidden
    assert gather(source, "w").count == 4


def test_consented_evidence_enters_scoped_context():
    source = service()
    source.meeting_context_enabled = True
    source.meeting_context = lambda channel: [segment()] if channel == "c" else []
    context = gather(source, "w")
    assert '"meeting_text"' in context.text
    assert ContextIndex(context).sources[-1].speaker == "u"


def test_withdrawal_during_gather_fails_closed():
    source = service()
    source.meeting_context_enabled = True
    calls = {}
    def changing(channel):
        calls[channel] = calls.get(channel, 0) + 1
        return [segment()] if channel == "c" and calls[channel] == 1 else []
    source.meeting_context = changing
    with pytest.raises(ValueError, match="Meeting consent or retention changed"):
        gather(source, "w")


def test_append_requires_permit_and_never_claims_speaker():
    client = MeetingClient("http://127.0.0.1:8090", "fixture")
    sent = []
    client.request = lambda path, body: sent.append((path, body))
    with pytest.raises(PermissionError):
        client.append_text("meeting", identifier="segment", permit=None, body="text")
    client.append_text("meeting", identifier="segment", body="text",
                       permit=CapturePermit("meeting", 2, frozenset({"u", "v"}), True))
    assert sent[0][1]["roster"] == ["u", "v"]
    assert "speaker" not in sent[0][1] and "speaker_id" not in sent[0][1]


def test_older_server_cannot_enable_text():
    client = MeetingClient("http://127.0.0.1:8090", "fixture")
    def unavailable(path):
        raise RuntimeError("Not found")
    client.request = unavailable
    assert client.capabilities()["meeting_text"] is False


def test_ui_choices_start_unchecked_and_storage_controls_ai():
    app = QApplication.instance() or QApplication([])
    commands = []
    worker = SimpleNamespace(user="u", command=lambda *args: commands.append(args))
    dialog = MeetingPrivacy(None, worker, {})
    assert not dialog.transcription.isChecked() and not dialog.ai_context.isEnabled()
    dialog.transcription.setChecked(True)
    dialog.ai_context.setChecked(True)
    dialog.transcription.setChecked(False)
    assert not dialog.ai_context.isChecked()
    dialog.save(worker)
    assert commands == [("consent", {"transcription": False, "ai_context": False})]
    dialog.deleteLater()
    app.processEvents()


def test_ui_withdrawal_is_explicit():
    app = QApplication.instance() or QApplication([])
    commands = []
    worker = SimpleNamespace(user="u", command=lambda *args: commands.append(args))
    dialog = MeetingPrivacy(None, worker, {})
    assert not commands
    dialog.withdraw(worker, False)
    assert commands == [("withdraw_text", {"delete": False})]
    dialog.deleteLater()
    app.processEvents()
