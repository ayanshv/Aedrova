"""Concrete file review, local application and separately approved GitHub delivery."""

import threading
from uuid import uuid4

from PySide6.QtCore import QThreadPool, QUrl, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QHBoxLayout,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
)

from aedrova.agents.context import authorize
from aedrova.delivery.files import apply_review, make_review
from aedrova.delivery.github import GitHub, prepare_publication, publish
from aedrova.delivery.preview import StaticPreview
from aedrova.desktop.controls import AppDialog
from aedrova.desktop.dialogs import button, label
from aedrova.desktop.projects import Job, binding, open_editor


class ReviewDialog(AppDialog):
    def __init__(self, studio):
        super().__init__(studio)
        self.studio, self.window = studio, studio.window
        self.review = self.publication = self.job = self.preview = None
        self.cancelled = threading.Event()
        self.callback = None
        self.setWindowTitle("Aedrova · Review & deliver")
        self.resize(960, 760)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)
        layout.addWidget(label("From working code to your project.", "heading"))
        layout.addWidget(
            label(
                "Review every changed file. Applying locally and publishing to GitHub "
                "are separate approvals.",
                "muted",
                wrap=True,
            )
        )
        self.status = label("Reading changes…", "muted", wrap=True)
        layout.addWidget(self.status)
        content = QHBoxLayout()
        self.files = QListWidget()
        self.files.setProperty("accountList", True)
        self.files.setAccessibleName("Changed files")
        self.files.setMaximumWidth(280)
        self.diff = QPlainTextEdit()
        self.diff.setReadOnly(True)
        self.diff.setAccessibleName("File diff")
        content.addWidget(self.files)
        content.addWidget(self.diff, 1)
        layout.addLayout(content, 1)
        self.scope = label("", "muted", wrap=True)
        layout.addWidget(self.scope)
        local = QHBoxLayout()
        self.refresh_button = button("Refresh review", role="outline")
        self.ide = button("Open build in IDE", role="outline")
        self.preview_button = button("Preview site", role="outline")
        self.apply_button = button("Apply to project…", role="primary")
        for control in (self.refresh_button, self.ide, self.preview_button, self.apply_button):
            local.addWidget(control)
        layout.addLayout(local)
        remote = QHBoxLayout()
        self.prepare_button = button("Prepare GitHub review", role="outline")
        self.publish_button = button("Publish branch & draft PR…", role="primary")
        self.publish_button.setEnabled(False)
        remote.addWidget(self.prepare_button)
        remote.addWidget(self.publish_button)
        layout.addLayout(remote)
        self.evidence_button = button("Requirements & shared evidence…", role="outline")
        self.evidence_button.clicked.connect(self.open_evidence)
        layout.addWidget(self.evidence_button)
        self.evidence_dialog = None

        self.files.currentRowChanged.connect(self.selected)
        self.refresh_button.clicked.connect(self.refresh)
        self.ide.clicked.connect(self.open_ide)
        self.preview_button.clicked.connect(self.open_preview)
        self.apply_button.clicked.connect(self.apply)
        self.prepare_button.clicked.connect(self.prepare)
        self.publish_button.clicked.connect(self.publish)
        studio.account.session_closed.connect(self.revoke)
        self.refresh()

    def set_busy(self, value):
        for control in (
            self.refresh_button,
            self.ide,
            self.preview_button,
            self.apply_button,
            self.prepare_button,
        ):
            control.setEnabled(not value and not self.cancelled.is_set())
        self.publish_button.setEnabled(
            not value and self.publication is not None and not self.cancelled.is_set()
        )

    def run(self, operation, completed, *, publishing=False):
        if self.job or self.cancelled.is_set():
            return
        self.set_busy(True)
        self.callback = completed
        self.status.setText("Checking access and preparing the action…")
        # Reserve the worker immediately so repeated clicks cannot enqueue another action.
        self.job = True

        def connect():
            try:
                return {"service": self.studio.account.service.fork_for_context()}
            except Exception:
                return {"error": "Could not verify workspace access. Sign in and retry."}

        def connected(result):
            if "error" in result:
                self.job_finished(result)
                return
            service = result["service"]
            if self.cancelled.is_set():
                service.close_context()
                self.job = None
                return

            def guard():
                if self.cancelled.is_set() or self.studio.invalidated:
                    raise PermissionError("Access changed or the review was cancelled.")

            def authorized_operation():
                try:
                    guard()
                    snapshot = service.snapshot()
                    allowed = authorize(snapshot, self.studio.workspace, self.studio.user)
                    if self.studio.context and not self.studio.context.channel_ids <= allowed:
                        raise PermissionError("Source access changed. Create a new build.")
                    if str(service.user.id) != self.studio.user:
                        raise PermissionError("The signed-in account changed.")
                    if publishing and not any(
                        m["workspace_id"] == self.studio.workspace
                        and m["user_id"] == self.studio.user
                        and m["role"] in {"owner", "admin"}
                        for m in snapshot["members"]
                    ):
                        raise PermissionError(
                            "A workspace owner or admin must approve GitHub publication."
                        )
                    guard()
                    return operation(guard)
                finally:
                    service.close_context()

            self.job = Job(authorized_operation)
            self.job.signals.finished.connect(self.job_finished)
            QThreadPool.globalInstance().start(self.job)

        if not self.window.connected.enqueue(("review", id(self)), connect, connected):
            self.job = None
            self.set_busy(False)
            self.status.setText("Connection busy. Try again shortly.")

    @Slot(object)
    def job_finished(self, result):
        self.job = None
        if self.cancelled.is_set():
            value = result.get("value")
            if isinstance(value, StaticPreview):
                value.close()
            return
        self.set_busy(False)
        if "error" in result:
            self.publication = None
            self.publish_button.setEnabled(False)
            self.status.setText(result["error"])
        else:
            self.callback(result["value"])

    def refresh(self):
        self.publication = None
        self.scope.clear()
        self.run(lambda guard: make_review(self.studio.project), self.loaded)

    def loaded(self, review):
        self.review = review
        self.files.clear()
        for change in review.changes:
            self.files.addItem(change.description())
        if review.changes:
            self.files.setCurrentRow(0)
        else:
            self.diff.setPlainText("No changes from this build's starting files.")
        self.status.setText(
            f"{len(review.changes)} changed files · local destination: {review.source}"
        )
        self.scope.setText("Review fingerprint: " + review.digest)
        self.apply_button.setEnabled(bool(review.changes))
        self.prepare_button.setEnabled(bool(review.changes))

    def open_evidence(self):
        if not self.review or self.job or self.cancelled.is_set():
            return
        from aedrova.desktop.build_evidence import SharedBuilds

        try:
            self.evidence_dialog = SharedBuilds(self.window, studio=self.studio, review=self.review)
            self.evidence_dialog.show()
        except (ValueError, OSError) as error:
            self.status.setText(str(error))

    def selected(self, row):
        if self.review and 0 <= row < len(self.review.changes):
            self.diff.setPlainText(self.review.changes[row].diff())

    def open_ide(self):
        try:
            open_editor(self.window, self.studio.project)
        except (ValueError, OSError) as exc:
            self.status.setText(str(exc))

    def open_preview(self):
        if self.preview:
            self.preview.close()
            self.preview = None
            self.preview_button.setText("Preview site")
            return
        self.run(lambda guard: StaticPreview(self.studio.project), self.preview_ready)

    def preview_ready(self, preview):
        self.preview = preview
        self.preview_button.setText("Stop preview")
        self.status.setText(
            "Local static preview. Network fetches and form submissions are blocked."
        )
        QDesktopServices.openUrl(QUrl(preview.url))

    def apply(self):
        if not self.review or not self.review.changes:
            return
        if (
            QMessageBox.question(
                self,
                "Apply reviewed changes?",
                f"Apply {len(self.review.changes)} reviewed file changes "
                f"to:\n{self.review.source}\n\n"
                "Existing edits to these files will block application. A recovery copy is kept. "
                "This does not stage, commit or push anything.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        self.run(lambda guard: apply_review(self.review, guard=guard), self.applied)

    def applied(self, receipt):
        self.status.setText("Applied. Recovery copy: " + str(receipt))
        self.apply_button.setEnabled(False)
        self.record_delivery("local_apply", "Reviewed changes applied locally")
        self.studio.repository.setText(str(self.review.source))

    def prepare(self):
        if not self.review:
            return
        repo = binding(self.window, self.studio.workspace).get("repository")
        if not repo:
            self.status.setText("Connect a GitHub repository in Projects first.")
            return
        self.run(
            lambda guard: prepare_publication(
                GitHub(), repo, self.review, self.studio.request.toPlainText()
            ),
            self.prepared,
            publishing=True,
        )

    def prepared(self, publication):
        self.publication = publication
        visibility = "PRIVATE" if publication.private else "PUBLIC — anyone can see uploaded code"
        self.scope.setText(
            f"{visibility}\nPR title: {publication.title}\n"
            f"Repository: {publication.repository}\nNew branch: "
            f"{publication.branch}\nBase: {publication.base_branch} at "
            f"{publication.base_sha}\nReview: {publication.review_digest}\nOnly the "
            f"displayed changed files will be uploaded. No chat context is included."
        )
        self.status.setText("Ready for approval. This scope expires in ten minutes.")
        self.publish_button.setEnabled(True)

    def publish(self):
        if not self.publication or not self.review:
            return
        if (
            QMessageBox.question(
                self,
                "Publish this exact review?",
                self.scope.text() + "\n\nCreate this new branch and draft pull request on GitHub?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        publication, review = self.publication, self.review
        self.publication = None
        self.run(
            lambda guard: publish(GitHub(), publication, review, authorized=True, guard=guard),
            self.published,
            publishing=True,
        )

    def published(self, result):
        self.status.setText(result["message"] + "\n" + result["url"])
        self.scope.setText(result["url"])
        self.record_delivery("draft_pr" if "/pull/" in result["url"] else "branch", result["url"])
        self.publish_button.setEnabled(False)

    def record_delivery(self, kind, reference):
        identifier = getattr(self.studio, "evidence_id", None)
        if not identifier:
            return
        parameters = {
            "p_id": str(uuid4()),
            "p_build": identifier,
            "p_digest": self.review.digest,
            "p_kind": kind,
            "p_reference": reference,
        }

        def write():
            try:
                self.studio.account.service.record_build_delivery(parameters)
                return True
            except Exception:
                return False

        def synced(ok):
            if not ok:
                self.window.notify(
                    "Delivery succeeded, but its shared receipt could not sync. "
                    "The actual result remains in this review."
                )

        if not self.window.connected.enqueue(("delivery-receipt", identifier, kind), write, synced):
            synced(False)

    def revoke(self):
        self.cancelled.set()
        if self.evidence_dialog:
            self.evidence_dialog.reject()
        if self.preview:
            self.preview.close()
            self.preview = None
        self.review = self.publication = None
        self.files.clear()
        self.diff.clear()
        self.scope.clear()
        self.status.clear()
        self.hide()

    def closeEvent(self, event):  # noqa: N802
        if self.job:
            self.status.setText("Finishing the approved action. Wait before closing this review.")
            event.ignore()
        else:
            self.revoke()
            event.accept()

    def reject(self):
        self.close()
