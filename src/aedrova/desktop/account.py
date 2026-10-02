"""Non-blocking account and workspace administration, separate from sample chat."""

from pathlib import Path
from threading import Event

from PySide6.QtCore import QObject, QRunnable, QSettings, QSize, Qt, QThreadPool, Signal, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from aedrova.desktop.brand import BrandMark
from aedrova.desktop.controls import ChoiceBox
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
        except Exception as error:
            from aedrova.identity.errors import retryable

            # Pass a classification only; never provider text or tokens.
            self.signals.finished.emit({"retryable": retryable(error)}, False)
        finally:
            self.operation = None


class AccountDialog(QDialog):
    dashboard_requested = Signal()
    session_closed = Signal()
    operation_failed = Signal()
    snapshot_loaded = Signal()
    operation_finished = Signal()

    def __init__(self, parent=None, *, settings=None, factory=IdentityService):
        super().__init__(parent)
        self.settings = settings if settings is not None else QSettings("Aedrova", "Desktop")
        self.factory = factory
        self.service = None
        self.busy = False
        self.pending_intent = None
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
        self._home_page()
        self.cancel_login = button("Cancel sign-in")
        self.cancel_login.hide()
        self.cancel_login.clicked.connect(self.cancel_google)
        layout.addWidget(self.cancel_login)
        close = button("Close")
        close.clicked.connect(self.accept)
        layout.addWidget(close, alignment=Qt.AlignmentFlag.AlignRight)
        for control in self.findChildren(QPushButton):
            control.setAutoDefault(False)
        self.onboarding_workspace.returnPressed.connect(self.advance_onboarding)

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
        self.google_button.setIcon(QIcon(str(Path(__file__).parent / "assets/google-g.png")))
        self.google_button.setIconSize(QSize(20, 20))
        self.google_button.setStyleSheet(
            "QPushButton { background: white; color: #1f1f1f; border: 1px solid #dadce0;"
            " border-radius: 24px; padding: 12px 24px; }"
            "QPushButton:hover { background: #f5f5f7; }"
            "QPushButton:disabled { color: #808080; }"
        )
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
        back = button("Back to workspace")
        back.clicked.connect(self.finish_setup)
        layout.addWidget(back)
        self.account_label = label("", "title", wrap=True)
        layout.addWidget(self.account_label)
        self.workspaces = ChoiceBox()
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
        create.clicked.connect(self.begin_onboarding)
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
        self.role = ChoiceBox()
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
        layout.addWidget(label("Invite teammates", "title"))
        invite = button("Create invitation")
        self.create_invitation_button = invite
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
        self.copy_invitation = button("Copy invitation code")
        self.copy_invitation.setEnabled(False)
        self.generated_code.textChanged.connect(
            lambda text: self.copy_invitation.setEnabled(bool(text))
        )
        self.copy_invitation.clicked.connect(
            lambda: QApplication.clipboard().setText(self.generated_code.text())
        )
        layout.addWidget(self.copy_invitation)
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
        choice = ChoiceBox()
        choice.setAccessibleName("Preferred building agent")
        choice.addItem("Codex", "codex")
        choice.addItem("Claude Code", "claude_code")
        return choice

    def _onboarding_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        self.onboarding_steps = QStackedWidget()
        layout.addWidget(self.onboarding_steps)

        def step(kicker, title, subtitle):
            panel = QWidget()
            column = QVBoxLayout(panel)
            column.setSpacing(20)
            column.addStretch()
            column.addWidget(label(kicker, "section"))
            column.addWidget(label(title, "heading", wrap=True))
            column.addWidget(label(subtitle, "muted", wrap=True))
            self.onboarding_steps.addWidget(panel)
            return column

        first = step("STEP 1 OF 2", "A space for your team.", "What would you like to call it?")
        self.onboarding_workspace = self.field("e.g. Northstar Labs")
        self.onboarding_workspace.setMaxLength(80)
        self.onboarding_workspace.setMinimumHeight(48)
        first.addWidget(self.onboarding_workspace)
        self.name_continue = button("Continue", role="primary")
        self.name_continue.setMinimumHeight(48)
        self.name_continue.clicked.connect(self.advance_onboarding)
        first.addWidget(self.name_continue)
        join = button("Have an invitation? Join your team")
        join.clicked.connect(lambda: self.pages.setCurrentIndex(3))
        first.addWidget(join)
        first.addStretch()

        second = step(
            "STEP 2 OF 2",
            "Meet your agent.",
            "Give your team's building partner a name. You can change it later.",
        )
        self.onboarding_nickname = self.field("Agent nickname")
        self.onboarding_nickname.setMaxLength(32)
        self.onboarding_nickname.setText("Aedrova")
        self.onboarding_nickname.setMinimumHeight(48)
        second.addWidget(self.onboarding_nickname)
        second.addWidget(label("Powered by", "muted"))
        self.onboarding_provider = self.provider_choice()
        second.addWidget(self.onboarding_provider)
        self.finish_onboarding = button("Create workspace", role="primary")
        self.finish_onboarding.setMinimumHeight(48)
        self.finish_onboarding.clicked.connect(self.complete_onboarding)
        second.addWidget(self.finish_onboarding)
        back = button("Back")
        back.clicked.connect(lambda: self.onboarding_steps.setCurrentIndex(0))
        second.addWidget(back)
        second.addStretch()

        ready = step(
            "ALL SET", "Your workspace is ready.", "A little space for your next big idea."
        )
        self.ready_summary = label("", "title", wrap=True)
        ready.addWidget(self.ready_summary)
        invite = button("Invite teammates", role="primary")
        invite.clicked.connect(self.show_simple_invite)
        ready.addWidget(invite)
        self.ready_continue = button("Go to dashboard", role="primary")
        self.ready_continue.clicked.connect(self.open_dashboard)
        ready.addWidget(self.ready_continue)
        ready.addStretch()

        invitations = step(
            "BRING YOUR TEAM",
            "Better together.",
            "Create a private invitation for a teammate's Google email.",
        )
        self.setup_email = self.field("Teammate’s Google email")
        invitations.addWidget(self.setup_email)
        self.setup_invite = button("Create invitation", role="primary")
        self.setup_invite.clicked.connect(
            lambda: self.mutate(
                "create_invitation",
                {
                    "p_workspace": self.workspace_id(),
                    "p_email": self.setup_email.text().strip(),
                    "p_role": "member",
                },
            )
        )
        invitations.addWidget(self.setup_invite)
        self.setup_code = self.field("Your invitation code")
        self.setup_code.setReadOnly(True)
        invitations.addWidget(self.setup_code)
        self.generated_code.textChanged.connect(self.setup_code.setText)
        self.setup_copy = button("Copy invitation code")
        self.setup_copy.setEnabled(False)
        self.setup_code.textChanged.connect(lambda text: self.setup_copy.setEnabled(bool(text)))
        self.setup_copy.clicked.connect(
            lambda: QApplication.clipboard().setText(self.setup_code.text())
        )
        invitations.addWidget(self.setup_copy)
        invitations.addWidget(
            label(
                "Share this code yourself. No email is sent. The invitation expires in 7 days.",
                "muted",
                wrap=True,
            )
        )
        self.invite_dashboard = button("Go to dashboard", role="primary")
        self.invite_dashboard.setMinimumHeight(48)
        self.invite_dashboard.clicked.connect(self.open_dashboard)
        invitations.addWidget(self.invite_dashboard)
        invitations.addWidget(label("You can invite more people anytime.", "muted"))
        invitations.addStretch()
        self.add_page(page)

        join_page = QWidget()
        join_layout = QVBoxLayout(join_page)
        join_layout.setSpacing(20)
        join_layout.addStretch()
        join_layout.addWidget(label("Your team is waiting.", "heading"))
        join_layout.addWidget(label("Use the code shared with your Google email.", "muted"))
        self.onboarding_invite = self.field("Paste invitation code", password=True)
        join_layout.addWidget(self.onboarding_invite)
        join_button = button("Join workspace", role="primary")
        join_button.clicked.connect(
            lambda: self.mutate(
                "accept_invitation", {"p_token": self.onboarding_invite.text().strip()}
            )
        )
        join_layout.addWidget(join_button)
        back = button("Back")
        back.clicked.connect(lambda: self.pages.setCurrentIndex(2))
        join_layout.addWidget(back)
        join_layout.addStretch()
        self.add_page(join_page)

    def _home_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)
        layout.addStretch()
        layout.addWidget(label("YOUR WORKSPACES", "section"))
        layout.addWidget(label("Welcome home.", "heading"))
        self.home_workspaces = ChoiceBox()
        self.home_workspaces.setAccessibleName("Choose your workspace")
        self.home_workspaces.currentIndexChanged.connect(self.workspaces.setCurrentIndex)
        self.workspaces.currentIndexChanged.connect(self.home_workspaces.setCurrentIndex)
        layout.addWidget(self.home_workspaces)
        self.home_dashboard = button("Go to dashboard", role="primary")
        self.home_dashboard.setMinimumHeight(48)
        self.home_dashboard.clicked.connect(self.open_dashboard)
        layout.addWidget(self.home_dashboard)
        invite = button("Invite teammates", role="primary")
        invite.clicked.connect(self.show_simple_invite)
        layout.addWidget(invite)
        settings = button("Workspace settings")
        settings.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        layout.addWidget(settings)
        create = button("Create another workspace")
        create.clicked.connect(self.begin_onboarding)
        layout.addWidget(create)
        layout.addWidget(
            label(
                "Your team is set up. Open your dashboard to start a conversation.",
                "muted",
                wrap=True,
            )
        )
        layout.addStretch()
        self.add_page(page)

    def begin_onboarding(self):
        self.pending_intent = None
        self.onboarding_workspace.clear()
        self.onboarding_nickname.setText("Aedrova")
        self.onboarding_provider.setCurrentIndex(0)
        self.onboarding_steps.setCurrentIndex(0)
        self.pages.setCurrentIndex(2)
        self.status.setText("Let's make room for your team.")
        self.onboarding_workspace.setFocus()

    def advance_onboarding(self):
        if not self.onboarding_workspace.text().strip():
            self.status.setText("Give your workspace a name to continue.")
            self.onboarding_workspace.setFocus()
            return
        self.onboarding_steps.setCurrentIndex(1)
        self.onboarding_nickname.setFocus()
        self.status.setText("One last detail. Then you're ready.")

    def show_simple_invite(self):
        if not self.workspace_id():
            self.status.setText("Refresh your workspaces before inviting teammates.")
            self.refresh()
            return
        self.pages.setCurrentIndex(2)
        self.onboarding_steps.setCurrentIndex(3)
        self.setup_email.setFocus()

    def open_dashboard(self):
        if self.busy:
            return
        if self.service and self.service.user and not self.workspace_id():
            self.status.setText("Choose or create a workspace before opening your dashboard.")
            self.refresh()
            return
        self.pending_intent = None
        self.generated_code.clear()
        self.dashboard_requested.emit()
        self.accept()

    def finish_setup(self):
        self.pending_intent = None
        self.generated_code.clear()
        if not self.workspace_id():
            self.refresh()
            return
        self.pages.setCurrentIndex(4)
        self.status.setText("You’re all set.")

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
            self.last_error_retryable = bool(result and result.get("retryable"))
            self.status.setText(
                "Request unsuccessful. Check your connection or permissions.\n"
                "Refresh before retrying a timed-out action."
            )
            if cancelled:
                self.status.setText("Sign-in cancelled. You can try again whenever you’re ready.")
            self.clear_connected()
            self.operation_failed.emit()
            if self.service is None or self.service.user is None:
                self.pages.setCurrentIndex(0)
        self.operation_finished.emit()

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
        previous = getattr(self, "pending_workspace", None) or self.workspace_id()
        self.pending_workspace = None
        self.snapshot = snapshot
        self.workspaces.blockSignals(True)
        self.workspaces.clear()
        for workspace in snapshot["workspaces"]:
            self.workspaces.addItem(workspace["name"], workspace["id"])
        index = self.workspaces.findData(previous)
        if index >= 0:
            self.workspaces.setCurrentIndex(index)
        self.workspaces.blockSignals(False)
        self.home_workspaces.blockSignals(True)
        self.home_workspaces.clear()
        for workspace in snapshot["workspaces"]:
            self.home_workspaces.addItem(workspace["name"], workspace["id"])
        self.home_workspaces.setCurrentIndex(self.workspaces.currentIndex())
        self.home_workspaces.blockSignals(False)
        self.render_workspace()
        self.pages.setCurrentIndex(4 if snapshot["workspaces"] else 2)
        if not snapshot["workspaces"]:
            self.onboarding_steps.setCurrentIndex(0)
        self.status.setText("Connected · workspace access is enforced by the server.")
        self.apply_intent()
        self.snapshot_loaded.emit()

    def apply_intent(self):
        intent, self.pending_intent = self.pending_intent, None
        if intent == "create":
            self.begin_onboarding()
        elif intent == "manage" and self.workspace_id():
            self.pages.setCurrentIndex(1)
        elif intent == "channel" and self.workspace_id():
            self.pages.setCurrentIndex(1)
            self.pages.widget(1).ensureWidgetVisible(self.channel_name)
            self.channel_name.setFocus()
        elif intent == "invite" and self.workspace_id():
            self.show_simple_invite()
            self.status.setText("Choose your connected workspace above, then invite a teammate.")

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
        for control in (
            self.agent_name,
            self.agent_provider,
            self.save_agent,
            self.setup_email,
            self.setup_invite,
            self.invite_email,
            self.create_invitation_button,
        ):
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

        previous_page = self.pages.currentIndex()
        invitation_step = (
            self.pages.currentIndex() == 2 and self.onboarding_steps.currentIndex() == 3
        )

        def operation():
            value = self.service.rpc(name, parameters)
            try:
                snapshot = self.service.snapshot()
            except Exception:
                # The write succeeded. Never present a failed refresh as a failed creation.
                snapshot = None
            return value, snapshot

        def completed(result):
            value, snapshot = result
            if snapshot is not None:
                self.loaded(snapshot)
                if name not in ("onboard_workspace", "accept_invitation"):
                    self.pages.setCurrentIndex(previous_page)
            else:
                self.clear_connected()
            if name in ("onboard_workspace", "accept_invitation"):
                index = self.workspaces.findData(value)
                if index >= 0:
                    self.workspaces.setCurrentIndex(index)
            self.invite_code.clear()
            self.onboarding_invite.clear()
            if name == "create_invitation":
                if invitation_step:
                    self.pages.setCurrentIndex(2)
                    self.onboarding_steps.setCurrentIndex(3)
                self.generated_code.setText(value)
                self.status.setText(
                    "Invitation created. Copy the code now and share it with the named teammate."
                )
            else:
                self.status.setText("Saved. Your workspace access is up to date.")
                if name == "onboard_workspace":
                    self.ready_summary.setText(parameters["p_name"])
                    self.pages.setCurrentIndex(2)
                    self.onboarding_steps.setCurrentIndex(2)
                    self.status.setText("Workspace created. Invite your team now or do it later.")

            if snapshot is None:
                self.status.setText(
                    "Saved successfully. Refresh workspace settings to load the latest details; "
                    "do not create it again."
                )

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
        self.home_workspaces.clear()
        self.render_workspace()
        self.generated_code.clear()
        self.invite_code.clear()
        self.account_label.clear()
        self.onboarding_invite.clear()
        self.setup_email.clear()

    def sign_out(self):
        self.session_closed.emit()
        self.clear_connected()
        self.onboarding_workspace.clear()
        self.onboarding_nickname.setText("Aedrova")
        self.onboarding_steps.setCurrentIndex(0)
        self.pending_intent = None

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
