"""Real, optional setup pages for the animated introduction; grants are never implicit."""

from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QSize, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLayout,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
)

from aedrova.delivery.github import repository_name
from aedrova.desktop.brand import ASSETS
from aedrova.desktop.controls import ChoiceBox, CodingProviderChoice, choose_project
from aedrova.desktop.dialogs import button, label
from aedrova.desktop.projects import binding, save_binding
from aedrova.desktop.zen_visuals import ProjectPicker, SetupVisual, ThemePhoto

SETUP_STEPS = (
    ("Choose your style", "Make the workspace feel like yours.", "Continue"),
    (
        "Your account",
        "Your teammates should know who is behind the good ones.",
        "Continue",
    ),
    (
        "Connect your workspace",
        "Connect a specific folder. Your original files stay under your control.",
        "Continue",
    ),
    (
        "Choose your agent’s workflow",
        "Choose how much your agent may do after an explicit mention.",
        "Continue",
    ),
    (
        "Connect with GitHub",
        "Connect GitHub when you are ready to publish reviewed work.",
        "Continue",
    ),
    (
        "Meet face to face",
        "Check devices deliberately. Nothing records in the background.",
        "Continue",
    ),
    (
        "You’re good to go",
        "Real settings. Clear permissions. No surprise builds.",
        "Save & enter workspace",
    ),
)
LAST_STAGE = 4 + len(SETUP_STEPS)


class SetupPages(QScrollArea):
    def __init__(self, flow):
        super().__init__(flow)
        self.flow, self.window = flow, flow.window
        self.workspace = self.window.workspace_id
        self.original = binding(self.window, self.workspace)
        self.draft = dict(self.original)
        self.preferences = {
            "theme": self.window.theme_mode,
            "motion": self.window.reduced_motion,
            "transparency": self.window.reduced_transparency,
            "editor": self.window.settings.value("editor", "Visual Studio Code"),
        }
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.Shape.NoFrame)
        self.setObjectName("ZenSettings")
        self.viewport().setAutoFillBackground(False)
        self.body = QFrame()
        self.body.setFrameShape(QFrame.Shape.NoFrame)
        self.body.setObjectName("ZenSettingsBody")
        self.setWidget(self.body)
        self.column = QVBoxLayout(self.body)
        self.column.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.column.setContentsMargins(20, 18, 20, 18)
        self.column.setSpacing(16)
        self.page = None
        self.status = None
        self.login_dialog = None
        self.login_active = False
        self.login_completed = False

    def note(self, text):
        self.column.addWidget(label(text, "muted", wrap=True))

    def capture(self):
        if self.page == 4:
            self.preferences.update(
                theme=self.appearance.currentData(),
                motion=self.motion.isChecked(),
                transparency=self.transparency.isChecked(),
                editor=self.editor.currentText(),
            )
        elif self.page == 6:
            self.draft.update(
                folder=self.folder.text().strip(), provider=self.provider.currentData()
            )
        elif self.page == 7:
            self.draft.update(
                background_build=self.automatic.isChecked(), auto_plan=self.automatic.isChecked()
            )
        elif self.page == 8:
            self.draft["repository"] = self.repository.text().strip()

    def render(self, stage):
        self.capture()
        self.page = stage
        if hasattr(self, "appearance"):
            self.appearance.deleteLater()
            del self.appearance
        self.column.setSpacing(12 if stage == 4 else 16)
        while self.column.count():
            item = self.column.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()
        self.status = label("", "muted", wrap=True)
        self.status.setAccessibleName("Onboarding setup status")
        if stage == 4:
            self.column.addWidget(label("Appearance", "title"))
            self.appearance = ChoiceBox(self.body)
            for title, value in (("Light", "light"), ("Dark", "dark"), ("Match macOS", "system")):
                self.appearance.addItem(title, value)
            self.appearance.setCurrentIndex(self.appearance.findData(self.preferences["theme"]))
            self.appearance.setAccessibleName("Dashboard appearance")
            self.appearance.hide()
            self.photo_group = QButtonGroup(self)
            photo_row = QHBoxLayout()
            photo_row.setSpacing(12)
            photo_row.setContentsMargins(0, 0, 0, 0)
            self.theme_photos = {}
            for mode in ("light", "dark", "system"):
                card = ThemePhoto(mode)
                self.photo_group.addButton(card)
                card.setChecked(mode == self.preferences["theme"])
                card.clicked.connect(
                    lambda checked=False, value=mode: self.appearance.setCurrentIndex(
                        self.appearance.findData(value)
                    )
                )
                photo_row.addWidget(card, 1)
                self.theme_photos[mode] = card
            photo_container = QFrame()
            photo_container.setLayout(photo_row)
            self.column.addWidget(photo_container)
            self.appearance.currentIndexChanged.connect(self.sync_theme_photos)
            self.editor = ChoiceBox()
            self.editor.addItems(["Visual Studio Code", "Cursor", "Xcode", "Finder"])
            self.editor.setCurrentText(self.preferences["editor"])
            self.editor.setAccessibleName("Preferred editor")
            self.column.addWidget(label("Your editor", "title"))
            self.column.addWidget(self.editor)
            self.motion = QCheckBox("Reduce motion")
            self.motion.setChecked(self.preferences["motion"])
            self.column.addWidget(self.motion)
            self.transparency = QCheckBox("Reduce transparency")
            self.transparency.setChecked(self.preferences["transparency"])
            self.column.addWidget(self.transparency)
            self.motion.toggled.connect(self.preview_motion)
            self.note(
                "Your introduction and dashboard follow this look. "
                "System matches macOS automatically."
            )
        elif stage == 5:
            if self.window.current_user():
                from aedrova.desktop.profile import ProfileDialog

                self.profile_form = ProfileDialog(
                    self.window,
                    self.window.account_dialog,
                    onboarding=True,
                    continued=self.profile_saved,
                )
                self.profile_form.setParent(self.body, Qt.WindowType.Widget)
                self.profile_form.setMinimumSize(0, 400)
                identity = self.profile_form.steps[0].layout()
                identity.itemAt(0).widget().hide()
                identity.itemAt(1).widget().hide()
                self.profile_form.avatar.setFixedSize(64, 64)
                self.profile_form.layout().setContentsMargins(12, 8, 12, 8)
                self.profile_form.next.hide()
                self.profile_form.back.hide()
                self.profile_form.state_changed.connect(self.sync_profile_controls)
                for control in self.profile_form.findChildren(QPushButton):
                    if control.text() == "Finish later":
                        control.hide()
                self.column.addWidget(self.profile_form)
                self.note(
                    "Confirm your name and username to continue. "
                    "Photo and other details are optional."
                )
            else:
                self.column.addWidget(SetupVisual(self.flow, "profile"))
                self.note("Sign in with Google, then confirm how your team will see you.")
                signin = button("Continue with Google", role="primary")
                signin.setIcon(QIcon(str(ASSETS / "google-g.png")))
                signin.setIconSize(QSize(20, 20))
                signin.clicked.connect(self.signin)
                self.column.addWidget(signin)
        elif stage == 6:
            user = self.window.current_user()
            if user:
                self.note("Signed in · " + (getattr(user, "email", None) or "Google account"))
                if self.workspace is None:
                    self.note("Create or join your team's workspace before connecting a project.")
                    workspace = button("Create or join a workspace", role="primary")
                    workspace.clicked.connect(self.workspace_settings)
                    self.column.addWidget(workspace)
            self.folder = QLineEdit(self.draft.get("folder", ""))
            self.folder.setPlaceholderText("Choose a specific project folder")
            self.folder.setAccessibleName("Onboarding project folder")
            self.project_picker = ProjectPicker(self.flow, self.folder)
            self.project_picker.clicked.connect(self.choose)
            self.column.addWidget(self.project_picker)
            self.column.addWidget(self.folder)
            self.provider = CodingProviderChoice()
            self.provider.setCurrentIndex(
                max(0, self.provider.findData(self.draft.get("provider", "codex")))
            )
            self.provider.setAccessibleName("Coding provider")
            self.column.addWidget(self.provider)
            self.note(
                "A folder connection is private to your account on this Mac. Builds "
                "use a separate copy. "
                "Provider login and usage allowance are required separately; choosing "
                "a provider does not sign in."
            )
        elif stage == 7:
            self.automatic = QCheckBox("Let my agent plan and execute automatically")
            self.automatic.setChecked(
                self.draft.get("background_build", self.draft.get("auto_plan", True))
            )
            self.column.addWidget(
                SetupVisual(self.flow, "workflow", enabled=self.automatic.isChecked)
            )
            self.column.addWidget(self.automatic)
            self.automatic.toggled.connect(lambda *_: self.body.update())
            self.note(
                "After an explicit @mention, this permits sharing accessible workspace "
                "conversations "
                "with your chosen provider, creating a plan, editing a build copy and "
                "running sandboxed tests "
                "without further prompts. Provider usage may be billed."
            )
            self.note(
                "Applying changes to the original project and pushing to GitHub still "
                "require approval. "
                "Private channel access follows membership. You can revoke this in "
                "Project settings."
            )
        elif stage == 8:
            self.column.addWidget(SetupVisual(self.flow, "repository"))
            self.repository = QLineEdit(self.draft.get("repository", ""))
            self.repository.setPlaceholderText("owner/repository · optional")
            self.repository.setAccessibleName("GitHub repository")
            self.column.addWidget(self.repository)
            setup = button("Set up GitHub CLI & sign in", role="outline")
            setup.clicked.connect(self.github)
            self.column.addWidget(setup)
            self.note(
                "The helper installer and GitHub authorization run only when you choose them. "
                "Saving a repository name does not prove access or authorize a push."
            )
        elif stage == 9:
            self.column.addWidget(SetupVisual(self.flow, "meeting"))
            devices = button("Check microphone, camera & screen", role="outline")
            devices.clicked.connect(self.devices)
            self.column.addWidget(devices)
            self.note(
                "macOS may ask for device permissions only when you start a specific check. "
                "A check never starts a call. You can skip and configure this when needed."
            )
            self.note(
                "No recording, transcription or AI meeting access is enabled here. "
                "Shared meeting hosting and transcription still follow their release requirements."
            )
        elif stage == 10:
            self.column.addWidget(SetupVisual(self.flow, "review"))
            name = (
                Path(self.draft["folder"]).name
                if self.draft.get("folder")
                else "Not connected · configure later"
            )
            self.column.addWidget(label("Project · " + name, "title", wrap=True))
            self.note("Provider · " + self.draft.get("provider", "codex"))
            self.note(
                "Agent workflow · "
                + (
                    "Automatic after your mention"
                    if self.draft.get("background_build")
                    else "Review plans before execution"
                )
            )
            self.note(
                "Repository · "
                + (self.draft.get("repository") or "Not connected · configure later")
            )
            self.note(
                "Provider sign-in, repository access and device permission are not "
                "claimed as ready by this summary."
            )
            self.note(
                "Save applies the local preferences and project permissions shown "
                "above. No build, call or push starts."
            )
        self.column.addWidget(self.status)
        self.column.addStretch()
        self.column.invalidate()
        self.column.activate()
        self.body.updateGeometry()
        self.verticalScrollBar().setValue(0)

    def sync_theme_photos(self):
        mode = self.appearance.currentData()
        self.preferences["theme"] = mode
        self.flow.apply_appearance(mode)
        for mode, card in self.theme_photos.items():
            card.setChecked(mode == self.appearance.currentData())

    def preview_motion(self, checked):
        self.flow.reduced = checked
        self.flow.canvas.update()

    def choose(self):
        folder = choose_project(self.flow, self.folder.text())
        if folder:
            self.folder.setText(folder)

    def valid(self):
        self.capture()
        if self.window.current_user() and self.workspace is None:
            self.status.setText("Create or join a workspace before continuing.")
            return False
        try:
            folder = self.draft.get("folder", "")
            if folder:
                root = Path(folder).expanduser().resolve(strict=True)
                if not root.is_dir() or root in (Path.home(), Path(root.anchor)):
                    raise ValueError("Choose a specific, accessible project folder.")
                self.draft["folder"] = str(root)
                if not self.same_account():
                    raise ValueError(
                        "Sign in to your original account and workspace to connect a project."
                    )
            if self.page != 6 and self.draft.get("background_build") and not folder:
                raise ValueError("Choose a project folder first, or turn automatic builds off.")
            if self.draft.get("repository"):
                self.draft["repository"] = repository_name(self.draft["repository"])
        except (ValueError, OSError):
            self.status.setText(
                "Choose an accessible project folder, sign in, and use "
                "owner/repository for GitHub. "
                "Automatic builds need a connected project."
            )
            return False
        return True

    def same_account(self):
        user = self.window.current_user()
        return bool(
            user
            and bool(self.workspace)
            and str(user.id) == self.flow.owner
            and self.window.workspace_id == self.workspace
        )

    def save(self):
        if not self.valid():
            return False
        if self.draft.get("folder"):
            if not self.same_account():
                return False
            save_binding(self.window, self.draft, self.workspace)
            build = getattr(self.window, "build_dialog", None)
            if build and build.background_run and not build.background_authorized():
                build.cancel()
            self.window._render_pages()
        self.window.set_theme(self.preferences["theme"])
        self.window.reduce_motion_action.setChecked(self.preferences["motion"])
        self.window.reduce_transparency_action.setChecked(self.preferences["transparency"])
        self.window.settings.setValue("editor", self.preferences["editor"])
        return True

    def show_child(self, dialog):
        if dialog is None:
            return
        from aedrova.desktop.theme import palette

        old_style, old_palette = dialog.styleSheet(), dialog.palette()
        self.flow.hide()
        dialog.setPalette(palette(self.flow.theme))
        dialog.setStyleSheet(self.flow.styleSheet())
        dialog.finished.connect(
            lambda *_: (dialog.setStyleSheet(old_style), dialog.setPalette(old_palette))
        )
        dialog.show()
        if not self.flow.reduced:
            from PySide6.QtWidgets import QApplication

            if QApplication.platformName() != "offscreen":
                dialog.zen_transition = QPropertyAnimation(dialog, b"windowOpacity", dialog)
                dialog.zen_transition.setDuration(220)
                dialog.zen_transition.setStartValue(0.0)
                dialog.zen_transition.setEndValue(1.0)
                dialog.zen_transition.setEasingCurve(QEasingCurve.Type.OutCubic)
                dialog.zen_transition.start()
        dialog.raise_()
        dialog.activateWindow()
        dialog.finished.connect(self.resume)

    def resume(self, *_):
        from aedrova.desktop.onboarding import account_key

        if self.flow.closed:
            return
        user = self.window.current_user()
        newly_signed_in = self.flow.owner is None and user
        if newly_signed_in:
            self.flow.owner = str(user.id)
            self.flow.prefix = account_key(self.window)
        elif account_key(self.window) != self.flow.prefix:
            self.flow.reject()
            return
        if newly_signed_in or (user and self.workspace is None):
            account = self.window.account_dialog
            allowed = {item["id"] for item in account.snapshot.get("workspaces", [])}
            self.workspace = (
                self.window.workspace_id if self.window.workspace_id in allowed else None
            )
            self.original = binding(self.window, self.workspace) if self.workspace else {}
            self.draft = dict(self.original)
        advance = self.login_active and self.login_completed and bool(user)
        self.login_active = self.login_completed = False
        if advance:
            self.flow.show_stage(5)
        else:
            self.render(self.page)
        self.flow.entered = self.flow.now()
        self.flow.show()
        self.flow.raise_()
        self.flow.activateWindow()
        self.flow.primary.setFocus()

    def signin(self):
        self.window.show_account()
        account = self.window.account_dialog
        if self.login_dialog is not account:
            if self.login_dialog is not None:
                self.login_dialog.sign_in_ready.disconnect(self.signed_in)
            self.login_dialog = account
            account.sign_in_ready.connect(self.signed_in)
        self.login_active = True
        self.login_completed = False
        self.show_child(account)

    def signed_in(self):
        if self.flow.closed or not self.login_active or self.page != 5:
            return
        account = self.login_dialog
        user = self.window.current_user()
        if user is None:
            return
        if self.flow.owner is not None and str(user.id) != self.flow.owner:
            account.accept()
            self.flow.reject()
            return
        self.login_completed = True
        if account.snapshot.get("workspaces"):
            # Use the same authenticated dashboard activation as normal sign-in.
            account.open_dashboard()
        else:
            self.window.update_profile_button()
            account.accept()

    def go_back(self):
        if self.page == 5 and hasattr(self, "profile_form"):
            form = self.profile_form
            if form.saving:
                return
            if form.stack.currentIndex() > 0:
                form.go(form.stack.currentIndex() - 1)
                return
        self.flow.show_stage(self.flow.stage - 1)

    def advance_profile(self):
        if self.window.current_user() is None:
            self.status.setText("Sign in with Google to continue.")
            return
        if self.profile_form.saving:
            return
        self.profile_form.advance()
        if self.page == 5:
            self.sync_profile_controls()

    def sync_profile_controls(self):
        if self.page != 5 or self.flow.closed:
            return
        self.profile_form.back.hide()
        self.flow.primary.setText(self.profile_form.next.text())
        self.flow.primary.setEnabled(not self.profile_form.saving)
        self.flow.back.setEnabled(not self.profile_form.saving)
        self.flow.skip.setEnabled(not self.profile_form.saving and self.flow.profile_complete())

    def profile_saved(self):
        if self.flow.closed or not self.same_user():
            return
        self.flow.show_stage(6)

    def same_user(self):
        user = self.window.current_user()
        return bool(user and str(user.id) == self.flow.owner)

    def profile(self):
        from aedrova.desktop.profile import open_profile_editor

        self.show_child(open_profile_editor(self.window))

    def workspace_settings(self):
        self.window.show_account("manage")
        account = self.window.account_dialog
        if self.workspace is None:
            self.workspace_dialog = account
            self.workspace_waiting = True
            account.snapshot_loaded.connect(self.workspace_ready)
            account.finished.connect(self.stop_workspace_wait)
        self.show_child(account)

    def stop_workspace_wait(self, *_):
        if getattr(self, "workspace_waiting", False):
            self.workspace_waiting = False
            self.workspace_dialog.snapshot_loaded.disconnect(self.workspace_ready)
            self.workspace_dialog.finished.disconnect(self.stop_workspace_wait)

    def workspace_ready(self):
        account = self.workspace_dialog
        user = self.window.current_user()
        if self.flow.closed or user is None or str(user.id) != self.flow.owner:
            return
        if not account.snapshot.get("workspaces"):
            return
        self.stop_workspace_wait()
        account.open_dashboard()

    def github(self):
        from aedrova.desktop.github_setup import open_github_setup

        open_github_setup(self.window)
        self.show_child(self.window.github_setup)

    def devices(self):
        from aedrova.desktop.meeting_setup import open_meeting_setup

        open_meeting_setup(self.window)
        self.show_child(self.window.meeting_setup)
