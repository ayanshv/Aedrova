"""Marketing Bud's private social workspace: choose, draft, review, approve, deliver."""

from urllib.parse import urlencode
from uuid import uuid4

from PySide6.QtCore import QDateTime, Qt, QTimer
from PySide6.QtWidgets import (
    QDateTimeEdit,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from aedrova.desktop.controls import AppDialog, ChoiceBox
from aedrova.desktop.dialogs import button, label
from aedrova.desktop.dots import DotDialog
from aedrova.dots.client import client


class SocialDialog(AppDialog):
    run = DotDialog.run

    def __init__(self, chat):
        super().__init__(chat)
        self.chat, self.window, self.bud = chat, chat.host, chat.bud
        self.workspace, self.user = chat.workspace, chat.user
        self.job, self.pending, self.row = None, False, None
        self.channels, self.posts = [], []
        self.dirty, self.rendering = False, False
        self.available = False
        self.setWindowTitle("Aedrova · Social · " + self.bud["name"])
        self.resize(820, 760)
        self.setMinimumSize(560, 580)
        outer = QVBoxLayout(self)
        header = QHBoxLayout()
        header.addWidget(label("Social", "heading"), 1)
        connect = button("Connect Buffer", role="outline")
        self.connect_button = connect
        connect.hide()
        connect.clicked.connect(self.connect_buffer)
        header.addWidget(connect)
        self.reload_button = button("Refresh", role="outline")
        self.reload_button.clicked.connect(self.refresh)
        header.addWidget(self.reload_button)
        outer.addLayout(header)
        outer.addWidget(
            label("Your strategy. Your voice. Every post reviewed by you.", "muted", wrap=True)
        )
        self.pages = QTabWidget()
        outer.addWidget(self.pages, 1)
        channels_page = QWidget()
        channel_layout = QVBoxLayout(channels_page)
        channel_layout.addWidget(label("Choose the channels this Bud may publish to.", wrap=True))
        self.channel_list = QListWidget()
        self.channel_list.setAccessibleName("Social publishing channel permissions")
        channel_layout.addWidget(self.channel_list, 1)
        select = button("Save channel selection", role="primary")
        select.clicked.connect(self.select_channels)
        channel_layout.addWidget(select)
        self.pages.addTab(channels_page, "Accounts")
        draft_page = QWidget()
        draft_layout = QVBoxLayout(draft_page)
        self.post_list = ChoiceBox()
        self.post_list.setAccessibleName("Saved social drafts and publishing status")
        self.post_list.currentIndexChanged.connect(self.load_post)
        draft_layout.addWidget(self.post_list)
        self.destination = ChoiceBox()
        self.destination.setAccessibleName("Publishing destination")
        self.destination.currentIndexChanged.connect(self.changed)
        draft_layout.addWidget(self.destination)
        self.editor = QPlainTextEdit()
        self.editor.setAccessibleName("Social post text and preview")
        self.editor.setPlaceholderText(
            "Write a draft, or use a caption from your Bud conversation…"
        )
        self.editor.textChanged.connect(self.changed)
        draft_layout.addWidget(self.editor, 1)
        media = QHBoxLayout()
        self.media_kind = ChoiceBox()
        self.media_kind.addItem("Image", "image")
        self.media_kind.addItem("Video", "video")
        self.media_kind.currentIndexChanged.connect(self.changed)
        media.addWidget(self.media_kind)
        self.media_url = QLineEdit()
        self.media_url.setAccessibleName("Public media URL shared with Buffer")
        self.media_url.setPlaceholderText("Optional stable public HTTPS media URL")
        self.media_url.textChanged.connect(self.changed)
        media.addWidget(self.media_url, 1)
        draft_layout.addLayout(media)
        timing = QHBoxLayout()
        self.mode = ChoiceBox()
        self.mode.addItem("Publish now", "publish")
        self.mode.addItem("Schedule", "schedule")
        self.mode.currentIndexChanged.connect(self.changed)
        timing.addWidget(self.mode)
        self.due = QDateTimeEdit(QDateTime.currentDateTime().addSecs(3600))
        self.due.setCalendarPopup(True)
        self.due.setAccessibleName("Publishing time in your local timezone")
        self.due.dateTimeChanged.connect(self.changed)
        self.due.setDisplayFormat("MMM d yyyy · HH:mm t")
        timing.addWidget(self.due, 1)
        draft_layout.addLayout(timing)
        draft_layout.addWidget(
            label(
                "Preview the exact text, destination and time before approval. "
                "Media must stay public "
                "until publication. Private chat uploads are never exposed automatically.",
                "muted",
                wrap=True,
            )
        )
        actions = QHBoxLayout()
        self.latest = button("Use latest reply", role="outline")
        self.latest.clicked.connect(self.use_reply)
        actions.addWidget(self.latest)
        self.ask = button("Ask Bud", role="outline")
        self.ask.clicked.connect(self.ask_bud)
        actions.addWidget(self.ask)
        self.reject_post = button("Reject draft", role="outline")
        self.reject_post.clicked.connect(self.reject_draft)
        actions.addWidget(self.reject_post)
        actions.addStretch()
        self.primary = button("Save draft", role="primary")
        self.primary.clicked.connect(self.act)
        actions.addWidget(self.primary)
        draft_layout.addLayout(actions)
        self.pages.addTab(draft_page, "Drafts & posts")
        self.status = label("", "muted", wrap=True)
        outer.addWidget(self.status)
        outer.addWidget(
            label(
                "Buffer OAuth metrics are unavailable. Disconnect stops future Aedrova "
                "requests; posts already scheduled in Buffer remain there.",
                "muted",
                wrap=True,
            )
        )
        self.guard = QTimer(self)
        self.guard.timeout.connect(lambda: None if self.chat.current() else self.reject())
        self.guard.start(250)
        self.refresh()

    def update_controls(self):
        self.pages.setEnabled(self.available and not self.pending and self.job is None)
        self.reload_button.setEnabled(not self.pending and self.job is None)
        self.due.setVisible(self.mode.currentData() == "schedule")

    def scope(self):
        return {"workspace": self.workspace, "dot": self.bud["id"]}

    def request(self, path, body, done):
        self.run(
            lambda service: client(service).request(
                "/api/buds/social/" + path, {**self.scope(), **body} if body is not None else None
            ),
            done,
        )

    def refresh(self):
        scope = urlencode(self.scope())

        def fetch(service):
            api = client(service)
            capability = api.request("/api/buds/social/capabilities?" + scope)
            if not capability["available"]:
                return {"channels": []}, {"posts": []}, capability
            return (
                api.request("/api/buds/social/channels?" + scope),
                api.request("/api/buds/social/posts?" + scope),
                capability,
            )

        self.run(fetch, self.loaded, recovery=True)

    def loaded(self, result):
        self.rendering = True
        self.available = result[2]["available"]
        self.connect_button.setVisible(self.available)
        old_id = self.row["id"] if self.row else ""
        self.channels, self.posts = result[0]["channels"], result[1]["posts"]
        self.channel_list.clear()
        self.destination.clear()
        for channel in self.channels:
            title = channel["name"] + " · " + channel["platform"]
            item = QListWidgetItem(title, self.channel_list)
            item.setData(Qt.ItemDataRole.UserRole, channel)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(
                Qt.CheckState.Checked if channel["selected"] else Qt.CheckState.Unchecked
            )
            if not channel["can_publish"]:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                item.setToolTip("Reconnect this channel in Buffer or check publishing permissions.")
            if channel["selected"] and channel["can_publish"]:
                self.destination.addItem(title, (channel["connection"], channel["id"]))
        self.post_list.clear()
        self.post_list.addItem("New draft", None)
        for row in self.posts:
            self.post_list.addItem(
                row["content"]["text"][:45] + " · " + (row["provider_status"] or row["state"]), row
            )
        self.rendering = False
        index = next((i + 1 for i, r in enumerate(self.posts) if r["id"] == old_id), 0)
        self.post_list.setCurrentIndex(index)
        self.load_post()
        self.status.setText(
            "Choose channels in Accounts to get started."
            if not self.destination.count()
            else "Choose a draft or create something new."
        )
        if self.available and self.row:
            self.checked(self.row)
        if not self.available:
            self.status.setText(
                result[2].get("setup_hint") or "Social publishing is being prepared."
            )

    def select_channels(self):
        grouped = {}
        for i in range(self.channel_list.count()):
            item = self.channel_list.item(i)
            row = item.data(Qt.ItemDataRole.UserRole)
            grouped.setdefault(row["connection"], [])
            if item.checkState() == Qt.CheckState.Checked and row["can_publish"]:
                grouped[row["connection"]].append(row["id"])

        def operation(service):
            api = client(service)
            for connection, channels in grouped.items():
                api.request(
                    "/api/buds/social/channels",
                    {**self.scope(), "connection": connection, "channels": channels},
                )

        self.run(operation, lambda _: self.refresh())

    def load_post(self, *_):
        if self.rendering:
            return
        self.rendering = True
        self.row = self.post_list.currentData()
        content = self.row["content"] if self.row else {}
        self.editor.setPlainText(content.get("text", ""))
        if self.row:
            self.destination.setCurrentIndex(
                next(
                    (
                        i
                        for i in range(self.destination.count())
                        if tuple(self.destination.itemData(i) or ())
                        == (self.row["connection"], self.row["channel"])
                    ),
                    -1,
                )
            )
        self.mode.setCurrentIndex(1 if content.get("action") == "schedule" else 0)
        if content.get("due_at"):
            self.due.setDateTime(
                QDateTime.fromString(content["due_at"], Qt.DateFormat.ISODate).toLocalTime()
            )
        assets = content.get("assets", [])
        kind = assets[0]["kind"] if assets else "image"
        value = assets[0] if assets else {}
        self.media_kind.setCurrentIndex(1 if kind == "video" else 0)
        self.media_url.setText(value.get("url", ""))
        locked = bool(self.row and self.row["state"] in {"sending", "submitted", "unknown"})
        self.editor.setReadOnly(locked)
        for control in (
            self.destination,
            self.mode,
            self.due,
            self.media_url,
            self.media_kind,
            self.latest,
            self.ask,
        ):
            control.setEnabled(not locked)
        self.reject_post.setEnabled(bool(self.row) and not locked)
        self.dirty = False
        self.rendering = False
        self.primary.setText(
            "Check status"
            if locked
            else "Publish now"
            if self.row and self.row["state"] == "approved" and content["action"] == "publish"
            else "Schedule post"
            if self.row and self.row["state"] == "approved"
            else "Approve draft"
            if self.row
            else "Save draft"
        )
        self.update_controls()
        if self.row:
            self.checked(self.row)

    def changed(self, *_):
        if not self.rendering:
            self.dirty = True
            self.primary.setText("Save draft")
            self.update_controls()

    def action_body(self):
        return {"id": self.row["id"], "revision": self.row["revision"]}

    def act(self):
        if not self.editor.toPlainText().strip() and not self.row:
            self.status.setText("Write a draft or use your Bud’s latest reply first.")
            return
        if self.row and self.row["state"] in {"sending", "submitted", "unknown"}:
            self.request("status", self.action_body(), self.checked)
        elif self.row and not self.dirty:
            path = "dispatch" if self.row["state"] == "approved" else "approve"
            self.request(path, self.action_body(), lambda _: self.refresh())
        else:
            destination = self.destination.currentData()
            if not destination:
                self.status.setText("Choose and save a publishing channel in Accounts first.")
                return
            # Keep the ID stable across a lost save response.
            if not self.row:
                self.row = {"id": str(uuid4()), "revision": 0, "state": "draft"}
            body = {
                **self.action_body(),
                "connection": destination[0],
                "channel": destination[1],
                "text": self.editor.toPlainText(),
                "action": self.mode.currentData(),
                "due_at": self.due.dateTime().toUTC().toString(Qt.DateFormat.ISODate)
                if self.mode.currentData() == "schedule"
                else None,
                "assets": [
                    {"kind": self.media_kind.currentData(), "url": self.media_url.text().strip()}
                ]
                if self.media_url.text().strip()
                else [],
            }
            self.request("drafts", body, self.saved)

    def saved(self, row):
        self.row = row
        self.refresh()

    def checked(self, row):
        state = row.get("provider_status") or row["state"]
        title = {
            "buffer": "Last confirmed: queued in Buffer",
            "scheduled": "Last confirmed: scheduled in Buffer",
            "published": "Last confirmed: published",
            "failed": "Buffer reported a publishing failure",
            "sent": "Published",
            "draft": "Draft",
            "approved": "Approved · ready for your final action",
            "rejected": "Not submitted",
            "unknown": "Submission unconfirmed",
            "sending": "Submission unconfirmed",
            "submitted": "Submitted to Buffer",
            "error": "Buffer reported a publishing error",
            "notSent": "Not published",
        }.get(state, "Publishing status unavailable")
        self.status.setText(title + (" · " + row.get("error", "") if row.get("error") else ""))

    def reject_draft(self):
        if self.row:
            self.request("reject", self.action_body(), lambda _: self.refresh())

    def use_reply(self):
        reply = next(
            (r["body"] for r in reversed(self.chat.history) if r["role"] == "assistant"), ""
        )
        self.editor.setPlainText(reply)

    def ask_bud(self):
        destination = self.destination.currentText() or "the intended social platform"
        brief = self.editor.toPlainText().strip()
        if not brief:
            self.status.setText("Write a short campaign brief first, then ask your Bud.")
            return
        if self.chat.busy or self.chat.job or not self.chat.loaded:
            self.status.setText("Wait for the current Bud conversation to finish.")
            return
        self.reject()
        self.chat.send(
            "Draft a platform-specific caption for "
            + destination
            + ". Include a clear call to action and suitable hashtags. Draft only; "
            "do not publish or claim publication. Brief: " + brief
        )

    def connect_buffer(self):
        from aedrova.desktop.bud_connectors import open_connectors

        open_connectors(
            self.window, self.bud["id"], on_change=self.refresh, initial_provider="buffer"
        )
