"""Bounded, authenticated meeting text surfaces; no RTC data publishing or capture."""

import time
from uuid import uuid4

from PySide6.QtCore import QThreadPool, QTimer
from PySide6.QtWidgets import QHBoxLayout, QPlainTextEdit, QVBoxLayout

from aedrova.desktop.controls import AppDialog, ChoiceBox
from aedrova.desktop.dialogs import button, label
from aedrova.desktop.materials import system_font
from aedrova.desktop.meeting_transcript import ReviewJob
from aedrova.meetings.consent import capture_permit


class MeetingTextSurface(AppDialog):
    """One request at a time; late results cannot resurrect a closed/private view."""

    def __init__(self, parent, title):
        super().__init__(parent)
        self.closed, self.busy, self.jobs = False, False, []
        self.loaded_once = False
        self.setWindowTitle(title + " · Aedrova")
        self.resize(640, 600)
        self.setMinimumSize(440, 440)
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(24, 24, 24, 24)
        self.body.setSpacing(12)
        self.body.addWidget(label(title, "title"))
        self.text = QPlainTextEdit()
        self.text.setReadOnly(True)
        self.text.setAccessibleName(title)
        self.status = label("", "muted", wrap=True)
        self.status.setAccessibleName(title + " status")
        self.timer = QTimer(self)
        self.timer.setInterval(3000)
        self.timer.timeout.connect(self.refresh)
        self.finished.connect(self.finish)

    def run(self, operation, received, error):
        if self.closed or self.busy:
            return
        self.busy = True
        if not self.loaded_once:
            self.set_loading(self.text, True, "feed")
        if hasattr(self, "update_send"):
            self.update_send()
        job = ReviewJob(operation, error=error)
        self.jobs.append(job)

        def done(result):
            self.jobs.remove(job)
            self.busy = False
            self.loaded_once = True
            if not self.closed:
                self.set_loading(self.text, False)
                received(result)
                if hasattr(self, "update_send"):
                    self.update_send()

        job.signals.result.connect(done)
        QThreadPool.globalInstance().start(job)

    def replace_text(self, text):
        # Preserve selection and scroll position when the server has no new text.
        if text == self.text.toPlainText():
            return
        scroll = self.text.verticalScrollBar()
        at_end, position = scroll.value() >= scroll.maximum(), scroll.value()
        self.text.setPlainText(text)
        scroll.setValue(scroll.maximum() if at_end else position)

    def finish(self, *_):
        self.closed = True
        self.timer.stop()
        self.set_loading(self.text, False)
        self.text.clear()


class MeetingChat(MeetingTextSurface):
    """Persistent channel chat, using the same authenticated/RLS RPCs as chatspace."""

    def __init__(self, parent, service, channel, user, *, valid=lambda: True, names=None):
        super().__init__(parent, "Channel chat")
        self.service, self.channel, self.user = service, channel, user
        self.valid, self.names = valid, names or {}
        self.pending = None
        self.sending = False
        self.body.addWidget(
            label(
                "Shared with this channel, including members outside the call. "
                "Messages stay in channel history.",
                "muted",
                wrap=True,
            )
        )
        self.body.addWidget(self.text, 1)
        self.body.addWidget(self.status)
        self.editor = QPlainTextEdit()
        self.editor.setAccessibleName("Channel message")
        self.editor.setPlaceholderText("Message your team…")
        self.editor.setMaximumHeight(100)
        self.body.addWidget(self.editor)
        actions = QHBoxLayout()
        self.send = button("Send", role="primary")
        self.send.clicked.connect(self.submit)
        self.editor.textChanged.connect(self.update_send)
        close = button("Done", role="outline")
        close.clicked.connect(self.accept)
        actions.addWidget(close)
        actions.addStretch()
        actions.addWidget(self.send)
        self.body.addLayout(actions)
        self.update_send()
        self.timer.start()
        self.refresh()

    def allowed(self):
        return (not self.closed and self.valid()
                and str(getattr(self.service.user, "id", "")) == self.user)

    def update_send(self):
        self.send.setEnabled(
            not self.closed
            and not self.sending
            and not self.busy
            and 1 <= len(self.editor.toPlainText().strip()) <= 10000
        )

    def refresh(self):
        if not self.allowed():
            self.reject()
            return
        if self.busy:
            return
        self.run(
            lambda: self.service.message_page(self.channel, limit=50),
            self.loaded,
            "Channel chat is unavailable. Check your connection and channel access.",
        )

    def loaded(self, result):
        if not self.allowed():
            self.reject()
            return
        if "error" in result:
            self.text.clear()
            self.status.setText(result["error"])
            return
        rows = list(reversed(result["value"][:50]))
        parts = []
        for row in rows:
            if row.get("channel_id") != self.channel:
                self.text.clear()
                self.status.setText("Channel access changed. Reopen chat from your workspace.")
                return
            name = (
                "You"
                if row["sender_id"] == self.user
                else self.names.get(row["sender_id"], "Teammate")
            )
            parts.append(name + "\n" + row["body"])
        self.replace_text("\n\n".join(parts))
        self.status.setText("Latest 50 channel messages" if rows else "Start the conversation.")

    def submit(self):
        if not self.allowed():
            self.reject()
            return
        body = self.editor.toPlainText().strip()
        if self.busy or self.sending or not 1 <= len(body) <= 10000:
            return
        # Retry an ambiguous response with the SAME ID: never duplicate a message.
        if not self.pending or self.pending[1] != body:
            self.pending = (str(uuid4()), body)
        identifier = self.pending[0]
        self.sending = True
        self.editor.setReadOnly(True)
        self.update_send()
        self.status.setText("Sending…")

        def sent(result):
            if not self.allowed():
                self.reject()
                return
            self.sending = False
            self.editor.setReadOnly(False)
            if "error" in result:
                self.text.clear()
                self.status.setText(result["error"])
            else:
                self.pending = None
                self.editor.clear()
                self.status.setText("Sent")
                self.refresh()
            self.update_send()

        self.run(
            lambda: self.service.rpc(
                "send_message",
                {
                    "p_id": identifier,
                    "p_channel": self.channel,
                    "p_body": body,
                    "p_parent": None,
                },
            ),
            sent,
            "Could not confirm sending. Your draft is kept; retry when ready.",
        )

    def finish(self, *_):
        super().finish()
        self.pending = None
        self.editor.clear()


class MeetingCaptions(MeetingTextSurface):
    """Opt-in display of permitted provider text. Does not enable transcription."""

    def __init__(self, parent, worker, *, people, names):
        super().__init__(parent, "Captions")
        self.worker, self.people, self.names = worker, people, names
        self.body.addWidget(
            label(
                "Unreviewed meeting text · speech processing may leave gaps. "
                "Opening captions does not start transcription. Each speaker "
                "must consent and start it themselves.",
                "muted",
                wrap=True,
            )
        )
        self.body.addWidget(self.text, 1)
        self.body.addWidget(self.status)
        actions = QHBoxLayout()
        self.size = ChoiceBox(self)
        self.size.setAccessibleName("Caption text size")
        for name, value in (("Standard", 14), ("Large", 18), ("Extra large", 22)):
            self.size.addItem(name, value)
        self.size.currentIndexChanged.connect(self.resize_text)
        self.resize_text()
        actions.addWidget(self.size)
        actions.addStretch()
        close = button("Done", role="outline")
        close.clicked.connect(self.accept)
        actions.addWidget(close)
        self.body.addLayout(actions)
        # Clear stale permission text BEFORE any network result arrives.
        self.guard = QTimer(self)
        self.guard.setInterval(500)
        self.guard.timeout.connect(self.check_consent)
        self.finished.connect(self.guard.stop)
        self.guard.start()
        self.timer.start()
        self.refresh()

    def resize_text(self, *_):
        self.text.setFont(system_font(self.size.currentData() or 14))

    def permitted(self):
        snapshot = self.worker.snapshot or {}
        if (
            self.closed
            or not self.worker.connected
            or not self.worker.text_available
            or time.monotonic() - self.worker.snapshot_at > 10
        ):
            return None
        permit = capture_permit(snapshot, self.people())
        return permit if permit and permit.meeting_id == self.worker.meeting else None

    def check_consent(self):
        if not self.permitted():
            self.text.clear()
            self.status.setText("Captions paused · waiting for current participant consent.")
            return False
        return True

    def refresh(self):
        if not self.check_consent() or self.busy:
            return
        permit = self.permitted()

        def received(result):
            if self.permitted() != permit:
                self.text.clear()
                self.status.setText("Consent changed. Waiting for permitted captions.")
                return
            if "error" in result:
                self.text.clear()
                self.status.setText(result["error"])
                return
            rows = result["value"][:20]
            if any(row.get("meeting_id") != self.worker.meeting for row in rows):
                self.text.clear()
                self.status.setText("Captions unavailable. Reopen the meeting.")
                return
            # Latest insertion order, not microphone offsets (speakers' offsets may overlap).
            parts = [
                self.names().get(row["speaker_id"], "Participant") + "\n" + row["body"]
                for row in reversed(rows)
            ]
            self.replace_text("\n\n".join(parts))
            self.status.setText(
                "Latest permitted captions · unreviewed"
                if parts
                else "Waiting for a participant to start transcription and speak."
            )

        self.run(
            lambda: self.worker.client.captions(permit.meeting_id),
            received,
            "Captions unavailable. Check your connection, consent and meeting service.",
        )
