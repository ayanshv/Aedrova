"""Account and project forms for the desktop first-run flow."""

from pathlib import Path

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout

from aedrova.desktop.brand import ASSETS
from aedrova.desktop.controls import CodingProviderChoice, choose_project
from aedrova.desktop.dialogs import apple_sign_in_button, button, label
from aedrova.desktop.getting_started import GOALS
from aedrova.desktop.icons import assign, icon
from aedrova.desktop.projects import binding, save_binding
from aedrova.identity.oauth import apple_login_enabled

WELCOME, ACCOUNT, PRIVACY, GOAL, PROJECT = range(5)


class SetupPages(QFrame):
    def __init__(self, flow):
        super().__init__(flow)
        self.flow = flow
        self.window = flow.window
        self.workspace = None
        self.draft = {}
        self.page = None
        self.login_dialog = None
        self.workspace_dialog = None
        self.profile_form = None
        self.first_action = None
        self.select_workspace()
        self.body = self
        self.column = QVBoxLayout(self)
        self.column.setContentsMargins(0, 0, 0, 0)
        self.column.setSpacing(10)

    def select_workspace(self):
        account = getattr(self.window, "account_dialog", None)
        if not account or not self.window.current_user():
            return
        allowed = {item["id"] for item in account.snapshot.get("workspaces", [])}
        selected = account.workspace_id()
        workspace = selected if selected in allowed else self.window.workspace_id
        if workspace not in allowed:
            self.workspace = None
            self.draft = {}
            return
        if workspace != self.workspace:
            self.workspace = workspace
            self.draft = dict(binding(self.window, workspace))

    def has_workspace(self):
        account = getattr(self.window, "account_dialog", None)
        return bool(
            account
            and self.workspace
            and any(item["id"] == self.workspace for item in account.snapshot.get("workspaces", []))
        )

    def note(self, text):
        self.column.addWidget(label(text, "muted", wrap=True))

    def render(self, stage):
        while self.column.count():
            item = self.column.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()
        self.profile_form = None
        self.first_action = None
        self.page = stage
        self.status = label("", "error", wrap=True)
        self.status.hide()
        if stage == ACCOUNT:
            self.render_account()
        elif stage == PRIVACY:
            self.render_privacy()
        elif stage == GOAL:
            self.render_goal()
        else:
            self.render_project()
        self.column.addWidget(self.status)
        self.updateGeometry()

    def render_account(self):
        self.column.addWidget(label("Your account", "title"))
        if self.window.current_user():
            from aedrova.desktop.profile import ProfileDialog

            self.profile_form = ProfileDialog(
                self.window,
                self.window.account_dialog,
                onboarding=True,
                continued=self.profile_saved,
                embedded=True,
            )
            self.profile_form.setParent(self.body, Qt.WindowType.Widget)
            self.profile_form.setMinimumSize(0, 0)
            self.profile_form.layout().setContentsMargins(0, 0, 0, 0)
            self.profile_form.steps[0].layout().itemAt(0).widget().hide()
            for index in range(self.profile_form.controls.count()):
                widget = self.profile_form.controls.itemAt(index).widget()
                if widget:
                    widget.hide()
            self.profile_form.state_changed.connect(self.sync_profile_controls)
            self.column.addWidget(self.profile_form)
            self.sync_profile_controls()
            return
        self.note("Sign in to create a workspace or join your team.")
        providers = QFrame()
        provider_buttons = QVBoxLayout(providers)
        provider_buttons.setContentsMargins(0, 0, 0, 0)
        provider_buttons.setSpacing(8)
        google = button("Continue with Google", role="primary")
        google.setIcon(QIcon(str(ASSETS / "google-g.png")))
        google.setIconSize(QSize(18, 18))
        google.setMinimumHeight(44)
        google.clicked.connect(lambda: self.signin("google"))
        provider_buttons.addWidget(google)
        self.first_action = google
        if apple_login_enabled():
            apple = apple_sign_in_button()
            apple.clicked.connect(lambda: self.signin("apple"))
            provider_buttons.addWidget(apple)
        self.column.addWidget(providers)

    def render_privacy(self):
        self.column.addWidget(label("Your account and access", "title"))
        email = getattr(self.window.current_user(), "email", None)
        if email:
            self.column.addWidget(label("Signed in as " + email, wrap=True))
        account = self.window.account_dialog
        workspace_name = next(
            (
                item["name"]
                for item in account.snapshot.get("workspaces", [])
                if item["id"] == self.workspace
            ),
            None,
        )
        if workspace_name:
            self.note("Workspace: " + workspace_name)
        self.note("Only channel members can access private conversations.")
        self.note(
            "You choose which project folder to connect. Applying edits to your original "
            "files and publishing changes require your approval."
        )

    def render_goal(self):
        from aedrova.desktop.iphone_companion import companion_section

        self.column.addWidget(label("What are you here to do?", "title"))
        self.note("Choose a starting point. You can change course in your workspace.")
        for key, title, description, symbol in GOALS:
            choice = button(title, role="outline")
            assign(choice, symbol)
            choice.setMinimumHeight(42)
            choice.setToolTip(description)
            choice.setAccessibleDescription(description)
            choice.clicked.connect(lambda checked=False, goal=key: self.flow.choose_goal(goal))
            self.column.addWidget(choice)
            if self.first_action is None:
                self.first_action = choice
        self.column.addWidget(companion_section())

    def render_project(self):
        self.column.addWidget(label("Connect a project", "title"))
        if not self.has_workspace():
            self.note("Create or join a workspace to continue.")
            workspace = button("Create or join a workspace", role="primary")
            workspace.clicked.connect(self.workspace_settings)
            self.column.addWidget(workspace)
            self.first_action = workspace
            self.flow.primary.hide()
            self.flow.skip.hide()
            return
        self.note("Choose a local folder for builds.")
        self.folder = QLineEdit(self.draft.get("folder", ""))
        self.folder.setPlaceholderText("Project folder")
        self.folder.setAccessibleName("Project folder")
        self.column.addWidget(self.folder)
        actions = QFrame()
        row = QHBoxLayout(actions)
        row.setContentsMargins(0, 0, 0, 0)
        browse = button("Choose folder…", role="outline")
        assign(browse, "folder")
        browse.clicked.connect(self.choose)
        new = button("Start a new project", role="outline")
        assign(new, "plus")
        new.clicked.connect(self.start_new_project)
        row.addWidget(browse)
        row.addWidget(new)
        row.addStretch()
        self.column.addWidget(actions)
        self.provider = CodingProviderChoice()
        self.provider.setCurrentIndex(self.provider.findData(self.draft.get("provider", "auto")))
        self.provider.setAccessibleName("Coding provider")
        self.column.addWidget(label("Coding provider"))
        self.column.addWidget(self.provider)
        self.automatic = QCheckBox("Plan and execute automatically")
        self.automatic.setChecked(
            bool(self.draft.get("background_build", self.draft.get("auto_plan", True)))
        )
        self.column.addWidget(self.automatic)
        warning = label(
            "Automatic execution is off. Start builds manually when you’re ready.",
            "error",
            wrap=True,
        )
        warning.setHidden(self.automatic.isChecked())
        self.automatic.toggled.connect(warning.setHidden)
        self.column.addWidget(warning)
        disclosure = QFrame()
        details = QVBoxLayout(disclosure)
        details.setContentsMargins(0, 3, 0, 0)
        details.setSpacing(5)
        for symbol, text in (
            ("mention", "A mention can share accessible chat with your provider."),
            ("terminal", "Builds edit a copy, run sandboxed tests, and may use credits."),
            ("permission_auto", "You approve changes to original files and publishing."),
        ):
            item = QHBoxLayout()
            item.setSpacing(8)
            glyph = QLabel()
            glyph.setFixedSize(16, 16)
            glyph.setPixmap(icon(symbol, self.flow.theme.secondary).pixmap(16, 16))
            item.addWidget(glyph, alignment=Qt.AlignmentFlag.AlignTop)
            item.addWidget(label(text, "muted", wrap=True), 1)
            details.addLayout(item)
        self.column.addWidget(disclosure)
        self.folder.textChanged.connect(self.status.hide)
        self.automatic.toggled.connect(self.status.hide)

    def show_error(self, text):
        self.status.setText(text)
        self.status.show()

    def choose(self):
        folder = choose_project(self.flow, self.folder.text())
        if folder:
            self.folder.setText(folder)

    def start_new_project(self):
        from aedrova.desktop.new_project import NewProjectDialog

        dialog = NewProjectDialog(self.flow)
        if dialog.exec() and dialog.project_path:
            self.folder.setText(dialog.project_path)

    def save(self):
        if not self.has_workspace() or self.window.workspace_id != self.workspace:
            self.show_error("Open your workspace before connecting a project.")
            return False
        folder = self.folder.text().strip()
        automatic = self.automatic.isChecked()
        if not folder:
            if automatic:
                self.show_error("Choose a project folder to enable automatic builds.")
                return False
            return True
        try:
            root = Path(folder).expanduser().resolve(strict=True)
            if not root.is_dir() or root in (Path.home(), Path(root.anchor)):
                raise ValueError("Choose a specific project folder.")
        except (ValueError, OSError, RuntimeError):
            self.show_error("Choose a specific, accessible project folder.")
            return False
        self.draft.update(
            folder=str(root),
            provider=self.provider.currentData(),
            background_build=automatic,
            auto_plan=automatic,
        )
        save_binding(self.window, self.draft, self.workspace)
        build = getattr(self.window, "build_dialog", None)
        if build and build.background_run and not build.background_authorized():
            build.cancel()
        self.window._render_pages()
        return True

    def advance_profile(self):
        if self.profile_form is not None:
            self.profile_form.advance()

    def profile_saved(self):
        if self.flow.closed:
            return
        self.select_workspace()
        account = self.window.account_dialog
        if self.has_workspace() and (
            not self.window.connected or self.window.workspace_id != self.workspace
        ):
            account.open_dashboard(require_profile=False)
        self.flow.show_stage(PRIVACY)
        self.flow.raise_()
        self.flow.activateWindow()

    def sync_profile_controls(self):
        if self.profile_form is not None and self.page == ACCOUNT:
            self.flow.primary.setEnabled(not self.profile_form.saving)
            self.flow.back.setEnabled(not self.profile_form.saving)
            text = "Saving…" if self.profile_form.saving else "Continue"
            self.flow.primary.setText(text)
            self.flow.primary.setAccessibleName(text)

    def signin(self, provider):
        self.window.show_account()
        account = self.window.account_dialog
        self.login_dialog = account
        account.sign_in_ready.connect(self.signed_in)
        account.finished.connect(self.login_closed)
        self.flow.hide()
        if provider == "apple":
            account.start_apple()
        else:
            account.start_google()

    def disconnect_login(self):
        if self.login_dialog is not None:
            account, self.login_dialog = self.login_dialog, None
            account.sign_in_ready.disconnect(self.signed_in)
            account.finished.disconnect(self.login_closed)

    def signed_in(self):
        from aedrova.desktop.onboarding import account_key

        user = self.window.current_user()
        if self.flow.closed or not user:
            return
        if self.flow.owner is not None and str(user.id) != self.flow.owner:
            self.flow.reject()
            return
        self.flow.owner = str(user.id)
        self.flow.prefix = account_key(self.window)
        self.select_workspace()
        account = self.login_dialog
        if self.has_workspace() and self.flow.profile_complete():
            account.open_dashboard(require_profile=False)
        else:
            account.accept()

    def login_closed(self, *_):
        self.disconnect_login()
        if self.flow.closed:
            return
        self.flow.show_stage(PRIVACY if self.flow.profile_complete() else ACCOUNT)
        self.flow.show()
        self.flow.raise_()
        self.flow.activateWindow()

    def workspace_settings(self):
        self.window.show_account()
        account = self.window.account_dialog
        self.workspace_dialog = account
        account.finished.connect(self.workspace_closed)
        self.flow.hide()

    def stop_workspace_wait(self):
        if self.workspace_dialog is not None:
            account, self.workspace_dialog = self.workspace_dialog, None
            account.finished.disconnect(self.workspace_closed)

    def workspace_closed(self, *_):
        self.stop_workspace_wait()
        from aedrova.desktop.onboarding import account_key

        if self.flow.closed:
            return
        if account_key(self.window) != self.flow.prefix:
            self.flow.reject()
            return
        self.select_workspace()
        if self.has_workspace() and self.workspace == self.window.workspace_id:
            self.flow.show_stage(GOAL)
        else:
            self.flow.show_stage(PROJECT)
        self.flow.show()
        self.flow.raise_()
        self.flow.activateWindow()
