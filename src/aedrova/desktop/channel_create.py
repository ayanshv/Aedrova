"""Immediate, focused channel creation; server-confirmed authority and publication."""

from uuid import uuid4

from PySide6.QtWidgets import QCheckBox, QHBoxLayout, QLineEdit, QVBoxLayout
from shiboken6 import isValid

from aedrova.desktop.brand import BrandMark
from aedrova.desktop.controls import AppDialog
from aedrova.desktop.dialogs import button, label


class CreateChannelDialog(AppDialog):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.bridge = window.connected
        self.service = self.bridge.account.service
        self.workspace = window.workspace_id
        self.pending = False
        self.bridge.account.session_closed.connect(self.invalidate)
        self.setWindowTitle("Aedrova · Create new channel")
        self.resize(440, 350)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(16)
        layout.addWidget(BrandMark(40))
        layout.addWidget(label("Create a new channel", "heading"))
        layout.addWidget(label("A place for a project, topic or team.", "muted", wrap=True))
        self.name = QLineEdit()
        self.name.setPlaceholderText("e.g. product-design")
        self.name.setAccessibleName("New channel name")
        self.name.setMaxLength(80)
        layout.addWidget(self.name)
        self.private = QCheckBox("Private · invited people only")
        role = next(
            (
                m["role"]
                for m in self.bridge.account.snapshot.get("members", [])
                if m["workspace_id"] == self.workspace and m["user_id"] == str(self.service.user.id)
            ),
            "",
        )
        self.private.setEnabled(role in {"owner", "admin"})
        layout.addWidget(self.private)
        self.notice = label("", "muted", wrap=True)
        layout.addWidget(self.notice)
        actions = QHBoxLayout()
        cancel = button("Cancel", role="outline")
        cancel.clicked.connect(self.reject)
        self.create = button("Create channel", role="primary")
        self.create.setEnabled(False)
        self.create.clicked.connect(self.submit)
        self.name.returnPressed.connect(self.submit)
        self.name.textChanged.connect(
            lambda: self.create.setEnabled(bool(self.name.text().strip()) and not self.pending)
        )
        actions.addWidget(cancel)
        actions.addWidget(self.create)
        layout.addLayout(actions)

    def submit(self):
        name = self.name.text().strip()
        if self.pending or not name:
            return
        if not self.current():
            self.invalidate()
            return
        self.pending = True
        self.create.setEnabled(False)
        self.create.setText("Creating…")
        self.notice.setText("Your channel is being created.")
        private = self.private.isChecked()

        def operation():
            try:
                identifier = self.service.rpc(
                    "create_channel",
                    {
                        "p_workspace": self.workspace,
                        "p_name": name,
                        "p_private": private,
                    },
                )
            except Exception:
                # Never retry a creation automatically after an ambiguous response.
                return None, None
            try:
                snapshot = self.service.snapshot()
            except Exception:
                snapshot = None
            return identifier, snapshot

        def completed(result):
            if not self.current():
                if isValid(self):
                    self.invalidate()
                return
            identifier, snapshot = result
            if identifier and snapshot is not None:
                self.bridge.apply(snapshot, [], self.workspace, identifier)
                if isValid(self):
                    self.accept()
                return
            if isValid(self):
                self.create.setText("Close and refresh")
                self.notice.setText(
                    "Channel created. Refresh your workspace to open it."
                    if identifier
                    else "Could not confirm creation. Refresh channels before trying again. "
                    "Your channel name is kept."
                )
                # Unknown outcomes must not expose a second Create action.
                self.create.clicked.disconnect(self.submit)
                self.create.clicked.connect(self.close_and_refresh)
                self.create.setEnabled(True)

        if not self.bridge.enqueue(
            ("create-channel", self.workspace, str(uuid4())), operation, completed, priority=True
        ):
            self.pending = False
            self.create.setText("Create channel")
            self.create.setEnabled(True)
            self.notice.setText("Connection busy. Try again in a moment.")

    def current(self):
        return (
            self.bridge.active
            and self.window.workspace_id == self.workspace
            and self.bridge.account.service is self.service
            and self.service.user is not None
        )

    def invalidate(self):
        self.pending = True
        self.name.clear()
        self.reject()

    def close_and_refresh(self):
        self.accept()
        if self.current():
            self.bridge.refresh()
