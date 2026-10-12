"""Local review drafts; only Confirm makes an atomic, permission-checked save."""

import json
import threading
import time

from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtWidgets import QHBoxLayout, QListWidget, QPlainTextEdit, QVBoxLayout

from aedrova.desktop.brand import BrandMark
from aedrova.desktop.controls import AppDialog
from aedrova.desktop.dialogs import button, label
from aedrova.desktop.meeting_transcript import ReviewJob


class MeetingWrapup(AppDialog):
    def __init__(self, parent, client, meeting, *, title="Meeting transcript", names=None):
        super().__init__(parent)
        self.client, self.meeting, self.names = client, meeting, names or {}
        self.rows, self.drafts, self.jobs = [], {}, []
        self.selected_index = -1
        self.busy = self.closed = False
        self.cancelled = threading.Event()
        self.setWindowTitle("Review your meeting · Aedrova")
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.resize(920, 700)
        self.setMinimumSize(640, 560)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)
        brand = QHBoxLayout()
        brand.addWidget(BrandMark(28))
        brand.addWidget(label("MEETING COMPLETE", "muted"), 1)
        layout.addLayout(brand)
        layout.addWidget(label("Share with Aedrova?", "heading", wrap=True))
        layout.addWidget(label("Review your transcript, make any corrections, then confirm.",
                               "muted", wrap=True))
        layout.addWidget(label(title, "title", wrap=True))
        self.status = label("", "muted", wrap=True)
        layout.addWidget(self.status)
        content = QHBoxLayout()
        content.setSpacing(18)
        self.sources = QListWidget()
        self.sources.setProperty("accountList", True)
        self.sources.setWordWrap(True)
        self.sources.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.sources.setMinimumWidth(190)
        self.sources.setMaximumWidth(280)
        self.sources.setAccessibleName("Meeting transcript segments")
        self.edit = QPlainTextEdit()
        self.edit.setAccessibleName("Edit meeting transcript")
        self.edit.setPlaceholderText("Select a part of the transcript to review.")
        content.addWidget(self.sources, 1)
        content.addWidget(self.edit, 3)
        layout.addLayout(content, 1)
        layout.addWidget(label("Only text participants allowed Aedrova to use becomes context. "
                               "Your edits preserve the original text and speaker attribution.",
                               "muted", wrap=True))
        actions = QHBoxLayout()
        self.later = button("Review later", role="outline")
        self.retry = button("Reload transcript", role="outline")
        self.retry.hide()
        self.confirm = button("Confirm", role="primary")
        actions.addWidget(self.later)
        actions.addWidget(self.retry)
        actions.addStretch()
        actions.addWidget(self.confirm)
        layout.addLayout(actions)
        self.later.clicked.connect(self.reject)
        self.retry.clicked.connect(self.load)
        self.confirm.clicked.connect(self.submit)
        self.sources.currentRowChanged.connect(self.select)
        self.edit.textChanged.connect(self.changed)
        self.finished.connect(self.finish)
        account = getattr(parent, "account_dialog", None)
        if account is not None and hasattr(account, "session_closed"):
            account.session_closed.connect(self.reject)
        self.load()

    def finish(self, *_):
        self.closed = True
        self.cancelled.set()
        self.rows.clear()
        self.drafts.clear()
        self.edit.clear()
        self.sources.clear()

    def run(self, operation, callback):
        if self.busy or self.closed:
            return
        self.busy = True
        self.set_loading(self.sources, True, "feed")
        self.retry.hide()
        self.edit.setEnabled(False)
        self.sources.setEnabled(False)
        self.confirm.setEnabled(False)
        job = ReviewJob(operation)
        self.jobs.append(job)

        def received(result):
            self.jobs.remove(job)
            if self.closed:
                return
            self.busy = False
            self.set_loading(self.sources, False)
            self.sources.setEnabled(True)
            if "error" in result:
                self.rows.clear()
                self.drafts.clear()
                self.sources.clear()
                self.edit.clear()
                self.selected_index = -1
                self.status.setText("Your transcript could not be confirmed. Access or text may "
                                    "have changed. Reload it to review the current version.")
                self.retry.show()
            else:
                callback(result["value"])
            self.changed()
        job.signals.result.connect(received)
        QThreadPool.globalInstance().start(job)

    def load(self):
        def fetch():
            deadline = time.monotonic() + 45
            status = self.client.wrapup(self.meeting)
            if status.get("ready") is not True or status.get("meeting") != self.meeting:
                raise PermissionError("Meeting is not ready for this reviewer")
            rows = []
            for page in range(200):
                if self.cancelled.is_set():
                    return []
                if time.monotonic() > deadline:
                    raise TimeoutError("Transcript load timed out")
                batch = self.client.transcript(self.meeting, page)
                rows.extend(batch)
                if len(batch) < 50:
                    break
            if len(rows) > 10000 or len({r["id"] for r in rows}) != len(rows):
                raise ValueError("Invalid transcript")
            return rows
        self.run(fetch, self.loaded)

    def loaded(self, rows):
        self.selected_index = -1
        self.sources.clear()
        self.rows = rows
        self.drafts = {r["id"]: r.get("review_body") or r["body"] for r in rows}
        for row in rows:
            seconds = row["offset_ms"] // 1000
            speaker = self.names.get(row["speaker_id"], "Participant")
            preview = self.drafts[row["id"]]
            self.sources.addItem(f"{seconds // 60:02}:{seconds % 60:02} · {speaker}\n"
                                 + preview[:55] + ("…" if len(preview) > 55 else ""))
        eligible = sum(r.get("ai_allowed") is True for r in rows)
        self.status.setText(f"{len(rows)} parts to review · {eligible} permitted for Aedrova")
        if rows:
            self.sources.setCurrentRow(0)
        else:
            self.status.setText("No saved transcript is available for this meeting.")
            self.edit.clear()

    def select(self, index):
        self.selected_index = index
        self.edit.blockSignals(True)
        self.edit.setPlainText(self.drafts[self.rows[index]["id"]]
                              if 0 <= index < len(self.rows) else "")
        self.edit.blockSignals(False)
        self.edit.setEnabled(not self.busy and 0 <= index < len(self.rows))
        self.changed()

    def payload(self):
        return [{"identifier": r["id"], "version": r.get("review_version", 0),
                 "body": self.drafts[r["id"]].strip()} for r in self.rows]

    def changed(self):
        if self.closed:
            return
        if 0 <= self.selected_index < len(self.rows) and not self.busy:
            self.drafts[self.rows[self.selected_index]["id"]] = self.edit.toPlainText()
        valid = bool(self.rows) and all(1 <= len(v.strip()) <= 2000
                                       for v in self.drafts.values())
        if valid:
            valid = len(json.dumps(self.payload(), ensure_ascii=False).encode()) < 1400000
        self.confirm.setEnabled(valid and not self.busy)
        if self.rows and not valid and not self.busy:
            self.status.setText("Keep each part between 1 and 2,000 characters. "
                                "Very large transcripts must be reviewed in meeting history.")

    def submit(self):
        if self.busy or not self.confirm.isEnabled():
            return
        payload = self.payload()

        def saved(result):
            if result.get("confirmed") == len(payload):
                self.accept()
            else:
                self.status.setText("Confirmation was not completed. Reload the transcript.")
                self.retry.show()
        self.run(lambda: self.client.confirm_transcript(self.meeting, payload), saved)


def offer_wrapup(window, worker, status):
    """A late callback cannot switch accounts, replace a newer call or reopen twice."""
    current = getattr(window, "meeting_call", None)
    account = getattr(window, "account_dialog", None)
    service = getattr(account, "service", None)
    user = getattr(service, "user", None)
    if (not isinstance(status, dict) or status.get("ready") is not True
            or status.get("meeting") != worker.meeting or user is None
            or str(user.id) != worker.user or current is None or current.worker is not worker):
        return
    if getattr(current, "wrapup_offered", False):
        return
    if getattr(window, "workspace_id", None) != getattr(worker, "workspace", None):
        return
    current.wrapup_offered = True
    current.accept()
    dialog = MeetingWrapup(window, worker.client, worker.meeting,
                          title=status.get("title") or "Meeting transcript", names=current.names)
    window.meeting_wrapup = dialog
    dialog.open()
