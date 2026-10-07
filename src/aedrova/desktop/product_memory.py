"""Source-backed workspace knowledge with explicit review and asynchronous writes."""

from uuid import uuid4

from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from aedrova.desktop.controls import AppDialog, ChoiceBox
from aedrova.desktop.design_system import FlowActions, MasterDetail
from aedrova.desktop.dialogs import button, label
from aedrova.memory.model import KINDS, STATES, snapshot_record


class ProductMemory(AppDialog):
    def __init__(self, window, source=None):
        super().__init__(window)
        self.window = window
        self.account = window.account_dialog
        self.workspace = window.workspace_id
        self.owner = str(window.current_user().id)
        self.channel = window.channel_id
        self.rows = []
        self.entry = None
        self.sources = []
        self.resolved = []
        self.replacement = None
        self.setup_required = False
        self.closed = False
        self.busy = False
        self.setWindowTitle("Aedrova · Product memory")
        self.resize(920, 800)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)
        layout.addWidget(label("What your team knows.", "heading"))
        layout.addWidget(
            label(
                "Source-backed goals, requirements and decisions. Proposals stay proposals until "
                "a teammate explicitly approves them. Private sources keep their access rules.",
                "muted",
                wrap=True,
            )
        )
        header = QHBoxLayout()
        self.query = QLineEdit()
        self.query.setPlaceholderText("Search product memory")
        self.query.setAccessibleName("Search product memory")
        header.addWidget(self.query, 1)
        search = button("Search", role="outline")
        search.clicked.connect(self.refresh)
        self.query.returnPressed.connect(self.refresh)
        header.addWidget(search)
        new = button("New proposal", role="outline")
        new.clicked.connect(self.new_entry)
        header.addWidget(new)
        layout.addLayout(header)
        self.status = label("Loading…", "muted", wrap=True)
        layout.addWidget(self.status)
        self.list = QListWidget()
        self.list.setProperty("accountList", True)
        self.list.setAccessibleName("Product memory entries")
        self.list.setMaximumHeight(110)
        self.list.currentRowChanged.connect(self.select_entry)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        form = QWidget()
        self.form = form
        editor = QVBoxLayout(form)
        editor.setContentsMargins(0, 8, 0, 8)
        editor.setSpacing(12)
        scroll.setWidget(form)
        self.master_detail = MasterDetail(self.list, scroll)
        layout.addWidget(self.master_detail, 1)
        selectors = QHBoxLayout()
        self.kind = ChoiceBox()
        self.kind.addItems(list(KINDS))
        self.kind.setAccessibleName("Memory category")
        self.state = ChoiceBox()
        self.state.addItems([s for s in STATES if s != "superseded"])
        self.state.setAccessibleName("Memory review state")
        selectors.addWidget(self.kind)
        selectors.addWidget(self.state)
        editor.addLayout(selectors)
        self.title = QLineEdit()
        self.title.setPlaceholderText("A clear, short title")
        self.title.setMaxLength(160)
        self.title.setAccessibleName("Memory title")
        editor.addWidget(self.title)
        self.body = QPlainTextEdit()
        self.body.setPlaceholderText(
            "Record the requirement, constraint, decision or open question."
        )
        self.body.setAccessibleName("Memory details")
        self.body.setMinimumHeight(120)
        editor.addWidget(self.body)
        sources = QHBoxLayout()
        self.source_query = QLineEdit()
        self.source_query.setPlaceholderText("Find a chat source across permitted channels")
        self.source_query.setAccessibleName("Find memory source")
        sources.addWidget(self.source_query, 1)
        find = button("Find sources", role="outline")
        find.clicked.connect(self.find_sources)
        self.source_query.returnPressed.connect(self.find_sources)
        sources.addWidget(find)
        editor.addLayout(sources)
        self.source_choice = ChoiceBox()
        self.source_choice.setAccessibleName("Select source message")
        self.source_choice.hide()
        self.source_choice.activated.connect(self.choose_source)
        editor.addWidget(self.source_choice)
        editor.addWidget(label("Evidence · review before approving", "section"))
        self.evidence = QPlainTextEdit()
        self.evidence.setReadOnly(True)
        self.evidence.setAccessibleName("Memory source citations and freshness")
        self.evidence.setMinimumHeight(110)
        editor.addWidget(self.evidence)
        source_actions = FlowActions()
        self.review = button("Review current sources", role="outline")
        self.review.clicked.connect(self.review_sources)
        self.open_source = button("Open citation", role="outline")
        self.open_source.clicked.connect(self.open_citation)
        source_actions.addWidget(self.review)
        source_actions.addWidget(self.open_source)
        editor.addLayout(source_actions)
        self.conflict = ChoiceBox()
        self.conflict.setAccessibleName("Conflicting memory entry")
        editor.addWidget(self.conflict)
        self.approval = QCheckBox("I reviewed the evidence and approve this requirement.")
        editor.addWidget(self.approval)
        self.history = QPlainTextEdit()
        self.history.setReadOnly(True)
        self.history.setAccessibleName("Memory revision history")
        self.history.setMinimumHeight(100)
        editor.addWidget(self.history)
        self.history.hide()
        actions = FlowActions()
        self.replace_button = button("Supersede with new entry", role="outline")
        self.replace_button.clicked.connect(self.supersede)
        history = button("Revision history", role="outline")
        history.clicked.connect(self.load_history)
        self.save = button("Save entry", role="primary")
        self.save.clicked.connect(self.save_entry)
        done = button("Done", role="outline")
        done.clicked.connect(self.accept)
        for control in (self.replace_button, history, self.save, done):
            actions.addWidget(control)
        layout.addLayout(actions)
        self.account.session_closed.connect(self.reject)
        self.account.snapshot_loaded.connect(self.check_access)
        self.finished.connect(self.cleanup)
        self.refresh(seed=source)

    def scoped(self):
        user = self.window.current_user()
        return (
            not self.closed
            and user is not None
            and str(user.id) == self.owner
            and self.window.workspace_id == self.workspace
        )

    def check_access(self, snapshot=None):
        if not self.scoped():
            self.reject()
            return
        from aedrova.agents.context import authorize

        try:
            channels = authorize(snapshot or self.account.snapshot, self.workspace, self.owner)
            if any(row["channel_id"] not in channels for row in self.rows) or (
                self.sources and self.channel not in channels
            ):
                self.reject()
        except PermissionError:
            self.reject()

    def task(self, name, action, callback):
        if not self.scoped() or self.busy:
            return False
        self.busy = True
        self.list.setEnabled(False)
        self.form.setEnabled(False)
        self.save.setEnabled(False)
        self.status.setText("Checking access and current evidence…")

        def completed(result):
            if not self.scoped():
                self.reject()
                return
            self.busy = False
            self.list.setEnabled(True)
            self.form.setEnabled(True)
            self.save.setEnabled(True)
            if isinstance(result, dict) and "error" in result:
                self.rows = []
                self.list.clear()
                self.new_entry()
                if result.get("conflict"):
                    self.status.setText(
                        "This entry or its evidence changed. Refresh and review "
                        "current sources before saving."
                    )
                    return
                self.status.setText(
                    "Could not load or save memory. Refresh and retry. "
                    "If setup is pending, run the Product Memory migration."
                )
                return
            callback(result)

        def operation():
            try:
                return action()
            except Exception as error:
                # Queue failures otherwise bypass the completion callback. Always restore
                # controls and clear cached evidence without exposing transport secrets.
                return {
                    "error": "Memory request failed",
                    "conflict": getattr(error, "code", None) == "PT409",
                }

        if not self.window.connected.enqueue(("memory", id(self), name), operation, completed):
            self.busy = False
            self.list.setEnabled(True)
            self.form.setEnabled(True)
            self.save.setEnabled(True)
            self.status.setText("Connection busy. Try again in a moment.")
            return False
        return True

    def refresh(self, *, seed=None):
        query = self.query.text()

        def loaded(payload):
            from aedrova.agents.context import authorize

            try:
                snapshot_record(
                    payload,
                    self.workspace,
                    authorize(self.account.snapshot, self.workspace, self.owner),
                )
            except (PermissionError, ValueError):
                self.reject()
                return
            self.setup_required = payload.get("setup_required", False)
            self.rows = payload["items"]
            self.list.clear()
            for row in self.rows:
                self.list.addItem(
                    f"{row['title']} · {row['kind']} · "
                    f"{row['state'] if row['fresh'] else 'source changed'} · v{row['version']}"
                )
            self.status.setText(
                "Product memory needs the Supabase migration before it can be used."
                if payload.get("setup_required")
                else f"{len(self.rows)} of {payload['total']} accessible entries. "
                + (
                    "Narrow your search to see omitted entries."
                    if payload.get("truncated")
                    else "No AI calls are made in this view."
                )
            )
            self.new_entry()
            self.save.setEnabled(not payload.get("setup_required"))
            if seed:
                self.use_source(seed)
            elif self.rows:
                self.list.setCurrentRow(0)

        self.task("list", lambda: self.account.service.memory_list(self.workspace, query), loaded)

    def new_entry(self):
        if self.busy:
            return
        self.list.blockSignals(True)
        self.list.setCurrentRow(-1)
        self.list.blockSignals(False)
        self.entry = None
        self.replacement = None
        self.sources = []
        self.resolved = []
        self.channel = self.window.channel_id
        self.title.clear()
        self.body.clear()
        self.evidence.clear()
        self.history.clear()
        self.history.hide()
        self.approval.setChecked(False)
        self.state.setCurrentText("proposal")
        self.conflict.clear()
        self.conflict.addItem("No unresolved conflict", None)
        self.source_choice.clear()
        self.source_choice.hide()
        self.replace_button.setEnabled(False)
        self.save.setEnabled(not self.setup_required)
        self.title.setFocus()

    def conflicts(self):
        self.conflict.clear()
        self.conflict.addItem("No unresolved conflict", None)
        for row in self.rows:
            if row["channel_id"] == self.channel and row["id"] != (self.entry or {}).get("id"):
                self.conflict.addItem(row["title"], row["id"])

    def select_entry(self, index):
        if self.busy or not 0 <= index < len(self.rows):
            return
        row = self.rows[index]
        self.entry = row
        self.replacement = None
        self.channel = row["channel_id"]
        self.sources = row["sources"]
        self.resolved = row["resolved_sources"]
        self.title.setText(row["title"])
        self.body.setPlainText(row["body"])
        self.kind.setCurrentText(row["kind"])
        self.state.setCurrentText(row["state"] if row["state"] != "superseded" else "proposal")
        self.approval.setChecked(False)
        self.conflicts()
        self.conflict.setCurrentIndex(max(0, self.conflict.findData(row.get("conflict_id"))))
        self.show_evidence()
        self.history.clear()
        self.replace_button.setEnabled(row["state"] != "superseded")
        self.save.setEnabled(row["state"] != "superseded")
        self.status.setText(
            "Superseded entry · revision history remains available."
            if row["state"] == "superseded"
            else "Review changes explicitly before approving. Source changes require review."
        )

    def find_sources(self):
        query = self.source_query.text()
        channel = self.channel

        def loaded(rows):
            self.source_choice.clear()
            for row in rows:
                self.source_choice.addItem(row["body"][:100], row)
            self.source_choice.setVisible(bool(rows))
            self.status.setText(
                f"{len(rows)} chat sources found. Choose one to attach as evidence."
            )

        self.task(
            "sources",
            lambda: (
                self.account.service.search_context(self.workspace, query)
                if query.strip()
                else self.account.service.recent_context(channel)
            ),
            loaded,
        )

    def choose_source(self, index):
        row = self.source_choice.itemData(index)
        if row:
            if self.entry and row["channel_id"] != self.channel:
                self.status.setText(
                    "An existing entry keeps its original channel access. "
                    "Create a new proposal for another channel."
                )
                return
            self.use_source({"kind": "message", "id": row["id"]})

    def use_source(self, source):
        def loaded(resolved):
            if not resolved:
                self.status.setText("Source unavailable or no longer authorized.")
                return
            self.channel = resolved["channel_id"]
            self.sources = [{k: resolved[k] for k in ("kind", "id", "fingerprint")}]
            self.resolved = [resolved]
            self.approval.setChecked(False)
            self.conflicts()
            self.show_evidence()

        self.task(
            "source",
            lambda: self.account.service.memory_source(source["kind"], source["id"]),
            loaded,
        )

    def review_sources(self):
        if not self.sources:
            self.status.setText("Find and select a source first.")
            return
        sources = list(self.sources)

        def loaded(rows):
            if any(not row or row["channel_id"] != self.channel for row in rows):
                self.sources = []
                self.resolved = []
                self.show_evidence()
                self.status.setText("Evidence unavailable. This entry cannot be approved.")
                return
            self.resolved = rows
            self.sources = [{k: row[k] for k in ("kind", "id", "fingerprint")} for row in rows]
            self.approval.setChecked(False)
            self.show_evidence()
            self.status.setText("Current evidence loaded. Check the requirement before approving.")

        self.task(
            "review",
            lambda: [self.account.service.memory_source(s["kind"], s["id"]) for s in sources],
            loaded,
        )

    def show_evidence(self):
        self.evidence.setPlainText(
            "\n\n".join(
                f"[{row['citation']}]\n{row['body']}\n"
                + (
                    "Current"
                    if any(
                        s["id"] == row["id"] and s["fingerprint"] == row["fingerprint"]
                        for s in self.sources
                    )
                    else "Changed · review current sources"
                )
                for row in self.resolved
            )
        )

    def supersede(self):
        if not self.entry or self.busy:
            return
        original = dict(self.entry)
        self.entry = None
        self.replacement = original
        self.state.setCurrentText("approved")
        self.approval.setChecked(False)
        self.conflicts()
        self.status.setText(
            "Editing a new replacement. Approval retires the prior version "
            "as superseded, with its history intact."
        )

    def save_entry(self):
        if self.busy:
            return
        state = self.state.currentText()
        if not self.title.text().strip() or not self.body.toPlainText().strip() or not self.sources:
            self.status.setText("Add a title, details and an accessible source first.")
            return
        if len(self.body.toPlainText()) > 8000:
            self.status.setText("Keep the entry within 8,000 characters.")
            return
        if state == "approved" and not self.approval.isChecked():
            self.status.setText("Review the evidence and check the approval box first.")
            return
        conflict = self.conflict.currentData()
        if state == "approved" and self.kind.currentText() == "question":
            self.status.setText("Resolve the question before marking it as approved.")
            return
        if state == "conflict" and not conflict:
            self.status.setText("Choose the conflicting entry first.")
            return
        if conflict and state == "approved":
            self.status.setText("Resolve the conflicting entry before approving.")
            return
        parameters = {
            "p_id": (self.entry or {}).get("id") or str(uuid4()),
            "p_workspace": self.workspace,
            "p_channel": self.channel,
            "p_version": (self.entry or {}).get("version", 0),
            "p_kind": self.kind.currentText(),
            "p_title": self.title.text().strip(),
            "p_body": self.body.toPlainText().strip(),
            "p_state": state,
            "p_sources": self.sources,
            "p_conflict": conflict,
            "p_supersedes": (self.replacement or {}).get("id"),
            "p_supersedes_version": (self.replacement or {}).get("version"),
        }

        def saved(_):
            studio = getattr(self.window, "build_dialog", None)
            if studio:
                studio.invalidate_plan()
                studio.verify_memory(force=True)
            self.refresh()

        self.task("save", lambda: self.account.service.save_memory(parameters), saved)

    def load_history(self):
        if not self.entry:
            return
        identifier = self.entry["id"]

        def loaded(rows):
            self.history.show()
            self.history.setPlainText(
                "\n\n".join(
                    f"v{row['version']} · {row['changed_at']}\n"
                    f"{row['record']['state']} · {row['record']['title']}\n{row['record']['body']}"
                    for row in rows
                )
            )
            self.status.setText("Latest 100 revisions. Access is checked for each source.")

        self.task("history", lambda: self.account.service.memory_history(identifier), loaded)

    def open_citation(self):
        if not self.resolved:
            return
        row = self.resolved[0]
        if row["kind"] == "message":
            from aedrova.desktop.collaboration import message_link

            self.window.collaboration.open_link(
                message_link(self.workspace, row["channel_id"], row["id"])
            )
        elif row["kind"] == "attachment":
            self.window.collaboration.open_attachment(row["id"], row.get("filename", "Source file"))
        else:

            def opened(current):
                if not current:
                    self.reject()
                    self.window.notify("Meeting source is no longer available for AI reuse.")
                    return
                self.evidence.setPlainText(
                    f"[{current['citation']}]\nMeeting {current['meeting_id']} · "
                    f"{current['offset_ms']} ms\n\n{current['body']}"
                )
                self.status.setText(
                    "Current consented meeting source. Review before relying on it."
                )

            self.task(
                "open-meeting",
                lambda: self.account.service.memory_source("meeting", row["id"]),
                opened,
            )

    def cleanup(self, *_):
        if self.closed:
            return
        self.closed = True
        self.rows = []
        self.sources = []
        self.resolved = []
        self.list.clear()
        self.evidence.clear()
        self.history.clear()
        self.body.clear()
        self.title.clear()
        self.account.snapshot_loaded.disconnect(self.check_access)
        self.account.session_closed.disconnect(self.reject)


def open_memory(window, source=None):
    if not window.current_user() or not getattr(window.connected, "active", False):
        window.notify("Sign in and open a shared workspace to use product memory.")
        return
    existing = getattr(window, "memory_dialog", None)
    if existing and not existing.closed:
        existing.raise_()
        if source:
            existing.use_source(source)
        return
    window.memory_dialog = ProductMemory(window, source)
    window.memory_dialog.show()
