"""Optional, versioned setup and safe, task-based dashboard spotlights."""

from dataclasses import dataclass

from PySide6.QtCore import (
    QEasingCurve,
    QEvent,
    QPoint,
    QPropertyAnimation,
    QRect,
    Qt,
    QTimer,
    QVariantAnimation,
)
from PySide6.QtGui import QColor, QKeySequence, QPainter, QPainterPath, QPen, QRegion, QShortcut
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from aedrova.desktop.controls import ChoiceBox
from aedrova.desktop.dialogs import button, label

VERSION = 2


@dataclass(frozen=True)
class Step:
    chapter: str
    title: str
    text: str
    target: str
    features: tuple[str, ...]
    tab: int = 0


STEPS = (
    Step(
        "Your team",
        "A place for every team.",
        "Switch teams here. Each workspace keeps its people, conversations and projects "
        "separate. Use + to create another.",
        "workspace_title",
        ("workspaces",),
        0,
    ),
    Step(
        "Your team",
        "Bring your people together.",
        "Invite teammates here. Workspace settings manages members, owner/admin roles and "
        "your agent’s nickname.",
        "invite_teammates_button",
        ("invitations", "roles", "nickname"),
        0,
    ),
    Step(
        "Your team",
        "Give conversations a home.",
        "Pick a channel or use + to create one. Public and private channels have topics, "
        "members and unread activity.",
        "channel_list",
        ("channels", "unread"),
        0,
    ),
    Step(
        "Your team",
        "A quieter conversation.",
        "Start a private conversation with one teammate or a group. "
        "Presence and typing indicators show who’s available and replying.",
        "dm_list",
        ("direct_messages",),
        0,
    ),
    Step(
        "Conversation",
        "Pick up the thread.",
        "Open a message’s replies to keep discussion in a thread. Scroll up for history; "
        "Escape closes the thread.",
        "messages",
        ("messages", "threads", "history"),
        0,
    ),
    Step(
        "Conversation",
        "Find the signal.",
        "Find messages, people, channels and files. ⌘K jumps to a conversation; context "
        "search finds decisions and sources.",
        "search_button",
        ("search", "decisions", "sources"),
        0,
    ),
    Step(
        "Conversation",
        "Keep the work close.",
        "Format text or code, add emoji, and attach or drag files here. "
        "Files keeps shared uploads together. ⌘⇧S saves a selected file.",
        "composer",
        ("attachments", "save_files", "rich_text", "drag_uploads"),
        0,
    ),
    Step(
        "Conversation",
        "Make messages work for you.",
        "Hover or right-click a message to react, reply, quote, edit or unsend. The + "
        "reaction button opens all emojis.",
        "messages",
        ("reactions", "emojis", "editing", "deletion", "quotes"),
        0,
    ),
    Step(
        "Conversation",
        "Keep the important things.",
        "Message actions pin, save, forward, share or copy a message link. Links show "
        "previews when available.",
        "messages",
        ("pins", "bookmarks", "forwarding", "message_links", "sharing_messages", "link_previews"),
        0,
    ),
    Step(
        "Conversation",
        "Stay in the loop.",
        "Activity collects mentions, direct messages and replies. Channel settings control "
        "notifications; unread badges show where to catch up.",
        "button:Activity",
        ("notifications", "activity", "read_state", "typing", "presence"),
        0,
    ),
    Step(
        "Build",
        "Your project, connected.",
        "Connect a local project and choose Codex or Claude Code. Your settings control "
        "planning and execution.",
        "button:Project settings|Connect a project",
        ("project", "provider", "workflow", "permissions"),
        1,
    ),
    Step(
        "Build",
        "Your editor stays yours.",
        "Open the connected project in your preferred editor. Choose VS Code, Cursor, Xcode "
        "or Finder in Settings.",
        "button:Open project in IDE",
        ("ide", "repository"),
        1,
    ),
    Step(
        "Build",
        "From a decision to a build.",
        "Type @ to choose your agent or a teammate. Your agent builds from accessible team "
        "context after your request.",
        "composer",
        ("mentions", "builds", "context"),
        0,
    ),
    Step(
        "Build",
        "Follow the work.",
        "Follow build progress, tools, results and usage here. Stop cancels a run; failed "
        "runs can be recovered.",
        "build_history",
        ("progress", "queue", "recovery", "usage", "cancel", "approvals"),
        0,
    ),
    Step(
        "Build",
        "Review before publishing.",
        "Inspect changes and tests before applying them. Publishing to GitHub always asks "
        "for your approval.",
        "build_history",
        ("review", "apply", "preview", "github"),
        0,
    ),
    Step(
        "Meet",
        "Arrive ready.",
        "Use meeting options to check your microphone, camera, speaker and screen. Checks "
        "stay local and never start a call.",
        "call_bar",
        ("devices", "screen_preview"),
        0,
    ),
    Step(
        "Meet",
        "A familiar room.",
        "The phone starts audio; the camera starts video. In a call, control microphone, "
        "camera, sharing, participants and leaving.",
        "call_bar",
        ("calls", "camera", "microphone", "sharing", "participants", "leave_call"),
        0,
    ),
    Step(
        "Make it yours",
        "Comfort comes first.",
        "Your account menu opens profile and settings. Change appearance, accessibility, "
        "editor preferences and status here.",
        "profile_button",
        ("account", "settings", "appearance", "accessibility", "profile"),
        0,
    ),
    Step(
        "Make it yours",
        "Know your allowance.",
        "Settings shows included AI usage. Plan & billing opens subscription details and "
        "usage allowances on the website.",
        "profile_button",
        ("billing", "allowance"),
        0,
    ),
    Step(
        "Make it yours",
        "You can always come back.",
        "Log out from Account. Help offers updates and these guides again. You can pause or "
        "skip this tour anytime.",
        "profile_button",
        ("logout", "help", "updates"),
        0,
    ),
)
FEATURES = frozenset(feature for step in STEPS for feature in step.features)


def fade(widget, reduced):
    # SpringButton already uses a graphics effect; nested opacity effects hide controls on Qt.
    if reduced:
        return
    position = widget.pos()
    animation = QPropertyAnimation(widget, b"pos", widget)
    animation.setDuration(0 if reduced else 180)
    animation.setStartValue(position + QPoint(0, 8))
    animation.setEndValue(position)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    widget.transition = animation
    animation.start()


def account_key(window):
    user = window.current_user()
    return f"onboarding/v{VERSION}/" + (str(user.id) if user else "local-preview")


# Public import retained for existing Help/first-run integration.
from aedrova.desktop.zen_onboarding import ZenOnboarding as SetupDialog  # noqa: E402, F401


class SpotlightTour(QWidget):
    """A cutout permits real control interaction; the guide never triggers that control."""

    def __init__(self, window):
        super().__init__(window.centralWidget())
        self.window = window
        self.prefix = account_key(window)
        self.index = int(window.settings.value(self.prefix + "/step", 0))
        self.index = max(0, min(len(STEPS) - 1, self.index))
        if window.settings.value(self.prefix + "/status") in {"completed", "skipped"}:
            self.index = 0
        self.reveal = 1.0
        self.highlight_animation = QVariantAnimation(self)
        self.highlight_animation.setDuration(240)
        self.highlight_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.highlight_animation.valueChanged.connect(self.animate_highlight)
        self.target_rect = QRect()
        self.saved_tab = window.pages.currentIndex()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName("Explore Aedrova guided tour")
        self.card = QFrame(self)
        self.card.setObjectName("TourCard")
        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        self.chapters = ChoiceBox()
        self.chapters.setAccessibleName("Tour chapter")
        for chapter in dict.fromkeys(step.chapter for step in STEPS):
            self.chapters.addItem(chapter)
        self.chapters.currentTextChanged.connect(self.chapter)
        layout.addWidget(self.chapters)
        self.progress = label("", "section")
        self.heading = label("", "title", wrap=True)
        self.description = label("", "muted", wrap=True)
        for widget in (self.progress, self.heading, self.description):
            layout.addWidget(widget)
        row = QHBoxLayout()
        self.back = button("Back", role="outline")
        self.back.clicked.connect(lambda: self.show_step(self.index - 1))
        self.next = button("Next", role="primary")
        self.next.clicked.connect(self.advance)
        row.addWidget(self.back)
        row.addStretch()
        row.addWidget(self.next)
        layout.addLayout(row)
        row = QHBoxLayout()
        pause = button("Pause tour", role="outline")
        pause.clicked.connect(lambda: self.finish("paused"))
        skip = button("Skip tour", role="outline")
        skip.clicked.connect(lambda: self.finish("skipped"))
        row.addWidget(pause)
        row.addWidget(skip)
        layout.addLayout(row)
        for key, action in (
            ("Alt+Right", self.advance),
            ("Alt+Left", lambda: self.show_step(self.index - 1)),
        ):
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(action)
        window.centralWidget().installEventFilter(self)
        self.show_step(self.index)
        self.show()
        self.raise_()

    def chapter(self, chapter):
        self.show_step(next(i for i, step in enumerate(STEPS) if step.chapter == chapter))

    def show_step(self, index):
        self.index = max(0, min(len(STEPS) - 1, index))
        step = STEPS[self.index]
        self.chapters.blockSignals(True)
        self.chapters.setCurrentText(step.chapter)
        self.chapters.blockSignals(False)
        self.progress.setText(f"{self.index + 1} OF {len(STEPS)} · ⌥→ NEXT · ESC PAUSE")
        self.heading.setText(step.title)
        self.description.setText(step.text)
        self.back.setEnabled(self.index > 0)
        self.next.setText("Finish" if self.index == len(STEPS) - 1 else "Next")
        self.window.select_tab(step.tab)
        self.window.settings.setValue(self.prefix + "/step", self.index)
        self.window.settings.setValue(self.prefix + "/status", "paused")
        self.next.setFocus()
        self.reposition()
        fade(self.card, self.window.reduced_motion)
        self.highlight_animation.stop()
        if self.window.reduced_motion:
            self.reveal = 1.0
        else:
            self.highlight_animation.setStartValue(0.0)
            self.highlight_animation.setEndValue(1.0)
            self.highlight_animation.start()
        QTimer.singleShot(0, self.reposition)

    def animate_highlight(self, value):
        self.reveal = float(value)
        self.update()

    def advance(self):
        if self.index == len(STEPS) - 1:
            self.finish("completed")
        else:
            self.show_step(self.index + 1)

    def reposition(self):
        self.setGeometry(self.parentWidget().rect())
        dark = self.window.theme.name == "dark"
        self.card.setStyleSheet(
            "QFrame#TourCard {background:"
            + ("#1C1C1E" if dark else "#FFFFFF")
            + ";border:1px solid "
            + ("#38383A" if dark else "#E5E5E7")
            + ";border-radius:24px;}"
        )
        target = getattr(self.window, STEPS[self.index].target, None)
        if STEPS[self.index].target.startswith("button:"):
            names = STEPS[self.index].target.removeprefix("button:").split("|")
            target = next(
                (
                    control
                    for control in self.window.pages.currentWidget().findChildren(QPushButton)
                    if control.text() in names and control.isVisible()
                ),
                None,
            )
        if target is not None and target.isVisible() and target.isEnabled():
            origin = self.mapFromGlobal(target.mapToGlobal(QPoint(0, 0)))
            self.target_rect = (
                QRect(origin, target.size()).adjusted(-5, -5, 5, 5).intersected(self.rect())
            )
        else:
            self.target_rect = QRect()  # Never spotlight a hidden or unavailable integration.
        self.card.setFixedWidth(min(420, self.width() - 48))
        self.card.adjustSize()
        x = max(24, self.width() - self.card.width() - 28)
        y = (
            28
            if self.target_rect.center().y() > self.height() // 2
            else self.height() - self.card.height() - 28
        )
        self.card.move(x, max(24, y))
        region = QRegion(self.rect())
        if not self.target_rect.isEmpty():
            region = region.subtracted(QRegion(self.target_rect))
        self.setMask(region.united(QRegion(self.card.geometry())))
        self.update()

    def eventFilter(self, watched, event):  # noqa: N802
        if event.type() in (QEvent.Type.Resize, QEvent.Type.LayoutRequest):
            QTimer.singleShot(0, self.reposition)
        return super().eventFilter(watched, event)

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath()
        path.addRect(self.rect())
        if not self.target_rect.isEmpty():
            cutout = QPainterPath()
            cutout.addRoundedRect(self.target_rect, 16, 16)
            path = path.subtracted(cutout)
        painter.fillPath(
            path,
            QColor(0, 0, 0, int((175 if self.window.reduced_transparency else 140) * self.reveal)),
        )
        if not self.target_rect.isEmpty():
            painter.setBrush(Qt.BrushStyle.NoBrush)
            accent = QColor(self.window.theme.accent)
            accent.setAlpha(int(210 * self.reveal))
            painter.setPen(QPen(accent, 2))
            painter.drawRoundedRect(self.target_rect, 16, 16)

    def finish(self, status):
        self.highlight_animation.stop()
        self.window.settings.setValue(self.prefix + "/status", status)
        self.window.settings.sync()
        self.window.select_tab(self.saved_tab)
        self.parentWidget().removeEventFilter(self)
        self.hide()
        self.deleteLater()
        self.window.tour = None
        self.window.composer.editor.setFocus()
