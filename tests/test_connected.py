"""Shared dashboard journeys with a fake transport; SQL tests cover access boundaries."""

from types import SimpleNamespace

from PySide6.QtCore import QSettings, Qt

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


def test_new_member_can_retry_profile_and_open_chat_without_a_setup_tour(qtbot, tmp_path):
    window = AedrovaWindow(
        settings=QSettings(str(tmp_path / "new.ini"), QSettings.Format.IniFormat)
    )
    qtbot.addWidget(window)
    window.show_account()
    account = window.account_dialog
    state = snapshot()
    state["user_profile"] = {}
    calls = []

    def save_profile(data, avatar):
        calls.append((data, avatar))
        if len(calls) == 1:
            raise ValueError("username is already taken")
        return data

    account.service = SimpleNamespace(
        user=SimpleNamespace(id="new-member"),
        snapshot=lambda: state,
        save_full_profile=save_profile,
        message_page=lambda *_args, **_kwargs: [],
        attachments_for=lambda _: [],
        realtime_credentials=lambda: None,
        rpc=lambda *_args: None,
    )
    account.loaded(state)
    account.open_dashboard()
    profile = window.profile_dialog
    qtbot.addWidget(profile)
    assert profile.isVisible() and window.connected is None
    profile.name.setText("Maya Chen")
    profile.username.setText("maya")
    profile.next.click()
    qtbot.waitUntil(lambda: profile.error.isVisible())
    assert profile.username.text() == "maya"
    profile.username.setText("maya_chen")
    profile.next.click()
    qtbot.waitUntil(lambda: window.connected is not None and window.connected.active)
    assert calls[-1][0]["profile_completed"]
    assert window.channel_id == "c"
    assert not account.isVisible()
    assert window.tour is None and getattr(window, "setup_dialog", None) is None
    qtbot.waitUntil(lambda: window.composer.editor.hasFocus())


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


def test_workspace_usage_ignores_old_space_balance_and_refreshes_after_reply(
    qtbot, tmp_path, monkeypatch
):
    from threading import Event

    from aedrova.desktop.workspace_usage import ManagedClient

    window, service = setup(qtbot, tmp_path)
    window.connected.stop_realtime()
    meter = window.workspace_usage
    started, release = Event(), Event()
    balances = {"w": 20, "other": 60}

    def balance(_client, workspace):
        if workspace == "w":
            started.set()
            if not release.wait(3):
                raise TimeoutError
        return {
            "status": "active",
            "monthly_budget": 100,
            "monthly_settled": balances[workspace],
            "monthly_spent": balances[workspace] + 5,
            "monthly_pending": 5,
        }

    service.realtime_credentials = lambda: ("", "", "fixture-access", "u")
    monkeypatch.setattr(ManagedClient, "balance", balance)
    monkeypatch.setattr(
        "aedrova.desktop.workspace_usage.application_origin", lambda: "https://example.test"
    )
    state = snapshot()
    state["workspaces"].append({"id": "other", "name": "Other team"})
    state["channels"].append(
        {"id": "other-chat", "workspace_id": "other", "name": "general", "private": False}
    )
    state["members"].append({"workspace_id": "other", "user_id": "u", "role": "member"})
    service.snapshot = lambda: state
    try:
        window.connected.apply(state, [], "w", "c")
        qtbot.waitUntil(started.is_set)
        window.switch_workspace("other")
        assert meter.remaining.text() == "Checking…" and meter.bar.isHidden()
    finally:
        release.set()
    qtbot.waitUntil(lambda: meter.remaining.text() == "40% left")
    assert meter.bar.value() == 60
    assert "reserved" in meter.toolTip()
    balances["other"] = 90
    window.connected.complete_agent_reply("other", "other-chat", "Done", "Aedrova")
    qtbot.waitUntil(lambda: meter.remaining.text() == "10% left")
    window.connected.disconnect()
    assert meter.isHidden() and not meter.timer.isActive()


def test_inactive_workspace_ai_turns_on_automatically_once(qtbot, tmp_path, monkeypatch):
    from aedrova.desktop.workspace_usage import ManagedClient

    window, service = setup(qtbot, tmp_path)
    window.connected.stop_realtime()
    meter = window.workspace_usage
    state = {"active": False, "activations": 0}

    def balance(_client, _workspace):
        if not state["active"]:
            return {"status": "inactive"}
        return {"status": "active", "monthly_budget": 100, "monthly_settled": 10}

    def activate(_client, workspace):
        state["activations"] += 1
        state["active"] = True
        return balance(_client, workspace)

    service.realtime_credentials = lambda: ("", "", "fixture-access", "u")
    monkeypatch.setattr(ManagedClient, "balance", balance)
    monkeypatch.setattr(ManagedClient, "activate_free", activate)
    monkeypatch.setattr(
        "aedrova.desktop.workspace_usage.application_origin", lambda: "https://example.test"
    )
    service.snapshot = lambda: snapshot()
    window.connected.apply(snapshot(), [], "w", "c")
    qtbot.waitUntil(lambda: meter.remaining.text() == "90% left")
    assert state["activations"] == 1
    meter.refresh()
    qtbot.wait(100)
    assert state["activations"] == 1
    window.connected.disconnect()


def test_workspace_without_a_plan_activates_instead_of_showing_unavailable(
    qtbot, tmp_path, monkeypatch
):
    from aedrova.desktop.workspace_usage import ManagedClient

    window, service = setup(qtbot, tmp_path)
    window.connected.stop_realtime()
    meter = window.workspace_usage
    state = {"active": False}

    def balance(_client, _workspace):
        if not state["active"]:
            raise RuntimeError(
                "This Space’s included AI is not active yet. Its owner or admin can open "
                "Settings → Your team’s plan & AI access → Activate included AI, then retry."
            )
        return {"status": "active", "monthly_budget": 100, "monthly_settled": 25}

    def activate(client, workspace):
        state["active"] = True
        return balance(client, workspace)

    service.realtime_credentials = lambda: ("", "", "fixture-access", "u")
    monkeypatch.setattr(ManagedClient, "balance", balance)
    monkeypatch.setattr(ManagedClient, "activate_free", activate)
    monkeypatch.setattr(
        "aedrova.desktop.workspace_usage.application_origin", lambda: "https://example.test"
    )
    service.snapshot = lambda: snapshot()
    window.connected.apply(snapshot(), [], "w", "c")
    qtbot.waitUntil(lambda: meter.remaining.text() == "75% left")
    window.connected.disconnect()


def test_failed_automatic_activation_stays_inactive_without_retry_loop(
    qtbot, tmp_path, monkeypatch
):
    from aedrova.desktop.workspace_usage import ManagedClient

    window, service = setup(qtbot, tmp_path)
    window.connected.stop_realtime()
    meter = window.workspace_usage
    attempts = []

    def refuse(_client, workspace):
        attempts.append(workspace)
        raise RuntimeError("Only owners can activate included AI.")

    service.realtime_credentials = lambda: ("", "", "fixture-access", "u")
    monkeypatch.setattr(ManagedClient, "balance", lambda *_: {"status": "inactive"})
    monkeypatch.setattr(ManagedClient, "activate_free", refuse)
    monkeypatch.setattr(
        "aedrova.desktop.workspace_usage.application_origin", lambda: "https://example.test"
    )
    service.snapshot = lambda: snapshot()
    window.connected.apply(snapshot(), [], "w", "c")
    qtbot.waitUntil(lambda: bool(attempts) and meter.remaining.text() == "Inactive")
    meter.refresh()
    qtbot.wait(150)
    assert attempts == ["w"]
    window.connected.disconnect()


def test_failed_send_keeps_draft_and_reuses_message_id(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    calls = []

    def fail(name, params):
        calls.append(params)
        raise PermissionError("denied")

    service.rpc = fail
    window.composer.editor.setPlainText("Keep me")
    window.send_message("Keep me")
    qtbot.waitUntil(lambda: bool(calls) and not window.account_dialog.busy)
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
    qtbot.waitUntil(lambda: bool(calls) and not window.account_dialog.busy)
    assert calls[0][0] == "send_message"
    assert calls[0][1]["p_body"] == "Hello"
    assert window.composer.editor.toPlainText() == ""
    assert window.channel.messages[0].body == "Hello"


def test_signed_in_meetings_opens_device_setup_and_signout_closes_it(qtbot, tmp_path):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QPushButton

    window, _ = setup(qtbot, tmp_path)
    window.select_tab(0)
    window.open_meeting_hub()

    window._render_pages()
    assert window.pages.currentIndex() == 0
    assert window.call_buttons["notes"].accessibleName() == "Take meeting notes"
    page = window.meeting_hub
    actions = [b for b in page.findChildren(QPushButton) if b.text() == "Check meeting devices"]
    assert len(actions) == 1
    qtbot.mouseClick(actions[0], Qt.MouseButton.LeftButton)
    assert window.meeting_setup.isVisible()
    assert not window.meeting_setup.check.handles
    window.account_dialog.session_closed.emit()
    assert not window.meeting_setup.isVisible()
    assert window.meeting_setup.check.closed


def test_server_snapshot_loads_private_attachment_preview(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    service.attachments_for = lambda _: [
        {"id": "attachment", "message_id": "m", "channel_id": "c", "filename": "note.txt"}
    ]
    service.download_attachment = lambda _: b"Private staging preview"
    window.connected.last_view = None
    window.connected.refresh()
    qtbot.waitUntil(
        lambda: window.collaboration.previews.cache.get("attachment") == "Private staging preview",
        timeout=5000,
    )
    assert window.messages.attachment_previews["attachment"] == "Private staging preview"


def test_queued_refresh_after_account_destruction_stops_without_network(qtbot, tmp_path):
    from unittest.mock import Mock

    from PySide6.QtCore import QCoreApplication, QEvent, QTimer

    window, _ = setup(qtbot, tmp_path)
    controller, account = window.connected, window.account_dialog
    account.run = Mock()
    controller.timer.start()
    QTimer.singleShot(0, controller.refresh)
    account.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    qtbot.waitUntil(lambda: not controller.active)
    assert not controller.timer.isActive()
    account.run.assert_not_called()


def test_usage_meter_defaults_to_five_hours_and_opens_both_windows_on_click(qtbot, tmp_path):
    import time

    window, _ = setup(qtbot, tmp_path)
    meter = window.workspace_usage
    now = int(time.time())
    data = {
        "status": "active",
        "weekly_budget": 2_000_000,
        "weekly_spent": 1_000_000,
        "weekly_reset_at": now + 86_400,
        "five_hour_budget": 800_000,
        "five_hour_spent": 200_000,
        "five_hour_reset_at": now + 3_600,
        "available": 100,
    }
    meter.show_balance(data)
    assert meter.caption.text() == "Next 5 hours"
    assert meter.remaining.text() == "75% left"  # the five-hour window, not the week's 50%
    assert meter.bar.value() == 25
    qtbot.mouseClick(meter, Qt.MouseButton.LeftButton)
    popover = meter.popover
    assert popover is not None and popover.isVisible()
    assert [(t, left) for t, left, _ in popover.rows] == [("Next 5 hours", 75), ("This week", 50)]
    assert "resets in" in popover.rows[0][2] and popover.rows[1][2].startswith("resets ")
    popover.close()

    # A full week stops work even though the five-hour window has room.
    meter.show_balance({**data, "weekly_spent": 2_000_000, "available": 0})
    assert meter.remaining.text() == "Limit reached" and meter.caption.text() == "This week"
    assert meter.bar.value() == 100

    # A full five-hour window shows the limit and explains it in the details.
    meter.show_balance({**data, "five_hour_spent": 800_000, "available": 0})
    assert meter.remaining.text() == "Limit reached"
    qtbot.keyClick(meter, Qt.Key.Key_Return)
    assert "5-hour window" in meter.popover.note
    meter.popover.close()


def test_a_free_workspace_is_upgraded_once_when_the_beta_allowance_is_available(
    qtbot, tmp_path, monkeypatch
):
    from aedrova.desktop.workspace_usage import ManagedClient

    window, service = setup(qtbot, tmp_path)
    window.connected.stop_realtime()
    meter = window.workspace_usage
    state = {"upgraded": False, "calls": 0}

    def balance(_client, _workspace):
        if state["upgraded"]:
            return {"status": "active", "monthly_budget": 100, "monthly_settled": 10}
        return {
            "status": "active",
            "monthly_budget": 100,
            "monthly_settled": 90,
            "early_access_available": True,
        }

    def activate(_client, workspace):
        state["calls"] += 1
        state["upgraded"] = True
        return balance(_client, workspace)

    service.realtime_credentials = lambda: ("", "", "fixture-access", "u")
    monkeypatch.setattr(ManagedClient, "balance", balance)
    monkeypatch.setattr(ManagedClient, "activate_free", activate)
    monkeypatch.setattr(
        "aedrova.desktop.workspace_usage.application_origin", lambda: "https://example.test"
    )
    service.snapshot = lambda: snapshot()
    window.connected.apply(snapshot(), [], "w", "c")
    qtbot.waitUntil(lambda: meter.remaining.text() == "90% left")  # after the upgrade
    meter.refresh()
    qtbot.wait(100)
    assert state["calls"] == 1
    window.connected.disconnect()
