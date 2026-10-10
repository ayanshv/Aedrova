import copy
import json
from dataclasses import replace

import pytest
from test_connected import setup
from test_context_retrieval import corpus

from aedrova.agents.retrieval import ContextIndex, validate_citations
from aedrova.desktop.product_memory import ProductMemory
from aedrova.memory.model import snapshot_record


def entry(state="proposal", fresh=True):
    return {
        "id": "memory1",
        "workspace_id": "w",
        "channel_id": "c",
        "version": 1,
        "title": "Export timezone",
        "body": "Use UTC",
        "state": state,
        "kind": "constraint",
        "fresh": fresh,
        "updated_at": "2026-10-06T12:00:00Z",
        "updated_by": "u",
        "sources": [{"kind": "message", "id": "0", "fingerprint": "hash"}],
        "resolved_sources": [
            {
                "kind": "message",
                "id": "0",
                "channel_id": "c",
                "citation": "message:0",
                "fingerprint": "hash",
                "body": "Use UTC",
            }
        ],
    }


def payload(row=None):
    return {"items": [row or entry()], "total": 1, "truncated": False}


def test_pinned_memory_changes_with_version_or_source_and_rejects_invalid_scope():
    original = payload()
    baseline = snapshot_record(original, "w", {"c"})
    changed = copy.deepcopy(original)
    changed["items"][0]["version"] += 1
    assert snapshot_record(changed, "w", {"c"}) != baseline
    changed["items"][0]["resolved_sources"][0]["channel_id"] = "private"
    with pytest.raises(PermissionError):
        snapshot_record(changed, "w", {"c"})
    with pytest.raises(PermissionError):
        snapshot_record(original, "other", {"c"})
    with pytest.raises(PermissionError):
        snapshot_record(original, "w", set())
    assert snapshot_record({"items": [], "total": 0}, "w", {"c"}) != baseline


@pytest.mark.parametrize(
    "state,fresh,expected",
    [
        ("approved", True, "memory_approved"),
        ("approved", False, "memory_stale"),
        ("proposal", True, "memory_proposal"),
        ("conflict", True, "memory_conflict"),
        ("superseded", True, "memory_superseded"),
        ("retired", True, "memory_retired"),
    ],
)
def test_retrieval_keeps_review_states_and_exact_citations(state, fresh, expected):
    context = corpus()
    record = snapshot_record(payload(entry(state, fresh)), "w", {"c"})
    context = replace(context, text=context.text + "\n" + json.dumps(record))
    index = ContextIndex(context)
    found = index.search("memory:memory1")[0]
    assert found.decision == expected
    assert (
        index.retrieve("timezone")["retrieval"]["product_memory"]
        == record["product_memory_snapshot"]
    )
    assert validate_citations(context, "Use memory:memory1 and message:0")
    with pytest.raises(ValueError):
        validate_citations(context, "Use memory:unknown")
    index.close()


def configure(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    service.memory_list = lambda *args: payload()
    service.memory_source = lambda *args: entry()["resolved_sources"][0]
    service.memory_history = lambda *args: [
        {"version": 1, "changed_at": "today", "record": entry()}
    ]
    service.recent_context = lambda *args: [{"id": "0", "channel_id": "c", "body": "Use UTC"}]
    service.search_context = lambda *args: [{"id": "0", "channel_id": "c", "body": "Use UTC"}]
    saved = []
    service.save_memory = lambda p: saved.append(copy.deepcopy(p)) or p["p_id"]
    dialog = ProductMemory(window)
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitUntil(lambda: not dialog.busy)
    return window, service, dialog, saved


def test_explicit_approval_edit_history_and_supersession(qtbot, tmp_path):
    window, service, dialog, saved = configure(qtbot, tmp_path)
    dialog.list.setCurrentRow(0)
    dialog.state.setCurrentText("approved")
    dialog.save_entry()
    assert not saved and "approval" in dialog.status.text()
    dialog.approval.setChecked(True)
    dialog.save_entry()
    qtbot.waitUntil(lambda: not dialog.busy)
    assert saved[0]["p_version"] == 1 and saved[0]["p_state"] == "approved"
    dialog.list.setCurrentRow(0)
    dialog.load_history()
    qtbot.waitUntil(lambda: not dialog.busy)
    assert "v1" in dialog.history.toPlainText()
    dialog.supersede()
    dialog.body.setPlainText("Use local time")
    dialog.approval.setChecked(True)
    dialog.save_entry()
    qtbot.waitUntil(lambda: not dialog.busy)
    assert saved[-1]["p_supersedes"] == "memory1"
    assert saved[-1]["p_supersedes_version"] == 1
    assert saved[-1]["p_id"] != "memory1"
    dialog.reject()
    assert not dialog.rows and not dialog.body.toPlainText()


def test_source_selection_and_revocation_clear_cached_evidence(qtbot, tmp_path):
    window, service, dialog, _ = configure(qtbot, tmp_path)
    dialog.find_sources()
    qtbot.waitUntil(lambda: not dialog.busy)
    dialog.choose_source(0)
    qtbot.waitUntil(lambda: not dialog.busy)
    assert dialog.sources[0]["id"] == "0"
    service.memory_source = lambda *args: None
    dialog.review_sources()
    qtbot.waitUntil(lambda: not dialog.busy)
    assert not dialog.sources and not dialog.evidence.toPlainText()
    window.account_dialog.session_closed.emit()
    assert dialog.closed and not dialog.rows


def test_missing_migration_and_compact_themes(qtbot, tmp_path):
    window, service, dialog, _ = configure(qtbot, tmp_path)
    for theme in ("light", "dark"):
        window.set_theme(theme)
        dialog.resize(640, 640)
        assert dialog.title.isVisible() and dialog.save.isVisible()
    service.memory_list = lambda *a: {"items": [], "total": 0, "setup_required": True}
    dialog.refresh()
    qtbot.waitUntil(lambda: not dialog.busy)
    assert not dialog.save.isEnabled() and "migration" in dialog.status.text()
    dialog.reject()


def test_conflict_and_question_cannot_be_approved(qtbot, tmp_path):
    _, _, dialog, saved = configure(qtbot, tmp_path)
    dialog.list.setCurrentRow(0)
    dialog.kind.setCurrentText("question")
    dialog.state.setCurrentText("approved")
    dialog.approval.setChecked(True)
    dialog.save_entry()
    assert not saved and "question" in dialog.status.text()
    dialog.kind.setCurrentText("constraint")
    dialog.state.setCurrentText("conflict")
    dialog.save_entry()
    assert not saved and "conflicting" in dialog.status.text()
    dialog.reject()


def test_memory_context_rechecks_after_collection_and_limits(qtbot):
    from test_builds import service

    from aedrova.agents.context import gather

    source = service()
    source.memory_list = lambda *args: payload(entry("approved"))
    result = gather(source, "w")
    assert "product_memory_snapshot" in result.text
    first = True

    def changing(*_):
        nonlocal first
        row = entry("approved")
        row["version"] = 1 if first else 2
        first = False
        return payload(row)

    source.memory_list = changing
    with pytest.raises(ValueError, match="memory changed"):
        gather(source, "w")
    source.memory_list = lambda *a: {**payload(), "truncated": True, "total": 201}
    with pytest.raises(ValueError, match="200 entries"):
        gather(source, "w")


def test_request_error_restores_controls_and_drops_cached_evidence(qtbot, tmp_path):
    _, service, dialog, _ = configure(qtbot, tmp_path)

    def failure(*_):
        raise RuntimeError("private transport secret")

    service.memory_list = failure
    dialog.refresh()
    qtbot.waitUntil(lambda: not dialog.busy)
    assert dialog.save.isEnabled()
    assert not dialog.rows and not dialog.body.toPlainText()
    assert "secret" not in dialog.status.text()
    dialog.reject()


def test_active_build_memory_verification_cancels_changed_context(qtbot, tmp_path):
    from types import SimpleNamespace

    from aedrova.desktop.builds import BuildDialog

    window, service, dialog, _ = configure(qtbot, tmp_path)
    context = corpus()
    context = replace(
        context, text=context.text + "\n" + json.dumps(snapshot_record(payload(), "w", {"c"}))
    )
    cancelled = []
    fake = SimpleNamespace(
        invalidated=False,
        context=context,
        account=window.account_dialog,
        workspace="w",
        window=window,
        review_dialog=None,
        cancel=lambda: cancelled.append(True),
        status=dialog.status,
    )
    changed = entry()
    changed["version"] = 2
    service.memory_list = lambda *_: payload(changed)
    BuildDialog.verify_memory(fake, force=True)
    qtbot.waitUntil(lambda: not fake.memory_check_pending)
    assert fake.invalidated and cancelled and not fake.approved_plan
    dialog.reject()


def test_stale_edit_conflict_is_friendly_and_does_not_expose_transport_text(qtbot, tmp_path):
    _, service, dialog, _ = configure(qtbot, tmp_path)

    class ConflictError(RuntimeError):
        code = "PT409"

    def conflict(*_):
        raise ConflictError("private transport secret")

    service.memory_list = conflict
    dialog.refresh()
    qtbot.waitUntil(lambda: not dialog.busy)
    assert dialog.save.isEnabled()
    assert not dialog.rows and not dialog.body.toPlainText()
    assert "changed" in dialog.status.text() and "review" in dialog.status.text()
    assert "secret" not in dialog.status.text()
    dialog.reject()
