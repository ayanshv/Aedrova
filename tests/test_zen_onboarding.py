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
from aedrova.desktop.zen_setup import (
    ACCOUNT,
    GOAL,
    IMPORT,
    OPENING,
    PRIVACY,
    PROJECT,
    THEME,
    WELCOME,
)


@pytest.fixture(autouse=True)
def nothing_to_allow(monkeypatch):
    """Existing flows assume the devices are already allowed; permissions have their own tests."""
    monkeypatch.setattr("aedrova.desktop.zen_onboarding.pending_kinds", lambda: [])


def past_privacy(flow):
    """Privacy, then the appearance choice, which a first run always shows."""
    flow.primary.click()
    assert flow.stage == THEME
    flow.primary.click()


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
    if flow.stage == OPENING:
        flow.activate()  # most flows start after the opening screen
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
    assert providers == ["apple"] and flow.isVisible()  # setup waits in place for the browser
    assert not flow.setup.wait_note.isHidden() and not window.account_dialog.isVisible()

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
    past_privacy(flow)
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
    past_privacy(flow)
    assert flow.stage == GOAL
    next(b for b in flow.setup.findChildren(QPushButton) if b.text() == "Build something").click()
    assert flow.closed and window.tour is None
    assert window.isFullScreen()  # the workspace fills the screen when setup ends
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
        if item.text().startswith("Automatic builds are off.")
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
    assert flow.content.width() >= 300
    left = flow.content.mapTo(flow, flow.content.rect().topLeft()).x()
    right = flow.content.mapTo(flow, flow.content.rect().topRight()).x()
    assert left >= 0 and right <= flow.surface.width()  # the form stays inside the left half
    assert flow.art.width() > 200 and not flow.grab().isNull()


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
    past_privacy(flow)
    assert flow.stage == PROJECT
    assert flow.primary.isHidden() and flow.skip.isHidden()
    assert flow.setup.first_action is flow.setup.workspace_name
    assert not window.settings.value(flow.prefix + "/setup", False, type=bool)


def test_fresh_walkthrough_reviews_existing_profile_then_creates_and_invites(
    fresh_window, qtbot, monkeypatch
):
    window = fresh_window
    window.review_onboarding_profile = True
    monkeypatch.setattr(AccountDialog, "start_provider", lambda *_: None)
    flow = show_setup(window, qtbot)
    window.setup_dialog = flow
    flow.primary.click()
    flow.setup.signin("google")
    account = window.account_dialog
    state = snapshot()
    state["user_profile"] = {
        "profile_completed": True,
        "display_name": "Maya Chen",
        "username": "maya_chen",
    }
    created = "buyer-workspace"
    invites = []

    def save_profile(data, _photo):
        state["user_profile"] = data
        return data

    def rpc(name, params):
        if name == "onboard_workspace":
            state["workspaces"].append({"id": created, "name": params["p_name"]})
            state["channels"].append(
                {
                    "id": "buyers-general",
                    "workspace_id": created,
                    "name": "general",
                    "private": False,
                }
            )
            state["members"].append({"workspace_id": created, "user_id": "u", "role": "owner"})
            return created
        if name == "create_workspace_join_code":
            invites.append(params["p_workspace"])
            return "A2-0123-4567-89AB-CDEF"

    user = SimpleNamespace(id="u", email="maya@example.com")
    account.service = SimpleNamespace(
        user=user,
        snapshot=lambda: state,
        save_full_profile=save_profile,
        rpc=rpc,
        message_page=lambda *args, **kwargs: [],
        attachments_for=lambda _: [],
        realtime_credentials=lambda: None,
    )
    account.authenticated(user)
    qtbot.waitUntil(lambda: flow.isVisible() and flow.setup.profile_form is not None)
    assert flow.setup.profile_form.name.text() == "Maya Chen"
    flow.primary.click()
    qtbot.waitUntil(lambda: flow.stage == PRIVACY)
    past_privacy(flow)
    assert flow.setup.create_button.isEnabled() is False
    flow.setup.workspace_name.setText("Buyer workspace")
    flow.setup.workspace_ack.setChecked(True)
    assert flow.setup.create_button.isEnabled() and not account.isVisible()
    flow.setup.create_button.click()  # created inside setup; the account window stays hidden
    qtbot.waitUntil(lambda: flow.isVisible() and hasattr(flow.setup, "folder"), timeout=8000)
    assert not account.isVisible()
    assert flow.stage == PROJECT and flow.created_workspace == created
    assert not invites
    flow.skip.click()
    assert flow.stage == IMPORT  # a just-made workspace offers the optional Slack import
    flow.skip.click()
    assert flow.stage == GOAL
    flow.skip.click()
    qtbot.waitUntil(lambda: invites == [created])
    assert flow.closed and window.workspace_id == created
    window.connected.timer.stop()


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


def test_theme_step_applies_the_choice_and_the_scene_follows(fresh_window, qtbot):
    window = fresh_window
    window.set_reduced_motion(True)
    flow = show_setup(window, qtbot)
    flow.show_stage(THEME)
    assert flow.art.scene == "theme"
    from aedrova.desktop.zen_visuals import ThemePhoto

    photos = {p.mode: p for p in flow.setup.findChildren(ThemePhoto)}
    assert set(photos) == {"system", "light", "dark"}
    photos["dark"].click()
    assert window.theme_mode == "dark" and flow.theme.name == "dark"
    assert flow.art.preview == "dark"
    assert flow.art.grab().toImage().pixelColor(5, 5).lightness() < 128
    photos["light"].click()
    assert window.theme_mode == "light" and flow.theme.name == "light"


def test_review_after_first_run_skips_the_theme_choice(fresh_window, qtbot):
    window = fresh_window
    flow = show_setup(window, qtbot)
    assert flow.shows_theme()
    window.settings.setValue(flow.prefix + "/setup", True)
    assert not flow.shows_theme()
    assert flow.next_after_privacy() != THEME


def test_every_step_has_a_scene_and_reduced_motion_holds_it_still(fresh_window, qtbot):
    from aedrova.desktop.onboarding_art import StageArt
    from aedrova.desktop.zen_setup import PERMISSIONS

    fresh_window.set_reduced_motion(True)
    flow = show_setup(fresh_window, qtbot)
    assert set(flow.SCENES.values()) == set(StageArt.SCENES)
    for scene in StageArt.SCENES:
        flow.art.show_scene(scene)
        assert flow.art.enter == 1.0 and not flow.art.timer.isActive()
        assert not flow.art.grab().isNull()
    flow.art.set_granted(["camera"])
    assert flow.art.levels["camera"] == 1.0 and flow.art.levels["screen"] == 0.0
    assert PERMISSIONS in flow.SCENES


def test_the_colour_wash_leans_a_new_way_on_each_step(fresh_window, qtbot):
    fresh_window.set_reduced_motion(True)
    flow = show_setup(fresh_window, qtbot)
    flow.show_stage(THEME)
    first = flow.surface.bias
    flow.show_stage(GOAL)
    assert flow.surface.bias != first


def test_back_is_offered_on_every_step_after_the_first(fresh_window, qtbot):
    fresh_window.set_reduced_motion(True)
    flow = show_setup(fresh_window, qtbot)
    assert flow.back.isHidden()
    for stage in (ACCOUNT, THEME, GOAL):
        flow.show_stage(stage)
        assert not flow.back.isHidden(), stage
    shown = []
    flow.show_stage = shown.append
    flow.stage = THEME
    flow.back.click()
    assert shown == [PRIVACY]


def test_a_first_run_opens_on_the_motto_screen_alone(fresh_window, qtbot):
    flow = SetupDialog(fresh_window)
    qtbot.addWidget(flow)
    flow.show()
    assert flow.stage == OPENING
    assert flow.opener_title.text() == "Your team, plus Agents."
    assert flow.art.isHidden() and flow.top.isHidden()
    assert flow.back.isHidden() and flow.primary.isHidden()
    assert not flow.begin.isHidden() and flow.pages.currentIndex() == 2
    flow.begin.click()
    assert flow.stage == WELCOME and not flow.art.isHidden() and not flow.top.isHidden()


def test_reviewing_setup_later_skips_the_motto_screen(fresh_window, qtbot):
    fresh_window.settings.setValue(account_key(fresh_window) + "/setup", True)
    flow = SetupDialog(fresh_window)
    qtbot.addWidget(flow)
    flow.show()
    assert flow.stage == WELCOME


def test_windows_arrive_instead_of_popping_in(fresh_window, qtbot, monkeypatch):
    from aedrova.desktop import motion

    calls = []
    monkeypatch.setattr(motion, "appear_window", lambda w, *a, **k: calls.append((w, a, k)))
    flow = SetupDialog(fresh_window)
    qtbot.addWidget(flow)
    flow.show()
    assert calls and calls[0][0] is flow and calls[0][1] == (700,)


def test_appear_window_runs_and_is_skipped_for_reduced_motion(fresh_window, qtbot, monkeypatch):
    from aedrova.desktop import motion

    assert motion.appear_window(fresh_window, 40) is not None
    qtbot.wait(150)
    monkeypatch.setattr(motion, "reduced", lambda: True)
    assert motion.appear_window(fresh_window, 40) is None


def test_changing_screens_glides_the_old_one_out_and_blurs_scenes_through(fresh_window, qtbot):
    from aedrova.desktop import motion

    flow = show_setup(fresh_window, qtbot)
    assert not motion.reduced()
    flow.show_stage(THEME)
    assert flow.ghost is not None and flow.art.previous is not None
    assert flow.art.graphicsEffect() is not None
    qtbot.waitUntil(lambda: flow.art.previous is None, timeout=3000)
    flow.show_stage(WELCOME)
    assert flow.art.direction == -1  # going back moves the other way
    qtbot.waitUntil(lambda: flow.art.previous is None, timeout=3000)
    assert flow.art.graphicsEffect() is None


def test_reduced_motion_changes_screens_without_ghosts(fresh_window, qtbot):
    fresh_window.set_reduced_motion(True)
    flow = show_setup(fresh_window, qtbot)
    flow.show_stage(THEME)
    assert getattr(flow, "ghost", None) is None and flow.art.previous is None


def test_signing_in_waits_inside_setup_and_can_be_cancelled(fresh_window, qtbot, monkeypatch):
    fresh_window.set_reduced_motion(True)
    monkeypatch.setattr(AccountDialog, "start_provider", lambda *_: None)
    flow = show_setup(fresh_window, qtbot)
    flow.show_stage(ACCOUNT)
    flow.setup.signin("google")
    account = fresh_window.account_dialog
    assert account.quiet and flow.isVisible() and not account.isVisible()
    assert not any(b.isEnabled() for b in flow.setup.sign_in_buttons)
    flow.setup.cancel_signin.click()
    assert not account.quiet and all(b.isEnabled() for b in flow.setup.sign_in_buttons)
    assert flow.setup.wait_note.isHidden()


def test_joining_with_a_code_is_done_in_setup(qtbot, tmp_path, monkeypatch):
    window, _ = setup(qtbot, tmp_path)
    window.account_dialog.snapshot.update(workspaces=[], channels=[], members=[])
    flow = show_setup(window, qtbot)
    flow.show_stage(PROJECT)
    assert flow.setup.join_code.isHidden()
    flow.setup.have_code.click()
    sent = []
    monkeypatch.setattr(
        window.account_dialog, "mutate", lambda name, params, **_: sent.append((name, params))
    )
    flow.setup.join_code.setText(" CODE-1 ")
    flow.setup.join_button.click()
    qtbot.waitUntil(lambda: bool(sent), timeout=3000)
    assert sent == [("accept_invitation", {"p_token": "CODE-1"})]
    assert not window.account_dialog.isVisible()
    flow.setup.release_job()


def test_setup_covers_the_screen_and_takes_focus_back_after_pickers(fresh_window, qtbot):
    flow = show_setup(fresh_window, qtbot)
    flow.cover_screen()
    assert flow.windowFlags() & Qt.WindowType.FramelessWindowHint
    assert not flow.isFullScreen()  # no macOS Space for file pickers to wander off to
    flow.setup.flow.regain_focus()


def test_a_first_run_opens_light_even_when_the_app_is_dark(fresh_window, qtbot):
    fresh_window.set_theme("dark")
    flow = SetupDialog(fresh_window)
    qtbot.addWidget(flow)
    assert flow.theme.name == "light" and flow.theme_mode == "light"
    fresh_window.settings.setValue(flow.prefix + "/setup", True)
    later = SetupDialog(fresh_window)
    qtbot.addWidget(later)
    assert later.theme.name == "dark"  # reviewing setup keeps their own appearance


def slack_zip(tmp_path):
    import json
    from zipfile import ZipFile

    path = tmp_path / "export.zip"
    with ZipFile(path, "w") as archive:
        archive.writestr("channels.json", json.dumps([{"id": "C123", "name": "general"}]))
        archive.writestr(
            "general/2023-11-14.json",
            json.dumps([{"type": "message", "ts": "1700000000.000001", "text": "Ship it"}]),
        )
    return path


def test_the_slack_step_is_optional_inline_and_can_import(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    window.set_reduced_motion(True)
    writes = []
    service.rpc = lambda name, params: (
        [] if name == "list_slack_imports" else writes.append(params) or len(params["p_rows"])
    )
    account = window.account_dialog
    account.snapshot["members"] = [{"workspace_id": "w", "user_id": "u", "role": "owner"}]
    service.user = SimpleNamespace(id="u")
    flow = show_setup(window, qtbot)
    flow.created_workspace = flow.setup.workspace = "w"
    assert flow.setup.can_import_history()
    flow.show_stage(IMPORT)
    assert flow.art.scene == "import" and flow.dots.count == 8
    assert not flow.skip.isHidden() and flow.skip.text() == "Skip for now"
    assert flow.primary.isHidden()  # nothing to continue from until something was imported
    panel = flow.setup.import_panel
    panel.load_zip(slack_zip(tmp_path))
    qtbot.waitUntil(panel.primary.isEnabled)
    assert panel.items.count() == 1 and not writes
    panel.primary.click()
    qtbot.waitUntil(lambda: panel.finished, timeout=5000)
    assert writes[-1]["p_finish"] and panel.bar.isHidden()
    assert not flow.primary.isHidden() and flow.primary.text() == "Continue"
    flow.primary.click()
    assert flow.stage == GOAL


def test_only_an_owner_or_admin_is_offered_the_slack_step(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    window.account_dialog.snapshot["members"] = [
        {"workspace_id": "w", "user_id": "u", "role": "member"}
    ]
    service.user = SimpleNamespace(id="u")
    flow = show_setup(window, qtbot)
    flow.setup.workspace = flow.created_workspace = "w"
    assert not flow.setup.can_import_history()
    assert flow.after_project() == GOAL
