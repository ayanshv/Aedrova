"""Optional first-run actions inside a signed-in workspace."""

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout

from aedrova.desktop.controls import ChoiceBox
from aedrova.desktop.dialogs import button, icon_button, label

GOALS = (
    ("catch-up", "Catch up with my team", "Find decisions and open questions.", "context"),
    ("build", "Build something", "Start with a plan or connect a project.", "terminal"),
    ("explore", "Explore Aedrova", "Try a small example before sending anything.", "search"),
)

STARTERS = (
    ("Catch up", "What has this team decided, and what’s still open?"),
    ("Plan a build", "Turn the latest product decision into a short implementation plan."),
    ("Prepare an update", "Draft a short team update from the work discussed in this channel."),
)


class GettingStarted(QFrame):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.pending = None
        self.result = None
        self.scope = None
        self.setObjectName("GettingStarted")
        self.setAccessibleName("Getting started")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 8, 14, 12)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.addWidget(label("Getting started", "heading"), 1)
        close = icon_button("close", "Dismiss getting started")
        close.clicked.connect(self.dismiss)
        header.addWidget(close)
        layout.addLayout(header)
        self.intro = label(
            "Try a starter in this channel or connect a project when you’re ready.",
            "muted",
            wrap=True,
        )
        layout.addWidget(self.intro)

        starter = QHBoxLayout()
        self.examples = ChoiceBox()
        self.examples.setAccessibleName("Starter prompt")
        for title, prompt in STARTERS:
            self.examples.addItem(title, prompt)
        starter.addWidget(self.examples, 1)
        self.draft = button("Draft prompt", role="outline")
        self.draft.clicked.connect(self.draft_prompt)
        starter.addWidget(self.draft)
        layout.addLayout(starter)

        actions = QHBoxLayout()
        self.search = button("Try workspace search", role="outline")
        self.search.clicked.connect(window.open_switcher)
        window.search_button.textEdited.connect(self.searched)
        actions.addWidget(self.search)
        self.project = button("Connect a project", role="outline")
        self.project.clicked.connect(self.connect_project)
        actions.addWidget(self.project)
        actions.addStretch()
        self.progress = label("", "muted")
        actions.addWidget(self.progress)
        layout.addLayout(actions)
        self.sample = label("", "muted", wrap=True)
        self.sample.hide()
        layout.addWidget(self.sample)
        self.next_step = button("See an example", role="outline")
        self.next_step.clicked.connect(self.follow_up)
        self.next_step.hide()
        layout.addWidget(self.next_step)
        self.hide()

    def settings_key(self):
        window = self.window
        user = window.current_user()
        if not (user and window.connected and window.connected.active and window.store.workspaces):
            return None
        account = window.account_dialog
        if not any(
            row["id"] == window.workspace_id for row in account.snapshot.get("workspaces", [])
        ):
            return None
        return f"getting-started/v1/{user.id}/{window.workspace_id}"

    def open(self, *, goal=None):
        if not (key := self.settings_key()):
            self.window.notify("Open a signed-in workspace to see getting started.")
            return
        if goal:
            self.window.settings.setValue(key + "/goal", goal)
            self.examples.setCurrentIndex(1 if goal == "build" else 0)
        self.window.settings.setValue(key + "/visible", True)
        self.window.select_tab(0)
        self.refresh()

    def dismiss(self):
        if key := self.settings_key():
            self.window.settings.setValue(key + "/visible", False)
        self.hide()
        self.pending = self.result = None
        self.sample.hide()
        self.window.composer.editor.setFocus()

    def refresh(self):
        from aedrova.desktop.projects import binding

        window = self.window
        key = self.settings_key()
        scope = (key, window.channel_id)
        if scope != self.scope:
            self.scope = scope
            self.pending = self.result = None
            self.sample.hide()
            goal = window.settings.value(key + "/goal", "") if key else ""
            self.examples.setCurrentIndex(1 if goal == "build" else 0)
        goal = window.settings.value(key + "/goal", "") if key else ""
        self.intro.setText(
            {
                "catch-up": "Ask your agent what your team decided and what’s still open.",
                "build": "Draft a plan first, or connect a project when you’re ready to build.",
                "explore": "See a sample or try a draft in this channel.",
            }.get(goal, "Try a starter in this channel or connect a project when you’re ready.")
        )
        self.next_step.setVisible(goal == "explore" or self.result is not None)
        self.next_step.setText("See an example")
        if self.result:
            kind, _ = self.result
            self.next_step.setText(
                {
                    "source": "Open a cited source",
                    "review": "Draft a review question",
                    "empty": "See an example",
                }[kind]
            )
        visible = bool(key and window.settings.value(key + "/visible", False, type=bool))
        self.setVisible(visible)
        if not visible:
            return
        drafted = window.settings.value(key + "/draft", False, type=bool)
        searched = window.settings.value(key + "/search", False, type=bool)
        connected = bool(binding(window).get("folder"))
        self.draft.setText("✓ Draft another" if drafted else "Draft prompt")
        self.search.setText("✓ Search workspace" if searched else "Try workspace search")
        self.project.setText("✓ Project settings" if connected else "Connect a project")
        self.progress.setText(f"{sum((drafted, searched, connected))} of 3 tried")
        self.draft.setEnabled(bool(window.channel_id))

    def draft_prompt(self):
        window = self.window
        if not (key := self.settings_key()) or not window.channel_id:
            return
        composer = window.composer
        editor = composer.editor
        if editor.toPlainText().strip():
            editor.setFocus()
            window.notify("Keep or clear your current draft before trying a starter.")
            return
        prompt = f"@{composer.agent_name} {self.examples.currentData()}"
        editor.setPlainText(prompt)
        self.pending = (prompt, self.examples.currentIndex(), None)
        cursor = editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        editor.setTextCursor(cursor)
        editor.setFocus()
        window.settings.setValue(key + "/draft", True)
        self.refresh()

    def prompt_sent(self, text, identifier):
        if (
            not self.isHidden()
            and self.scope == (self.settings_key(), self.window.channel_id)
            and self.pending
            and self.pending[2] is None
            and text.strip() == self.pending[0]
            and identifier
        ):
            self.pending = (*self.pending[:2], identifier)

    def reply_received(self, workspace, channel, prompt_id, text):
        from aedrova.desktop.response_actions import citations

        window = self.window
        if (
            self.isHidden()
            or self.scope != (self.settings_key(), self.window.channel_id)
            or (workspace, channel) != (window.workspace_id, window.channel_id)
            or self.pending is None
            or not prompt_id
            or prompt_id != self.pending[2]
        ):
            return
        _, starter, _ = self.pending
        self.pending = None
        sources = citations(text)
        source = next(
            (item for item in sources if item.startswith(("message:", "attachment:"))), None
        )
        if starter == 1:
            self.result = ("review", None)
            note = "Your plan is in the conversation. Review its scope before starting a build."
            if sources:
                note += " The reply also includes source references."
        elif sources:
            self.result = ("source", source) if source else ("empty", None)
            note = "The reply includes source references. Use them to check the original context."
        else:
            self.result = ("empty", None)
            note = "No sources were cited. Try the sample or add a short project brief."
        self.sample.setText(note)
        self.sample.show()
        self.refresh()

    def follow_up(self):
        kind, source = self.result or ("empty", None)
        if kind == "source":
            self.window.messages.open_reply_source(source)
        elif kind == "review":
            composer = self.window.composer
            if composer.editor.toPlainText().strip():
                composer.editor.setFocus()
                self.window.notify("Keep or clear your current draft before trying a starter.")
                return
            composer.editor.setPlainText(
                f"@{composer.agent_name} What should I verify before starting this plan?"
            )
            composer.editor.setFocus()
        else:
            self.sample.setText(
                "Example only · The team agreed to add an invite step. "
                "The open question is who can send invites. In a real reply, source links "
                "take you back to the messages the agent cites."
            )
            self.sample.show()

    def searched(self, query):
        if self.isHidden() or not query.strip():
            return
        if key := self.settings_key():
            if not self.window.settings.value(key + "/search", False, type=bool):
                self.window.settings.setValue(key + "/search", True)
                self.refresh()

    def connect_project(self):
        from aedrova.desktop.zen_setup import PROJECT

        if self.settings_key():
            self.window.show_setup(stage=PROJECT)
            # Refresh after the dialog and its project save finish.
            dialog = self.window.setup_dialog
            dialog.finished.connect(lambda *_: QTimer.singleShot(0, self.refresh))
