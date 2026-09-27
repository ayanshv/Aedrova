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


def test_invalid_config_never_starts_network(qtbot, tmp_path):
    widget = dialog(qtbot, tmp_path)
    widget.url.setText("https://example.supabase.co")
    widget.key.setText("sb_secret_not_allowed")
    widget.authenticate("signin")
    assert not widget.busy
    assert "forbidden" in widget.status.text()


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


def test_password_removed_before_background_auth_and_not_saved(qtbot, tmp_path):
    widget = dialog(qtbot, tmp_path)
    widget.url.setText("https://example.supabase.co")
    widget.key.setText("sb_publishable_abcdefghijk1234567890")
    widget.email.setText("a@b.test")
    widget.password.setText("secret-password")

    class Service:
        user = None

        def sign_up(self, email, password):
            assert password == "secret-password"
            return None

    widget.factory = lambda config: Service()
    widget.authenticate("signup")
    assert widget.password.text() == ""
    qtbot.waitUntil(lambda: not widget.busy)
    assert "confirm" in widget.status.text()
    assert all("password" not in key.lower() for key in widget.settings.allKeys())
