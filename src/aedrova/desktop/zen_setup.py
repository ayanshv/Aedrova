"""Account and project forms for the desktop first-run flow."""

from pathlib import Path

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QCheckBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QVBoxLayout

from aedrova.desktop import motion
from aedrova.desktop.brand import ASSETS
from aedrova.desktop.controls import CodingProviderChoice, choose_project
from aedrova.desktop.dialogs import apple_sign_in_button, button, label
from aedrova.desktop.getting_started import GOALS
from aedrova.desktop.icons import assign, icon
from aedrova.desktop.projects import binding, save_binding
from aedrova.identity.oauth import apple_login_enabled

WELCOME, ACCOUNT, PRIVACY, GOAL, PROJECT, PERMISSIONS, THEME, OPENING, IMPORT = range(9)


def heading(text):
    """The step title: large, light and tight, like a quiet sentence."""
    from PySide6.QtGui import QFont

    from aedrova.desktop.materials import system_font

    widget = label(text, "title")
    widget.setFont(system_font(30, QFont.Weight.DemiBold, -0.4))
    widget.setObjectName("ZenHeading")
    return widget


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
        self.column.setSpacing(16)

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

    def needs_workspace(self):
        return not self.has_workspace() or (
            self.flow.review_profile and not self.flow.workspace_selected
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
        elif stage == PERMISSIONS:
            self.render_permissions()
        elif stage == THEME:
            self.render_theme()
        elif stage == IMPORT:
            self.render_import()
        else:
            self.render_project()
        self.column.addWidget(self.status)
        self.updateGeometry()

    def render_account(self):
        signed_in = self.window.current_user()
        self.column.addWidget(heading("Your profile" if signed_in else "Sign in"))
        if signed_in:
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
        self.note("Create your workspace or join your team.")
        providers = QFrame()
        provider_buttons = QVBoxLayout(providers)
        provider_buttons.setContentsMargins(0, 0, 0, 0)
        provider_buttons.setSpacing(12)
        google = button("Continue with Google", role="primary")
        google.setIcon(QIcon(str(ASSETS / "google-g.png")))
        google.setIconSize(QSize(18, 18))
        google.setMinimumHeight(44)
        google.clicked.connect(lambda: self.signin("google"))
        provider_buttons.addWidget(google)
        self.first_action = google
        self.sign_in_buttons = [google]
        if apple_login_enabled():
            apple = apple_sign_in_button()
            apple.clicked.connect(lambda: self.signin("apple"))
            provider_buttons.addWidget(apple)
            self.sign_in_buttons.append(apple)
        self.column.addWidget(providers)
        self.wait_note = label("", "muted", wrap=True)
        self.wait_note.hide()
        self.column.addWidget(self.wait_note)
        self.cancel_signin = button("Cancel", role="outline")
        self.cancel_signin.hide()
        self.cancel_signin.clicked.connect(self.stop_signin)
        self.column.addWidget(self.cancel_signin, alignment=Qt.AlignmentFlag.AlignLeft)

    def render_privacy(self):
        self.column.addWidget(heading("You’re in control"))
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
        self.note("Private chats stay private. You approve every change and publish.")

    def render_permissions(self):
        from aedrova.desktop.permission_cards import PermissionsPage
        from aedrova.meetings.devices import NativeDevices

        self.column.addWidget(heading("Set up permissions"))
        self.note("Aedrova asks only when you start a call or share. You can change this anytime.")
        backend = getattr(self.flow, "permission_backend", None) or NativeDevices(self.flow)
        if not hasattr(self.flow, "assumed_permissions"):
            self.flow.assumed_permissions = set()
        self.permissions = PermissionsPage(backend, assumed=self.flow.assumed_permissions)
        self.column.addWidget(self.permissions)
        self.permissions.changed.connect(self.flow.permissions_changed)
        self.flow.permissions_changed()
        self.first_action = self.permissions.all

    def can_import_history(self):
        """Only the person who just made the workspace (an owner or admin) is offered the import."""
        account = getattr(self.window, "account_dialog", None)
        user = self.window.current_user()
        if not account or not user or not self.workspace:
            return False
        return any(
            str(member.get("user_id")) == str(user.id)
            and str(member.get("workspace_id")) == str(self.workspace)
            and member.get("role") in {"owner", "admin"}
            for member in account.snapshot.get("members", [])
        )

    def render_import(self):
        from aedrova.desktop.slack_history import SlackImportPanel

        self.column.addWidget(heading("Bring your Slack history"))
        self.note(
            "Optional. Drop a public-channel export and past decisions become searchable. "
            "You can also do this later in Workspace settings."
        )
        self.import_panel = SlackImportPanel(self.window.account_dialog.service, self.workspace)
        self.import_panel.imported.connect(self.history_imported)
        self.column.addWidget(self.import_panel)
        self.first_action = self.import_panel.choose_button
        self.note("Members can search it. Agents use it only when your workspace AI is on.")

    def history_imported(self, count):
        self.flow.history_imported = count
        self.flow.primary.setText("Continue")
        self.flow.primary.show()
        self.flow.skip.hide()
        self.flow.actions.show()
        self.flow.primary.setFocus()

    def render_theme(self):
        from PySide6.QtWidgets import QButtonGroup

        from aedrova.desktop.zen_visuals import ThemePhoto

        self.column.addWidget(heading("Choose your theme"))
        self.note("Pick light or dark mode to match your style.")
        row = QFrame()
        photos = QHBoxLayout(row)
        photos.setContentsMargins(0, 8, 0, 0)
        photos.setSpacing(12)
        group = QButtonGroup(row)
        for mode in ("system", "light", "dark"):
            photo = ThemePhoto(mode)
            photo.setFixedWidth(112)
            photo.setChecked(mode == self.flow.theme_mode)
            photo.clicked.connect(lambda _=False, chosen=mode: self.flow.choose_theme(chosen))
            group.addButton(photo)
            photos.addWidget(photo)
            if self.first_action is None:
                self.first_action = photo
        photos.addStretch()
        self.column.addWidget(row)
        self.flow.art.set_preview(self.flow.theme_mode)

    def render_goal(self):
        from aedrova.desktop.iphone_companion import companion_section

        self.column.addWidget(heading("What first?"))
        self.note("Pick one. Change it anytime.")
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
        if self.needs_workspace():
            self.render_workspace()
            return
        self.column.addWidget(heading("Connect a project"))
        self.note("Pick the folder Aedrova builds in.")
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
        self.provider.setAccessibleName("Agent")
        self.column.addWidget(label("Agent"))
        self.column.addWidget(self.provider)
        self.automatic = QCheckBox("Plan and execute automatically")
        self.automatic.setChecked(
            bool(self.draft.get("background_build", self.draft.get("auto_plan", True)))
        )
        self.column.addWidget(self.automatic)
        warning = label(
            "Automatic builds are off. Start them yourself.",
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
            ("mention", "Mentions share team chat with the AI."),
            ("terminal", "Builds run on a copy of your project."),
            ("permission_auto", "You approve changes to your files."),
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

    def render_workspace(self):
        """Create a workspace or join one with a code, right here in setup."""
        self.column.addWidget(heading("Your workspace"))
        self.note("Name it for your team, or join one with a code.")
        self.workspace_name = QLineEdit()
        self.workspace_name.setPlaceholderText("Workspace name, e.g. Northstar Labs")
        self.workspace_name.setMaxLength(80)
        self.workspace_name.setAccessibleName("Workspace name")
        self.workspace_name.setMinimumHeight(44)
        self.column.addWidget(self.workspace_name)
        self.workspace_ack = QCheckBox(
            "Let Aedrova work in this workspace. You approve each change."
        )
        self.column.addWidget(self.workspace_ack)
        self.create_button = button("Create workspace", role="primary")
        self.create_button.setMinimumHeight(44)
        self.create_button.setEnabled(False)
        self.create_button.clicked.connect(self.create_workspace)
        self.column.addWidget(self.create_button)
        for signal in (self.workspace_name.textChanged, self.workspace_ack.toggled):
            signal.connect(self.sync_create_button)
        self.workspace_name.returnPressed.connect(self.create_workspace)
        self.join_code = QLineEdit()
        self.join_code.setPlaceholderText("Invitation code")
        self.join_code.setEchoMode(QLineEdit.EchoMode.Password)
        self.join_code.setAccessibleName("Invitation code")
        self.join_code.setMinimumHeight(44)
        self.join_code.hide()
        self.join_button = button("Join workspace", role="primary")
        self.join_button.setMinimumHeight(44)
        self.join_button.hide()
        self.join_button.clicked.connect(self.join_workspace)
        self.join_code.returnPressed.connect(self.join_workspace)
        self.have_code = button("I have an invitation code", role="outline")
        self.have_code.clicked.connect(self.show_join)
        self.column.addWidget(self.have_code)
        self.column.addWidget(self.join_code)
        self.column.addWidget(self.join_button)
        if self.has_workspace():
            existing = button("Use an existing workspace", role="outline")
            existing.clicked.connect(lambda: self.workspace_settings(create=False))
            self.column.addWidget(existing)
        self.first_action = self.workspace_name
        self.flow.primary.hide()
        self.flow.skip.hide()
        self.flow.actions.setVisible(not self.flow.back.isHidden())

    def sync_create_button(self, *_):
        self.create_button.setEnabled(
            bool(self.workspace_name.text().strip()) and self.workspace_ack.isChecked()
        )

    def show_join(self):
        self.have_code.hide()
        self.join_code.show()
        self.join_button.show()
        self.join_code.setFocus()
        motion.fade_in(self.join_code, motion.BASE)

    def working(self, text):
        for control in (
            self.workspace_name,
            self.workspace_ack,
            self.create_button,
            self.join_code,
            self.join_button,
            self.have_code,
        ):
            control.setEnabled(False)
        self.status.setProperty("role", "muted")
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)
        self.status.setText(text)
        self.status.show()
        self.flow.back.setEnabled(False)

    def idle_again(self, text):
        for control in (
            self.workspace_name,
            self.workspace_ack,
            self.have_code,
            self.join_code,
            self.join_button,
        ):
            control.setEnabled(True)
        self.sync_create_button()
        self.flow.back.setEnabled(True)
        self.show_error(text)

    def start_workspace_job(self, run):
        """Run an account action with that window kept out of sight, then open the workspace."""
        account = self.window.ensure_account_dialog()
        account.quiet = True
        self.workspace_dialog = account
        account.finished.connect(self.workspace_closed)
        self.job_account = account
        account.operation_finished.connect(self.workspace_job_done)
        account.operation_failed.connect(self.workspace_job_failed)
        self.job_tries = 0
        self.job_run = run
        self.attempt_workspace_job()

    def attempt_workspace_job(self):
        account = self.job_account
        if self.flow.closed:
            return
        if account.busy and self.job_tries < 40:  # the snapshot after sign-in may still be loading
            self.job_tries += 1
            QTimer.singleShot(250, self, self.attempt_workspace_job)
            return
        self.job_run(account)

    def release_job(self):
        account = getattr(self, "job_account", None)
        if account is None:
            return
        self.job_account = None
        for signal, slot in (
            (account.operation_finished, self.workspace_job_done),
            (account.operation_failed, self.workspace_job_failed),
        ):
            try:
                signal.disconnect(slot)
            except (RuntimeError, TypeError):
                pass

    def workspace_job_done(self):
        account = self.job_account
        if account is None or account.busy or self.flow.closed:
            return
        self.select_workspace()
        if self.has_workspace() and account.workspace_id():
            self.release_job()
            self.working("Opening your workspace…")
            account.open_dashboard(require_profile=False)
        # otherwise the action is still finishing; the next finished operation lands here again

    def workspace_job_failed(self):
        account = self.job_account
        self.release_job()
        self.stop_workspace_wait()
        if account is not None:
            account.quiet = False
        self.idle_again(
            account.status.text()
            if account is not None and account.status.text()
            else "That didn’t work. Check your connection and try again."
        )

    def create_workspace(self):
        name = self.workspace_name.text().strip()
        if not name or not self.workspace_ack.isChecked():
            return
        self.working("Creating your workspace…")

        def run(account):
            account.begin_onboarding()
            account.onboarding_workspace.setText(name)
            account.onboarding_ack.setChecked(True)
            account.complete_onboarding()

        self.start_workspace_job(run)

    def join_workspace(self):
        code = self.join_code.text().strip()
        if not code:
            self.show_error("Paste the invitation code you were given.")
            return
        self.working("Joining your team…")
        self.start_workspace_job(
            lambda account: account.mutate("accept_invitation", {"p_token": code})
        )

    def show_error(self, text):
        self.status.setProperty("role", "error")
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)
        self.status.setText(text)
        self.status.show()

    def choose(self):
        folder = choose_project(self.flow, self.folder.text())
        self.flow.regain_focus()
        if folder:
            self.folder.setText(folder)

    def start_new_project(self):
        from aedrova.desktop.new_project import NewProjectDialog

        dialog = NewProjectDialog(self.flow)
        accepted = dialog.exec()
        self.flow.regain_focus()
        if accepted and dialog.project_path:
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
        self.flow.profile_reviewed = True
        self.select_workspace()
        account = self.window.account_dialog
        if not self.needs_workspace() and (
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
        """Sign in without leaving setup: the browser does the asking, this screen waits."""
        account = self.window.ensure_account_dialog()
        account.quiet = True
        self.login_dialog = account
        account.sign_in_ready.connect(self.signed_in)
        account.finished.connect(self.login_closed)
        account.operation_failed.connect(self.signin_failed)
        for choice in getattr(self, "sign_in_buttons", []):
            choice.setEnabled(False)
        self.wait_note.setText(
            f"Continue with {provider.title()} in your browser. Setup waits here."
        )
        self.wait_note.show()
        self.cancel_signin.show()
        motion.fade_in(self.wait_note, motion.BASE)
        if provider == "apple":
            account.start_apple()
        else:
            account.start_google()

    def signin_failed(self):
        for choice in getattr(self, "sign_in_buttons", []):
            choice.setEnabled(True)
        self.cancel_signin.hide()
        self.wait_note.setText("Sign-in didn’t finish. Try again when you’re ready.")

    def stop_signin(self):
        account = self.login_dialog
        self.disconnect_login()
        if account is not None:
            account.cancel_google()
        for choice in getattr(self, "sign_in_buttons", []):
            choice.setEnabled(True)
        self.wait_note.hide()
        self.cancel_signin.hide()

    def disconnect_login(self):
        if self.login_dialog is not None:
            account, self.login_dialog = self.login_dialog, None
            account.quiet = False
            account.sign_in_ready.disconnect(self.signed_in)
            account.finished.disconnect(self.login_closed)
            account.operation_failed.disconnect(self.signin_failed)

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

    def workspace_settings(self, *, create=None):
        if create is None:
            create = self.needs_workspace()
        self.window.ensure_account_dialog().quiet = False
        self.window.show_account("create" if create else None)
        account = self.window.account_dialog
        self.workspace_dialog = account
        account.finished.connect(self.workspace_closed)
        self.flow.hide()

    def stop_workspace_wait(self):
        if self.workspace_dialog is not None:
            account, self.workspace_dialog = self.workspace_dialog, None
            account.quiet = False
            account.finished.disconnect(self.workspace_closed)

    def workspace_closed(self, *_):
        self.stop_workspace_wait()
        QTimer.singleShot(0, self, self.resume_workspace_flow)

    def resume_workspace_flow(self):
        from aedrova.desktop.onboarding import account_key

        if self.flow.closed:
            return
        if account_key(self.window) != self.flow.prefix:
            self.flow.reject()
            return
        self.select_workspace()
        if (
            self.has_workspace()
            and self.workspace == self.window.workspace_id
            and self.window.connected
            and self.window.connected.active
        ):
            self.flow.workspace_selected = True
            self.flow.show_stage(PROJECT if self.flow.created_workspace == self.workspace else GOAL)
        else:
            self.flow.show_stage(PROJECT)
        self.flow.show()
        self.flow.raise_()
        self.flow.activateWindow()
