"""Live, anchored workspace search without a separate dialog window."""

from PySide6.QtCore import QEvent, QPoint, Qt, QTimer
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from aedrova.desktop.popup_depth import paint_depth


class SearchResults(QWidget):
    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        paint_depth(painter, self.rect(), self)


class WorkspaceSearch(QLineEdit):
    def __init__(self, host):
        super().__init__(host)
        self.host = host
        self.generation = 0
        self.scope = None
        self.setObjectName("Search")
        self.setPlaceholderText("Search your workspace   ⌘F")
        self.setAccessibleName("Search your workspace")
        self.setToolTip("Search messages, people, channels and files · ⌘F · ⌘K")
        self.setMaxLength(256)
        self.menu = SearchResults(host)
        self.menu.setObjectName("WorkspaceSearchResults")
        self.menu.setStyleSheet(
            "QWidget#WorkspaceSearchResults { background: transparent; border: none; }"
            "QListWidget#ChatResults { background: transparent; border: none; outline: none; }"
        )
        self.menu.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)
        layout = QVBoxLayout(self.menu)
        layout.setContentsMargins(36, 28, 36, 36)
        layout.setSpacing(8)
        self.results = QListWidget()
        self.results.setObjectName("ChatResults")
        self.results.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.results.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.results.setTextElideMode(Qt.TextElideMode.ElideRight)
        layout.addWidget(self.results)
        self.notice = QLabel()
        self.notice.setProperty("role", "muted")
        layout.addWidget(self.notice)
        self.results.itemClicked.connect(self.open_item)
        self.menu.hide()
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self.remote)
        self.textChanged.connect(self.refresh)
        QApplication.instance().installEventFilter(self)

    def current_scope(self):
        owner = getattr(self.host, "collaboration", None)
        connected = owner.connected() if owner else None
        service = connected.account.service if connected else None
        return (
            self.host.workspace_id,
            connected,
            service,
            str(getattr(getattr(service, "user", None), "id", "")),
        )

    def dismiss(self):
        self.generation += 1
        self.timer.stop()
        self.menu.hide()
        self.results.clear()

    def activate(self):
        self.setFocus()
        self.selectAll()
        self.refresh()

    def refresh(self):
        owner = getattr(self.host, "collaboration", None)
        if owner is None:
            return
        self.generation += 1
        self.scope = self.current_scope()
        query = self.text().strip()
        data = owner.local_inventory(query, "search", None)
        # Retain jumping between already-authorized, locally loaded workspaces.
        channels = []
        for workspace in self.host.store.workspaces:
            for channel in workspace.channels:
                if query.casefold() in f"{channel.name} {workspace.name}".casefold():
                    channels.append(
                        {
                            "id": channel.id,
                            "name": channel.name,
                            "workspace": workspace.id,
                            "topic": workspace.name,
                        }
                    )
        self.local_channels = channels
        self.render(data)
        self.position_menu()
        self.menu.show()
        self.menu.raise_()
        self.timer.start()

    def position_menu(self):
        anchor = self.mapTo(self.host, QPoint(0, self.height()))
        width = min(max(self.width() + 40, 420), self.host.width() - 16)
        x = max(8, min(anchor.x() - 20, self.host.width() - width - 8))
        y = max(0, anchor.y() - 12)
        desired = min(420, max(130, self.results.count() * 53 + 84))
        height = min(desired, self.host.height() - y - 8)
        self.menu.setGeometry(x, y, width, height)

    def remote(self):
        if not self.menu.isVisible() or self.scope != self.current_scope():
            self.dismiss()
            return
        workspace, connected, service, _user = self.scope
        if connected is None or not hasattr(service, "chat_inventory"):
            return
        generation, query, scope = self.generation, self.text().strip(), self.scope
        self.notice.setText("Updating results…")

        def loaded(data):
            if (
                self.menu.isVisible()
                and generation == self.generation
                and scope == self.current_scope()
            ):
                self.generation += 1
                self.render(data)

        def timed_out():
            if (
                self.menu.isVisible()
                and generation == self.generation
                and scope == self.current_scope()
            ):
                self.notice.setText("Showing available results. Type to retry online search.")

        QTimer.singleShot(10000, self, timed_out)
        connected.enqueue(
            ("header-search", workspace, generation, query),
            lambda: service.chat_inventory(workspace, query, "search", None),
            loaded,
        )

    def render(self, data):
        self.results.clear()
        channels = list(self.local_channels)
        seen = {(c["workspace"], c["id"]) for c in channels}
        for channel in data.get("channels", []):
            if (self.host.workspace_id, channel["id"]) not in seen:
                channels.append(dict(channel, workspace=self.host.workspace_id))
        for channel in channels[:30]:
            self.add(
                f"# {channel['name']} · {channel.get('topic') or 'Conversation'}",
                {"channel": channel["id"], "workspace": channel["workspace"]},
            )
        for person in data.get("people", [])[:20]:
            self.add(person["display_name"], {"person": person})
        for message in data.get("messages", [])[:40]:
            content = message.get("filename") or message.get("body", "")
            self.add(
                f"{message['author']} · #{message['channel']}\n{content[:180]}",
                {"message": message},
            )
        if self.results.count():
            self.results.setCurrentRow(0)
        self.position_menu()
        self.notice.setText(
            "↑ ↓ to browse · Enter to open"
            if self.results.count()
            else "No results. Try another search."
        )

    def add(self, text, data):
        item = QListWidgetItem(text)
        item.setData(Qt.ItemDataRole.UserRole, data)
        item.setToolTip(text)
        self.results.addItem(item)

    def open_item(self, item):
        if item is None:
            return
        if self.scope != self.current_scope():
            self.dismiss()
            return
        data = item.data(Qt.ItemDataRole.UserRole)
        self.dismiss()
        if "channel" in data:
            self.host.jump_to(data["workspace"], data["channel"])
        elif "person" in data:
            self.host.collaboration.profile(data["person"])
        else:
            self.host.collaboration.open_message(data["message"])

    def event(self, event):
        if (
            event.type() == QEvent.Type.ShortcutOverride
            and event.key() == Qt.Key.Key_Escape
            and self.menu.isVisible()
        ):
            event.accept()
            return True
        return super().event(event)

    def keyPressEvent(self, event):  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.dismiss()
            return
        if event.key() in (Qt.Key.Key_Down, Qt.Key.Key_Up):
            if not self.menu.isVisible():
                self.refresh()
            delta = 1 if event.key() == Qt.Key.Key_Down else -1
            self.results.setCurrentRow(
                max(0, min(self.results.count() - 1, self.results.currentRow() + delta))
            )
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.open_item(self.results.currentItem())
            return
        super().keyPressEvent(event)

    def eventFilter(self, watched, event):  # noqa: N802
        if watched is self and event.type() in (QEvent.Type.FocusIn, QEvent.Type.MouseButtonPress):
            self.refresh()
        if watched is self.host and event.type() in (QEvent.Type.Resize, QEvent.Type.Move):
            self.position_menu()
        if self.menu.isVisible():
            if self.scope != self.current_scope():
                self.dismiss()
            elif event.type() == QEvent.Type.MouseButtonPress and isinstance(watched, QWidget):
                if watched is not self and not self.menu.isAncestorOf(watched):
                    self.dismiss()
            elif watched is self.host and event.type() in (
                QEvent.Type.Hide,
                QEvent.Type.WindowDeactivate,
            ):
                self.dismiss()
        return False
