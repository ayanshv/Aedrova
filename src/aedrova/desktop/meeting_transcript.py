"""Permission-scoped transcript review. Provider text is never implicitly a decision."""

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, Signal
from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QListWidget, QPlainTextEdit, QVBoxLayout

from aedrova.desktop.controls import AppDialog, ChoiceBox
from aedrova.desktop.dialogs import button, label


class ReviewSignals(QObject):
    result = Signal(object)


class ReviewJob(QRunnable):
    def __init__(self, operation):
        super().__init__()
        self.operation, self.signals = operation, ReviewSignals()

    def run(self):
        try:
            result = {'value': self.operation()}
        except Exception:
            result = {'error': 'Could not load or save this transcript. Your access, consent '
                               'or its version may have changed. Refresh and try again.'}
        self.signals.result.emit(result)


class TranscriptReview(AppDialog):
    def __init__(self, parent, client, *, meeting=None, channel=None):
        super().__init__(parent)
        self.client, self.meeting, self.channel = client, meeting, channel
        self.rows, self.page, self.busy, self.closed = [], 0, False, False
        self.jobs = []
        self.setWindowTitle('Meeting transcript · Aedrova')
        self.resize(900, 760)
        self.setMinimumSize(620, 620)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)
        layout.addWidget(label('From conversation to shared context.', 'heading', wrap=True))
        layout.addWidget(label('Review speech before your agent uses it. Corrections keep the '
            'original text and citation. Confirm a decision only when your team agreed. '
            'Account attribution identifies the microphone sender, not a verified voice.',
            'muted', wrap=True))
        self.meetings = ChoiceBox(self)
        self.meetings.setAccessibleName('Meeting to review')
        self.meetings.setVisible(channel is not None)
        self.meetings.currentIndexChanged.connect(self.change_meeting)
        layout.addWidget(self.meetings)
        self.status = label('Loading permitted meeting text…', 'muted', wrap=True)
        layout.addWidget(self.status)
        self.sources = QListWidget()
        self.sources.setProperty('accountList', True)
        self.sources.setWordWrap(True)
        self.sources.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.sources.setAccessibleName('Transcript segments')
        layout.addWidget(self.sources, 1)
        layout.addWidget(label("Original text and source", "muted"))
        self.original = QPlainTextEdit()
        self.original.setReadOnly(True)
        self.original.setAccessibleName('Original speech and citation')
        self.original.setMaximumHeight(140)
        layout.addWidget(self.original)
        layout.addWidget(label("Reviewed text", "muted"))
        self.edit = QPlainTextEdit()
        self.edit.setAccessibleName('Reviewed transcript text')
        layout.addWidget(self.edit, 1)
        self.decision = QCheckBox('Confirm this reviewed text as an agreed decision')
        layout.addWidget(self.decision)
        privacy = QHBoxLayout()
        self.withdraw = button('Withdraw AI access', role='outline')
        self.delete = button('Delete shared text', role='outline')
        self.withdraw.clicked.connect(lambda: self.withdraw_text(False))
        self.delete.clicked.connect(lambda: self.withdraw_text(True))
        privacy.addWidget(self.withdraw)
        privacy.addWidget(self.delete)
        privacy.addStretch()
        layout.addLayout(privacy)
        actions = QHBoxLayout()
        self.previous = button('Previous', role='outline')
        self.next = button('Next', role='outline')
        self.refresh = button('Refresh', role='outline')
        self.save = button('Save reviewed text', role='primary')
        done = button('Done', role='outline')
        for control in (self.previous, self.next, self.refresh, self.save, done):
            actions.addWidget(control)
        layout.addLayout(actions)
        self.previous.clicked.connect(lambda: self.turn(-1))
        self.next.clicked.connect(lambda: self.turn(1))
        self.refresh.clicked.connect(self.load)
        self.save.clicked.connect(self.review)
        done.clicked.connect(self.accept)
        self.sources.currentRowChanged.connect(self.selected)
        self.edit.textChanged.connect(self.enable_save)
        self.finished.connect(self.finish)
        # Clear displayed text immediately when an account session closes.
        window = parent
        while window is not None:
            account = getattr(window, 'account_dialog', None)
            if account is not None and hasattr(account, 'session_closed'):
                account.session_closed.connect(self.reject)
                break
            window = window.parent()
        self.selected()
        if channel:
            self.run(lambda: client.history(channel), self.loaded_meetings)
        else:
            self.load()

    def finish(self, *_):
        self.closed = True
        self.rows.clear()
        self.sources.clear()
        self.original.clear()
        self.edit.clear()

    def run(self, operation, callback):
        if self.busy or self.closed:
            return
        self.busy = True
        self.enable_save()
        for control in (self.refresh, self.previous, self.next, self.meetings):
            control.setEnabled(False)
        job = ReviewJob(operation)
        self.jobs.append(job)

        def received(result):
            self.jobs.remove(job)
            if self.closed:
                return
            self.busy = False
            self.refresh.setEnabled(True)
            self.meetings.setEnabled(True)
            if 'error' in result:
                # Do not retain stale private evidence when authorization may have failed.
                self.rows.clear()
                self.sources.clear()
                self.original.clear()
                self.edit.clear()
                self.status.setText(result['error'])
            else:
                callback(result['value'])
            self.previous.setEnabled(not self.busy and self.page > 0)
            self.next.setEnabled(not self.busy and len(self.rows) == 50 and self.page < 199)
            self.enable_save()
        job.signals.result.connect(received)
        QThreadPool.globalInstance().start(job)

    def loaded_meetings(self, rows):
        self.meetings.blockSignals(True)
        for row in rows[:50]:
            self.meetings.addItem(row['title'] + ' · ' + row['started_at'][:16], row['id'])
        self.meetings.blockSignals(False)
        self.change_meeting()

    def change_meeting(self, *_):
        self.meeting = self.meetings.currentData()
        self.page = 0
        self.load()

    def turn(self, direction):
        if not self.busy:
            self.page = max(0, min(199, self.page + direction))
            self.load()

    def load(self):
        if self.busy or self.closed:
            return
        self.rows.clear()
        self.sources.clear()
        if not self.meeting:
            self.status.setText('No permitted meetings yet.')
            return
        self.run(lambda: self.client.transcript(self.meeting, self.page), self.loaded)

    def loaded(self, rows):
        self.rows = rows[:50]
        for row in self.rows:
            state = ('Decision' if row.get('confirmed_decision') else
                     'Reviewed' if row.get('reviewed_at') else 'Needs review')
            self.sources.addItem(f"{row['offset_ms']//1000}s · {state} · "
                + (row.get('review_body') or row['body'])[:150])
        self.status.setText(f'Page {self.page + 1} · {len(self.rows)} segments. '
                            'Expired or withdrawn text is unavailable.' if rows else
                            'No saved text on this page. Transcription may be off or withdrawn.')
        if rows:
            self.sources.setCurrentRow(0)
        self.selected()

    def selected(self, *_):
        index = self.sources.currentRow()
        row = self.rows[index] if 0 <= index < len(self.rows) else None
        self.original.setPlainText('' if row is None else
            f"[meeting:{row['id']}] · {row['speaker_id']}\n" + row['body'])
        self.edit.setPlainText('' if row is None else row.get('review_body') or row['body'])
        self.decision.setChecked(bool(row and row.get('confirmed_decision')))
        self.edit.setEnabled(row is not None)
        self.decision.setEnabled(row is not None)
        self.enable_save()

    def enable_save(self):
        for control in (self.withdraw, self.delete):
            control.setEnabled(not self.busy and not self.closed and bool(self.meeting))
        self.save.setEnabled(not self.busy and not self.closed
            and 0 <= self.sources.currentRow() < len(self.rows)
            and 1 <= len(self.edit.toPlainText().strip()) <= 2000)

    def review(self):
        index = self.sources.currentRow()
        if self.busy or not 0 <= index < len(self.rows):
            return
        row, body = self.rows[index], self.edit.toPlainText().strip()
        if not 1 <= len(body) <= 2000:
            return
        decision = self.decision.isChecked()
        self.run(lambda: self.client.review(row['id'], row.get('review_version', 0),
                                           body, decision), lambda _: self.load())

    def withdraw_text(self, delete):
        if self.busy or not self.meeting:
            return
        confirm = AppDialog(self)
        confirm.setWindowTitle('Delete shared text?' if delete else 'Withdraw AI access?')
        layout = QVBoxLayout(confirm)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addWidget(label('This affects everyone’s saved text from this meeting. '
            'It cannot recall context already sent to a provider.' +
            (' Deletion is permanent.' if delete else ''), 'muted', wrap=True))
        controls = QHBoxLayout()
        cancel = button('Cancel', role='outline')
        proceed = button('Delete text' if delete else 'Withdraw access', role='primary')
        cancel.clicked.connect(confirm.reject)
        proceed.clicked.connect(confirm.accept)
        controls.addWidget(cancel)
        controls.addWidget(proceed)
        layout.addLayout(controls)
        if confirm.exec():
            meeting = self.meeting
            self.run(lambda: self.client.withdraw_text(meeting, delete), lambda _: self.load())


def open_transcript_history(window):
    from aedrova.agents.managed import application_origin
    from aedrova.meetings.access import MeetingClient
    if not window.connected or not window.connected.active:
        window.notify('Sign in and open a workspace to review meeting text.')
        return
    origin = application_origin()
    if not origin:
        window.notify('The Aedrova meeting service is not configured yet.')
        return
    service = window.account_dialog.service
    token = service.client.auth.get_session().access_token
    dialog = TranscriptReview(window, MeetingClient(origin, token), channel=window.channel_id)
    dialog.show()
