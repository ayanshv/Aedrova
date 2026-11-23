"""First-run setup for the desktop workspace."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from aedrova.desktop import motion
from aedrova.desktop.agent_components import StepIcon
from aedrova.desktop.brand import BrandLockup, BrandMark
from aedrova.desktop.controls import AppDialog
from aedrova.desktop.dialogs import button, label
from aedrova.desktop.icons import icon
from aedrova.desktop.onboarding_art import AuroraSurface, Confetti, StageArt
from aedrova.desktop.onboarding_motion import OnboardingStack
from aedrova.desktop.permission_cards import pending_kinds
from aedrova.desktop.theme import palette
from aedrova.desktop.zen_setup import (
    ACCOUNT,
    GOAL,
    IMPORT,
    OPENING,
    PERMISSIONS,
    PRIVACY,
    PROJECT,
    THEME,
    WELCOME,
    SetupPages,
    heading,
)
from aedrova.desktop.zen_theme import onboarding_styles, resolve_theme


class ReadinessChip(QFrame):
    """What is finishing in the background. It informs; it never blocks the next step."""

    def __init__(self, window, setup):
        super().__init__()
        self.window, self.setup = window, setup
        self.setObjectName("ReadinessChip")
        self.setAccessibleName("Setup in the background")
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 8, 14, 8)
        row.setSpacing(10)
        self.icon = StepIcon("running")
        row.addWidget(self.icon)
        self.text = label("", "muted")
        row.addWidget(self.text)
        self.timer = QTimer(self)
        self.timer.setInterval(1000)  # what is finished changes slowly; check slowly
        self.timer.timeout.connect(self.refresh)
        self.turn = QTimer(self)  # the spinner turns on its own clock so it never stutters
        self.turn.setInterval(30)
        self.turn.timeout.connect(self.spin)
        self.hide()

    def spin(self):
        self.icon.angle = (self.icon.angle + 12) % 360
        self.icon.update()

    def tasks(self):
        tasks = [("Setting up your workspace", self.setup.has_workspace())]
        usage = getattr(self.window, "workspace_usage", None)
        if usage is not None and usage.scope is not None:
            tasks.append(("Turning on AI", usage.data is not None))
        return tasks

    def refresh(self):
        if not self.window.current_user():
            self.hide()
            return
        tasks = self.tasks()
        waiting = [name for name, done in tasks if not done]
        self.show()
        if waiting:
            self.icon.state = "running"
            self.text.setText(waiting[0] + "…  You can keep going.")
            self.timer.start()
            if not motion.reduced() and not self.turn.isActive():
                self.turn.start()
        else:
            self.icon.state = "done"
            self.text.setText("You’re all set.")
            self.timer.stop()
            self.turn.stop()
            QTimer.singleShot(1600, self, self.hide)
        self.icon.update()

    def watch(self):
        self.refresh()
        self.timer.start()

    def hideEvent(self, event):  # noqa: N802
        self.turn.stop()
        super().hideEvent(event)


class StepDots(QWidget):
    """Where you are in setup: small dots, the current one a short pill."""

    def __init__(self, count):
        super().__init__()
        self.count, self.current = count, 0
        self.setFixedHeight(14)
        self.setFixedWidth(count * 14 + 14)
        self.setAccessibleName("Setup progress")

    def set_current(self, index):
        self.current = index
        self.setAccessibleDescription(f"Step {index + 1} of {self.count}")
        self.update()

    def paintEvent(self, event):  # noqa: N802
        from PySide6.QtCore import QRectF
        from PySide6.QtGui import QColor, QPainter, QPalette

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        ink = self.palette().color(QPalette.ColorRole.Text)
        x = 7.0
        for index in range(self.count):
            active = index == self.current
            width = 16.0 if active else 6.0
            color = QColor("#3D74FF") if active else QColor(ink)
            if not active:
                color.setAlpha(70 if index > self.current else 140)
            painter.setBrush(color)
            painter.drawRoundedRect(QRectF(x, 4, width, 6), 3, 3)
            x += width + 8


FEATURES = (
    ("chat", "mention", "Chat with your team and your AI Buds.", "#8275E6", "#C9B6FF"),
    ("build", "terminal", "Mention @Aedrova to plan and build.", "#3D74FF", "#7DB4FF"),
    ("people", "people", "Bring your history over from Slack.", "#E5589F", "#FFB5DA"),
    ("work", "folder", "Keep projects, files and meetings together.", "#E8923A", "#FFD3B3"),
)


def feature_tile(symbol, start, end):
    """A small gradient tile with a white glyph, drawn once."""
    size = 26
    pixmap = QPixmap(size * 2, size * 2)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    gradient = QLinearGradient(0, 0, size * 2, size * 2)
    gradient.setColorAt(0.0, QColor(end))
    gradient.setColorAt(1.0, QColor(start))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(gradient)
    painter.drawRoundedRect(0, 0, size * 2, size * 2, 14, 14)
    icon(symbol, "#FFFFFF").paint(painter, 12, 12, size * 2 - 24, size * 2 - 24)
    painter.end()
    pixmap.setDevicePixelRatio(2)
    return pixmap


class FeatureRow(QFrame):
    def __init__(self, symbol, text, start, end):
        super().__init__()
        self.setObjectName("FeatureRow")
        row = QHBoxLayout(self)
        row.setContentsMargins(10, 9, 14, 9)
        row.setSpacing(12)
        tile = QLabel()
        tile.setFixedSize(26, 26)
        tile.setPixmap(feature_tile(symbol, start, end))
        row.addWidget(tile)
        row.addWidget(label(text, wrap=True), 1)

    def set_active(self, active):
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)


class ZenOnboarding(AppDialog):
    def __init__(self, window):
        super().__init__(window)
        from aedrova.desktop.onboarding import account_key

        self.window = window
        user = window.current_user()
        self.prefix = account_key(window)
        self.owner = str(user.id) if user else None
        self.review_profile = getattr(window, "review_onboarding_profile", False)
        self.profile_reviewed = False
        self.created_workspace = None
        self.workspace_selected = False
        self.closed = False
        self.celebrated = False
        self.reduced_motion = window.reduced_motion
        self.appear_ms = 700  # the first thing a person sees should arrive, not pop
        self.setWindowTitle("Aedrova · Welcome")
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumSize(780, 540)
        self.resize(900, 600)

        # Theme first: the art and the colour wash read it while they are built.
        # A first run opens light, whatever the system or an earlier install said; the theme step
        # is where someone chooses otherwise. Reviewing setup later keeps their own choice.
        self.theme_mode = "light" if self.shows_theme() else window.theme_mode
        self.theme = resolve_theme(self.theme_mode)
        self.setPalette(palette(self.theme))

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        surface = AuroraSurface()
        self.surface = surface
        outer.addWidget(surface, 10)
        self.art = StageArt(self)
        outer.addWidget(self.art, 9)

        shell = QHBoxLayout(surface)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.addStretch(1)
        panel = QWidget()
        panel.setMaximumWidth(580)
        shell.addWidget(panel, 100)
        shell.addStretch(1)
        left = QVBoxLayout(panel)
        left.setContentsMargins(44, 30, 36, 26)
        left.setSpacing(0)
        self.top = QWidget()
        top = QHBoxLayout(self.top)
        top.setContentsMargins(0, 0, 0, 0)
        self.brand = BrandLockup(24, 15)
        top.addWidget(self.brand)
        top.addStretch()
        self.dots = StepDots(8)
        top.addWidget(self.dots)
        left.addWidget(self.top)
        self.top_gap = QSpacerItem(0, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        left.addItem(self.top_gap)

        scroll = QScrollArea()
        scroll.setObjectName("ZenSettings")
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.viewport().setAutoFillBackground(False)
        self.scroll = scroll
        left.addWidget(scroll, 1)
        self.content = QWidget()
        self.content.setAutoFillBackground(False)
        scroll.setWidget(self.content)
        column = QVBoxLayout(self.content)
        column.setContentsMargins(0, 0, 10, 8)
        column.setSpacing(14)

        self.pages = OnboardingStack(self)
        self.pages.reduced = lambda: True  # the screen change below does its own, richer motion
        intro = QWidget()
        welcome = QVBoxLayout(intro)
        welcome.setContentsMargins(0, 0, 0, 0)
        welcome.setSpacing(8)
        title = heading("Welcome to Aedrova")
        subtitle = label(
            "Set up your workspace for chat, Buds and building together.", "muted", wrap=True
        )
        welcome.addWidget(title)
        welcome.addWidget(subtitle)
        welcome.addSpacing(16)
        self.feature_rows = []
        for _, symbol, text, start, end in FEATURES:
            row = FeatureRow(symbol, text, start, end)
            welcome.addWidget(row)
            self.feature_rows.append(row)
        welcome.addStretch()
        self.welcome_pieces = (title, subtitle, *self.feature_rows)
        self.highlight = 0
        self.feature_rows[0].set_active(True)
        self.pages.addWidget(intro)
        self.setup = SetupPages(self)
        self.pages.addWidget(self.setup)
        self.pages.addWidget(self.build_opener())
        column.addWidget(self.pages)
        column.addStretch()
        self.column = column

        self.readiness = ReadinessChip(window, self.setup)
        left.addSpacing(8)
        left.addWidget(self.readiness, alignment=Qt.AlignmentFlag.AlignLeft)
        left.addSpacing(10)
        self.actions = QWidget()
        actions = QHBoxLayout(self.actions)
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(10)
        self.back = button("Back")
        self.back.setObjectName("OnboardingBack")
        self.back.clicked.connect(self.go_back)
        actions.addWidget(self.back)
        actions.addStretch()
        self.skip = button("Set up later")
        self.skip.setObjectName("OnboardingBack")
        self.skip.clicked.connect(self.skip_step)
        actions.addWidget(self.skip)
        self.primary = button("Get started", role="primary")
        self.primary.setObjectName("OnboardingContinue")
        self.primary.setProperty("onboardingAction", True)
        self.primary.setMinimumHeight(38)
        self.primary.setMinimumWidth(110)
        self.primary.setDefault(True)
        self.primary.clicked.connect(self.activate)
        actions.addWidget(self.primary)
        left.addWidget(self.actions)

        self.cycle = QTimer(self)
        self.cycle.setInterval(2200)
        self.cycle.timeout.connect(self.next_highlight)
        self.apply_appearance(self.theme_mode)
        self.style_hints = QApplication.instance().styleHints()
        self.style_hints.colorSchemeChanged.connect(self.system_appearance_changed)
        self.show_stage(OPENING if self.shows_theme() else WELCOME)

    def cover_screen(self):
        """Fill the screen without macOS's full-screen Space, so file pickers and other windows
        open on top of setup and focus never wanders off to another desktop."""
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        screen = self.window.screen() or QApplication.primaryScreen()
        self.setGeometry(screen.geometry())
        self.appear_rise = 0
        self.covering = True

    def leave_cover(self):
        """Escape steps out of the full-screen cover into an ordinary window. It never cancels."""
        if not getattr(self, "covering", False):
            return
        self.covering = False
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, False)
        screen = (self.window.screen() or QApplication.primaryScreen()).availableGeometry()
        width, height = min(980, screen.width() - 120), min(680, screen.height() - 120)
        self.setGeometry(
            screen.x() + (screen.width() - width) // 2,
            screen.y() + (screen.height() - height) // 2,
            width,
            height,
        )
        self.show()

    def keyPressEvent(self, event):  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            event.accept()  # setup is never abandoned by a stray Escape
            self.leave_cover()
            return
        super().keyPressEvent(event)

    def regain_focus(self):
        self.raise_()
        self.activateWindow()
        if not self.primary.isHidden():
            self.primary.setFocus()

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        # On a big display the title sits a little lower instead of hugging the top edge.
        self.top_gap.changeSize(
            0,
            30 + max(0, int((self.height() - 620) * 0.14)),
            QSizePolicy.Policy.Minimum,
            QSizePolicy.Policy.Fixed,
        )
        self.surface.layout().invalidate()

    def build_opener(self):
        """The first screen: the mark, one sentence, one button. Nothing else."""
        page = QWidget()
        stack = QVBoxLayout(page)
        stack.setContentsMargins(0, 0, 0, 0)
        stack.setSpacing(10)
        stack.addStretch(2)
        self.opener_mark = BrandMark(72)
        stack.addWidget(self.opener_mark, alignment=Qt.AlignmentFlag.AlignHCenter)
        stack.addSpacing(22)
        self.opener_title = label("Your team, plus Agents.", "display", wrap=True)
        self.opener_title.setObjectName("ZenOpening")
        self.opener_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stack.addWidget(self.opener_title)
        self.opener_text = label("Chat, plan and build together.", "muted", wrap=True)
        self.opener_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stack.addWidget(self.opener_text)
        stack.addSpacing(26)
        self.begin = button("Get started", role="primary")
        self.begin.setObjectName("OnboardingContinue")
        self.begin.setMinimumHeight(44)
        self.begin.setFixedWidth(200)
        self.begin.clicked.connect(self.activate)
        stack.addWidget(self.begin, alignment=Qt.AlignmentFlag.AlignHCenter)
        stack.addStretch(3)
        self.opening_pieces = (self.opener_mark, self.opener_title, self.opener_text, self.begin)
        return page

    def next_highlight(self):
        if self.stage != WELCOME or not self.isVisible():
            return
        self.feature_rows[self.highlight].set_active(False)
        self.highlight = (self.highlight + 1) % len(self.feature_rows)
        self.feature_rows[self.highlight].set_active(True)

    def apply_appearance(self, mode):
        self.theme_mode = mode
        self.theme = resolve_theme(mode)
        self.setPalette(palette(self.theme))
        self.setStyleSheet(onboarding_styles(self.theme))
        if hasattr(self, "art"):
            self.art.update()
            self.surface.update()

    def system_appearance_changed(self, *_):
        if self.theme_mode == "system":
            self.apply_appearance("system")

    ORDER = (WELCOME, ACCOUNT, PRIVACY, THEME, PERMISSIONS, PROJECT, IMPORT, GOAL)
    ORDER_INDEX = {
        OPENING: -1,
        WELCOME: 0,
        ACCOUNT: 1,
        PRIVACY: 2,
        THEME: 3,
        PERMISSIONS: 4,
        PROJECT: 5,
        IMPORT: 6,
        GOAL: 7,
    }
    SCENES = {
        WELCOME: "welcome",
        ACCOUNT: "account",
        PRIVACY: "privacy",
        THEME: "theme",
        PERMISSIONS: "permissions",
        PROJECT: "project",
        IMPORT: "import",
        GOAL: "goal",
    }

    def slide_out(self, forward):
        """The screen you are leaving glides away and fades, as the next one arrives."""
        if motion.reduced() or not self.isVisible():
            return
        from PySide6.QtCore import QParallelAnimationGroup, QPoint, QPropertyAnimation
        from PySide6.QtWidgets import QGraphicsOpacityEffect

        area = self.scroll.viewport()
        ghost = QLabel(area)
        ghost.setPixmap(area.grab())
        ghost.setGeometry(area.rect())
        ghost.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        effect = QGraphicsOpacityEffect(ghost)
        ghost.setGraphicsEffect(effect)
        ghost.show()
        ghost.raise_()
        group = QParallelAnimationGroup(ghost)
        fade = QPropertyAnimation(effect, b"opacity", ghost)
        fade.setStartValue(1.0)
        fade.setEndValue(0.0)
        slide = QPropertyAnimation(ghost, b"pos", ghost)
        slide.setStartValue(QPoint(0, 0))
        slide.setEndValue(QPoint(-44 if forward else 44, 0))
        for part in (fade, slide):
            part.setDuration(motion.SLOW)
            part.setEasingCurve(motion.EASE)
            group.addAnimation(part)
        group.finished.connect(ghost.deleteLater)
        group.start()
        self.ghost = ghost

    def show_stage(self, stage):
        previous = getattr(self, "stage", None)
        forward = previous is None or self.ORDER_INDEX.get(stage, -1) >= self.ORDER_INDEX.get(
            previous, -1
        )
        if previous is not None and previous != stage:
            self.slide_out(forward)
        self.stage = stage
        opening = stage == OPENING
        self.top.setVisible(not opening)
        self.art.setVisible(not opening)
        self.surface.opening = opening
        self.back.setVisible(stage not in (WELCOME, OPENING))
        self.back.setEnabled(True)
        self.skip.setVisible(stage in (GOAL, PROJECT, IMPORT))
        self.skip.setText("Skip for now" if stage in (GOAL, IMPORT) else "Set up later")
        self.primary.setVisible(
            stage not in (GOAL, OPENING, IMPORT)
            and (stage != ACCOUNT or self.window.current_user() is not None)
        )
        self.primary.setEnabled(True)
        labels = {
            WELCOME: "Get started",
            PROJECT: "Connect project" if self.created_workspace else "Open workspace",
        }
        self.primary.setText(labels.get(stage, "Continue"))
        self.primary.setAccessibleName(self.primary.text())
        if stage not in (WELCOME, OPENING):
            self.setup.render(stage)
        self.actions.setVisible(
            any(not control.isHidden() for control in (self.back, self.skip, self.primary))
        )
        page_index = {WELCOME: 0, OPENING: 2}.get(stage, 1)
        for index in range(self.pages.count()):
            self.pages.widget(index).setSizePolicy(
                QSizePolicy.Policy.Expanding,
                (
                    QSizePolicy.Policy.Expanding
                    if index == page_index and opening
                    else QSizePolicy.Policy.Preferred
                    if index == page_index
                    else QSizePolicy.Policy.Ignored
                ),
            )
        self.column.setStretch(0, 1 if opening else 0)
        self.pages.setCurrentIndex(page_index)
        self.pages.updateGeometry()
        self.content.updateGeometry()
        if not self.primary.isHidden():
            self.primary.setFocus()
        elif self.setup.first_action is not None:
            self.setup.first_action.setFocus()
        position = self.ORDER.index(stage) if stage in self.ORDER else 0
        self.dots.set_current(position)
        self.surface.set_active(True)
        self.surface.set_stage(position)
        if stage != OPENING:
            self.art.show_scene(self.SCENES[stage], forward)
        if stage == WELCOME and not motion.reduced():
            self.cycle.start()
        else:
            self.cycle.stop()
        if stage != WELCOME and self.window.current_user():
            self.readiness.watch()
        if stage == GOAL and not self.celebrated and self.isVisible():
            self.celebrated = True
            if not motion.reduced():
                Confetti(self)
        self.reveal_stage()

    def reveal_stage(self):
        """Each screen arrives piece by piece, like a sentence being said."""
        from aedrova.desktop.motion import reveal

        if not self.isVisible():
            return
        if self.stage == OPENING:
            pieces = list(self.opening_pieces)
        elif self.stage == WELCOME:
            pieces = list(self.welcome_pieces)
        else:
            pieces = [
                self.setup.column.itemAt(i).widget()
                for i in range(self.setup.column.count())
                if self.setup.column.itemAt(i).widget() is not None
            ]
        pieces.extend(c for c in (self.actions,) if not self.actions.isHidden())
        reveal(pieces, step={OPENING: 170, WELCOME: 110}.get(self.stage, 70), delay=150)

    def shows_theme(self):
        """The appearance choice is part of first-run setup, not of reviewing it later."""
        return not self.window.settings.value(self.prefix + "/setup", False, type=bool)

    def next_after_privacy(self):
        if self.shows_theme():
            return THEME
        return self.next_after_theme()

    def next_after_theme(self):
        if pending_kinds():
            return PERMISSIONS
        return GOAL if not self.setup.needs_workspace() else PROJECT

    def choose_theme(self, mode):
        self.window.set_theme(mode)
        self.apply_appearance(mode)
        self.art.set_preview(mode)

    def permissions_changed(self):
        rows = self.setup.permissions.rows
        self.art.set_granted([kind for kind, row in rows.items() if row.state == "granted"])

    def go_back(self):
        earlier = THEME if self.shows_theme() else PRIVACY
        if self.stage == PERMISSIONS:
            previous = earlier
        elif self.stage == PROJECT:
            previous = PERMISSIONS if pending_kinds() else earlier
        else:
            previous = {ACCOUNT: WELCOME, PRIVACY: ACCOUNT, THEME: PRIVACY, GOAL: PRIVACY}.get(
                self.stage, WELCOME
            )
        self.show_stage(previous)

    def choose_goal(self, goal):
        self.finish(goal=goal)

    def after_project(self):
        """A new workspace offers its owner the optional Slack import before the first task."""
        return IMPORT if self.setup.can_import_history() else GOAL

    def skip_step(self):
        if self.stage == IMPORT:
            self.show_stage(GOAL)
        elif (
            self.stage == PROJECT
            and self.created_workspace
            and self.created_workspace == self.setup.workspace
        ):
            self.show_stage(self.after_project())
        else:
            self.finish()

    def activate(self):
        from aedrova.desktop.onboarding import account_key

        if account_key(self.window) != self.prefix:
            self.reject()
        elif self.stage == OPENING:
            self.show_stage(WELCOME)
        elif self.stage == WELCOME:
            self.show_stage(PRIVACY if self.profile_complete() else ACCOUNT)
        elif self.stage == ACCOUNT:
            self.setup.advance_profile()
        elif self.stage == PRIVACY:
            self.show_stage(self.next_after_privacy())
        elif self.stage == THEME:
            self.show_stage(self.next_after_theme())
        elif self.stage == PERMISSIONS:
            self.show_stage(GOAL if not self.setup.needs_workspace() else PROJECT)
        elif self.stage == IMPORT:
            self.show_stage(GOAL)
        elif self.setup.save():
            self.skip_step()

    def profile_complete(self):
        account = getattr(self.window, "account_dialog", None)
        profile = account.snapshot.get("user_profile") if account else None
        return bool(
            self.window.current_user()
            and isinstance(profile, dict)
            and (
                self.profile_reviewed
                or (profile.get("profile_completed") and not self.review_profile)
            )
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
        if first_run:
            self.window.showFullScreen()  # setup ends with the workspace filling the screen
        else:
            self.window.show()
        self.window.raise_()
        self.window.activateWindow()
        self.window.select_tab(0)
        if first_run or goal:
            self.window.getting_started.open(goal=goal)
        from aedrova.desktop.team_invite import open_workspace_join_code

        invited = first_run and open_workspace_join_code(self.window, self.setup.workspace)
        if not invited:
            QTimer.singleShot(0, self.window.composer.editor.setFocus)
        if first_run:
            # Once setup has closed and the workspace is in view, tag what is where. Owners also
            # get an invite window; the tour waits for it rather than being skipped.
            QTimer.singleShot(1200, self.window, self.window.start_first_tour)

    def done(self, result):
        if not self.closed:
            self.closed = True
            if result == 0 and not self.window.isVisible():
                self.window.show()  # setup was cancelled: do not leave the app with no window
            self.style_hints.colorSchemeChanged.disconnect(self.system_appearance_changed)
            self.setup.stop_workspace_wait()
            self.setup.disconnect_login()
            if getattr(self.setup, "import_panel", None) is not None:
                self.setup.import_panel.stop()
        super().done(result)
