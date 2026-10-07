"""Actual local diffs and subprocess checks, plus scoped sharing UI regressions."""

import json
import subprocess
import sys
from dataclasses import replace
from types import SimpleNamespace

import pytest
from test_connected import setup
from test_context_retrieval import corpus
from test_product_memory import entry, payload

from aedrova.agents.checkout import prepare
from aedrova.agents.runtime import LocalRunner
from aedrova.delivery.evidence import command_result, manifest, project_fingerprint, validate
from aedrova.delivery.files import make_review
from aedrova.desktop.build_evidence import SharedBuilds
from aedrova.memory.model import snapshot_record


@pytest.fixture
def evidence(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "calculation.py").write_text("def add(a, b):\n    return a - b\n")
    project = prepare(source, tmp_path / "builds")
    (project / "calculation.py").write_text("def add(a, b):\n    return a + b\n")
    context = corpus()
    record = snapshot_record(payload(entry("approved")), "w", {"c"})
    context = replace(context, text=context.text + "\n" + json.dumps(record))
    checked = subprocess.run(
        [
            sys.executable,
            "-c",
            'from calculation import add; assert add(2, 3) == 5; print("1 assertion passed")',
        ],
        cwd=project,
        capture_output=True,
        text=True,
        check=False,
    )
    result = command_result("python: verify addition", checked.stdout, checked.returncode)
    result["project_fingerprint"] = project_fingerprint(project)
    value = manifest(context, "Implement addition", "codex", make_review(project), [result])
    return context, project, value


def test_real_changed_file_and_check_are_linked_without_agent_prose(evidence):
    _, _, value = evidence
    assert "+    return a + b" in value["files"][0]["diff"]
    assert value["checks"][0]["state"] == "passed"
    assert value["requirements"][0]["assessment"] == "not_assessed"
    row = value["requirements"][0]
    row.update(
        assessment="reviewer_verified", files=["calculation.py"], checks=[value["checks"][0]["id"]]
    )
    assert validate(value)


def test_successful_command_before_later_edits_cannot_verify_requirement(evidence):
    context, project, value = evidence
    (project / "calculation.py").write_text("def add(a, b):\n    return 0\n")
    value = manifest(context, "Implement addition", "codex", make_review(project), value["checks"])
    value["requirements"][0].update(
        assessment="reviewer_verified", files=["calculation.py"], checks=[value["checks"][0]["id"]]
    )
    with pytest.raises(ValueError, match="current files"):
        validate(value)


@pytest.mark.parametrize(
    "code,state", [(0, "passed"), (1, "failed"), (None, "unverified"), (False, "unverified")]
)
def test_command_exit_code_is_observed_not_inferred_from_output(code, state):
    assert command_result("pytest", "ALL PASSED says the agent", code)["state"] == state


def test_unrecognized_or_failed_checks_and_missing_files_never_verify(evidence):
    _, _, value = evidence
    value["requirements"][0].update(
        assessment="reviewer_verified", files=["calculation.py"], checks=[]
    )
    with pytest.raises(ValueError):
        validate(value)
    value["requirements"][0]["checks"] = ["invented"]
    with pytest.raises(ValueError, match="actual"):
        validate(value)
    value["requirements"][0]["checks"] = [value["checks"][0]["id"]]
    value["checks"][0]["state"] = "failed"
    with pytest.raises(ValueError):
        validate(value)


def test_secrets_are_not_in_command_receipts_or_shared_diffs(evidence):
    context, project, _ = evidence
    credential = "sk-ant-" + "a" * 30
    receipt = command_result("echo " + credential, credential, 0)
    assert credential not in json.dumps(receipt)
    (project / "calculation.py").write_text('token = "' + credential + '"')
    with pytest.raises(ValueError, match="credential"):
        manifest(context, "Task", "codex", make_review(project), [])


def test_runtime_records_completed_commands_with_file_snapshot(evidence):
    _, project, _ = evidence
    runner = LocalRunner(lambda text: None)
    runner.evidence_project = project
    runner.observe_command("pytest", "1 passed", 0)
    assert runner.command_results[0]["project_fingerprint"] == project_fingerprint(project)
    for _ in range(110):
        runner.observe_command("true", "", 0)
    assert len(runner.command_results) == 101


def test_shared_read_view_clears_evidence_on_account_change(qtbot, tmp_path, evidence):
    window, service = setup(qtbot, tmp_path)
    _, _, value = evidence
    row = {
        "id": "review",
        "evidence": value,
        "version": 1,
        "source_channels": ["c"],
        "current": True,
    }
    service.build_reviews = lambda workspace: {"items": [row], "setup_required": False}
    service.build_review_decisions = lambda identifier: []
    dialog = SharedBuilds(window)
    qtbot.addWidget(dialog)
    qtbot.waitUntil(lambda: bool(dialog.rows))
    assert not dialog.share.isVisible()
    assert "Implement addition" in dialog.details.toPlainText()
    window.workspace_id = "other"
    assert not dialog.valid()
    assert not dialog.rows and not dialog.value and not dialog.details.toPlainText()


def test_shared_review_failure_restores_controls_without_transport_details(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)

    def unavailable(_workspace):
        raise RuntimeError("private auth secret")

    service.build_reviews = unavailable
    dialog = SharedBuilds(window)
    qtbot.addWidget(dialog)
    qtbot.waitUntil(lambda: not dialog.busy)
    assert dialog.refresh_button.isEnabled()
    assert "secret" not in dialog.status.text()
    dialog.reject()


def test_share_draft_rejects_changed_local_files(qtbot, tmp_path, evidence):
    window, service = setup(qtbot, tmp_path)
    context, project, _ = evidence
    studio = SimpleNamespace(
        context=context,
        invalidated=False,
        request=SimpleNamespace(toPlainText=lambda: "Implement addition"),
        provider=SimpleNamespace(currentData=lambda: "codex"),
        project=project,
        command_results=[],
    )
    dialog = SharedBuilds(window, studio=studio, review=make_review(project))
    qtbot.addWidget(dialog)
    (project / "calculation.py").write_text("changed again")
    dialog.share_evidence()
    assert "Local files changed" in dialog.status.text()
    dialog.reject()


def test_invalid_receipt_state_and_criteria_are_rejected(evidence):
    _, _, value = evidence
    value["checks"][0]["exit_code"] = False
    with pytest.raises(ValueError, match="integer exit"):
        validate(value)
    value["checks"][0]["exit_code"] = 0
    value["acceptance_criteria"] = ["x" * 2001]
    with pytest.raises(ValueError, match="criteria"):
        validate(value)


def test_source_revocation_clears_all_cached_shared_content(qtbot, tmp_path, evidence):
    window, service = setup(qtbot, tmp_path)
    _, _, value = evidence
    service.build_reviews = lambda _: {
        "items": [
            {
                "id": "review",
                "evidence": value,
                "version": 1,
                "source_channels": ["c"],
                "current": True,
            }
        ],
        "setup_required": False,
    }
    service.build_review_decisions = lambda _: []
    dialog = SharedBuilds(window)
    qtbot.addWidget(dialog)
    qtbot.waitUntil(lambda: bool(dialog.rows))
    dialog.note.setPlainText("Private review")
    snapshot = dict(window.account_dialog.snapshot)
    snapshot["channels"] = []
    dialog.check_access(snapshot)
    assert dialog.closed and not dialog.rows and dialog.value is None
    assert not dialog.details.toPlainText() and not dialog.note.toPlainText()
    assert window.shared_build_dialog is None


def test_disconnecting_closes_shared_review(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    service.build_reviews = lambda _: {"items": [], "setup_required": False}
    dialog = SharedBuilds(window)
    qtbot.addWidget(dialog)
    qtbot.waitUntil(lambda: not dialog.busy)
    window.connected.disconnect()
    assert dialog.closed and window.shared_build_dialog is None
