"""Durable local scheduling and explicit recovery for autonomous builds."""

import json
from pathlib import Path
from types import SimpleNamespace

from PySide6.QtCore import QObject, QSettings, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QHBoxLayout, QListWidget, QPlainTextEdit, QVBoxLayout

from aedrova.agents.context import authorize
from aedrova.agents.ledger import RunLedger
from aedrova.desktop.controls import AppDialog
from aedrova.desktop.dialogs import button, label
from aedrova.desktop.projects import binding


def scope(saved):
    return {
        key: saved.get(key, default)
        for key, default in (("folder", ""), ("provider", "codex"), ("background_build", False))
    }


class ExecutionQueue(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        directory = Path.home() / "Library/Application Support/Aedrova/execution"
        if window.settings.format() == QSettings.Format.IniFormat:
            directory = Path(window.settings.fileName()).parent / "execution"
        self.ledger = RunLedger(directory)
        self.lease = self.ledger.lock()
        if self.lease:
            self.ledger.recover()
        self.active = None
        self.dialog = None
        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.tick)
        self.timer.start()
        self.last_user = self.identity()
        self.recovery_notified = set()
        window.account_dialog.session_closed.connect(self.pause)

    def pause(self):
        if self.last_user:
            self.ledger.pause_user(self.last_user)
        if self.dialog:
            self.dialog.details.clear()
            self.dialog.list.clear()
            self.dialog.close()

    def identity(self):
        user = self.window.current_user()
        return str(user.id) if user else ""

    def submit(self, task, *, teammate=None):
        if not self.lease:
            self.window.notify(
                "Another Aedrova instance owns the build queue. Close it and reopen this app."
            )
            return False
        user = self.identity()
        saved = scope(binding(self.window))
        if not user or not saved["folder"] or not saved["background_build"]:
            self.window.agent_setup_needed = True
            self.window.agent_activity(
                self.window.workspace_id, "Enable background builds in Project settings"
            )
            return False
        if teammate:
            from aedrova.teammates.model import validate

            validate(teammate["config"])
            if teammate["workspace_id"] != self.window.workspace_id or teammate["paused"]:
                self.window.notify("Teammate is unavailable. Refresh the workspace.")
                return False
            saved["ai_teammate"] = teammate
        try:
            run_id, fresh = self.ledger.enqueue(user, self.window.workspace_id, task, saved)
        except ValueError as exc:
            self.window.notify(str(exc))
            return False
        self.window.notify(
            "Build queued." if fresh else "This request is already in your build queue."
        )
        self.tick()
        return True

    def tick(self):
        if not self.lease:
            return
        user = self.identity()
        if self.last_user and self.last_user != user:
            self.ledger.pause_user(self.last_user)
        self.last_user = user
        if self.active:
            dialog = self.active[1]
            if dialog.pending or dialog.background_transition:
                return
            run_id, _ = self.active
            state = (
                "completed"
                if dialog.successful_build
                else ("cancelled" if dialog.collection_cancelled.is_set() else "failed")
            )
            self.ledger.update(run_id, state, project=dialog.project, baseline=dialog.baseline)
            self.active = None
            if state != "completed":
                self.ledger.pause_user(dialog.user)
                if user == dialog.user:
                    self.window.notify("Build stopped. Waiting requests are paused in Builds.")
        if not user or not self.window.connected or not self.window.connected.active:
            return
        current = getattr(self.window, "build_dialog", None)
        if current and (
            current.pending
            or current.background_transition
            or (current.review_dialog and current.review_dialog.job)
        ):
            return
        rows = self.ledger.rows(user, self.window.workspace_id)
        key = (user, self.window.workspace_id)
        if key not in self.recovery_notified:
            self.recovery_notified.add(key)
            if any(r["state"] in {"paused", "interrupted"} for r in rows):
                self.window.notify(
                    "Saved builds need your review. Open Builds to resume or inspect them."
                )
        queued = [row for row in reversed(rows) if row["state"] == "queued"]
        if not queued:
            return
        row = queued[0]
        try:
            authorize(self.window.account_dialog.snapshot, row["workspace"], user)
        except PermissionError:
            self.ledger.update(row["id"], "paused")
            return
        pinned = json.loads(row["settings"])
        teammate = pinned.pop("ai_teammate", None)
        if teammate:
            live = next(
                (
                    r
                    for r in self.window.account_dialog.snapshot.get("ai_teammates", [])
                    if r["id"] == teammate["id"] and r["workspace_id"] == row["workspace"]
                ),
                None,
            )
            if not live or live["paused"] or live["version"] != teammate["version"]:
                self.ledger.update(row["id"], "paused")
                self.window.notify("Teammate settings changed. Send a fresh assignment.")
                return
        if pinned != scope(binding(self.window)):
            self.ledger.update(row["id"], "paused")
            self.window.notify(
                "A queued build paused because project permissions changed. Review it in Builds."
            )
            return
        # Persist before any context request or provider process can start.
        self.ledger.update(row["id"], "running")
        from aedrova.desktop.builds import _start_background_build

        try:
            started = (
                _start_background_build(self.window, row["task"], teammate=teammate)
                if teammate
                else _start_background_build(self.window, row["task"])
            )
        except Exception:
            self.ledger.update(row["id"], "failed")
            self.window.notify("Could not start the queued build. Review it in Builds.")
            return
        if started:
            dialog = self.window.build_dialog
            dialog.run_id = row["id"]
            dialog.execution_queue = self
            self.active = (row["id"], dialog)
        else:
            self.ledger.update(row["id"], "failed")

    def show_history(self):
        if not self.identity():
            self.window.notify("Sign in to view your builds.")
            return
        if self.dialog:
            self.dialog.close()
        self.dialog = RunHistory(self)
        self.dialog.show()


class RunHistory(AppDialog):
    def __init__(self, queue):
        super().__init__(queue.window)
        self.queue = queue
        self.user, self.workspace = queue.identity(), queue.window.workspace_id
        self.setWindowTitle("Aedrova · Builds")
        self.resize(720, 600)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addWidget(label("Builds & usage", "heading"))
        layout.addWidget(
            label(
                "One build at a time on this Mac · up to 10 waiting requests. "
                "After a restart, requests pause for your review. Retrying starts a fresh build; "
                "inspect partial files first. Usage is local telemetry, not a bill.",
                "muted",
                wrap=True,
            )
        )
        shared = button("Shared build reviews…", role="outline")
        shared.clicked.connect(self.open_shared)
        layout.addWidget(shared)
        self.list = QListWidget()
        self.list.setProperty("accountList", True)
        layout.addWidget(self.list, 1)
        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setMaximumHeight(160)
        layout.addWidget(self.details)
        row = QHBoxLayout()
        self.retry = button("Retry / resume", role="primary")
        self.cancel = button("Cancel queued", role="outline")
        self.folder = button("Open saved files", role="outline")
        self.review = button("Review result", role="outline")
        for control in (self.retry, self.cancel, self.folder, self.review):
            row.addWidget(control)
        layout.addLayout(row)
        self.list.currentRowChanged.connect(self.select)
        self.retry.clicked.connect(self.resume)
        self.cancel.clicked.connect(self.cancel_selected)
        self.folder.clicked.connect(self.open_folder)
        self.review.clicked.connect(self.review_result)
        self.rows = []
        self.refresh()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)

    def open_shared(self):
        if self.valid():
            from aedrova.desktop.build_evidence import SharedBuilds

            self.shared_dialog = SharedBuilds(self.queue.window)
            self.shared_dialog.show()

    def valid(self):
        try:
            if (
                self.user != self.queue.identity()
                or self.workspace != self.queue.window.workspace_id
            ):
                raise PermissionError()
            authorize(self.queue.window.account_dialog.snapshot, self.workspace, self.user)
            return True
        except (PermissionError, AttributeError):
            self.details.clear()
            self.list.clear()
            self.close()
            return False

    def refresh(self):
        if not self.valid():
            return
        index = self.list.currentRow()
        rows = self.queue.ledger.rows(self.user, self.workspace)
        if rows != self.rows:
            self.rows = rows
            self.list.clear()
            self.list.addItems([f"{r['state'].capitalize()} · {r['task'][:100]}" for r in rows])
            self.list.setCurrentRow(max(0, min(index, len(rows) - 1)))
        self.select(self.list.currentRow())

    def selected(self):
        index = self.list.currentRow()
        return self.rows[index] if 0 <= index < len(self.rows) else None

    def select(self, _index):
        row = self.selected()
        self.retry.setEnabled(
            bool(row and row["state"] in {"paused", "failed", "interrupted", "cancelled"})
        )
        self.cancel.setEnabled(bool(row and row["state"] in {"queued", "paused"}))
        self.folder.setEnabled(bool(row and row["project"] and Path(row["project"]).is_dir()))
        self.review.setEnabled(bool(row and row["state"] == "completed" and row["project"]))
        if not row:
            self.details.clear()
            return
        usage = self.queue.ledger.usage(row["id"], self.user, self.workspace)
        lines = [row["task"], "", "Provider usage (missing values are unknown):"]
        for entry in usage:
            lines.append(
                f"{entry['phase']} · {entry['seconds']:.1f}s · "
                f"input {entry['input_tokens']} · output {entry['output_tokens']}"
            )
        self.details.setPlainText("\n".join(lines))

    def resume(self):
        if not self.valid():
            return
        row = self.selected()
        if not row or row["state"] not in {"paused", "failed", "interrupted", "cancelled"}:
            return
        saved = json.loads(row["settings"])
        teammate = saved.pop("ai_teammate", None)
        if teammate:
            live = next(
                (
                    r
                    for r in self.queue.window.account_dialog.snapshot.get("ai_teammates", [])
                    if r["id"] == teammate["id"] and r["workspace_id"] == self.workspace
                ),
                None,
            )
            if not live or live["paused"] or live["version"] != teammate["version"]:
                self.queue.window.notify("Teammate settings changed. Send a fresh assignment.")
                return
        if saved != scope(binding(self.queue.window)):
            self.queue.window.notify(
                "Project settings changed. Send a new mention using the current settings."
            )
            return
        if not self.queue.lease:
            return
        # Reuse the durable identity, never duplicate the original action automatically.
        if row["state"] == "paused":
            self.queue.ledger.update(row["id"], "queued")
        else:
            try:
                self.queue.ledger.enqueue(
                    self.user, self.workspace, row["task"], json.loads(row["settings"])
                )
            except ValueError as exc:
                self.queue.window.notify(str(exc))
                return
        self.queue.tick()
        self.refresh()

    def cancel_selected(self):
        if self.valid():
            row = self.selected()
            if row and row["state"] in {"queued", "paused"}:
                self.queue.ledger.update(row["id"], "cancelled")
                self.refresh()

    def review_result(self):
        if not self.valid():
            return
        row = self.selected()
        if not row or row["state"] != "completed":
            return
        window = self.queue.window
        current = getattr(window, "build_dialog", None)
        if self.queue.active or (
            current and (current.pending or (current.review_dialog and current.review_dialog.job))
        ):
            window.notify(
                "Wait for the current build or delivery action before opening a saved review."
            )
            return
        saved = json.loads(row["settings"])
        teammate = saved.pop("ai_teammate", None)
        if teammate:
            live = next(
                (
                    r
                    for r in window.account_dialog.snapshot.get("ai_teammates", [])
                    if r["id"] == teammate["id"] and r["workspace_id"] == self.workspace
                ),
                None,
            )
            if not live or live["paused"] or live["version"] != teammate["version"]:
                window.notify("Teammate settings changed. Send a fresh assignment.")
                return
            if teammate["config"]["role"] != "engineering":
                window.notify(
                    "This teammate completed an analysis, with no code changes to review."
                )
                return
        if saved != scope(binding(window)):
            window.notify("Reconnect this build's original project settings before reviewing it.")
            return
        allowed = authorize(window.account_dialog.snapshot, self.workspace, self.user)
        channels = set(json.loads(row["channels"]))
        if not channels <= allowed:
            window.notify("Source access changed. Start a new build with your current access.")
            return
        self.queue.ledger.pause_user(self.user)
        if current:
            current.invalidate()
        from aedrova.desktop.builds import BuildDialog

        studio = BuildDialog(window, row["task"])
        studio.teammate = teammate
        window.build_dialog = studio
        studio.project = Path(row["project"])
        studio.baseline = row["baseline"]
        studio.context = SimpleNamespace(channel_ids=channels)
        try:
            studio.command_results = json.loads(
                (studio.project.parent / "observed-checks.json").read_text()
            )
        except (OSError, ValueError):
            studio.command_results = []
        studio.successful_build = True
        studio.open_review()

    def open_folder(self):
        if self.valid():
            row = self.selected()
            if row and row["project"] and Path(row["project"]).is_dir():
                QDesktopServices.openUrl(QUrl.fromLocalFile(row["project"]))


def execution_queue(window):
    queue = getattr(window, "execution_queue", None)
    if queue is None:
        queue = ExecutionQueue(window)
        window.execution_queue = queue
    return queue
