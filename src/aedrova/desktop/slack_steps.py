"""Plain, numbered instructions for getting a Slack export and importing it."""

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from aedrova.desktop.dialogs import button, label
from aedrova.desktop.slack_logo import slack_icon

EXPORT_HELP = "https://slack.com/help/articles/201658943-Export-your-workspace-data"

IN_SLACK = (
    "Open Slack in your web browser and sign in to the workspace you want to bring over. "
    "You must be a Workspace Owner or Admin.",
    "Click your workspace name at the top left of Slack. Choose Tools & settings, then "
    "Workspace settings.",
    "In the page that opens, choose Import/Export Data (top right), then open the Export tab. "
    "You can also go to your-workspace.slack.com/services/export.",
    "Pick a date range. Choose Entire history for everything. Then click Start export.",
    "Wait for Slack to email you that the export is ready, usually a few minutes. Click "
    "Download. You get one file ending in .zip. Do not open or unzip it.",
)
IN_AEDROVA = (
    "Drop that .zip file into the box below, or click Choose ZIP and select it.",
    "Look at the channel list. Untick any channel you do not want to bring over.",
    "Click Import history. Keep Aedrova open until the bar finishes.",
)
RESULT = (
    "When it finishes, each Slack channel appears under From Slack in the sidebar as a "
    "read-only copy with its messages. Everyone in the workspace can search it, and agents "
    "can use it when workspace AI is on."
)
LIMITS = (
    "Only public channels are imported. Private channels and direct messages are not in "
    "Slack's standard export and are ignored. If Aedrova says the file is too large, export "
    "a shorter date range."
)


class NumberedStep(QWidget):
    def __init__(self, number, text):
        super().__init__()
        row = QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)
        badge = QLabel(str(number))
        badge.setObjectName("StepBadge")
        badge.setFixedSize(24, 24)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        row.addWidget(badge, alignment=Qt.AlignmentFlag.AlignTop)
        self.text = label(text, wrap=True)
        row.addWidget(self.text, 1)


class ExportSteps(QWidget):
    """Part 1 happens in Slack, part 2 in Aedrova. Every click is spelled out."""

    def __init__(self, *, open_url=QDesktopServices.openUrl):
        super().__init__()
        self.steps = []
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(10)
        column.addWidget(label("PART 1 · IN SLACK", "section"))
        for number, text in enumerate(IN_SLACK, 1):
            step = NumberedStep(number, text)
            self.steps.append(step)
            column.addWidget(step)
        self.guide = button("Open Slack’s export guide", role="outline")
        self.guide.setIcon(slack_icon(16))
        self.guide.clicked.connect(lambda: open_url(QUrl(EXPORT_HELP)))
        column.addWidget(self.guide, alignment=Qt.AlignmentFlag.AlignLeft)
        column.addSpacing(6)
        column.addWidget(label("PART 2 · IN AEDROVA", "section"))
        for number, text in enumerate(IN_AEDROVA, len(IN_SLACK) + 1):
            step = NumberedStep(number, text)
            self.steps.append(step)
            column.addWidget(step)
        for note in (RESULT, LIMITS):
            line = QFrame()
            line.setObjectName("StepNote")
            holder = QVBoxLayout(line)
            holder.setContentsMargins(12, 10, 12, 10)
            holder.addWidget(label(note, "muted", wrap=True))
            column.addWidget(line)


QUICK = (
    "In Slack, open Workspace settings, then Import/Export Data, then Export.",
    "Start the export and download the .zip. Do not unzip it.",
    "Drop the .zip below, then click Import history.",
)


class QuickSteps(QWidget):
    """The short version for setup: three lines and a link to Slack's own guide."""

    def __init__(self, *, open_url=QDesktopServices.openUrl):
        super().__init__()
        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(8)
        self.steps = []
        for number, text in enumerate(QUICK, 1):
            step = NumberedStep(number, text)
            self.steps.append(step)
            column.addWidget(step)
        self.guide = button("Slack’s export guide", role="outline")
        self.guide.setIcon(slack_icon(16))
        self.guide.clicked.connect(lambda: open_url(QUrl(EXPORT_HELP)))
        column.addSpacing(2)
        column.addWidget(self.guide, alignment=Qt.AlignmentFlag.AlignLeft)
