"""Cancellable upload state inside the originating composer, never a global footer."""

from threading import Event

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout

from aedrova.desktop.dialogs import button


class UploadProgress(QFrame):
    updated = Signal(str)

    def __init__(self, composer, name):
        super().__init__(composer)
        self.setObjectName("UploadProgress")
        self.cancelled = Event()
        self.label = QLabel(name)
        self.label.setWordWrap(True)
        self.label.setTextFormat(self.label.textFormat().PlainText)
        self.state = QLabel("Waiting to upload…")
        self.state.setProperty("role", "muted")
        self.cancel_button = button("Cancel", "Cancel this upload", "icon")
        self.cancel_button.clicked.connect(self.cancel)
        self.meter = QProgressBar()
        self.meter.setObjectName("UploadMeter")
        self.meter.setRange(0, 0)
        self.meter.setTextVisible(False)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        row = QHBoxLayout()
        row.addWidget(self.label, 1)
        row.addWidget(self.cancel_button)
        layout.addLayout(row)
        layout.addWidget(self.state)
        layout.addWidget(self.meter)
        self.updated.connect(self.progress)
        composer.layout().insertWidget(composer.layout().count() - 1, self)

    def progress(self, value):
        if not self.cancelled.is_set():
            self.state.setText(value)
        if value == "Verifying before sharing…":
            # Publication may already be committing; do not promise cancellation then.
            self.cancel_button.setEnabled(False)

    def cancel(self):
        self.cancelled.set()
        self.state.setText("Cancelling · waiting for the current transfer to stop…")
        self.cancel_button.setEnabled(False)

    def complete(self, text):
        self.state.setText(text)
        self.meter.hide()
        self.cancel_button.setEnabled(True)
        self.cancel_button.setText("Dismiss")
        self.cancel_button.clicked.disconnect()
        self.cancel_button.clicked.connect(self.deleteLater)
