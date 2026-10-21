"""Compact, cancellable attachment feedback in the originating composer."""

import re
from threading import Event

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout

from aedrova.desktop.dialogs import button


class UploadProgress(QFrame):
    updated = Signal(str)

    def __init__(self, composer, name):
        super().__init__(composer)
        self.setObjectName("UploadProgress")
        self.cancelled = Event()
        self.finished = False
        self.label = QLabel(name)
        self.label.setWordWrap(True)
        self.label.setTextFormat(Qt.TextFormat.PlainText)
        self.state = QLabel("Queued")
        self.state.setProperty("role", "muted")
        self.cancel_button = button("×", "Cancel this upload", "icon")
        self.cancel_button.setFixedSize(28, 28)
        self.cancel_button.clicked.connect(self.cancel)
        self.meter = QProgressBar()
        self.meter.setObjectName("UploadMeter")
        self.meter.setRange(0, 0)
        self.meter.setTextVisible(False)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 6, 6)
        layout.setSpacing(3)
        row = QHBoxLayout()
        row.addWidget(self.label, 1)
        row.addWidget(self.state)
        row.addWidget(self.cancel_button)
        layout.addLayout(row)
        layout.addWidget(self.meter)
        self.updated.connect(self.progress)
        composer.layout().insertWidget(composer.layout().count() - 1, self)

    def progress(self, value):
        if self.finished or self.cancelled.is_set():
            return
        self.state.setText(value)
        match = re.fullmatch(r"Uploading · (\d+)%", value)
        if match:
            self.meter.setRange(0, 100)
            self.meter.setValue(min(100, int(match[1])))
        else:
            self.meter.setRange(0, 0)
        if value == "Verifying before sharing…":
            self.state.setText("Checking file…")
            self.cancel_button.setEnabled(False)

    def cancel(self):
        if self.finished:
            return
        self.cancelled.set()
        self.state.setText("Cancelling…")
        self.cancel_button.setEnabled(False)

    def complete(self, text, *, success=False):
        self.finished = True
        self.state.setText("Shared ✓" if success else text)
        self.state.setToolTip(text)
        self.meter.hide()
        self.cancel_button.setEnabled(True)
        self.cancel_button.setToolTip("Dismiss upload status")
        self.cancel_button.setAccessibleName("Dismiss upload status")
        self.cancel_button.clicked.disconnect()
        self.cancel_button.clicked.connect(self.deleteLater)
        if success or text == "Upload cancelled":
            QTimer.singleShot(2400 if success else 600, self.deleteLater)
