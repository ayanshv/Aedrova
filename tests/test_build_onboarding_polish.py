from types import SimpleNamespace

from PySide6.QtWidgets import QFileDialog, QPushButton
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


def test_result_finishing_in_another_channel_stays_with_original_chat(qtbot, tmp_path, monkeypatch):
    from test_connected import row, snapshot

    window, _ = setup(qtbot, tmp_path)
    qtbot.waitUntil(lambda: not window.account_dialog.busy)
    data = snapshot()
    data["channels"].append(
        {"id": "other", "workspace_id": "w", "name": "other", "private": False}
    )
    window.connected.apply(data, [row()], "w", "c")
    monkeypatch.setattr(window.connected, "refresh", lambda: None)
    window.build_dialog = SimpleNamespace(
        workspace="w", pending=True, invalidated=False, background_transition=False
    )
    window.activity_channel = "c"
    window.agent_activity("w", "Reading your team’s decisions…")
    assert window.messages.agent_visible
    window.switch_channel("other")
    assert not window.messages.agent_visible
    window.build_dialog.pending = False
    window.finish_agent_response("w", "Built the feature.")
    assert window.agent_feed.status_row is None
    assert not window.messages.agent_visible
    assert window.message_stack.currentIndex() == 1
    assert window.connected.agent_replies[("w", "c")][0]["body"] == "Built the feature."
    window.switch_channel("c")
    assert window.messages.agent_visible
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
    dialog.progress("Running: python3 -m pytest")
    response = "Feature implemented.\n\n## Verification\n\n- `pytest` passed."
    dialog.finished(
        {
            "ok": True,
            "text": response,
            "project": tmp_path,
            "baseline": "",
            "changes": "feature.py",
            "commands": [{"state": "passed"}, {"state": "failed"}, {"state": "unverified"}],
        },
        False,
    )
    assert window.agent_feed.toPlainText().startswith(response)
    assert "1 passed · 1 failed · 1 unverified" in window.agent_feed.toPlainText()
    assert dialog.report_tabs.currentWidget() is dialog.response
    assert "<h2" in dialog.response.toHtml()
    assert "Running:" not in dialog.response.toPlainText()
    assert "Running: python3 -m pytest" in dialog.output.toPlainText()
    actions = window.agent_feed.reply_row.findChildren(QPushButton)
    assert [action.text() for action in actions] == ["Review changes"]
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
