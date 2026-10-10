import os
import time

from aedrova.agents.checkout import prepare
from aedrova.agents.retention import CONTEXT_AGE, SNAPSHOT_AGE, maintain, protect


def snapshot(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "main.py").write_text("print('original')")
    root = tmp_path / "builds"
    project = prepare(source, root)
    stamp = time.time() - SNAPSHOT_AGE - 100
    os.utime(project.parent / "snapshot-info.json", (stamp, stamp))
    (project.parent / "workspace-context.jsonl").write_text("synthetic private context")
    return source, project, root


def test_only_redundant_idle_snapshot_expires(tmp_path):
    source, project, root = snapshot(tmp_path)
    preview = maintain(root, dry_run=True)
    assert preview["snapshots"] and project.exists()
    result = maintain(root)
    assert result["contexts"] and result["snapshots"]
    assert not project.parent.exists()
    assert (source / "main.py").read_text() == "print('original')"


def test_active_snapshot_and_context_are_preserved(tmp_path):
    _, project, root = snapshot(tmp_path)
    lease = protect(project)
    try:
        assert maintain(root) == {"contexts": [], "snapshots": []}
        assert (project.parent / "workspace-context.jsonl").exists()
    finally:
        lease.close()


def test_unapplied_edits_are_preserved_but_stale_context_expires(tmp_path):
    _, project, root = snapshot(tmp_path)
    (project / "main.py").write_text("print('unique build work')")
    result = maintain(root)
    assert result["contexts"] and not result["snapshots"]
    assert project.exists() and not (project.parent / "workspace-context.jsonl").exists()


def test_recovery_receipts_are_never_automatically_deleted(tmp_path):
    _, project, root = snapshot(tmp_path)
    (project.parent / "apply-backup-synthetic").mkdir()
    assert not maintain(root)["snapshots"]
    assert project.exists()


def test_changed_or_missing_original_keeps_copy(tmp_path):
    source, project, root = snapshot(tmp_path)
    (source / "main.py").unlink()
    assert not maintain(root)["snapshots"]
    assert project.exists()


def test_context_idle_age_uses_last_run_not_original_creation(tmp_path):
    _, project, root = snapshot(tmp_path)
    idle = project.parent / ".last-used"
    idle.touch()
    assert not maintain(root)["contexts"]
    assert maintain(root, now=time.time() + CONTEXT_AGE + 1)["contexts"]
    assert project.exists()


def test_symlink_cannot_escape_cleanup_root(tmp_path):
    _, project, root = snapshot(tmp_path)
    outside = tmp_path / "outside"
    outside.write_text("keep me")
    (project / "link").symlink_to(outside)
    assert not maintain(root)["snapshots"]
    assert outside.read_text() == "keep me"


def test_unknown_recovery_material_is_preserved(tmp_path):
    _, project, root = snapshot(tmp_path)
    (project.parent / "my-notes.txt").write_text("keep")
    assert not maintain(root)["snapshots"]


def test_old_snapshot_selected_for_iteration_is_not_pruned(tmp_path):
    _, project, root = snapshot(tmp_path)
    next_project = prepare(project, root)
    assert project.exists() and next_project.exists()


def test_protected_source_never_expires(tmp_path):
    _, project, root = snapshot(tmp_path)
    assert not maintain(root, protected=[project.parent])["snapshots"]
    assert (project.parent / "workspace-context.jsonl").exists()


def test_extra_hidden_material_cannot_be_silently_pruned(tmp_path):
    _, project, root = snapshot(tmp_path)
    (project / ".cache").mkdir()
    (project / ".cache" / "important.txt").write_text("preserve")
    assert not maintain(root)["snapshots"]
    assert (project / ".cache" / "important.txt").exists()
