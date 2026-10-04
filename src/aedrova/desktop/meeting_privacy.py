"""Explicit per-participant meeting-text consent. No audio capture is started here."""

from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QVBoxLayout

from aedrova.desktop.controls import AppDialog
from aedrova.desktop.dialogs import button, label


class MeetingPrivacy(AppDialog):
    def __init__(self, parent, worker, snapshot):
        super().__init__(parent)
        self.setWindowTitle("Meeting privacy · Aedrova")
        self.resize(560, 540)
        self.setMinimumSize(520, 540)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)
        layout.addWidget(label("Your meeting text. Your choice.", "title", wrap=True))
        layout.addWidget(
            label(
                ("With everyone's consent, Start transcription sends short microphone chunks "
                 "to OpenAI for speech-to-text. Raw audio is not saved by Aedrova. "
                 "Each participant "
                 "must start their own transcription and unmute. Processing may leave gaps. "
                 "Provider data handling applies; already-sent audio cannot be recalled."
                 if getattr(worker, "speech_available", False) else
                 "Audio transcription is not connected. These permissions apply to participant "
                 "text supplied during a call. No audio or video recording starts here."),
                "muted",
                wrap=True,
            )
        )
        self.transcription = QCheckBox("Allow shared meeting text to be saved for 30 days")
        self.ai_context = QCheckBox("Also allow eligible text as context for the team’s agent")
        layout.addWidget(self.transcription)
        layout.addWidget(self.ai_context)
        current = next(
            (
                p
                for p in (snapshot or {}).get("participants", [])
                if p.get("user_id") == worker.user
            ),
            {},
        )
        self.transcription.setChecked(current.get("transcription") is True)
        self.ai_context.setChecked(current.get("ai_context") is True)
        self.ai_context.setEnabled(self.transcription.isChecked())
        self.transcription.toggled.connect(self.sync_choices)
        layout.addWidget(
            label(
                "Every present participant must approve saving. AI reuse requires separate "
                "approval from everyone. Leaving ends future capture; saved text keeps its prior "
                "consent until expiry or explicit withdrawal. Withdrawal affects all shared text "
                "from this meeting and cannot recall context already sent to a provider.",
                "muted",
                wrap=True,
            )
        )
        withdraw_ai = button("Withdraw AI access to saved meeting text", role="outline")
        withdraw_ai.clicked.connect(lambda: self.withdraw(worker, False))
        layout.addWidget(withdraw_ai)
        delete = button("Delete saved meeting text for everyone", role="outline")
        delete.clicked.connect(lambda: self.confirm_delete(worker))
        layout.addWidget(delete)
        actions = QHBoxLayout()
        cancel = button("Cancel", role="outline")
        cancel.clicked.connect(self.reject)
        save = button("Save my choices", role="primary")
        save.clicked.connect(lambda: self.save(worker))
        actions.addWidget(cancel)
        actions.addWidget(save)
        layout.addLayout(actions)

    def sync_choices(self, checked):
        self.ai_context.setEnabled(checked)
        if not checked:
            self.ai_context.setChecked(False)

    def save(self, worker):
        worker.command(
            "consent",
            {
                "transcription": self.transcription.isChecked(),
                "ai_context": self.ai_context.isChecked(),
            },
        )
        self.accept()

    def withdraw(self, worker, delete):
        worker.command("withdraw_text", {"delete": delete})
        self.accept()

    def confirm_delete(self, worker):
        confirmation = AppDialog(self)
        confirmation.setWindowTitle("Delete shared meeting text?")
        layout = QVBoxLayout(confirmation)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addWidget(
            label(
                "This permanently deletes all saved text from this meeting "
                "for everyone. It cannot be undone.",
                wrap=True,
            )
        )
        cancel = button("Keep meeting text", role="outline")
        cancel.clicked.connect(confirmation.reject)
        delete = button("Delete for everyone", role="primary")
        delete.clicked.connect(confirmation.accept)
        layout.addWidget(cancel)
        layout.addWidget(delete)
        if confirmation.exec():
            self.withdraw(worker, True)
