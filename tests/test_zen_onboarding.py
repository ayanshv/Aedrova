"""Exercise desktop setup navigation, account boundaries and project permissions."""

from types import SimpleNamespace

import pytest
from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QApplication, QLabel, QPushButton
from test_connected import setup, snapshot

from aedrova.desktop.account import AccountDialog
from aedrova.desktop.onboarding import SetupDialog, account_key
from aedrova.desktop.projects import binding
from aedrova.desktop.window import AedrovaWindow
from aedrova.desktop.zen_setup import ACCOUNT, GOAL, PRIVACY, PROJECT, WELCOME


@pytest.fixture
def fresh_window(qtbot, tmp_path):
    window = AedrovaWindow(
        settings=QSettings(str(tmp_path / "onboarding.ini"), QSettings.IniFormat)
    )
    qtbot.addWidget(window)
    window.show()
    return window


def show_setup(window, qtbot):
    flow = SetupDialog(window)
    qtbot.addWidget(flow)
    flow.show()
    return flow


def test_welcome_goes_directly_to_account_and_apple_returns_to_profile(
    fresh_window, qtbot, monkeypatch
):
    window = fresh_window
    monkeypatch.setenv("AEDROVA_APPLE_LOGIN_ENABLED", "true")
    providers = []
    monkeypatch.setattr(
        AccountDialog, "start_provider", lambda _, provider: providers.append(provider)
    )
    flow = show_setup(window, qtbot)
    assert flow.stage == WELCOME
    flow.primary.click()
    assert flow.stage == ACCOUNT and flow.primary.isHidden()
    apple = next(
        b for b in flow.setup.findChildren(QPushButton) if b.text() == "Sign in with Apple"
    )
    assert not apple.icon().isNull()
    apple.click()
    assert providers == ["apple"] and not flow.isVisible()

    account = window.account_dialog
    user = SimpleNamespace(
        id="u", email="maya@example.com", user_metadata={"full_name": "Maya Chen"}
    )
    stored = {}

    def save(values, photo):
        stored.update(values)
        return values

    account.service = SimpleNamespace(user=user, snapshot=snapshot, save_full_profile=save)
    account.authenticated(user)
    qtbot.waitUntil(lambda: flow.isVisible() and flow.setup.profile_form is not None)
    assert flow.stage == ACCOUNT and flow.setup.workspace == "w"
    form = flow.setup.profile_form
    assert form.name.text() == "Maya Chen"
    flow.primary.click()
    qtbot.waitUntil(lambda: flow.stage == PRIVACY)
    assert any(
        item.text() == "Signed in as maya@example.com" for item in flow.setup.findChildren(QLabel)
    )
    flow.primary.click()
    assert flow.stage == GOAL
    flow.skip.click()
    assert flow.closed and window.getting_started.isVisible()
    assert stored["profile_completed"]
    window.connected.timer.stop()


def test_google_still_works_when_apple_is_disabled(fresh_window, qtbot, monkeypatch):
    monkeypatch.setenv("AEDROVA_APPLE_LOGIN_ENABLED", "false")
    providers = []
    monkeypatch.setattr(
        AccountDialog, "start_provider", lambda _, provider: providers.append(provider)
    )
    flow = show_setup(fresh_window, qtbot)
    flow.primary.click()
    buttons = flow.setup.findChildren(QPushButton)
    assert not any(b.text() == "Sign in with Apple" for b in buttons)
    next(b for b in buttons if b.text() == "Continue with Google").click()
    assert providers == ["google"]
    fresh_window.account_dialog.reject()
    assert flow.isVisible() and flow.stage == ACCOUNT


def test_signed_in_profile_completion_opens_workspace_with_no_tour(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    sample_code = "A2-0123-4567-89AB-CDEF"
    service.rpc = lambda name, _: sample_code if name == "create_workspace_join_code" else None
    window.account_dialog.snapshot["user_profile"] = {"profile_completed": True}
    flow = show_setup(window, qtbot)
    flow.primary.click()
    assert flow.stage == PRIVACY
    flow.primary.click()
    assert flow.stage == GOAL
    next(b for b in flow.setup.findChildren(QPushButton) if b.text() == "Build something").click()
    assert flow.closed and window.tour is None
    assert window.getting_started.examples.currentIndex() == 1
    assert window.getting_started.isVisible()
    assert window.settings.value(account_key(window) + "/setup", False, type=bool)
    assert not binding(window)
    invite = window.onboarding_team_invite
    qtbot.waitUntil(invite.copy.isEnabled)
    assert invite.isVisible() and invite.code.text() == sample_code
    invite.copy.click()
    assert QApplication.clipboard().text() == sample_code
    invite.accept()
    window.getting_started.dismiss()
    window.getting_started.refresh()
    assert not window.getting_started.isVisible()


def test_project_starts_with_review_and_saves_only_after_confirmation(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    flow = show_setup(window, qtbot)
    flow.show_stage(PROJECT)
    assert flow.setup.automatic.isChecked()
    warning = next(
        item
        for item in flow.setup.findChildren(QLabel)
        if item.text().startswith("Automatic execution is off.")
    )
    assert warning.isHidden()
    flow.setup.automatic.setChecked(False)
    assert warning.isVisible()
    flow.setup.automatic.setChecked(True)
    assert warning.isHidden()
    flow.primary.click()
    assert "Choose a project folder" in flow.setup.status.text()
    assert flow.isVisible() and not binding(window)
    folder = tmp_path / "project"
    folder.mkdir()
    flow.setup.folder.setText(str(folder))
    flow.primary.click()
    assert flow.closed
    saved = binding(window)
    assert saved["folder"] == str(folder) and saved["background_build"]


def test_workspace_change_blocks_project_save(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    flow = show_setup(window, qtbot)
    flow.show_stage(PROJECT)
    flow.setup.folder.setText(str(tmp_path))
    window.workspace_id = "different"
    flow.primary.click()
    assert flow.isVisible() and not binding(window, "w")


def test_profile_errors_stay_inline(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    service.save_full_profile = lambda *_: (_ for _ in ()).throw(
        ValueError("username is already taken")
    )
    flow = show_setup(window, qtbot)
    flow.show_stage(ACCOUNT)
    form = flow.setup.profile_form
    form.name.setText("Maya")
    form.username.setText("maya_chen")
    flow.primary.click()
    qtbot.waitUntil(lambda: not form.saving)
    assert "taken" in form.error.text()
    assert flow.primary.isEnabled() and form.username.text() == "maya_chen"


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_compact_layout_fits_supported_minimum(fresh_window, qtbot, theme):
    flow = show_setup(fresh_window, qtbot)
    flow.apply_appearance(theme)
    flow.resize(560, 580)
    qtbot.keyClick(flow.primary, Qt.Key.Key_Return)
    assert flow.stage == ACCOUNT
    qtbot.waitUntil(lambda: flow.content.height() > 100)
    assert flow.content.width() >= 400
    center = flow.content.mapTo(flow, flow.content.rect().center())
    assert abs(center.x() - flow.rect().center().x()) <= 2
    assert abs(center.y() - flow.rect().center().y()) <= 2
    assert not flow.grab().isNull()


def test_dashboard_first_run_keeps_profile_before_workspace(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    window.enable_guided_onboarding = True
    window.account_dialog.snapshot["user_profile"] = {}
    window.account_dialog.open_dashboard()
    flow = window.setup_dialog
    assert flow.isVisible() and flow.stage == ACCOUNT
    assert flow.setup.profile_form is not None


def test_profile_then_join_requires_a_real_workspace(fresh_window, qtbot, monkeypatch):
    window = fresh_window
    monkeypatch.setattr(AccountDialog, "start_provider", lambda *_: None)
    flow = show_setup(window, qtbot)
    flow.primary.click()
    flow.setup.signin("google")
    account = window.account_dialog
    user = SimpleNamespace(
        id="u", email="maya@example.com", user_metadata={"full_name": "Maya Chen"}
    )
    empty = {**snapshot(), "workspaces": [], "channels": [], "members": []}
    account.service = SimpleNamespace(
        user=user, snapshot=lambda: empty, save_full_profile=lambda values, _: values
    )
    account.authenticated(user)
    qtbot.waitUntil(lambda: flow.isVisible() and flow.setup.profile_form is not None)
    flow.primary.click()
    qtbot.waitUntil(lambda: flow.stage == PRIVACY)
    flow.primary.click()
    assert flow.stage == PROJECT
    assert flow.primary.isHidden() and flow.skip.isHidden()
    assert flow.setup.first_action.text() == "Create or join a workspace"
    assert not window.settings.value(flow.prefix + "/setup", False, type=bool)


def test_starter_drafts_are_local_and_do_not_overwrite_or_send(qtbot, tmp_path, monkeypatch):
    window, service = setup(qtbot, tmp_path)
    guide = window.getting_started
    monkeypatch.setattr(service, "rpc", lambda *_: pytest.fail("The guide must never send"))
    guide.open()
    editor = window.composer.editor
    editor.setPlainText("Existing draft")
    guide.draft.click()
    assert editor.toPlainText() == "Existing draft"
    assert guide.progress.text() == "0 of 3 tried"

    editor.clear()
    guide.examples.setCurrentIndex(1)
    guide.draft.click()
    assert editor.toPlainText().startswith(f"@{window.composer.agent_name} Turn the latest")
    assert guide.progress.text() == "1 of 3 tried"
    guide.searched("onboarding")
    assert guide.progress.text() == "2 of 3 tried"
    guide.dismiss()
    guide.refresh()
    assert guide.isHidden()
    guide.open()
    assert guide.progress.text() == "2 of 3 tried"
    window.connected.disconnect()
    assert guide.isHidden()


def test_first_reply_guide_follows_only_the_selected_starter(qtbot, tmp_path, monkeypatch):
    window, _ = setup(qtbot, tmp_path)
    guide = window.getting_started
    guide.open(goal="catch-up")
    guide.draft.click()
    guide.prompt_sent(window.composer.editor.toPlainText(), "starter")
    guide.reply_received("w", "c", "unrelated", "Other reply")
    assert guide.sample.isHidden()
    source = "message:11111111-1111-4111-8111-111111111111"
    guide.reply_received("w", "c", "starter", "See " + source)
    assert guide.next_step.text() == "Open a cited source"
    opened = []
    monkeypatch.setattr(window.messages, "open_reply_source", opened.append)
    guide.next_step.click()
    assert opened == [source]
