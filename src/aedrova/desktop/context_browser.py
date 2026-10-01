"""Private, provider-free evidence search and explicit decision recording."""

import threading

from PySide6.QtCore import Qt, QThreadPool, Slot
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QVBoxLayout,
)

from aedrova.agents.context import authorize
from aedrova.agents.retrieval import ContextIndex
from aedrova.desktop.dialogs import button, label


class ContextBrowser(QDialog):
    def __init__(self, studio):
        super().__init__(studio)
        self.studio = studio
        self.index = None
        self.generation = 0
        self.cancelled = threading.Event()
        self.jobs = {}
        self.closed = False
        self.busy = False
        self.setWindowTitle("Aedrova · Workspace context")
        self.resize(820, 700)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.addWidget(label("Your team's sources", "heading"))
        layout.addWidget(
            label(
                "Search permitted chats and attachments. Confirm only agreed requirements. "
                "Your confirmation is visible to members with access to the source. "
                "This view does not send anything to an AI provider.",
                "muted",
                wrap=True,
            )
        )
        self.query = QLineEdit()
        self.query.setPlaceholderText("Search workspace evidence")
        self.query.setAccessibleName("Search workspace evidence")
        layout.addWidget(self.query)
        self.status = label("Loading current evidence…", "muted", wrap=True)
        layout.addWidget(self.status)
        self.results = QListWidget()
        self.results.setProperty("accountList", True)
        self.results.setWordWrap(True)
        self.results.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.results.setAccessibleName("Context sources")
        layout.addWidget(self.results)
        self.detail = QPlainTextEdit()
        self.detail.setReadOnly(True)
        self.detail.setAccessibleName("Source citation and content")
        layout.addWidget(self.detail, 1)
        actions = QHBoxLayout()
        self.refresh_button = button("Refresh", role="outline")
        self.confirm = button("Confirm decision", role="primary")
        self.retire = button("Retire decision", role="outline")
        self.done = button("Done", role="outline")
        for control in (self.refresh_button, self.confirm, self.retire, self.done):
            actions.addWidget(control)
        layout.addLayout(actions)
        self.query.textChanged.connect(self.search)
        self.results.currentRowChanged.connect(self.selected)
        self.refresh_button.clicked.connect(self.refresh)
        self.confirm.clicked.connect(lambda: self.record(True))
        self.retire.clicked.connect(lambda: self.record(False))
        self.done.clicked.connect(self.close)
        studio.account.session_closed.connect(self.revoke)
        self.selected()
        self.refresh()

    def clear_index(self):
        self.results.clear()
        self.detail.clear()
        if self.index:
            self.index.close()
            self.index = None
        self.sources = []

    def refresh(self):
        if self.closed or self.busy:
            return
        self.clear_index()
        self.busy = True
        self.refresh_button.setEnabled(False)
        self.generation += 1
        generation = self.generation
        self.status.setText("Checking access and reading current workspace sources…")

        def connect():
            return {"service": self.studio.account.service.fork_for_context()}

        def connected(result):
            service = result.get("service")
            if self.closed or generation != self.generation:
                if service:
                    service.close_context()
                return
            if "error" in result:
                self.finish_error(result["error"])
                return
            from aedrova.desktop.builds import ContextJob

            job = ContextJob(service, self.studio.workspace, self.cancelled, generation)
            self.jobs[generation] = job
            job.signals.finished.connect(self.loaded)
            job.signals.progress.connect(self.progress)
            QThreadPool.globalInstance().start(job)

        if not self.studio.window.connected.enqueue(
            ("context-browser", id(self), generation), connect, connected
        ):
            self.finish_error("Connection busy. Refresh to retry.")

    @Slot(str)
    def progress(self, text):
        if not self.closed:
            self.status.setText(text)

    def finish_error(self, message):
        self.busy = False
        self.refresh_button.setEnabled(True)
        self.status.setText(message)

    @Slot(object)
    def loaded(self, payload):
        self.jobs.pop(payload["generation"], None)
        if self.closed or payload["generation"] != self.generation:
            return
        result = payload["result"]
        if "error" in result:
            self.finish_error(result["error"])
            return
        context = result["context"]
        try:
            allowed = authorize(
                self.studio.account.snapshot, self.studio.workspace, self.studio.user
            )
            if not context.channel_ids <= allowed:
                raise PermissionError("Access changed. Reopen context to retry.")
            self.index = ContextIndex(context)
        except (PermissionError, ValueError) as exc:
            self.finish_error(str(exc))
            return
        self.channels = context.channel_ids
        self.busy = False
        self.refresh_button.setEnabled(True)
        self.search()

    def search(self):
        self.results.clear()
        self.sources = self.index.search(self.query.text(), 200) if self.index else []
        for source in self.sources:
            self.results.addItem(
                f"#{source.channel} · {source.decision} · {source.body[:90].replace(chr(10), ' ')}"
            )
        self.status.setText(
            f"{len(self.sources)} shown (up to 200) · refresh before relying on old evidence."
        )
        if self.sources:
            self.results.setCurrentRow(0)

    def selected(self, *_):
        row = self.results.currentRow()
        source = (
            self.sources[row] if hasattr(self, "sources") and 0 <= row < len(self.sources) else None
        )
        self.confirm.setEnabled(bool(source and not source.attachment and not self.busy))
        self.retire.setEnabled(
            bool(source and source.decision in {"confirmed", "stale"} and not self.busy)
        )
        if source:
            names = {
                r["user_id"]: r["display_name"]
                for r in self.studio.account.snapshot.get("directory", [])
            }
            recorder = (
                "You"
                if source.confirmed_by == self.studio.user
                else names.get(source.confirmed_by, source.confirmed_by or "—")
            )
            self.detail.setToolTip(f"Source fingerprint: {source.fingerprint}")
            self.detail.setPlainText(
                f"[{source.citation}]\n#{source.channel} · {source.created_at}\n"
                f"Status: {source.decision}\nRecorded by: {recorder}\n"
                f"Thread: {source.parent_id or source.message_id}\n\n{source.body}"
            )
        else:
            self.detail.clear()

    def record(self, confirmed):
        row = self.results.currentRow()
        if self.closed or self.busy or row < 0:
            return
        source = self.sources[row]
        if source.attachment:
            return
        self.busy = True
        self.selected()
        self.refresh_button.setEnabled(False)
        self.status.setText("Saving decision…")

        def action():
            self.studio.account.service.set_context_decision(
                source.message_id, source.body, confirmed
            )
            return {"saved": True}

        def saved(result):
            if self.closed:
                return
            self.busy = False
            self.refresh_button.setEnabled(True)
            if "error" in result:
                self.clear_index()
                self.status.setText(result["error"] + " Refresh to retry.")
                return
            self.studio.invalidate_plan()
            self.refresh()

        if not self.studio.window.connected.enqueue(("decision", source.message_id), action, saved):
            self.finish_error("Connection busy. Refresh to retry.")

    def check_access(self, snapshot):
        try:
            allowed = authorize(snapshot, self.studio.workspace, self.studio.user)
            if not getattr(self, "channels", frozenset()) <= allowed:
                raise PermissionError()
        except PermissionError:
            self.revoke()

    def revoke(self):
        self.close()

    def closeEvent(self, event):  # noqa: N802
        self.closed = True
        self.cancelled.set()
        self.generation += 1
        self.clear_index()
        self.query.clear()
        self.detail.setToolTip("")
        self.status.clear()
        event.accept()

    def reject(self):
        self.close()
