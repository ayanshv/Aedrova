"""Shared dashboard journeys with a fake transport; SQL tests cover access boundaries."""

from types import SimpleNamespace

from PySide6.QtCore import QSettings

from aedrova.desktop.connected import message_tree, workspaces_from_snapshot
from aedrova.desktop.window import AedrovaWindow


def snapshot():
    return {
        "workspaces": [{"id": "w", "name": "Real team"}],
        "channels": [{"id": "c", "workspace_id": "w", "name": "general", "private": False}],
        "members": [{"workspace_id": "w", "user_id": "u", "role": "owner"}],
        "invitations": [],
        "agent_preferences": [],
    }


def row(identifier="m", parent=None):
    return {
        "id": identifier,
        "sender_id": "u",
        "body": "Hello",
        "channel_id": "c",
        "parent_id": parent,
        "created_at": "2026-09-27T12:00:00+00:00",
        "sequence": 1,
    }


def setup(qtbot, tmp_path):
    window = AedrovaWindow(settings=QSettings(str(tmp_path / "ui.ini"), QSettings.Format.IniFormat))
    qtbot.addWidget(window)
    window.settings.setValue("githubHelperOnboarded", True)
    window.show_account()
    service = SimpleNamespace(
        user=SimpleNamespace(id="u"),
        snapshot=snapshot,
        message_page=lambda _, **kw: [] if kw.get("after") else [row()],
        attachments_for=lambda _: [],
        realtime_credentials=lambda: None,
        rpc=lambda *args: None,
    )
    window.account_dialog.service = service
    window.account_dialog.loaded(snapshot())
    window.account_dialog.open_dashboard()
    window.connected.timer.stop()
    return window, service


def test_dashboard_uses_real_workspaces_and_messages(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    assert window.workspace_id == "w"
    assert window.channel_id == "c"
    assert [w.name for w in window.store.workspaces] == ["Real team"]
    window.connected.refresh()
    qtbot.waitUntil(lambda: not window.account_dialog.busy)
    assert window.channel.messages[0].body == "Hello"
    assert "Local preview" not in window.windowTitle()
    assert window.isVisible()


def test_archived_last_workspace_leaves_dashboard_and_can_restore(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    archived = snapshot()
    archived["archived_workspaces"] = archived["workspaces"]
    archived["workspaces"] = []
    service.snapshot = lambda: archived
    window.account_dialog.loaded(archived)
    assert not window.connected.active
    assert window.store.workspaces == []
    assert window.account_dialog.pages.currentIndex() == 4
    assert window.account_dialog.archived_workspaces.currentData() == "w"
    restored = snapshot()
    restored["archived_workspaces"] = []
    service.snapshot = lambda: restored
    window.account_dialog.loaded(restored)
    window.account_dialog.open_dashboard()
    window.connected.timer.stop()
    assert window.connected.active
    assert window.workspace_id == "w"
    assert window.channel_id == "c"


def test_failed_send_keeps_draft_and_reuses_message_id(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    calls = []

    def fail(name, params):
        calls.append(params)
        raise PermissionError("denied")

    service.rpc = fail
    window.composer.editor.setPlainText("Keep me")
    window.send_message("Keep me")
    qtbot.waitUntil(lambda: not window.account_dialog.busy)
    assert window.composer.editor.toPlainText() == "Keep me"
    window.connected.retry_at = 0
    window.send_message("Keep me")
    qtbot.waitUntil(lambda: len(calls) >= 2 and not window.account_dialog.busy)
    assert calls[0]["p_id"] == calls[1]["p_id"]
    assert calls[0]["p_channel"] == "c"


def test_sync_preserves_draft_and_signout_clears_private_state(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    window.composer.editor.setPlainText("Draft 🙂")
    window.connected.refresh()
    qtbot.waitUntil(lambda: not window.account_dialog.busy)
    assert window.composer.editor.toPlainText() == "Draft 🙂"
    window.account_dialog.session_closed.emit()
    assert not window.isVisible()
    assert not window.connected.active
    assert window.store.workspaces == []
    assert window.store.drafts == {}


def test_thread_tree_and_empty_guest_channel():
    tree = message_tree([row(), row("reply", "m")], "u")
    assert len(tree) == 1
    assert tree[0].replies[0].id == "reply"
    data = snapshot()
    data["channels"] = []
    assert workspaces_from_snapshot(data)[0].channels[0].id == ""


def test_successful_send_persists_and_clears_only_sent_draft(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    calls = []

    def save(name, params):
        calls.append((name, params))
        return params.get("p_id")

    service.rpc = save
    window.composer.editor.setPlainText("Hello")
    window.send_message("Hello")
    qtbot.waitUntil(lambda: not window.account_dialog.busy)
    assert calls[0][0] == "send_message"
    assert calls[0][1]["p_body"] == "Hello"
    assert window.composer.editor.toPlainText() == ""
    assert window.channel.messages[0].body == "Hello"


def test_signed_in_meetings_opens_device_setup_and_signout_closes_it(qtbot, tmp_path):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QPushButton

    window, _ = setup(qtbot, tmp_path)
    window.pages.setCurrentIndex(4)
    # Rebuilding the connected dashboard must preserve both tab and device action.
    window._render_pages()
    assert window.pages.currentIndex() == 4
    page = window.pages.widget(4)
    actions = [b for b in page.findChildren(QPushButton)
               if b.text() == "Check meeting devices"]
    assert len(actions) == 1
    qtbot.mouseClick(actions[0], Qt.MouseButton.LeftButton)
    assert window.meeting_setup.isVisible()
    assert not window.meeting_setup.check.handles
    window.account_dialog.session_closed.emit()
    assert not window.meeting_setup.isVisible()
    assert window.meeting_setup.check.closed
