"""Account UI stays responsive and discards stale sensitive state on failures."""

from threading import Event
from types import SimpleNamespace

from PySide6.QtCore import QSettings

from aedrova.desktop.account import AccountDialog


def dialog(qtbot, tmp_path):
    widget = AccountDialog(
        settings=QSettings(str(tmp_path / "account.ini"), QSettings.Format.IniFormat)
    )
    qtbot.addWidget(widget)
    widget.show()
    return widget


def test_missing_configuration_never_starts_network(qtbot, tmp_path, monkeypatch):
    from aedrova.identity.service import Connection

    monkeypatch.setattr(Connection, "for_application", lambda: None)
    widget = dialog(qtbot, tmp_path)
    widget.start_google()
    assert not widget.busy
    assert "not available" in widget.status.text()


def test_worker_does_not_block_event_loop_or_close_during_request(qtbot, tmp_path):
    widget = dialog(qtbot, tmp_path)
    release = Event()
    results = []
    widget.run(lambda: release.wait(timeout=3), results.append)
    try:
        assert widget.busy and not widget.pages.isEnabled()
        widget.accept()
        assert widget.isVisible()
        widget.status.setText("UI is responsive")
    finally:
        release.set()
    qtbot.waitUntil(lambda: not widget.busy)
    assert results == [True]


def test_errors_clear_cached_roster_and_never_show_provider_details(qtbot, tmp_path):
    widget = dialog(qtbot, tmp_path)
    widget.service = SimpleNamespace(user=SimpleNamespace(id="user"))
    widget.snapshot["members"] = [{"workspace_id": "w", "user_id": "secret-user", "role": "owner"}]
    widget.generated_code.setText("secret-invitation")

    def failing():
        raise RuntimeError("sensitive-token")

    widget.run(failing, lambda _: None)
    qtbot.waitUntil(lambda: not widget.busy)
    assert widget.snapshot["members"] == []
    assert widget.generated_code.text() == ""
    assert "sensitive-token" not in widget.status.text()


def test_customer_login_has_no_password_or_infrastructure_fields(qtbot, tmp_path):
    widget = dialog(qtbot, tmp_path)
    assert widget.google_button.isVisible()
    for attribute in ("url", "key", "email", "password", "code", "connection_dialog"):
        assert not hasattr(widget, attribute)


def test_new_google_user_gets_onboarding(qtbot, tmp_path):
    widget = dialog(qtbot, tmp_path)
    widget.service = SimpleNamespace(user=SimpleNamespace(id="user", email="u@example.com"))
    widget.loaded(
        {
            "workspaces": [],
            "channels": [],
            "members": [],
            "invitations": [],
            "agent_preferences": [],
        }
    )
    assert widget.pages.currentIndex() == 2
    assert widget.onboarding_nickname.text() == "Aedrova"
    assert "Aedrova" in widget.windowTitle()


def test_onboarding_sends_shared_nickname_and_provider(qtbot, tmp_path):
    widget = dialog(qtbot, tmp_path)
    calls = []
    widget.mutate = lambda name, data: calls.append((name, data))
    widget.onboarding_workspace.setText("Our team")
    widget.onboarding_nickname.setText("Sparky")
    widget.onboarding_provider.setCurrentIndex(1)
    widget.complete_onboarding()
    assert calls == [
        (
            "onboard_workspace",
            {"p_name": "Our team", "p_nickname": "Sparky", "p_provider": "claude_code"},
        )
    ]
    widget.onboarding_nickname.setText("<admin>")
    widget.complete_onboarding()
    assert len(calls) == 1


def test_member_cannot_edit_team_agent_preference(qtbot, tmp_path):
    widget = dialog(qtbot, tmp_path)
    widget.service = SimpleNamespace(user=SimpleNamespace(id="user"))
    widget.loaded(
        {
            "workspaces": [{"id": "w", "name": "Team"}],
            "channels": [],
            "members": [{"workspace_id": "w", "user_id": "user", "role": "member"}],
            "invitations": [],
            "agent_preferences": [{"workspace_id": "w", "nickname": "Atlas", "provider": "codex"}],
        }
    )
    assert widget.agent_name.text() == "Atlas"
    assert not widget.save_agent.isEnabled()
    widget.snapshot["members"][0]["role"] = "owner"
    widget.render_workspace()
    assert widget.save_agent.isEnabled()


def test_create_intent_survives_sign_in_and_existing_workspaces(qtbot, tmp_path):
    widget = dialog(qtbot, tmp_path)
    widget.pending_intent = "create"
    widget.service = SimpleNamespace(user=SimpleNamespace(id="user"))
    widget.loaded(
        {
            "workspaces": [{"id": "w", "name": "Existing"}],
            "channels": [],
            "members": [],
            "invitations": [],
            "agent_preferences": [],
        }
    )
    assert widget.pages.currentIndex() == 2
    assert widget.pending_intent is None
    assert widget.onboarding_nickname.text() == "Aedrova"


def test_invitation_copy_and_access(qtbot, tmp_path):
    widget = dialog(qtbot, tmp_path)
    widget.service = SimpleNamespace(user=SimpleNamespace(id="user"))
    widget.pending_intent = "invite"
    widget.loaded(
        {
            "workspaces": [{"id": "w", "name": "Team"}],
            "channels": [],
            "members": [{"workspace_id": "w", "user_id": "user", "role": "owner"}],
            "invitations": [],
            "agent_preferences": [],
        }
    )
    assert widget.pages.currentIndex() == 2
    assert widget.onboarding_steps.currentIndex() == 3
    assert widget.create_invitation_button.isEnabled()
    assert not widget.copy_invitation.isEnabled()
    widget.generated_code.setText("test-invitation")
    widget.copy_invitation.click()
    from PySide6.QtWidgets import QApplication

    assert QApplication.clipboard().text() == "test-invitation"
    widget.snapshot["members"][0]["role"] = "member"
    widget.render_workspace()
    assert not widget.create_invitation_button.isEnabled()
    assert not widget.copy_invitation.isEnabled()


def setup_service(widget, *, fail_refresh=False):
    calls = []
    snapshot = {
        "workspaces": [{"id": "new", "name": "Our team"}],
        "members": [{"workspace_id": "new", "user_id": "user", "role": "owner"}],
        "channels": [],
        "invitations": [],
        "agent_preferences": [],
    }

    def rpc(name, params):
        calls.append((name, params))
        return "invite-token" if name == "create_invitation" else "new"

    def read():
        if fail_refresh:
            raise RuntimeError("private-error")
        return snapshot

    widget.service = SimpleNamespace(user=SimpleNamespace(id="user"), rpc=rpc, snapshot=read)
    return calls


def test_wizard_finishes_once_without_returning_to_create(qtbot, tmp_path):
    widget = dialog(qtbot, tmp_path)
    calls = setup_service(widget)
    widget.begin_onboarding()
    widget.name_continue.click()
    assert widget.onboarding_steps.currentIndex() == 0
    widget.onboarding_workspace.setText("Our team")
    widget.name_continue.click()
    assert widget.onboarding_steps.currentIndex() == 1
    widget.finish_onboarding.click()
    widget.finish_onboarding.click()  # Disabled while request is running.
    qtbot.waitUntil(lambda: not widget.busy)
    assert len(calls) == 1
    assert widget.workspace_id() == "new"
    assert widget.onboarding_steps.currentIndex() == 2
    assert widget.ready_summary.text() == "Our team"
    widget.finish_setup()
    assert widget.pages.currentIndex() == 4
    assert widget.home_workspaces.currentData() == "new"
    assert len(calls) == 1


def test_successful_create_with_failed_refresh_is_not_reported_as_failed(qtbot, tmp_path):
    widget = dialog(qtbot, tmp_path)
    calls = setup_service(widget, fail_refresh=True)
    widget.begin_onboarding()
    widget.onboarding_workspace.setText("Our team")
    widget.advance_onboarding()
    widget.finish_onboarding.click()
    qtbot.waitUntil(lambda: not widget.busy)
    assert len(calls) == 1
    assert widget.onboarding_steps.currentIndex() == 2
    assert "Saved successfully" in widget.status.text()
    assert "private-error" not in widget.status.text()


def test_optional_invite_stays_on_invitation_step(qtbot, tmp_path):
    widget = dialog(qtbot, tmp_path)
    calls = setup_service(widget)
    widget.loaded(widget.service.snapshot())
    widget.show_simple_invite()
    widget.setup_email.setText("friend@example.com")
    widget.setup_invite.click()
    qtbot.waitUntil(lambda: not widget.busy)
    assert widget.pages.currentIndex() == 2
    assert widget.onboarding_steps.currentIndex() == 3
    assert widget.setup_code.text() == "invite-token"
    assert calls[0][1]["p_workspace"] == "new"
    widget.finish_setup()
    assert widget.pages.currentIndex() == 4
    assert widget.setup_code.text() == ""


def test_google_icon_available(qtbot, tmp_path):
    widget = dialog(qtbot, tmp_path)
    assert not widget.google_button.icon().isNull()


def test_failed_creation_preserves_draft_and_step(qtbot, tmp_path):
    widget = dialog(qtbot, tmp_path)
    setup_service(widget)

    def fail(*args):
        raise RuntimeError("private-server-detail")

    widget.service.rpc = fail
    widget.begin_onboarding()
    widget.onboarding_workspace.setText("Keep this name")
    widget.onboarding_nickname.setText("Atlas")
    widget.advance_onboarding()
    widget.finish_onboarding.click()
    qtbot.waitUntil(lambda: not widget.busy)
    assert widget.onboarding_steps.currentIndex() == 1
    assert widget.onboarding_workspace.text() == "Keep this name"
    assert widget.onboarding_nickname.text() == "Atlas"
    assert "private-server-detail" not in widget.status.text()


def test_join_invitation_ends_at_workspace_home(qtbot, tmp_path):
    widget = dialog(qtbot, tmp_path)
    setup_service(widget)
    widget.pages.setCurrentIndex(3)
    widget.mutate("accept_invitation", {"p_token": "test-code"})
    qtbot.waitUntil(lambda: not widget.busy)
    assert widget.pages.currentIndex() == 4
    assert widget.workspace_id() == "new"
