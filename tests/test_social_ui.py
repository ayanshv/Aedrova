"""Native review flow: edits invalidate approval and no draft silently dispatches."""

import pytest
from PySide6.QtWidgets import QWidget
from test_connected import setup

from aedrova.desktop.social import SocialDialog
from aedrova.desktop.theme import DARK, LIGHT, palette, stylesheet


@pytest.fixture
def social(qtbot, tmp_path, monkeypatch):
    window, _ = setup(qtbot, tmp_path)
    callbacks = []
    monkeypatch.setattr(SocialDialog, "run", lambda self, op, done, **kw: callbacks.append(done))
    chat = QWidget(window)
    chat.host, chat.workspace, chat.user = window, window.workspace_id, "u"
    chat.bud = {"id": "bud-1", "name": "Social Bud", "role": "Marketing"}
    chat.current = lambda: True
    chat.history = [{"role": "assistant", "body": "A caption to review."}]
    dialog = SocialDialog(chat)
    qtbot.addWidget(dialog)
    dialog.show()
    channel = dict(
        id="channel-1",
        connection="connection-1",
        name="Test profile",
        platform="linkedin",
        selected=True,
        can_publish=True,
    )
    dialog.loaded(({"channels": [channel]}, {"posts": []}, {"available": True}))
    calls = []
    monkeypatch.setattr(dialog, "request", lambda path, body, done: calls.append((path, body)))
    return dialog, calls


def approved():
    return dict(
        id="post-1",
        connection="connection-1",
        channel="channel-1",
        revision=1,
        state="approved",
        provider_status="",
        content={"text": "Approved caption.", "action": "publish", "assets": [], "due_at": None},
    )


def test_edited_approval_only_saves_and_never_dispatches(social):
    dialog, calls = social
    dialog.post_list.addItem("Approved caption", approved())
    dialog.post_list.setCurrentIndex(1)
    assert dialog.primary.text() == "Publish now"
    dialog.editor.setPlainText("An edited caption.")
    assert dialog.primary.text() == "Save draft"
    dialog.act()
    assert [c[0] for c in calls] == ["drafts"]
    assert calls[0][1]["text"] == "An edited caption."


def test_unknown_submission_is_not_editable_or_retried(social):
    dialog, calls = social
    row = {**approved(), "state": "unknown", "error": "Check Buffer"}
    dialog.post_list.addItem("Unconfirmed", row)
    dialog.post_list.setCurrentIndex(1)
    assert dialog.editor.isReadOnly()
    assert not dialog.destination.isEnabled()
    assert not dialog.reject_post.isEnabled()
    dialog.act()
    assert [c[0] for c in calls] == ["status"]


def test_latest_reply_is_a_local_draft_until_saved(social):
    dialog, calls = social
    dialog.use_reply()
    assert dialog.editor.toPlainText() == "A caption to review."
    assert dialog.primary.text() == "Save draft"
    assert not calls
    dialog.act()
    assert calls[0][0] == "drafts"


def test_preparation_state_has_no_dead_connect_button(social):
    dialog, _ = social
    dialog.loaded(
        (
            {"channels": []},
            {"posts": []},
            {"available": False, "setup_hint": "Owner setup is required."},
        )
    )
    dialog.update_controls()
    assert dialog.connect_button.isHidden()
    assert not dialog.pages.isEnabled()
    assert "Owner setup" in dialog.status.text()


@pytest.mark.parametrize("theme", [LIGHT, DARK])
def test_social_review_is_readable_in_both_themes(social, theme, qtbot):
    dialog, _ = social
    dialog.setPalette(palette(theme))
    dialog.setStyleSheet(stylesheet(theme))
    dialog.pages.setCurrentIndex(1)
    dialog.resize(680, 760)
    qtbot.waitUntil(lambda: dialog.editor.width() > 100)
    assert dialog.primary.isVisible() and dialog.primary.width() >= 44
    assert dialog.destination.isVisible()
    assert not dialog.grab().isNull()


def test_provider_rejection_is_visible_when_opening_draft(social):
    dialog, calls = social
    row = {**approved(), "state": "rejected", "error": "Check Instagram media format."}
    dialog.post_list.addItem("Rejected draft", row)
    dialog.post_list.setCurrentIndex(1)
    assert "Not submitted" in dialog.status.text()
    assert "Check Instagram media format" in dialog.status.text()
    assert not calls


def test_current_provider_scheduled_state_is_clear(social):
    dialog, _ = social
    row = {**approved(), "state": "submitted", "provider_status": "scheduled"}
    dialog.checked(row)
    assert "scheduled in Buffer" in dialog.status.text()
    assert "unavailable" not in dialog.status.text()


def test_no_channels_has_actionable_buffer_setup(social):
    dialog, _ = social
    dialog.loaded(({"channels": []}, {"posts": []}, {"available": True}))
    dialog.update_controls()
    assert dialog.channel_setup.isVisible()
    assert not dialog.selection_button.isEnabled()
    assert "refresh here" in dialog.status.text()
