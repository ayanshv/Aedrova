"""Non-blocking account and workspace administration, separate from sample chat."""

import json
from pathlib import Path
from threading import Event

from PySide6.QtCore import (
    QObject,
    QRunnable,
    QSettings,
    QSize,
    Qt,
    QThreadPool,
    Signal,
    Slot,
)
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from shiboken6 import isValid

from aedrova.desktop.brand import BrandMark
from aedrova.desktop.controls import AppDialog, ChoiceBox, CodingProviderChoice
from aedrova.desktop.dialogs import button, icon_button, label
from aedrova.desktop.welcome_surface import WelcomeSurface
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
            success = True
        except Exception as error:
            from aedrova.identity.errors import retryable

            # Pass a classification only; never provider text or tokens.
            result, success = {"retryable": retryable(error)}, False
        finally:
            self.operation = None
        # The window/application may close while this background request runs.
        # A destroyed Qt receiver must not turn shutdown into a second failure.
        if isValid(self.signals):
            try:
                self.signals.finished.emit(result, success)
            except RuntimeError:
                if isValid(self.signals):
                    raise


class AccountDialog(AppDialog):
    dashboard_requested = Signal()
    session_closed = Signal()
    operation_failed = Signal()
    snapshot_loaded = Signal()
    sign_in_ready = Signal()
    operation_finished = Signal()

    def __init__(self, parent=None, *, settings=None, factory=IdentityService):
        super().__init__(parent)
        self.settings = settings if settings is not None else QSettings("Aedrova", "Desktop")
        self.factory = factory
        self.service = None
        self.busy = False
        self.pending_intent = None
        self.creation_workspace = None
        self.oauth_cancel = None
        self.awaiting_sign_in_snapshot = False
        QApplication.instance().aboutToQuit.connect(self.cancel_google)
        self.snapshot = {
            "workspaces": [],
            "channels": [],
            "members": [],
            "invitations": [],
            "agent_preferences": [],
        }
        self.setObjectName("AccountDialog")
        self.setWindowTitle("Aedrova · Account & workspaces")
        self.resize(720, 780)
        self.setMinimumSize(600, 540)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        top = QHBoxLayout()
        top.addWidget(BrandMark(36))
        top.addWidget(label("Aedrova", "title"))
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
        close = self.workspace_icon("close", "Close")
        close.clicked.connect(self.accept)
        layout.addWidget(close, alignment=Qt.AlignmentFlag.AlignRight)
        for control in self.findChildren(QPushButton):
            control.setAutoDefault(False)
        self.onboarding_workspace.returnPressed.connect(self.advance_onboarding)

    def add_page(self, page):
        page.setObjectName("AccountPage")
        scroll = QScrollArea()
        scroll.setFrameShape(QFrame.Shape.NoFrame)
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
        page = WelcomeSurface()
        outer = QVBoxLayout(page)
        outer.addStretch()
        row = QHBoxLayout()
        row.addStretch()
        card = QWidget()
        card.setObjectName("AccountLoginCard")
        card.setFixedWidth(340)
        column = QVBoxLayout(card)
        column.setContentsMargins(24, 28, 24, 28)
        column.setSpacing(16)
        column.addWidget(BrandMark(40), alignment=Qt.AlignmentFlag.AlignHCenter)
        heading = label("Get started with Aedrova", "title")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        column.addWidget(heading)
        subtitle = label("Your team’s context. Put to work.", "muted", wrap=True)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        column.addWidget(subtitle)
        self.google_button = button("Continue with Google", role="primary")
        self.google_button.setIcon(QIcon(str(Path(__file__).parent / "assets/google-g.png")))
        self.google_button.setIconSize(QSize(18, 18))
        self.google_button.setMinimumHeight(40)
        self.google_button.clicked.connect(self.start_google)
        column.addWidget(self.google_button)
        note = label(
            "Sign in securely in your browser.\nWe’ll bring you straight back to setup.",
            "muted",
            wrap=True,
        )
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        column.addWidget(note)
        row.addWidget(card)
        row.addStretch()
        outer.addLayout(row)
        outer.addStretch()
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
        self.status.show()
        self.status.setText(
            "Continue with Google in your browser. We’ll bring your workspace here."
        )

    def cancel_google(self):
        if self.oauth_cancel is not None:
            self.oauth_cancel.set()
            self.status.setText("Cancelling sign-in…")

    def _workspace_page(self):
        from aedrova.desktop.workspace_settings import WorkspaceSettingsView

        self.workspace_settings = WorkspaceSettingsView()
        page = self.workspace_settings
        self.workspaces = ChoiceBox()
        self.workspaces.setAccessibleName("Your connected workspaces")
        self.workspaces.currentIndexChanged.connect(self.render_workspace)
        page.workspace_slot.addWidget(self.workspaces)
        self.account_label = label("", "muted", wrap=True)
        # Account identity belongs in its own section, rather than above every form.
        agent = page.add_section(
            "agent", "Your agent", "Choose how Aedrova builds with your team.", "work"
        )
        agent.addSpacing(8)
        agent.addWidget(label("Agent name", "muted"))
        self.agent_name = self.field("Agent nickname")
        self.agent_name.setMaxLength(32)
        agent.addWidget(self.agent_name)
        agent.addWidget(label("Powered by", "muted"))
        self.agent_provider = self.provider_choice()
        agent.addWidget(self.agent_provider)
        self.save_agent = button("Save agent", role="primary")
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
        agent.addWidget(self.save_agent)
        agent.addStretch(1)

        channels = page.add_section(
            "channels", "Channels", "Give each conversation a place.", "context"
        )
        self.channels = QListWidget()
        self.channels.setProperty("accountList", True)
        self.channels.setAccessibleName("Authorized channels")
        self.channels.setMinimumHeight(110)
        channels.addWidget(self.channels, 1)
        self.channel_name = self.field("New channel name")
        self.channel_name.setMaxLength(80)
        channels.addWidget(self.channel_name)
        self.private = QCheckBox("Private · invited members only")
        channels.addWidget(self.private)
        create_channel = button("Create channel", role="primary")
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
        channels.addWidget(create_channel)

        people = page.add_section(
            "people", "People & access", "Select a teammate to manage their access.", "smile"
        )
        self.members = QListWidget()
        self.members.setProperty("accountList", True)
        self.members.setAccessibleName("Workspace members")
        self.members.setMinimumHeight(140)
        people.addWidget(self.members, 1)
        self.role = ChoiceBox()
        self.role.addItems(["member", "guest", "admin"])
        self.role.setAccessibleName("Member or invitation role")
        people.addWidget(self.role)
        change = button("Update role", role="primary")
        self.update_member_role_button = change
        change.setEnabled(False)
        self.members.currentItemChanged.connect(
            lambda current, _previous: change.setEnabled(bool(current) and self.can_manage_roles)
        )
        change.clicked.connect(lambda: self.member_action("role"))
        people.addWidget(change)
        from PySide6.QtWidgets import QGroupBox

        advanced = QGroupBox("More access controls")
        advanced.setCheckable(True)
        advanced.setChecked(False)
        tools = QWidget()
        row = QGridLayout(tools)
        self.access_channel = ChoiceBox()
        self.access_channel.setAccessibleName("Channel access to manage")
        row.addWidget(self.access_channel, 0, 0)
        for index, (title, operation) in enumerate(
            [("Remove member", "remove"), ("Grant channel", "grant"), ("Revoke channel", "revoke")]
        ):
            control = button(title, role="outline")
            control.clicked.connect(lambda checked=False, op=operation: self.member_action(op))
            row.addWidget(control, index + 1, 0)
        advanced_layout = QVBoxLayout(advanced)
        advanced_layout.addWidget(tools)
        tools.setVisible(False)
        advanced.toggled.connect(tools.setVisible)
        people.addWidget(advanced)

        invites = page.add_section(
            "invitations", "Invitations", "Bring a teammate into this workspace.", "mention"
        )
        self.invite_email = self.field("Teammate email")
        invites.addWidget(self.invite_email)
        self.invite_role = ChoiceBox()
        for title, role in (("Teammate", "member"), ("Guest", "guest"), ("Administrator", "admin")):
            self.invite_role.addItem(title, role)
        self.invite_role.setAccessibleName("Invitation role")
        invites.addWidget(self.invite_role)
        self.create_invitation_button = button("Create invitation", role="primary")
        self.create_invitation_button.clicked.connect(
            lambda: self.mutate(
                "create_invitation",
                {
                    "p_workspace": self.workspace_id(),
                    "p_email": self.invite_email.text().strip(),
                    "p_role": self.invite_role.currentData(),
                },
            )
        )
        invites.addWidget(self.create_invitation_button)
        self.generated_code = self.field("Invitation code appears here once")
        self.generated_code.setReadOnly(True)
        self.generated_code.hide()
        invites.addWidget(self.generated_code)
        self.copy_invitation = button("Copy invitation code", role="outline")
        self.copy_invitation.setEnabled(False)
        self.copy_invitation.hide()
        self.generated_code.textChanged.connect(
            lambda text: self.generated_code.setVisible(bool(text))
        )
        self.generated_code.textChanged.connect(
            lambda text: self.copy_invitation.setVisible(bool(text))
        )
        self.generated_code.textChanged.connect(
            lambda text: self.copy_invitation.setEnabled(bool(text))
        )
        self.copy_invitation.clicked.connect(
            lambda: QApplication.clipboard().setText(self.generated_code.text())
        )
        invites.addWidget(self.copy_invitation)
        self.invitation_note = label(
            "Share the single-use code. Expires in seven days; no email is sent.",
            "muted",
            wrap=True,
        )
        self.invitation_note.hide()
        self.generated_code.textChanged.connect(
            lambda text: self.invitation_note.setVisible(bool(text))
        )
        invites.addWidget(self.invitation_note)
        self.invitations = QListWidget()
        self.invitations.setProperty("accountList", True)
        self.invitations.setAccessibleName("Pending invitations")
        self.invitations.setMinimumHeight(100)
        invites.addWidget(self.invitations, 1)
        revoke = button("Revoke selected invitation", role="outline")
        self.revoke_invitation_button = revoke
        revoke.clicked.connect(self.revoke_invitation)
        invites.addWidget(revoke)

        account = page.add_section(
            "account", "Account", "Manage your session and workspaces.", "spaces"
        )
        account.addWidget(self.account_label)
        actions = QHBoxLayout()
        create = icon_button("plus", "Create a workspace")
        create.clicked.connect(self.begin_onboarding)
        actions.addWidget(create)
        refresh = icon_button("refresh", "Refresh workspace")
        refresh.clicked.connect(self.refresh)
        actions.addWidget(refresh)
        actions.addStretch()
        signout = icon_button("logout", "Sign out")
        signout.clicked.connect(self.sign_out)
        actions.addWidget(signout)
        back = icon_button("enter", "Back to workspace", primary=True)
        back.clicked.connect(self.finish_setup)
        actions.addWidget(back)
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(8)
        account.addSpacing(8)
        account.addWidget(label("Join a workspace", "title"))
        join_row = QHBoxLayout()
        join_row.setSpacing(12)
        self.invite_code = self.field("Invitation code", password=True)
        join_row.addWidget(self.invite_code, 1)
        join = icon_button("enter", "Join workspace")
        join.clicked.connect(
            lambda: self.mutate("accept_invitation", {"p_token": self.invite_code.text().strip()})
        )
        join_row.addWidget(join)
        account.addLayout(join_row)
        account.addSpacing(8)
        account.addLayout(actions)
        account.addStretch(1)
        self.add_page(page)

    def provider_choice(self):
        choice = CodingProviderChoice()
        choice.setAccessibleName("Preferred building agent")
        return choice

    def _onboarding_page(self):
        page = WelcomeSurface()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        self.onboarding_steps = QStackedWidget()
        self.onboarding_steps.setMaximumWidth(440)
        layout.addWidget(self.onboarding_steps, alignment=Qt.AlignmentFlag.AlignHCenter)

        def step(kicker, title, subtitle):
            panel = QWidget()
            column = QVBoxLayout(panel)
            column.setSpacing(14)
            column.addStretch()
            column.addWidget(label(kicker, "section"))
            heading = label(title, "title", wrap=True)
            heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
            column.addWidget(heading)
            column.addWidget(label(subtitle, "muted", wrap=True))
            self.onboarding_steps.addWidget(panel)
            return column

        first = step("STEP 1 OF 3", "A space for your team.", "What would you like to call it?")
        self.onboarding_workspace = self.field("e.g. Northstar Labs")
        self.onboarding_workspace.setMaxLength(80)
        self.onboarding_workspace.setMinimumHeight(48)
        first.addWidget(self.onboarding_workspace)
        self.space_parent = ChoiceBox()
        self.space_parent.setAccessibleName("Independent Space or shared subspace")
        self.space_parent.addItem("Independent Space · separate plan and AI", None)
        first.addWidget(self.space_parent)
        first.addWidget(
            label(
                "One subscription covers your team. A subspace shares its parent’s plan "
                "and AI capacity. Creating either never charges your card.",
                "muted",
                wrap=True,
            )
        )
        self.name_continue = button("Continue", role="primary")
        self.name_continue.setMinimumHeight(48)
        self.name_continue.clicked.connect(self.advance_onboarding)
        first.addWidget(self.name_continue)
        join = button("Have an invitation? Join your team")
        join.clicked.connect(lambda: self.pages.setCurrentIndex(3))
        first.addWidget(join)
        first.addStretch()

        second = step(
            "STEP 2 OF 3",
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
        self.provider_continue = button("Continue", role="primary")
        self.provider_continue.setMinimumHeight(48)
        self.provider_continue.clicked.connect(self.review_ai_setup)
        second.addWidget(self.provider_continue)
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

        # Keep existing ready/invitation indices stable; creation visits this
        # required review before either independent Space or subspace is written.
        self.ai_review_step = self.onboarding_steps.count()
        review = step(
            "STEP 3 OF 3",
            "How should your agent work?",
            "Choose how builds run on this computer. You can change it later.",
        )
        # Let the surrounding scroll area scroll on short screens instead of
        # squeezing wrapped disclosures and actions into overlapping rows.
        review.parentWidget().setMinimumHeight(560)
        review.addWidget(label("Model", "section"))
        self.onboarding_model = label("", "muted", wrap=True)
        review.addWidget(self.onboarding_model)
        review.addWidget(label("Build workflow · this computer", "section"))
        self.onboarding_workflow = ChoiceBox()
        self.onboarding_workflow.setAccessibleName("AI build workflow")
        self.onboarding_workflow.addItem("Plan and execute in the background", True)
        self.onboarding_workflow.addItem("Review the plan before building", False)
        review.addWidget(self.onboarding_workflow)
        self.onboarding_permission = label("", "muted", wrap=True)
        self.onboarding_permission.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Minimum
        )
        review.addWidget(self.onboarding_permission)
        review.addWidget(
            label(
                "Applying to original files and publishing still need approval. "
                "Connect a project before building.",
                "muted",
                wrap=True,
            )
        )
        self.onboarding_ack = QCheckBox("I’ve reviewed and allow this AI setup")
        review.addWidget(self.onboarding_ack)
        self.finish_onboarding = button("Create workspace", role="primary")
        self.finish_onboarding.setMinimumHeight(48)
        self.finish_onboarding.setEnabled(False)
        self.finish_onboarding.clicked.connect(self.complete_onboarding)
        review.addWidget(self.finish_onboarding)
        back_ai = button("Back", role="outline")
        back_ai.clicked.connect(lambda: self.onboarding_steps.setCurrentIndex(1))
        review.addWidget(back_ai)
        review.addStretch()
        self.onboarding_ack.toggled.connect(self.finish_onboarding.setEnabled)
        self.onboarding_workflow.currentIndexChanged.connect(self.update_ai_review)
        self.onboarding_provider.currentIndexChanged.connect(self.update_ai_review)
        self.update_ai_review()
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

    def workspace_icon(self, name, title, *, primary=False):
        return icon_button(name, title, primary=primary)

    def _home_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        content = QWidget()
        content.setMinimumWidth(0)
        content.setMaximumWidth(720)
        content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        body = QVBoxLayout(content)
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(20)
        heading = QHBoxLayout()
        heading.addWidget(label("Your workspaces", "heading"))
        heading.addStretch()
        create = self.workspace_icon("plus", "Create a workspace")
        create.clicked.connect(self.begin_onboarding)
        heading.addWidget(create)
        body.addLayout(heading)

        row = QHBoxLayout()
        row.setSpacing(12)
        self.home_workspaces = ChoiceBox()
        self.home_workspaces.setAccessibleName("Choose your workspace")
        self.home_workspaces.setFixedHeight(44)
        self.home_workspaces.currentIndexChanged.connect(self.workspaces.setCurrentIndex)
        self.workspaces.currentIndexChanged.connect(self.home_workspaces.setCurrentIndex)
        row.addWidget(self.home_workspaces, 1)
        self.home_dashboard = self.workspace_icon("enter", "Open workspace", primary=True)
        self.home_dashboard.clicked.connect(self.open_dashboard)
        row.addWidget(self.home_dashboard)
        body.addLayout(row)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        self.home_invite = self.workspace_icon("invite", "Invite teammates")
        self.home_invite.clicked.connect(self.show_simple_invite)
        actions.addWidget(self.home_invite)
        self.home_settings = self.workspace_icon("settings", "Workspace settings")
        self.home_settings.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        actions.addWidget(self.home_settings)
        actions.addStretch()
        self.archive_workspace = self.workspace_icon("archive", "Archive workspace for me")
        self.archive_workspace.clicked.connect(self.confirm_archive)
        actions.addWidget(self.archive_workspace)
        body.addLayout(actions)

        self.archived_section = QWidget()
        archived_layout = QVBoxLayout(self.archived_section)
        archived_layout.setContentsMargins(0, 24, 0, 0)
        archived_layout.setSpacing(10)
        archived_layout.addWidget(label("Archived", "muted"))
        archived_row = QHBoxLayout()
        archived_row.setSpacing(12)
        self.archived_workspaces = ChoiceBox()
        self.archived_workspaces.setAccessibleName("Your archived workspaces")
        self.archived_workspaces.setFixedHeight(44)
        archived_row.addWidget(self.archived_workspaces, 1)
        self.restore_workspace = self.workspace_icon("restore", "Restore workspace")
        self.restore_workspace.clicked.connect(self.restore_archived)
        archived_row.addWidget(self.restore_workspace)
        archived_layout.addLayout(archived_row)
        self.archived_section.hide()
        body.addWidget(self.archived_section)
        centered = QHBoxLayout()
        centered.setContentsMargins(0, 0, 0, 0)
        centered.addStretch()
        centered.addWidget(content, 1)
        centered.addStretch()
        layout.addStretch(1)
        layout.addLayout(centered)
        layout.addStretch(2)
        self.add_page(page)

    def confirm_archive(self):
        workspace = self.workspace_id()
        if self.busy or not workspace:
            return
        if self.archive_blocked():
            return
        self.archive_confirmation = AppDialog(self)
        self.archive_confirmation.setWindowTitle("Aedrova · Archive for me")
        self.archive_confirmation.setMinimumWidth(420)
        layout = QVBoxLayout(self.archive_confirmation)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        layout.addWidget(label("Archive this workspace for you?", "title", wrap=True))
        layout.addWidget(label(self.workspaces.currentText(), "muted", wrap=True))
        layout.addWidget(
            label(
                "It will leave your dashboard. Teammates keep access and no messages or files are "
                "deleted. Finish active builds and leave calls before archiving. "
                "Archiving does not cancel a subscription. "
                "You can restore it in Account & workspaces.",
                "muted",
                wrap=True,
            )
        )
        row = QHBoxLayout()
        cancel = button("Cancel")
        cancel.clicked.connect(self.archive_confirmation.reject)
        archive = button("Archive for me", role="primary")

        def confirmed():
            if self.archive_blocked():
                self.archive_confirmation.reject()
                return
            self.archive_confirmation.accept()
            self.mutate(
                "set_workspace_archived",
                {
                    "p_workspace": workspace,
                    "p_archived": True,
                },
            )

        archive.clicked.connect(confirmed)
        row.addWidget(cancel)
        row.addWidget(archive)
        layout.addLayout(row)
        for control in (cancel, archive):
            control.setAutoDefault(False)
        self.archive_confirmation.open()

    def archive_blocked(self):
        window = self.parent()
        build = getattr(window, "build_dialog", None)
        call = getattr(window, "meeting_call", None)
        if (build and build.pending) or (call and not call.closed):
            self.status.setText(
                "Finish active builds and leave calls before archiving a workspace."
            )
            return True
        return False

    def restore_archived(self):
        workspace = self.archived_workspaces.currentData()
        if not workspace or self.busy:
            return
        self.mutate("set_workspace_archived", {"p_workspace": workspace, "p_archived": False})

    def begin_onboarding(self):
        self.pending_intent = None
        self.creation_workspace = None
        self.onboarding_workspace.clear()
        self.onboarding_nickname.setText("Aedrova")
        self.onboarding_provider.setCurrentIndex(self.onboarding_provider.findData("auto"))
        self.onboarding_workflow.setCurrentIndex(0)
        self.onboarding_ack.setChecked(False)
        self.finish_onboarding.setText("Create workspace")
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
        self.status.setText("Choose your team’s AI provider.")

    def update_ai_review(self, *_):
        from aedrova.agents.managed import ai_access_mode

        self.onboarding_ack.setChecked(False)
        provider = self.onboarding_provider.currentText()
        self.onboarding_model.setText(
            provider + " · Aedrova’s approved model and your plan’s usage limits."
            if ai_access_mode() == "included"
            else provider
            + " · your provider’s default model, using your existing provider sign-in."
        )
        self.onboarding_permission.setText(
            "Explicit build requests can share accessible workspace context with this provider "
            "and run plans, isolated edits and sandboxed tests. Usage may be billed."
            if self.onboarding_workflow.currentData()
            else "Build requests open a plan for your review. Context is shared only when you "
            "authorize the workflow. Automatic execution stays off."
        )

        self.onboarding_permission.setMinimumHeight(self.onboarding_permission.sizeHint().height())

    def review_ai_setup(self):
        if not self.onboarding_nickname.text().strip():
            self.status.setText("Give your agent a name first.")
            return
        self.update_ai_review()
        self.onboarding_steps.setCurrentIndex(self.ai_review_step)
        self.status.setText("Review your AI setup before creating the workspace.")

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
        if self.service and self.service.user:
            from aedrova.desktop.projects import binding_key

            try:
                data = json.loads(
                    self.settings.value(
                        binding_key(str(self.service.user.id), self.workspace_id()), "{}"
                    )
                )
            except (ValueError, TypeError):
                data = {}
            if not isinstance(data, dict):
                data = {}
            if data.get("ai_setup_pending"):
                self.creation_workspace = self.workspace_id()
                self.onboarding_nickname.setText(data.get("agent_nickname", "Aedrova"))
                self.onboarding_provider.setCurrentIndex(
                    self.onboarding_provider.findData(data.get("provider", "auto"))
                )
                self.onboarding_workflow.setCurrentIndex(
                    self.onboarding_workflow.findData(bool(data.get("background_build")))
                )
                self.pages.setCurrentIndex(2)
                self.review_ai_setup()
                self.finish_onboarding.setText("Finish AI setup")
                self.status.setText("This workspace exists. Finish its AI setup to continue.")
                return
        self.pending_intent = None
        self.generated_code.clear()
        self.accept()
        self.dashboard_requested.emit()

    def finish_setup(self):
        self.pending_intent = None
        self.generated_code.clear()
        if not self.workspace_id():
            self.refresh()
            return
        self.pages.setCurrentIndex(4)
        self.status.setText("You’re all set.")

    def complete_onboarding(self):
        if self.busy:
            return
        if not self.onboarding_ack.isChecked():
            self.review_ai_setup()
            self.status.setText("Review and allow your AI setup before creating the workspace.")
            return
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
        from aedrova.agents.managed import ai_access_mode

        configuration = {
            "provider": self.onboarding_provider.currentData(),
            "model_policy": "managed" if ai_access_mode() == "included" else "provider_default",
            "background_build": bool(self.onboarding_workflow.currentData()),
            "auto_plan": bool(self.onboarding_workflow.currentData()),
            "ai_setup_version": 1,
            "agent_nickname": nickname,
        }
        if self.creation_workspace:
            self.mutate(
                "set_agent_preferences",
                {
                    "p_workspace": self.creation_workspace,
                    "p_nickname": nickname,
                    "p_provider": configuration["provider"],
                },
                configuration=configuration,
                created_workspace=self.creation_workspace,
            )
            return
        if self.space_parent.currentData():
            self.mutate(
                "create_subspace",
                {"p_parent": self.space_parent.currentData(), "p_name": name},
                configuration=configuration,
            )
            return
        self.mutate(
            "onboard_workspace",
            {
                "p_name": name,
                "p_nickname": nickname,
                "p_provider": self.onboarding_provider.currentData(),
            },
            configuration=configuration,
        )

    def workspace_id(self):
        return self.workspaces.currentData()

    def run(self, operation, success, *, background=False):
        if self.busy:
            return
        self.busy = True
        self.background_job = background
        if not background:
            self.pages.setEnabled(False)
            self.set_loading(self.pages, True)
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
        self.set_loading(self.pages, False)
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
        self.awaiting_sign_in_snapshot = True
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
        self.space_parent.clear()
        self.space_parent.addItem("Independent Space · separate plan and AI", None)
        if snapshot.get("space_hierarchy_available"):
            for space in snapshot["workspaces"]:
                if space.get("can_manage_billing"):
                    self.space_parent.addItem(
                        "Subspace of " + space["name"] + " · shared plan", space["id"]
                    )
        self.workspaces.blockSignals(True)
        self.workspaces.clear()
        for workspace in snapshot["workspaces"]:
            self.workspaces.addItem(
                ("↳ " if workspace.get("parent_id") else "") + workspace["name"], workspace["id"]
            )
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
        self.archived_workspaces.clear()
        for workspace in snapshot.get("archived_workspaces", []):
            self.archived_workspaces.addItem(workspace["name"], workspace["id"])
        self.archived_section.setVisible(self.archived_workspaces.count() > 0)
        self.restore_workspace.setEnabled(self.archived_workspaces.count() > 0)
        self.archive_workspace.setEnabled(bool(snapshot["workspaces"]))
        self.home_dashboard.setEnabled(bool(snapshot["workspaces"]))
        self.home_invite.setEnabled(bool(snapshot["workspaces"]))
        self.home_settings.setEnabled(bool(snapshot["workspaces"]))
        self.render_workspace()
        self.pages.setCurrentIndex(
            4 if snapshot["workspaces"] or snapshot.get("archived_workspaces") else 2
        )
        if not snapshot["workspaces"]:
            self.onboarding_steps.setCurrentIndex(0)
        self.status.setText("Connected")
        self.apply_intent()
        self.snapshot_loaded.emit()
        if self.awaiting_sign_in_snapshot and self.service and self.service.user:
            self.awaiting_sign_in_snapshot = False
            self.sign_in_ready.emit()
        # Profile customization remains in Account → Edit profile; the intro is a
        # permission-free product playground, with no competing setup dialogs.

    def apply_intent(self):
        intent, self.pending_intent = self.pending_intent, None
        if intent == "create":
            self.begin_onboarding()
        elif intent == "manage" and self.workspace_id():
            self.pages.setCurrentIndex(1)
            self.workspace_settings.show_section("agent")
            self.resize(840, 690)
        elif intent == "channel" and self.workspace_id():
            self.pages.setCurrentIndex(1)
            self.workspace_settings.show_section("channels")
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
        provider_index = self.agent_provider.findData(preference.get("provider", "auto"))
        self.agent_provider.setCurrentIndex(
            provider_index if provider_index >= 0 else self.agent_provider.findData("auto")
        )
        user_id = str(self.service.user.id) if self.service and self.service.user else None
        can_edit = any(
            m["workspace_id"] == workspace
            and m["user_id"] == user_id
            and m["role"] in ("owner", "admin")
            for m in self.snapshot["members"]
        )
        self.can_manage_roles = any(
            m["workspace_id"] == workspace and m["user_id"] == user_id and m["role"] == "owner"
            for m in self.snapshot["members"]
        )
        self.role.setEnabled(self.can_manage_roles)
        self.update_member_role_button.setEnabled(False)
        selected_access = self.access_channel.currentData()
        self.access_channel.clear()
        self.access_channel.addItem("Choose a channel…", None)
        for channel in self.snapshot["channels"]:
            if channel["workspace_id"] == workspace:
                self.access_channel.addItem(channel["name"], channel["id"])
        if selected_access:
            self.access_channel.setCurrentIndex(
                max(0, self.access_channel.findData(selected_access))
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
        self.invitations.setVisible(self.invitations.count() > 0)
        self.revoke_invitation_button.setVisible(self.invitations.count() > 0)

    def mutate(self, name, parameters, *, configuration=None, created_workspace=None):
        if self.busy:
            if getattr(self, "queued_settings_save", False):
                return
            self.queued_settings_save = True
            service = self.service
            user = str(service.user.id) if service and service.user else None
            self.status.setText("Saving after the current update. Your changes are kept.")

            def after_update():
                self.operation_finished.disconnect(after_update)
                self.queued_settings_save = False
                if (
                    self.service is service
                    and service
                    and service.user
                    and str(service.user.id) == user
                    and parameters.get("p_workspace", self.workspace_id()) == self.workspace_id()
                    and self.snapshot.get("workspaces")
                    and not getattr(self, "logout_pending", False)
                ):
                    self.mutate(
                        name,
                        parameters,
                        configuration=configuration,
                        created_workspace=created_workspace,
                    )
                else:
                    self.status.setText(
                        "Your session or workspace changed. Review it before saving."
                    )

            self.operation_finished.connect(after_update)
            return
        if any(value is None for value in parameters.values()):
            self.status.setText("Choose a workspace first.")
            return

        previous_page = self.pages.currentIndex()
        invitation_step = (
            self.pages.currentIndex() == 2 and self.onboarding_steps.currentIndex() == 3
        )
        creator = str(self.service.user.id) if configuration else None

        def operation():
            value = self.service.rpc(name, parameters)
            if name == "create_subspace" and configuration:
                try:
                    self.service.rpc(
                        "set_agent_preferences",
                        {
                            "p_workspace": value,
                            "p_nickname": configuration["agent_nickname"],
                            "p_provider": configuration["provider"],
                        },
                    )
                except Exception:
                    # Creation already succeeded. Retain its ID and retry setup,
                    # never issue another create after a preference failure.
                    configuration["ai_setup_pending"] = True
            try:
                snapshot = self.service.snapshot()
            except Exception:
                # The write succeeded. Never present a failed refresh as a failed creation.
                snapshot = None
            return value, snapshot

        def completed(result):
            value, snapshot = result
            if configuration:
                from aedrova.desktop.projects import binding_key

                value = created_workspace or value
                self.creation_workspace = value
                key = binding_key(creator, value)
                try:
                    stored = json.loads(self.settings.value(key, "{}"))
                    if not isinstance(stored, dict):
                        stored = {}
                except (ValueError, TypeError):
                    stored = {}
                stored.update(configuration)
                stored["ai_setup_pending"] = bool(configuration.get("ai_setup_pending"))
                if stored["ai_setup_pending"]:
                    stored["background_build"] = False
                    stored["auto_plan"] = False
                self.settings.setValue(key, json.dumps(stored))
                self.settings.sync()
                local_error = self.settings.status() != QSettings.Status.NoError
            else:
                local_error = False
            if snapshot is not None:
                self.loaded(snapshot)
                if name not in ("onboard_workspace", "accept_invitation") and not configuration:
                    self.pages.setCurrentIndex(previous_page)
            else:
                self.clear_connected()
            if (
                configuration
                or name in ("onboard_workspace", "accept_invitation")
                or (name == "set_workspace_archived" and parameters["p_archived"] is False)
            ):
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
                if name == "onboard_workspace" or configuration:
                    self.ready_summary.setText(
                        parameters.get("p_name", self.onboarding_workspace.text().strip())
                    )
                    self.pages.setCurrentIndex(2)
                    self.onboarding_steps.setCurrentIndex(2)
                    self.status.setText("Workspace created. Invite your team now or do it later.")
                elif name == "set_workspace_archived":
                    self.pages.setCurrentIndex(4)
                    self.status.setText(
                        "Archived for you. Restore it here anytime."
                        if parameters["p_archived"]
                        else "Workspace restored to your dashboard."
                    )

            if snapshot is None:
                if configuration:
                    self.pending_workspace = value
                self.status.setText(
                    "Saved successfully. Refresh workspace settings to load the latest details; "
                    "do not create it again."
                )
            if configuration and (configuration.get("ai_setup_pending") or local_error):
                self.pages.setCurrentIndex(2)
                self.onboarding_steps.setCurrentIndex(self.ai_review_step)
                self.finish_onboarding.setText("Retry AI setup")
                self.status.setText(
                    "Your workspace was created. AI setup hasn’t finished. Retry setup here; "
                    "this will not create another workspace."
                )

        self.run(operation, completed)

    def member_action(self, action):
        member = self.members.currentItem()
        channel = self.channels.currentItem()
        channel_id = self.access_channel.currentData() or (
            channel.data(Qt.ItemDataRole.UserRole) if channel else None
        )
        if not member or (action in ("grant", "revoke") and not channel_id):
            self.status.setText("Select a member and, when changing channel access, a channel.")
            return
        user = member.data(Qt.ItemDataRole.UserRole)
        if action in ("grant", "revoke"):
            self.mutate(
                "set_channel_member",
                {
                    "p_channel": channel_id,
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
        self.archived_workspaces.clear()
        self.archived_section.hide()
        self.archive_workspace.setEnabled(False)
        self.restore_workspace.setEnabled(False)
        self.home_dashboard.setEnabled(False)
        self.home_invite.setEnabled(False)
        self.home_settings.setEnabled(False)
        self.render_workspace()
        self.generated_code.clear()
        self.invite_code.clear()
        self.account_label.clear()
        self.onboarding_invite.clear()
        self.setup_email.clear()

    def sign_out(self):
        if self.busy:
            if not getattr(self, "logout_pending", False):
                self.logout_pending = True
                self.operation_finished.connect(self.finish_pending_logout)
            return
        service = self.service
        self.service = None
        self.awaiting_sign_in_snapshot = False
        self.session_closed.emit()
        self.clear_connected()
        self.onboarding_workspace.clear()
        self.onboarding_nickname.setText("Aedrova")
        self.onboarding_steps.setCurrentIndex(0)
        self.pending_intent = None

        def completed(_):
            self.pages.setCurrentIndex(0)
            self.status.setText("Signed out. Your session has been removed from this app.")
            if self.parent():
                self.parent().update_profile_button()

        def revoke():
            if service is None:
                return
            try:
                service.sign_out()
            except Exception:
                # Local credentials are discarded even if Auth is unreachable.
                # Remote sessions retain their normal expiry; do not claim revocation.
                return

        self.run(revoke, completed)

    def finish_pending_logout(self):
        self.operation_finished.disconnect(self.finish_pending_logout)
        self.logout_pending = False
        self.sign_out()

    def done(self, result):
        if self.busy:
            self.cancel_google()
            self.status.setText("Finishing the current request…")
            return
        self.generated_code.clear()
        super().done(result)
