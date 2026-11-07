"""Settings scopes retain working controls without exposing team actions as personal ones."""

from PySide6.QtWidgets import QPushButton
from test_connected import setup

from aedrova.desktop.preferences import SettingsDialog
from aedrova.desktop.projects import ProjectDialog


def test_personal_and_workspace_controls_are_separate(qtbot, tmp_path, monkeypatch):
    monkeypatch.setattr("aedrova.desktop.preferences.application_origin", lambda: "")
    window, _ = setup(qtbot, tmp_path)
    personal = SettingsDialog(window)
    team = SettingsDialog(window, scope="workspace")
    qtbot.addWidget(personal)
    qtbot.addWidget(team)
    assert "profile" in personal.view.pages and "billing" not in personal.view.pages
    assert "integrations" not in personal.view.pages
    assert set(team.view.pages) == {"integrations", "billing"}
    assert not hasattr(team, "appearance")
    personal.show()
    personal.view.buttons["appearance"].click()
    assert personal.appearance.isVisible() and not personal.name.isVisible()
    personal.appearance.setCurrentIndex(personal.appearance.findData("dark"))
    assert window.theme_mode == "dark"
    assert all(not button.icon().isNull() for button in personal.view.buttons.values())
    personal.view.buttons["language"].setChecked(True)
    assert personal.view.sections.currentIndex() == personal.view.pages["language"]
    window.account_dialog.session_closed.emit()
    assert not personal.isVisible() and not team.isVisible()


def test_settings_pages_fit_both_themes_and_keep_footer_visible(qtbot, tmp_path, monkeypatch):
    monkeypatch.setattr("aedrova.desktop.preferences.application_origin", lambda: "")
    window, _ = setup(qtbot, tmp_path)
    personal = SettingsDialog(window)
    project = ProjectDialog(window)
    qtbot.addWidget(personal)
    qtbot.addWidget(project)
    for theme in ("light", "dark"):
        window.set_theme(theme, persist=False)
        for dialog in (personal, project):
            dialog.resize(800, 620)
            dialog.show()
            for key in dialog.view.pages:
                dialog.view.show_section(key)
                qtbot.wait(5)
                page = dialog.view.sections.currentWidget()
                assert page.horizontalScrollBar().maximum() == 0, key
                assert all(not b.icon().isNull() for b in dialog.view.buttons.values())
            # The primary save/done stays outside the independently scrolling pages.
            primary = [
                b
                for b in dialog.findChildren(QPushButton)
                if b.text() in ("Done", "Save connection")
            ][0]
            assert primary.isVisible() and primary.isEnabled()
            assert dialog.rect().contains(primary.mapTo(dialog, primary.rect().bottomRight()))
            dialog.hide()
    project.view.buttons["ai"].setChecked(True)
    assert project.view.sections.currentIndex() == project.view.pages["ai"]


def test_workspace_tool_links_require_current_authorized_workspace(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    account = window.account_dialog
    opened = []
    account.open_workspace_tool(lambda: opened.append(window.workspace_id))
    assert opened == ["w"]
    account.workspaces.addItem("Unavailable workspace", "missing")
    account.workspaces.setCurrentIndex(account.workspaces.findData("missing"))
    account.open_workspace_tool(lambda: opened.append(window.workspace_id))
    assert opened == ["w"]
    assert "Refresh your workspace access" in account.status.text()
