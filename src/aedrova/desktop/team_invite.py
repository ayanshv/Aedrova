from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QHBoxLayout, QVBoxLayout

from aedrova.desktop.controls import AppDialog
from aedrova.desktop.dialogs import button, label


def open_workspace_join_code(window, workspace):
    connected = getattr(window, "connected", None)
    if not connected or not connected.active or str(window.workspace_id) != str(workspace):
        return False
    account = connected.account
    user = getattr(account.service, "user", None)
    if not user or not any(
        str(member.get("user_id")) == str(user.id)
        and str(member.get("workspace_id")) == str(workspace)
        and member.get("role") in {"owner", "admin"}
        for member in account.snapshot.get("members", [])
    ):
        return False
    previous = getattr(window, "onboarding_team_invite", None)
    if previous is not None and not previous.closed:
        return True
    invite = TeamInviteDialog(window, workspace, connected)
    window.onboarding_team_invite = invite
    invite.finished.connect(lambda _: window.composer.editor.setFocus())
    invite.open()
    return True


class TeamInviteDialog(AppDialog):
    def __init__(self, window, workspace, connected):
        super().__init__(window)
        self.setWindowTitle("Invite your team")
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setMinimumWidth(410)
        self.workspace = workspace
        self.connected = connected
        self.finished.connect(lambda _: setattr(self, "closed", True))
        self.closed = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)
        layout.addWidget(label("Invite your team", "heading"))
        layout.addWidget(
            label("Teammates can enter this code when joining a workspace.", "muted", wrap=True)
        )

        row = QHBoxLayout()
        self.code = label("")
        font = self.code.font()
        font.setPointSize(22)
        self.code.setFont(font)
        self.code.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.code.setAccessibleName("Workspace join code")
        row.addWidget(self.code, 1)
        self.copy = button("Copy", "Copy join code", "outline")
        self.copy.setEnabled(False)
        self.copy.clicked.connect(lambda: self.copy_code())
        row.addWidget(self.copy)
        self.copy_message = button("Copy invite", "Copy invitation message", "outline")
        self.copy_message.setEnabled(False)
        self.copy_message.clicked.connect(lambda: self.copy_code(invitation=True))
        row.addWidget(self.copy_message)
        layout.addLayout(row)

        self.status = label("", "muted", wrap=True)
        layout.addWidget(self.status)
        actions = QHBoxLayout()
        self.retry = button("Try again", role="outline")
        self.retry.clicked.connect(self.load_code)
        self.retry.hide()
        actions.addWidget(self.retry)
        actions.addStretch()
        done = button("Open workspace", role="primary")
        done.clicked.connect(self.accept)
        actions.addWidget(done)
        layout.addLayout(actions)
        QTimer.singleShot(0, self.load_code)

    def load_code(self):
        self.status.setText("Creating a join code…")
        self.retry.hide()
        service = self.connected.account.service

        def request():
            try:
                return service.rpc("create_workspace_join_code", {"p_workspace": self.workspace})
            except Exception:
                return None

        def received(code):
            if self.closed or self.connected.account.service is not service:
                return
            if not isinstance(code, str) or not code:
                self.status.setText("Couldn’t create a join code. Try again or open the workspace.")
                self.retry.show()
                return
            self.code.setText(code)
            self.copy.setEnabled(True)
            self.copy_message.setEnabled(True)
            self.status.setText("Valid for 7 days or 20 joins. Share it only with your team.")

        if not self.connected.enqueue(("workspace-join-code", self.workspace), request, received):
            received(None)

    def copy_code(self, *, invitation=False):
        code = self.code.text()
        if invitation:
            QApplication.clipboard().setText(f"Join my Aedrova workspace with this code: {code}")
            self.copy_message.setText("Copied")
        else:
            QApplication.clipboard().setText(code)
            self.copy.setText("Copied")
