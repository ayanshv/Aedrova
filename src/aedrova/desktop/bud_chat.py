"""User-owned Bud conversations, outside shared channels and workspace search."""

from datetime import datetime
from uuid import uuid4

from PySide6.QtCore import Qt, QThreadPool, QTimer
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QScrollArea, QVBoxLayout, QWidget

from aedrova.desktop.agent_stream import ActivityRow
from aedrova.desktop.controls import AppDialog
from aedrova.desktop.conversation import Composer
from aedrova.desktop.dialogs import button, label
from aedrova.desktop.dot_analysis import QueryJob
from aedrova.desktop.dots import shelf_rows
from aedrova.desktop.projects import binding


class BudChat(AppDialog):
    def __init__(self, window, bud):
        super().__init__(window)
        self.host, self.bud = window, dict(bud)
        self.workspace, self.user = window.workspace_id, str(window.current_user().id)
        self.service = window.account_dialog.service
        self.history, self.job = [], None
        self.closed, self.busy = False, False
        self.loaded = False
        self.unsaved_reply = None
        self.setWindowTitle("Aedrova · " + bud["name"])
        self.resize(760, 760)
        self.setMinimumSize(520, 520)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)
        header = QHBoxLayout()
        from aedrova.desktop.ai_teammates import Character

        avatar = Character(shelf_rows([bud])[0]["config"], reduced_motion=window.reduced_motion)
        avatar.setFixedSize(48, 44)
        header.addWidget(avatar)
        header.addWidget(label(bud["name"], "title"), 1)
        settings = button("Configure", "Configure " + bud["name"], "outline")
        settings.clicked.connect(self.configure)
        header.addWidget(settings)
        from aedrova.dots.roles import role_for

        if role_for(bud.get("role", "")) == "marketing":
            social = button("Social", "Social accounts, drafts and publishing", "outline")
            social.clicked.connect(self.open_social)
            header.addWidget(social)
        close = button("Close", role="outline")
        close.clicked.connect(self.reject)
        header.addWidget(close)
        layout.addLayout(header)
        layout.addWidget(
            label(
                "Only you · Saved to your account · Replies use your AI provider",
                "muted",
                wrap=True,
            )
        )
        self.workspace_context = QCheckBox("Include workspace context for this reply")
        self.workspace_context.setToolTip(
            "Off by default. When enabled, permitted chats, files, product memory and "
            "approved meeting transcripts may be sent to your AI provider."
        )
        layout.addWidget(self.workspace_context)
        layout.addWidget(
            label(
                "Uses this Bud’s authorized tools. Conversations aren’t shared with teammates. "
                "For code changes, use the Build studio in your workspace.",
                "muted",
                wrap=True,
            )
        )
        self.feed = QScrollArea()
        self.feed.setWidgetResizable(True)
        self.feed.setObjectName("AgentStream")
        self.feed.setAccessibleName("Private conversation with " + bud["name"])
        self.feed.setAccessibleDescription(
            "Shows the latest 100 saved messages. Replies use up to 40 recent messages."
        )
        self.feed.setToolTip(self.feed.accessibleDescription())
        content = QWidget()
        self.rows = QVBoxLayout(content)
        self.rows.setContentsMargins(0, 4, 8, 4)
        self.rows.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.rows.setSpacing(12)
        self.feed.setWidget(content)
        layout.addWidget(self.feed, 1)
        self.status = label("", "muted", wrap=True)
        layout.addWidget(self.status)
        actions = QHBoxLayout()
        self.retry = button("Retry", role="outline")
        self.retry.clicked.connect(self.retry_request)
        self.retry.hide()
        self.stop = button("Stop", "Stop Bud reply", "outline")
        self.stop.clicked.connect(self.cancel)
        self.stop.hide()
        actions.addWidget(self.retry)
        actions.addWidget(self.stop)
        actions.addStretch()
        layout.addLayout(actions)
        self.composer = Composer(self)
        self.composer.set_agent_name(bud["name"])
        self.composer.command_cue.setText("PRIVATE · " + bud["name"])
        self.composer.editor.setPlaceholderText("Ask " + bud["name"] + " anything…")
        self.composer.mention.hide()
        self.composer.submitted.connect(self.send)
        layout.addWidget(self.composer)
        self.finished.connect(self.shutdown)
        window.account_dialog.session_closed.connect(self.reject)
        self.guard = QTimer(self)
        self.guard.timeout.connect(lambda: None if self.current() else self.reject())
        self.guard.start(250)
        self.load()

    def current(self):
        return (
            not self.closed
            and self.host.current_user()
            and str(self.host.current_user().id) == self.user
            and self.host.workspace_id == self.workspace
            and self.host.account_dialog.service is self.service
            and self.host.connected.active
        )

    def configure(self):
        from aedrova.desktop.dots import open_dots

        self.reject()
        open_dots(self.host, self.bud["id"])

    def open_social(self):
        from aedrova.desktop.social import SocialDialog

        self.social_dialog = SocialDialog(self)
        self.social_dialog.show()

    def waiting(self, active):
        self.busy = active
        self.composer.setEnabled(
            not active
            and self.loaded
            and not self.job
            and not self.unsaved_reply
            and not getattr(self, "pending_message", None)
        )
        self.workspace_context.setEnabled(not active)

    def request(self, operation, done):
        self.waiting(True)
        self.retry.hide()
        token = self.request_token = object()
        timer = QTimer(self)
        self.request_timer = timer
        timer.setSingleShot(True)

        def work():
            if self.closed:
                return {"error": True}
            try:
                value = operation()
                if self.closed and hasattr(value, "close_context"):
                    value.close_context()
                    return {"error": True}
                return {"value": value}
            except Exception:
                return {"error": True}

        def finished(result):
            if self.request_token is not token or not self.current():
                value = result.get("value")
                if hasattr(value, "close_context"):
                    value.close_context()
                return
            timer.stop()
            timer.deleteLater()
            if self.request_timer is timer:
                self.request_timer = None
            self.request_token = None
            self.waiting(False)
            if result.get("error"):
                self.set_loading(self.feed, False)
                self.status.setText(
                    "Couldn’t save or load this private conversation. Check your connection "
                    "and access, then retry. Contact support if this continues."
                )
                self.retry.show()
                return
            done(result["value"])

        timer.timeout.connect(lambda: finished({"error": True}))
        timer.start(30000)
        if not self.host.connected.enqueue("bud-chat-" + str(uuid4()), work, finished):
            finished({"error": True})

    def load(self):
        self.status.setText("")
        self.set_loading(self.feed, True, "feed")

        def loaded(rows):
            self.set_loading(self.feed, False)
            self.history = rows
            self.loaded = True
            self.render()
            self.composer.setEnabled(True)
            self.composer.editor.setFocus()
            if self.history and self.history[-1]["role"] == "user":
                self.status.setText("Your last question is saved. Retry to get a reply.")
                self.retry.show()

        self.request(
            lambda: self.service.rpc("bud_conversation", {"p_bud": self.bud["id"]}), loaded
        )

    def render(self):
        while self.rows.count():
            item = self.rows.takeAt(0)
            item.widget().deleteLater()
        pending = getattr(self, "pending_message", None)
        visible = self.history[-100:] + (
            [
                {
                    "role": "user",
                    "body": pending["p_body"],
                    "pending": True,
                }
            ]
            if pending
            else []
        )
        for row in visible:
            if row["role"] == "assistant":
                widget = ActivityRow(
                    row["body"],
                    author=self.bud["name"],
                    character_config=shelf_rows([self.bud])[0]["config"],
                )
                # Saved timestamps, rather than the time the conversation was reopened.
                sent = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00")).astimezone()
                widget.timestamp.setText(sent.strftime("%I:%M %p · %b %d"))
                widget.timestamp.setToolTip(sent.isoformat())
            else:
                widget = QWidget()
                column = QVBoxLayout(widget)
                column.setContentsMargins(28, 6, 20, 6)
                column.addWidget(
                    label("You · Sending…" if row.get("pending") else "You", "section")
                )
                body = label(row["body"], wrap=True)
                body.setTextInteractionFlags(
                    Qt.TextInteractionFlag.TextSelectableByMouse
                    | Qt.TextInteractionFlag.TextSelectableByKeyboard
                )
                body.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
                body.setMargin(2)
                column.addWidget(body)
            self.rows.addWidget(widget)
        if not visible:
            self.rows.addWidget(
                label(
                    "A little space to think together. Ask a question or work through an idea.",
                    "muted",
                    wrap=True,
                )
            )
        QTimer.singleShot(
            0,
            lambda: self.feed.verticalScrollBar().setValue(self.feed.verticalScrollBar().maximum()),
        )

    def send(self, text):
        text = text.strip()
        if (
            not self.current()
            or not self.loaded
            or self.busy
            or self.job
            or not text
            or self.unsaved_reply
            or getattr(self, "pending_message", None)
        ):
            return
        if len(text) > 20000:
            self.status.setText("Keep your message under 20,000 characters.")
            return
        from aedrova.security.credentials import credential_rules

        if credential_rules(text.encode()):
            self.status.setText("Remove credentials before sending this message.")
            return
        self.pending_message = {
            "p_id": str(uuid4()),
            "p_bud": self.bud["id"],
            "p_body": text,
        }
        self.composer.clear_submission(text)
        self.render()
        self.save_question()

    def save_question(self):
        message = self.pending_message
        self.status.setText("Sending…")

        def saved(row):
            self.history.append(row)
            self.pending_message = None
            self.render()
            self.answer(row)

        self.request(lambda: self.service.rpc("append_bud_message", message), saved)

    def retry_request(self):
        if self.busy or self.job:
            return
        if self.unsaved_reply:
            self.save_answer(self.unsaved_reply)
        elif getattr(self, "pending_message", None):
            self.save_question()
        elif self.history and self.history[-1]["role"] == "user":
            self.answer(self.history[-1])
        else:
            self.load()

    def answer(self, question):
        self.waiting(True)
        self.retry.hide()
        self.status.setText(self.bud["name"] + " is thinking…")
        include_workspace = self.workspace_context.isChecked()
        self.workspace_context.setChecked(False)

        def ready(service):
            if not self.current():
                service.close_context()
                return
            job = QueryJob(
                service,
                self.workspace,
                "",
                question["body"],
                binding(self.host).get("provider", "codex"),
                bud=self.bud,
                private_history=list(self.history),
                include_workspace=include_workspace,
            )
            self.job = job
            self.reply_preview = None
            self.waiting(True)
            self.stop.show()
            job.signals.reply.connect(lambda text: self.preview_reply(job, text))
            job.signals.finished.connect(lambda result: self.answered(question, result))
            QThreadPool.globalInstance().start(job)

        self.request(self.service.fork_for_context, ready)

    def preview_reply(self, job, text):
        if not self.current() or self.job is not job or job.runner.cancelled.is_set():
            return
        if self.reply_preview is None:
            self.reply_preview = ActivityRow(
                text,
                author=self.bud["name"],
                character_config=shelf_rows([self.bud])[0]["config"],
            )
            self.rows.addWidget(self.reply_preview)
        else:
            self.reply_preview.set_message(text)
        self.status.setText("Replying…")

    def answered(self, question, result):
        cancelled = self.job.runner.cancelled.is_set()
        self.job = None
        self.stop.hide()
        if not self.current():
            return
        self.waiting(False)
        if cancelled or result.get("error"):
            self.render()  # Partial replies are not saved or presented as completed answers.
            self.status.setText("Reply stopped." if cancelled else result["text"])
            self.retry.show()
            return
        self.unsaved_reply = {
            "p_id": str(uuid4()),
            "p_bud": self.bud["id"],
            "p_body": result["text"],
            "p_reply_to": question["id"],
        }
        self.save_answer(self.unsaved_reply)

    def save_answer(self, message):
        def saved(row):
            self.unsaved_reply = None
            self.history.append(row)
            self.status.setText("")
            self.waiting(False)
            self.render()
            self.composer.editor.setFocus()

        self.request(lambda: self.service.rpc("append_bud_message", message), saved)

    def cancel(self):
        if self.job:
            self.job.runner.cancel()

    def shutdown(self, *_):
        if self.closed:
            return
        self.closed = True
        self.host.account_dialog.session_closed.disconnect(self.reject)
        timer = getattr(self, "request_timer", None)
        if timer is not None:
            timer.stop()
            timer.deleteLater()
            self.request_timer = None
        self.set_loading(self.feed, False)
        self.guard.stop()
        self.cancel()
        self.history.clear()
        self.composer.clear()
        self.unsaved_reply = None
        self.pending_message = None
        self.render()


def open_bud_chat(window, bud_id):
    if not window.current_user() or not window.connected or not window.connected.active:
        window.notify("Sign in to talk privately with a Bud.")
        return
    bud = next(
        (
            r
            for r in window.account_dialog.snapshot.get("dots", [])
            if r["id"] == bud_id and r["workspace_id"] == window.workspace_id
        ),
        None,
    )
    if not bud:
        window.notify("This Bud is no longer available in your workspace.")
        return
    existing = getattr(window, "bud_chat", None)
    if existing and not existing.closed:
        if existing.bud["id"] == bud_id and existing.current():
            existing.show()
            existing.raise_()
            existing.composer.editor.setFocus()
            return
        existing.reject()
    window.bud_chat = BudChat(window, bud)
    window.bud_chat.open()
