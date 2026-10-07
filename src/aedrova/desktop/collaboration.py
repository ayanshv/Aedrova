"""Chat actions and shared collaboration surfaces; transport stays off the UI thread."""

import http.client
import re
import time
from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID, uuid4

from PySide6.QtCore import QEvent, QObject, Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QImageReader, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPlainTextEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from aedrova.desktop.controls import AppDialog, AppMenu, ChoiceBox
from aedrova.desktop.conversation import SafeDocument
from aedrova.desktop.dialogs import button, label


def snippet(body):
    body = re.sub(r"<@([a-f0-9-]{36})\|([^>\n]{1,80})>", lambda m: "@" + m[2], body)
    document = SafeDocument()
    from html import escape

    document.setMarkdown(escape(body, quote=False))
    return " ".join(document.toPlainText().split())[:190]


def message_link(workspace, channel, message):
    return f"aedrova://chat/{workspace}/{channel}/{message}"


class ChatPanel(AppDialog):
    """One searchable surface for activity, saved content, files and workspace search."""

    def __init__(self, owner, section, channel=None):
        super().__init__(owner.window)
        self.owner, self.section, self.channel = owner, section, channel
        self.generation = 0
        self.setWindowTitle(
            {
                "search": "Search your workspace",
                "saved": "Saved for later",
                "pinned": "Pinned messages",
                "files": "Workspace files",
                "activity": "Activity",
                "recent": "Recent activity",
                "people": "People & presence",
            }[section]
        )
        self.resize(760, 620)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)
        layout.addWidget(label(self.windowTitle(), "title"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search messages, people, channels and files…")
        self.search.setAccessibleName("Search workspace")
        layout.addWidget(self.search)
        self.notice = label("", "muted", wrap=True)
        layout.addWidget(self.notice)
        self.results = QListWidget()
        self.results.setObjectName("ChatResults")
        self.results.setSpacing(6)
        self.results.setWordWrap(True)
        self.results.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.results.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.results.itemActivated.connect(self.open_item)
        self.results.itemClicked.connect(self.open_item)
        layout.addWidget(self.results, 1)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.load)
        self.search.textChanged.connect(lambda: self.timer.start())
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(5000)
        self.refresh_timer.timeout.connect(self.load)
        if section in ("activity", "people", "recent"):
            self.refresh_timer.start()
        self.finished.connect(lambda _: self.timer.stop())
        self.finished.connect(lambda _: self.refresh_timer.stop())
        QTimer.singleShot(0, self.load)

    def load(self):
        if not self.isVisible():
            return
        self.generation += 1
        generation = self.generation
        self.notice.setText("Searching…")
        self.results.clear()
        self.owner.inventory(
            self.search.text(),
            self.section,
            self.channel,
            lambda data: (
                self.loaded(data) if generation == self.generation and self.isVisible() else None
            ),
        )

    def loaded(self, data):
        self.results.clear()
        if data.get("setup_required"):
            self.notice.setText(
                "Chat collaboration needs the latest Supabase migration. "
                "Existing conversations remain available."
            )
            return
        if self.section in ("search", "people"):
            for person in data.get("people", []):
                self.add(
                    f"{person['display_name']} · {person.get('availability', 'offline')}\n"
                    f"{person.get('status') or person.get('role', 'Member')}",
                    {"person": person},
                )
        if self.section == "search":
            for channel in data.get("channels", []):
                self.add(
                    f"{'🔒' if channel.get('private') else '#'} {channel['name']}\n"
                    f"{channel.get('topic') or 'Conversation'}",
                    {"channel": channel["id"]},
                )
        if self.section != "people":
            for message in data.get("messages", []):
                prefix = (message.get("notification") or "").capitalize()
                unseen = (
                    " · New" if self.section == "activity" and not message.get("seen_at") else ""
                )
                text = (
                    f"{prefix}{unseen}   {message['author']} · "
                    f"{message['created_at'].replace('T', ' ')[:16]}\n"
                    f"#{message['channel']} · {message.get('filename') or snippet(message['body'])}"
                )
                self.add(text.strip(), {"message": message})
        self.notice.setText(
            f"{self.results.count()} results · Click to open"
            if self.results.count()
            else "Nothing here yet."
        )

    def add(self, text, value):
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, value)
        item.setToolTip(text)
        self.results.addItem(item)

    def open_item(self, item):
        data = item.data(Qt.ItemDataRole.UserRole)
        if "person" in data:
            self.owner.profile(data["person"])
        elif "channel" in data:
            self.owner.window.switch_channel(data["channel"])
            self.accept()
        else:
            message = data["message"]
            if self.section == "files":
                self.owner.open_attachment(message["attachment_id"], message["filename"])
            else:
                self.owner.open_message(message)
                self.accept()


class Collaboration(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.data = {}
        self.avatar_images = {}
        self.avatar_pending = set()
        self.avatar_failed = set()
        for view in (window.messages, window.thread_messages):
            view.avatar_images = self.avatar_images
            view.avatar_paths = {}
        self.manual_unread = set()
        self.dialogs = []
        self.local_saved = set()
        self.last_typing = 0
        self.last_heartbeat = 0
        self.channel_seen = None
        self.notification_ids = set()
        self.pending_link = None
        self.scope_workspace = None
        self.allowed_channels = set()
        self.toolbar = QWidget()
        row = QHBoxLayout(self.toolbar)
        row.setContentsMargins(28, 4, 28, 4)
        row.setSpacing(8)
        for title, section in [("Activity", "activity"), ("Saved", "saved"), ("Files", "files")]:
            control = button(title, role="outline")
            control.clicked.connect(lambda checked=False, s=section: self.panel(s))
            row.addWidget(control)
            if section == "activity":
                self.activity_button = control
        more = button("•••", "More chat tools", "icon")
        more.clicked.connect(self.menu)
        row.addWidget(more)
        row.addStretch()
        self.typing_label = label("", "muted")
        row.addWidget(self.typing_label, 1)
        self.window.chat_column.layout().insertWidget(0, self.toolbar)
        for view in (window.messages, window.thread_messages):
            view.action_requested.connect(self.action)
            view.link_requested.connect(self.preview_link)
            view.files_dropped.connect(lambda paths, v=view: self.drop_files(paths, v))
        for composer in (window.composer, window.thread_composer):
            attach = button("＋", "Attach files or images", "icon")
            attach.setFixedSize(30, 29)
            attach.clicked.connect(lambda checked=False, c=composer: self.attach(c))
            composer.layout().itemAt(composer.layout().count() - 1).layout().insertWidget(0, attach)
            composer.editor.textChanged.connect(lambda c=composer: self.typing(c))
            composer.editor.files_dropped.connect(
                lambda paths, c=composer: self.drop_files(
                    paths, window.thread_messages if c.thread else window.messages
                )
            )
            people_button = button("⌄", "Mention a teammate or channel", "icon")
            people_button.setFixedSize(24, 29)
            people_button.clicked.connect(lambda checked=False, c=composer: self.mention_menu(c))
            composer.layout().itemAt(composer.layout().count() - 1).layout().insertWidget(
                2, people_button
            )
            formatting = button("Aa", "Formatting", "icon")
            formatting.setFixedSize(30, 29)
            formatting.clicked.connect(lambda checked=False, c=composer: self.format_menu(c))
            composer.layout().itemAt(composer.layout().count() - 1).layout().insertWidget(
                3, formatting
            )
        window.search_button.clicked.disconnect(window.open_switcher)
        window.search_button.clicked.connect(
            lambda: self.panel("search") if self.connected() else window.open_switcher()
        )
        window.search_button.setText("Search your workspace                          ⌘ F")
        window.search_button.setToolTip(
            "Search messages, people, channels and files · ⌘F · ⌘K jumps to a conversation"
        )
        self.shortcut = QShortcut(QKeySequence("Ctrl+F"), window)
        self.shortcut.activated.connect(lambda: self.panel("search"))
        self.timer = QTimer(self)
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.pulse)
        self.timer.start()
        QApplication.instance().installEventFilter(self)
        self.last_input = time.monotonic()
        self.last_availability = "online"

    def eventFilter(self, watched, event):
        if event.type() in (
            QEvent.Type.KeyPress,
            QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseMove,
        ):
            self.last_input = time.monotonic()
        return False

    def connected(self):
        return (
            self.window.connected
            if self.window.connected and self.window.connected.active
            else None
        )

    def request(self, action, data, done=None):
        connected = self.connected()
        if not connected:
            self.window.notify("Sign in to use shared collaboration tools.")
            return
        service = connected.account.service
        if getattr(service, "collaboration_available", None) is False:
            self.window.notify("Run the chat collaboration SQL migration, then restart Aedrova.")
            return
        connected.enqueue(
            ("chat", action, str(data)),
            lambda: service.rpc("chat_action", {"p_action": action, "p_data": data}),
            lambda result: self.completed(action, result, done),
        )

    def completed(self, action, result, done):
        connected = self.connected()
        if connected:
            connected.last_view = None
        if action not in ("typing", "heartbeat", "profile", "seen"):
            self.window.notify("Updated.")
        if done:
            done(result)

    def inventory(self, query, section, channel, done):
        connected = self.connected()
        if not connected:
            done(self.local_inventory(query, section, channel))
            return
        service, workspace = connected.account.service, self.window.workspace_id
        if not hasattr(service, "chat_inventory"):
            done({"setup_required": True})
            return
        connected.enqueue(
            ("inventory", workspace, query, section, channel),
            lambda: service.chat_inventory(workspace, query, section, channel),
            lambda data: (
                done(data) if self.connected() and self.window.workspace_id == workspace else None
            ),
        )

    def local_inventory(self, query, section, channel):
        rows = []
        workspace = next(
            (w for w in self.window.store.workspaces if w.id == self.window.workspace_id), None
        )
        if not workspace:
            return {"messages": [], "channels": [], "people": []}
        for c in workspace.channels:
            if channel and c.id != channel:
                continue
            for root in c.messages:
                for m in [root, *root.replies]:
                    if m.unsent or query.casefold() not in (m.body + m.attachment).casefold():
                        continue
                    if (
                        section == "saved"
                        and not m.saved
                        or section == "pinned"
                        and not m.pinned
                        or section == "files"
                        and not m.attachment
                    ):
                        continue
                    if section in ("people", "activity"):
                        continue
                    rows.append(
                        {
                            "id": m.id,
                            "body": m.body,
                            "author": m.author,
                            "created_at": m.time,
                            "channel": c.name,
                            "channel_id": c.id,
                            "parent_id": root.id if m is not root else None,
                            "filename": m.attachment,
                            "attachment_id": m.attachment_id,
                        }
                    )
        return {
            "messages": rows,
            "channels": [
                vars(c)
                for c in self.window.workspace.channels
                if query.casefold() in c.name.casefold()
            ],
            "people": [],
        }

    def panel(self, section, channel=None):
        dialog = ChatPanel(self, section, channel)
        self.keep(dialog)
        dialog.show()
        dialog.search.setFocus()

    def keep(self, dialog):
        self.dialogs.append(dialog)
        dialog.finished.connect(
            lambda _: self.dialogs.remove(dialog) if dialog in self.dialogs else None
        )

    def load_avatar(self, path, done):
        if path in self.avatar_images:
            done(self.avatar_images[path])
            return
        account = getattr(self.window, "account_dialog", None)
        if (
            path in self.avatar_pending
            or path in self.avatar_failed
            or not account
            or not account.service
            or not account.service.user
        ):
            return
        service = account.service
        user_id = str(service.user.id)

        def fetch():
            try:
                return service.avatar_bytes(path)
            except Exception:
                return b""

        def loaded(data):
            self.avatar_pending.discard(path)
            if (
                not account.service
                or not account.service.user
                or str(account.service.user.id) != user_id
            ):
                return
            QImageReader.setAllocationLimit(64)
            image = QPixmap()
            if data and image.loadFromData(data, "PNG"):
                if len(self.avatar_images) >= 128:
                    self.avatar_images.clear()
                self.avatar_images[path] = image
                done(image)
            else:
                self.avatar_failed.add(path)

        connected = self.connected()
        if connected:
            self.avatar_pending.add(path)
            if not connected.enqueue(("avatar", path), fetch, loaded):
                self.avatar_pending.discard(path)
        elif not account.busy:
            self.avatar_pending.add(path)
            account.run(fetch, loaded)

    def sync(self, snapshot):
        data = snapshot.get("chat", {})
        scope = data.get("workspace_id", self.window.workspace_id)
        allowed = {c["id"] for c in snapshot.get("channels", [])}
        if self.scope_workspace and (
            scope != self.scope_workspace or self.allowed_channels - allowed
        ):
            for dialog in list(self.dialogs):
                dialog.reject()
        self.scope_workspace = scope
        self.allowed_channels = allowed
        previous = self.data
        if not previous:
            self.last_availability = snapshot.get("user_profile", {}).get("availability", "online")
        self.data = data
        window = self.window
        fresh = {
            r["id"]
            for r in data.get("messages", [])
            if r.get("notification") and not r.get("seen_at")
        }
        own = next(
            (
                p
                for p in data.get("people", [])
                if self.connected()
                and p["user_id"] == str(self.connected().account.service.user.id)
            ),
            {},
        )
        if previous and fresh - self.notification_ids and own.get("availability") != "busy":
            QTimer.singleShot(
                0,
                lambda: (
                    window.notify(
                        "New activity · Open Activity to see mentions, messages and replies."
                    )
                    if self.connected()
                    else None
                ),
            )
        self.notification_ids = fresh
        people = data.get("people", [])
        paths = {p["user_id"]: p["avatar_path"] for p in people if p.get("avatar_path")}
        for view in (window.messages, window.thread_messages):
            view.avatar_paths = paths
        for path in list(paths.values())[:12]:
            self.load_avatar(
                path,
                lambda image: (
                    window.messages.viewport().update(),
                    window.thread_messages.viewport().update(),
                ),
            )
        for composer in (window.composer, window.thread_composer):
            composer.people = people
        self.activity_button.setText(
            "Activity" + (f" · {data['unseen']}" if data.get("unseen") else "")
        )
        names = {p["user_id"]: p["display_name"] for p in people}
        typing = [
            names.get(t["user_id"], "A teammate")
            for t in data.get("typing", [])
            if t["channel_id"] == window.channel_id
        ]
        self.typing_label.setText(
            ", ".join(typing[:3]) + (" is typing…" if len(typing) == 1 else " are typing…")
            if typing
            else ""
        )
        if self.channel_seen != window.channel_id:
            self.manual_unread.clear()
            self.channel_seen = window.channel_id
        if self.pending_link and people:
            link, self.pending_link = self.pending_link, None
            QTimer.singleShot(0, lambda: self.open_link(link))

    def reset(self):
        self.avatar_images.clear()
        self.avatar_pending.clear()
        self.avatar_failed.clear()
        for view in (self.window.messages, self.window.thread_messages):
            view.avatar_paths = {}
            view.viewport().update()
        self.data = {}
        self.notification_ids.clear()
        self.pending_link = None
        self.manual_unread.clear()
        self.channel_seen = None
        self.scope_workspace = None
        self.allowed_channels.clear()
        self.activity_button.setText("Activity")
        self.typing_label.clear()
        for composer in (self.window.composer, self.window.thread_composer):
            composer.people = []
            composer.mention_tokens.clear()
        for dialog in list(self.dialogs):
            dialog.reject()

    def pulse(self):
        connected = self.connected()
        if not connected:
            return
        if not self.window.isVisible():
            return
        if getattr(connected.account.service, "collaboration_available", None) is not True:
            return
        now = time.monotonic()
        if now - self.last_heartbeat > 30:
            self.last_heartbeat = now
            own = next(
                (
                    p
                    for p in self.data.get("people", [])
                    if p["user_id"] == str(connected.account.service.user.id)
                ),
                {},
            )
            away = now - self.last_input > 300
            availability = (
                "busy"
                if own.get("availability") == "busy"
                else ("away" if away else self.last_availability)
            )
            self.request("profile", {"status": own.get("status", ""), "availability": availability})
        if (
            self.window.composer.editor.hasFocus()
            and self.window.composer.editor.toPlainText().strip()
        ):
            self.typing(self.window.composer)

    def typing(self, composer):
        if (
            not self.connected()
            or getattr(self.connected().account.service, "collaboration_available", None)
            is not True
        ):
            return
        now = time.monotonic()
        active = bool(composer.editor.toPlainText().strip()) and composer.editor.hasFocus()
        if active and now - self.last_typing < 3:
            return
        self.last_typing = now
        self.request("typing", {"channel": self.window.channel_id, "active": active})

    def menu(self):
        menu = AppMenu(self.window)
        for title, callback in [
            ("People & presence", lambda: self.panel("people")),
            ("Channel details & members", self.channel_details),
            ("Pinned messages", lambda: self.panel("pinned", self.window.channel_id)),
            ("Recent activity", lambda: self.panel("recent")),
            ("Start group DM…", self.group_dm),
            ("Set your status…", self.set_status),
            ("Notification preferences…", self.preferences),
        ]:
            menu.addAction(title, callback)
        menu.exec(self.toolbar.mapToGlobal(self.toolbar.rect().bottomLeft()))

    def action(self, action, identifier):
        message = self.window._local_message(identifier)
        if not message:
            return
        if action == "quote":
            composer = (
                self.window.thread_composer
                if self.window.thread_messages.hasFocus()
                else self.window.composer
            )
            composer.editor.textCursor().insertText(
                "> "
                + message.author
                + "\n"
                + "\n".join("> " + line for line in message.body.splitlines())
                + "\n\n"
            )
            composer.editor.setFocus()
        elif action == "link":
            QApplication.clipboard().setText(
                message_link(self.window.workspace_id, self.window.channel_id, identifier)
            )
            self.window.notify("Message link copied. Access still requires workspace membership.")
        elif action in ("saved", "pinned"):
            if not self.connected():
                setattr(message, action, not getattr(message, action))
                self.window._refresh_interactions()
            else:
                self.request(
                    action, {"message": identifier, "present": not getattr(message, action)}
                )
        elif action == "edit":
            self.edit(message)
        elif action == "forward":
            self.forward(message)
        elif action == "unread":
            self.manual_unread.add(self.window.channel_id)
            if self.connected():
                self.connected().read_marked.pop(self.window.channel_id, None)
            self.request("unread", {"message": identifier})
        elif action == "profile":
            row = (
                self.connected().cache.get(self.window.channel_id, {}).get(identifier, {})
                if self.connected()
                else {}
            )
            person = next(
                (p for p in self.data.get("people", []) if p["user_id"] == row.get("sender_id")),
                {"display_name": message.author},
            )
            self.profile(person)
        elif action == "attachment":
            self.open_attachment(message.attachment_id, message.attachment)

    def edit(self, message):
        dialog = AppDialog(self.window)
        dialog.setWindowTitle("Edit message")
        dialog.resize(560, 340)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)
        layout.addWidget(label("Edit message", "title"))
        editor = QPlainTextEdit(message.body)
        layout.addWidget(editor)
        submit = button("Save changes", role="primary")
        layout.addWidget(submit)

        def save():
            body = editor.toPlainText().strip()
            if not 1 <= len(body) <= 10000:
                return
            if self.connected():
                self.request(
                    "edit", {"message": message.id, "body": body}, lambda _: dialog.accept()
                )
            elif message.mine:
                message.body = body
                message.edited = True
                self.window._refresh_interactions()
                dialog.accept()

        submit.clicked.connect(save)
        self.keep(dialog)
        dialog.show()

    def forward(self, message):
        dialog = AppDialog(self.window)
        dialog.setWindowTitle("Forward message")
        dialog.resize(480, 280)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)
        layout.addWidget(label("Share with a conversation", "title"))
        layout.addWidget(
            label(
                "Forwards the message text. Files stay in their original conversation.",
                "muted",
                wrap=True,
            )
        )
        choice = ChoiceBox()
        layout.addWidget(choice)
        for channel in self.window.workspace.channels:
            choice.addItem(channel.name, channel.id)
        submit = button("Forward", role="primary")
        layout.addWidget(submit)

        def send():
            if self.connected():
                self.request(
                    "forward",
                    {
                        "message": message.id,
                        "destination": choice.currentData(),
                        "id": str(uuid4()),
                    },
                    lambda _: dialog.accept(),
                )
            else:
                self.window.store.send(
                    self.window.workspace_id,
                    choice.currentData(),
                    "Forwarded message\n\n" + message.body,
                )
                self.window._load_channel()
                dialog.accept()

        submit.clicked.connect(send)
        self.keep(dialog)
        dialog.show()

    def open_message(self, message):
        self.window.switch_channel(message["channel_id"])
        connected = self.connected()
        if connected:
            service = connected.account.service
            channel = message["channel_id"]
            parent = message.get("parent_id")

            def fetch():
                rows = service.thread_context(channel, parent or message["id"])
                files = service.attachments_for([r["id"] for r in rows])
                return rows, files

            def loaded(result):
                rows, files = result
                connected.cache.setdefault(channel, {}).update({r["id"]: r for r in rows})
                connected.files.update({f["message_id"]: f for f in files})
                if self.window.channel_id != channel:
                    return
                connected.apply(
                    connected.account.snapshot,
                    list(connected.cache[channel].values()),
                    self.window.workspace_id,
                    channel,
                )
                if parent:
                    self.window.open_thread(parent)
                self.focus_message(message["id"], bool(parent))
                if message.get("notification"):
                    self.request("seen", {"message": message["id"]})

            connected.enqueue(("open-message", message["id"]), fetch, loaded)
        else:
            if message.get("parent_id"):
                self.window.open_thread(message["parent_id"])
            self.focus_message(message["id"], bool(message.get("parent_id")))

    def focus_message(self, identifier, thread=False):
        view = self.window.thread_messages if thread else self.window.messages
        for i, m in enumerate(view.conversation_model.messages):
            if m.id == identifier:
                index = view.model().index(i)
                view.setCurrentIndex(index)
                view.scrollTo(index)
                view.setFocus()
                break

    def open_link(self, link):
        parsed = urlsplit(link)
        parts = parsed.path.strip("/").split("/")
        if parsed.scheme != "aedrova" or parsed.netloc != "chat" or len(parts) != 3:
            return
        try:
            for value in parts:
                UUID(value)
        except ValueError:
            return
        if not self.connected():
            self.pending_link = link
            self.window.show_account()
            return
        workspace, channel, message = parts
        allowed = any(
            w.id == workspace and any(c.id == channel for c in w.channels)
            for w in self.window.store.workspaces
        )
        if not allowed:
            self.window.notify("This conversation is unavailable to your account.")
            return
        self.window.switch_workspace(workspace)
        # Read message through the user-JWT before deciding whether it is a reply.
        connected = self.connected()
        service = connected.account.service

        def fetched(rows):
            if rows:
                self.open_message(rows[0])
            else:
                self.window.notify("Message unavailable.")

        connected.enqueue(
            ("link", message), lambda: service.thread_context(channel, message), fetched
        )

    def attach(self, composer=None):
        if self.connected():
            self.connected().upload(
                parent=self.window.thread_id
                if self.window.thread_composer.editor.hasFocus()
                else None
            )
        else:
            self.window.notify("Sign in to upload files securely.")

    def drop_files(self, paths, view):
        connected = self.connected()
        if not connected:
            self.window.notify("Sign in to upload files securely.")
            return
        for path in paths[:10]:
            if Path(path).is_file():
                connected.upload(
                    path,
                    parent=self.window.thread_id if view is self.window.thread_messages else None,
                )

    def open_attachment(self, identifier, filename):
        connected = self.connected()
        if not connected or not identifier:
            self.window.notify("This sample file has no uploaded content.")
            return
        service = connected.account.service

        def loaded(data):
            dialog = AppDialog(self.window)
            dialog.setWindowTitle(filename)
            dialog.resize(760, 600)
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(24, 24, 24, 24)
            layout.addWidget(label(filename, "title"))
            QImageReader.setAllocationLimit(64)
            pixmap = QPixmap()
            if Path(filename).suffix.lower() in (
                ".png",
                ".jpg",
                ".jpeg",
                ".webp",
                ".gif",
            ) and pixmap.loadFromData(data):
                image = QLabel()
                image.setAlignment(Qt.AlignmentFlag.AlignCenter)
                image.setPixmap(
                    pixmap.scaled(
                        700,
                        480,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
                scroll = QScrollArea()
                scroll.setWidgetResizable(True)
                scroll.setWidget(image)
                layout.addWidget(scroll)
            else:
                text = QPlainTextEdit()
                text.setReadOnly(True)
                try:
                    content = data[:200000].decode("utf-8")
                except UnicodeDecodeError:
                    content = (
                        "Preview is unavailable for this file type. "
                        "Save a copy to open it in another app."
                    )
                text.setPlainText(content)
                layout.addWidget(text)
            save = button("Save a copy…", role="outline")
            layout.addWidget(save)

            def save_file():
                from PySide6.QtWidgets import QFileDialog

                from aedrova.identity.transfers import save_download

                path, _ = QFileDialog.getSaveFileName(dialog, "Save attachment", filename)
                if path:
                    save_download(path, data)

            save.clicked.connect(save_file)
            self.keep(dialog)
            dialog.show()

        connected.enqueue(
            ("preview-file", identifier), lambda: service.download_attachment(identifier), loaded
        )

    def group_dm(self):
        self.inventory("", "people", None, self.group_picker)

    def group_picker(self, data):
        if data.get("setup_required") or not self.connected():
            self.window.notify("Sign in and apply the chat collaboration migration first.")
            return
        dialog = AppDialog(self.window)
        dialog.setWindowTitle("Group message")
        dialog.resize(480, 480)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)
        layout.addWidget(label("Bring your people together", "title"))
        layout.addWidget(
            label(
                "Choose 2–20 teammates. Only these people can read this conversation.",
                "muted",
                wrap=True,
            )
        )
        people = QListWidget()
        people.setObjectName("ChatResults")
        layout.addWidget(people, 1)
        me = str(self.connected().account.service.user.id)
        for person in data.get("people", []):
            if person["user_id"] == me:
                continue
            item = QListWidgetItem(person["display_name"])
            item.setData(Qt.ItemDataRole.UserRole, person["user_id"])
            item.setCheckState(Qt.CheckState.Unchecked)
            people.addItem(item)
        submit = button("Start group conversation", role="primary")
        layout.addWidget(submit)

        def start():
            members = [
                people.item(i).data(Qt.ItemDataRole.UserRole)
                for i in range(people.count())
                if people.item(i).checkState() == Qt.CheckState.Checked
            ]
            if not 2 <= len(members) <= 20:
                self.window.notify("Choose 2–20 teammates.")
                return
            self.request(
                "group_dm",
                {"workspace": self.window.workspace_id, "members": members, "id": str(uuid4())},
                lambda result: self.group_opened(result, dialog),
            )

        submit.clicked.connect(start)
        self.keep(dialog)
        dialog.show()

    def group_opened(self, result, dialog):
        connected = self.connected()
        if not connected:
            return
        workspace = self.window.workspace_id
        connected.enqueue(
            ("group-refresh", result["channel"]),
            connected.account.service.snapshot,
            lambda snapshot: connected.apply(snapshot, [], workspace, result["channel"]),
        )
        dialog.accept()

    def channel_details(self):
        self.inventory("", "people", self.window.channel_id, self.details_loaded)

    def details_loaded(self, data):
        channel = self.window.channel
        dialog = AppDialog(self.window)
        dialog.setWindowTitle("Channel details")
        dialog.resize(560, 640)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)
        layout.addWidget(label(channel.name, "title"))
        layout.addWidget(
            label(
                "Private · members only" if channel.private else "Public · workspace members",
                "muted",
            )
        )
        topic = QLineEdit(channel.topic)
        topic.setMaxLength(240)
        topic.setPlaceholderText("Channel topic")
        layout.addWidget(topic)
        description = QPlainTextEdit(channel.description)
        description.setPlaceholderText("Channel description")
        description.setMaximumHeight(100)
        layout.addWidget(description)
        posting = ChoiceBox()
        posting.addItem("Everyone can post", "members")
        posting.addItem("Only owners and admins can post", "admins")
        posting.setCurrentIndex(max(0, posting.findData(channel.posting)))
        layout.addWidget(posting)
        layout.addWidget(label("Members", "section"))
        members = QListWidget()
        members.setObjectName("ChatResults")
        layout.addWidget(members, 1)
        for person in data.get("people", []):
            item = QListWidgetItem(
                f"{person['display_name']} · {person.get('availability', 'offline')} · "
                f"{person.get('role', 'member')}"
            )
            item.setData(Qt.ItemDataRole.UserRole, person)
            members.addItem(item)
        members.itemActivated.connect(
            lambda item: self.profile(item.data(Qt.ItemDataRole.UserRole))
        )
        role = self.own_role()
        editable = role in ("owner", "admin") and not channel.direct
        for control in (topic, description, posting):
            control.setEnabled(editable)
        save = button("Save channel details", role="primary")
        save.setEnabled(editable)
        layout.addWidget(save)
        save.clicked.connect(
            lambda: self.request(
                "channel",
                {
                    "channel": channel.id,
                    "topic": topic.text(),
                    "description": description.toPlainText(),
                    "posting": posting.currentData(),
                },
                lambda _: dialog.accept(),
            )
        )
        manage = button("Manage members and permissions…", role="outline")
        layout.addWidget(manage)
        manage.clicked.connect(lambda: self.manage_members(dialog))
        self.keep(dialog)
        dialog.show()

    def own_role(self):
        connected = self.connected()
        if not connected:
            return "member"
        return next(
            (
                r["role"]
                for r in connected.account.snapshot.get("members", [])
                if r["workspace_id"] == self.window.workspace_id
                and r["user_id"] == str(connected.account.service.user.id)
            ),
            "member",
        )

    def manage_members(self, dialog):
        dialog.accept()
        # Existing account page owns invitations, workspace roles and private-channel access.
        self.window.show_account()

    def profile(self, person):
        dialog = AppDialog(self.window)
        dialog.setWindowTitle("Profile")
        dialog.resize(480, 480)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)
        from aedrova.desktop.profile import Avatar

        avatar = Avatar(72)
        avatar.initials = "".join(p[0] for p in person.get("display_name", "T").split()[:2])
        layout.addWidget(avatar)
        if person.get("avatar_path"):
            self.load_avatar(
                person["avatar_path"],
                lambda image: (setattr(avatar, "pixmap", image), avatar.update()),
            )
        layout.addWidget(label(person.get("display_name", "Teammate"), "heading"))
        if person.get("username"):
            layout.addWidget(label("@" + person["username"], "muted"))
        for field in ("title", "bio"):
            if person.get(field):
                layout.addWidget(label(person[field], wrap=True))
        layout.addWidget(
            label(
                person.get("role", "Member").capitalize()
                + " · "
                + person.get("availability", "offline"),
                "muted",
            )
        )
        layout.addWidget(
            label(
                (person.get("status_emoji") or "")
                + " "
                + (person.get("status") or "No status set."),
                wrap=True,
            )
        )
        if (
            person.get("user_id")
            and self.connected()
            and person["user_id"] != str(self.connected().account.service.user.id)
        ):
            dm = button("Message", role="primary")
            layout.addWidget(dm)

            def start():
                connected = self.connected()
                service = connected.account.service
                workspace = self.window.workspace_id
                connected.enqueue(
                    ("profile-dm", person["user_id"]),
                    lambda: (
                        service.rpc(
                            "start_direct_message",
                            {"p_workspace": workspace, "p_user": person["user_id"]},
                        ),
                        service.snapshot(),
                    ),
                    lambda result: connected.apply(result[1], [], workspace, result[0]),
                )
                dialog.accept()

            dm.clicked.connect(start)
        self.keep(dialog)
        dialog.show()

    def set_status(self):
        dialog = AppDialog(self.window)
        dialog.setWindowTitle("Your status")
        dialog.resize(440, 320)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)
        layout.addWidget(label("How are you working today?", "title"))
        own = next(
            (
                p
                for p in self.data.get("people", [])
                if self.connected()
                and p["user_id"] == str(self.connected().account.service.user.id)
            ),
            {},
        )
        status = QLineEdit(own.get("status", ""))
        status.setMaxLength(120)
        status.setPlaceholderText("e.g. Focus time until 2 pm")
        layout.addWidget(status)
        availability = ChoiceBox()
        for text, value in [("Online", "online"), ("Away", "away"), ("Do not disturb", "busy")]:
            availability.addItem(text, value)
        availability.setCurrentIndex(
            max(0, availability.findData(own.get("availability", "online")))
        )
        layout.addWidget(availability)
        save = button("Save status", role="primary")
        layout.addWidget(save)

        def update():
            self.last_availability = availability.currentData()
            self.request(
                "profile",
                {"status": status.text(), "availability": availability.currentData()},
                lambda _: dialog.accept(),
            )

        save.clicked.connect(update)
        self.keep(dialog)
        dialog.show()

    def preferences(self):
        dialog = AppDialog(self.window)
        dialog.setWindowTitle("Notifications")
        dialog.resize(460, 300)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)
        layout.addWidget(label("Notifications for " + self.window.channel.name, "title"))
        mode = ChoiceBox()
        for title, value in [
            ("All messages", "all"),
            ("Mentions, DMs and thread replies", "mentions"),
            ("Muted", "none"),
        ]:
            mode.addItem(title, value)
        current = next(
            (
                p["mode"]
                for p in self.data.get("preferences", [])
                if p["channel_id"] == self.window.channel_id
            ),
            "mentions",
        )
        mode.setCurrentIndex(max(0, mode.findData(current)))
        layout.addWidget(mode)
        save = button("Save preference", role="primary")
        layout.addWidget(save)
        save.clicked.connect(
            lambda: self.request(
                "notification_mode",
                {"channel": self.window.channel_id, "mode": mode.currentData()},
                lambda _: dialog.accept(),
            )
        )
        self.keep(dialog)
        dialog.show()

    def mention_menu(self, composer):
        menu = AppMenu(self.window)
        choices = (
            [
                (composer.agent_name, "@" + composer.agent_name),
                ("channel", "@channel"),
                ("everyone", "@everyone"),
            ]
            + [
                (r["config"]["name"], "<@ai:" + r["id"] + "|" + r["config"]["name"] + ">")
                for r in composer.ai_teammates
                if not r["paused"]
            ]
            + [
                (p["display_name"], "<@" + p["user_id"] + "|" + p["display_name"] + ">")
                for p in composer.people
            ]
            + [
                (p["username"], "<@" + p["user_id"] + "|" + p["username"] + ">")
                for p in composer.people
                if p.get("username")
            ]
        )
        for name, token in choices:
            menu.addAction(
                "@" + name + (" · AI teammate" if token.startswith("<@ai:") else ""),
                lambda checked=False, t=token, n=name: self.insert_person(composer, n, t),
            )
        menu.exec(composer.mention.mapToGlobal(composer.mention.rect().topLeft()))
        composer.editor.setFocus()

    def format_menu(self, composer):
        menu = AppMenu(self.window)
        for name, before, after in [
            ("Bold", "**", "**"),
            ("Italic", "*", "*"),
            ("Inline code", "`", "`"),
            ("Code block", "\n```\n", "\n```\n"),
            ("List", "\n- ", ""),
            ("Link", "[", "](https://)"),
        ]:
            menu.addAction(
                name, lambda checked=False, b=before, a=after: self.format(composer, b, a)
            )
        menu.exec(composer.mapToGlobal(composer.rect().topLeft()))

    def format(self, composer, before, after):
        cursor = composer.editor.textCursor()
        selected = cursor.selectedText().replace("\u2029", "\n")
        cursor.insertText(before + selected + after)
        composer.editor.setFocus()

    def insert_person(self, composer, name, token):
        if token.startswith("<@"):
            composer.mention_tokens[name] = token
        composer.editor.textCursor().insertText("@" + name + " ")

    def preview_link(self, url):
        parsed = urlsplit(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return
        dialog = AppDialog(self.window)
        dialog.setWindowTitle("Link preview")
        dialog.resize(520, 340)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)
        title = label(parsed.hostname, "title", wrap=True)
        description = label(url, "muted", wrap=True)
        layout.addWidget(title)
        layout.addWidget(description)
        metadata = button("Load page preview", role="outline")
        layout.addWidget(metadata)
        open_button = button("Open in browser ↗", role="primary")
        layout.addWidget(open_button)
        open_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(url)))

        def fetch():
            from aedrova.identity.link_preview import fetch_preview

            try:
                return fetch_preview(url)
            except (OSError, ValueError, http.client.HTTPException):
                return {
                    "title": parsed.hostname,
                    "description": "This page does not provide a preview.",
                }

        def loaded(data):
            if not dialog.isVisible():
                return
            title.setText(data["title"])
            description.setText(data["description"])
            metadata.hide()

        def load():
            connected = self.connected()
            if not connected:
                description.setText("Sign in to load page metadata.")
                return
            metadata.setEnabled(False)
            metadata.setText("Loading…")
            connected.enqueue(("preview-link", url), fetch, loaded)

        metadata.clicked.connect(load)
        self.keep(dialog)
        dialog.show()
