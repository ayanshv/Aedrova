"""On-device meeting notes with participant consent and review before channel sharing."""

import tempfile
import threading
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import QObject, QThreadPool, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QProgressBar,
    QTabWidget,
    QVBoxLayout,
)
from shiboken6 import isValid

from aedrova.desktop.brand import BrandMark
from aedrova.desktop.controls import AppDialog
from aedrova.desktop.dialogs import button, label
from aedrova.desktop.meeting_listening import ListeningCapsule
from aedrova.desktop.meeting_transcript import ReviewJob
from aedrova.meetings.local_capture import LocalCapture, possible_meeting_apps
from aedrova.meetings.local_speech import download, draft_notes, ready, render_transcript


class DownloadSignals(QObject):
    progress = Signal(int)


class LocalMeetingNotes(AppDialog):
    def __init__(self, window, *, capture=None):
        super().__init__(window)
        self.window = window
        self.workspace, self.channel = window.workspace_id, window.channel_id
        self.account = getattr(window, "account_dialog", None)
        self.service = getattr(self.account, "service", None)
        self.rows, self.jobs = [], []
        self.closed = False
        self.downloading = self.saving = False
        self.cancelled = threading.Event()
        self.identifier = str(uuid4())
        self.capture = capture or LocalCapture(self)
        self.setWindowTitle("Meeting notes · Aedrova")
        self.resize(860, 720)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)
        header = QHBoxLayout()
        header.addWidget(BrandMark(32))
        header.addWidget(label("Notes for your meeting", "title"), 1)
        layout.addLayout(header)
        layout.addWidget(
            label(
                "Keep your call in Zoom, Meet or Teams. Transcription runs on this Mac.",
                "muted",
                wrap=True,
            )
        )
        self.suggestion = label(
            "Browser meeting? You can start notes manually.", "muted", wrap=True
        )
        layout.addWidget(self.suggestion)
        self.title = QLineEdit("Meeting notes")
        self.title.setMaxLength(120)
        self.title.setAccessibleName("Meeting title")
        layout.addWidget(self.title)
        self.consent = QCheckBox("Everyone has agreed to transcription and sharing reviewed notes")
        layout.addWidget(self.consent)
        layout.addWidget(
            label(
                "Microphone and computer audio are captured, including other apps’ sounds. "
                "No video is saved. Audio stays on this Mac and is removed after processing. "
                "Only Confirm shares text with the selected channel.",
                "muted",
                wrap=True,
            )
        )
        self.download = button("Download on-device speech · 148 MB", role="outline")
        self.download.setVisible(not ready())
        self.download.clicked.connect(self.install_model)
        layout.addWidget(self.download)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.hide()
        layout.addWidget(self.progress)
        self.tabs = QTabWidget()
        self.notes = QPlainTextEdit()
        self.notes.setPlaceholderText(
            "Draft notes appear here after you finish. Edit them before sharing."
        )
        self.notes.setAccessibleName("Edit meeting notes")
        self.transcript = QPlainTextEdit()
        self.transcript.setPlaceholderText("Your local transcript will appear here.")
        self.transcript.setAccessibleName("Edit meeting transcript")
        self.tabs.addTab(self.notes, "Notes")
        self.tabs.addTab(self.transcript, "Transcript")
        layout.addWidget(self.tabs, 1)
        self.share_transcript = QCheckBox("Include the reviewed transcript")
        self.share_transcript.setChecked(True)
        layout.addWidget(self.share_transcript)
        destination = getattr(getattr(window, "channel", None), "name", self.channel)
        layout.addWidget(label("Share to #" + destination, "muted", wrap=True))
        self.status = label("Not listening", "muted", wrap=True)
        layout.addWidget(self.status)
        actions = QHBoxLayout()
        self.start = button("Start notes", role="primary")
        self.stop = button("Finish", role="outline")
        self.stop.setEnabled(False)
        self.confirm = button("Confirm", role="primary")
        self.confirm.setEnabled(False)
        actions.addWidget(self.start)
        actions.addWidget(self.stop)
        actions.addStretch()
        actions.addWidget(self.confirm)
        layout.addLayout(actions)
        self.start.clicked.connect(self.begin)
        self.stop.clicked.connect(self.capture.stop)
        self.confirm.clicked.connect(self.share)
        self.consent.toggled.connect(self.update_controls)
        self.indicator = ListeningCapsule(self)
        self.indicator.stop_requested.connect(self.capture.stop)
        self.indicator.review_requested.connect(self.show_review)
        self.capture.status.connect(self.capture_status)
        if hasattr(self.capture, "level"):
            self.capture.level.connect(self.audio_level)
        self.capture.segment.connect(self.add_segment)
        self.capture.finished.connect(self.review)
        self.finished.connect(self.dispose)
        QApplication.instance().aboutToQuit.connect(self.dispose)
        if self.account:
            self.account.session_closed.connect(self.reject)
        self.detector = QTimer(self)
        self.detector.setInterval(15000)
        self.detector.timeout.connect(self.detect)
        self.detector.start()
        QTimer.singleShot(0, self.detect)
        self.update_controls()

    def detect(self):
        if self.closed or self.capture.active:
            return
        job = ReviewJob(possible_meeting_apps, error="Meeting app detection unavailable.")
        self.jobs.append(job)

        def detected(result):
            data = result.get("value") or {}
            if not self.closed and data.get("names"):
                names = ", ".join(data["names"])
                self.suggestion.setText(
                    (names + " is using your microphone. In a meeting? Start notes when ready.")
                    if data.get("active")
                    else names + " is open. Start notes when your call begins."
                )

        job.signals.result.connect(detected)
        QThreadPool.globalInstance().start(job)

    def update_controls(self, *_):
        self.start.setEnabled(
            self.consent.isChecked()
            and ready()
            and not self.closed
            and not self.capture.active
            and not self.downloading
            and not self.rows
        )
        self.stop.setEnabled(self.capture.active and not self.closed)
        self.confirm.setEnabled(
            bool(self.rows)
            and not self.capture.active
            and not self.closed
            and not self.saving
            and self.consent.isChecked()
        )
        self.consent.setEnabled(not self.capture.active and not self.saving)

    def install_model(self):
        if self.downloading:
            return
        self.downloading = True
        self.download.setEnabled(False)
        self.progress.show()
        self.download_signals = DownloadSignals(self)
        self.download_signals.progress.connect(self.progress.setValue)
        job = ReviewJob(
            lambda: download(self.download_signals.progress.emit, self.cancelled.is_set),
            error="Speech download did not finish. Check your connection and retry.",
        )
        self.jobs.append(job)

        def installed(result):
            self.downloading = False
            if self.closed:
                return
            self.progress.hide()
            self.download.setVisible(not ready())
            self.download.setEnabled(True)
            self.status.setText(
                result.get("error") or "Speech is ready on this Mac. No API key needed."
            )
            self.update_controls()

        job.signals.result.connect(installed)
        QThreadPool.globalInstance().start(job)

    def begin(self):
        try:
            self.capture.start(consent=self.consent.isChecked())
        except (ValueError, PermissionError) as error:
            self.status.setText(str(error))
        if self.capture.active:
            self.indicator.set_state("Preparing notes")
            self.indicator.show_on_side()
        self.transcript.setReadOnly(self.capture.active)
        self.notes.setReadOnly(self.capture.active)
        self.update_controls()

    def show_review(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def audio_level(self, value):
        self.indicator.pulse.target = value

    def capture_status(self, text):
        self.status.setText(text)
        if text.startswith("Listening locally"):
            self.indicator.set_state("Listening locally", listening=True)
        elif text.startswith("Allow "):
            self.indicator.set_state("Allow audio access")
        elif text.startswith("Finishing"):
            self.indicator.set_state("Finishing notes")

    def add_segment(self, row):
        if self.closed:
            return
        self.rows.append(row)
        text = render_transcript(self.rows)
        if len(text.encode("utf-8")) > 220000:
            self.capture.stop()
            self.status.setText("Transcript size limit reached. Finish and review these notes.")
            return
        self.transcript.setPlainText(text)
        bar = self.transcript.verticalScrollBar()
        bar.setValue(bar.maximum())

    def review(self):
        self.indicator.hide()
        if self.closed:
            return
        self.transcript.setReadOnly(False)
        self.notes.setReadOnly(False)
        self.notes.setPlainText(draft_notes(self.rows))
        self.status.setText(
            "Share with Aedrova? Review the draft notes and transcript, then Confirm."
            if self.rows
            else "No speech was transcribed. Check your devices and permissions."
        )
        self.update_controls()

    def share(self):
        connected = getattr(self.window, "connected", None)
        if (
            self.closed
            or self.capture.active
            or self.saving
            or not self.rows
            or not self.consent.isChecked()
            or not connected
            or not connected.active
            or self.window.workspace_id != self.workspace
            or self.window.channel_id != self.channel
            or self.account.service is not self.service
        ):
            self.status.setText("Return to the original signed-in channel to share these notes.")
            return
        notes = self.notes.toPlainText().strip()
        transcript = (
            self.transcript.toPlainText().strip() if self.share_transcript.isChecked() else ""
        )
        title = self.title.text().strip() or "Meeting notes"
        text = (
            title
            + "\n\nReviewed meeting notes\n"
            + notes
            + ("\n\nReviewed transcript\n" + transcript if transcript else "")
        )
        data = text.encode("utf-8")
        if not (notes or transcript) or len(data) > 240000:
            self.status.setText("Choose up to 240 KB of reviewed text to share.")
            return
        from aedrova.security.credentials import credential_rules

        if credential_rules(data):
            self.status.setText("Remove credentials from the reviewed text before sharing.")
            return
        self.saving = True
        self.update_controls()
        self.tabs.setEnabled(False)
        self.status.setText("Sharing reviewed text with this channel…")

        def operation():
            try:
                with tempfile.TemporaryDirectory(prefix="aedrova-reviewed-notes-") as temporary:
                    path = Path(temporary) / "meeting-notes.txt"
                    path.write_bytes(data)
                    message = self.service.upload_attachment(
                        self.identifier,
                        self.channel,
                        path,
                        None,
                        cancelled=self.cancelled.is_set,
                    )
                    return {"message": message}
            except Exception:
                return {"error": True}

        def saved(result):
            self.saving = False
            if self.closed or not isValid(self):
                return
            self.tabs.setEnabled(True)
            if result.get("message"):
                self.status.setText(
                    "Shared with this channel. Aedrova and its Buds can use the reviewed text."
                )
                self.confirm.setEnabled(False)
                self.rows.clear()
                QTimer.singleShot(0, connected.refresh)
            else:
                self.status.setText(
                    "Sharing was not confirmed. Review the channel before retrying."
                )
                self.update_controls()

        if not connected.enqueue(
            ("local-meeting-notes", self.identifier), operation, saved, priority=True
        ):
            self.saving = False
            self.tabs.setEnabled(True)
            self.status.setText("Wait for the current request, then try Confirm again.")
            self.update_controls()

    def dispose(self, *_):
        self.closed = True
        self.cancelled.set()
        self.detector.stop()
        self.indicator.hide()
        self.capture.discard()
        self.rows.clear()
        self.notes.clear()
        self.transcript.clear()


def open_local_meeting_notes(window):
    existing = getattr(window, "local_meeting_notes", None)
    if existing and existing.closed and existing.capture.active:
        window.notify("Finishing the previous local capture. Try again in a moment.")
        return
    if existing and (existing.isVisible() or existing.capture.active):
        existing.show()
        existing.raise_()
        return
    window.local_meeting_notes = LocalMeetingNotes(window)
    window.local_meeting_notes.open()
