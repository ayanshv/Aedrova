"""Compact agent transcript: public messages and expandable tool activity."""

import json
from datetime import datetime
from math import ceil
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from aedrova.desktop.brand import BrandMark
from aedrova.desktop.materials import system_font


class ActivityRow(QFrame):
    def __init__(
        self,
        summary,
        details="",
        *,
        tool=False,
        pending=False,
        author="Aedrova",
        character_config=None,
    ):
        super().__init__()
        self.sent_at = datetime.now().astimezone()
        self.summary = summary
        self.pending = pending
        self.status = "running" if pending else "done"
        if not pending and details.startswith("$ "):
            self.status = "done" if details.splitlines()[-1] == "Exit code: 0" else "failed"
        self.setObjectName("AgentMessage")
        if tool:
            outer = QVBoxLayout(self)
            outer.setContentsMargins(74, 2, 20, 10)
            container = QFrame()
            container.setObjectName("AgentTool")
            outer.addWidget(container)
            layout = QVBoxLayout(container)
            layout.setContentsMargins(12, 8, 12, 8)
        else:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(2, 4, 2, 8)
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
            self.details.document().documentLayout().documentSizeChanged.connect(self.resize_output)
            self.details.setPlainText(details[:20000])
            self.details.hide()
            layout.addWidget(self.details)
            self.expand(False)
        else:
            layout.setContentsMargins(28, 18, 20, 22)
            layout.setSpacing(6)
            body = QHBoxLayout()
            body.setSpacing(12)
            if character_config:
                from aedrova.desktop.ai_teammates import Character

                avatar = Character(character_config, reduced_motion=True)
                avatar.setFixedSize(34, 32)
            else:
                avatar = BrandMark(34)
            body.addWidget(avatar, 0, Qt.AlignmentFlag.AlignTop)
            column = QVBoxLayout()
            self.column = column
            column.setSpacing(6)
            header = QHBoxLayout()
            header.setSpacing(12)
            self.author = QLabel(author)
            self.author.setTextFormat(Qt.TextFormat.PlainText)
            self.author.setFont(system_font(14))
            self.author.setStyleSheet("font-weight: 600;")
            self.author.setAccessibleName("Agent sender: " + author)
            self.timestamp = QLabel(self.sent_at.strftime("%-I:%M %p · %b %-d"))
            self.timestamp.setProperty("role", "muted")
            self.timestamp.setFont(system_font(11))
            self.timestamp.setToolTip(self.sent_at.strftime("%A, %B %-d, %Y at %-I:%M:%S %p %Z"))
            header.addWidget(self.author)
            header.addWidget(self.timestamp)
            header.addStretch()
            column.addLayout(header)
            self.message = QLabel(summary)
            self.message.setTextFormat(Qt.TextFormat.PlainText)
            self.message.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self.message.setWordWrap(True)
            self.message.setAccessibleName("Agent update")
            self.message.setFont(system_font(14))
            self.message.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            column.addWidget(self.message)
            body.addLayout(column, 1)
            layout.addLayout(body)

    def resize_output(self, size):
        height = ceil(size.height() * self.details.fontMetrics().lineSpacing()) + 16
        self.details.setFixedHeight(min(160, max(60, height)))

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
    changed = Signal()

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
        self.status_row = None
        self.status_controls = None
        self.author_name = "Aedrova"
        self.character_config = None
        self.inline = False
        self.rows = []
        self.running = {}
        self.scroll_timer = QTimer(self)
        self.scroll_timer.setSingleShot(True)
        self.scroll_timer.timeout.connect(self.scroll_latest)
        self.hide()

    def sizeHint(self):  # noqa: N802
        return QSize(600, self.height() if self.inline else 230)

    def minimumSizeHint(self):  # noqa: N802
        return QSize(100, self.height() if self.inline else 70)

    def clear(self):
        self.scroll_timer.stop()
        if self.status_controls:
            self.status_controls.hide()
            self.status_controls.setParent(self)
        self.status_row = None
        for row in self.rows:
            self.layout.removeWidget(row)
            row.hide()
            row.deleteLater()
        self.rows.clear()
        self.running.clear()
        self.changed.emit()

    def toPlainText(self):  # noqa: N802
        return "\n".join(row.summary for row in self.rows)

    def appendPlainText(self, text):  # noqa: N802
        self.add_row(
            ActivityRow(
                text[:50000], author=self.author_name, character_config=self.character_config
            )
        )

    def add_row(self, row):
        bar = self.verticalScrollBar()
        follow = bar.value() >= bar.maximum() - 8
        self.rows.append(row)
        self.layout.addWidget(row)
        if len(self.rows) > 100:
            old = self.rows.pop(1 if self.rows[0] is self.status_row else 0)
            self.running = {key: value for key, value in self.running.items() if value is not old}
            self.layout.removeWidget(old)
            old.hide()
            old.deleteLater()
        if row.toggle:
            row.toggle.toggled.connect(lambda *_: self.changed.emit())
        self.show()
        self.changed.emit()
        if follow:
            self.scroll_timer.start(0)

    def scroll_latest(self):
        if self.inline:
            return
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
                self.changed.emit()
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

    def make_inline(self):
        self.inline = True
        self.setMaximumHeight(16777215)
        self.setMinimumHeight(0)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)

    def content_height(self, width):
        self.widget().setFixedWidth(max(100, width))
        self.layout.invalidate()
        self.layout.activate()
        heights = []
        for row in self.rows:
            row_layout = row.layout()
            row_layout.invalidate()
            row_height = row_layout.totalHeightForWidth(max(100, width))
            heights.append(row_height if row_height >= 0 else row_layout.sizeHint().height())
        height = max(1, sum(heights) + self.layout.spacing() * max(0, len(heights) - 1))
        if self.inline:
            # A scroll area otherwise retains its previous viewport/content height
            # after a long transcript is replaced by a short final response. The
            # conversation owns scrolling; both must match the live row exactly.
            self.widget().setFixedHeight(height)
            self.setFixedHeight(height)
        return height

    def install_status_controls(self, controls):
        self.status_controls = controls
        controls.setParent(self)
        controls.hide()

    def set_status(self, author, text):
        self.author_name = author
        if self.status_row is None:
            self.status_row = ActivityRow(
                text, author=author, character_config=self.character_config
            )
            self.status_row.message.hide()
            self.status_row.column.addWidget(self.status_controls)
            self.status_controls.show()
            self.add_row(self.status_row)
        else:
            self.status_row.summary = text
            self.changed.emit()

    def finish_with_result(self, text):
        self.clear()
        self.appendPlainText(text)
