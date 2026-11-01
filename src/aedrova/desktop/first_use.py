"""The real six-stage first-use surface, hosted by the existing desktop app."""

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QSize, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QBoxLayout,
    QCheckBox,
    QFrame,
    QGraphicsOpacityEffect,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QPlainTextEdit,
    QProgressBar,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from aedrova.desktop.brand import BrandMark
from aedrova.desktop.controls import AppDialog, ChoiceBox
from aedrova.desktop.dialogs import button, icon_button, label
from aedrova.desktop.first_use_actions import JourneyActions
from aedrova.desktop.first_use_visuals import PURPOSE_ROLES, BudChoice, OpeningScene
from aedrova.desktop.materials import system_font
from aedrova.desktop.theme import palette

TITLES = (
    "Your team, plus Agents.",
    "Everything starts with a Space.",
    "Give Aedrova the bigger picture.",
    "Meet your new teammates.",
    "Better things happen together.",
    "Let’s make something happen.",
)
COPY = (
    (
        "One shared workspace where conversations become decisions, and "
        "decisions become working software."
    ),
    "Bring your people, projects, conversations, and AI teammates together.",
    "Your team already has the context. Connect the tools where your work happens.",
    "Aedrova coordinates the work. Buds bring a specialty of their own.",
    "Invite a few teammates, or start with a little room to grow.",
    "Describe a real project. We’ll put its first conversation in your Space.",
)


class JourneyScope(QWidget):
    "An explicitly named workspace for existing connector UI, without switching chats."

    def __init__(self, flow):
        super().__init__(flow)
        self.flow = flow
        self.account_dialog = flow.account
        self.reduced_motion = flow.reduced
        self.dot_connection_states = {}
        self.connected = self
        self.jobs = []
        from threading import Lock

        self.transport_lock = Lock()

    def enqueue(self, key, operation, completed, **_):
        # Reuse the connector's isolated service context without constructing a
        # dashboard or mutating the user's currently selected conversation.
        from PySide6.QtCore import QThreadPool

        from aedrova.desktop.account import AccountJob

        if self.flow.closed or not self.current_user():
            return False

        def serialized():
            with self.transport_lock:
                return operation()

        job = AccountJob(serialized)
        self.jobs.append(job)

        def ready(value, ok):
            self.jobs.remove(job)
            completed(value if ok else {"error": "Sign in again before connecting tools."})

        job.signals.finished.connect(ready)
        QThreadPool.globalInstance().start(job)
        return True

    def sync_bud_connections(self, rows):
        if not self.flow.closed:
            self.account_dialog.snapshot["dots"] = [
                row
                for row in self.account_dialog.snapshot.get("dots", [])
                if row["workspace_id"] != self.workspace_id
            ] + rows

    @property
    def workspace_id(self):
        return self.flow.state.get("workspace_id")

    def current_user(self):
        return self.flow.window.current_user()


class FirstUseJourney(JourneyActions, AppDialog):
    def __init__(self, window):
        super().__init__(window)
        self.window, self.account = window, window.account_dialog
        self.theme, self.reduced = window.theme, bool(window.reduced_motion)
        self.state, self.owner, self.pending, self.closed = {}, None, False, False
        self.signing_in = False
        self.local_codes = {}
        self.stage = 0
        self.connector_gallery = None
        self.scope = JourneyScope(self)
        self.setObjectName("FirstUseJourney")
        self.setWindowTitle("Aedrova · Welcome")
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setMinimumSize(360, 540)
        self.resize(1120, 820)
        self.setPalette(palette(self.theme))
        self.layout_root = QVBoxLayout(self)
        self.layout_root.setContentsMargins(36, 24, 36, 22)
        self.layout_root.setSpacing(18)
        bar = QHBoxLayout()
        bar.addWidget(BrandMark(30))
        bar.addWidget(label("Aedrova", "title"))
        bar.addStretch()
        self.stage_label = label("WELCOME", "muted")
        bar.addWidget(self.stage_label)
        self.close_button = icon_button("close", "Save and close setup")
        self.close_button.clicked.connect(self.reject)
        bar.addWidget(self.close_button)
        self.layout_root.addLayout(bar)
        self.progress = QProgressBar()
        self.progress.setRange(0, 1000)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(3)
        self.progress.setAccessibleName("Onboarding progress")
        self.progress_animation = QPropertyAnimation(self.progress, b"value", self)
        self.progress_animation.setDuration(280)
        self.progress_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.layout_root.addWidget(self.progress)
        self.stack = QStackedWidget()
        self.layout_root.addWidget(self.stack, 1)
        self.pages = []
        self.headings = []
        self._opening()
        self._space()
        self._context()
        self._buds()
        self._team()
        self._build()
        self.status = label("", "muted", wrap=True)
        self.status.setAccessibleName("Setup status")
        self.layout_root.addWidget(self.status)
        nav = QHBoxLayout()
        self.back = icon_button("back", "Back")
        self.back.clicked.connect(self.go_back)
        nav.addWidget(self.back)
        self.skip = button("Do this later")
        self.skip.clicked.connect(self.skip_stage)
        nav.addWidget(self.skip)
        nav.addStretch()
        self.retry = button("Reload setup", role="outline")
        self.retry.clicked.connect(self.reload_state)
        self.retry.hide()
        nav.addWidget(self.retry)
        self.primary = button("Get started", role="primary")
        self.primary.setMinimumSize(160, 46)
        self.primary.clicked.connect(self.advance)
        nav.addWidget(self.primary)
        self.layout_root.addLayout(nav)
        self.account.sign_in_ready.connect(self.authenticated)
        self.account.operation_finished.connect(self.sign_in_finished)
        self.finished.connect(self.cleanup)
        self.apply_styles()
        self.show_stage(0, animated=False)

    def apply_styles(self):
        t = self.theme
        self.setStyleSheet(f"""
        QDialog#FirstUseJourney {{background:{t.bg};
            color:{t.text};
            }}
        QLabel {{color:{t.text};}}
        QLabel[role="title"] {{font-size:18px; font-weight:600;}}
        QFrame#JourneyMaterial {{background:{t.surface};
            border:1px solid {t.border};
            border-radius:18px;
            }}
        QWidget#JourneyViewport {{background:{t.bg};}}
        QWidget#JourneyPage {{background:transparent;
            }}
        QLabel[journeyHeading="true"] {{font-size:{28 if self.width() < 760 else 42}px;
            font-weight:600; color:{t.text};}}
        QLabel[role="muted"] {{color:{t.muted};
            font-size:13px;
            }}
        QLineEdit,QPlainTextEdit,QComboBox {{background:{t.surface};
            color:{t.text};
            border:1px solid {t.border};
            border-radius:10px;
            padding:12px;
            font-size:14px;
            }}
        QLineEdit:focus,QPlainTextEdit:focus,QComboBox:focus {{border-color:{t.accent};
            }}
        QCheckBox {{color:{t.secondary};
            font-size:12px;
            spacing:10px;
            }}
        QPushButton {{color:{t.text};
            background:transparent;
            border:0;
            border-radius:10px;
            padding:11px;
            font-size:13px;
            }}
        QPushButton:hover {{background:{t.hover};
            }}
        QPushButton[role="primary"] {{background:{t.accent};
            color:{t.primary_text};
            font-weight:600;
            }}
        QPushButton[role="primary"]:hover {{background:{t.accent_hover};
            }}
        QPushButton:disabled {{color:{t.muted};
            background:{t.surface};
            }}
        QPushButton:focus {{border:2px solid {t.accent};
            }}
        QListWidget {{background:transparent;
            border:0;
            color:{t.text};
            font-size:13px;
            }}
        QListWidget::item {{padding:12px; border-radius:9px;}}
        QListWidget::item:selected {{background:{t.accent_bg}; color:{t.text};}}
        QProgressBar {{background:{t.border};
            border:0;
            border-radius:1px;
            }}
        QProgressBar::chunk {{background:{t.accent};
            border-radius:1px;
            }}
        QScrollArea {{background:transparent;
            border:0;
            }}
        """)
        from aedrova.desktop.icons import refresh

        refresh(self, t)

    def page(self, index):
        content = QWidget()
        content.setObjectName("JourneyPage")
        content.setMinimumWidth(0)
        content.setMaximumWidth(960)
        frame = QWidget()
        frame.setObjectName("JourneyViewport")
        centered = QHBoxLayout(frame)
        centered.setContentsMargins(0, 0, 0, 0)
        centered.addStretch()
        centered.addWidget(content, 1)
        centered.addStretch()
        body = QVBoxLayout(content)
        body.setContentsMargins(8, 22, 8, 24)
        body.setSpacing(18)
        heading = label(TITLES[index], "heading", wrap=True)
        heading.setProperty("journeyHeading", True)
        heading.setAccessibleName(TITLES[index])
        heading.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        heading.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        body.addWidget(heading)
        body.addWidget(label(COPY[index], "muted", wrap=True))
        self.headings.append(heading)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(frame)
        self.stack.addWidget(scroll)
        self.pages.append(content)
        return body

    def field(self, title, placeholder, limit):
        widget = QLineEdit()
        widget.setAccessibleName(title)
        widget.setPlaceholderText(placeholder)
        widget.setMaxLength(limit)
        widget.setMinimumWidth(0)
        widget.setMinimumHeight(46)
        widget.textEdited.connect(self.save_local)
        return widget

    def _opening(self):
        body = self.page(0)
        self.opening_layout = QBoxLayout(QBoxLayout.Direction.LeftToRight)
        self.opening_layout.setSpacing(26)
        self.opening_scene = OpeningScene(self)
        self.opening_layout.addWidget(self.opening_scene, 1)
        body.addLayout(self.opening_layout, 1)
        explore = button("Explore Aedrova")
        explore.clicked.connect(self.explore)
        body.addWidget(explore, alignment=Qt.AlignmentFlag.AlignLeft)
        body.addStretch()

    def _space(self):
        body = self.page(1)
        self.sign_in = button("Continue with Google", role="primary")
        from pathlib import Path

        from PySide6.QtGui import QIcon

        self.sign_in.setIcon(QIcon(str(Path(__file__).parent / "assets/google-g.png")))
        self.sign_in.setIconSize(QSize(18, 18))
        self.sign_in.clicked.connect(self.google_sign_in)
        body.addWidget(self.sign_in, alignment=Qt.AlignmentFlag.AlignLeft)
        self.space_form = QWidget()
        form = QVBoxLayout(self.space_form)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(14)
        form.addWidget(label("SPACE NAME", "muted"))
        self.space_name = self.field("Space name", "e.g. Northstar Labs", 80)
        self.icon_choices = ChoiceBox()
        self.icon_choices.setAccessibleName("Space icon")
        from aedrova.desktop.icons import icon

        for glyph, title in (
            ("spaces", "Space"),
            ("folder", "Project"),
            ("context", "Ideas"),
            ("work", "Team"),
            ("smile", "Studio"),
            ("search", "Research"),
        ):
            self.icon_choices.addItem(icon(glyph, self.theme.accent), title, glyph)
        name_row = QHBoxLayout()
        name_row.setSpacing(12)
        name_row.addWidget(self.space_name, 1)
        self.icon_choices.setFixedWidth(134)
        name_row.addWidget(self.icon_choices)
        form.addLayout(name_row)
        self.purpose = ChoiceBox()
        self.purpose.setAccessibleName("What your Space is for")
        for key, text in (
            ("software", "Building software"),
            ("design", "Design and creative work"),
            ("research", "Research and learning"),
            ("marketing", "Marketing and growth"),
            ("operations", "Product and operations"),
            ("personal", "An idea of my own"),
        ):
            self.purpose.addItem(text, key)
        form.addWidget(self.purpose)
        self.description = self.field(
            "What your team is building", "A little about what you’re building (optional)", 2000
        )
        form.addWidget(self.description)
        self.parent_space = ChoiceBox()
        self.parent_space.setAccessibleName("Independent Space or subspace")
        self.parent_space.addItem("Independent Space", None)
        self.parent_space.hide()
        form.addWidget(self.parent_space)
        self.automatic = QCheckBox("Allow background builds after a request")
        self.automatic.toggled.connect(self.revoke_review)
        form.addWidget(self.automatic)
        form.addWidget(
            label(
                (
                    "Aedrova uses Auto routing and your plan’s allowance. Permitted "
                    "context may be shared with our AI providers. Applying changes to "
                    "original files and publishing require separate approval."
                ),
                "muted",
                wrap=True,
            )
        )
        self.ai_consent = QCheckBox("I’ve reviewed and allow this AI setup")
        form.addWidget(self.ai_consent)
        self.ai_consent.toggled.connect(self.refresh_navigation)
        body.addWidget(self.space_form)
        body.addStretch()
        self.space_form.hide()

    def _context(self):
        body = self.page(2)
        self.context_note = label(
            ("No tools are connected yet. Your own conversations remain your starting point."),
            "muted",
            wrap=True,
        )
        body.addWidget(self.context_note)
        self.connect_button = button("Connect a tool", role="primary")
        self.connect_button.clicked.connect(self.begin_connections)
        body.addWidget(self.connect_button, alignment=Qt.AlignmentFlag.AlignLeft)
        self.connector_host = QWidget()
        self.connector_layout = QVBoxLayout(self.connector_host)
        self.connector_layout.setContentsMargins(0, 0, 0, 0)
        body.addWidget(self.connector_host, 1)
        body.addStretch()

    def _buds(self):
        body = self.page(3)
        identity = QHBoxLayout()
        identity.addWidget(BrandMark(48))
        agent = QVBoxLayout()
        agent.addWidget(label("Aedrova · Your main agent", "title"))
        agent.addWidget(
            label(
                "Coordinates your requests and builds from permitted team context.",
                "muted",
                wrap=True,
            )
        )
        identity.addLayout(agent, 1)
        body.addLayout(identity)
        self.capacity_note = label("Checking your team’s Bud allowance…", "muted", wrap=True)
        body.addWidget(self.capacity_note)
        self.bud_host = QWidget()
        self.bud_grid = QGridLayout(self.bud_host)
        self.bud_grid.setContentsMargins(0, 0, 0, 0)
        self.bud_grid.setSpacing(12)
        self.bud_choices = {}
        for i, role in enumerate(
            ("builder", "designer", "product", "research", "marketing", "finance")
        ):
            choice = BudChoice(role, self)
            choice.toggled.connect(self.bud_selection_changed)
            self.bud_choices[role] = choice
            self.bud_grid.addWidget(choice, i // 3, i % 3)
        body.addWidget(self.bud_host)
        body.addWidget(
            label(
                (
                    "A Bud starts with no external account access. Connect only the "
                    "tools you want it to use."
                ),
                "muted",
                wrap=True,
            )
        )
        body.addStretch()

    def _team(self):
        body = self.page(4)
        self.team_email = self.field("Teammate email", "teammate@company.com", 320)
        row = QHBoxLayout()
        row.addWidget(self.team_email, 1)
        self.invite_button = icon_button("plus", "Create teammate invitation", primary=True)
        self.invite_button.clicked.connect(self.invite_teammate)
        row.addWidget(self.invite_button)
        self.team_email.returnPressed.connect(self.invite_teammate)
        body.addLayout(row)
        body.addWidget(
            label(
                (
                    "We create a private, single-use code for each teammate. Copy it "
                    "and share it yourself. No email is sent."
                ),
                "muted",
                wrap=True,
            )
        )
        self.invite_list = QListWidget()
        self.invite_list.setAccessibleName("Your teammate invitations")
        self.invite_list.setMinimumHeight(150)
        body.addWidget(self.invite_list)
        self.copy_invite = button("Copy selected invitation code", role="outline")
        self.copy_invite.clicked.connect(self.copy_invitation)
        body.addWidget(self.copy_invite, alignment=Qt.AlignmentFlag.AlignLeft)
        body.addStretch()

    def _build(self):
        body = self.page(5)
        self.goal = QPlainTextEdit()
        self.goal.setAccessibleName("Your first project or objective")
        self.goal.setPlaceholderText("What are you and your team building?")
        self.goal.setMinimumHeight(160)
        self.goal.setMaximumHeight(240)
        self.goal.textChanged.connect(self.goal_changed)
        body.addWidget(self.goal)
        self.goal_count = label("0 / 4,000", "muted")
        body.addWidget(self.goal_count)
        self.project_button = button("Choose an existing project", role="outline")
        self.project_button.clicked.connect(self.choose_project)
        project_row = QHBoxLayout()
        project_row.addWidget(self.project_button, 1)
        self.new_project_button = icon_button("plus", "Start a new project")
        self.new_project_button.clicked.connect(self.start_new_project)
        project_row.addWidget(self.new_project_button)
        body.addLayout(project_row)
        self.project_note = label(
            "Optional. Connect a folder when you’re ready to build software.", "muted", wrap=True
        )
        body.addWidget(self.project_note)
        body.addWidget(
            label(
                (
                    "Start building saves this as your first team conversation and "
                    "opens your Space. No model run, meeting analysis or external "
                    "publishing starts automatically."
                ),
                "muted",
                wrap=True,
            )
        )
        body.addStretch()

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        compact = self.width() < 760
        self.layout_root.setContentsMargins(
            16 if compact else 48, 18 if compact else 26, 16 if compact else 48, 18
        )
        for heading in self.headings:
            heading.setFont(system_font(27 if compact else 40, QFont.Weight.DemiBold, -0.8))
        if getattr(self, "compact", None) != compact:
            self.compact = compact
            self.apply_styles()
        if self.connector_gallery:
            self.connector_gallery.setMinimumHeight(300 if compact else 420)
        columns = 2 if compact else 3
        for i, choice in enumerate(self.bud_choices.values()):
            self.bud_grid.addWidget(choice, i // columns, i % columns)
        self.opening_scene.setMinimumHeight(250 if compact else 340)

    def show_stage(self, stage, *, animated=True):
        if getattr(self, "transitioning", False):
            return
        if animated and not self.reduced and self.isVisible() and stage != self.stage:
            self.transitioning = True
            self.refresh_navigation()
            effect = QGraphicsOpacityEffect(self.stack)
            self.stack.setGraphicsEffect(effect)
            self.exit_animation = QPropertyAnimation(effect, b"opacity", self)
            self.exit_animation.setStartValue(1.0)
            self.exit_animation.setEndValue(0.0)
            self.exit_animation.setDuration(100)
            self.exit_animation.setEasingCurve(QEasingCurve.Type.InCubic)

            def enter():
                self.transitioning = False
                self.enter_stage(stage, animated=True)
                self.enter_animation = QPropertyAnimation(effect, b"opacity", self)
                self.enter_animation.setStartValue(0.0)
                self.enter_animation.setEndValue(1.0)
                self.enter_animation.setDuration(220)
                self.enter_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
                self.enter_animation.start()

            self.exit_animation.finished.connect(enter)
            self.exit_animation.start()
        else:
            self.enter_stage(stage, animated=animated)

    def enter_stage(self, stage, *, animated=True):
        self.stage = stage
        self.stack.setCurrentIndex(stage)
        self.stage_label.setText("WELCOME" if stage == 0 else f"{stage + 1} OF 6")
        value = stage * 200
        if self.reduced:
            self.progress.setValue(value)
        else:
            self.progress_animation.stop()
            self.progress_animation.setStartValue(self.progress.value())
            self.progress_animation.setEndValue(value)
            self.progress_animation.start()
        if animated and not self.reduced:
            panel = self.pages[stage]
            end = panel.pos()
            panel.move(end.x(), end.y() + 14)
            self.transition = QPropertyAnimation(panel, b"pos", self)
            self.transition.setStartValue(panel.pos())
            self.transition.setEndValue(end)
            self.transition.setDuration(280)
            self.transition.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.transition.start()
        self.status.clear()
        self.refresh_navigation()
        if stage == 2:
            role = PURPOSE_ROLES[self.purpose.currentData()]
            self.context_note.setText(
                "Connections belong to a Bud. Connecting a tool adds your "
                + role.title()
                + (
                    " Bud and uses one Bud slot. You choose access on the provider’s "
                    "own screen. You can skip this."
                )
            )
            if self.owner and self.connector_gallery is None:
                self.open_connector_gallery(role)
        if stage == 3 and self.owner:
            self.load_capacity()
        if stage == 4:
            self.load_invitations()
        self.headings[stage].setFocus(Qt.FocusReason.OtherFocusReason)

    def refresh_navigation(self, *_):
        if not hasattr(self, "primary"):
            return
        self.back.setVisible(self.stage > 0)
        self.skip.setVisible(self.stage in (2, 3, 4))
        self.primary.setText(
            "Get started"
            if self.stage == 0
            else "Start building"
            if self.stage == 5
            else "Continue"
        )
        self.primary.setEnabled(not self.pending and not self.signing_in)
        if self.stage == 1 and self.owner:
            self.primary.setEnabled(
                not self.pending
                and (bool(self.state.get("workspace_id")) or self.ai_consent.isChecked())
            )
        if self.stage == 5:
            self.primary.setEnabled(
                not self.pending and 0 < len(self.goal.toPlainText().strip()) <= 4000
            )
        if getattr(self, "transitioning", False):
            self.primary.setEnabled(False)
        self.back.setEnabled(not self.pending and not getattr(self, "transitioning", False))
        self.skip.setEnabled(not self.pending and not getattr(self, "transitioning", False))
        self.invite_button.setEnabled(not self.pending)
        self.copy_invite.setEnabled(bool(self.local_codes))
