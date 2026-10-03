"""Optional, versioned setup and safe, task-based dashboard spotlights."""

from dataclasses import dataclass

from PySide6.QtCore import QEasingCurve, QEvent, QPoint, QPropertyAnimation, QRect, Qt, QTimer
from PySide6.QtGui import QColor, QKeySequence, QPainter, QPainterPath, QRegion, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from aedrova.desktop.controls import AppDialog, ChoiceBox
from aedrova.desktop.dialogs import button, label

VERSION = 1


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
        "Switch workspaces here. Each workspace has its own people, conversations and "
        "projects. Use + on the left to create another.",
        "workspace_title",
        ("workspaces",),
    ),
    Step(
        "Your team",
        "Bring your people together.",
        "Invite teammates with a workspace invitation. Owners and admins manage "
        "invitations, membership and the agent nickname in Workspace settings.",
        "invite_teammates_button",
        ("invitations", "roles", "nickname"),
    ),
    Step(
        "Your team",
        "Give conversations a home.",
        "Channels organize your work. Use + to create a channel; select a channel to see "
        "its conversation and unread activity.",
        "channel_list",
        ("channels", "unread"),
    ),
    Step(
        "Your team",
        "A quieter conversation.",
        "Direct messages stay separate from channels. Use the Direct messages list or ⌘⇧M"
        " to choose a teammate.",
        "dm_list",
        ("direct_messages",),
    ),
    Step(
        "Conversation",
        "Pick up the thread.",
        "Select a message's reply control to open its thread. Replies keep the main "
        "conversation clear; Escape closes the thread. Scroll up for older messages, or "
        "use ⌘⇧H.",
        "messages",
        ("messages", "threads", "history"),
    ),
    Step(
        "Conversation",
        "Find the signal.",
        "⌘K jumps to conversations. Search and context tools help you review accessible "
        "messages, decisions and sources before building. Private context follows "
        "membership permissions.",
        "search_button",
        ("search", "decisions", "sources"),
    ),
    Step(
        "Conversation",
        "Keep the work close.",
        "Use ⌘⇧U to attach a file and ⌘⇧S to save the selected attachment. The Files tab "
        "explains file access; attachments in chat are the current shared-file workflow.",
        "composer",
        ("attachments", "save_files"),
    ),
    Step(
        "Build",
        "Your project, connected.",
        "Connect a local folder in Project settings. Choose Codex or Claude and configure"
        " planning, execution permissions and your repository. Changes to these "
        "permissions always stay in your hands.",
        "button:Project settings|Connect a project",
        ("project", "provider", "workflow", "permissions"),
        1,
    ),
    Step(
        "Build",
        "Your editor stays yours.",
        "Open a connected project in your preferred IDE from this page. Select VS Code, "
        "Cursor, Xcode or Finder in Settings. GitHub is optional until you want to "
        "publish.",
        "button:Open project in IDE",
        ("ide", "repository"),
        1,
    ),
    Step(
        "Build",
        "From a decision to a build.",
        "Type @ to select your named agent, then ask it to build. It gathers context from"
        " conversations you can access and works in the background using your project "
        "permissions. Provider login or included access must be ready first.",
        "composer",
        ("mentions", "builds", "context"),
    ),
    Step(
        "Build",
        "Follow the work.",
        "Builds opens the queue, progress, recovery and usage. During a run, the activity"
        " stream shows tools and results; Stop cancels work. Review requested approvals "
        "before granting them.",
        "build_history",
        ("progress", "queue", "recovery", "usage", "cancel", "approvals"),
    ),
    Step(
        "Build",
        "Review before publishing.",
        "Open a completed run to inspect changes and test results, apply the reviewed "
        "work, open the IDE or preview, and publish to the connected GitHub repository. "
        "Publication requires your explicit approval.",
        "build_history",
        ("review", "apply", "preview", "github"),
    ),
    Step(
        "Meet",
        "Arrive ready.",
        "Check meeting devices previews your camera, microphone, speaker and screen "
        "locally. Enable macOS camera, microphone and screen-recording permissions when "
        "prompted. Checks are never recorded.",
        "button:Check meeting devices",
        ("devices", "screen_preview"),
        4,
    ),
    Step(
        "Meet",
        "A familiar room.",
        "Open channel call to meet with your team. Inside the call, use microphone and "
        "camera toggles, screen sharing, participants and leave controls. Shared hosting "
        "is required for calls between Macs. Transcription and AI meeting context are "
        "still being prepared; no silent recording.",
        "button:Open channel call",
        ("calls", "camera", "microphone", "sharing", "participants", "leave_call"),
        4,
    ),
    Step(
        "Make it yours",
        "Comfort comes first.",
        "Account → Settings lets you choose light, dark or system appearance, reduce "
        "motion and transparency, set your editor and update your display name. These "
        "preferences are saved on this Mac.",
        "profile_button",
        ("account", "settings", "appearance", "accessibility", "profile"),
    ),
    Step(
        "Make it yours",
        "Know your allowance.",
        "Settings shows your workspace's included AI usage and opens Plan & billing on "
        "the website. Local alpha builds use provider access; purchasing a sandbox plan "
        "never enables paid AI.",
        "profile_button",
        ("billing", "allowance"),
    ),
    Step(
        "Make it yours",
        "You can always come back.",
        "Log out from the account menu. Check for updates or replay Getting started "
        "and Explore Aedrova from "
        "Help whenever you like. Pause this tour to resume later; skip without changing "
        "any workspace data.",
        "profile_button",
        ("logout", "help", "updates"),
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


class SetupDialog(AppDialog):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.prefix = account_key(window)
        self.step = 0
        self.setWindowTitle("Aedrova · Make yourself at home")
        self.resize(560, 460)
        self.setMinimumWidth(460)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(18)
        self.progress = label("", "section")
        self.heading = label("", "heading", wrap=True)
        self.description = label("", "muted", wrap=True)
        for widget in (self.progress, self.heading, self.description):
            layout.addWidget(widget)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(12)
        layout.addWidget(self.content)
        layout.addStretch()
        row = QHBoxLayout()
        skip = button("Set up later", role="outline")
        skip.clicked.connect(self.defer)
        self.back = button("Back", role="outline")
        self.back.clicked.connect(lambda: self.show_step(self.step - 1))
        self.next = button("Continue", role="primary")
        self.next.clicked.connect(self.advance)
        row.addWidget(skip)
        row.addStretch()
        row.addWidget(self.back)
        row.addWidget(self.next)
        layout.addLayout(row)
        self.show_step(0)

    def show_step(self, step):
        self.step = max(0, min(3, step))
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            item.widget().deleteLater()
        content = (
            (
                "Your team, your space.",
                "Your workspace and agent name stay with your team. You can revisit invitations "
                "and workspace settings at any time.",
            ),
            (
                "Make it comfortable.",
                "Choose how Aedrova feels on this Mac. You can change these preferences later.",
            ),
            (
                "Bring your tools.",
                "Connect only the folder you want your agent to work in. Provider access and "
                "build permissions are configured in Project settings.",
            ),
            (
                "A little guidance, on your terms.",
                "Explore the dashboard in short chapters. You can skip, pause, go back or replay "
                "the tour from Help. No build or purchase starts during the tour.",
            ),
        )[self.step]
        self.progress.setText(f"MAKE YOURSELF AT HOME · {self.step + 1} OF 4")
        self.heading.setText(content[0])
        self.description.setText(content[1])
        self.back.setEnabled(self.step > 0)
        self.next.setText("Explore the dashboard" if self.step == 3 else "Continue")
        if self.step == 0:
            control = button("Workspace & agent settings", role="outline")
            control.setEnabled(bool(self.window.current_user()))
            control.clicked.connect(lambda: self.window.show_account("manage"))
            self.content_layout.addWidget(control)
        if self.step == 1:
            appearance = ChoiceBox()
            appearance.setAccessibleName("Appearance")
            for mode in ("system", "light", "dark"):
                appearance.addItem(mode.title(), mode)
            appearance.setCurrentIndex(appearance.findData(self.window.theme_mode))
            appearance.currentIndexChanged.connect(
                lambda: self.window.set_theme(appearance.currentData())
            )
            self.content_layout.addWidget(appearance)
            for text, value, callback in (
                ("Reduce motion", self.window.reduced_motion, self.window.set_reduced_motion),
                (
                    "Reduce transparency",
                    self.window.reduced_transparency,
                    self.window.set_reduced_transparency,
                ),
            ):
                control = QCheckBox(text)
                control.setChecked(value)
                control.toggled.connect(callback)
                self.content_layout.addWidget(control)
        if self.step == 2:
            editor = ChoiceBox()
            editor.setAccessibleName("Preferred editor")
            editor.addItems(["Visual Studio Code", "Cursor", "Xcode", "Finder"])
            editor.setCurrentText(self.window.settings.value("editor", "Visual Studio Code"))
            editor.currentTextChanged.connect(
                lambda value: self.window.settings.setValue("editor", value)
            )
            self.content_layout.addWidget(editor)
            for text, callback in (
                ("Connect project & workflow", self.project),
                ("Set up GitHub", self.github),
            ):
                control = button(text, role="outline")
                control.setEnabled(bool(self.window.current_user()))
                control.clicked.connect(callback)
                self.content_layout.addWidget(control)
        self.next.setFocus()
        fade(self.content, self.window.reduced_motion)

    def project(self):
        from aedrova.desktop.projects import open_project

        open_project(self.window)

    def github(self):
        from aedrova.desktop.github_setup import open_github_setup

        open_github_setup(self.window)

    def advance(self):
        if self.step < 3:
            self.show_step(self.step + 1)
        else:
            self.window.settings.setValue(self.prefix + "/setup", True)
            self.accept()
            self.window.show_tour()

    def defer(self):
        self.window.settings.setValue(self.prefix + "/deferred", True)
        self.reject()


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
        QTimer.singleShot(0, self.reposition)

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
        painter.fillPath(path, QColor(0, 0, 0, 175 if self.window.reduced_transparency else 140))

    def finish(self, status):
        self.window.settings.setValue(self.prefix + "/status", status)
        self.window.settings.sync()
        self.window.select_tab(self.saved_tab)
        self.parentWidget().removeEventFilter(self)
        self.hide()
        self.deleteLater()
        self.window.tour = None
