"""Shared live meeting cards, with channel-scoped presence and bounded profile images."""

from urllib.parse import urlparse

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QWidget

from aedrova.desktop.dialogs import button, label
from aedrova.desktop.materials import system_font

_IMAGES = {}


class ParticipantAvatar(QWidget):
    def __init__(self, person, theme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.name = person.get("display_name") or "Teammate"
        self.setToolTip(self.name)
        self.setAccessibleName("Meeting participant: " + self.name)
        self.setFixedSize(30, 30)
        self.image = None
        url = person.get("avatar_url") or ""
        parsed = urlparse(url)
        host = parsed.hostname or ""
        if (parsed.scheme != "https" or not host.startswith("lh")
                or not host.removeprefix("lh").removesuffix(".googleusercontent.com").isdigit()
                or not host.endswith(".googleusercontent.com") or parsed.username
                or parsed.password or parsed.port not in (None, 443)):
            return
        if url in _IMAGES:
            self.image = _IMAGES[url]
            return
        self.network = QNetworkAccessManager(self)
        request = QNetworkRequest(QUrl(url))
        request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,
                             QNetworkRequest.RedirectPolicy.ManualRedirectPolicy)
        self.reply = self.network.get(request)
        self.reply.readyRead.connect(self.limit_image)
        self.reply.finished.connect(lambda: self.loaded(url))
        QTimer.singleShot(5000, self.reply, self.reply.abort)

    def limit_image(self):
        if self.reply.bytesAvailable() > 256 * 1024:
            self.reply.abort()

    def loaded(self, url):
        if self.reply.error() == self.reply.NetworkError.NoError:
            data = self.reply.readAll()
            if len(data) <= 256 * 1024:
                image = QPixmap()
                if image.loadFromData(data) and image.width() <= 4096 and image.height() <= 4096:
                    self.image = image.scaled(60, 60, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                              Qt.TransformationMode.SmoothTransformation)
                    if len(_IMAGES) >= 128:
                        _IMAGES.pop(next(iter(_IMAGES)))
                    _IMAGES[url] = self.image
                    self.update()
        self.reply.deleteLater()

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addEllipse(1, 1, 28, 28)
        painter.setClipPath(path)
        if self.image:
            painter.drawPixmap(-1, -1, 32, 32, self.image)
        else:
            painter.fillRect(self.rect(), QColor(self.theme.hover))
            painter.setPen(QColor(self.theme.text))
            painter.setFont(system_font(11))
            initials = "".join(part[0] for part in self.name.split()[:2]).upper()
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, initials)


class MeetingAction(QFrame):
    def __init__(self, theme, meeting, join, *, announcement=False, channel_name=""):
        super().__init__()
        self.setObjectName("MeetingAnnouncement" if announcement else "MeetingAction")
        if announcement:
            outer = QVBoxLayout(self)
            outer.setContentsMargins(18, 16, 18, 16)
            outer.setSpacing(12)
            layout = QHBoxLayout()
        else:
            layout = QHBoxLayout(self)
            layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(8)
        if announcement:
            self.setStyleSheet(
                f"QFrame#MeetingAnnouncement {{ background: {theme.surface}; "
                f"border: 1px solid {theme.border}; border-radius: 20px; }}"
            )
            copy = QVBoxLayout()
            copy.setSpacing(4)
            copy.addWidget(label("Meeting in progress", "section"))
            copy.addWidget(label("#" + channel_name + " · " + meeting.get("title", "Team meeting"),
                                 "muted", wrap=True))
            outer.addLayout(copy)
            outer.addLayout(layout)
        self.action = button("Join meeting" if meeting else "Start meeting", role="primary")
        self.action.clicked.connect(join)
        layout.addWidget(self.action)
        participants = meeting.get("participants", []) if meeting else []
        for person in participants[:4]:
            layout.addWidget(ParticipantAvatar(person, theme))
        self.count = label(f"{len(participants)} in meeting", "muted")
        self.count.setAccessibleName(f"{len(participants)} meeting participants")
        self.count.setVisible(bool(meeting))
        layout.addWidget(self.count)
        layout.addStretch()


def current_meetings(window):
    if not getattr(window, "connected", None) or not window.connected.active:
        return []
    activity = window.account_dialog.snapshot.get("meeting_activity", {})
    allowed = {channel.id for channel in window.workspace.channels}
    return [meeting for meeting in activity.get("meetings", [])
            if meeting.get("workspace_id") == window.workspace_id
            and meeting.get("channel_id") in allowed]


def update_meeting_ui(window):
    from aedrova.desktop.meeting_call import open_channel_call

    meetings = current_meetings(window)
    selected = next((m for m in meetings if m["channel_id"] == window.channel_id), None)
    if hasattr(window, "meeting_action_layout"):
        replace_widgets(window.meeting_action_layout)
        window.meeting_action_layout.addWidget(MeetingAction(
            window.theme, selected, lambda: open_channel_call(window)))
    if getattr(window, "meeting_destination", None) is not None:
        destination_choice = window.meeting_destination
        preferences = window.account_dialog.snapshot.get("meeting_activity", {}).get(
            "preferences", [])
        selected_channel = next((p["announcement_channel"] for p in preferences
                                 if p["workspace_id"] == window.workspace_id), None)
        if selected_channel and destination_choice.findData(selected_channel) >= 0:
            destination_choice.setCurrentIndex(destination_choice.findData(selected_channel))
    replace_widgets(window.meeting_announcements_layout)
    preferences = window.account_dialog.snapshot.get("meeting_activity", {}).get("preferences", [])
    destination = next((p["announcement_channel"] for p in preferences
                        if p["workspace_id"] == window.workspace_id), None)
    destination = destination or next((c.id for c in window.workspace.channels
                                      if c.name == "general" and not c.direct), window.channel_id)
    for meeting in meetings:
        target = meeting["channel_id"] if meeting.get("private") else destination
        if window.channel_id not in {target, meeting["channel_id"]}:
            continue
        channel = next(c for c in window.workspace.channels if c.id == meeting["channel_id"])
        window.meeting_announcements_layout.addWidget(MeetingAction(
            window.theme, meeting,
            lambda checked=False, channel=channel.id: join_channel(window, channel),
            announcement=True, channel_name=channel.name))
    window.meeting_announcements.setVisible(window.meeting_announcements_layout.count() > 0)


def join_channel(window, channel):
    from aedrova.desktop.meeting_call import open_channel_call

    window.switch_channel(channel)
    open_channel_call(window)


def replace_widgets(layout):
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().hide()
            item.widget().deleteLater()
