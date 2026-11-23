"""Versioned setup and a short tour that tags the parts of the workspace you will use."""

from dataclasses import dataclass

from PySide6.QtCore import (
    QEvent,
    QPoint,
    QPropertyAnimation,
    QRect,
    QRectF,
    Qt,
    QTimer,
    QVariantAnimation,
)
from PySide6.QtGui import QColor, QKeySequence, QPainter, QPainterPath, QPen, QShortcut
from PySide6.QtWidgets import QFrame, QGraphicsDropShadowEffect, QHBoxLayout, QVBoxLayout, QWidget

from aedrova.desktop import motion
from aedrova.desktop.dialogs import button, label

VERSION = 2


@dataclass(frozen=True)
class Step:
    title: str
    text: str
    target: str  # a window attribute, or "attribute.child"
    tab: int = 0
    side: str = "auto"  # where the tag prefers to sit: right, above, below or left


# Nine stops, one line each. Order follows how a first session actually goes.
STEPS = (
    Step(
        "Your workspaces",
        "Switch teams, or start a new one.",
        "workspace_title",
        side="right",
    ),
    Step(
        "Share your join code",
        "Give teammates a code to join.",
        "invite_teammates_button",
        side="right",
    ),
    Step(
        "Buds",
        "AI teammates with a role. Add your first.",
        "ai_team_section",
        side="right",
    ),
    Step(
        "Channels",
        "One place for each topic. Direct messages sit below.",
        "channel_list",
        side="right",
    ),
    Step(
        "Mention @Aedrova",
        "Say what to build. It reads your chat, files and meetings first.",
        "composer",
        side="above",
    ),
    Step(
        "You set the access",
        "Ask first, approve safe steps, or allow everything.",
        "composer.permissions",
        side="above",
    ),
    Step(
        "Project, Work, Files",
        "Connect a folder, follow builds, find uploads.",
        "primary_navigation",
        side="below",
    ),
    Step(
        "Your AI allowance",
        "What's left for the next 5 hours. Click it for the week.",
        "workspace_usage",
        side="right",
    ),
    Step(
        "Settings and help",
        "Appearance, plan and this tour, any time.",
        "profile_button",
        side="right",
    ),
)
TITLES = tuple(step.title for step in STEPS)


def account_key(window):
    user = window.current_user()
    return f"onboarding/v{VERSION}/" + (str(user.id) if user else "local-preview")


from aedrova.desktop.zen_onboarding import ZenOnboarding as SetupDialog  # noqa: E402, F401


def resolve(window, path):
    """The widget a step points at, or None when it is not on screen."""
    target = window
    for part in path.split("."):
        target = getattr(target, part, None)
        if target is None:
            return None
    visible = getattr(target, "isVisible", None)
    return target if visible and visible() and target.isEnabled() else None


class SpotlightTour(QWidget):
    """Dim the window, light one real control, and tag it with a sentence."""

    def __init__(self, window):
        super().__init__(window.centralWidget())
        self.window = window
        self.prefix = account_key(window)
        self.index = int(window.settings.value(self.prefix + "/step", 0))
        self.index = max(0, min(len(STEPS) - 1, self.index))
        if window.settings.value(self.prefix + "/status") in {"completed", "skipped"}:
            self.index = 0
        self.target_rect = QRect()
        self.hole = QRectF()
        self.saved_tab = window.pages.currentIndex()
        self.glide = QVariantAnimation(self)
        self.glide.setDuration(motion.SLOW)
        self.glide.setEasingCurve(motion.EASE)
        self.glide.valueChanged.connect(self.move_hole)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName("Aedrova tour")
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground)

        self.card = QFrame(self)
        self.card.setObjectName("TourCard")
        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(36)
        shadow.setOffset(0, 10)
        shadow.setColor(QColor(0, 0, 0, 70))
        self.card.setGraphicsEffect(shadow)
        self.card_slide = None
        self.pulse = 0.0
        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(6)
        top = QHBoxLayout()
        from aedrova.desktop.zen_onboarding import StepDots

        self.dots = StepDots(len(STEPS))
        top.addWidget(self.dots)
        self.progress = label("", "section")
        self.progress.hide()  # the dots say it; the words stay for screen readers
        top.addStretch()
        self.skip = button("Skip")
        self.skip.setObjectName("TourSkip")
        self.skip.setCursor(Qt.CursorShape.PointingHandCursor)
        self.skip.clicked.connect(lambda: self.finish("skipped"))
        top.addWidget(self.skip)
        layout.addLayout(top)
        self.heading = label("", "title", wrap=True)
        self.heading.setObjectName("TourHeading")
        self.description = label("", "muted", wrap=True)
        layout.addWidget(self.heading)
        layout.addWidget(self.description)
        layout.addSpacing(6)
        row = QHBoxLayout()
        self.back = button("Back")
        self.back.setObjectName("TourBack")
        self.back.clicked.connect(lambda: self.show_step(self.index - 1, direction=-1))
        self.next = button("Next", role="primary")
        self.next.setObjectName("TourNext")
        self.next.clicked.connect(self.advance)
        row.addWidget(self.back)
        row.addStretch()
        row.addWidget(self.next)
        layout.addLayout(row)
        for key, action in (
            ("Alt+Right", self.advance),
            ("Alt+Left", lambda: self.show_step(self.index - 1, direction=-1)),
            ("Right", self.advance),
            ("Left", lambda: self.show_step(self.index - 1, direction=-1)),
        ):
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(action)
        window.centralWidget().installEventFilter(self)
        self.setGeometry(self.parentWidget().rect())
        self.show_step(self.index)
        self.show()
        self.raise_()
        motion.fade_in(self, motion.SLOW)

    # -- navigation ----------------------------------------------------------------
    def visible_steps(self):
        return [i for i, step in enumerate(STEPS) if resolve(self.window, step.target)]

    def show_step(self, index, *, direction=1):
        index = max(0, min(len(STEPS) - 1, index))
        # Steps whose control is not on screen (no AI allowance yet, a hidden sidebar) are skipped.
        order = range(index, len(STEPS)) if direction > 0 else range(index, -1, -1)
        chosen = None
        for candidate in order:
            self.window.select_tab(STEPS[candidate].tab)
            if resolve(self.window, STEPS[candidate].target):
                chosen = candidate
                break
        index = index if chosen is None else chosen
        self.index = index
        step = STEPS[index]
        shown = self.visible_steps()
        position = shown.index(index) + 1 if index in shown else index + 1
        total = len(shown) or len(STEPS)
        self.progress.setText(f"{position} OF {total}")
        self.dots.count = total
        self.dots.setFixedWidth(total * 14 + 14)
        self.dots.set_current(position - 1)
        self.heading.setText(step.title)
        self.description.setText(step.text)
        self.back.setEnabled(bool(shown) and index != shown[0])
        last = bool(shown) and index == shown[-1]
        self.next.setText("Done" if last else "Next")
        self.window.settings.setValue(self.prefix + "/step", index)
        self.window.settings.setValue(self.prefix + "/status", "paused")
        self.next.setFocus()
        self.layout_for_step(animate=True)
        QTimer.singleShot(0, self.layout_for_step)

    def advance(self):
        shown = self.visible_steps()
        if not shown or self.index >= shown[-1]:
            self.finish("completed")
        else:
            self.show_step(self.index + 1)

    # -- geometry ------------------------------------------------------------------
    def layout_for_step(self, animate=False):
        available = self.parentWidget().rect()
        self.setGeometry(available)
        step = STEPS[self.index]
        target = resolve(self.window, step.target)
        if target is None:
            self.target_rect = QRect()
        else:
            origin = self.parentWidget().mapFromGlobal(target.mapToGlobal(QPoint(0, 0)))
            self.target_rect = QRect(origin, target.size()).intersected(available)
        goal = QRectF()
        if not self.target_rect.isEmpty():
            goal = QRectF(self.target_rect.adjusted(-6, -6, 6, 6))
        self.card.setFixedWidth(min(340, available.width() - 48))
        self.card.adjustSize()
        before = self.card.pos()
        spot = self.tag_position(available, step.side)
        had_card = self.card.isVisible() and before != QPoint(0, 0)
        self.card.raise_()
        if self.card_slide is not None:
            self.card_slide.stop()
        if animate and had_card and not motion.reduced() and before != spot:
            self.card_slide = QPropertyAnimation(self.card, b"pos", self)
            self.card_slide.setDuration(motion.SLOW + 80)
            self.card_slide.setEasingCurve(motion.EASE)
            self.card_slide.setStartValue(before)
            self.card_slide.setEndValue(spot)
            self.card_slide.start()
        else:
            self.card.move(spot)
        if animate and not motion.reduced() and not self.hole.isEmpty() and not goal.isEmpty():
            self.glide.stop()
            self.glide.setStartValue(self.hole)
            self.glide.setEndValue(goal)
            self.glide.start()
        else:
            self.glide.stop()
            self.hole = goal
        if animate:
            motion.fade_in(self.heading, motion.SLOW)
            motion.fade_in(self.description, motion.SLOW)
        self.update()

    def tag_position(self, available, preferred):
        """Put the tag beside the lit control, on the side with room, inside the window."""
        card, gap, margin = self.card.size(), 16, 16
        rect = self.target_rect
        if rect.isEmpty():
            return QPoint(available.width() - card.width() - 28, 28)
        options = {
            "right": QPoint(rect.right() + gap, rect.center().y() - card.height() // 2),
            "left": QPoint(
                rect.left() - gap - card.width(), rect.center().y() - card.height() // 2
            ),
            "above": QPoint(
                rect.center().x() - card.width() // 2, rect.top() - gap - card.height()
            ),
            "below": QPoint(rect.center().x() - card.width() // 2, rect.bottom() + gap),
        }
        order = [preferred] if preferred in options else []
        order += [s for s in ("right", "below", "above", "left") if s not in order]
        bounds = available.adjusted(margin, margin, -margin, -margin)
        for side in order:
            spot = options[side]
            if bounds.contains(QRect(spot, card)):
                return spot
        spot = options[order[0]]
        return QPoint(
            max(bounds.left(), min(spot.x(), bounds.right() - card.width())),
            max(bounds.top(), min(spot.y(), bounds.bottom() - card.height())),
        )

    def move_hole(self, value):
        self.hole = QRectF(value)
        self.update()

    # -- painting ------------------------------------------------------------------
    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        dark = self.window.theme.name == "dark"
        veil = QPainterPath()
        veil.addRect(QRectF(self.rect()))
        if not self.hole.isEmpty():
            veil.addRoundedRect(self.hole, 12, 12)
        veil.setFillRule(Qt.FillRule.OddEvenFill)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 150 if dark else 105))
        painter.drawPath(veil)
        if not self.hole.isEmpty():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for spread, alpha in ((10, 14), (6, 26), (3, 46)):
                glow = QColor("#7C9DFF")
                glow.setAlpha(alpha)
                painter.setPen(QPen(glow, spread))
                painter.drawRoundedRect(self.hole.adjusted(-1, -1, 1, 1), 13, 13)
            ring = QColor("#3D74FF")
            ring.setAlpha(235)
            painter.setPen(QPen(ring, 2))
            painter.drawRoundedRect(self.hole, 12, 12)

    def mousePressEvent(self, event):  # noqa: N802
        event.accept()  # the lit control is for looking; the tag is the only thing to press

    def eventFilter(self, watched, event):  # noqa: N802
        if event.type() in (QEvent.Type.Resize, QEvent.Type.LayoutRequest):
            QTimer.singleShot(0, self.layout_for_step)
        return super().eventFilter(watched, event)

    def finish(self, status):
        self.glide.stop()
        self.window.settings.setValue(self.prefix + "/status", status)
        self.window.settings.sync()
        self.window.select_tab(self.saved_tab)
        self.parentWidget().removeEventFilter(self)
        self.hide()
        self.deleteLater()
        self.window.tour = None
        self.window.composer.editor.setFocus()
