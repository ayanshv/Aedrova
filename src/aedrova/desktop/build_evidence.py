"""Native source-scoped build evidence sharing and teammate review."""

import copy
import time
from uuid import uuid4

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QVBoxLayout,
)

from aedrova.agents.context import authorize
from aedrova.delivery.evidence import manifest, validate
from aedrova.desktop.controls import AppDialog, ChoiceBox
from aedrova.desktop.dialogs import button, label


class SharedBuilds(AppDialog):
    def __init__(self, window, *, studio=None, review=None):
        super().__init__(window)
        self.window, self.studio, self.review = window, studio, review
        self.user = str(window.current_user().id)
        self.workspace = window.workspace_id
        self.channel = window.channel_id
        self.rows, self.value, self.selected_record = [], None, None
        self.review_actions = {}
        self.busy = False
        self.closed = False
        self.last_refresh = 0.0
        previous = getattr(window, "shared_build_dialog", None)
        if previous:
            previous.reject()
        window.shared_build_dialog = self
        self.record_id = getattr(studio, "evidence_id", None) or str(uuid4())
        self.record_version = getattr(studio, "evidence_version", 0)
        self.setWindowTitle("Aedrova · Build evidence")
        self.resize(1000, 840)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(12)
        layout.addWidget(label("Build evidence.", "heading"))
        layout.addWidget(
            label(
                "Actual file diffs and observed command results. Shared records are visible only "
                "to teammates who can access every source channel. "
                "Review never applies or publishes code.",
                "muted",
                wrap=True,
            )
        )
        self.status = label("", "muted", wrap=True)
        layout.addWidget(self.status)
        self.records = QListWidget()
        self.records.setAccessibleName("Shared build reviews")
        self.records.setProperty("accountList", True)
        self.records.setMaximumHeight(76)
        layout.addWidget(self.records)
        row = QHBoxLayout()
        self.requirements = QListWidget()
        self.requirements.setAccessibleName("Build requirements")
        self.requirements.setProperty("accountList", True)
        self.requirements.setMaximumWidth(300)
        self.details = QPlainTextEdit()
        self.details.setMinimumHeight(180)
        self.details.setReadOnly(True)
        self.details.setAccessibleName("Build evidence details")
        row.addWidget(self.requirements)
        row.addWidget(self.details, 1)
        layout.addLayout(row, 1)
        self.criteria = QPlainTextEdit()
        self.criteria.setPlaceholderText("Acceptance criteria · one concise condition per line")
        self.criteria.setAccessibleName("Build acceptance criteria")
        self.criteria.setMaximumHeight(80)
        layout.addWidget(self.criteria)
        self.assessment = ChoiceBox()
        for title, value in (
            ("Not assessed", "not_assessed"),
            ("Needs work", "needs_work"),
            ("Verified by reviewer", "reviewer_verified"),
        ):
            self.assessment.addItem(title, value)
        self.assessment.setAccessibleName("Requirement assessment")
        layout.addWidget(self.assessment)
        links = QHBoxLayout()
        self.files, self.checks = QListWidget(), QListWidget()
        self.files.setAccessibleName("Link changed files to requirement")
        self.checks.setAccessibleName("Link observed checks to requirement")
        for widget in (self.files, self.checks):
            widget.setProperty("accountList", True)
            widget.setMaximumHeight(130)
            links.addWidget(widget)
        layout.addLayout(links)
        self.link = button("Save requirement links", role="outline")
        self.link.clicked.connect(self.link_requirement)
        layout.addWidget(self.link)
        self.note = QPlainTextEdit()
        self.note.setPlaceholderText("A concise review note")
        self.note.setAccessibleName("Build review note")
        self.note.setMaximumHeight(70)
        layout.addWidget(self.note)
        actions = QHBoxLayout()
        self.refresh_button = button("Refresh", role="outline")
        self.share = button("Share exact evidence", role="primary")
        self.decision = ChoiceBox()
        for title, value in (
            ("Comment", "comment"),
            ("Request changes", "changes_requested"),
            ("Approve reviewed evidence", "approved"),
        ):
            self.decision.addItem(title, value)
        self.submit = button("Send review", role="outline")
        done = button("Done", role="outline")
        for widget in (self.refresh_button, self.share, self.decision, self.submit, done):
            actions.addWidget(widget)
        layout.addLayout(actions)
        self.refresh_button.clicked.connect(self.refresh)
        self.share.clicked.connect(self.share_evidence)
        self.submit.clicked.connect(self.send_review)
        done.clicked.connect(self.reject)
        self.records.currentRowChanged.connect(self.select_record)
        self.requirements.currentRowChanged.connect(self.select_requirement)
        self.files.currentRowChanged.connect(self.inspect_file)
        self.checks.currentRowChanged.connect(self.inspect_check)
        window.account_dialog.session_closed.connect(self.reject)
        if studio:
            self.value = manifest(
                studio.context,
                studio.request.toPlainText(),
                studio.provider.currentData(),
                review,
                getattr(studio, "command_results", []),
            )
            self.status.setText(
                "Review this exact snapshot before sharing. No code is uploaded to GitHub."
            )
            self.records.hide()
            self.fill()
        else:
            self.refresh()

    def valid(self):
        try:
            if (
                self.closed
                or self.user != str(self.window.current_user().id)
                or self.workspace != self.window.workspace_id
                or (self.studio and self.studio.invalidated)
            ):
                raise PermissionError()
            allowed = authorize(self.window.account_dialog.snapshot, self.workspace, self.user)
            channels = self.studio.context.channel_ids if self.studio else set()
            if self.selected_record:
                channels = set(self.selected_record["source_channels"])
            if not set(channels) <= allowed:
                raise PermissionError()
            return True
        except (AttributeError, PermissionError):
            self.reject()
            return False

    def run(self, name, action, completed):
        if self.busy or not self.valid():
            return
        self.busy = True
        for widget in (self.share, self.submit, self.refresh_button):
            widget.setEnabled(False)

        def operation():
            try:
                return {"value": action(self.window.account_dialog.service)}
            except Exception as error:
                return {"error": getattr(error, "code", "")}

        def finish(result):
            self.busy = False
            if not self.valid():
                return
            self.fill_controls()
            if "error" in result:
                self.value = self.selected_record = None
                self.rows = []
                for widget in (self.records, self.requirements, self.files, self.checks):
                    widget.clear()
                self.criteria.clear()
                self.note.clear()
                self.details.clear()
                self.fill_controls()
                self.status.setText(
                    "Evidence changed or access is unavailable. "
                    "Refresh and review before retrying. "
                    "If setup is pending, run the Build reviews SQL migration."
                )
                return
            completed(result["value"])

        if not self.window.connected.enqueue(("build-evidence", id(self), name), operation, finish):
            self.busy = False
            self.fill_controls()
            self.status.setText("Connection busy. Try again shortly.")

    def check_access(self, snapshot):
        try:
            allowed = authorize(snapshot, self.workspace, self.user)
            channels = set().union(*(set(r["source_channels"]) for r in self.rows))
            if self.studio:
                channels |= set(self.studio.context.channel_ids)
            if not channels <= allowed or not self.valid():
                self.reject()
                return
            if not self.studio and not self.busy and time.monotonic() - self.last_refresh > 15:
                self.refresh()
        except PermissionError:
            self.reject()

    def refresh(self):
        self.last_refresh = time.monotonic()
        if self.studio:
            self.status.setText("Reopen from Refresh review to capture current local files.")
            return

        def loaded(payload):
            self.rows = payload["items"]
            self.records.clear()
            self.records.addItems([r["evidence"]["task"][:120] for r in self.rows])
            self.status.setText(
                "Run the Build reviews SQL migration to enable sharing."
                if payload["setup_required"]
                else f"{len(self.rows)} accessible reviews."
            )
            if self.rows:
                self.records.setCurrentRow(0)
            else:
                self.value = None
                self.fill()

        self.run("list", lambda service: service.build_reviews(self.workspace), loaded)

    def select_record(self, index):
        if self.studio or not 0 <= index < len(self.rows):
            return
        self.selected_record = self.rows[index]
        self.value = copy.deepcopy(self.selected_record["evidence"])
        self.fill()
        for receipt in self.selected_record.get("receipts", []):
            self.details.appendPlainText(
                "\nDelivery receipt · " + receipt["kind"] + "\n" + receipt["reference"]
            )
        if self.requirements.count():
            self.requirements.setCurrentRow(0)
        identifier = self.selected_record["id"]

        def history(rows):
            if self.selected_record and self.selected_record["id"] == identifier:
                self.details.appendPlainText(
                    "\nReviews (each applies to its stated version):\n"
                    + "\n".join(
                        f"v{r['build_version']} · {r['decision']} · {r['created_at']}\n{r['note']}"
                        for r in rows
                    )
                )

        self.run("decisions", lambda service: service.build_review_decisions(identifier), history)

    def fill_controls(self):
        editing = bool(self.studio and self.value and not self.busy)
        for widget in (self.assessment, self.criteria, self.link):
            widget.setEnabled(editing)
        self.share.setEnabled(editing)
        self.share.setVisible(bool(self.studio))
        self.assessment.setVisible(bool(self.studio))
        self.link.setVisible(bool(self.studio))
        self.submit.setEnabled(bool(self.selected_record and not self.busy))
        self.note.setVisible(not self.studio)
        self.decision.setVisible(not self.studio)
        self.submit.setVisible(not self.studio)
        self.refresh_button.setEnabled(not self.busy)

    def fill(self):
        self.requirements.clear()
        self.files.clear()
        self.checks.clear()
        self.fill_controls()
        if not self.value:
            self.details.clear()
            return
        value = self.value
        self.requirements.addItems(
            [f"{r['title']} · {r['assessment'].replace('_', ' ')}" for r in value["requirements"]]
        )
        self.criteria.setPlainText("\n".join(value["acceptance_criteria"]))
        for f in value["files"]:
            item = QListWidgetItem(f["path"])
            item.setData(Qt.ItemDataRole.UserRole, f["path"])
            item.setCheckState(Qt.CheckState.Unchecked)
            self.files.addItem(item)
        for c in value["checks"]:
            item = QListWidgetItem(c["state"].upper() + " · " + c["command"][:100])
            item.setData(Qt.ItemDataRole.UserRole, c["id"])
            item.setCheckState(Qt.CheckState.Unchecked)
            self.checks.addItem(item)
        self.details.setPlainText(
            (
                "Historical evidence · sources changed since this build.\n\n"
                if self.selected_record and not self.selected_record.get("current", False)
                else ""
            )
            + value["task"]
            + "\n\nPinned memory: "
            + value["memory_revision"]
            + "\nReview fingerprint: "
            + value["review_digest"]
            + "\n\n"
            + value["notice"]
            + (
                "\nNo observed command results. Agent prose is not test evidence."
                if not value["checks"]
                else ""
            )
            + (
                "\nCommand inventory truncated; additional results were omitted."
                if value["checks_truncated"]
                else ""
            )
        )

    def select_requirement(self, index):
        if not self.value or not 0 <= index < len(self.value["requirements"]):
            return
        row = self.value["requirements"][index]
        self.assessment.setCurrentIndex(self.assessment.findData(row["assessment"]))
        for widget, key in ((self.files, "files"), (self.checks, "checks")):
            for i in range(widget.count()):
                item = widget.item(i)
                item.setCheckState(
                    Qt.CheckState.Checked
                    if item.data(Qt.ItemDataRole.UserRole) in row[key]
                    else Qt.CheckState.Unchecked
                )
        self.details.setPlainText(
            self.value["task"]
            + "\n\n"
            + f"{row['title']}\n{row['body']}\n\n"
            + f"Assessment: {row['assessment'].replace('_', ' ')}\n"
            + f"Memory v{row['version']}\n"
            + "\n".join(s["kind"] + ":" + s["id"] for s in row["sources"])
        )

    def link_requirement(self):
        index = self.requirements.currentRow()
        if not self.studio or not self.value or not 0 <= index < len(self.value["requirements"]):
            return
        candidate = copy.deepcopy(self.value)
        row = candidate["requirements"][index]
        row["assessment"] = self.assessment.currentData()
        for widget, key in ((self.files, "files"), (self.checks, "checks")):
            row[key] = [
                widget.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(widget.count())
                if widget.item(i).checkState() == Qt.CheckState.Checked
            ]
        try:
            validate(candidate)
        except ValueError as error:
            self.status.setText(str(error))
            return
        self.value = candidate
        self.requirements.item(index).setText(
            row["title"] + " · " + row["assessment"].replace("_", " ")
        )
        self.status.setText(
            "Requirement links saved in this draft. Share to make them visible to your team."
        )

    def inspect_file(self, index):
        if self.value and 0 <= index < len(self.value["files"]):
            row = self.value["files"][index]
            self.details.setPlainText(
                row["path"]
                + "\n"
                + row["diff"]
                + (
                    "\nDiff excerpt truncated. Review the full file locally."
                    if row["truncated"]
                    else ""
                )
            )

    def inspect_check(self, index):
        if self.value and 0 <= index < len(self.value["checks"]):
            row = self.value["checks"][index]
            self.details.setPlainText(
                f"{row['command']}\nExit code: {row['exit_code']}\n{row['output']}\n"
                + ("Output excerpt truncated." if row["truncated"] else "")
            )

    def share_evidence(self):
        if not self.studio or not self.value or not self.valid():
            return
        if not self.value["memory_revision"]:
            self.status.setText(
                "This saved build has no pinned memory snapshot. "
                "Start a fresh build to share traceable evidence."
            )
            return
        try:
            from aedrova.delivery.files import make_review

            if make_review(self.studio.project).digest != self.review.digest:
                raise ValueError("Local files changed. Refresh review and reopen evidence.")
            value = copy.deepcopy(self.value)
            value["acceptance_criteria"] = [
                line.strip() for line in self.criteria.toPlainText().splitlines() if line.strip()
            ]
            if len(value["acceptance_criteria"]) > 50:
                raise ValueError("Keep acceptance criteria to 50 concise conditions.")
            validate(value)
        except (ValueError, OSError) as error:
            self.status.setText(str(error))
            return
        parameters = {
            "p_id": self.record_id,
            "p_workspace": self.workspace,
            "p_channel": self.channel,
            "p_sources": sorted(self.studio.context.channel_ids),
            "p_version": self.record_version,
            "p_evidence": value,
        }

        def saved(version):
            self.record_version = version
            self.studio.evidence_id, self.studio.evidence_version = self.record_id, version
            self.status.setText(
                f"Shared evidence v{version}. Teammates with source access can review it in Builds."
            )

        def save(service):
            from aedrova.memory.model import snapshot_record

            allowed = authorize(service.snapshot(), self.workspace, self.user)
            if not self.studio.context.channel_ids <= allowed:
                raise PermissionError("Source access changed")
            current = snapshot_record(
                service.memory_context(self.workspace), self.workspace, allowed
            )
            if current["product_memory_snapshot"]["revision"] != value["memory_revision"]:
                raise ValueError("Product memory changed. Start a fresh build.")
            return service.save_build_review(parameters)

        self.run("save", save, saved)

    def send_review(self):
        if not self.selected_record:
            return
        note = self.note.toPlainText().strip()
        if not 1 <= len(note) <= 4000:
            self.status.setText("Add a concise review note (up to 4,000 characters).")
            return
        from aedrova.security.credentials import credential_rules

        if credential_rules(note.encode()):
            self.status.setText("Remove the recognizable credential from your review note.")
            return
        action_key = (
            self.selected_record["id"],
            self.selected_record["version"],
            self.decision.currentData(),
            note,
        )
        parameters = {
            "p_id": self.review_actions.setdefault(action_key, str(uuid4())),
            "p_build": self.selected_record["id"],
            "p_version": self.selected_record["version"],
            "p_decision": self.decision.currentData(),
            "p_note": note,
        }

        def saved(_identifier):
            self.note.clear()
            self.status.setText(
                "Review recorded for this exact evidence version. Code has not been published."
            )

        self.run("decision", lambda service: service.decide_build_review(parameters), saved)

    def reject(self):
        self.closed = True
        if getattr(self.window, "shared_build_dialog", None) is self:
            self.window.shared_build_dialog = None
        self.value = self.selected_record = None
        self.rows = []
        self.details.clear()
        self.requirements.clear()
        self.records.clear()
        self.files.clear()
        self.checks.clear()
        self.note.clear()
        self.criteria.clear()
        super().reject()
