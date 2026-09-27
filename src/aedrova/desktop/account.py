"""Non-blocking account and workspace administration, separate from sample chat."""

from threading import Event

from PySide6.QtCore import QObject, QRunnable, QSettings, Qt, QThreadPool, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from aedrova.desktop.brand import BrandMark
from aedrova.desktop.dialogs import button, label
from aedrova.identity.oauth import google_sign_in
from aedrova.identity.service import Connection, IdentityService


class ResultSignals(QObject):
    finished = Signal(object, bool)


class AccountJob(QRunnable):
    def __init__(self, operation):
        super().__init__()
        self.operation = operation
        self.signals = ResultSignals()

    def run(self):
        try:
            result = self.operation()
            self.signals.finished.emit(result, True)
        except Exception:
            # Never surface raw provider exceptions: they may include credentials or tokens.
            self.signals.finished.emit(None, False)
        finally:
            self.operation = None


class AccountDialog(QDialog):
    def __init__(self, parent=None, *, settings=None, factory=IdentityService):
        super().__init__(parent)
        self.settings = settings if settings is not None else QSettings("Aedrova", "Desktop")
        self.factory = factory
        self.service = None
        self.busy = False
        self.oauth_cancel = None
        QApplication.instance().aboutToQuit.connect(self.cancel_google)
        self.snapshot = {
            "workspaces": [],
            "channels": [],
            "members": [],
            "invitations": [],
            "agent_preferences": [],
        }
        self.setWindowTitle("Aedrova · Account & workspaces")
        self.resize(720, 780)
        self.setMinimumSize(600, 540)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        top = QHBoxLayout()
        top.addWidget(BrandMark(54))
        top.addWidget(label("Your space to build.", "heading"))
        top.addStretch()
        layout.addLayout(top)
        self.status = label(
            "Your team. Your ideas. One place to build.",
            "muted",
            wrap=True,
        )
        layout.addWidget(self.status)
        self.pages = QStackedWidget()
        self.pages.setObjectName("AccountPages")
        layout.addWidget(self.pages)
        self._login_page()
        self._workspace_page()
        self._onboarding_page()
        self.cancel_login = button("Cancel sign-in")
        self.cancel_login.hide()
        self.cancel_login.clicked.connect(self.cancel_google)
        layout.addWidget(self.cancel_login)
        close = button("Done")
        close.clicked.connect(self.accept)
        layout.addWidget(close, alignment=Qt.AlignmentFlag.AlignRight)

    def add_page(self, page):
        page.setObjectName("AccountPage")
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        self.pages.addWidget(scroll)

    def field(self, placeholder, *, password=False):
        result = QLineEdit()
        result.setPlaceholderText(placeholder)
        result.setAccessibleName(placeholder)
        if password:
            result.setEchoMode(QLineEdit.EchoMode.Password)
        return result

    def _login_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(18)
        layout.addStretch()
        layout.addWidget(label("Welcome to Aedrova", "heading"))
        layout.addWidget(label("Pick up where your next idea begins.", "muted", wrap=True))
        self.google_button = button("Continue with Google", role="primary")
        self.google_button.setMinimumHeight(48)
        self.google_button.clicked.connect(self.start_google)
        layout.addWidget(self.google_button)
        layout.addWidget(label("Sign in securely in your browser, then return here.", "muted"))
        layout.addStretch()
        self.add_page(page)

    def start_google(self):
        if self.busy:
            return
        try:
            connection = Connection.for_application()
            if connection is None:
                raise ValueError("Unconfigured build")
        except (ValueError, KeyError, OSError):
            self.status.setText(
                "Sign-in is not available in this preview yet. Please try a configured build."
            )
            return
        self.oauth_cancel = Event()
        self.cancel_login.show()

        def operation():
            self.service = self.factory(connection)
            return google_sign_in(self.service, self.oauth_cancel)

        self.run(operation, self.authenticated)
        self.status.setText(
            "Continue with Google in your browser. We’ll bring your workspace here."
        )

    def cancel_google(self):
        if self.oauth_cancel is not None:
            self.oauth_cancel.set()
            self.status.setText("Cancelling sign-in…")

    def _workspace_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)
        self.account_label = label("", "title", wrap=True)
        layout.addWidget(self.account_label)
        self.workspaces = QComboBox()
        self.workspaces.setAccessibleName("Your connected workspaces")
        self.workspaces.currentIndexChanged.connect(self.render_workspace)
        layout.addWidget(self.workspaces)
        layout.addWidget(label("Your team’s agent", "title"))
        agent_row = QHBoxLayout()
        self.agent_name = self.field("Agent nickname")
        self.agent_name.setMaxLength(32)
        self.agent_provider = self.provider_choice()
        self.save_agent = button("Save agent name")
        self.save_agent.clicked.connect(
            lambda: self.mutate(
                "set_agent_preferences",
                {
                    "p_workspace": self.workspace_id(),
                    "p_nickname": self.agent_name.text().strip(),
                    "p_provider": self.agent_provider.currentData(),
                },
            )
        )
        agent_row.addWidget(self.agent_name)
        agent_row.addWidget(self.agent_provider)
        agent_row.addWidget(self.save_agent)
        layout.addLayout(agent_row)
        layout.addWidget(
            label(
                "A shared name for your team. Aedrova is still your workspace.", "muted", wrap=True
            )
        )
        row = QHBoxLayout()
        create = button("Create workspace")
        create.clicked.connect(lambda: self.pages.setCurrentIndex(2))
        row.addWidget(create)
        layout.addLayout(row)
        row = QHBoxLayout()
        self.invite_code = self.field("Invitation code", password=True)
        row.addWidget(self.invite_code)
        join = button("Join workspace")
        join.clicked.connect(
            lambda: self.mutate("accept_invitation", {"p_token": self.invite_code.text().strip()})
        )
        row.addWidget(join)
        layout.addLayout(row)
        layout.addWidget(label("Channels", "title"))
        self.channels = QListWidget()
        self.channels.setProperty("accountList", True)
        self.channels.setAccessibleName("Authorized channels")
        self.channels.setFixedHeight(110)
        layout.addWidget(self.channels)
        row = QHBoxLayout()
        self.channel_name = self.field("New channel name")
        self.private = QCheckBox("Private")
        row.addWidget(self.channel_name)
        row.addWidget(self.private)
        create_channel = button("Create channel")
        create_channel.clicked.connect(
            lambda: self.mutate(
                "create_channel",
                {
                    "p_workspace": self.workspace_id(),
                    "p_name": self.channel_name.text(),
                    "p_private": self.private.isChecked(),
                },
            )
        )
        row.addWidget(create_channel)
        layout.addLayout(row)
        layout.addWidget(label("Members & access", "title"))
        self.members = QListWidget()
        self.members.setProperty("accountList", True)
        self.members.setAccessibleName("Workspace members")
        self.members.setFixedHeight(100)
        layout.addWidget(self.members)
        row = QHBoxLayout()
        self.role = QComboBox()
        self.role.addItems(["member", "guest", "admin"])
        self.role.setAccessibleName("Member or invitation role")
        row.addWidget(self.role)
        for title, operation in [
            ("Change role", "role"),
            ("Remove member", "remove"),
            ("Grant channel", "grant"),
            ("Revoke channel", "revoke"),
        ]:
            control = button(title)
            control.clicked.connect(lambda checked=False, op=operation: self.member_action(op))
            row.addWidget(control)
        layout.addLayout(row)
        layout.addWidget(
            label(
                "Select a member and channel to change access.\nOnly owners can change roles.",
                "muted",
                wrap=True,
            )
        )
        row = QHBoxLayout()
        self.invite_email = self.field("Teammate email")
        row.addWidget(self.invite_email)
        invite = button("Create invitation")
        invite.clicked.connect(
            lambda: self.mutate(
                "create_invitation",
                {
                    "p_workspace": self.workspace_id(),
                    "p_email": self.invite_email.text().strip(),
                    "p_role": self.role.currentText(),
                },
            )
        )
        row.addWidget(invite)
        layout.addLayout(row)
        self.generated_code = self.field("Invitation code appears here once")
        self.generated_code.setReadOnly(True)
        layout.addWidget(self.generated_code)
        layout.addWidget(
            label(
                "Share this single-use code with the named teammate.\n"
                "It expires in seven days; no email is sent.",
                "muted",
                wrap=True,
            )
        )
        self.invitations = QListWidget()
        self.invitations.setProperty("accountList", True)
        self.invitations.setAccessibleName("Pending invitations")
        self.invitations.setFixedHeight(85)
        layout.addWidget(self.invitations)
        row = QHBoxLayout()
        revoke = button("Revoke selected invitation")
        revoke.clicked.connect(self.revoke_invitation)
        row.addWidget(revoke)
        refresh = button("Refresh")
        refresh.clicked.connect(self.refresh)
        row.addWidget(refresh)
        signout = button("Sign out")
        signout.clicked.connect(self.sign_out)
        row.addWidget(signout)
        layout.addLayout(row)
        self.add_page(page)

    def provider_choice(self):
        choice = QComboBox()
        choice.setAccessibleName("Preferred building agent")
        choice.addItem("Codex", "codex")
        choice.addItem("Claude Code", "claude_code")
        return choice

    def _onboarding_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)
        layout.addStretch()
        layout.addWidget(label("Make it your team’s space.", "heading", wrap=True))
        layout.addWidget(
            label("Give your workspace a name, then introduce your agent.", "muted", wrap=True)
        )
        self.onboarding_workspace = self.field("Workspace name")
        self.onboarding_workspace.setMaxLength(80)
        layout.addWidget(self.onboarding_workspace)
        layout.addWidget(label("What should we call your agent?", "title"))
        self.onboarding_nickname = self.field("e.g. Nova, Atlas, or Sparky")
        self.onboarding_nickname.setMaxLength(32)
        self.onboarding_nickname.setText("Nova")
        layout.addWidget(self.onboarding_nickname)
        self.onboarding_provider = self.provider_choice()
        layout.addWidget(self.onboarding_provider)
        layout.addWidget(
            label(
                "Your team shares this nickname. You can change it later.\n"
                "Building will be available in a later milestone.",
                "muted",
                wrap=True,
            )
        )
        create = button("Create our workspace", role="primary")
        create.clicked.connect(self.complete_onboarding)
        layout.addWidget(create)
        layout.addWidget(label("Already invited?", "title"))
        self.onboarding_invite = self.field("Paste your invitation code", password=True)
        layout.addWidget(self.onboarding_invite)
        join = button("Join my team")
        join.clicked.connect(
            lambda: self.mutate(
                "accept_invitation",
                {
                    "p_token": self.onboarding_invite.text().strip(),
                },
            )
        )
        layout.addWidget(join)
        back = button("Back to account")
        back.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        layout.addWidget(back)
        layout.addStretch()
        self.add_page(page)

    def complete_onboarding(self):
        name = self.onboarding_workspace.text().strip()
        nickname = self.onboarding_nickname.text().strip()
        if (
            not name
            or not nickname
            or not nickname[0].isalnum()
            or any(not (character.isalnum() or character in " _-") for character in nickname)
        ):
            self.status.setText(
                "Add a workspace name. Nicknames can use letters, numbers, spaces, - or _."
            )
            return
        self.mutate(
            "onboard_workspace",
            {
                "p_name": name,
                "p_nickname": nickname,
                "p_provider": self.onboarding_provider.currentData(),
            },
        )

    def workspace_id(self):
        return self.workspaces.currentData()

    def run(self, operation, success):
        if self.busy:
            return
        self.busy = True
        self.pages.setEnabled(False)
        self.status.setText("Connecting securely…")
        self.success = success
        self.job = AccountJob(operation)
        self.job.signals.finished.connect(self.finished_job)
        QThreadPool.globalInstance().start(self.job)

    @Slot(object, bool)
    def finished_job(self, result, ok):
        cancelled = self.oauth_cancel is not None and self.oauth_cancel.is_set()
        self.oauth_cancel = None
        self.cancel_login.hide()
        self.busy = False
        self.pages.setEnabled(True)
        if ok:
            self.success(result)
        else:
            self.status.setText(
                "Request unsuccessful. Check your connection or permissions.\n"
                "Refresh before retrying a timed-out action."
            )
            if cancelled:
                self.status.setText("Sign-in cancelled. You can try again whenever you’re ready.")
            self.clear_connected()
            if self.service is None or self.service.user is None:
                self.pages.setCurrentIndex(0)

    def authenticated(self, user):
        if user is None:
            self.status.setText("Sign-in did not finish. Please try again.")
            return
        self.show()
        self.raise_()
        self.activateWindow()
        self.account_label.setText(user.email or "Signed in")
        self.pages.setCurrentIndex(1)
        self.refresh()

    def refresh(self):
        self.generated_code.clear()
        self.run(self.service.snapshot, self.loaded)

    def loaded(self, snapshot):
        previous = self.workspace_id()
        self.snapshot = snapshot
        self.workspaces.blockSignals(True)
        self.workspaces.clear()
        for workspace in snapshot["workspaces"]:
            self.workspaces.addItem(workspace["name"], workspace["id"])
        index = self.workspaces.findData(previous)
        if index >= 0:
            self.workspaces.setCurrentIndex(index)
        self.workspaces.blockSignals(False)
        self.render_workspace()
        self.pages.setCurrentIndex(1 if snapshot["workspaces"] else 2)
        self.status.setText(
            "Connected · workspace access is enforced by the server. Chat remains a local preview."
        )

    def render_workspace(self):
        workspace = self.workspace_id()
        self.generated_code.clear()
        preference = next(
            (
                p
                for p in self.snapshot.get("agent_preferences", [])
                if p["workspace_id"] == workspace
            ),
            {},
        )
        self.agent_name.setText(preference.get("nickname", ""))
        provider_index = self.agent_provider.findData(preference.get("provider", "codex"))
        self.agent_provider.setCurrentIndex(max(0, provider_index))
        user_id = str(self.service.user.id) if self.service and self.service.user else None
        can_edit = any(
            m["workspace_id"] == workspace
            and m["user_id"] == user_id
            and m["role"] in ("owner", "admin")
            for m in self.snapshot["members"]
        )
        for control in (self.agent_name, self.agent_provider, self.save_agent):
            control.setEnabled(can_edit)
        for widget, key in [
            (self.channels, "channels"),
            (self.members, "members"),
            (self.invitations, "invitations"),
        ]:
            widget.clear()
            for record in self.snapshot[key]:
                if record["workspace_id"] != workspace:
                    continue
                if key == "channels":
                    title = ("Private · " if record["private"] else "# ") + record["name"]
                    value = record["id"]
                elif key == "members":
                    title, value = (
                        f"{record.get('email', record['user_id'])} · {record['role']}",
                        record["user_id"],
                    )
                else:
                    if record["accepted_at"] or record["revoked_at"]:
                        continue
                    title, value = (
                        f"{record['email']} · {record['role']}"
                        f" · expires {record['expires_at'][:10]}",
                        record["id"],
                    )
                item = QListWidgetItem(title)
                item.setData(Qt.ItemDataRole.UserRole, value)
                widget.addItem(item)

    def mutate(self, name, parameters):
        if any(value is None for value in parameters.values()):
            self.status.setText("Choose a workspace first.")
            return

        def operation():
            value = self.service.rpc(name, parameters)
            return value, self.service.snapshot()

        def completed(result):
            value, snapshot = result
            self.loaded(snapshot)
            if name in ("onboard_workspace", "accept_invitation"):
                index = self.workspaces.findData(value)
                if index >= 0:
                    self.workspaces.setCurrentIndex(index)
            self.invite_code.clear()
            self.onboarding_invite.clear()
            if name == "create_invitation":
                self.generated_code.setText(value)
                self.status.setText(
                    "Invitation created. Copy the code now and share it with the named teammate."
                )
            else:
                self.status.setText("Saved. Your workspace access is up to date.")

        self.run(operation, completed)

    def member_action(self, action):
        member = self.members.currentItem()
        channel = self.channels.currentItem()
        if not member or (action in ("grant", "revoke") and not channel):
            self.status.setText("Select a member and, when changing channel access, a channel.")
            return
        user = member.data(Qt.ItemDataRole.UserRole)
        if action in ("grant", "revoke"):
            self.mutate(
                "set_channel_member",
                {
                    "p_channel": channel.data(Qt.ItemDataRole.UserRole),
                    "p_user": user,
                    "p_allowed": action == "grant",
                },
            )
        else:
            parameters = {"p_workspace": self.workspace_id(), "p_user": user}
            if action == "role":
                parameters["p_role"] = self.role.currentText()
            self.mutate("set_member_role" if action == "role" else "remove_member", parameters)

    def revoke_invitation(self):
        item = self.invitations.currentItem()
        if item:
            self.mutate("revoke_invitation", {"p_invitation": item.data(Qt.ItemDataRole.UserRole)})

    def clear_connected(self):
        self.snapshot = {
            "workspaces": [],
            "channels": [],
            "members": [],
            "invitations": [],
            "agent_preferences": [],
        }
        self.workspaces.clear()
        self.render_workspace()
        self.generated_code.clear()
        self.invite_code.clear()
        self.account_label.clear()
        self.onboarding_invite.clear()
        self.onboarding_workspace.clear()
        self.onboarding_nickname.setText("Nova")

    def sign_out(self):
        self.clear_connected()

        def completed(_):
            self.service = None
            self.pages.setCurrentIndex(0)
            self.status.setText("Signed out. Your session has been removed from this app.")

        self.run(self.service.sign_out, completed)

    def done(self, result):
        if self.busy:
            self.cancel_google()
            self.status.setText("Finishing the current request…")
            return
        self.generated_code.clear()
        super().done(result)
