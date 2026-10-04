from types import SimpleNamespace

from PySide6.QtWidgets import QFileDialog
from test_connected import setup

from aedrova.desktop.controls import choose_project
from aedrova.desktop.onboarding import SetupDialog
from aedrova.desktop.projects import binding


def test_working_status_is_in_chat_and_final_result_replaces_transients(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    window.build_dialog = SimpleNamespace(
        workspace="w",
        pending=True,
        background_transition=False,
        invalidated=False,
        job=None,
        verify_access=lambda _: None,
    )
    window.agent_activity("w", "Reading your team’s decisions…")
    assert window.messages.isAncestorOf(window.build_activity)
    window.agent_event("w", "Running: python3 -m pytest")
    window.agent_event("w", "$ python3 -m pytest\n4 passed\nExit code: 0")
    controls = window.agent_feed.status_controls
    window.finish_agent_response("w", "Built the feature. All four tests passed.")
    qtbot.wait(20)
    assert window.agent_feed.toPlainText() == "Built the feature. All four tests passed."
    assert len(window.agent_feed.rows) == 1
    assert not window.agent_feed.running
    assert controls.isHidden()
    window.agent_activity("w", "Starting the next build…")
    assert window.messages.isAncestorOf(window.build_activity)
    window.finish_agent_response("w", "Cancelled. Partial changes are available for review.")
    assert "Starting" not in window.agent_feed.toPlainText()
    window.build_dialog = None


def test_onboarding_saves_explicit_project_authority_without_running_build(
    qtbot, tmp_path, monkeypatch
):
    window, _ = setup(qtbot, tmp_path)
    monkeypatch.setattr(
        window,
        "start_agent_request",
        lambda *_: (_ for _ in ()).throw(AssertionError("Onboarding must not start builds")),
    )
    project = tmp_path / "project"
    project.mkdir()
    dialog = SetupDialog(window)
    qtbot.addWidget(dialog)
    dialog.show_step(2)
    assert not dialog.automatic_builds.isChecked()
    dialog.project_folder.setText(str(project))
    dialog.automatic_builds.setChecked(True)
    dialog.coding_provider.setCurrentIndex(dialog.coding_provider.findData("claude_code"))
    dialog.show_step(1)
    dialog.show_step(2)
    assert dialog.project_folder.text() == str(project)
    assert dialog.automatic_builds.isChecked()
    dialog.advance()
    assert dialog.step == 3
    saved = binding(window)
    assert saved["folder"] == str(project.resolve())
    assert saved["provider"] == "claude_code"
    assert saved["auto_plan"] and saved["background_build"]


def test_onboarding_rejects_missing_folder_and_changed_account(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    dialog = SetupDialog(window)
    qtbot.addWidget(dialog)
    dialog.show_step(2)
    dialog.automatic_builds.setChecked(True)
    dialog.advance()
    assert dialog.step == 2 and not binding(window)
    dialog.project_folder.setText(str(tmp_path))
    window.current_user = lambda: SimpleNamespace(id="different-user")
    dialog.advance()
    assert dialog.step == 2 and not binding(window)


def test_project_picker_requests_native_folder_dialog(monkeypatch):
    calls = []
    monkeypatch.setattr(QFileDialog, "getExistingDirectory", lambda *args: calls.append(args) or "")
    assert choose_project(None, "/tmp") == ""
    assert calls[0][-1] & QFileDialog.Option.ShowDirsOnly
    assert not calls[0][-1] & QFileDialog.Option.DontUseNativeDialog


def test_finished_build_keeps_results_and_removes_live_activity(qtbot, tmp_path):
    from aedrova.desktop.builds import BuildDialog

    window, _ = setup(qtbot, tmp_path)
    dialog = BuildDialog(window)
    qtbot.addWidget(dialog)
    window.build_dialog = dialog
    dialog.pending = True
    window.agent_activity("w", "Working on the project…")
    window.agent_event("w", "Running: python3 -m pytest")
    dialog.finished(
        {
            "ok": True,
            "text": "Feature implemented. Four tests passed.",
            "project": tmp_path,
            "baseline": "",
            "changes": "feature.py",
        },
        False,
    )
    assert window.agent_feed.toPlainText() == "Feature implemented. Four tests passed."
    assert not window.agent_feed.running and window.agent_feed.status_row is None
    dialog.pending = True
    window.agent_activity("w", "Trying again…")
    dialog.finished(
        {
            "ok": False,
            "text": "Provider unavailable. Your files are safe.",
            "project": tmp_path,
            "baseline": "",
        },
        False,
    )
    assert window.agent_feed.toPlainText() == "Provider unavailable. Your files are safe."
