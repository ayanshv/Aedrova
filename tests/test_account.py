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
    assert widget.onboarding_nickname.text() == "Nova"
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
