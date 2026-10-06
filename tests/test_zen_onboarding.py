"""Exercise the real sequence, input scoping, account boundary and no-effect contract."""

from types import SimpleNamespace

import pytest
from PySide6.QtCore import QSettings, Qt

from aedrova.desktop.onboarding import SetupDialog, account_key
from aedrova.desktop.projects import binding
from aedrova.desktop.window import AedrovaWindow
from aedrova.desktop.zen_onboarding import processing_progress, settled_spring
from aedrova.desktop.zen_setup import LAST_STAGE


@pytest.fixture
def flow(qtbot, tmp_path, monkeypatch):
    window = AedrovaWindow(
        settings=QSettings(str(tmp_path / "zen.ini"), QSettings.Format.IniFormat)
    )
    qtbot.addWidget(window)
    window.show()

    def forbidden(*args, **kwargs):
        pytest.fail("Preview must not run product actions")

    for action in (
        "send_message",
        "start_agent_request",
        "create_workspace",
        "show_account",
    ):
        monkeypatch.setattr(window, action, forbidden)
    dialog = SetupDialog(window)
    qtbot.addWidget(dialog)
    dialog.clock = 100.0
    dialog.now = lambda: dialog.clock
    dialog.entered = dialog.now()
    dialog.show()
    dialog.timer.stop()
    return window, dialog


def advance_time(dialog, seconds):
    dialog.clock += seconds
    dialog.tick()


def test_full_sequence_timing_keyboard_and_dashboard_handoff(flow, qtbot, monkeypatch):
    window, dialog = flow
    dialog.activate()
    dialog.activate()  # double click cannot advance twice
    advance_time(dialog, 0.43)
    assert dialog.stage == 1
    qtbot.mouseClick(dialog.primary, Qt.MouseButton.LeftButton)
    assert dialog.success and not binding(window)
    advance_time(dialog, 1)
    assert dialog.stage == 2
    advance_time(dialog, 2.49)
    assert dialog.stage == 2 and 0 < dialog.processing < 1
    advance_time(dialog, 0.01)
    assert dialog.stage == 3
    qtbot.keyPress(dialog, Qt.Key.Key_Control)
    assert dialog.command_down
    qtbot.keyPress(dialog, Qt.Key.Key_K, Qt.KeyboardModifier.ControlModifier)
    assert dialog.unlocked
    advance_time(dialog, 0.7)
    assert dialog.stage == 4
    monkeypatch.setattr(dialog.setup, "advance_profile", lambda: dialog.show_stage(6))
    for stage in range(4, LAST_STAGE):
        assert dialog.stage == stage
        dialog.activate()
    assert dialog.stage == LAST_STAGE
    advance_time(dialog, 1)
    assert not dialog.isVisible() and not dialog.timer.isActive()
    key = account_key(window)
    assert window.settings.value(key + "/hasCompletedOnboarding", False, type=bool)
    assert window.settings.value(key + "/setup", False, type=bool)
    assert not binding(window)
    qtbot.waitUntil(lambda: window.tour is not None)
    assert window.tour.index == 0
    assert window.tour.next.hasFocus()
    window.tour.finish("completed")
    qtbot.waitUntil(lambda: window.composer.editor.hasFocus())


def test_click_alternative_and_account_change_cannot_mark_new_account(flow, qtbot):
    window, dialog = flow
    dialog.show_stage(3)
    qtbot.mouseClick(dialog.primary, Qt.MouseButton.LeftButton)
    assert dialog.unlocked
    window.current_user = lambda: SimpleNamespace(id="another-account")
    advance_time(dialog, 1)
    advance_time(dialog, 1)
    dialog.activate()
    assert not window.settings.value(account_key(window) + "/setup", False, type=bool)
    assert not dialog.timer.isActive()


def test_escape_skip_and_reduced_motion_do_not_grant_setup(flow, qtbot):
    window, dialog = flow
    dialog.reduced = True
    dialog.activate()
    advance_time(dialog, 0.06)
    assert dialog.stage == 1
    dialog.defer()
    assert dialog.stage == 4
    dialog.defer()
    assert dialog.isVisible() and dialog.stage == 5
    assert not window.settings.value(account_key(window) + "/deferred", False, type=bool)
    assert not window.settings.value(
        account_key(window) + "/hasCompletedOnboarding", False, type=bool
    )


@pytest.mark.parametrize("size", [(640, 620), (960, 720), (1440, 940)])
def test_all_scenes_render_and_controls_fit(flow, qtbot, size):
    _, dialog = flow
    dialog.resize(*size)
    for stage in range(LAST_STAGE + 1):
        dialog.show_stage(stage)
        qtbot.wait(5)
        assert not dialog.canvas.grab().isNull()
        assert dialog.rect().contains(dialog.primary.geometry())
        assert dialog.rect().contains(dialog.skip.geometry())


def test_curves_are_monotonic_accelerating_and_bounded():
    assert processing_progress(-1) == 0 and processing_progress(2.5) == 1
    assert processing_progress(2.5) - processing_progress(2) > processing_progress(0.5)
    values = [settled_spring(i / 60) for i in range(121)]
    assert values == sorted(values) and all(0 <= value <= 1 for value in values)


def test_boot_keyboard_and_escape_cleanup(flow, qtbot):
    _, dialog = flow
    qtbot.keyClick(dialog, Qt.Key.Key_Return)
    assert dialog.action_started is not None
    advance_time(dialog, 0.43)
    assert dialog.stage == 1
    qtbot.keyClick(dialog, Qt.Key.Key_Escape)
    assert not dialog.isVisible() and not dialog.timer.isActive()


def test_missing_logo_has_immediate_render_fallback(flow):
    from PySide6.QtGui import QPixmap

    _, dialog = flow
    dialog.logo = QPixmap()
    assert not dialog.canvas.grab().isNull()
    dialog.activate()
    advance_time(dialog, 0.43)
    assert dialog.stage == 1


def test_explicit_configuration_saves_account_scoped_project_not_a_build(
    qtbot, tmp_path, monkeypatch
):
    from test_connected import setup

    window, _ = setup(qtbot, tmp_path)
    monkeypatch.setattr(
        window, "start_agent_request", lambda *_: pytest.fail("No build during setup")
    )
    dialog = SetupDialog(window)
    qtbot.addWidget(dialog)
    project = tmp_path / "specific-project"
    project.mkdir()
    dialog.show_stage(6)
    dialog.setup.folder.setText(str(project))
    dialog.setup.provider.setCurrentIndex(1)
    dialog.activate()
    assert dialog.stage == 7
    assert not dialog.setup.automatic.isChecked()
    dialog.setup.automatic.setChecked(True)
    dialog.activate()
    dialog.setup.repository.setText("ayanshv/Aedrova")
    dialog.activate()
    dialog.activate()
    assert dialog.stage == 10 and not binding(window)
    dialog.activate()
    saved = binding(window)
    assert saved["folder"] == str(project)
    assert saved["provider"] == "claude_code"
    assert saved["background_build"] and saved["auto_plan"]
    assert saved["repository"] == "ayanshv/Aedrova"
    assert dialog.stage == LAST_STAGE


def test_permissions_require_project_and_original_workspace(qtbot, tmp_path):
    from test_connected import setup

    window, _ = setup(qtbot, tmp_path)
    dialog = SetupDialog(window)
    qtbot.addWidget(dialog)
    dialog.show_stage(7)
    dialog.setup.automatic.setChecked(True)
    dialog.activate()
    assert dialog.stage == 7 and not binding(window)
    project = tmp_path / "project"
    project.mkdir()
    dialog.show_stage(6)
    dialog.setup.folder.setText(str(project))
    window.workspace_id = "different-workspace"
    dialog.activate()
    assert dialog.stage == 6 and not binding(window)


def test_preferences_are_drafts_until_review_and_back_keeps_choices(flow):
    window, dialog = flow
    old_mode = window.theme_mode
    dialog.show_stage(4)
    dialog.setup.appearance.setCurrentIndex(dialog.setup.appearance.findData("light"))
    dialog.setup.editor.setCurrentText("Cursor")
    dialog.activate()
    assert window.theme_mode == old_mode
    dialog.show_stage(4)
    assert dialog.setup.editor.currentText() == "Cursor"
    dialog.show_stage(10)
    dialog.activate()
    assert window.theme_mode == "light"
    assert window.settings.value("editor") == "Cursor"


def test_integration_dialog_keeps_window_parent_and_resumes_flow(flow, qtbot):
    from PySide6.QtWidgets import QDialog

    window, dialog = flow
    child = QDialog(window)
    qtbot.addWidget(child)
    original = child.styleSheet()
    dialog.setup.show_child(child)
    assert child.parentWidget() is window
    assert child.isVisible() and not dialog.isVisible()
    child.accept()
    assert dialog.isVisible() and child.styleSheet() == original
    dialog.setup.show_child(child)
    dialog.reject()
    child.reject()
    assert not dialog.isVisible()


def test_theme_photos_choose_real_theme_and_persist_draft(flow, qtbot):
    _, dialog = flow
    dialog.show_stage(4)
    for mode in ("dark", "system", "light"):
        card = dialog.setup.theme_photos[mode]
        assert all(not image.isNull() for image in card.photos.values())
        qtbot.mouseClick(card, Qt.MouseButton.LeftButton)
        assert dialog.setup.appearance.currentData() == mode
        assert card.isChecked()
    dialog.show_stage(5)
    assert dialog.setup.preferences["theme"] == "light"


def test_system_photo_keeps_both_halves_when_assets_missing(qtbot):
    from PySide6.QtGui import QPixmap

    from aedrova.desktop.zen_visuals import ThemePhoto

    card = ThemePhoto("system")
    qtbot.addWidget(card)
    card.resize(300, 180)
    card.photos = {"light": QPixmap(), "dark": QPixmap()}
    image = card.grab().toImage()
    assert image.pixelColor(70, 50).lightness() > 200
    assert image.pixelColor(230, 50).lightness() < 60


def test_small_setup_illustrations_never_overlap_controls(flow, qtbot):
    from aedrova.desktop.zen_visuals import SetupVisual

    _, dialog = flow
    dialog.resize(640, 620)
    for stage in range(5, 11):
        dialog.show_stage(stage)
        qtbot.wait(10)
        items = [dialog.setup.column.itemAt(i).widget() for i in range(dialog.setup.column.count())]
        widgets = [widget for widget in items if widget is not None and widget.isVisible()]
        for previous, following in zip(widgets, widgets[1:], strict=False):
            assert previous.geometry().bottom() < following.geometry().top()
        for visual in dialog.setup.body.findChildren(SetupVisual):
            if visual.isVisible():
                assert visual.height() >= 172


def test_onboarding_theme_previews_all_scenes_without_saving(flow, qtbot):
    from PySide6.QtGui import QPalette

    from aedrova.desktop.theme import DARK, LIGHT

    window, dialog = flow
    original = window.theme_mode
    dialog.show_stage(4)
    qtbot.mouseClick(dialog.setup.theme_photos["dark"], Qt.MouseButton.LeftButton)
    assert dialog.theme == DARK
    assert dialog.palette().color(QPalette.ColorRole.WindowText).name() == DARK.text.lower()
    assert window.theme_mode == original
    for stage in range(LAST_STAGE + 1):
        dialog.show_stage(stage)
        qtbot.wait(5)
        screenshot = dialog.canvas.grab().toImage()
        assert screenshot.pixelColor(5, 5).lightness() < 60
        assert (
            sum(
                screenshot.pixelColor(x, y).lightness() > 180
                for x in range(32, screenshot.width() - 32, 3)
                for y in range(90, 180, 3)
            )
            > 100
        )
    dialog.show_stage(4)
    qtbot.mouseClick(dialog.setup.theme_photos["light"], Qt.MouseButton.LeftButton)
    assert dialog.theme == LIGHT
    assert dialog.canvas.grab().toImage().pixelColor(5, 5).lightness() > 240


def test_system_appearance_follows_changes_but_explicit_modes_do_not(flow, monkeypatch):
    from aedrova.desktop import zen_onboarding
    from aedrova.desktop.theme import DARK, LIGHT
    from aedrova.desktop.zen_theme import resolve_theme

    _, dialog = flow
    scheme = [Qt.ColorScheme.Light]
    monkeypatch.setattr(
        zen_onboarding, "resolve_theme", lambda mode: resolve_theme(mode, scheme[0])
    )
    dialog.apply_appearance("system")
    assert dialog.theme == LIGHT
    scheme[0] = Qt.ColorScheme.Dark
    dialog.system_appearance_changed()
    assert dialog.theme == DARK and dialog.theme_mode == "system"
    dialog.apply_appearance("light")
    dialog.system_appearance_changed()
    assert dialog.theme == LIGHT
    dialog.apply_appearance("dark")
    scheme[0] = Qt.ColorScheme.Light
    dialog.system_appearance_changed()
    assert dialog.theme == DARK


def test_google_returns_to_embedded_required_profile_then_project(qtbot, tmp_path):
    from PySide6.QtWidgets import QPushButton
    from test_connected import snapshot

    window = AedrovaWindow(
        settings=QSettings(str(tmp_path / "oauth-flow.ini"), QSettings.IniFormat)
    )
    qtbot.addWidget(window)
    window.show()
    dialog = SetupDialog(window)
    window.setup_dialog = dialog
    qtbot.addWidget(dialog)
    dialog.show()
    dialog.show_stage(5)
    dialog.activate()
    assert dialog.stage == 5 and "Sign in" in dialog.setup.status.text()
    dialog.setup.signin()
    account = window.account_dialog
    user = SimpleNamespace(
        id="u", email="maya@example.com", user_metadata={"full_name": "Maya Chen"}
    )
    stored = {}

    def save(values, photo):
        stored.update(values)
        return dict(values)

    service = SimpleNamespace(
        user=user,
        snapshot=lambda: {**snapshot(), "user_profile": dict(stored)},
        message_page=lambda *args, **kwargs: [],
        attachments_for=lambda _: [],
        realtime_credentials=lambda: None,
        rpc=lambda *args: None,
        save_full_profile=save,
    )
    account.service = service
    account.authenticated(user)
    qtbot.waitUntil(lambda: dialog.isVisible() and hasattr(dialog.setup, "profile_form"))
    assert not account.isVisible() and dialog.stage == 5
    assert dialog.owner == "u" and dialog.setup.workspace == "w"
    form = dialog.setup.profile_form
    assert form.name.text() == "Maya Chen"
    assert not any(
        control.isVisible() and control.text() == "Personalize my profile"
        for control in dialog.setup.body.findChildren(QPushButton)
    )
    dialog.activate()
    assert dialog.stage == 5 and form.stack.currentIndex() == 1
    dialog.setup.go_back()
    assert dialog.stage == 5 and form.stack.currentIndex() == 0
    dialog.activate()
    dialog.activate()
    assert dialog.stage == 5 and form.stack.currentIndex() == 2
    dialog.activate()
    qtbot.waitUntil(lambda: dialog.stage == 6)
    assert stored["profile_completed"] and stored["display_name"] == "Maya Chen"
    assert dialog.setup.workspace == "w" and not binding(window)
    account.loaded(service.snapshot())
    assert dialog.stage == 6  # ordinary refreshes never restart or advance onboarding
    window.connected.timer.stop()


def test_cancelled_google_returns_to_same_required_step(qtbot, tmp_path):
    window = AedrovaWindow(
        settings=QSettings(str(tmp_path / "cancel-login.ini"), QSettings.IniFormat)
    )
    qtbot.addWidget(window)
    window.show()
    dialog = SetupDialog(window)
    window.setup_dialog = dialog
    qtbot.addWidget(dialog)
    dialog.show_stage(5)
    dialog.show()
    dialog.setup.signin()
    window.account_dialog.reject()
    assert dialog.isVisible() and dialog.stage == 5 and dialog.owner is None
    dialog.activate()
    assert dialog.stage == 5


def test_first_account_has_no_demo_workspace_binding(qtbot, tmp_path):
    from test_connected import snapshot

    window = AedrovaWindow(
        settings=QSettings(str(tmp_path / "new-account.ini"), QSettings.IniFormat)
    )
    qtbot.addWidget(window)
    window.show()
    dialog = SetupDialog(window)
    window.setup_dialog = dialog
    qtbot.addWidget(dialog)
    dialog.show_stage(5)
    dialog.show()
    dialog.setup.signin()
    account = window.account_dialog
    user = SimpleNamespace(id="u", email="new@example.com", user_metadata={"name": "New Member"})
    empty = {**snapshot(), "workspaces": [], "channels": [], "members": []}
    account.service = SimpleNamespace(user=user, snapshot=lambda: empty)
    account.authenticated(user)
    qtbot.waitUntil(lambda: dialog.isVisible() and dialog.owner == "u")
    assert dialog.setup.workspace is None
    assert not dialog.setup.same_account()
    dialog.show_stage(6)
    folder = tmp_path / "project"
    folder.mkdir()
    dialog.setup.folder.setText(str(folder))
    assert not dialog.setup.valid()
    assert not binding(window)


def test_required_profile_failure_keeps_step_and_retry_controls(qtbot, tmp_path):
    from test_connected import setup

    window, service = setup(qtbot, tmp_path)
    service.save_full_profile = lambda *_: (_ for _ in ()).throw(
        ValueError("username is already taken")
    )
    dialog = SetupDialog(window)
    qtbot.addWidget(dialog)
    dialog.show()
    dialog.show_stage(5)
    form = dialog.setup.profile_form
    form.name.setText("Maya")
    form.username.setText("maya_chen")
    form.go(2)
    dialog.activate()
    qtbot.waitUntil(lambda: not form.saving)
    assert dialog.stage == 5 and "taken" in form.error.text()
    assert dialog.primary.isEnabled() and dialog.back.isEnabled()
    assert form.name.text() == "Maya" and form.username.text() == "maya_chen"
    assert not window.settings.value(account_key(window) + "/setup", False, type=bool)
