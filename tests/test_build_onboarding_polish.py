from types import SimpleNamespace

from PySide6.QtWidgets import QFileDialog
from test_connected import setup

from aedrova.desktop.controls import choose_project


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
