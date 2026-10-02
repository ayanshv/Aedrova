"""Compact agent transcript: public messages and expandable tool activity."""

import json
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class ActivityRow(QFrame):
    def __init__(self, summary, details="", *, tool=False, pending=False):
        super().__init__()
        self.summary = summary
        self.pending = pending
        self.status = "running" if pending else "done"
        if not pending and details.startswith("$ "):
            self.status = "done" if details.splitlines()[-1] == "Exit code: 0" else "failed"
        self.setObjectName("AgentTool" if tool else "AgentMessage")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8) if tool else layout.setContentsMargins(2, 4, 2, 8)
        layout.setSpacing(6)
        self.toggle = None
        self.details = None
        if tool:
            self.toggle = QPushButton()
            self.toggle.setObjectName("AgentDisclosure")
            self.toggle.setCheckable(True)
            self.toggle.setCursor(Qt.CursorShape.PointingHandCursor)
            self.toggle.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
            self.toggle.setMinimumHeight(28)
            self.toggle.setAccessibleName("Expand command activity")
            self.toggle.toggled.connect(self.expand)
            layout.addWidget(self.toggle)
            self.details = QPlainTextEdit()
            self.details.setReadOnly(True)
            self.details.setObjectName("AgentCommandOutput")
            self.details.setAccessibleName("Command and output")
            self.details.setMaximumHeight(160)
            self.details.setPlainText(details[:20000])
            self.details.hide()
            layout.addWidget(self.details)
            self.expand(False)
        else:
            self.message = QLabel(summary)
            self.message.setTextFormat(Qt.TextFormat.PlainText)
            self.message.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.message.setWordWrap(True)
            self.message.setAccessibleName("Agent update")
            layout.addWidget(self.message)

    def expand(self, expanded):
        marker = {"running": "◦", "done": "✓", "failed": "!", "stopped": "□"}[self.status]
        self.toggle.setText(f"{'▾' if expanded else '▸'}  {marker}  {self.summary}")
        self.toggle.setToolTip(self.summary)
        self.details.setVisible(expanded)
        self.toggle.setAccessibleDescription("Expanded" if expanded else "Collapsed")

    def complete(self, summary, details):
        self.summary, self.pending = summary, False
        self.status = "done" if details.splitlines()[-1] == "Exit code: 0" else "failed"
        self.details.setPlainText(details[:20000])
        self.expand(self.toggle.isChecked())


class AgentStream(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setObjectName("AgentStream")
        self.setAccessibleName("Agent updates and actions")
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setMaximumHeight(230)
        self.setMinimumHeight(70)
        content = QWidget()
        content.setObjectName("AgentStreamContent")
        self.layout = QVBoxLayout(content)
        self.layout.setContentsMargins(2, 0, 8, 0)
        self.layout.setSpacing(7)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.setWidget(content)
        self.rows = []
        self.running = {}
        self.scroll_timer = QTimer(self)
        self.scroll_timer.setSingleShot(True)
        self.scroll_timer.timeout.connect(self.scroll_latest)
        self.hide()

    def sizeHint(self):  # noqa: N802
        return QSize(600, 230)

    def minimumSizeHint(self):  # noqa: N802
        return QSize(100, 70)

    def clear(self):
        self.scroll_timer.stop()
        for row in self.rows:
            self.layout.removeWidget(row)
            row.deleteLater()
        self.rows.clear()
        self.running.clear()

    def toPlainText(self):  # noqa: N802
        return "\n".join(row.summary for row in self.rows)

    def appendPlainText(self, text):  # noqa: N802
        self.add_row(ActivityRow(text[:1400]))

    def add_row(self, row):
        bar = self.verticalScrollBar()
        follow = bar.value() >= bar.maximum() - 8
        self.rows.append(row)
        self.layout.addWidget(row)
        if len(self.rows) > 100:
            old = self.rows.pop(0)
            self.running = {key: value for key, value in self.running.items() if value is not old}
            self.layout.removeWidget(old)
            old.deleteLater()
        self.show()
        if follow:
            self.scroll_timer.start(0)

    def scroll_latest(self):
        bar = self.verticalScrollBar()
        bar.setValue(bar.maximum())

    def finish_pending(self):
        for row in self.running.values():
            row.pending = False
            row.status = "stopped"
            row.summary = "Ended · " + row.summary.removeprefix("Running ")
            row.expand(row.toggle.isChecked())
        self.running.clear()

    def add_event(self, text):
        if text.startswith("Running:"):
            command = text.removeprefix("Running:").strip()
            row = ActivityRow("Running " + command[:180], command, tool=True, pending=True)
            self.running[command] = row
            self.add_row(row)
        elif text.startswith("$ "):
            lines = text.splitlines()
            command = lines[0][2:]
            code = lines[-1] if lines[-1].startswith("Exit code:") else "Command finished"
            summary = command[:180] + " · " + code
            row = self.running.pop(command, None)
            if row:
                row.complete(summary, text)
            else:
                self.add_row(ActivityRow(summary, text, tool=True))
        elif text.startswith("Files changed:"):
            try:
                files = json.loads(text.split(":", 1)[1])
                names = [Path(item["path"]).name for item in files]
                summary = "Edited " + ", ".join(names[:6])
                details = "\n".join(str(item["path"]) for item in files)
            except (ValueError, TypeError, KeyError):
                summary, details = "Updated project files", text
            self.add_row(ActivityRow(summary, details, tool=True))
        else:
            self.appendPlainText(text)
