import asyncio
from types import SimpleNamespace

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget

from aedrova.desktop.meeting_wrapup import MeetingWrapup, offer_wrapup
from aedrova.meetings.call import CallWorker


def rows():
    return [dict(id=f"segment-{i}", body=f"Original {i}", speaker_id="speaker",
                 offset_ms=i * 10000, review_version=i, ai_allowed=i == 0)
            for i in range(2)]


class Client:
    def __init__(self):
        self.saved = []
        self.ready = True
        self.fail = False

    def wrapup(self, meeting):
        return dict(meeting=meeting, ready=self.ready)

    def transcript(self, meeting, page):
        return rows() if page == 0 else []

    def confirm_transcript(self, meeting, segments):
        if self.fail:
            raise PermissionError("revoked")
        self.saved.append((meeting, segments))
        return dict(confirmed=len(segments))


def test_review_drafts_switch_segments_and_confirm_once(qtbot):
    client = Client()
    dialog = MeetingWrapup(None, client, "meeting")
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitUntil(lambda: not dialog.busy and len(dialog.rows) == 2)
    dialog.edit.setPlainText("Corrected first part")
    dialog.sources.setCurrentRow(1)
    dialog.edit.setPlainText("Corrected second part")
    dialog.sources.setCurrentRow(0)
    assert dialog.edit.toPlainText() == "Corrected first part"
    assert not client.saved
    assert "1 permitted" in dialog.status.text()
    dialog.submit()
    dialog.submit()
    qtbot.waitUntil(lambda: dialog.closed)
    assert client.saved == [("meeting", [
        dict(identifier="segment-0", version=0, body="Corrected first part"),
        dict(identifier="segment-1", version=1, body="Corrected second part")])]
    assert not dialog.rows and not dialog.edit.toPlainText()


def test_active_or_unauthorized_meeting_never_offers_text(qtbot):
    client = Client()
    client.ready = False
    dialog = MeetingWrapup(None, client, "meeting")
    qtbot.addWidget(dialog)
    qtbot.waitUntil(lambda: not dialog.busy)
    assert not dialog.rows and not dialog.confirm.isEnabled() and dialog.retry.isVisibleTo(dialog)
    assert not client.saved
    dialog.reject()


def test_rejected_confirmation_clears_private_drafts_and_allows_reload(qtbot):
    client = Client()
    dialog = MeetingWrapup(None, client, "meeting")
    qtbot.addWidget(dialog)
    qtbot.waitUntil(lambda: not dialog.busy and bool(dialog.rows))
    dialog.edit.setPlainText("")
    assert not dialog.confirm.isEnabled()
    dialog.edit.setPlainText("Correction")
    client.fail = True
    dialog.submit()
    qtbot.waitUntil(lambda: not dialog.busy)
    assert not dialog.rows and not dialog.drafts and not dialog.edit.toPlainText()
    assert dialog.retry.isVisibleTo(dialog)
    client.fail = False
    dialog.load()
    qtbot.waitUntil(lambda: not dialog.busy and bool(dialog.rows))
    dialog.reject()


def test_leave_queries_status_only_after_successful_cleanup(qapp):
    calls = []
    client = SimpleNamespace(
        leave=lambda _: calls.append("leave"),
        wrapup=lambda m: calls.append("wrapup") or dict(meeting=m, ready=True))
    worker = CallWorker(client, workspace="w", channel="c", user="u")
    worker.meeting, worker.text_available = "meeting", True
    asyncio.run(worker._cleanup())
    assert calls == ["leave", "wrapup"] and worker.wrapup_status["ready"]
    worker.text_available = False
    calls.clear()
    asyncio.run(worker._cleanup())
    assert calls == ["leave"]


def test_late_review_cannot_reopen_for_a_different_account_or_new_call():
    worker = SimpleNamespace(meeting="meeting", user="old-user")
    window = SimpleNamespace(meeting_call=SimpleNamespace(worker=worker),
        account_dialog=SimpleNamespace(service=SimpleNamespace(user=SimpleNamespace(id="new-user"))))
    offer_wrapup(window, worker, dict(meeting="meeting", ready=True))
    assert not hasattr(window, "meeting_wrapup")


def test_authorized_wrapup_replaces_ended_call_once_without_reactivating_window(monkeypatch):
    calls = []
    class Dialog:
        def __init__(self, *args, **kwargs):
            calls.append("review created")
        def open(self):
            calls.append("review opened")
    monkeypatch.setattr("aedrova.desktop.meeting_wrapup.MeetingWrapup", Dialog)
    worker = SimpleNamespace(meeting="meeting", user="u", workspace="w", client=object())
    current = SimpleNamespace(worker=worker, names={}, accept=lambda: calls.append("call closed"))
    window = SimpleNamespace(workspace_id="w", meeting_call=current,
        account_dialog=SimpleNamespace(service=SimpleNamespace(user=SimpleNamespace(id="u"))))
    status = dict(meeting="meeting", ready=True)
    offer_wrapup(window, worker, status)
    offer_wrapup(window, worker, status)
    assert calls == ["call closed", "review created", "review opened"]


def test_admin_leaving_just_before_group_gets_review_only_after_server_end(qtbot, monkeypatch):
    calls = []
    class FastTimer(QTimer):
        def setInterval(self, _):  # noqa: N802
            super().setInterval(10)
    class Dialog:
        def __init__(self, *a, **kw):
            calls.append("review")
        def open(self):
            pass
    monkeypatch.setattr("aedrova.desktop.meeting_wrapup.QTimer", FastTimer)
    monkeypatch.setattr("aedrova.desktop.meeting_wrapup.MeetingWrapup", Dialog)
    window = QWidget()
    qtbot.addWidget(window)
    window.workspace_id = "w"
    window.account_dialog = SimpleNamespace(service=SimpleNamespace(user=SimpleNamespace(id="u")))
    worker = SimpleNamespace(meeting="m", user="u", workspace="w",
        client=SimpleNamespace(wrapup=lambda _: dict(meeting="m", ready=True, can_review=True)))
    current = SimpleNamespace(worker=worker, names={}, accept=lambda: calls.append("call closed"))
    window.meeting_call = current
    offer_wrapup(window, worker, dict(meeting="m", ready=False, can_review=True))
    assert not calls
    qtbot.waitUntil(lambda: calls == ["call closed", "review"])
    offer_wrapup(window, worker, dict(meeting="m", ready=True, can_review=True))
    assert calls == ["call closed", "review"]
