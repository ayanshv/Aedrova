"""Personal archiving preserves shared state and remains recoverable with no active spaces."""

from types import SimpleNamespace

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QPushButton

from aedrova.desktop.account import AccountDialog


def account(qtbot, tmp_path, *, archived=False):
    widget = AccountDialog(
        settings=QSettings(str(tmp_path / "archive.ini"), QSettings.Format.IniFormat)
    )
    qtbot.addWidget(widget)
    data = {
        "workspaces": [] if archived else [{"id": "w", "name": "Test workspace"}],
        "archived_workspaces": [{"id": "w", "name": "Test workspace"}] if archived else [],
        "members": [{"workspace_id": "w", "user_id": "user", "role": "member"}],
        "channels": [],
        "invitations": [],
        "agent_preferences": [],
    }
    widget.service = SimpleNamespace(user=SimpleNamespace(id="user"))
    widget.loaded(data)
    widget.show()
    return widget, data


def test_archived_only_account_can_restore_without_onboarding(qtbot, tmp_path):
    widget, _ = account(qtbot, tmp_path, archived=True)
    assert widget.pages.currentIndex() == 4
    assert widget.archived_section.isVisible()
    assert widget.restore_workspace.isEnabled()
    assert not widget.home_dashboard.isEnabled()
    assert not widget.archive_workspace.isEnabled()
    calls = []
    widget.mutate = lambda *args: calls.append(args)
    widget.restore_workspace.click()
    assert calls == [("set_workspace_archived", {"p_workspace": "w", "p_archived": False})]


def test_archive_requires_explicit_confirmation_and_cancel_has_no_effect(qtbot, tmp_path):
    widget, _ = account(qtbot, tmp_path)
    calls = []
    widget.mutate = lambda *args: calls.append(args)
    widget.archive_workspace.click()
    assert widget.archive_confirmation.isVisible()
    assert not calls
    controls = {b.text(): b for b in widget.archive_confirmation.findChildren(QPushButton)}
    controls["Cancel"].click()
    assert not calls
    widget.archive_workspace.click()
    controls = {b.text(): b for b in widget.archive_confirmation.findChildren(QPushButton)}
    controls["Archive for me"].click()
    assert calls == [("set_workspace_archived", {"p_workspace": "w", "p_archived": True})]


def test_archiving_last_space_keeps_restore_screen(qtbot, tmp_path):
    widget, data = account(qtbot, tmp_path)

    def rpc(name, params):
        assert name == "set_workspace_archived"
        data["archived_workspaces"] = data["workspaces"]
        data["workspaces"] = []
        return params["p_workspace"]

    widget.service.rpc = rpc
    widget.service.snapshot = lambda: data
    widget.mutate("set_workspace_archived", {"p_workspace": "w", "p_archived": True})
    qtbot.waitUntil(lambda: not widget.busy)
    assert widget.pages.currentIndex() == 4
    assert widget.archived_workspaces.currentData() == "w"
    assert "Archived for you" in widget.status.text()


def test_restore_selects_restored_space(qtbot, tmp_path):
    widget, data = account(qtbot, tmp_path, archived=True)

    def rpc(name, params):
        data["workspaces"] = [{"id": "other", "name": "Other"}, *data["archived_workspaces"]]
        data["archived_workspaces"] = []
        return params["p_workspace"]

    widget.service.rpc = rpc
    widget.service.snapshot = lambda: data
    widget.restore_workspace.click()
    qtbot.waitUntil(lambda: not widget.busy)
    assert widget.workspace_id() == "w"
    assert widget.home_workspaces.currentData() == "w"
    assert not widget.archived_section.isVisible()
    assert widget.home_dashboard.isEnabled()


def test_failed_archive_refresh_does_not_repeat_write(qtbot, tmp_path):
    widget, _ = account(qtbot, tmp_path)
    calls = []
    widget.service.rpc = lambda *args: calls.append(args) or "w"

    def unavailable():
        raise OSError("private connection error")

    widget.service.snapshot = unavailable
    widget.mutate("set_workspace_archived", {"p_workspace": "w", "p_archived": True})
    qtbot.waitUntil(lambda: not widget.busy)
    assert len(calls) == 1
    assert "Saved successfully" in widget.status.text()
    assert not widget.archive_workspace.isEnabled()
    assert "private" not in widget.status.text()


def test_signout_clears_archived_workspace_names(qtbot, tmp_path):
    widget, _ = account(qtbot, tmp_path, archived=True)
    widget.clear_connected()
    assert widget.archived_workspaces.count() == 0
    assert not widget.archived_section.isVisible()


def test_archive_is_blocked_while_build_or_call_is_active(qtbot, tmp_path, monkeypatch):
    widget, _ = account(qtbot, tmp_path)
    window = SimpleNamespace(build_dialog=SimpleNamespace(pending=True))
    monkeypatch.setattr(widget, "parent", lambda: window)
    widget.confirm_archive()
    assert not hasattr(widget, "archive_confirmation")
    assert "Finish active builds" in widget.status.text()
    window.build_dialog.pending = False
    window.meeting_call = SimpleNamespace(closed=False)
    widget.confirm_archive()
    assert not hasattr(widget, "archive_confirmation")
    window.meeting_call.closed = True
    widget.confirm_archive()
    assert widget.archive_confirmation.isVisible()


def test_build_starting_during_confirmation_prevents_archive(qtbot, tmp_path, monkeypatch):
    widget, _ = account(qtbot, tmp_path)
    window = SimpleNamespace(build_dialog=SimpleNamespace(pending=False))
    monkeypatch.setattr(widget, "parent", lambda: window)
    calls = []
    widget.mutate = lambda *args: calls.append(args)
    widget.confirm_archive()
    window.build_dialog.pending = True
    control = next(
        b
        for b in widget.archive_confirmation.findChildren(QPushButton)
        if b.text() == "Archive for me"
    )
    control.click()
    assert not calls
