"""First-run setup for the desktop workspace."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from aedrova.desktop.brand import BrandLockup
from aedrova.desktop.controls import AppDialog
from aedrova.desktop.dialogs import button, label
from aedrova.desktop.onboarding_motion import OnboardingStack
from aedrova.desktop.theme import palette
from aedrova.desktop.zen_setup import ACCOUNT, GOAL, PRIVACY, PROJECT, WELCOME, SetupPages
from aedrova.desktop.zen_theme import onboarding_styles, resolve_theme


class ZenOnboarding(AppDialog):
    def __init__(self, window):
        super().__init__(window)
        from aedrova.desktop.onboarding import account_key

        self.window = window
        user = window.current_user()
        self.prefix = account_key(window)
        self.owner = str(user.id) if user else None
        self.closed = False
        self.reduced_motion = window.reduced_motion
        self.setWindowTitle("Aedrova · Welcome")
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setMinimumSize(560, 580)
        self.resize(650, 660)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setObjectName("ZenSettings")
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        surface = QWidget()
        surface.setObjectName("ZenSettingsBody")
        scroll.setWidget(surface)
        center = QVBoxLayout(surface)
        center.setContentsMargins(32, 28, 32, 28)
        center.addStretch()
        self.content = QWidget()
        self.content.setMaximumWidth(440)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(self.content, 100)
        row.addStretch()
        center.addLayout(row)
        center.addStretch()

        column = QVBoxLayout(self.content)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(16)
        column.addWidget(BrandLockup(29, 18), alignment=Qt.AlignmentFlag.AlignHCenter)

        self.pages = OnboardingStack(self)
        intro = QWidget()
        welcome = QVBoxLayout(intro)
        welcome.setContentsMargins(0, 0, 0, 0)
        welcome.setSpacing(8)
        title = label("Welcome to Aedrova", "display", wrap=True)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome.addWidget(title)
        subtitle = label("One place for team chat, projects, and Agents.", "muted", wrap=True)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        welcome.addWidget(subtitle)
        self.pages.addWidget(intro)
        self.setup = SetupPages(self)
        self.pages.addWidget(self.setup)
        column.addWidget(self.pages)

        self.actions = QWidget()
        actions = QHBoxLayout(self.actions)
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(8)
        actions.addStretch()
        self.back = button("Back")
        self.back.clicked.connect(self.go_back)
        actions.addWidget(self.back)
        self.skip = button("Set up later")
        self.skip.clicked.connect(self.finish)
        actions.addWidget(self.skip)
        self.primary = button("Get started", role="primary")
        self.primary.setObjectName("OnboardingContinue")
        self.primary.setProperty("onboardingAction", True)
        self.primary.setMinimumHeight(44)
        self.primary.setDefault(True)
        self.primary.clicked.connect(self.activate)
        actions.addWidget(self.primary)
        actions.addStretch()
        column.addWidget(self.actions)

        self.theme_mode = window.theme_mode
        self.apply_appearance(self.theme_mode)
        self.style_hints = QApplication.instance().styleHints()
        self.style_hints.colorSchemeChanged.connect(self.system_appearance_changed)
        self.show_stage(WELCOME)

    def apply_appearance(self, mode):
        self.theme_mode = mode
        self.theme = resolve_theme(mode)
        self.setPalette(palette(self.theme))
        self.setStyleSheet(onboarding_styles(self.theme))

    def system_appearance_changed(self, *_):
        if self.theme_mode == "system":
            self.apply_appearance("system")

    def show_stage(self, stage):
        self.stage = stage
        self.back.setVisible(stage == GOAL or (stage == ACCOUNT and self.owner is None))
        self.back.setEnabled(True)
        self.skip.setVisible(stage in (GOAL, PROJECT))
        self.skip.setText("Skip for now" if stage == GOAL else "Set up later")
        self.primary.setVisible(
            stage != GOAL and (stage != ACCOUNT or self.window.current_user() is not None)
        )
        self.primary.setEnabled(True)
        self.primary.setText(
            "Get started"
            if stage == WELCOME
            else "Open workspace"
            if stage == PROJECT
            else "Continue"
        )
        self.primary.setAccessibleName(self.primary.text())
        if stage != WELCOME:
            self.setup.render(stage)
        self.actions.setVisible(
            any(not control.isHidden() for control in (self.back, self.skip, self.primary))
        )
        page_index = 0 if stage == WELCOME else 1
        for index in range(self.pages.count()):
            self.pages.widget(index).setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Preferred if index == page_index else QSizePolicy.Policy.Ignored,
            )
        self.pages.setCurrentIndex(page_index)
        self.pages.updateGeometry()
        self.content.updateGeometry()
        if not self.primary.isHidden():
            self.primary.setFocus()
        elif self.setup.first_action is not None:
            self.setup.first_action.setFocus()

    def go_back(self):
        self.show_stage(PRIVACY if self.stage == GOAL else WELCOME)

    def choose_goal(self, goal):
        self.finish(goal=goal)

    def activate(self):
        from aedrova.desktop.onboarding import account_key

        if account_key(self.window) != self.prefix:
            self.reject()
        elif self.stage == WELCOME:
            self.show_stage(PRIVACY if self.profile_complete() else ACCOUNT)
        elif self.stage == ACCOUNT:
            self.setup.advance_profile()
        elif self.stage == PRIVACY:
            if self.setup.has_workspace():
                self.show_stage(GOAL)
            else:
                self.show_stage(PROJECT)
        elif self.setup.save():
            self.finish()

    def profile_complete(self):
        account = getattr(self.window, "account_dialog", None)
        profile = account.snapshot.get("user_profile") if account else None
        return bool(
            self.window.current_user()
            and isinstance(profile, dict)
            and profile.get("profile_completed")
        )

    def finish(self, *, goal=None):
        from aedrova.desktop.onboarding import account_key

        if self.closed:
            return
        if account_key(self.window) != self.prefix:
            self.reject()
            return
        account = getattr(self.window, "account_dialog", None)
        if not self.setup.has_workspace() or self.setup.workspace != self.window.workspace_id:
            self.setup.workspace_settings()
            return
        first_run = not self.window.settings.value(self.prefix + "/setup", False, type=bool)
        self.window.settings.setValue(self.prefix + "/hasCompletedOnboarding", True)
        self.window.settings.setValue(self.prefix + "/setup", True)
        self.window.settings.sync()
        self.accept()
        if not (self.window.connected and self.window.connected.active):
            account.open_dashboard(require_profile=False)
        self.window.raise_()
        self.window.activateWindow()
        self.window.select_tab(0)
        if first_run or goal:
            self.window.getting_started.open(goal=goal)
        from aedrova.desktop.team_invite import open_workspace_join_code

        if not first_run or not open_workspace_join_code(self.window, self.setup.workspace):
            QTimer.singleShot(0, self.window.composer.editor.setFocus)

    def done(self, result):
        if not self.closed:
            self.closed = True
            self.style_hints.colorSchemeChanged.disconnect(self.system_appearance_changed)
            self.setup.stop_workspace_wait()
            self.setup.disconnect_login()
        super().done(result)
