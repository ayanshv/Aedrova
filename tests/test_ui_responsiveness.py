"""Cached navigation must not wait for networking or bypass mutation authority."""

from threading import Event

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from test_connected import row, snapshot
from test_connected import setup as connected_setup

from aedrova.desktop.collaboration import ChatPanel
from aedrova.desktop.profile import rounded_profile_photo


def setup(qtbot, tmp_path):
    window, service = connected_setup(qtbot, tmp_path)
    # Finish the activation poll before measuring the user action itself.
    qtbot.wait(50)
    qtbot.waitUntil(lambda: not window.account_dialog.busy)
    return window, service


def test_dm_picker_opens_from_session_cache_even_while_transport_busy(qtbot, tmp_path, monkeypatch):
    window, service = setup(qtbot, tmp_path)
    window.account_dialog.snapshot["directory"] = [
        {"workspace_id": "w", "user_id": "peer", "display_name": "Morgan"},
        {"workspace_id": "foreign", "user_id": "stranger", "display_name": "Hidden"},
    ]
    service.snapshot = lambda: pytest.fail("Opening a picker must not fetch a snapshot")
    chosen = []
    monkeypatch.setattr(
        "aedrova.desktop.connected.choose_conversation",
        lambda _, people, buds: chosen.append(people) or None,
    )
    monkeypatch.setattr(window.connected, "enqueue", lambda *a, **k: pytest.fail("No queue wait"))
    window.account_dialog.busy = True
    try:
        window.start_dm_button.click()
        assert [p["user_id"] for p in chosen[0]] == ["peer"]
    finally:
        window.account_dialog.busy = False


def test_settings_open_from_cache_during_background_sync(qtbot, tmp_path, monkeypatch):
    window, _ = setup(qtbot, tmp_path)
    account = window.account_dialog
    monkeypatch.setattr(account, "refresh", lambda: pytest.fail("No blocking refresh on open"))
    account.busy, account.background_job = True, True
    try:
        window.show_account("manage")
        assert account.isVisible() and account.pages.currentIndex() == 1
        assert account.pages.isEnabled()
        view = account.workspace_settings
        assert view.sections.count() == 5
        assert view.sections.currentIndex() == view.pages["agent"]
        assert not account.invite_email.isVisible()
        view.buttons["invitations"].click()
        assert account.invite_email.isVisible()
        assert not account.agent_name.isVisible()
    finally:
        account.busy = False


def test_channel_plus_opens_focused_form_without_backend_work(qtbot, tmp_path, monkeypatch):
    window, service = setup(qtbot, tmp_path)
    service.snapshot = lambda: pytest.fail("No network required to open form")
    window.create_channel_button.click()
    dialog = window.channel_create_dialog
    qtbot.addWidget(dialog)
    assert dialog.isVisible() and not dialog.create.isEnabled()
    assert not window.account_dialog.isVisible()
    dialog.name.setText("design")
    assert dialog.create.isEnabled()
    window.create_channel_button.click()
    assert window.channel_create_dialog is dialog


def test_channel_creation_queues_once_and_waits_for_server(qtbot, tmp_path, monkeypatch):
    window, service = setup(qtbot, tmp_path)
    callbacks = []
    monkeypatch.setattr(
        window.connected,
        "enqueue",
        lambda key, work, done, **kw: callbacks.append((work, done)) or True,
    )
    window.create_channel()
    dialog = window.channel_create_dialog
    qtbot.addWidget(dialog)
    dialog.name.setText("design")
    dialog.create.click()
    dialog.create.click()
    assert len(callbacks) == 1 and dialog.pending
    assert window.channel_id == "c"  # No invented channel ID or permission.
    data = snapshot()
    data["channels"].append(
        {"id": "new-channel", "workspace_id": "w", "name": "design", "private": False}
    )
    service.rpc = lambda name, params: "new-channel"
    service.snapshot = lambda: data
    work, done = callbacks[0]
    done(work())
    assert not dialog.isVisible() and window.channel_id == "new-channel"


def test_ambiguous_channel_failure_does_not_offer_duplicate_create(qtbot, tmp_path, monkeypatch):
    window, service = setup(qtbot, tmp_path)
    callbacks = []
    monkeypatch.setattr(
        window.connected,
        "enqueue",
        lambda key, work, done, **kw: callbacks.append((work, done)) or True,
    )
    service.rpc = lambda *a: (_ for _ in ()).throw(TimeoutError())
    window.create_channel()
    dialog = window.channel_create_dialog
    qtbot.addWidget(dialog)
    dialog.name.setText("design")
    dialog.create.click()
    work, done = callbacks[0]
    done(work())
    assert dialog.name.text() == "design"
    assert dialog.create.text() == "Close and refresh"
    dialog.submit()
    assert len(callbacks) == 1


def test_profile_photo_has_transparent_rounded_corners(qapp):
    photo = QPixmap(100, 60)
    photo.fill(Qt.GlobalColor.red)
    image = rounded_profile_photo(photo).toImage()
    assert image.pixelColor(0, 0).alpha() == 0
    assert image.pixelColor(image.width() // 2, image.height() // 2).alpha() == 255


def test_cached_search_results_render_before_network_and_clear_on_failure(
    qtbot, tmp_path, monkeypatch
):
    window, _ = setup(qtbot, tmp_path)
    window.connected.apply(snapshot(), [row()], "w", "c")
    pending = []
    monkeypatch.setattr(
        window.collaboration, "inventory", lambda q, s, c, done: pending.append(done)
    )
    panel = ChatPanel(window.collaboration, "search")
    qtbot.addWidget(panel)
    panel.show()
    panel.load()
    assert panel.results.count() > 0 and pending
    panel.load_failed()
    assert panel.results.count() == 0
    assert "Check your access" in panel.notice.text()


def test_settings_save_during_background_sync_is_not_silently_dropped(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    account = window.account_dialog
    release = Event()
    calls = []
    service.rpc = lambda name, params: calls.append((name, params))
    account.run(lambda: release.wait(3), lambda _: None, background=True)
    try:
        assert account.busy and account.pages.isEnabled()
        account.mutate(
            "set_agent_preferences",
            {"p_workspace": "w", "p_nickname": "Orbit", "p_provider": "auto"},
        )
        assert not calls
    finally:
        release.set()
    qtbot.waitUntil(lambda: bool(calls) and not account.busy)
    assert len(calls) == 1 and calls[0][1]["p_provider"] == "auto"


def test_pending_channel_form_is_cleared_on_signout(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    window.create_channel()
    dialog = window.channel_create_dialog
    qtbot.addWidget(dialog)
    dialog.name.setText("private draft")
    window.account_dialog.session_closed.emit()
    assert not dialog.isVisible() and dialog.name.text() == ""


def test_queued_settings_save_is_cancelled_when_signout_requested(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    account = window.account_dialog
    release = Event()
    calls = []
    service.rpc = lambda name, params: calls.append(name)
    service.sign_out = lambda: None
    account.run(lambda: release.wait(3), lambda _: None, background=True)
    try:
        account.mutate(
            "set_agent_preferences",
            {"p_workspace": "w", "p_nickname": "Orbit", "p_provider": "auto"},
        )
        account.sign_out()
        assert account.logout_pending
    finally:
        release.set()
    qtbot.waitUntil(lambda: account.service is None and not account.busy)
    assert calls == []


def test_workspace_settings_accessibility_selection_changes_visible_page(qtbot):
    from aedrova.desktop.workspace_settings import WorkspaceSettingsView

    view = WorkspaceSettingsView()
    qtbot.addWidget(view)
    view.add_section("agent", "Your agent", "Agent settings", "sparkle")
    view.add_section("account", "Account", "Account settings", "spaces")
    view.buttons["account"].setChecked(True)
    assert view.sections.currentIndex() == view.pages["account"]
    view.buttons["agent"].setChecked(True)
    assert view.sections.currentIndex() == view.pages["agent"]
