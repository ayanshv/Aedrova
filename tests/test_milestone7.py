"""Account, project binding, and approved local-delivery journeys."""

from types import SimpleNamespace

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox
from test_connected import setup

from aedrova.desktop.builds import BuildDialog, open_build
from aedrova.desktop.preferences import SettingsDialog
from aedrova.desktop.projects import ProjectDialog, binding, binding_key, save_binding
from aedrova.desktop.review import ReviewDialog


def test_account_menu_routes_real_actions(qtbot, tmp_path):
    window, source = setup(qtbot, tmp_path)
    source.user.email = "person@example.test"
    source.user.user_metadata = {"full_name": "Test Person"}
    calls = []
    window.show_account = lambda intent=None: calls.append(intent)
    window.open_profile_menu()
    assert window.profile_button.text() == "TP"
    actions = {a.text(): a for a in window.profile_menu.actions()}
    assert not actions["person@example.test"].isEnabled()
    actions["Workspace settings…"].trigger()
    actions["Invite teammates…"].trigger()
    assert calls == ["manage", "invite"]
    assert "Log out" in actions
    window.profile_menu.close()


def test_settings_persist_and_clear_private_identity_on_logout(qtbot, tmp_path):
    window, source = setup(qtbot, tmp_path)
    source.user.user_metadata = {"full_name": "Before"}
    saved = []

    def update(value):
        saved.append(value)
        source.user.user_metadata["full_name"] = value

    source.update_profile = update
    dialog = SettingsDialog(window)
    qtbot.addWidget(dialog)
    dialog.name.setText("After Name")
    dialog.save.click()
    qtbot.waitUntil(lambda: dialog.save.isEnabled())
    assert saved == ["After Name"]
    assert window.profile_button.text() == "AN"
    dialog.appearance.setCurrentIndex(dialog.appearance.findData("dark"))
    dialog.motion.setChecked(True)
    dialog.transparency.setChecked(True)
    dialog.editor.setCurrentText("Finder")
    assert window.theme_mode == "dark"
    assert window.reduced_motion and window.reduced_transparency
    assert window.settings.value("editor") == "Finder"
    window.account_dialog.session_closed.emit()
    assert not dialog.name.text() and dialog.user is None
    assert not window.connected.active and not window.build_activity.isVisible()


def test_logout_empty_draft_does_not_require_confirmation(qtbot, tmp_path, monkeypatch):
    window, source = setup(qtbot, tmp_path)
    qtbot.waitUntil(lambda: not window.account_dialog.busy)
    window.store.drafts[("w", "c", "")] = ""
    calls = []
    window.account_dialog.sign_out = lambda: calls.append("logout")
    monkeypatch.setattr(QMessageBox, "question", lambda *args: pytest.fail("No draft to discard"))
    window.log_out()
    assert calls == ["logout"]


def test_logout_with_draft_can_be_cancelled(qtbot, tmp_path, monkeypatch):
    window, source = setup(qtbot, tmp_path)
    qtbot.waitUntil(lambda: not window.account_dialog.busy)
    window.composer.editor.setPlainText("Keep my thought")
    window.account_dialog.sign_out = lambda: pytest.fail("Logout was cancelled")
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.No)
    window.log_out()
    assert window.composer.editor.toPlainText() == "Keep my thought"


def test_project_binding_is_account_and_workspace_scoped(qtbot, tmp_path):
    window, source = setup(qtbot, tmp_path)
    save_binding(window, {"folder": str(tmp_path), "auto_plan": True})
    assert binding(window)["auto_plan"]
    assert binding(window, "other") == {}
    source.user = SimpleNamespace(id="other-user")
    assert binding(window) == {}
    window.settings.setValue(binding_key("other-user", "w"), "[]")
    assert binding(window) == {}


def test_project_save_keeps_selected_tab_and_reuses_connection(qtbot, tmp_path):
    window, source = setup(qtbot, tmp_path)
    project = tmp_path / "actual-project"
    project.mkdir()
    window.select_tab(1)
    dialog = ProjectDialog(window)
    qtbot.addWidget(dialog)
    dialog.folder.setText(str(project))
    dialog.repository.setText("https://github.com/team/project.git")
    dialog.auto_plan.setChecked(True)
    dialog.save()
    assert window.pages.currentIndex() == 1
    assert binding(window)["repository"] == "team/project"
    build = BuildDialog(window)
    qtbot.addWidget(build)
    assert build.repository.text() == str(project)
    assert build.consent.isChecked()
    dialog.disconnect()
    assert binding(window) == {}


def test_named_request_autoplans_only_with_explicit_opt_in(qtbot, tmp_path, monkeypatch):
    window, source = setup(qtbot, tmp_path)
    calls = []
    monkeypatch.setattr(BuildDialog, "start", lambda self, plan: calls.append(plan))
    open_build(window, "First request")
    qtbot.wait(30)
    assert not calls
    save_binding(window, {"folder": str(tmp_path), "background_build": True})
    open_build(window, "Second request")
    qtbot.waitUntil(lambda: bool(calls))
    assert calls == [True]
    assert window.build_dialog.request.toPlainText() == "Second request"


@pytest.mark.parametrize("theme", ["dark", "light"])
def test_dropdown_keyboard_and_theme(qtbot, tmp_path, theme):
    window, source = setup(qtbot, tmp_path)
    window.set_theme(theme)
    dialog = SettingsDialog(window)
    qtbot.addWidget(dialog)
    dialog.show()
    choice = dialog.editor
    choice.setFocus()
    qtbot.keyClick(choice, Qt.Key.Key_Down)
    assert choice.currentText() == "Cursor"
    choice.showPopup()
    assert choice.view().isVisible()
    assert not choice.view().grab().isNull()
    choice.hidePopup()


def test_review_actual_apply_and_logout_cleanup(qtbot, tmp_path, monkeypatch):
    from aedrova.agents.checkout import prepare

    window, service = setup(qtbot, tmp_path)
    service.fork_for_context = lambda: service
    service.close_context = lambda: None
    source = tmp_path / "project"
    source.mkdir()
    (source / "app.py").write_text("value = 1\n")
    build = BuildDialog(window)
    qtbot.addWidget(build)
    build.project = prepare(source, tmp_path / "copies")
    (build.project / "app.py").write_text("value = 2\n")
    review = ReviewDialog(build)
    qtbot.addWidget(review)
    qtbot.waitUntil(lambda: review.review is not None, timeout=5000)
    assert "+value = 2" in review.diff.toPlainText()
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.No)
    review.apply()
    assert (source / "app.py").read_text() == "value = 1\n"
    monkeypatch.setattr(QMessageBox, "question", lambda *args: QMessageBox.StandardButton.Yes)
    review.apply()
    qtbot.waitUntil(lambda: not review.job, timeout=5000)
    assert (source / "app.py").read_text() == "value = 2\n", review.status.text()
    assert build.repository.text() == str(source)
    assert not review.apply_button.isEnabled()
    window.account_dialog.session_closed.emit()
    assert review.cancelled.is_set()
    assert not review.diff.toPlainText() and review.review is None


def test_review_guest_cannot_publish(qtbot, tmp_path):
    from test_connected import snapshot

    window, service = setup(qtbot, tmp_path)
    service.fork_for_context = lambda: service
    service.close_context = lambda: None
    data = snapshot()
    data["members"][0]["role"] = "member"
    service.snapshot = lambda: data
    build = BuildDialog(window)
    qtbot.addWidget(build)
    review = ReviewDialog(build)
    qtbot.addWidget(review)
    qtbot.waitUntil(lambda: not review.job, timeout=5000)
    executed = []
    review.run(lambda guard: executed.append(True), lambda result: None, publishing=True)
    qtbot.waitUntil(lambda: not review.job, timeout=5000)
    assert "owner or admin" in review.status.text()
    assert not executed


def test_new_mention_respects_updated_project_binding(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    save_binding(window, {"folder": str(tmp_path / "first")})
    open_build(window, "Initial task")
    assert window.build_dialog.repository.text() == str(tmp_path / "first")
    save_binding(window, {"folder": str(tmp_path / "second")})
    open_build(window, "New task")
    assert window.build_dialog.repository.text() == str(tmp_path / "second")
