"""Non-blocking account and workspace administration, separate from sample chat."""

from PySide6.QtCore import QObject, QRunnable, QSettings, Qt, QThreadPool, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
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
        self.snapshot = {"workspaces": [], "channels": [], "members": [], "invitations": []}
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
            "Connect your account. Your session stays on this Mac until you sign out or quit.",
            "muted",
            wrap=True,
        )
        layout.addWidget(self.status)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.pages = QStackedWidget()
        self.pages.setObjectName("AccountPages")
        scroll.setWidget(self.pages)
        layout.addWidget(scroll)
        self._login_page()
        self._workspace_page()
        close = button("Done")
        close.clicked.connect(self.accept)
        layout.addWidget(close, alignment=Qt.AlignmentFlag.AlignRight)

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
        layout.setSpacing(14)
        layout.addWidget(label("Welcome to Aedrova", "title"))
        layout.addWidget(
            label(
                "Use a Supabase project with the Aedrova identity migration installed.",
                "muted",
                wrap=True,
            )
        )
        form = QFormLayout()
        self.url = self.field("https://your-project.supabase.co")
        self.key = self.field("Public publishable key", password=True)
        try:
            env = Connection.from_environment()
        except ValueError:
            env = None
        self.url.setText(env.url if env else self.settings.value("supabaseUrl", ""))
        self.key.setText(env.public_key if env else self.settings.value("supabasePublicKey", ""))
        self.email = self.field("Email address")
        self.password = self.field("Password", password=True)
        self.code = self.field("Email confirmation code")
        for name, field in [
            ("Project URL", self.url),
            ("Public key", self.key),
            ("Email", self.email),
            ("Password", self.password),
            ("Confirmation code", self.code),
        ]:
            form.addRow(name, field)
        layout.addLayout(form)
        row = QHBoxLayout()
        for title, mode in [
            ("Sign in", "signin"),
            ("Create account", "signup"),
            ("Confirm email", "verify"),
        ]:
            control = button(title, role="primary" if mode == "signin" else "")
            control.clicked.connect(lambda checked=False, m=mode: self.authenticate(m))
            row.addWidget(control)
        layout.addLayout(row)
        layout.addWidget(
            label(
                "Confirm your email using the email link, then sign in.\n"
                "If you received a code, enter it above.",
                "muted",
                wrap=True,
            )
        )
        layout.addWidget(
            label(
                "Chat remains a local preview. Connected chat arrives in milestone 4.",
                "muted",
                wrap=True,
            )
        )
        layout.addStretch()
        self.pages.addWidget(page)

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
        row = QHBoxLayout()
        self.workspace_name = self.field("New workspace name")
        row.addWidget(self.workspace_name)
        create = button("Create workspace")
        create.clicked.connect(
            lambda: self.mutate("create_workspace", {"p_name": self.workspace_name.text()})
        )
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
        self.pages.addWidget(page)

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
        self.busy = False
        self.pages.setEnabled(True)
        if ok:
            self.success(result)
        else:
            self.status.setText(
                "Request unsuccessful. Check your connection or permissions.\n"
                "Refresh before retrying a timed-out action."
            )
            self.clear_connected()
            if self.service is None or self.service.user is None:
                self.pages.setCurrentIndex(0)

    def authenticate(self, mode):
        try:
            connection = Connection(self.url.text().strip().rstrip("/"), self.key.text().strip())
        except ValueError as exc:
            self.status.setText(str(exc))
            return
        email, password, code = (
            self.email.text().strip(),
            self.password.text(),
            self.code.text().strip(),
        )
        if not email or (mode != "verify" and not password) or (mode == "verify" and not code):
            self.status.setText("Enter your email and password, or your email confirmation code.")
            return
        self.password.clear()
        self.code.clear()
        self.settings.setValue("supabaseUrl", connection.url)
        self.settings.setValue("supabasePublicKey", connection.public_key)

        def operation():
            self.service = self.factory(connection)
            if mode == "signin":
                return self.service.sign_in(email, password)
            if mode == "signup":
                return self.service.sign_up(email, password)
            return self.service.verify_email(email, code)

        self.run(operation, self.authenticated)

    def authenticated(self, user):
        if user is None:
            self.status.setText("Check your email to confirm your account, then sign in.")
            return
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
        self.status.setText(
            "Connected · workspace access is enforced by the server. Chat remains a local preview."
        )

    def render_workspace(self):
        workspace = self.workspace_id()
        self.generated_code.clear()
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
            self.invite_code.clear()
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
        self.snapshot = {"workspaces": [], "channels": [], "members": [], "invitations": []}
        self.workspaces.clear()
        self.render_workspace()
        self.generated_code.clear()
        self.invite_code.clear()
        self.account_label.clear()

    def sign_out(self):
        self.clear_connected()

        def completed(_):
            self.service = None
            self.pages.setCurrentIndex(0)
            self.status.setText("Signed out. Your session has been removed from this app.")

        self.run(self.service.sign_out, completed)

    def done(self, result):
        if self.busy:
            self.status.setText("Finishing the current request…")
            return
        self.generated_code.clear()
        self.password.clear()
        self.code.clear()
        super().done(result)
