"""Animated introduction followed by explicit, optional real configuration."""

import math
import time

from PySide6.QtCore import QEvent, QRectF, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen, QPixmap, QRadialGradient
from PySide6.QtWidgets import QApplication, QPushButton, QWidget

from aedrova.desktop.brand import brand_image
from aedrova.desktop.controls import AppDialog
from aedrova.desktop.materials import system_font
from aedrova.desktop.theme import palette
from aedrova.desktop.zen_setup import LAST_STAGE, SETUP_STEPS, SetupPages
from aedrova.desktop.zen_theme import onboarding_styles, resolve_theme, tone

PROCESSING_SECONDS = 2.5


def settled_spring(seconds, frequency=11):
    """Exact critically damped step response: heavy, smooth, and no overshoot."""
    return 1 - (1 + frequency * seconds) * math.exp(-frequency * seconds)


def processing_progress(seconds):
    return min(1.0, max(0.0, seconds / PROCESSING_SECONDS) ** 1.65)


class ZenCanvas(QWidget):
    def __init__(self, flow):
        super().__init__(flow)
        self.flow = flow
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAccessibleName("Aedrova interactive product preview")

    def paintEvent(self, event):  # noqa: N802
        f = self.flow
        theme = f.theme
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(self.rect(), QColor(theme.bg))
        x, y = w / 2, h / 2
        elapsed = f.now() - f.entered
        pulse = 0.5 if f.reduced else (1 + math.sin(elapsed * 2.4)) / 2
        glow = QRadialGradient(x, y, min(w, h) * 0.62)
        glow.setColorAt(0, QColor(68, 149, 236, int(18 + pulse * 9)))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        p.fillRect(self.rect(), glow)
        # Enter each scene through a critically damped lift, rather than moving Qt layouts.
        lift = 0 if f.reduced else 22 * (1 - settled_spring(elapsed))
        p.translate(0, lift)
        title_size = 48 if w >= 800 else 36

        def text(rect, value, size=15, color=None, weight=QFont.Weight.Normal):
            font = system_font(size, weight, -1.1 if size >= 30 else 0)
            flags = Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap
            while (
                font.pixelSize() > 10
                and QFontMetrics(font).boundingRect(rect.toRect(), flags, value).height()
                > rect.height()
            ):
                font.setPixelSize(font.pixelSize() - 1)
            p.setFont(font)
            p.setPen(QColor(theme.text if color is None else tone(theme, color)))
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, value)

        def panel(rect, fill=theme.bg, border=theme.border, radius=24):
            p.setPen(QPen(QColor(tone(theme, border)), 1))
            p.setBrush(QColor(tone(theme, fill)))
            p.drawRoundedRect(rect, radius, radius)

        titles = (
            (
                "A spark. A shared workspace.",
                "Your team's context. Put to work.",
                "From conversation to clarity.",
                "Find your rhythm.",
            )
            + tuple(step[0] for step in SETUP_STEPS)
            + ("Make something together.",)
        )
        subtitles = (
            (
                "Aedrova · Where teams and AI build together",
                "One mention turns a shared decision into a build.",
                "An illustrated journey through accessible team context.",
                "Try the shortcut you'll use to jump to a conversation.",
            )
            + tuple(step[1] for step in SETUP_STEPS)
            + ("Your workspace is ready to explore.",)
        )
        text(
            QRectF(36, 44, w - 72, 24),
            f"AEDROVA  /  {f.stage + 1:02d} OF {LAST_STAGE + 1}",
            11,
            theme.muted,
        )
        text(QRectF(32, 90, w - 64, 90), titles[f.stage], title_size, weight=QFont.Weight.DemiBold)
        text(QRectF(44, 180, w - 88, 48), subtitles[f.stage], 15, theme.secondary)
        area = QRectF(max(32, x - 310), 250, min(620, w - 64), max(180, h - 410))
        cy = area.center().y()
        if f.stage == 0:
            p.save()
            scale = f.button_scale
            p.translate(x, cy)
            p.scale(scale, scale)
            halo = QRadialGradient(0, 0, 125)
            halo.setColorAt(0, QColor(69, 144, 228, 85))
            halo.setColorAt(1, QColor(69, 144, 228, 0))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(halo)
            p.drawEllipse(QRectF(-125, -125, 250, 250))
            panel(QRectF(-48, -48, 96, 96), "#FFFFFF", "#C6DEF6", 30)
            if f.logo.isNull():
                text(QRectF(-44, -44, 88, 88), "A", 48, "#176CCD", QFont.Weight.Medium)
            else:
                p.drawPixmap(QRectF(-38, -38, 76, 76).toRect(), f.logo)
            p.restore()
            if not f.reduced:
                for i, color in enumerate(("#589ADE", "#8A75D8", "#A99AE0")):
                    angle = elapsed * 0.7 + i * math.tau / 3
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(QColor(tone(theme, color)))
                    p.drawEllipse(
                        QRectF(x + math.cos(angle) * 110 - 3, cy + math.sin(angle) * 110 - 3, 6, 6)
                    )
        elif f.stage == 1:
            panel(area)
            text(
                QRectF(area.left() + 20, area.top() + 16, area.width() - 40, 32),
                "# product  ·  Demo workspace",
                13,
                theme.secondary,
            )
            rows = (
                ("Team", "We agreed on the next feature."),
                ("Design", "Keep the interface simple."),
                ("Engineering", "Build on our existing project."),
            )
            count = 3 if area.height() >= 340 else 2 if area.height() >= 270 else 1
            for index, (author, message) in enumerate(rows[:count]):
                top = area.top() + 68 + index * 66
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor(tone(theme, "#E2EFFF")))
                p.drawEllipse(QRectF(area.left() + 24, top + 5, 34, 34))
                text(QRectF(area.left() + 24, top + 5, 34, 34), author[0], 15, "#176CCD")
                panel(
                    QRectF(area.left() + 70, top, area.width() - 94, 54), "#F7FAFE", "#E2ECF6", 14
                )
                text(
                    QRectF(area.left() + 80, top + 2, area.width() - 114, 48),
                    author + " · " + message,
                    14,
                )
            if area.height() >= 340:
                text(
                    QRectF(area.left() + 24, area.bottom() - 140, area.width() - 48, 30),
                    "Conversations  ·  Files  ·  Decisions",
                    13,
                    "#4D7198",
                )
            panel(
                QRectF(area.left() + 24, area.bottom() - 92, area.width() - 48, 66),
                "#F5F5F7",
                "#DAE7F5",
                18,
            )
            value = (
                f"{f.agent}  ·  Preview complete ✓"
                if f.success
                else f"@{f.agent}, build our agreed feature"
            )
            text(
                QRectF(area.left() + 36, area.bottom() - 82, area.width() - 72, 44),
                value,
                15,
                "#176CCD",
            )
            if f.success and not f.reduced:
                t = min(1, (f.now() - f.action_started) / 0.95)
                p.setPen(Qt.PenStyle.NoPen)
                for i in range(28):
                    angle = i * math.tau / 28
                    r = 35 + 180 * settled_spring(t, 6)
                    p.setBrush(QColor(67, 150, 234, int(220 * (1 - t))))
                    p.drawEllipse(
                        QRectF(x + math.cos(angle) * r - 3, cy + math.sin(angle) * r - 3, 6, 6)
                    )
        elif f.stage == 2:
            panel(QRectF(x - 50, area.top(), 100, 100), "#EFF6FF", "#CAE1F8", 32)
            text(QRectF(x - 48, area.top() + 4, 96, 88), "◇", 44, "#1877DB")
            if area.height() >= 290:
                for i, name in enumerate(("Chats", "Files", "Decisions")):
                    nx = x - 180 + i * 180
                    p.setPen(QPen(QColor(tone(theme, "#BDD8F3")), 1))
                    p.drawLine(nx, area.top() + 70, x, area.top() + 50)
                    panel(QRectF(nx - 52, area.top() + 95, 104, 38), "#F4F9FF", "#D7E7F7", 13)
                    text(QRectF(nx - 50, area.top() + 96, 100, 36), name, 13, "#2367A7")
            messages = (
                "Reading conversations…",
                "Connecting decisions…",
                "Indexing shared files…",
                "Tracing project context…",
                "Preparing a build brief…",
                "Preview complete.",
            )
            index = min(5, int(f.processing * 6))
            for i in range(max(0, index - 2), index + 1):
                text(
                    QRectF(
                        area.left(),
                        area.top()
                        + (155 if area.height() >= 290 else 112)
                        + (i - max(0, index - 2)) * 25,
                        area.width(),
                        24,
                    ),
                    messages[i],
                    12,
                    None if i == index else theme.muted,
                )
            bar = QRectF(area.left() + 30, area.bottom() - 32, area.width() - 60, 6)
            panel(bar, "#E8E8EB", "#E8E8EB", 3)
            if f.processing > 0:
                panel(
                    QRectF(bar.left(), bar.top(), bar.width() * f.processing, 6),
                    "#368BE8",
                    "#368BE8",
                    3,
                )
        elif f.stage == 3:
            for i, (key, on) in enumerate(
                (("⌘ / Ctrl", f.command_down or f.unlocked), ("K", f.k_down or f.unlocked))
            ):
                rect = QRectF(x - 154 + i * 166, cy - 62, 142, 124)
                panel(rect, "#EAF3FF" if on else theme.bg, "#4092E7" if on else "#DAE7F5", 24)
                text(rect, key, 25, "#175FAD")
            text(
                QRectF(area.left(), cy + 70, area.width(), 32),
                "Access granted" if f.unlocked else "⌘ K on Mac  ·  Ctrl K elsewhere",
                17,
                "#176CCD" if f.unlocked else theme.secondary,
            )
        elif f.stage == LAST_STAGE:
            # The two panels part to reveal the actual dashboard behind this dialog.
            t = 1 if f.reduced else settled_spring(elapsed, 5)
            p.setOpacity(1 - t * 0.6)
            panel(QRectF(x - 150 - t * 240, cy - 75, 140, 150), "#F0F7FF", "#DCE9F6")
            panel(QRectF(x + 10 + t * 240, cy - 75, 140, 150), "#F0F7FF", "#DCE9F6")
            p.setOpacity(1)
            text(QRectF(x - 100, cy - 50, 200, 100), "Aedrova", 28, "#176CCD", QFont.Weight.Medium)
        for index in range(LAST_STAGE + 1):
            dot = QRectF(x - (LAST_STAGE * 7) + index * 14 - 3, h - 76, 6, 6)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor("#368BE8" if index <= f.stage else "#DDE7F3"))
            p.drawEllipse(dot)
        text(
            QRectF(40, h - 55, w - 80, 22),
            "Interactive preview · Nothing runs or changes"
            if f.stage < 4
            else "Your choices. Your control. · No build, call or push starts during setup",
            10,
            theme.muted,
        )
        if f.flash_started is not None and not f.reduced:
            t = min(1, (f.now() - f.flash_started) / 0.42)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(150, 205, 255, int(130 * (1 - t))))
            radius = max(w, h) * settled_spring(t, 7)
            p.drawEllipse(QRectF(x - radius, cy - radius, radius * 2, radius * 2))
        p.end()


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
        self.resize(960, 850)
        self.setMinimumSize(640, 620)
        self.theme_mode = window.theme_mode
        self.theme = resolve_theme(self.theme_mode)
        self.apply_appearance(self.theme_mode)
        self.canvas = ZenCanvas(self)
        self.primary = QPushButton("Click to boot  ↵", self)
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
        self.primary.setGeometry(self.width() // 2 - 164, self.height() - 142, 328, 58)
        self.skip.setGeometry(self.width() - 164, 24, 148, 40)
        self.back.setGeometry(20, 24, 128, 40)
        self.layout_setup()

    def show_stage(self, stage):
        self.stage = stage
        self.entered = self.now()
        self.action_started = None
        actions = (
            "Click to begin  ↵",
            "Send the demo mention",
            "Mapping demo context…",
            "Click to unlock",
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
            max(32, self.width() // 2 - 310),
            240 + lift,
            min(620, self.width() - 64),
            max(170, self.height() - 410),
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
        width = int(328 * self.button_scale)
        height = int(58 * self.button_scale)
        self.primary.setGeometry(
            (self.width() - width) // 2, self.height() - 113 - height // 2, width, height
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
