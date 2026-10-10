"""Milestone 2 desktop shell. Local fixtures only; service work starts in milestone 3."""

from PySide6.QtCore import QSettings, QSize, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from aedrova.desktop.agent_activity import AgentActivity, AgentClock
from aedrova.desktop.agent_stream import AgentStream
from aedrova.desktop.brand import BrandMark, app_icon
from aedrova.desktop.controls import AppDialog, AppMenu
from aedrova.desktop.conversation import Composer, MessageView
from aedrova.desktop.design_system import FlowActions
from aedrova.desktop.dialogs import CreateDialog, SwitcherDialog, button, label
from aedrova.desktop.materials import (
    AdaptiveBento,
    Backdrop,
    DocumentTile,
    GlassFrame,
    SpringButton,
    system_font,
)
from aedrova.desktop.state import DemoStore
from aedrova.desktop.theme import DARK, LIGHT, palette, stylesheet


class AedrovaWindow(QMainWindow):
    def __init__(self, *, settings=None, store=None):
        super().__init__()
        self.settings = settings if settings is not None else QSettings("Aedrova", "Desktop")
        self.store = store or DemoStore()
        self.connected = None
        self.workspace_id = "northstar"
        self.channel_id = "product"
        self.thread_id = ""
        self.last_channels = {"northstar": "product", "orbit": "orbit-general"}
        self.theme_mode = self.settings.value("appearance", "system")
        if self.theme_mode not in ("light", "dark", "system"):
            self.theme_mode = "system"
        self.theme = LIGHT
        self.reduced_motion = self.settings.value("reduceMotion", False, type=bool)
        self.reduced_transparency = self.settings.value("reduceTransparency", False, type=bool)
        QApplication.instance().setProperty("reduceMotion", self.reduced_motion)
        self.setFont(system_font())
        self.setWindowIcon(app_icon())
        self.setWindowTitle("Aedrova — Northstar Labs · Local preview")
        self.resize(1440, 940)
        self.setMinimumSize(900, 650)
        self.dialog = None
        self.tour = None
        self.workspace_buttons = {}
        self.tab_buttons = []
        self._build_shell()
        self._menus()
        from aedrova.desktop.collaboration import Collaboration

        self.collaboration = Collaboration(self)
        QApplication.instance().styleHints().colorSchemeChanged.connect(self._system_theme_changed)
        self.set_theme(self.theme_mode, persist=False)
        self._populate_rail()
        self._populate_channels()
        self._load_channel()
        self._render_pages()

    @property
    def workspace(self):
        return self.store.workspace(self.workspace_id)

    @property
    def channel(self):
        return self.store.channel(self.workspace_id, self.channel_id)

    def _build_shell(self):
        root = Backdrop()
        self.backdrop = root
        root.setObjectName("Root")
        self.setCentralWidget(root)
        vertical = QVBoxLayout(root)
        vertical.setContentsMargins(0, 0, 0, 0)
        vertical.setSpacing(0)
        top = QFrame()
        top.setObjectName("Topbar")
        top.setFixedHeight(48)
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(16, 0, 16, 0)
        identity = QWidget()
        identity.setFixedWidth(244)
        identity_layout = QHBoxLayout(identity)
        identity_layout.setContentsMargins(0, 0, 0, 0)
        identity_layout.setSpacing(9)
        identity_layout.addWidget(BrandMark(26))
        brand = label("Aedrova")
        brand.setStyleSheet("font-size: 14px; font-weight: 600;")
        identity_layout.addWidget(brand)
        identity_layout.addStretch()
        top_layout.addWidget(identity)
        self.sidebar_toggle = button("☷", "Toggle channel sidebar", "icon")
        self.sidebar_toggle.setFixedSize(34, 34)
        self.sidebar_toggle.setToolTip("Show or hide channels")
        self.sidebar_toggle.clicked.connect(self.toggle_sidebar)
        top_layout.addWidget(self.sidebar_toggle)
        self.search_button = button(
            "Find a conversation · ⌘K",
            "Jump to channel or workspace",
        )
        self.search_button.setObjectName("Search")
        self.search_button.setToolTip("Find a channel, person, or workspace · ⌘K")
        self.search_button.setMaximumWidth(470)
        self.search_button.setMinimumHeight(36)
        self.search_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.search_button.clicked.connect(self.open_switcher)
        top_layout.addWidget(self.search_button, 1)
        top_layout.addStretch()
        self.connection_badge = label("Local preview", "badge")
        top_layout.addWidget(self.connection_badge, 0, Qt.AlignmentFlag.AlignVCenter)
        self.theme_button = button("◐", "Toggle light and dark appearance", "icon")
        self.theme_button.setFixedSize(34, 34)
        self.theme_button.clicked.connect(self.toggle_theme)
        top_layout.addWidget(self.theme_button)
        vertical.addWidget(top)
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        vertical.addLayout(body, 1)
        rail = QFrame()
        rail.setObjectName("Rail")
        rail.setFixedWidth(54)
        rail_outer = QVBoxLayout(rail)
        rail_outer.setContentsMargins(3, 18, 3, 18)
        self.rail_items = QVBoxLayout()
        self.rail_items.setSpacing(12)
        rail_scroll = QScrollArea()
        rail_scroll.setFrameShape(QFrame.Shape.NoFrame)
        rail_scroll.setWidgetResizable(True)
        rail_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        rail_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        rail_scroll.setStyleSheet("QScrollArea { background: transparent; }")
        rail_content = QWidget()
        self.rail_items.setContentsMargins(0, 0, 0, 0)
        self.rail_items.setAlignment(Qt.AlignmentFlag.AlignTop)
        rail_content.setLayout(self.rail_items)
        rail_scroll.setWidget(rail_content)
        rail_scroll.setFixedHeight(52)
        rail_content.setAutoFillBackground(False)
        rail_scroll.viewport().setAutoFillBackground(False)
        rail_outer.addWidget(rail_scroll)
        self.workspace_picker = button("", "All workspaces", "icon")
        self.workspace_picker.setFixedSize(42, 36)
        from aedrova.desktop.icons import assign

        assign(self.workspace_picker, "spaces")
        self.workspace_picker.clicked.connect(self.workspace_menu)
        rail_outer.addWidget(self.workspace_picker)
        rail_outer.addStretch(1)
        self.create_workspace_button = button("+", "Create workspace", "workspace")
        self.create_workspace_button.setFixedSize(44, 44)
        self.create_workspace_button.setToolTip("Create a workspace")
        self.create_workspace_button.clicked.connect(self.create_workspace)
        rail_outer.addWidget(self.create_workspace_button)
        self.profile_button = button("○", "Account menu", "icon")
        self.profile_button.setFixedSize(42, 38)
        self.profile_button.setToolTip("Account and settings")
        self.profile_button.clicked.connect(self.open_profile_menu)
        rail_outer.addWidget(self.profile_button)
        body.addWidget(rail)
        self.sidebar = GlassFrame(layer="sidebar", radius=0)
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(236)
        side = QVBoxLayout(self.sidebar)
        side.setContentsMargins(16, 20, 16, 16)
        side.setSpacing(8)
        self.workspace_title = button("Northstar Labs  ⌄", "Select workspace")
        self.workspace_title.setStyleSheet("font-size: 16px; font-weight: 600; padding-left: 6px;")
        self.workspace_title.clicked.connect(self.workspace_menu)
        side.addWidget(self.workspace_title)
        subtitle = label("Team workspace", "muted")
        subtitle.setContentsMargins(7, 0, 0, 0)
        side.addWidget(subtitle)
        self.invite_teammates_button = button("Invite teammates…", "Invite teammates")
        self.invite_teammates_button.clicked.connect(lambda: self.show_account("invite"))
        side.addWidget(self.invite_teammates_button)
        self.pulse_button = button("Pulse", "Open startup command center", "tab")
        self.pulse_button.setCheckable(True)
        self.pulse_button.setToolTip("Your startup’s connected context and recent changes")
        self.pulse_button.clicked.connect(self.open_pulse)
        side.addWidget(self.pulse_button)
        from aedrova.desktop.dots import DotSection

        self.ai_team_section = DotSection(self)
        side.addWidget(self.ai_team_section)
        side.addSpacing(8)
        self.workspace_tools_toggle = button("Workspace tools  ⌄", "Show workspace tools")
        self.workspace_tools_toggle.setObjectName("WorkspaceToolsToggle")
        self.workspace_tools_toggle.setCheckable(True)
        self.workspace_tools_toggle.setToolTip(
            "Product memory, build queue, activity and saved messages"
        )
        self.workspace_tools = QWidget()
        self.workspace_tools.setObjectName("WorkspaceTools")
        self.workspace_tools_layout = FlowActions(self.workspace_tools)
        self.workspace_tools.hide()
        self.workspace_tools_toggle.toggled.connect(self.workspace_tools.setVisible)
        side.addWidget(self.workspace_tools_toggle)
        side.addWidget(self.workspace_tools)
        side.addSpacing(12)
        channels_header = QHBoxLayout()
        channels_header.addWidget(label("CHANNELS", "section"))
        channels_header.addStretch()
        self.create_channel_button = button("+", "Create channel", "icon")
        self.create_channel_button.setFixedSize(25, 25)
        self.create_channel_button.clicked.connect(self.create_channel)
        channels_header.addWidget(self.create_channel_button)
        side.addLayout(channels_header)
        self.channel_list = QListWidget()
        self.channel_list.setObjectName("Navigation")
        self.channel_list.setAccessibleName("Workspace channels")
        self.channel_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.channel_list.currentItemChanged.connect(self._channel_selected)
        side.addWidget(self.channel_list, 3)
        side.addSpacing(12)
        side.addWidget(label("DIRECT MESSAGES", "section"))
        self.dm_list = QListWidget()
        self.dm_list.setObjectName("Navigation")
        self.dm_list.setAccessibleName("Direct conversations")
        self.dm_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.dm_list.currentItemChanged.connect(self._channel_selected)
        side.addWidget(self.dm_list, 2)
        side.addStretch(1)
        body.addWidget(self.sidebar)
        main = GlassFrame(layer="main", radius=0)
        self.main_surface = main
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.header = QFrame()
        self.header.setObjectName("ChannelHeader")
        self.header.setFixedHeight(68)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(24, 12, 24, 12)
        heading = QVBoxLayout()
        heading.setSpacing(2)
        self.channel_title = label("Product", "display")
        self.channel_title.setStyleSheet("font-size:20px;font-weight:600;")
        self.channel_title.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.channel_topic = label("", "muted")
        self.channel_topic.setWordWrap(True)
        space_identity = QHBoxLayout()
        space_identity.setSpacing(8)
        self.space_symbol = label("#", "title")
        self.space_symbol.setObjectName("SpaceSymbol")
        space_identity.addWidget(self.space_symbol)
        space_identity.addWidget(self.channel_title, 1)
        heading.addLayout(space_identity)
        heading.addWidget(self.channel_topic)
        header_layout.addLayout(heading, 1)
        self.members_label = label("AM   MC   SR   + You", "muted")
        self.members_label.setParent(self.header)
        self.members_label.setToolTip("Sample conversation participants")
        self.members_label.hide()
        self.call_bar = QFrame()
        self.call_bar.setObjectName("CallBar")
        self.call_bar.setFixedHeight(40)
        call_layout = QHBoxLayout(self.call_bar)
        call_layout.setContentsMargins(5, 5, 5, 5)
        call_layout.setSpacing(3)
        self.call_count = label("", "muted")
        self.call_count.hide()
        call_layout.addWidget(self.call_count)
        self.call_buttons = {}
        for kind, title in (
            ("phone", "Start audio call"),
            ("camera", "Start video call"),
            ("settings", "Meeting options"),
        ):
            control = button("", title, "icon")
            control.setFixedSize(30, 30)
            control.setAccessibleName(title)
            if kind == "settings":
                control.clicked.connect(self.open_call_options)
            else:
                mode = "audio" if kind == "phone" else "video"
                control.clicked.connect(
                    lambda checked=False, mode=mode: self.start_channel_call(mode)
                )
            self.call_buttons[kind] = control
            call_layout.addWidget(control)
        header_layout.addWidget(self.call_bar)
        main_layout.addWidget(self.header)
        tab_area = QWidget()
        tab_area_outer = QVBoxLayout(tab_area)
        tab_area_outer.setContentsMargins(24, 0, 24, 8)
        tab_area_layout = FlowActions()
        tab_area_outer.addLayout(tab_area_layout)
        tab_area.setObjectName("Segments")
        self.primary_navigation = tab_area
        self.primary_tabs_layout = tab_area_layout
        tabs_layout = tab_area_layout
        for index, title in enumerate(("Conversation", "Project", "Work", "Files")):
            tab = button(title, f"Open {title.lower()} tab", "tab")
            tab.setCheckable(True)
            tab.clicked.connect(lambda checked=False, i=index: self.select_tab(i))
            self.tab_buttons.append(tab)
            tabs_layout.addWidget(tab)
        tab_area_layout.addStretch()
        self.memory_button = button("Team context", "Open product memory", "outline")
        self.memory_button.clicked.connect(self.open_product_memory)
        self.workspace_tools_layout.addWidget(self.memory_button)
        self.navigation_actions = self.workspace_tools_layout
        main_layout.addWidget(tab_area)
        self.pages = QStackedWidget()
        main_layout.addWidget(self.pages, 1)
        body.addWidget(main, 1)
        self._build_chat()
        for _ in range(3):
            self.pages.addWidget(QWidget())
        from aedrova.desktop.pulse import PulsePage

        self.pulse_page = PulsePage(self)
        self.pages.addWidget(self.pulse_page)
        self.select_tab(0)
        self.notice = label(
            "Local preview · messages and new spaces reset when the app closes.", "muted"
        )
        self.notice.setObjectName("ShortcutFooter")
        self.notice.setContentsMargins(16, 5, 16, 5)
        self.notice.setWordWrap(True)
        vertical.addWidget(self.notice)
        self.notice_timer = QTimer(self)
        self.notice_timer.setSingleShot(True)
        self.notice_timer.timeout.connect(self._reset_notice)

    def _build_chat(self):
        self.chat_page = QWidget()
        self.chat_page.setObjectName("Chat")
        row = QHBoxLayout(self.chat_page)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        self.chat_column = QWidget()
        chat = QVBoxLayout(self.chat_column)
        chat.setContentsMargins(0, 0, 0, 0)
        chat.setSpacing(0)
        self.pinned = button(
            "↗   Pinned decision     ·     Three steps. Less friction.",
            "Open pinned onboarding decision",
        )
        self.pinned.setObjectName("Pinned")
        self.pinned.clicked.connect(self.open_pinned)
        pinned_area = QHBoxLayout()
        pinned_area.setContentsMargins(28, 4, 28, 0)
        pinned_area.addWidget(self.pinned)
        chat.addLayout(pinned_area)
        self.conversation_date = label("Friday, September 25  ·  Sample conversation", "section")
        date = self.conversation_date
        date.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        conversation_header = QWidget()
        conversation_header.setObjectName("ConversationHeader")
        self.conversation_header_layout = QHBoxLayout(conversation_header)
        self.conversation_header_layout.setContentsMargins(28, 8, 28, 8)
        self.conversation_header_layout.addWidget(date)
        self.conversation_header_layout.addStretch()
        chat.addWidget(conversation_header)
        self.meeting_announcements = QWidget()
        self.meeting_announcements_layout = QVBoxLayout(self.meeting_announcements)
        self.meeting_announcements_layout.setContentsMargins(28, 0, 28, 10)
        self.meeting_announcements.hide()
        chat.addWidget(self.meeting_announcements)
        self.message_stack = QStackedWidget()
        self.messages = MessageView()
        self.messages.thread_requested.connect(self.open_thread)
        self.message_stack.addWidget(self.messages)
        empty = QWidget()
        empty_layout = QVBoxLayout(empty)
        empty_layout.setContentsMargins(32, 32, 32, 32)
        empty_layout.addStretch()
        empty_layout.addWidget(BrandMark(76))
        empty_layout.addSpacing(12)
        empty_heading = label("Every good idea starts\nwith a conversation.", "heading")
        empty_heading.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        empty_layout.addWidget(empty_heading)
        empty_layout.addWidget(label("Start the conversation. Send your first message.", "muted"))
        empty_layout.addStretch()
        empty_scroll = QScrollArea()
        empty_scroll.setWidgetResizable(True)
        empty_scroll.setFrameShape(QFrame.Shape.NoFrame)
        empty_scroll.setWidget(empty)
        empty.setObjectName("Chat")
        self.message_stack.addWidget(empty_scroll)
        chat.addWidget(self.message_stack, 1)
        compose_area = QWidget()
        composition = QVBoxLayout(compose_area)
        composition.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        composition.setContentsMargins(28, 12, 28, 18)
        composition.setSpacing(9)
        self.composer = Composer()
        self.composer.submitted.connect(self.send_message)
        self.build_activity = AgentActivity()
        self.build_activity.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.build_activity.hide()
        self.build_activity.clicked.connect(self.open_agent_activity)
        activity_row = QHBoxLayout()
        activity_row.setContentsMargins(0, 0, 0, 0)
        activity_row.addWidget(self.build_activity, 1)
        self.agent_clock = AgentClock()
        activity_row.addWidget(self.agent_clock)
        self.stop_agent = button("Stop", "Stop background build", "outline")
        self.stop_agent.hide()
        self.stop_agent.clicked.connect(self.cancel_agent)
        activity_row.addWidget(self.stop_agent)
        self.build_history = button("Builds", "Build queue, recovery and usage", "outline")

        def show_builds():
            from aedrova.desktop.execution import execution_queue

            execution_queue(self).show_history()

        self.build_history.clicked.connect(show_builds)
        self.build_history.setText("Queue")
        self.workspace_tools_layout.addWidget(self.build_history)
        self.agent_feed = AgentStream()
        status_controls = QWidget()
        status_controls.setLayout(activity_row)
        self.agent_feed.install_status_controls(status_controls)
        self.last_agent_event = ""
        self.messages.attach_agent_feed(self.agent_feed)
        composition.addWidget(self.composer)
        footer = label("Aedrova stays quiet until you mention it.", "muted")
        footer.hide()
        composition.addWidget(footer)
        chat.addWidget(compose_area)
        row.addWidget(self.chat_column, 1)
        self.thread_panel = GlassFrame(layer="thread", radius=0)
        self.thread_panel.setObjectName("ThreadPanel")
        thread = QVBoxLayout(self.thread_panel)
        thread.setContentsMargins(0, 0, 0, 0)
        thread.setSpacing(0)
        top = QHBoxLayout()
        top.setContentsMargins(20, 16, 14, 16)
        self.thread_title = label("Thread", "title")
        top.addWidget(self.thread_title)
        top.addStretch()
        self.thread_close = button("×", "Close thread", "icon")
        self.thread_close.setFixedSize(30, 30)
        self.thread_close.clicked.connect(self.close_thread)
        top.addWidget(self.thread_close)
        thread.addLayout(top)
        self.thread_messages = MessageView(allow_threads=False)
        self.thread_messages.setAccessibleName("Thread messages")
        for view in (self.messages, self.thread_messages):
            view.reaction_requested.connect(self.react_message)
            view.unsend_requested.connect(self.unsend_message)
        thread.addWidget(self.thread_messages, 1)
        thread_composition = QVBoxLayout()
        thread_composition.setContentsMargins(16, 8, 16, 18)
        self.thread_composer = Composer(thread=True)
        self.thread_composer.editor.setPlaceholderText("Reply to this thread…")
        self.thread_composer.submitted.connect(self.send_reply)
        thread_composition.addWidget(self.thread_composer)
        thread.addLayout(thread_composition)
        row.addWidget(self.thread_panel)
        row.setSpacing(12)
        row.setContentsMargins(0, 0, 0, 0)
        self.thread_panel.hide()
        self.pages.addWidget(self.chat_page)

    def _menus(self):
        workspace_menu = self.menuBar().addMenu("Workspace")
        workspace_menu.addAction("New workspace…", self.create_workspace)
        workspace_menu.addAction("New channel…", self.create_channel)
        workspace_menu.addAction("Invite teammates…", lambda: self.show_account("invite"))
        view = self.menuBar().addMenu("View")
        jump = view.addAction("Jump to conversation…", self.open_switcher)
        jump.setShortcut(QKeySequence("Ctrl+K"))
        view.addAction("Toggle sidebar", self.toggle_sidebar)
        pulse_action = view.addAction("Startup Pulse", self.open_pulse)
        pulse_action.setShortcut(QKeySequence("Ctrl+5"))
        appearance = view.addMenu("Appearance")
        group = QActionGroup(self)
        self.appearance_actions = {}
        for mode in ("system", "light", "dark"):
            action = QAction(mode.title(), self)
            action.setCheckable(True)
            action.triggered.connect(lambda checked=False, m=mode: self.set_theme(m))
            group.addAction(action)
            appearance.addAction(action)
            self.appearance_actions[mode] = action
        view.addSeparator()
        self.reduce_motion_action = view.addAction("Reduce motion")
        self.reduce_motion_action.setCheckable(True)
        self.reduce_motion_action.setChecked(self.reduced_motion)
        self.reduce_motion_action.toggled.connect(self.set_reduced_motion)
        self.reduce_transparency_action = view.addAction("Reduce transparency")
        self.reduce_transparency_action.setCheckable(True)
        self.reduce_transparency_action.setChecked(self.reduced_transparency)
        self.reduce_transparency_action.toggled.connect(self.set_reduced_transparency)
        for i in range(4):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{i + 1}"), self)
            shortcut.activated.connect(lambda index=i: self.select_tab(index))
        theme_shortcut = QShortcut(QKeySequence("Ctrl+Shift+L"), self)
        theme_shortcut.activated.connect(self.toggle_theme)
        escape = QShortcut(QKeySequence("Escape"), self)
        escape.activated.connect(
            lambda: self.tour.finish("paused") if self.tour else self.close_thread()
        )
        account_menu = self.menuBar().addMenu("Account")
        account_menu.addAction("Account & workspaces…", self.show_account)
        settings = account_menu.addAction("Settings…", self.show_settings)
        settings.setShortcut(QKeySequence("Ctrl+,"))
        account_menu.addAction("Log out", self.log_out)
        help_menu = self.menuBar().addMenu("Help")
        help_menu.addAction("Getting started…", self.show_setup)
        help_menu.addAction("Explore Aedrova…", self.show_tour)
        help_menu.addAction("Check for updates…", self.show_updates)
        help_menu.addAction("About this preview", self.show_about)

    def _populate_rail(self):
        while self.rail_items.count():
            widget = self.rail_items.takeAt(0).widget()
            widget.deleteLater()
        self.workspace_buttons.clear()
        for workspace in self.store.workspaces:
            item = button(workspace.initials, f"Open {workspace.name} workspace", "workspace")
            item.setFixedSize(44, 44)
            item.setCheckable(True)
            item.setChecked(workspace.id == self.workspace_id)
            item.setToolTip("Workspace · " + workspace.name)
            item.clicked.connect(
                lambda checked=False, wid=workspace.id: (
                    self.workspace_menu()
                    if wid == self.workspace_id
                    else self.switch_workspace(wid)
                )
            )
            # Parent the control before showing it. An unparented visible button
            # briefly becomes a native window and can switch macOS fullscreen Spaces.
            self.rail_items.addWidget(item)
            item.setVisible(workspace.id == self.workspace_id)
            self.workspace_buttons[workspace.id] = item

    def _populate_channels(self):
        self.workspace_title.setText(
            self.workspace_title.fontMetrics().elidedText(
                f"{self.workspace.name}  ⌄",
                Qt.TextElideMode.ElideRight,
                177,
            )
        )
        self.workspace_title.setToolTip(self.workspace.name)
        for listing in (self.channel_list, self.dm_list):
            listing.blockSignals(True)
            listing.clear()
        for channel in self.workspace.channels:
            item = QListWidgetItem(f"{'○' if channel.direct else '#'}    {channel.name}")
            item.setData(Qt.ItemDataRole.UserRole, channel.id)
            item.setToolTip(channel.topic)
            listing = self.dm_list if channel.direct else self.channel_list
            listing.addItem(item)
            if channel.id == self.channel_id:
                listing.setCurrentItem(item)
        self.channel_list.setMaximumHeight(min(280, max(80, self.channel_list.count() * 41)))
        self.dm_list.setMaximumHeight(max(38, min(160, self.dm_list.count() * 41)))
        self.dm_list.setVisible(self.dm_list.count() > 0)
        for listing in (self.channel_list, self.dm_list):
            listing.blockSignals(False)

    def _channel_selected(self, item, previous):
        if item:
            self.switch_channel(item.data(Qt.ItemDataRole.UserRole))

    def _save_drafts(self):
        self.store.drafts[(self.workspace_id, self.channel_id, "")] = (
            self.composer.editor.toPlainText()
        )
        if self.thread_id:
            self.store.drafts[(self.workspace_id, self.channel_id, self.thread_id)] = (
                self.thread_composer.editor.toPlainText()
            )

    def switch_workspace(self, workspace_id):
        if workspace_id == self.workspace_id:
            self.workspace_buttons[workspace_id].setChecked(True)
            return
        dot_dialog = getattr(self, "dots_dialog", None)
        if dot_dialog:
            dot_dialog.reject()
        query = getattr(self, "dot_query", None)
        if query and hasattr(query, "runner"):
            query.runner.cancel()
        teammate_dialog = getattr(self, "teammates_dialog", None)
        if teammate_dialog and not teammate_dialog.closed:
            teammate_dialog.reject()
        memory = getattr(self, "memory_dialog", None)
        if memory and not memory.closed:
            memory.reject()
        shared = getattr(self, "shared_build_dialog", None)
        if shared:
            shared.reject()
        self._save_drafts()
        self.last_channels[self.workspace_id] = self.channel_id
        self.workspace_id = workspace_id
        candidate = self.last_channels.get(workspace_id)
        self.channel_id = next(
            (c.id for c in self.workspace.channels if c.id == candidate),
            self.workspace.channels[0].id,
        )
        self.thread_id = ""
        self.thread_panel.hide()
        self.chat_column.show()
        self._populate_rail()
        self._populate_channels()
        self._load_channel()
        self._render_pages()
        self.select_tab(0)
        if self.connected and self.connected.active:
            self.connected.refresh()

    def switch_channel(self, channel_id):
        if channel_id == self.channel_id:
            self.select_tab(0)
            return
        self._save_drafts()
        self.channel_id = channel_id
        self.thread_id = ""
        self.thread_panel.hide()
        self.chat_column.show()
        self._populate_channels()
        self._load_channel()
        self.select_tab(0)
        if self.connected and self.connected.active:
            self.connected.refresh()

    def _load_channel(self):
        account = getattr(self, "account_dialog", None)
        preferences = account.snapshot.get("agent_preferences", []) if account else []
        nickname = next(
            (p["nickname"] for p in preferences if p["workspace_id"] == self.workspace_id),
            "Aedrova",
        )
        if hasattr(self, "ai_team_section"):
            team = (
                [
                    r
                    for r in account.snapshot.get("dots", [])
                    if r["workspace_id"] == self.workspace_id
                ]
                if account
                else []
            )
            self.ai_team_section.sync(team, self.workspace_id)
        for composer in (self.composer, self.thread_composer):
            composer.dots = (
                [
                    r
                    for r in self.account_dialog.snapshot.get("dots", [])
                    if r["workspace_id"] == self.workspace_id
                ]
                if hasattr(self, "account_dialog")
                else []
            )
            composer.set_agent_name(nickname)
        if self.connected and self.current_user():
            from aedrova.desktop.execution import execution_queue

            execution_queue(self)
        if hasattr(self, "stop_agent"):
            self.update_agent_cancel()
        if hasattr(self, "agent_feed"):
            self.messages.set_agent_visible(
                getattr(self, "activity_workspace", None) == self.workspace_id
                and getattr(self, "activity_channel", None) == self.channel_id
                and bool(self.agent_feed.toPlainText())
            )
        if hasattr(self, "build_activity"):
            self.build_activity.setVisible(
                getattr(self, "activity_workspace", None) == self.workspace_id
            )
        channel = self.channel
        self.setWindowTitle(f"Aedrova — {self.workspace.name} · Local preview")
        self.channel_title.setText(channel.name if channel.direct else channel.name.capitalize())
        self.channel_topic.setText(channel.topic)
        self.conversation_date.setText(
            "Friday, September 25  ·  Sample conversation"
            if self.workspace_id == "northstar"
            else "Local conversation"
        )
        self.messages.show_messages(channel.messages)
        self.message_stack.setCurrentIndex(0 if self.messages.model().rowCount() else 1)
        shared_pins = [
            m
            for root in channel.messages
            for m in [root, *root.replies]
            if m.pinned and not m.unsent
        ]
        self.pinned.setVisible(bool(shared_pins) or any(m.decision for m in channel.messages))
        if shared_pins:
            self.pinned.setText(
                f"↗   {len(shared_pins)} pinned "
                + ("message" if len(shared_pins) == 1 else "messages")
            )
        self.composer.editor.setPlaceholderText(
            f"Message {' ' if channel.direct else '#'}{channel.name}…"
        )
        self.composer.editor.setPlainText(
            self.store.drafts.get((self.workspace_id, self.channel_id, ""), "")
        )
        if self.connected and self.connected.active:
            self.setWindowTitle(f"Aedrova — {self.workspace.name}")
            self.connection_badge.setText("Connected")
            self.conversation_date.setText("Shared conversation")
            self.members_label.setText("Your team")
            self.composer.setEnabled(bool(self.channel_id))
        if hasattr(self, "account_dialog"):
            from aedrova.desktop.meeting_activity import update_meeting_ui

            update_meeting_ui(self)

    def open_pinned(self):
        if self.connected and self.connected.active and hasattr(self, "collaboration"):
            self.collaboration.panel("pinned", self.channel_id)
            return
        for message in self.channel.messages:
            if message.decision:
                self.open_thread(message.id)
                break

    def open_thread(self, message_id):
        parent = next((m for m in self.channel.messages if m.id == message_id), None)
        if parent is None:
            return
        self._save_drafts()
        self.thread_id = message_id
        self.thread_title.setText(f"Thread · {len(parent.replies)} replies")
        self.thread_messages.show_messages([parent, *parent.replies])
        self.thread_composer.editor.setPlainText(
            self.store.drafts.get((self.workspace_id, self.channel_id, message_id), "")
        )
        self.thread_panel.show()
        self._adapt_thread()
        self.thread_composer.editor.setFocus()

    def close_thread(self):
        if not self.thread_id:
            return
        self._save_drafts()
        self.thread_id = ""
        self.thread_panel.hide()
        self.chat_column.show()
        self.composer.editor.setFocus()

    def _adapt_thread(self):
        if self.thread_id:
            wide = self.chat_page.width() >= 940
            self.chat_column.setVisible(wide)
            self.thread_panel.setMinimumWidth(360 if wide else 0)
            self.thread_panel.setMaximumWidth(390 if wide else 16777215)

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        if hasattr(self, "thread_panel"):
            self._adapt_thread()
            QTimer.singleShot(0, self._adapt_thread)
            compact = self.height() < 760
            self.header.setFixedHeight(64 if compact else 68)
            self.conversation_date.setContentsMargins(
                0, 8 if compact else 12, 0, 6 if compact else 8
            )

    def open_agent_activity(self):
        if getattr(self, "agent_setup_needed", False):
            from aedrova.desktop.projects import open_project

            open_project(self)
            return
        from aedrova.desktop.builds import open_build

        open_build(self)

    def update_agent_cancel(self):
        build = getattr(self, "build_dialog", None)
        active = bool(
            build
            and not build.invalidated
            and build.workspace == self.workspace_id
            and (build.pending or build.background_transition)
        )
        query = getattr(self, "dot_query", None)
        active = active or bool(query and query.workspace == self.workspace_id)
        self.stop_agent.setVisible(active)
        self.agent_clock.set_active(active)
        if not active and hasattr(self, "agent_feed"):
            self.agent_feed.finish_pending()
        self.build_activity.configure(self.theme, self.reduced_motion, active)

    def agent_event(self, workspace, text, *, update_activity=True):
        if workspace != self.workspace_id:
            return
        if text == self.last_agent_event:
            return
        self.last_agent_event = text
        if text.startswith("$ "):
            summary = text.splitlines()[0][:200] + " · " + text.splitlines()[-1]
        elif text.startswith("Files changed:"):
            import json
            from pathlib import Path

            try:
                names = [Path(c["path"]).name for c in json.loads(text.split(":", 1)[1])]
                summary = "Edited " + ", ".join(names[:6])
            except (ValueError, TypeError, KeyError):
                summary = "Updated project files"
        else:
            summary = text[:1400]
        self.activity_workspace = workspace
        self.activity_channel = getattr(self, "activity_channel", self.channel_id)
        account = getattr(self, "account_dialog", None)
        preferences = account.snapshot.get("agent_preferences", []) if account else []
        self.agent_feed.author_name = next(
            (p["nickname"] for p in preferences if p["workspace_id"] == workspace), "Aedrova"
        )
        active = getattr(self, "build_dialog", None)
        if active and getattr(active, "teammate", None) and active.workspace == workspace:
            self.agent_feed.author_name = active.teammate["config"]["name"]
        query = getattr(self, "dot_query", None)
        bud = (
            getattr(query, "bud", None)
            if query
            else getattr(active, "bud", None)
            if active and active.workspace == workspace
            else None
        )
        if bud:
            self.agent_feed.author_name = bud["name"]
        self.agent_feed.add_event(text)
        self.messages.set_agent_visible(self.activity_channel == self.channel_id)
        if self.messages.model().rowCount() == 0:
            self.message_stack.setCurrentIndex(0)
        if update_activity and getattr(self, "build_dialog", None) and self.build_dialog.job:
            phase = "Working · latest update below"
            if text.startswith("Running:"):
                phase = "Running command · " + text.removeprefix("Running:").strip()[:100]
            elif text.startswith("Files changed:"):
                phase = summary
            self.agent_activity(workspace, phase)

    def cancel_agent(self):
        query = getattr(self, "dot_query", None)
        if query and hasattr(query, "runner"):
            query.runner.cancel()
        build = getattr(self, "build_dialog", None)
        if build and build.workspace == self.workspace_id:
            build.cancel()

    def agent_activity(self, workspace, text):
        self.activity_workspace = workspace
        account = getattr(self, "account_dialog", None)
        preferences = account.snapshot.get("agent_preferences", []) if account else []
        nickname = next(
            (p["nickname"] for p in preferences if p["workspace_id"] == workspace), "Aedrova"
        )
        active = getattr(self, "build_dialog", None)
        if active and getattr(active, "teammate", None) and active.workspace == workspace:
            nickname = active.teammate["config"]["name"]
        bud = getattr(active, "bud", None)
        if bud and active.workspace == workspace and not getattr(self, "dot_query", None):
            nickname = bud["name"]
        query = getattr(self, "dot_query", None)
        bud = getattr(query, "bud", None)
        if bud and getattr(query, "workspace", None) == workspace:
            nickname = bud["name"]
        self.build_activity.setText(text[:105])
        if workspace == self.workspace_id:
            self.activity_channel = getattr(self, "activity_channel", self.channel_id)
            build = getattr(self, "build_dialog", None)
            if (
                build
                and not (build.pending or build.background_transition)
                and not getattr(self, "dot_query", None)
            ):
                self.agent_feed.author_name = nickname
                self.agent_feed.finish_with_result(text)
            else:
                self.agent_feed.set_status(nickname, text)
            self.messages.set_agent_visible(self.activity_channel == self.channel_id)
            self.message_stack.setCurrentIndex(0)
        self.build_activity.setToolTip(text + "\nPrivate build activity. Click for details.")
        self.build_activity.setVisible(workspace == self.workspace_id)
        self.update_agent_cancel()
        build = getattr(self, "build_dialog", None)
        self.build_activity.configure(
            self.theme,
            self.reduced_motion,
            bool(getattr(self, "dot_query", None))
            or bool(
                build
                and build.workspace == workspace
                and (build.pending or build.background_transition)
            ),
        )

    def finish_agent_response(self, workspace, text):
        if workspace != self.workspace_id:
            return
        self.agent_feed.finish_with_result(text)
        self.update_agent_cancel()
        self.build_activity.hide()
        self.messages.set_agent_visible(getattr(self, "activity_channel", None) == self.channel_id)

    def start_agent_request(self, text):
        from aedrova.agents.context import build_command
        from aedrova.desktop.builds import open_build

        preferences = self.account_dialog.snapshot.get("agent_preferences", [])
        nickname = next(
            (p["nickname"] for p in preferences if p["workspace_id"] == self.workspace_id),
            "Aedrova",
        )
        from aedrova.dots.client import mention

        rows = [
            r
            for r in self.account_dialog.snapshot.get("dots", [])
            if r["workspace_id"] == self.workspace_id
        ]
        dot = mention(text, rows)
        task = build_command(text, nickname)
        # A direct Bud mention owns the response, including action-word requests.
        if dot and task is None:
            import re

            from aedrova.desktop.dot_analysis import start_analysis

            request = re.sub(
                r"^(?:@" + re.escape(dot["name"]) + r"|<@dot:[^>]+>)[,:]?\s*",
                "",
                text.strip(),
                flags=re.IGNORECASE,
            )
            building = bool(
                re.match(
                    r"^(?:please\s+)?(?:/build|build|implement|fix|create|ship|add)\b",
                    request,
                    re.IGNORECASE,
                )
            )
            if building:
                from aedrova.desktop.builds import start_background_build

                accepted = start_background_build(self, request, bud=dot)
            else:
                accepted = start_analysis(self, text, bud=dot)
            if accepted:
                for composer in (self.composer, self.thread_composer):
                    if composer.editor.toPlainText().strip() == text.strip():
                        composer.clear()
                self._save_drafts()
            return True
        import re

        candidate = text.strip()
        names = [nickname, "Aedrova", *(r["name"] for r in rows)]
        prefix = "|".join(re.escape(name) for name in sorted(names, key=len, reverse=True))
        candidate = re.sub(
            r"^(?:@(?:" + prefix + r")|<@dot:[^>]+>)[,:]?\s*", "", candidate, flags=re.IGNORECASE
        )
        building = candidate.startswith("/build") or bool(
            re.match(
                r"^(?:please\s+)?(?:build|implement|fix|create|ship|add)\b",
                candidate,
                re.IGNORECASE,
            )
        )
        if (dot or (task is not None and rows)) and not building:
            from aedrova.desktop.dot_analysis import start_analysis

            if start_analysis(self, task or text):
                for composer in (self.composer, self.thread_composer):
                    if composer.editor.toPlainText().strip() == text.strip():
                        composer.clear()
                self._save_drafts()
            return True
        task = build_command(text, nickname) or (text if dot and building else None)
        if task is None:
            return False
        if text.lstrip().startswith("/build"):
            open_build(self, task)
        else:
            from aedrova.desktop.builds import start_background_build

            if start_background_build(self, task):
                for composer in (self.composer, self.thread_composer):
                    if composer.editor.toPlainText().strip() == text.strip():
                        composer.clear()
                self._save_drafts()
        return True

    def _local_message(self, identifier):
        return next(
            (
                m
                for root in self.channel.messages
                for m in [root, *root.replies]
                if m.id == identifier
            ),
            None,
        )

    def react_message(self, identifier, emoji, present):
        if self.connected and self.connected.active:
            self.connected.interact(identifier, emoji, present)
            return
        message = self._local_message(identifier)
        if not message or message.unsent:
            return
        existing = next((r for r in message.reactions if r["emoji"] == emoji), None)
        if present and not existing:
            message.reactions.append({"emoji": emoji, "count": 1, "mine": True})
        elif existing and bool(existing.get("mine")) != present:
            existing["count"] += 1 if present else -1
            existing["mine"] = present
            message.reactions = [r for r in message.reactions if r["count"] > 0]
        self._refresh_interactions()

    def unsend_message(self, identifier):
        if self.connected and self.connected.active:
            self.connected.interact(identifier)
            return
        message = self._local_message(identifier)
        if message and message.mine and not message.unsent:
            message.body, message.unsent = "Message unsent.", True
            message.attachment, message.attachment_id = "", ""
            message.reactions.clear()
            self._refresh_interactions()

    def _refresh_interactions(self):
        self.messages.show_messages(self.channel.messages, force=True)
        if self.thread_id:
            parent = self._local_message(self.thread_id)
            if parent:
                self.thread_messages.show_messages([parent, *parent.replies], force=True)

    def send_message(self, text):
        if self.connected and self.connected.active:
            if self.start_agent_request(text):
                return
            self.connected.send(text)
            return
        try:
            message = self.store.send(self.workspace_id, self.channel_id, text)
        except ValueError as exc:
            self.notify(str(exc))
            return
        self.messages.conversation_model.append(message)
        self.messages.animate_sent(message.id)
        self.message_stack.setCurrentIndex(0)
        self.composer.clear()
        self.store.drafts[(self.workspace_id, self.channel_id, "")] = ""
        QTimer.singleShot(0, self.messages.scrollToBottom)
        self.notify(
            "Saved locally. Agent execution isn’t connected in this preview."
            if "@aedrova" in text.lower()
            else "Message added to this local preview."
        )

    def send_reply(self, text):
        if self.connected and self.connected.active:
            if self.start_agent_request(text):
                return
            self.connected.send(text, self.thread_id or None)
            return
        if not self.thread_id:
            return
        try:
            message = self.store.send(self.workspace_id, self.channel_id, text, self.thread_id)
        except ValueError as exc:
            self.notify(str(exc))
            return
        parent = next(m for m in self.channel.messages if m.id == self.thread_id)
        self.thread_messages.show_messages([parent, *parent.replies])
        self.thread_messages.animate_sent(message.id)
        self.thread_title.setText(f"Thread · {len(parent.replies)} replies")
        self.messages.conversation_model.refresh(self.thread_id)
        self.messages.scheduleDelayedItemsLayout()
        self.thread_composer.clear()
        self.store.drafts[(self.workspace_id, self.channel_id, self.thread_id)] = ""
        QTimer.singleShot(0, self.thread_messages.scrollToBottom)
        self.notify("Reply added to this local preview.")

    def open_product_memory(self):
        from aedrova.desktop.product_memory import open_memory

        open_memory(self)

    def select_tab(self, index):
        if not 0 <= index < len(self.tab_buttons):
            return
        self.pages.setCurrentIndex(index)
        self.pulse_button.setChecked(False)
        self.header.show()
        self.primary_navigation.show()
        if hasattr(self, "space_symbol"):
            self.space_symbol.setText("↗" if self.channel.direct else "#")
        for i, tab in enumerate(self.tab_buttons):
            tab.setChecked(i == index)
        if index == 0 and hasattr(self, "thread_panel"):
            self._adapt_thread()

    def open_pulse(self):
        self.pages.setCurrentWidget(self.pulse_page)
        self.header.hide()
        self.primary_navigation.hide()
        self.pulse_button.setChecked(True)
        for tab in self.tab_buttons:
            tab.setChecked(False)

    def toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())
        QTimer.singleShot(0, self._adapt_thread)

    def set_theme(self, mode, *, persist=True):
        if mode not in ("system", "light", "dark"):
            raise ValueError("Unknown appearance mode")
        self.theme_mode = mode
        dark = mode == "dark" or (
            mode == "system"
            and QApplication.instance().styleHints().colorScheme() == Qt.ColorScheme.Dark
        )
        self.theme = DARK if dark else LIGHT
        QApplication.instance().setPalette(palette(self.theme))
        self.setPalette(palette(self.theme))
        for dialog in self.findChildren(AppDialog):
            dialog.setPalette(palette(self.theme))
        self.setStyleSheet(stylesheet(self.theme, reduced_transparency=self.reduced_transparency))
        self.build_activity.configure(self.theme, self.reduced_motion, self.build_activity.active)
        if hasattr(self, "pulse_page"):
            self.pulse_page.apply_theme()
        self.messages.set_theme(self.theme)
        self.thread_messages.set_theme(self.theme)
        self._apply_materials()
        self.refresh_call_bar()
        self.theme_button.setToolTip(f"{self.theme.name.title()} appearance · click to switch")
        for name, action in self.appearance_actions.items():
            action.setChecked(name == mode)
        if persist:
            self.settings.setValue("appearance", mode)
            self.settings.sync()

    def _apply_materials(self):
        from aedrova.desktop.icons import refresh

        refresh(self, self.theme)
        self.build_activity.configure(self.theme, self.reduced_motion, self.build_activity.active)
        self.backdrop.theme = self.theme
        self.backdrop.reduced_transparency = self.reduced_transparency
        self.backdrop.invalidate()
        for panel in self.findChildren(GlassFrame):
            panel.theme = self.theme
            panel.reduced_transparency = self.reduced_transparency
            panel.update()
        for tile in self.findChildren(DocumentTile):
            tile.theme = self.theme
            tile.update()
        for mark in self.findChildren(BrandMark):
            mark.set_reduced_motion(self.reduced_motion)
        for control in self.findChildren(SpringButton):
            control.motion.set_enabled(not self.reduced_motion)

    def set_reduced_motion(self, reduced):
        self.reduced_motion = reduced
        self.build_activity.configure(self.theme, reduced, self.build_activity.active)
        self.settings.setValue("reduceMotion", reduced)
        QApplication.instance().setProperty("reduceMotion", reduced)
        self._apply_materials()

    def set_reduced_transparency(self, reduced):
        self.reduced_transparency = reduced
        self.setStyleSheet(stylesheet(self.theme, reduced_transparency=reduced))
        self.settings.setValue("reduceTransparency", reduced)
        self._apply_materials()

    def toggle_theme(self):
        self.set_theme("light" if self.theme.name == "dark" else "dark")

    def _system_theme_changed(self, scheme):
        if self.theme_mode == "system":
            self.set_theme("system", persist=False)

    def notify(self, text):
        self.notice.setText(text)
        self.notice_timer.start(6500)

    def _reset_notice(self):
        if self.connected and self.connected.active:
            self.notice.setText(
                "Shared chat · syncs every 3 seconds · latest 500 messages · "
                "drafts stay on this device."
            )
            return
        self.notice.setText("Local preview · messages and new spaces reset when the app closes.")

    def workspace_menu(self):
        menu = AppMenu(self)
        for workspace in self.store.workspaces:
            menu.addAction(
                workspace.name, lambda checked=False, wid=workspace.id: self.switch_workspace(wid)
            )
        menu.addSeparator()
        menu.addAction("Create workspace…", self.create_workspace)
        menu.exec(self.workspace_title.mapToGlobal(self.workspace_title.rect().bottomLeft()))

    def open_switcher(self):
        self.dialog = SwitcherDialog(self, self.store)
        self.dialog.chosen.connect(self.jump_to)
        self.dialog.open()
        self.dialog.search.setFocus()

    def jump_to(self, workspace_id, channel_id):
        self.switch_workspace(workspace_id)
        self.switch_channel(channel_id)

    def create_workspace(self):
        self.show_account("create")

    def create_local_workspace(self):
        self.dialog = CreateDialog(
            self,
            workspace=True,
            create=lambda name, topic: self.store.add_workspace(name),
        )
        self.dialog.accepted.connect(lambda: self.switch_workspace(self.dialog.result_object.id))
        self.dialog.open()
        self.dialog.name.setFocus()

    def create_channel(self):
        if self.connected and self.connected.active:
            self.show_account("channel")
            return
        self.dialog = CreateDialog(
            self,
            workspace=False,
            create=lambda name, topic: self.store.add_channel(self.workspace_id, name, topic),
        )
        self.dialog.accepted.connect(lambda: self.switch_channel(self.dialog.result_object.id))
        self.dialog.open()
        self.dialog.name.setFocus()

    def _render_pages(self):
        # Preserve the selected tab when project settings rebuild its contents.
        selected = self.pages.currentIndex()
        builders = (self._project_page, self._builds_page, self._files_page)
        for index, builder in enumerate(builders, 1):
            old = self.pages.widget(index)
            self.pages.removeWidget(old)
            old.deleteLater()
            if self.connected and self.connected.active and index == 2:
                from aedrova.desktop.builds import open_build

                page, layout = self._page(
                    "WORK",
                    "From direction to delivery",
                    "Turn an idea into working code with Codex or Claude, "
                    "grounded in your accessible workspace conversations.",
                )
                layout.addWidget(
                    self._card(
                        "Your next idea starts here",
                        "Mention your agent in conversation, or start here. Your saved project "
                        "permissions govern planning, coding and tests in a separate local copy.",
                        "Start a build",
                        lambda: open_build(self),
                    )
                )
                from aedrova.desktop.build_evidence import SharedBuilds
                from aedrova.desktop.execution import execution_queue

                queue = button("Queue & run history", role="outline")
                queue.clicked.connect(lambda: execution_queue(self).show_history())
                reviews = button("Shared build evidence", role="outline")
                reviews.clicked.connect(lambda: SharedBuilds(self).show())
                layout.addWidget(queue)
                layout.addWidget(reviews)
                layout.addStretch()
                self.pages.insertWidget(index, page)
            elif self.connected and self.connected.active and index == 1:
                from aedrova.desktop.projects import binding, open_editor, open_project

                data = binding(self)
                page, layout = self._page(
                    "YOUR PROJECT",
                    "Your code, connected.",
                    "Connect this workspace to a local project and start builds from conversation.",
                )
                layout.addWidget(
                    label(data.get("folder") or "No project connected yet", "title", wrap=True)
                )
                layout.addWidget(
                    label(
                        data.get("repository")
                        or "GitHub is optional. Connect it when you're ready to publish.",
                        "muted",
                        wrap=True,
                    )
                )
                configure = button(
                    "Project settings" if data else "Connect a project", role="primary"
                )
                configure.clicked.connect(lambda: open_project(self))
                layout.addWidget(configure)
                if data.get("folder"):
                    editor = button("Open project in IDE", role="outline")

                    def edit_project(checked=False):
                        try:
                            open_editor(self, binding(self)["folder"])
                        except (ValueError, OSError) as exc:
                            self.notify(str(exc))

                    editor.clicked.connect(edit_project)
                    layout.addWidget(editor)
                layout.addStretch()
                self.pages.insertWidget(index, page)
            elif self.connected and self.connected.active:
                page, layout = self._page(
                    "YOUR WORKSPACE",
                    ("Projects", "Builds", "Files")[index - 1],
                    "Find the files your team has shared in permitted conversations.",
                )
                browse = button("Browse workspace files", role="primary")
                browse.clicked.connect(lambda: self.collaboration.panel("files"))
                layout.addWidget(browse)
                layout.addStretch()
                self.pages.insertWidget(index, page)
            else:
                self.pages.insertWidget(index, builder())
        self.pages.setCurrentIndex(max(0, selected))
        self._apply_materials()

    def _page(self, eyebrow, title, description):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content.setObjectName("Chat")
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 24, 32, 32)
        layout.setSpacing(16)
        layout.addWidget(label(eyebrow, "section"))
        layout.addWidget(label(title, "heading", wrap=True))
        layout.addWidget(label(description, "muted", wrap=True))
        layout.addSpacing(12)
        return scroll, layout

    def _card(self, title, description, action_text="", action=None):
        card = GlassFrame()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(10)
        layout.addWidget(label(title, "title"))
        layout.addWidget(label(description, "muted", wrap=True))
        if action_text:
            control = button(action_text, role="outline")
            control.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
            control.clicked.connect(action)
            layout.addWidget(control)
        return card

    def _project_page(self):
        page, layout = self._page(
            "PROJECTS",
            "Good ideas deserve a home.",
            "The context, the decisions, and the next thing you're making.",
        )
        hero = GlassFrame(layer="hero")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(30, 30, 30, 30)
        hero_layout.setSpacing(16)
        hero_layout.addWidget(label(f"{self.workspace.name.upper()}  /  SAMPLE PROJECT", "section"))
        hero_layout.addWidget(label("Less setup.\nMore possibility.", "display"))
        hero_layout.addWidget(
            label(
                "A simpler first five minutes. Three thoughtful steps from an idea to a workspace.",
                "muted",
                wrap=True,
            )
        )
        hero_layout.addSpacing(16)
        steps = QHBoxLayout()
        for number, title in (("01", "Workspace"), ("02", "Your team"), ("03", "A project")):
            column = QVBoxLayout()
            column.addWidget(label(number, "section"))
            column.addWidget(label(title))
            steps.addLayout(column)
        hero_layout.addLayout(steps)
        hero_layout.addStretch()
        action = button("Explore the brief  ↗", role="primary")
        action.clicked.connect(lambda: self.show_document("Product brief.md"))
        hero_layout.addWidget(action, alignment=Qt.AlignmentFlag.AlignLeft)
        tile = DocumentTile("Design principles", "A quieter way to work.", "02")
        tile.clicked.connect(lambda: self.show_document("Design principles.md"))
        connection = self._card(
            "Your code, connected.",
            "Repository access is not connected in this local preview.",
        )
        layout.addWidget(AdaptiveBento([hero, tile, connection], asymmetric=True))
        layout.addStretch()
        return page

    def _builds_page(self):
        page, layout = self._page(
            "WORKSPACE / BUILDS",
            "From a decision to a working change.",
            "Plans, progress and reviews in a connected workspace.",
        )
        layout.addWidget(
            self._card(
                "Ready when your team is.",
                "No builds have run. In a connected workspace, mention @Aedrova in a conversation "
                "to propose a plan. You stay in control of what gets pushed.",
                "Go to the conversation  →",
                lambda: self.select_tab(0),
            )
        )
        layout.addWidget(label("Agent execution isn’t connected in this preview.", "muted"))
        layout.addStretch()
        return page

    def _files_page(self):
        page, layout = self._page(
            "FILES",
            "A little shared understanding.",
            "The references behind the work. Open a sample document to take a closer look.",
        )
        tiles = []
        for number, name, title, description in (
            ("01", "Product brief.md", "Product brief", "Purpose, scope, and the next step."),
            (
                "02",
                "Design principles.md",
                "Design principles",
                "Simple. Considered. Quietly useful.",
            ),
        ):
            tile = DocumentTile(title, description, number)
            tile.clicked.connect(lambda checked=False, file=name: self.show_document(file))
            tiles.append(tile)
        layout.addWidget(AdaptiveBento(tiles))
        layout.addStretch()
        return page

    def start_channel_call(self, mode):
        from aedrova.desktop.meeting_call import open_channel_call

        open_channel_call(self, mode=mode)

    def refresh_call_bar(self, meeting=None):
        from PySide6.QtGui import QColor

        from aedrova.desktop.meeting_icons import meeting_icon

        if not hasattr(self, "call_buttons"):
            return
        if meeting is None:
            from aedrova.desktop.meeting_activity import current_meetings

            meeting = next(
                (m for m in current_meetings(self) if m["channel_id"] == self.channel_id), None
            )
        for kind, control in self.call_buttons.items():
            control.setIcon(meeting_icon(kind, QColor(self.theme.text)))
            control.setIconSize(QSize(20, 20))
            if kind != "settings":
                title = ("Join" if meeting else "Start") + (
                    " audio call" if kind == "phone" else " video call"
                )
                control.setToolTip(title)
                control.setAccessibleName(title)
        count = len((meeting or {}).get("participants", []))
        self.call_count.setVisible(bool(meeting))
        self.call_count.setText(str(count))
        self.call_count.setToolTip(f"{count} participants in this channel’s call")
        self.call_count.setAccessibleName(f"{count} call participants")

    def open_call_options(self):
        from aedrova.desktop.meeting_setup import open_meeting_setup

        menu = AppMenu(self)
        menu.addAction("Check meeting devices…", lambda: open_meeting_setup(self))
        menu.addAction("Meeting settings & transcripts…", self.open_meeting_hub)
        self.call_options = menu
        menu.popup(
            self.call_buttons["settings"].mapToGlobal(
                self.call_buttons["settings"].rect().bottomRight()
            )
        )

    def open_meeting_hub(self):
        existing = getattr(self, "meeting_hub", None)
        if existing:
            existing.reject()
            existing.deleteLater()
        dialog = AppDialog(self)
        dialog.setWindowTitle("Meeting settings")
        dialog.resize(760, 680)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._meetings_page())
        done = button("Done", role="primary")
        done.clicked.connect(dialog.accept)
        layout.addWidget(done, alignment=Qt.AlignmentFlag.AlignRight)
        self.meeting_hub = dialog
        self.meeting_hub_scope = (self.workspace_id, self.channel_id)
        account = getattr(self, "account_dialog", None)
        if account:
            account.session_closed.connect(dialog.reject)
        dialog.show()

    def _meetings_page(self):
        self.meeting_destination = None
        from aedrova.desktop.meeting_setup import open_meeting_setup

        page, layout = self._page(
            "WORKSPACE / MEETINGS",
            "Make room for the conversation.",
            "Meet in this channel. Device checks are local; calls require the meeting service.",
        )
        layout.addWidget(
            self._card(
                "Together, in the same room.",
                "Start a call from a channel, share your screen, and keep the decisions close "
                "to the work. Transcription and AI access will always be explicit choices.",
                "Check meeting devices",
                lambda: open_meeting_setup(self),
            )
        )
        from aedrova.desktop.meeting_activity import MeetingAction, current_meetings
        from aedrova.desktop.meeting_call import open_channel_call

        active = next(
            (m for m in current_meetings(self) if m["channel_id"] == self.channel_id), None
        )
        self.meeting_action_layout = QVBoxLayout()
        self.meeting_action_layout.addWidget(
            MeetingAction(self.theme, active, lambda: open_channel_call(self))
        )
        layout.addLayout(self.meeting_action_layout)
        if self.connected and self.connected.active:
            from aedrova.desktop.controls import ChoiceBox

            layout.addWidget(label("Meeting announcements", "section"))
            destinations = ChoiceBox()
            self.meeting_destination = destinations
            destinations.setAccessibleName("Meeting announcement channel")
            public = [
                c
                for c in self.account_dialog.snapshot.get("channels", [])
                if c["workspace_id"] == self.workspace_id
                and not c.get("private")
                and c.get("kind", "channel") == "channel"
            ]
            for channel in public:
                destinations.addItem("#" + channel["name"], channel["id"])
            preferences = self.account_dialog.snapshot.get("meeting_activity", {}).get(
                "preferences", []
            )
            selected = next(
                (
                    p["announcement_channel"]
                    for p in preferences
                    if p["workspace_id"] == self.workspace_id
                ),
                None,
            )
            selected = selected or next((c["id"] for c in public if c["name"] == "general"), None)
            destinations.setCurrentIndex(max(0, destinations.findData(selected)))
            admin = any(
                m["workspace_id"] == self.workspace_id
                and m["user_id"] == str(self.current_user().id)
                and m["role"] in ("owner", "admin")
                for m in self.account_dialog.snapshot.get("members", [])
            )
            destinations.setEnabled(
                admin
                and not self.account_dialog.snapshot.get("meeting_activity", {}).get(
                    "setup_required"
                )
            )
            workspace = self.workspace_id

            def save_destination(_):
                channel = destinations.currentData()
                self.connected.enqueue(
                    ("meeting-channel", workspace),
                    lambda: self.account_dialog.service.rpc(
                        "set_meeting_announcement_channel",
                        {"p_workspace": workspace, "p_channel": channel},
                    ),
                    lambda _: self.connected.refresh(),
                )

            destinations.activated.connect(save_destination)
            layout.addWidget(destinations)
            layout.addWidget(
                label(
                    "Public meetings appear here and in their own channel. "
                    "Private meetings stay in their private channel.",
                    "muted",
                    wrap=True,
                )
            )
        service = getattr(getattr(self, "account_dialog", None), "service", None)
        if getattr(service, "meeting_context_enabled", False):
            from aedrova.desktop.meeting_transcript import open_transcript_history

            history = button("Review meeting transcripts", role="outline")
            history.clicked.connect(lambda: open_transcript_history(self))
            layout.addWidget(history)

        layout.addWidget(
            label(
                "Your devices stay off until you enable a check. No checks are recorded.",
                "muted",
                wrap=True,
            )
        )
        layout.addStretch()
        return page

    def show_document(self, name):
        content = {
            "Product brief.md": (
                "PRODUCT BRIEF · SAMPLE DOCUMENT\n\nOnboarding refresh\n\n"
                "Purpose\nHelp a new team reach its workspace before asking for optional setup.\n\n"
                "Three steps\n1. Create a workspace\n2. Invite teammates (optional)\n"
                "3. Connect a project\n\nAcceptance criteria\n"
                "• Existing Google sign-in continues to work.\n• Invitations can be skipped.\n"
                "• Each screen has one primary action.\n• Existing sessions remain valid.\n\n"
                "Source\nSample discussion in #product. This document is a UI fixture."
            ),
            "Design principles.md": (
                "DESIGN PRINCIPLES · SAMPLE DOCUMENT\n\nQuiet by design\n\n"
                "Keep conversation at the center. Use space, typography and restrained color "
                "to establish hierarchy.\n\nFamiliar, with less friction\n\n"
                "Channels hold discussions. Tabs offer views. Threads keep details close "
                "without interrupting the conversation.\n\nHuman control\n\n"
                "Aedrova waits to be invited. Important external actions require approval."
            ),
        }
        self.dialog = AppDialog(self)
        self.dialog.setWindowTitle(name)
        self.dialog.resize(620, 560)
        layout = QVBoxLayout(self.dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addWidget(label(name, "title"))
        editor = QPlainTextEdit(content[name])
        editor.setReadOnly(True)
        editor.setAccessibleName(f"Sample document: {name}")
        layout.addWidget(editor)
        close = button("Done", role="primary")
        close.clicked.connect(self.dialog.accept)
        layout.addWidget(close, alignment=Qt.AlignmentFlag.AlignRight)
        self.dialog.open()

    def show_about(self):
        self.dialog = AppDialog(self)
        self.dialog.setWindowTitle("About Aedrova")
        self.dialog.resize(480, 430)
        layout = QVBoxLayout(self.dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addWidget(BrandMark(112), 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(label("Aedrova", "heading"))
        layout.addWidget(label("Where teams and AI build together.", "muted"))
        layout.addWidget(label("Internal preview", "muted"))
        layout.addWidget(
            label(
                "Your team’s conversations, shared context and coding agent in one workspace. "
                "Aedrova is being prepared for release. Service availability depends on setup. "
                "Local sample workspaces use preview data; your appearance and accessibility "
                "preferences are saved on this Mac.",
                wrap=True,
            )
        )
        done = button("Got it", role="primary")
        done.clicked.connect(self.dialog.accept)
        layout.addWidget(done)
        self.dialog.open()

    def current_user(self):
        account = getattr(self, "account_dialog", None)
        return account.service.user if account and account.service else None

    def update_profile_button(self):
        user = self.current_user()
        metadata = getattr(user, "user_metadata", None) or {}
        profile = getattr(getattr(self, "account_dialog", None), "snapshot", {}).get(
            "user_profile", {}
        )
        name = (
            profile.get("display_name")
            or metadata.get("full_name")
            or getattr(user, "email", "")
            or ""
        )
        initials = "".join(part[0] for part in name.split()[:2]).upper() if name else "○"
        self.profile_button.setText(initials)
        self.profile_button.setIcon(QIcon())
        path = profile.get("avatar_path")
        collaboration = getattr(self, "collaboration", None)
        if path and collaboration:

            def photo_loaded(photo):
                current = getattr(self.account_dialog, "snapshot", {}).get("user_profile", {})
                if self.current_user() and current.get("avatar_path") == path:
                    self.profile_button.setText("")
                    self.profile_button.setIcon(QIcon(photo))
                    self.profile_button.setIconSize(QSize(34, 34))

            collaboration.load_avatar(path, photo_loaded)
        self.profile_button.setToolTip(name or "Sign in or open settings")

    def open_profile_menu(self):
        self.update_profile_button()
        menu = AppMenu(self)
        user = self.current_user()
        if user:
            identity = menu.addAction(getattr(user, "email", None) or "Signed in")
            identity.setEnabled(False)
            menu.addSeparator()
        if user:
            from aedrova.desktop.profile import open_profile_editor

            menu.addAction("Edit profile…", lambda: open_profile_editor(self))
        menu.addAction("Settings…", self.show_settings)
        if user:
            menu.addAction("Workspace settings…", lambda: self.show_account("manage"))
            menu.addAction("Connectors…", self.open_connectors)
            menu.addAction("Invite teammates…", lambda: self.show_account("invite"))
            menu.addSeparator()
            menu.addAction("Log out", self.log_out)
        else:
            menu.addAction("Sign in with Google…", self.show_account)
        self.profile_menu = menu
        menu.popup(self.profile_button.mapToGlobal(self.profile_button.rect().topRight()))

    def open_connectors(self):
        from aedrova.desktop.bud_connectors import open_connectors

        open_connectors(self)

    def show_settings(self):
        from aedrova.desktop.preferences import SettingsDialog

        self.preferences_dialog = SettingsDialog(self)
        self.preferences_dialog.show()

    def log_out(self):
        account = getattr(self, "account_dialog", None)
        if not self.current_user():
            self.show_account()
            return
        if account.busy:
            self.notify("Finishing the current request. Try Log out again in a moment.")
            return
        build = getattr(self, "build_dialog", None)
        drafts = self.composer.editor.toPlainText() or self.thread_composer.editor.toPlainText()
        if (build and build.pending) or drafts or any(self.store.drafts.values()):
            choice = QMessageBox.question(
                self,
                "Log out of Aedrova?",
                "Active builds will stop and unsent drafts will be cleared. Local build "
                "files remain.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if choice != QMessageBox.StandardButton.Yes:
                return
        account.show()
        if self.tour:
            self.tour.finish("paused")
        if getattr(self, "setup_dialog", None):
            self.setup_dialog.close()
        account.sign_out()
        self.update_profile_button()

    def show_account(self, intent=None):
        from aedrova.desktop.account import AccountDialog

        if not hasattr(self, "account_dialog"):
            self.account_dialog = AccountDialog(self, settings=self.settings)
            self.account_dialog.dashboard_requested.connect(self.open_dashboard)
        self.account_dialog.pending_intent = intent
        if self.connected and self.connected.active:
            self.account_dialog.pending_workspace = self.workspace_id
        if self.account_dialog.service and self.account_dialog.service.user:
            if not self.account_dialog.busy:
                self.account_dialog.refresh()
        self.account_dialog.show()
        self.account_dialog.raise_()
        self.account_dialog.activateWindow()

    def open_dashboard(self):
        account = self.account_dialog
        self.update_profile_button()
        if account.service and account.service.user:
            if self.connected is None:
                from aedrova.desktop.connected import ConnectedDashboard

                self.connected = ConnectedDashboard(self, account)
            self.connected.activate()
            self.select_tab(0)
            QTimer.singleShot(0, self.offer_setup)
            return
        # Explicit local-preview navigation remains available in demo mode.
        self.select_tab(0)
        self.show()
        self.raise_()
        self.activateWindow()

    def offer_github_setup(self):
        if self.current_user() and self.connected and self.connected.active:
            from aedrova.desktop.github_setup import open_github_setup

            open_github_setup(self)

    def offer_setup(self):
        from aedrova.desktop.onboarding import account_key

        key = account_key(self)
        if not self.current_user() or getattr(self, "setup_offered", None) == key:
            return
        self.setup_offered = key
        if not self.settings.value(key + "/setup", False, type=bool) and not self.settings.value(
            key + "/deferred", False, type=bool
        ):
            self.show_setup()

    def show_setup(self):
        from aedrova.desktop.onboarding import SetupDialog

        if self.tour:
            self.tour.finish("paused")
        existing = getattr(self, "setup_dialog", None)
        if existing and existing.timer.isActive():
            if existing.isVisible():
                existing.raise_()
                existing.activateWindow()
            return
        self.setup_dialog = SetupDialog(self)
        self.setup_dialog.show()
        self.setup_dialog.raise_()

    def show_tour(self):
        from aedrova.desktop.onboarding import SpotlightTour

        if self.tour:
            self.tour.raise_()
            return
        self.tour = SpotlightTour(self)

    def show_updates(self):
        from aedrova.desktop.release_check import ReleaseDialog

        self.release_dialog = ReleaseDialog(self)
        self.release_dialog.show()
