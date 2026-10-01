"""Durability, isolation, scheduling and mention interaction acceptance."""

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from PySide6.QtCore import Qt
from test_background_builds import configured

from aedrova.agents.ledger import RunLedger
from aedrova.agents.runtime import LocalRunner
from aedrova.desktop.builds import start_background_build
from aedrova.desktop.conversation import Composer
from aedrova.desktop.execution import execution_queue
from aedrova.desktop.projects import save_binding


def test_atomic_duplicate_queue_and_limits(tmp_path):
    ledger = RunLedger(tmp_path / "queue")
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: ledger.enqueue("u", "w", "Build it", {}), range(20)))
    assert len({r[0] for r in results}) == 1
    assert sum(r[1] for r in results) == 1
    for number in range(9):
        ledger.enqueue("u", "w", f"Build {number}", {})
    with pytest.raises(ValueError, match="full"):
        ledger.enqueue("u", "w", "Overflow", {})
    assert not ledger.rows("other", "w")
    assert not ledger.rows("u", "other")
    assert ledger.path.stat().st_mode & 0o777 == 0o600


def test_restart_never_replays_and_lock_exclusive(tmp_path):
    first = RunLedger(tmp_path)
    running, _ = first.enqueue("u", "w", "Running", {})
    queued, _ = first.enqueue("u", "w", "Waiting", {})
    first.update(running, "running", project="/saved/copy")
    lease = first.lock()
    second = RunLedger(tmp_path)
    assert second.lock() is None
    lease.close()
    lease = second.lock()
    assert lease
    second.recover()
    states = {r["id"]: r for r in second.rows("u", "w")}
    assert states[running]["state"] == "interrupted"
    assert states[running]["project"] == "/saved/copy"
    assert states[queued]["state"] == "paused"
    lease.close()


def test_usage_unknown_not_zero_and_scoped(tmp_path):
    ledger = RunLedger(tmp_path)
    run, _ = ledger.enqueue("u", "w", "Build", {})
    ledger.record_usage(run, "planning", "codex", 1.5, {"input_tokens": 40})
    ledger.record_usage(run, "building", "codex", 3, {"output_tokens": -2})
    rows = ledger.usage(run, "u", "w")
    assert len(rows) == 2
    assert next(r for r in rows if r["phase"] == "planning")["input_tokens"] == 40
    assert all(r["output_tokens"] is None for r in rows)
    assert not ledger.usage(run, "other", "w")
    assert not ledger.usage(run, "u", "other")


@pytest.mark.parametrize("key", [Qt.Key.Key_Tab, Qt.Key.Key_Return])
def test_mention_keyboard_does_not_send(qtbot, key):
    composer = Composer()
    qtbot.addWidget(composer)
    composer.show()
    sent = []
    composer.submitted.connect(sent.append)
    composer.editor.setFocus()
    qtbot.keyClicks(composer.editor, "@ae")
    assert composer.suggestion.isVisible()
    qtbot.keyClick(composer.editor, key)
    assert composer.editor.toPlainText() == "@Aedrova "
    assert not sent and composer.suggestion.isHidden()
    qtbot.keyClicks(composer.editor, "build it")
    qtbot.keyClick(composer.editor, Qt.Key.Key_Return)
    assert sent == ["@Aedrova build it"]


def test_mention_click_escape_email_unicode(qtbot):
    composer = Composer()
    qtbot.addWidget(composer)
    composer.show()
    composer.editor.setPlainText("email@example.com")
    assert composer.suggestion.isHidden()
    composer.editor.setPlainText("🚀 @")
    cursor = composer.editor.textCursor()
    cursor.movePosition(cursor.MoveOperation.End)
    composer.editor.setTextCursor(cursor)
    assert composer.suggestion.isVisible()
    composer.suggestion.click()
    assert composer.editor.toPlainText() == "🚀 @Aedrova "
    composer.editor.clear()
    qtbot.keyClicks(composer.editor, "@")
    qtbot.keyClick(composer.editor, Qt.Key.Key_Escape)
    assert composer.suggestion.isHidden()
    assert composer.editor.toPlainText() == "@"


def test_queue_serializes_and_preserves_iteration_and_usage(qtbot, tmp_path, monkeypatch):
    window, _, root = configured(qtbot, tmp_path, monkeypatch)
    gate = threading.Event()
    entered = threading.Event()
    calls = []

    def run(self, provider, project, prompt, *, plan):
        calls.append(plan)
        if len(calls) == 1:
            entered.set()
            gate.wait(5)
        self.usage = {"input_tokens": 11, "output_tokens": 3}
        if plan:
            return "Implement. [message:requirement]"
        (project / "hello.py").write_text("ok = True")
        return "Done"

    monkeypatch.setattr(LocalRunner, "run", run)
    assert start_background_build(window, "First")
    qtbot.waitUntil(entered.is_set)
    assert start_background_build(window, "Second")
    assert start_background_build(window, "Second")
    queue = execution_queue(window)
    assert len(queue.ledger.rows("u", "w")) == 2
    assert calls == [True]
    gate.set()
    qtbot.waitUntil(
        lambda: all(r["state"] == "completed" for r in queue.ledger.rows("u", "w")), timeout=15000
    )
    assert calls == [True, False, True, False]
    for row in queue.ledger.rows("u", "w"):
        assert len(queue.ledger.usage(row["id"], "u", "w")) == 2
    assert not (root / "hello.py").exists()


def test_queue_pauses_changed_scope_and_logout(qtbot, tmp_path, monkeypatch):
    window, _, _ = configured(qtbot, tmp_path, monkeypatch)
    queue = execution_queue(window)
    queue.timer.stop()
    run, _ = queue.ledger.enqueue("u", "w", "Build", {"folder": "old"})
    monkeypatch.setattr(LocalRunner, "run", lambda *a, **k: pytest.fail("No provider allowed"))
    queue.tick()
    assert queue.ledger.rows("u", "w")[0]["state"] == "paused"
    save_binding(window, {"folder": "new", "background_build": True})
    queue.ledger.enqueue("u", "w", "More", {})
    queue.pause()
    assert all(r["state"] == "paused" for r in queue.ledger.rows("u", "w"))
    queue.show_history()
    window.account_dialog.session_closed.emit()
    assert not queue.dialog.isVisible()
    assert not queue.dialog.details.toPlainText()


def test_saved_result_review_rechecks_channels(qtbot, tmp_path, monkeypatch):
    from aedrova.desktop.builds import BuildDialog
    from aedrova.desktop.execution import scope
    from aedrova.desktop.projects import binding

    window, _, root = configured(qtbot, tmp_path, monkeypatch)
    queue = execution_queue(window)
    run, _ = queue.ledger.enqueue("u", "w", "Saved", scope(binding(window)))
    queue.ledger.update(run, "completed", project=root)
    queue.ledger.save_channels(run, {"revoked-private-channel"})
    queue.show_history()
    opened = []
    monkeypatch.setattr(BuildDialog, "open_review", lambda self: opened.append(self))
    queue.dialog.review_result()
    assert not opened
    queue.ledger.save_channels(run, {"c"})
    queue.dialog.refresh()
    queue.dialog.review_result()
    assert len(opened) == 1
    assert opened[0].context.channel_ids == {"c"}
    assert opened[0].project == root


def test_low_disk_prevents_snapshot(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from aedrova.agents.checkout import prepare

    root = tmp_path / "source"
    root.mkdir()
    monkeypatch.setattr(
        "aedrova.agents.checkout.shutil.disk_usage", lambda _: SimpleNamespace(free=1)
    )
    with pytest.raises(ValueError, match="512 MiB"):
        prepare(root, tmp_path / "copies")
    assert not list((tmp_path / "copies").iterdir())


def test_runtime_records_actual_usage(tmp_path, monkeypatch):
    from test_builds import fake_codex

    fake_codex(
        tmp_path,
        monkeypatch,
        """
print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'Done'}}),flush=True)
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':52,'output_tokens':7}}),flush=True)
""",
    )
    runner = LocalRunner(lambda _: None)
    assert runner.run("codex", tmp_path, "task", plan=True) == "Done"
    assert runner.usage == {"input_tokens": 52, "output_tokens": 7}
