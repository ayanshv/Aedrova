"""Real chat orchestration. Existing desktop controls keep their layout and styling."""

import time
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import QEvent, QObject, Qt, QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QFileDialog

from aedrova.desktop.controls import choose_teammate
from aedrova.desktop.conversation import MESSAGE_ROLE
from aedrova.desktop.state import Channel, DemoStore, Message, Workspace
from aedrova.identity.realtime import RealtimeWakeups
from aedrova.identity.transfers import save_download

PAGE_SIZE = 100


def with_reaction(row, emoji, present):
    """Apply our desired membership without mutating authoritative counts."""
    row = {**row, "reactions": [dict(r) for r in row.get("reactions", [])]}
    if row.get("unsent_at"):
        return row
    reaction = next((r for r in row["reactions"] if r["emoji"] == emoji), None)
    if reaction is None and present:
        row["reactions"].append({"emoji": emoji, "count": 1, "mine": True})
    elif reaction is not None and bool(reaction.get("mine")) != present:
        reaction["count"] += 1 if present else -1
        reaction["mine"] = present
    row["reactions"] = [r for r in row["reactions"] if r["count"] > 0]
    return row


def workspaces_from_snapshot(snapshot, user_id=None):
    names = {
        (x["workspace_id"], x["user_id"]): x["display_name"] for x in snapshot.get("directory", [])
    }
    result = []
    for row in snapshot["workspaces"]:
        channels = []
        for c in snapshot["channels"]:
            if c["workspace_id"] != row["id"]:
                continue
            direct = c.get("kind") in ("dm", "group_dm")
            other = c.get("dm_high") if c.get("dm_low") == user_id else c.get("dm_low")
            name = (
                names.get((row["id"], other), "Direct conversation")
                if c.get("kind") == "dm"
                else c["name"]
            )
            if c.get("kind") == "group_dm":
                name = c.get("display_name") or "Group conversation"
            channels.append(
                Channel(
                    c["id"],
                    name,
                    c.get("topic") or "Private conversation"
                    if direct
                    else (
                        c.get("topic") or ("Private channel" if c["private"] else "Team channel")
                    ),
                    direct=direct,
                    private=c.get("private", False),
                    description=c.get("description", ""),
                    posting=c.get("posting", "members"),
                )
            )
        if not channels:
            channels = [Channel("", "No channels yet", "Ask an admin for channel access.")]
        initials = "".join(word[0] for word in row["name"].split())[:2].upper()
        result.append(Workspace(row["id"], row["name"], initials, channels))
    return result


def message_tree(rows, user_id, *, directory=None, attachments=None):
    directory, attachments = directory or {}, attachments or {}
    by_id = {}
    for row in sorted(rows, key=lambda r: (bool(r.get("local")), r.get("sequence", 0))):
        mine = row["sender_id"] == user_id
        author = (
            "You" if mine else directory.get(row["sender_id"], "Teammate " + row["sender_id"][:6])
        )
        file = attachments.get(row["id"], {})
        by_id[row["id"]] = Message(
            row["id"],
            author,
            "".join(word[0] for word in author.split())[:2],
            row["created_at"].replace("T", " ")[:16],
            row["body"],
            attachment=file.get("filename", ""),
            attachment_id=file.get("id", ""),
            sequence=row.get("sequence", 0),
            delivery=row.get("delivery", ""),
            mine=mine,
            unsent=bool(row.get("unsent_at")),
            reactions=row.get("reactions", []),
            edited=bool(row.get("edited_at")),
            saved=bool(row.get("saved")),
            pinned=bool(row.get("pinned")),
            sender_id=row["sender_id"],
        )
    roots = []
    for row in sorted(rows, key=lambda r: (bool(r.get("local")), r.get("sequence", 0))):
        if row["parent_id"] is None:
            roots.append(by_id[row["id"]])
        elif row["parent_id"] in by_id:
            by_id[row["parent_id"]].replies.append(by_id[row["id"]])
    return roots


class ConnectedDashboard(QObject):
    def __init__(self, window, account):
        super().__init__(window)
        self.window, self.account = window, account
        self.active = False
        self.pending = {}
        self.outbox = {}
        self.reaction_edits = {}
        self.reaction_jobs = set()
        self.queue = deque()
        self.current_action = None
        self.last_view = None
        self.cache = {}
        self.files = {}
        self.history_done = set()
        self.pages_ready = False
        self.retry_at = 0
        self.failures = 0
        self.read_marked = {}
        self.realtime = None
        self.timer = QTimer(self)
        self.timer.setInterval(3000)
        self.timer.timeout.connect(self.refresh)
        account.session_closed.connect(self.disconnect)
        account.operation_failed.connect(self.failed)
        account.snapshot_loaded.connect(self.account_changed)
        account.operation_finished.connect(self.drain_queue)
        QApplication.instance().aboutToQuit.connect(self.stop_realtime)
        window.notice_timer.timeout.disconnect(window._reset_notice)
        window.notice_timer.timeout.connect(self.reset_notice)
        self.shortcuts = []
        for keys, callback in [
            ("Ctrl+Shift+M", self.start_dm),
            ("Ctrl+Shift+U", self.upload),
            ("Ctrl+Shift+S", self.download),
            ("Ctrl+Shift+H", self.load_older),
        ]:
            shortcut = QShortcut(QKeySequence(keys), window)
            shortcut.activated.connect(callback)
            self.shortcuts.append(shortcut)
        window.dm_list.setToolTip("Start a direct message: ⌘⇧M")
        for view in (window.messages, window.thread_messages):
            view.viewport().installEventFilter(self)
        window.messages.thread_requested.connect(lambda _: QTimer.singleShot(0, self.refresh))

    def eventFilter(self, watched, event):  # noqa: N802
        if self.active and event.type() == QEvent.Type.Wheel and event.angleDelta().y() > 0:
            for view in (self.window.messages, self.window.thread_messages):
                if watched is view.viewport() and view.verticalScrollBar().value() == 0:
                    parent = self.window.thread_id if view is self.window.thread_messages else None
                    QTimer.singleShot(0, lambda p=parent: self.load_older(p))
        return False

    def reset_notice(self):
        if self.active:
            self.window.notice.setText(
                "Shared chat · ⌘⇧M direct message · ⌘⇧U attach file · "
                "⌘⇧S save selected file · ⌘⇧H older messages"
            )
        else:
            self.window._reset_notice()

    def stop_realtime(self):
        if self.realtime:
            self.realtime.stop()
            self.realtime = None

    def activate(self):
        if not self.account.service or not self.account.service.user:
            self.window.show_account()
            return
        if not self.active:
            self.window.store = DemoStore()
            self.window.store.workspaces = []
            self.window.store.drafts.clear()
            self.window.last_channels.clear()
            self.realtime = RealtimeWakeups(self)
            source = self.realtime
            source.changed.connect(
                lambda: self.refresh() if self.active and self.realtime is source else None
            )
        self.active = True
        self.apply(self.account.snapshot, [], self.account.workspace_id(), None)
        if not self.active:
            return
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()
        self.timer.start()
        QTimer.singleShot(0, self.refresh)

    def account_changed(self):
        if self.active:
            self.cache.clear()
            self.files.clear()
            self.last_view = None
            self.apply(self.account.snapshot, [], self.window.workspace_id, self.window.channel_id)

    def disconnect(self):
        if self.window.tour:
            self.window.tour.finish("paused")
        if getattr(self.window, "setup_dialog", None):
            self.window.setup_dialog.close()
        build = getattr(self.window, "build_dialog", None)
        if build:
            build.invalidate()
        self.active = False
        self.last_view = None
        self.pages_ready = False
        self.timer.stop()
        self.stop_realtime()
        self.pending.clear()
        self.outbox.clear()
        self.reaction_edits.clear()
        self.reaction_jobs.clear()
        self.queue.clear()
        self.current_action = None
        self.cache.clear()
        self.files.clear()
        self.history_done.clear()
        self.read_marked.clear()
        self.window.store.drafts.clear()
        self.window.composer.clear()
        self.window.thread_composer.clear()
        self.window.thread_id = ""
        self.window.thread_panel.hide()
        self.window.messages.show_messages([])
        self.window.thread_messages.show_messages([])
        self.window.store.workspaces.clear()
        self.window.build_activity.hide()
        self.window.stop_agent.hide()
        self.window.agent_clock.reset()
        self.window.agent_feed.clear()
        self.window.agent_feed.hide()
        self.window.last_agent_event = ""
        if hasattr(self.window, "collaboration"):
            self.window.collaboration.reset()
        self.window.hide()

    def failed(self):
        if not self.active:
            return
        build = getattr(self.window, "build_dialog", None)
        if build and build.pending:
            build.invalidate()
        retryable = getattr(self.account, "last_error_retryable", False)
        self.failures += 1
        self.retry_at = time.monotonic() + min(2 ** min(self.failures, 5), 30)
        if self.current_action:
            action, self.current_action = self.current_action, None
            if action[0][0] == "send":
                pending_row = self.outbox.get(action[0][1])
                if pending_row:
                    pending_row["delivery"] = "Retrying…" if retryable else "Not sent · retry"
                    w = self.window
                    parent = pending_row["parent_id"]
                    composer = w.thread_composer if parent else w.composer
                    if (
                        w.channel_id == pending_row["channel_id"]
                        and (not parent or w.thread_id == parent)
                        and not composer.editor.toPlainText()
                    ):
                        composer.editor.setPlainText(pending_row["body"])
            if retryable:
                self.queue.appendleft(action)
            else:
                self.pending.pop(action[0], None)
                self.window.notify(
                    "Action not completed. Check your access and try again. Your draft is kept."
                )
        self.last_view = None
        self.cache.clear()
        self.files.clear()
        self.history_done.clear()
        self.window.messages.show_messages([])
        self.window.thread_messages.show_messages([])
        for workspace in self.window.store.workspaces:
            for channel in workspace.channels:
                channel.messages.clear()
        self.window.message_stack.setCurrentIndex(1)
        if retryable:
            self.window.notify(
                "Connection interrupted. Reconnecting and retrying pending messages…"
            )
        if not self.account.service or not self.account.service.user:
            self.disconnect()
            self.window.show_account()
        elif self.outbox:
            self.render_local_messages()

    def drain_queue(self):
        if self.active and self.queue:
            QTimer.singleShot(0, self.refresh)

    def enqueue(self, key, operation, completed, *, priority=False):
        if not self.active:
            return
        if any(a[0] == key for a in self.queue) or (
            self.current_action and self.current_action[0] == key
        ):
            return
        if len(self.queue) >= 100:
            self.window.notify("Too many pending actions. Wait for the connection to recover.")
            return
        action = (key, operation, completed)
        if priority:
            position = next(
                (i for i, queued in enumerate(self.queue) if queued[0][0] != "send"),
                len(self.queue),
            )
            self.queue.insert(position, action)
        else:
            self.queue.append(action)
        self.refresh()
        return True

    def refresh(self):
        if (
            not self.active
            or self.account.busy
            or (self.account.isVisible() and not self.queue)
            or time.monotonic() < self.retry_at
        ):
            return
        if self.queue:
            self.current_action = self.queue.popleft()
            _, operation, completed = self.current_action

            def done(result):
                self.current_action = None
                self.failures = 0
                self.retry_at = 0
                if self.active:
                    completed(result)
                    QTimer.singleShot(0, self.refresh)

            self.account.run(operation, done)
            return
        w, service = self.window, self.account.service
        workspace_id, channel_id, parent = w.workspace_id, w.channel_id, w.thread_id or None
        cached = dict(self.cache.get(channel_id, {}))
        reload_metadata = self.last_view is None

        def operation():
            snapshot = service.snapshot()
            if hasattr(service, "meeting_activity"):
                snapshot["meeting_activity"] = service.meeting_activity()
            allowed = {c["id"] for c in snapshot["channels"]}
            incoming = []
            if channel_id in allowed:
                for thread in [None] + ([parent] if parent else []):
                    sequences = [r["sequence"] for r in cached.values() if r["parent_id"] == thread]
                    incoming.extend(
                        service.message_page(
                            channel_id, after=max(sequences) if sequences else None, parent=thread
                        )
                    )
            ids = list(
                dict.fromkeys(
                    [r["id"] for r in incoming] + (list(cached) if reload_metadata else [])
                )
            )
            interactions = []
            if channel_id in allowed and hasattr(service, "message_interactions"):
                all_ids = list(dict.fromkeys(list(cached) + [r["id"] for r in incoming]))
                for start in range(0, len(all_ids), 100):
                    interactions.extend(service.message_interactions(all_ids[start : start + 100]))
            files = []
            if channel_id in allowed:
                for start in range(0, len(ids), 100):
                    files.extend(service.attachments_for(ids[start : start + 100]))
            if hasattr(service, "chat_inventory") and workspace_id:
                snapshot["chat"] = service.chat_inventory(workspace_id, section="recent")
                channel_details = {c["id"]: c for c in snapshot["chat"].get("channels", [])}
                snapshot["channels"] = [
                    {**c, **channel_details.get(c["id"], {})} for c in snapshot["channels"]
                ]
            credentials = service.realtime_credentials()
            return snapshot, incoming, files, credentials, interactions

        def loaded(result):
            if not self.active:
                return
            snapshot, incoming, files, credentials, interactions = result
            self.failures = 0
            self.retry_at = 0
            allowed = {c["id"] for c in snapshot["channels"]}
            self.cache = {c: rows for c, rows in self.cache.items() if c in allowed}
            self.files = {m: f for m, f in self.files.items() if f["channel_id"] in allowed}
            if channel_id in allowed:
                self.cache.setdefault(channel_id, {}).update({r["id"]: r for r in incoming})
                self.files.update({f["message_id"]: f for f in files})
                for item in interactions:
                    message_id = item["id"]
                    if message_id in self.cache[channel_id]:
                        self.cache[channel_id][message_id] = {
                            **self.cache[channel_id][message_id],
                            **item,
                        }
                        if item.get("unsent_at"):
                            self.files.pop(message_id, None)
            if self.realtime and credentials:
                self.realtime.configure(credentials)
            if (workspace_id, channel_id) != (w.workspace_id, w.channel_id):
                QTimer.singleShot(0, self.refresh)
                return
            self.apply(
                snapshot, list(self.cache.get(channel_id, {}).values()), workspace_id, channel_id
            )
            # A cursor only advances through records actually fetched while this chat is visible.
            if (
                channel_id not in getattr(w.collaboration, "manual_unread", set())
                and w.isActiveWindow()
                and w.pages.currentIndex() == 0
                and channel_id in allowed
                and w.messages.verticalScrollBar().value()
                >= w.messages.verticalScrollBar().maximum() - 4
            ):
                seq = max((r["sequence"] for r in incoming), default=0)
                if seq > self.read_marked.get(channel_id, 0):
                    self.enqueue(
                        ("read", channel_id, seq),
                        lambda: service.rpc(
                            "mark_channel_read", {"p_channel": channel_id, "p_sequence": seq}
                        ),
                        lambda _: self.read_marked.update({channel_id: seq}),
                    )
            if len(incoming) >= PAGE_SIZE:
                QTimer.singleShot(0, self.refresh)

        self.account.run(operation, loaded)

    def load_older(self, parent=None):
        if not self.active:
            return
        channel = self.window.channel_id
        if not channel or (channel, parent) in self.history_done:
            return
        rows = [r for r in self.cache.get(channel, {}).values() if r["parent_id"] == parent]
        if not rows:
            self.refresh()
            return
        before = min(r["sequence"] for r in rows)
        service = self.account.service

        def operation():
            records = service.message_page(channel, before=before, parent=parent)
            return records, service.attachments_for([r["id"] for r in records])

        def loaded(result):
            records, files = result
            self.cache.setdefault(channel, {}).update({r["id"]: r for r in records})
            self.files.update({f["message_id"]: f for f in files})
            if len(records) < PAGE_SIZE:
                self.history_done.add((channel, parent))
            self.last_view = None

        self.enqueue(("older", channel, parent, before), operation, loaded)

    def apply(self, snapshot, rows, workspace_id, channel_id):
        build = getattr(self.window, "build_dialog", None)
        if build:
            build.verify_access(snapshot)
        w = self.window
        self.outbox = {
            i: r
            for i, r in self.outbox.items()
            if r["channel_id"] in {c["id"] for c in snapshot["channels"]}
        }
        server_ids = {r["id"] for r in rows}
        for identifier in server_ids:
            self.outbox.pop(identifier, None)
        rows = rows + [dict(r) for r in self.outbox.values() if r["channel_id"] == channel_id]
        allowed_channels = {c["id"] for c in snapshot["channels"]}
        self.reaction_edits = {
            k: v for k, v in self.reaction_edits.items() if k[0] in allowed_channels
        }
        rows = self.reaction_overlay(rows, channel_id)
        self.account.snapshot = snapshot
        if hasattr(w, "collaboration"):
            w.collaboration.sync(snapshot)
        view = (snapshot, rows, workspace_id, channel_id, dict(self.files))
        if view == self.last_view:
            return
        self.last_view = view
        cursor = w.composer.editor.textCursor()
        position, anchor = cursor.position(), cursor.anchor()
        old_workspace = w.workspace_id
        spaces = workspaces_from_snapshot(snapshot, str(self.account.service.user.id))
        if not spaces:
            self.disconnect()
            self.account.loaded(snapshot)
            self.account.show()
            return
        w._save_drafts()
        w.store.workspaces = spaces
        w.workspace_id = next((x.id for x in spaces if x.id == workspace_id), spaces[0].id)
        channels = w.workspace.channels
        w.channel_id = next((c.id for c in channels if c.id == channel_id), channels[0].id)
        allowed = {(space.id, c.id) for space in spaces for c in space.channels}
        w.store.drafts = {k: v for k, v in w.store.drafts.items() if k[:2] in allowed}
        if w.channel_id == channel_id:
            names = {
                r["user_id"]: r["display_name"]
                for r in snapshot.get("directory", [])
                if r["workspace_id"] == workspace_id
            }
            w.channel.messages = message_tree(
                rows, str(self.account.service.user.id), directory=names, attachments=self.files
            )
        w._populate_rail()
        w._populate_channels()
        unread = {r["channel_id"]: r["unread"] for r in snapshot.get("unread", [])}
        for listing in (w.channel_list, w.dm_list):
            for i in range(listing.count()):
                item = listing.item(i)
                count = unread.get(item.data(Qt.ItemDataRole.UserRole), 0)
                if count:
                    item.setText(item.text() + f"  ({count})")
                item.setToolTip(f"{count} unread messages")
        w._load_channel()
        if old_workspace != w.workspace_id or not getattr(self, "pages_ready", False):
            w._render_pages()
            self.pages_ready = True
        if w.channel_id == channel_id:
            from PySide6.QtGui import QTextCursor

            cursor = w.composer.editor.textCursor()
            end = len(w.composer.editor.toPlainText().encode("utf-16-le")) // 2
            cursor.setPosition(min(anchor, end))
            cursor.setPosition(min(position, end), QTextCursor.MoveMode.KeepAnchor)
            w.composer.editor.setTextCursor(cursor)
        if w.thread_id:
            parent = next((m for m in w.channel.messages if m.id == w.thread_id), None)
            if parent:
                w.thread_messages.show_messages([parent, *parent.replies])
                w.thread_title.setText(f"Thread · {len(parent.replies)} replies")
            else:
                w.close_thread()
        w.composer.setEnabled(bool(w.channel_id))
        if not w.notice_timer.isActive():
            w.notice.setText(
                "Shared chat · ⌘⇧M direct message · ⌘⇧U attach file · "
                "⌘⇧S save selected file · ⌘⇧H older messages"
            )

    def render_local_messages(self):
        w = self.window
        if not self.active or not w.store.workspaces:
            return
        rows = list(self.cache.get(w.channel_id, {}).values())
        ids = {r["id"] for r in rows}
        rows += [
            r
            for r in self.outbox.values()
            if r["channel_id"] == w.channel_id and r["id"] not in ids
        ]
        rows = self.reaction_overlay(rows, w.channel_id)
        names = {
            r["user_id"]: r["display_name"]
            for r in self.account.snapshot.get("directory", [])
            if r["workspace_id"] == w.workspace_id
        }
        w.channel.messages = message_tree(
            rows, str(self.account.service.user.id), directory=names, attachments=self.files
        )
        w.messages.show_messages(w.channel.messages)
        w.message_stack.setCurrentIndex(0 if w.messages.model().rowCount() else 1)
        if w.thread_id:
            parent = next((m for m in w.channel.messages if m.id == w.thread_id), None)
            if parent:
                w.thread_messages.show_messages([parent, *parent.replies])

    def send(self, text, parent_id=None):
        w = self.window
        if not w.channel_id or not text.strip() or len(text.strip()) > 10000:
            w.notify("Write a message of 1–10,000 characters in an available channel.")
            return
        channel_id, workspace_id = w.channel_id, w.workspace_id
        key = (channel_id, parent_id, text.strip())
        message_id = self.pending.setdefault(key, str(uuid4()))
        editor = w.thread_composer if parent_id else w.composer
        service = self.account.service

        def operation():
            return service.rpc(
                "send_message",
                {
                    "p_id": message_id,
                    "p_channel": channel_id,
                    "p_body": text.strip(),
                    "p_parent": parent_id,
                },
            )

        def sent(_):
            self.pending.pop(key, None)
            if message_id in self.outbox:
                self.outbox[message_id]["delivery"] = ""
            self.render_local_messages()
            draft_key = (workspace_id, channel_id, parent_id or "")
            same = (w.workspace_id, w.channel_id) == (workspace_id, channel_id)
            if parent_id:
                same = same and w.thread_id == parent_id
            if same and editor.editor.toPlainText() == text:
                editor.clear()
                w.store.drafts[draft_key] = ""
            elif not same and w.store.drafts.get(draft_key) == text:
                w.store.drafts[draft_key] = ""
            w.notify("Message sent.")

        accepted = self.enqueue(("send", message_id), operation, sent, priority=True)
        if not accepted:
            return
        self.outbox[message_id] = {
            "id": message_id,
            "channel_id": channel_id,
            "sender_id": str(service.user.id),
            "body": text.strip(),
            "parent_id": parent_id,
            "created_at": datetime.now(UTC).isoformat(),
            "sequence": 0,
            "local": True,
            "delivery": "Sending…",
        }
        editor.clear()
        w.store.drafts[(workspace_id, channel_id, parent_id or "")] = ""
        self.render_local_messages()
        (w.thread_messages if parent_id else w.messages).scrollToBottom()

    def reaction_overlay(self, rows, channel):
        edits = [(key, value) for key, value in self.reaction_edits.items() if key[0] == channel]
        result = []
        for row in rows:
            for (_, message_id, emoji), edit in edits:
                if row["id"] == message_id:
                    row = with_reaction(row, emoji, edit["present"])
            result.append(row)
        return result

    def submit_reaction(self, key):
        if key in self.reaction_jobs or key not in self.reaction_edits:
            return
        channel, message_id, emoji = key
        service = self.account.service
        user = str(service.user.id)
        self.reaction_jobs.add(key)

        def operation():
            edit = dict(self.reaction_edits.get(key, {}))
            if not edit:
                return {"cancelled": True}
            try:
                service.rpc(
                    "set_message_reaction",
                    {"p_message": message_id, "p_emoji": emoji, "p_present": edit["present"]},
                )
                items = (
                    service.message_interactions([message_id])
                    if hasattr(service, "message_interactions")
                    else []
                )
                return {"edit": edit, "items": items}
            except Exception:
                return {"edit": edit, "error": True}

        def done(result):
            if (
                not self.active
                or self.account.service is not service
                or str(service.user.id) != user
            ):
                return
            self.reaction_jobs.discard(key)
            current = self.reaction_edits.get(key)
            row = self.cache.get(channel, {}).get(message_id)
            if not current or not row or result.get("cancelled"):
                self.reaction_edits.pop(key, None)
                return
            acknowledged = result["edit"]
            if not result.get("error"):
                item = next((r for r in result["items"] if r["id"] == message_id), None)
                self.cache[channel][message_id] = (
                    {**row, **item} if item else with_reaction(row, emoji, acknowledged["present"])
                )
            if current["version"] != acknowledged["version"]:
                self.submit_reaction(key)
            else:
                self.reaction_edits.pop(key, None)
                if result.get("error"):
                    self.window.notify(
                        "Reaction could not be confirmed. Check connection or access."
                    )
            self.last_view = None
            if self.window.channel_id == channel:
                self.render_local_messages()

        if not self.enqueue(("reaction", *key), operation, done, priority=True):
            self.reaction_jobs.discard(key)
            self.reaction_edits.pop(key, None)
            self.render_local_messages()
            self.window.notify("Reaction not saved. Wait for pending actions, then try again.")

    def interact(self, message_id, emoji=None, present=True):
        channel = self.window.channel_id
        service = self.account.service
        row = self.cache.get(channel, {}).get(message_id)
        if not row or row.get("unsent_at") or message_id in self.outbox:
            self.window.notify("Wait for this message to finish sending.")
            return
        if emoji is None and row["sender_id"] != str(service.user.id):
            self.window.notify("Only the sender can unsend a message.")
            return
        if emoji is not None:
            key = (channel, message_id, emoji)
            previous = self.reaction_edits.get(key, {})
            self.reaction_edits[key] = {
                "present": bool(present),
                "version": previous.get("version", 0) + 1,
            }
            self.render_local_messages()
            self.submit_reaction(key)
            return
        name = "unsend_message" if emoji is None else "set_message_reaction"
        params = {"p_message": message_id}
        if emoji is not None:
            params.update(p_emoji=emoji, p_present=present)

        def done(_):
            self.last_view = None
            self.window.notify("Message unsent." if emoji is None else "Reaction updated.")

        self.enqueue((name, message_id, emoji, present), lambda: service.rpc(name, params), done)

    def start_dm(self):
        if not self.active:
            return
        service = self.account.service
        workspace = self.window.workspace_id

        def choose(snapshot):
            people = [
                r
                for r in snapshot.get("directory", [])
                if r["workspace_id"] == workspace and r["user_id"] != str(service.user.id)
            ]
            if not people:
                self.window.notify("Invite a teammate before starting a direct message.")
                return
            labels = [r["display_name"] + " · " + r["user_id"][:8] for r in people]
            label, ok = choose_teammate(self.window, labels)
            if not ok:
                return
            recipient = people[labels.index(label)]["user_id"]

            def create():
                identifier = service.rpc(
                    "start_direct_message", {"p_workspace": workspace, "p_user": recipient}
                )
                return identifier, service.snapshot()

            def opened(result):
                identifier, data = result
                self.apply(data, [], workspace, identifier)

            self.enqueue(("dm", workspace, recipient), create, opened)

        self.enqueue(("directory", workspace), service.snapshot, choose)

    def upload(self, path=None, *, parent=None):
        if not self.active or not self.window.channel_id:
            return
        if not path or isinstance(path, bool):
            parent = parent or (
                self.window.thread_id if self.window.thread_composer.editor.hasFocus() else None
            )
            path, _ = QFileDialog.getOpenFileName(self.window, "Attach a file · up to 10 MB")
        if not path:
            return
        # Capture context before the dialog/worker runs; changing channels never redirects uploads.
        channel = self.window.channel_id
        service = self.account.service
        key = ("upload", channel, parent, str(Path(path).resolve()))
        identifier = self.pending.setdefault(key, str(uuid4()))

        def done(_):
            self.pending.pop(key, None)
            self.window.notify("File shared. Select its message and press ⌘⇧S to save a copy.")

        self.enqueue(
            key, lambda: service.upload_attachment(identifier, channel, path, parent), done
        )

    def download(self):
        if not self.active:
            return
        view = (
            self.window.thread_messages
            if self.window.thread_messages.hasFocus()
            else self.window.messages
        )
        index = view.currentIndex()
        message = index.data(MESSAGE_ROLE) if index.isValid() else None
        if message is None or not message.attachment_id:
            self.window.notify("Select a message with a file before saving it.")
            return
        destination, _ = QFileDialog.getSaveFileName(
            self.window, "Save attachment", Path(message.attachment).name
        )
        if not destination:
            return
        service, identifier = self.account.service, message.attachment_id

        def operation():
            data = service.download_attachment(identifier)
            save_download(destination, data)

        self.enqueue(
            ("download", identifier, destination),
            operation,
            lambda _: self.window.notify("File saved."),
        )
