"""Compact agent transcript: public messages and expandable tool activity."""

import json
import webbrowser
from datetime import datetime
from math import ceil
from pathlib import Path
from urllib.parse import urlsplit
from uuid import uuid4

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
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

from aedrova.desktop.agent_activity import activity_icon
from aedrova.desktop.agent_components import (
    ApprovalCard,
    ChoiceCard,
    FourDots,
    PromptCard,
    StepChecklist,
    StepSummary,
)
from aedrova.desktop.brand import BrandMark
from aedrova.desktop.conversation import human_time
from aedrova.desktop.icons import assign
from aedrova.desktop.materials import system_font


class ActivityRow(QFrame):
    reply_action = Signal(object, str)

    def __init__(
        self,
        summary,
        details="",
        *,
        tool=False,
        pending=False,
        author="Aedrova",
        character_config=None,
        markdown=True,
        streaming=False,
    ):
        super().__init__()
        self.sent_at = datetime.now().astimezone()
        self.summary = summary
        self.character_config = dict(character_config) if character_config else None
        self.response_id = None
        self.rating = ""
        self.copied = False
        self.file_summary = None
        self.streaming = streaming
        self.choice_card = None
        self.actions_label = None
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
            layout.setContentsMargins(28, 10, 20, 12)
            layout.setSpacing(6)
            body = QHBoxLayout()
            body.setSpacing(12)
            if self.character_config:
                from aedrova.desktop.ai_teammates import Character

                avatar = Character(
                    self.character_config,
                    reduced_motion=QApplication.instance().property("reduceMotion") is True,
                )
                avatar.setFixedSize(34, 32)
            else:
                avatar = BrandMark(34)
            body.addWidget(avatar, 0, Qt.AlignmentFlag.AlignTop)
            column = QVBoxLayout()
            self.column = column
            column.setSpacing(6)
            header = QHBoxLayout()
            self.header = header
            header.setSpacing(12)
            self.author = QLabel(author)
            self.author.setTextFormat(Qt.TextFormat.PlainText)
            self.author.setFont(system_font(14))
            self.author.setStyleSheet("font-weight: 600;")
            self.author.setAccessibleName("Agent sender: " + author)
            self.timestamp = QLabel(human_time(self.sent_at.strftime("%Y-%m-%d %H:%M")))
            self.timestamp.setProperty("role", "muted")
            self.timestamp.setObjectName("MessageTimestamp")
            self.timestamp.setFont(system_font(11))
            self.timestamp.setToolTip(self.sent_at.strftime("%A, %B %d, %Y at %I:%M:%S %p %Z"))
            header.addWidget(self.author)
            identity = QLabel("Agent")
            identity.setObjectName("AgentIdentity")
            identity.setAccessibleName("Agent")
            header.addWidget(identity)
            header.addWidget(self.timestamp)
            header.addStretch()
            column.addLayout(header)
            self.message = QLabel(summary)
            self.message.setFont(system_font(14))
            if markdown:
                self.message.setTextFormat(Qt.TextFormat.RichText)
                self.set_message(summary)
            else:
                self.message.setTextFormat(Qt.TextFormat.PlainText)
            self.message.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
                | Qt.TextInteractionFlag.TextSelectableByKeyboard
                | Qt.TextInteractionFlag.LinksAccessibleByMouse
                | Qt.TextInteractionFlag.LinksAccessibleByKeyboard
            )
            self.message.linkActivated.connect(self.open_source)
            self.message.linkHovered.connect(self.show_action_tooltip)
            self.message.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            self.message.setMargin(0)
            self.message.setWordWrap(True)
            self.message.setAccessibleName("Agent update")
            self.message.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
            column.addWidget(self.message)
            body.addLayout(column, 1)
            layout.addLayout(body)

    def set_message(self, text):


        from aedrova.desktop.conversation import markdown_html
        from aedrova.desktop.response_actions import long_reply, response_parts, streaming_body

        body = streaming_body(text) if self.streaming else text
        options = None
        long_words = None
        if self.response_id:
            body, options = response_parts(text)
            shortened = None if self.streaming else long_reply(body)
            if shortened:
                body, long_words = shortened
        self.message.setProperty("aedrovaSourceText", body)
        self.message.setProperty("aedrovaReplyOptions", options)
        self.message.setProperty("aedrovaReplyRating", self.rating)
        self.message.setProperty("aedrovaFileSummary", self.file_summary)
        self.message.setProperty("aedrovaTranslatingStream", self.streaming or self.pending)
        self.message.setProperty("aedrovaPlainReply", self.choice_card is not None)
        if self.choice_card is not None:
            # Choices are buttons below the answer, so the text carries no links.
            self.message.setText(markdown_html(body, base_font=self.message.font(), agent=True))
            self.actions_label.setText(
                markdown_html(
                    "", base_font=self.message.font(), agent=True, options=(),
                    rating=self.rating, file_summary=self.file_summary, copied=self.copied,
                    long_words=long_words,
                )
            )
            return
        self.message.setText(
            markdown_html(
                body, base_font=self.message.font(), agent=True, options=options,
                rating=self.rating, file_summary=self.file_summary, copied=self.copied,
                long_words=long_words,
            )
        )

    def install_choices(self, options):
        """Replace the choice links with buttons and a text box under the answer."""
        if self.choice_card is not None or not options:
            return None
        self.choice_card = ChoiceCard(options)
        self.actions_label = QLabel()
        self.actions_label.setTextFormat(Qt.TextFormat.RichText)
        self.actions_label.setFont(system_font(14))
        self.actions_label.linkActivated.connect(self.open_source)
        self.actions_label.linkHovered.connect(self.show_action_tooltip)
        self.actions_label.setAccessibleName("Response actions")
        self.actions_label.setFixedHeight(32)
        self.actions_label.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)
        index = self.column.indexOf(self.message) + 1
        self.column.insertWidget(index, self.choice_card)
        self.column.insertWidget(index + 1, self.actions_label)
        return self.choice_card

    def show_action_tooltip(self, link):
        from aedrova.desktop.response_actions import HoverTip, reply_action_label

        if getattr(self, "hover_tip", None) is None:
            self.hover_tip = HoverTip(self)
        label = reply_action_label(link, copied=self.copied, rating=self.rating)
        if self.response_id and label:
            self.hover_tip.move((link, label), label, self.message)
        else:
            self.hover_tip.leave()

    def open_source(self, value):
        from aedrova.desktop.response_actions import ACTION_PREFIX, SOURCE_PREFIX

        if value.startswith((ACTION_PREFIX, SOURCE_PREFIX)):
            if self.response_id:
                self.reply_action.emit(self, value)
            return
        try:
            parsed = urlsplit(value)
            if (
                parsed.scheme == "https"
                and parsed.hostname
                and not (parsed.username or parsed.password)
            ):
                webbrowser.open(value)
        except ValueError:
            return

    def resize_output(self, size):
        height = ceil(size.height() * self.details.fontMetrics().lineSpacing()) + 16
        self.details.setFixedHeight(min(160, max(60, height)))

    def expand(self, expanded):
        marker = {"running": "◦", "done": "✓", "failed": "!", "stopped": "□"}[self.status]
        assign(self.toggle, activity_icon(self.summary))
        self.toggle.setText(f"{marker}  {self.summary}")
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
    reply_action = Signal(object, str)
    choice_requested = Signal(str, str, bool)

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
        self.resolve_cards()
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
                text[:50000],
                author=self.author_name,
                character_config=self.character_config,
                markdown=False,
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
        checklist = getattr(self.status_row, "checklist", None)
        if checklist is not None:
            checklist.observe(text)  # steps and commands live in the task list, once
            return
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



            self.widget().setFixedHeight(height)
            self.setFixedHeight(height)
        return height

    def add_approval(self, tool, data):
        """An inline Allow once / Deny card. The caller waits for `decided`."""
        card = ApprovalCard(tool, data)
        self.add_row(card)
        return card

    def add_prompt(self, question):
        """The agent's clarifying question as buttons and a text box."""
        card = PromptCard(question)
        self.add_row(card)
        card.focus_first()
        return card

    def remove_row(self, row):
        if row in self.rows:
            self.rows.remove(row)
        self.layout.removeWidget(row)
        row.hide()
        row.deleteLater()
        self.changed.emit()

    def cards(self):
        return [row for row in self.rows if isinstance(row, (ApprovalCard, PromptCard))]

    def resolve_cards(self):
        """Deny anything still waiting, so no run is left blocked on a hidden card."""
        for card in self.cards():
            if isinstance(card, ApprovalCard) and not card.resolved:
                card.resolve(False)

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
            if self.status_controls is not None:
                self.status_row.column.addWidget(self.status_controls)
                self.status_controls.show()
            self.status_row.dots = FourDots()
            header = self.status_row.header
            header.insertWidget(header.count() - 1, self.status_row.dots)
            self.status_row.checklist = StepChecklist()
            self.status_row.checklist.changed.connect(self.changed)
            self.status_row.column.addWidget(self.status_row.checklist)
            self.status_row.checklist.observe(text)
            self.add_row(self.status_row)
        else:
            self.status_row.summary = text
            self.status_row.checklist.observe(text)

    def record_work(self, text):
        """The task list is the single record of progress; no repeated sentences."""
        return False

    def retire_status(self):
        """Fold the live status row into the answer so nothing jumps when it arrives."""
        steps = []
        row = self.status_row
        if row is None:
            return steps
        if getattr(row, "checklist", None):
            row.checklist.finish()
            steps = [dict(s) for s in row.checklist.steps]
        self.layout.removeWidget(row)
        if row in self.rows:
            self.rows.remove(row)
        if self.status_controls:
            self.status_controls.hide()
            self.status_controls.setParent(self)
        row.hide()
        row.deleteLater()
        self.status_row = None
        return steps

    def attach_summary(self, steps):
        reply = getattr(self, "reply_row", None)
        if reply is None or len(steps) < 2 or getattr(reply, "step_summary", None):
            return
        summary = StepSummary(steps)
        summary.changed.connect(self.changed)
        reply.step_summary = summary
        reply.column.insertWidget(1, summary)

    def finish_with_result(self, text, *, file_summary=None):
        self.resolve_cards()
        content = self.widget()
        content.setUpdatesEnabled(False)  # one clean repaint, never a half-built answer
        try:
            for transient in list(self.rows):
                if transient is self.status_row or getattr(transient, "is_reply", False):
                    continue
                self.layout.removeWidget(transient)
                self.rows.remove(transient)
                transient.hide()
                transient.deleteLater()
            steps = self.retire_status()
            self.set_reply(text)
            reply = self.reply_row
            if reply:
                self.attach_summary(steps)
                reply.response_id = "agent-" + str(uuid4())
                reply.rating = ""
                reply.file_summary = file_summary
                reply.streaming = False
                from aedrova.desktop.response_actions import response_parts

                options = response_parts(text)[1]
                card = reply.install_choices(options)
                author = reply.author.text()
                if card is not None:
                    card.chosen.connect(
                        lambda value, free: self.choice_requested.emit(author, value, free)
                    )
                reply.set_message(text)
                reply.message.setProperty("aedrovaTranslatingStream", False)
        finally:
            content.setUpdatesEnabled(True)
            self.changed.emit()

    def set_reply(self, text):
        """Update a single streaming response without adding activity-log rows."""
        if not getattr(self, "reply_row", None) or self.reply_row not in self.rows:
            content = self.widget()
            content.setUpdatesEnabled(False)
            try:
                steps = self.retire_status()
                self.reply_row = ActivityRow(
                    text,
                    author=self.author_name,
                    character_config=self.character_config,
                    streaming=True,
                )
                self.reply_row.is_reply = True
                self.reply_row.reply_action.connect(self.reply_action)
                self.reply_row.message.setProperty("aedrovaTranslatingStream", True)
                self.add_row(self.reply_row)
                self.attach_summary(steps)
            finally:
                content.setUpdatesEnabled(True)
        elif self.reply_row.summary != text:
            self.reply_row.summary = text
            self.reply_row.set_message(text)
            self.reply_row.message.setProperty("aedrovaTranslatingStream", True)
            self.changed.emit()
