"""Animated introduction followed by explicit, optional real configuration."""

import math
import time

from PySide6.QtCore import QEvent, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QPushButton, QWidget

from aedrova.desktop.brand import brand_image
from aedrova.desktop.controls import AppDialog
from aedrova.desktop.materials import system_font
from aedrova.desktop.theme import palette
from aedrova.desktop.zen_setup import LAST_STAGE, SETUP_STEPS, SetupPages
from aedrova.desktop.zen_theme import onboarding_styles, resolve_theme

PROCESSING_SECONDS = 2.5


def settled_spring(seconds, frequency=11):
    """Exact critically damped step response: heavy, smooth, and no overshoot."""
    return 1 - (1 + frequency * seconds) * math.exp(-frequency * seconds)


def processing_progress(seconds):
    return min(1.0, max(0.0, seconds / PROCESSING_SECONDS) ** 1.65)


class ZenCanvas(QWidget):
    """Reference-led centered composition; the surrounding app remains real."""

    def __init__(self, flow):
        super().__init__(flow)
        self.flow = flow
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAccessibleName("Aedrova welcome and setup")

    def paintEvent(self, event):
        f, w, h = self.flow, self.width(), self.height()
        t = f.theme
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(t.bg))
        elapsed = f.now() - f.entered
        lift = 0 if f.reduced else 10 * (1 - settled_spring(elapsed))
        p.translate(0, lift)

        def text(rect, value, size=14, color=None, weight=QFont.Weight.Normal):
            font = system_font(size, weight, -0.5 if size > 24 else 0)
            p.setFont(font)
            p.setPen(QColor(color or t.text))
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, value)

        titles = (
            (
                "Welcome to Aedrova",
                "Your team. With a builder.",
                "Context, connected.",
                "Meet the command menu",
            )
            + tuple(x[0] for x in SETUP_STEPS)
            + ("You’re ready to make things.",)
        )
        subtitles = (
            (
                "A shared workspace where conversations become working products.",
                "Try one mention. This is a preview; no work runs.",
                "Chats, approved decisions and consented meeting text. One useful brief.",
                "Press ⌘ K to find your next conversation.",
            )
            + tuple(x[1] for x in SETUP_STEPS)
            + ("Your settings are saved. Let’s explore your workspace.",)
        )
        if not f.logo.isNull():
            p.drawPixmap(QRectF(w / 2 - 18, 46, 36, 36).toRect(), f.logo)
        text(QRectF(w / 2 - 100, 86, 200, 24), "Aedrova", 15, weight=QFont.Weight.DemiBold)
        text(QRectF(50, 146, w - 100, 44), titles[f.stage], 28, weight=QFont.Weight.DemiBold)
        text(
            QRectF(w / 2 - min(270, w / 2 - 30), 198, min(540, w - 60), 42),
            subtitles[f.stage],
            13,
            t.secondary,
        )
        area = QRectF(w / 2 - 220, 272, 440, min(230, max(180, h - 410)))
        if 0 < f.stage < 4:
            p.setPen(QPen(QColor(t.border), 1))
            p.setBrush(QColor(t.bg))
            p.drawRoundedRect(area, 10, 10)
        if f.stage == 0 or f.stage == LAST_STAGE:
            from aedrova.desktop.teammate_habitat import paint_orb

            paint_orb(
                p,
                QRectF(w / 2 - 52, area.top() + 30, 104, 104),
                {"color": "#4388F5", "shape": "round"},
                phase=0 if f.reduced else elapsed,
            )
            text(
                QRectF(w / 2 - 190, area.top() + 145, 380, 48),
                "Team context. Real work.\nAll in your workspace.",
                15,
                t.secondary,
            )
        elif f.stage == 1:
            text(
                QRectF(w / 2 - 180, area.top() + 14, 360, 24),
                "# product · Interactive preview",
                12,
                t.muted,
            )
            text(
                QRectF(w / 2 - 184, area.top() + 62, 368, 50),
                "A shared decision\nBuild from the context we already have.",
                15,
            )
            text(
                QRectF(w / 2 - 180, area.top() + 128, 360, 54),
                "Brief ready · sources connected ✓"
                if f.success
                else "@" + f.agent + ", build our agreed feature",
                14,
                t.accent,
            )
        elif f.stage == 2:
            text(QRectF(w / 2 - 160, area.top() + 50, 320, 50), "Organizing the demo context…", 16)
            bar = QRectF(w / 2 - 150, area.top() + 116, 300, 5)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(t.border))
            p.drawRoundedRect(bar, 2.5, 2.5)
            p.setBrush(QColor(t.accent))
            p.drawRoundedRect(QRectF(bar.x(), bar.y(), bar.width() * f.processing, 5), 2.5, 2.5)
            text(
                QRectF(w / 2 - 170, area.top() + 144, 340, 30),
                "Illustrative preview · nothing is indexed",
                11,
                t.muted,
            )
        elif f.stage == 3:
            text(
                QRectF(w / 2 - 150, area.top() + 40, 300, 76),
                "⌘  K",
                44,
                t.accent if f.unlocked else t.text,
                QFont.Weight.Medium,
            )
            text(
                QRectF(w / 2 - 150, area.top() + 140, 300, 36),
                "That was easy." if f.unlocked else "Or click Continue to try it later.",
                13,
                t.secondary,
            )
        for i in range(LAST_STAGE + 1):
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(t.accent if i <= f.stage else t.border))
            p.drawEllipse(QRectF(w / 2 - (LAST_STAGE * 14) / 2 + i * 14 - 2, h - 42, 4, 4))
        text(
            QRectF(w / 2 - 100, h - 30, 200, 18), f"{f.stage + 1} of {LAST_STAGE + 1}", 10, t.muted
        )


class ZenOnboarding(AppDialog):
    """A tactile introduction with explicit configuration; never starts work itself."""

    now = staticmethod(time.monotonic)

    def __init__(self, window):
        super().__init__(window)
        from aedrova.desktop.onboarding import account_key

        self.window = window
        self.prefix = account_key(window)
        self.owner = str(window.current_user().id) if window.current_user() else None
        self.reduced = bool(window.reduced_motion)
        self.stage = 0
        self.entered = self.now()
        self.action_started = None
        self.flash_started = None
        self.success = self.unlocked = False
        self.command_down = self.k_down = False
        self.processing = 0.0
        self.button_scale = 1.0
        self.scale_origin = self.scale_target = 1.0
        self.scale_started = self.now()
        try:
            self.logo = QPixmap.fromImage(brand_image()).scaled(
                128,
                128,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        except (RuntimeError, ValueError):
            self.logo = QPixmap()
        self.finished_once = False
        self.closed = False
        composer = getattr(window, "composer", None)
        self.agent = str(getattr(composer, "agent_name", "Aedrova"))[:32] or "Aedrova"
        self.setWindowTitle("Aedrova · Welcome")
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.resize(1120, 820)
        self.setMinimumSize(640, 620)
        self.theme_mode = window.theme_mode
        self.theme = resolve_theme(self.theme_mode)
        self.apply_appearance(self.theme_mode)
        self.canvas = ZenCanvas(self)
        self.primary = QPushButton("Get started", self)
        self.primary.setObjectName("OnboardingContinue")
        self.primary.setCursor(Qt.CursorShape.PointingHandCursor)
        self.primary.clicked.connect(self.activate)
        self.primary.installEventFilter(self)
        self.skip = QPushButton("Skip intro", self)
        self.skip.setObjectName("ZenSkip")
        self.skip.clicked.connect(self.defer)
        self.back = QPushButton("← Back", self)
        self.back.clicked.connect(lambda: self.setup.go_back())
        self.back.hide()
        self.setup = SetupPages(self)
        self.setup.hide()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        QApplication.instance().installEventFilter(self)
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.setInterval(16)  # ~60 Hz repaint target; actual delivery is OS-dependent.
        self.timer.timeout.connect(self.tick)
        self.finished.connect(self.cleanup)
        QApplication.instance().styleHints().colorSchemeChanged.connect(
            self.system_appearance_changed
        )
        self.timer.start()
        self.show_stage(0)

    def apply_appearance(self, mode):
        self.theme_mode = mode
        self.theme = resolve_theme(mode)
        self.setPalette(palette(self.theme))
        self.setStyleSheet(onboarding_styles(self.theme))
        self.update()
        for widget in self.findChildren(QWidget):
            widget.update()

    def system_appearance_changed(self, *_):
        if not self.closed and self.theme_mode == "system":
            self.apply_appearance("system")

    @property
    def step(self):
        return self.stage

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self.canvas.setGeometry(self.rect())
        self.primary.setGeometry(self.width() // 2 - 200, self.height() - 102, 400, 40)
        self.skip.setGeometry(self.width() - 164, 24, 148, 40)
        self.back.setGeometry(20, 24, 128, 40)
        self.layout_setup()

    def show_stage(self, stage):
        self.stage = stage
        self.entered = self.now()
        self.action_started = None
        actions = (
            "Get started",
            "Send the demo mention",
            "Mapping demo context…",
            "Continue",
        )
        self.primary.setText(
            actions[stage]
            if stage < 4
            else "Opening your workspace…"
            if stage == LAST_STAGE
            else SETUP_STEPS[stage - 4][2]
        )
        self.primary.setAccessibleName(self.primary.text())
        self.primary.setVisible(stage not in (2, LAST_STAGE))
        self.back.setVisible(4 < stage < LAST_STAGE)
        self.back.setEnabled(True)
        self.skip.setEnabled(True)
        self.skip.setText("Set up later" if stage >= 4 else "Skip intro")
        self.skip.setEnabled(stage < 4 or self.profile_complete())
        self.skip.setToolTip("" if self.skip.isEnabled() else "Confirm your account profile first.")
        self.setup.setVisible(4 <= stage < LAST_STAGE)
        if 4 <= stage < LAST_STAGE:
            self.setup.render(stage)
        self.animate_scale(1)
        self.layout_setup()
        self.primary.setEnabled(True)
        if stage == 2:
            self.processing = 0
        self.canvas.setAccessibleName(self.primary.text() + " · Simulated product preview")
        self.primary.setFocus()
        self.canvas.update()

    def layout_setup(self):
        if not hasattr(self, "setup"):
            return
        lift = 0 if self.reduced else int(16 * (1 - settled_spring(self.now() - self.entered)))
        self.setup.setGeometry(
            max(32, self.width() // 2 - 250),
            254 + lift,
            min(500, self.width() - 64),
            max(170, self.height() - 380),
        )

    def activate(self):
        if self.action_started is not None or self.stage in (2, LAST_STAGE):
            return
        if 4 <= self.stage < LAST_STAGE:
            from aedrova.desktop.onboarding import account_key

            if account_key(self.window) != self.prefix:
                self.reject()
                return
            if self.stage == 5:
                self.setup.advance_profile()
                return
            self.setup.capture()
            if self.stage in (6, 7, 8, 10) and not self.setup.valid():
                return
            if self.stage == LAST_STAGE - 1 and not self.setup.save():
                return
            self.show_stage(self.stage + 1)
            return
        self.action_started = self.now()
        self.primary.setEnabled(False)
        if self.stage == 0:
            self.flash_started = self.now()
            self.animate_scale(0.82)
        elif self.stage == 1:
            self.success = True
            self.primary.setText("Context → Build brief → Result  ✓")
        elif self.stage == 3:
            self.unlocked = True
            self.command_down = self.k_down = True
            self.primary.setText("Access granted  ✓")
        self.canvas.update()

    def animate_scale(self, target):
        self.scale_origin = self.button_scale
        self.scale_target = target
        self.scale_started = self.now()

    def tick(self):
        from aedrova.desktop.onboarding import account_key

        if self.owner is not None and account_key(self.window) != self.prefix:
            self.reject()
            return
        elapsed = self.now() - self.entered
        self.button_scale = (
            1
            if self.reduced
            else (
                self.scale_origin
                + (self.scale_target - self.scale_origin)
                * settled_spring(self.now() - self.scale_started)
            )
        )
        width = int(400 * self.button_scale)
        height = int(40 * self.button_scale)
        self.primary.setGeometry(
            (self.width() - width) // 2,
            (min(self.height() - 102, 530) if self.stage < 4 else self.height() - 102),
            width,
            height,
        )
        if self.flash_started is not None and self.now() - self.flash_started >= 0.42:
            self.flash_started = None
        if self.stage == 2:
            self.processing = processing_progress(elapsed)
            if elapsed >= PROCESSING_SECONDS:
                self.show_stage(3)
        elif self.stage == LAST_STAGE and elapsed >= (0.05 if self.reduced else 0.9):
            self.complete()
        elif self.action_started is not None:
            delay = 0.05 if self.reduced else (0.42, 0.95, 0, 0.65, 0)[self.stage]
            if self.now() - self.action_started >= delay:
                self.show_stage(self.stage + 1)
        if self.stage == LAST_STAGE and QApplication.platformName() != "offscreen":
            self.setWindowOpacity(1 - settled_spring(self.now() - self.entered, 5) * 0.9)
        self.layout_setup()
        self.canvas.update()

    def eventFilter(self, obj, event):  # noqa: N802
        if (
            not self.isVisible()
            or not isinstance(obj, QWidget)
            or not (obj is self or self.isAncestorOf(obj))
        ):
            return False
        kind = event.type()
        if obj is self.primary and kind == QEvent.Type.Enter:
            self.animate_scale(0.96)
        if obj is self.primary and kind == QEvent.Type.Leave:
            self.animate_scale(1)
        if obj is self.primary and kind == QEvent.Type.MouseButtonPress:
            self.animate_scale(0.82)
        if obj is self.primary and kind == QEvent.Type.MouseButtonRelease:
            self.animate_scale(1)
        if kind in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease, QEvent.Type.ShortcutOverride):
            if event.isAutoRepeat():
                return False
            key = event.key()
            if kind == QEvent.Type.ShortcutOverride and key in (
                Qt.Key.Key_K,
                Qt.Key.Key_Return,
                Qt.Key.Key_Enter,
            ):
                event.accept()
                return True
            if kind == QEvent.Type.KeyPress and key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if self.stage == 0:
                    self.activate()
                    return True
            if self.stage == 3:
                down = kind == QEvent.Type.KeyPress
                if key in (Qt.Key.Key_Meta, Qt.Key.Key_Control):
                    self.command_down = down
                if key == Qt.Key.Key_K:
                    self.k_down = down
                    self.command_down = bool(
                        event.modifiers()
                        & (Qt.KeyboardModifier.MetaModifier | Qt.KeyboardModifier.ControlModifier)
                    )
                if self.command_down and self.k_down:
                    self.activate()
                self.canvas.update()
                if key in (Qt.Key.Key_Meta, Qt.Key.Key_Control, Qt.Key.Key_K):
                    return True
        return False

    def complete(self):
        from aedrova.desktop.onboarding import account_key

        if self.finished_once:
            return
        # Never mark another account as completed if sign-in changes during the preview.
        if account_key(self.window) != self.prefix:
            self.reject()
            return
        self.finished_once = True
        self.window.settings.setValue(self.prefix + "/hasCompletedOnboarding", True)
        self.window.settings.setValue(self.prefix + "/setup", True)
        self.window.settings.sync()
        self.accept()
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()
        self.window.select_tab(0)
        # Window activation and dialog dismissal settle on the next event-loop turn.
        QTimer.singleShot(0, self.start_controls_tour)

    def start_controls_tour(self):
        from aedrova.desktop.onboarding import account_key

        if account_key(self.window) != self.prefix:
            return
        self.window.settings.setValue(self.prefix + "/step", 0)
        self.window.settings.setValue(self.prefix + "/status", "pending")
        self.window.show_tour()
        self.window.tour.next.setFocus()

    def focus_workspace(self):
        from aedrova.desktop.onboarding import account_key

        if account_key(self.window) != self.prefix:
            return
        composer = getattr(self.window, "composer", None)
        if composer is not None:
            self.window.activateWindow()
            QApplication.setActiveWindow(self.window)
            getattr(composer, "editor", composer).setFocus()

    def profile_complete(self):
        account = getattr(self.window, "account_dialog", None)
        return bool(
            self.window.current_user()
            and account is not None
            and account.snapshot.get("user_profile", {}).get("profile_completed")
        )

    def defer(self):
        if self.stage < 4:
            self.show_stage(4)
            return
        if not self.profile_complete():
            self.show_stage(5)
            self.setup.status.setText("Confirm your account profile before continuing.")
            return
        self.window.settings.setValue(self.prefix + "/deferred", True)
        self.reject()
        self.window.show()
        self.window.activateWindow()

    def cleanup(self, *_):
        if self.closed:
            return
        self.closed = True
        QApplication.instance().styleHints().colorSchemeChanged.disconnect(
            self.system_appearance_changed
        )
        self.timer.stop()
        self.setup.stop_workspace_wait()
        QApplication.instance().removeEventFilter(self)

    def done(self, result):
        self.cleanup()
        super().done(result)

    def closeEvent(self, event):  # noqa: N802
        self.cleanup()
        super().closeEvent(event)
