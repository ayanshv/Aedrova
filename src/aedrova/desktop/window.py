"""Milestone 2 desktop shell. Local fixtures only; service work starts in milestone 3."""

from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import QAction, QActionGroup, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QPlainTextEdit,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from aedrova.desktop.brand import BrandMark, app_icon
from aedrova.desktop.conversation import Composer, MessageView
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
        self.workspace_buttons = {}
        self.tab_buttons = []
        self._build_shell()
        self._menus()
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
        top.setFixedHeight(68)
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(28, 0, 24, 0)
        identity = QWidget()
        identity.setFixedWidth(240)
        identity_layout = QHBoxLayout(identity)
        identity_layout.setContentsMargins(0, 0, 0, 0)
        identity_layout.setSpacing(9)
        identity_layout.addWidget(BrandMark(44))
        brand = label("Aedrova")
        brand.setStyleSheet("font-size: 19px; font-weight: 600;")
        identity_layout.addWidget(brand)
        identity_layout.addStretch()
        top_layout.addWidget(identity)
        self.sidebar_toggle = button("☷", "Toggle channel sidebar", "icon")
        self.sidebar_toggle.setFixedSize(34, 34)
        self.sidebar_toggle.setToolTip("Show or hide channels")
        self.sidebar_toggle.clicked.connect(self.toggle_sidebar)
        top_layout.addWidget(self.sidebar_toggle)
        self.search_button = button(
            "Jump to a conversation                      ⌘ K",
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
        top_layout.addWidget(label("Local preview", "badge"), 0, Qt.AlignmentFlag.AlignVCenter)
        self.theme_button = button("◐", "Toggle light and dark appearance", "icon")
        self.theme_button.setFixedSize(34, 34)
        self.theme_button.clicked.connect(self.toggle_theme)
        top_layout.addWidget(self.theme_button)
        vertical.addWidget(top)
        body = QHBoxLayout()
        body.setContentsMargins(12, 0, 20, 0)
        body.setSpacing(14)
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
        rail_content.setAutoFillBackground(False)
        rail_scroll.viewport().setAutoFillBackground(False)
        rail_outer.addWidget(rail_scroll, 1)
        self.create_workspace_button = button("+", "Create workspace", "workspace")
        self.create_workspace_button.setFixedSize(44, 44)
        self.create_workspace_button.setToolTip("Create a local workspace")
        self.create_workspace_button.clicked.connect(self.create_workspace)
        rail_outer.addWidget(self.create_workspace_button)
        profile = label("AV", "badge")
        profile.setAlignment(Qt.AlignmentFlag.AlignCenter)
        profile.setFixedSize(42, 32)
        profile.setToolTip("You · local preview profile")
        rail_outer.addSpacing(15)
        rail_outer.addWidget(profile)
        body.addWidget(rail)
        self.sidebar = GlassFrame(layer="sidebar")
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(222)
        side = QVBoxLayout(self.sidebar)
        side.setContentsMargins(14, 24, 14, 22)
        side.setSpacing(8)
        self.workspace_title = button("Northstar Labs  ⌄", "Select workspace")
        self.workspace_title.setStyleSheet("font-size: 16px; font-weight: 600; padding-left: 6px;")
        self.workspace_title.clicked.connect(self.workspace_menu)
        side.addWidget(self.workspace_title)
        subtitle = label("Team workspace", "muted")
        subtitle.setContentsMargins(7, 0, 0, 0)
        side.addWidget(subtitle)
        side.addSpacing(30)
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
        side.addWidget(self.channel_list)
        side.addSpacing(18)
        side.addWidget(label("DIRECT MESSAGES", "section"))
        self.dm_list = QListWidget()
        self.dm_list.setObjectName("Navigation")
        self.dm_list.setAccessibleName("Direct conversations")
        self.dm_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.dm_list.currentItemChanged.connect(self._channel_selected)
        side.addWidget(self.dm_list)
        side.addStretch(1)
        quiet = QFrame()
        quiet.setObjectName("Quiet")
        quiet_layout = QVBoxLayout(quiet)
        quiet_layout.setContentsMargins(8, 20, 8, 10)
        quiet_layout.setSpacing(7)
        presence = QHBoxLayout()
        presence.addWidget(BrandMark(46))
        presence.addWidget(label("Aedrova"))
        presence.addStretch()
        quiet_layout.addLayout(presence)
        quiet_layout.addWidget(label("Quiet until you need it.", "muted"))
        quiet_layout.addWidget(label("From a thought to a thing.", "muted"))
        side.addWidget(quiet)
        side.addSpacing(8)
        side.addWidget(label("Preview · changes stay on this Mac", "muted", wrap=True))
        body.addWidget(self.sidebar)
        main = GlassFrame(layer="main")
        self.main_surface = main
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.header = QFrame()
        self.header.setObjectName("ChannelHeader")
        self.header.setFixedHeight(112)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(32, 22, 32, 16)
        heading = QVBoxLayout()
        heading.setSpacing(5)
        self.channel_title = label("Product", "display")
        self.channel_title.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.channel_topic = label("", "muted")
        self.channel_topic.setWordWrap(True)
        heading.addWidget(self.channel_title)
        heading.addWidget(self.channel_topic)
        header_layout.addLayout(heading, 1)
        self.members_label = label("AM   MC   SR   + You", "muted")
        self.members_label.setToolTip("Sample conversation participants")
        header_layout.addWidget(self.members_label)
        main_layout.addWidget(self.header)
        tab_area = QWidget()
        tab_area_layout = QHBoxLayout(tab_area)
        tab_area_layout.setContentsMargins(30, 0, 30, 14)
        tabs = QWidget()
        tabs.setObjectName("Segments")
        tabs_layout = QHBoxLayout(tabs)
        tabs_layout.setContentsMargins(4, 4, 4, 4)
        tabs_layout.setSpacing(2)
        for index, title in enumerate(("Chat", "Projects", "Builds", "Files", "Meetings")):
            tab = button(title, f"Open {title.lower()} tab", "tab")
            tab.setCheckable(True)
            tab.clicked.connect(lambda checked=False, i=index: self.select_tab(i))
            self.tab_buttons.append(tab)
            tabs_layout.addWidget(tab)
        tab_area_layout.addWidget(tabs)
        tab_area_layout.addStretch()
        main_layout.addWidget(tab_area)
        self.pages = QStackedWidget()
        main_layout.addWidget(self.pages, 1)
        body.addWidget(main, 1)
        self._build_chat()
        for _ in range(4):
            self.pages.addWidget(QWidget())
        self.select_tab(0)
        self.notice = label(
            "Local preview · messages and new spaces reset when the app closes.", "muted"
        )
        self.notice.setContentsMargins(30, 9, 30, 9)
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
        date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        date.setContentsMargins(0, 20, 0, 10)
        chat.addWidget(date)
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
        empty_layout.addWidget(label("Every good idea starts\nwith a conversation.", "heading"))
        empty_layout.addWidget(label("Send the first message in this local preview.", "muted"))
        empty_layout.addStretch()
        self.message_stack.addWidget(empty)
        chat.addWidget(self.message_stack, 1)
        compose_area = QWidget()
        composition = QVBoxLayout(compose_area)
        composition.setContentsMargins(28, 12, 28, 18)
        composition.setSpacing(9)
        self.composer = Composer()
        self.composer.submitted.connect(self.send_message)
        composition.addWidget(self.composer)
        footer = label("Aedrova stays quiet until you mention it.", "muted")
        composition.addWidget(footer)
        chat.addWidget(compose_area)
        row.addWidget(self.chat_column, 1)
        self.thread_panel = GlassFrame(layer="thread", radius=22)
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
        row.setContentsMargins(0, 0, 12, 8)
        self.thread_panel.hide()
        self.pages.addWidget(self.chat_page)

    def _menus(self):
        workspace_menu = self.menuBar().addMenu("Workspace")
        workspace_menu.addAction("New workspace…", self.create_workspace)
        workspace_menu.addAction("New channel…", self.create_channel)
        view = self.menuBar().addMenu("View")
        jump = view.addAction("Jump to conversation…", self.open_switcher)
        jump.setShortcut(QKeySequence("Ctrl+K"))
        view.addAction("Toggle sidebar", self.toggle_sidebar)
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
        for i in range(5):
            shortcut = QShortcut(QKeySequence(f"Ctrl+{i + 1}"), self)
            shortcut.activated.connect(lambda index=i: self.select_tab(index))
        theme_shortcut = QShortcut(QKeySequence("Ctrl+Shift+L"), self)
        theme_shortcut.activated.connect(self.toggle_theme)
        escape = QShortcut(QKeySequence("Escape"), self)
        escape.activated.connect(self.close_thread)
        account_menu = self.menuBar().addMenu("Account")
        account_menu.addAction("Account & workspaces…", self.show_account)
        help_menu = self.menuBar().addMenu("Help")
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
            item.setToolTip(workspace.name)
            item.clicked.connect(lambda checked=False, wid=workspace.id: self.switch_workspace(wid))
            self.workspace_buttons[workspace.id] = item
            self.rail_items.addWidget(item)

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
        self._save_drafts()
        self.last_channels[self.workspace_id] = self.channel_id
        self.workspace_id = workspace_id
        self.channel_id = self.last_channels.get(workspace_id, self.workspace.channels[0].id)
        self.thread_id = ""
        self.thread_panel.hide()
        self.chat_column.show()
        self._populate_rail()
        self._populate_channels()
        self._load_channel()
        self._render_pages()
        self.select_tab(0)

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

    def _load_channel(self):
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
        self.message_stack.setCurrentIndex(0 if channel.messages else 1)
        self.pinned.setVisible(any(m.decision for m in channel.messages))
        self.composer.editor.setPlaceholderText(
            f"Message {' ' if channel.direct else '#'}{channel.name}…"
        )
        self.composer.editor.setPlainText(
            self.store.drafts.get((self.workspace_id, self.channel_id, ""), "")
        )

    def open_pinned(self):
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
            self.members_label.setVisible(self.width() >= 1100)

    def send_message(self, text):
        try:
            message = self.store.send(self.workspace_id, self.channel_id, text)
        except ValueError as exc:
            self.notify(str(exc))
            return
        self.messages.conversation_model.append(message)
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
        if not self.thread_id:
            return
        try:
            self.store.send(self.workspace_id, self.channel_id, text, self.thread_id)
        except ValueError as exc:
            self.notify(str(exc))
            return
        parent = next(m for m in self.channel.messages if m.id == self.thread_id)
        self.thread_messages.show_messages([parent, *parent.replies])
        self.thread_title.setText(f"Thread · {len(parent.replies)} replies")
        self.messages.conversation_model.refresh(self.thread_id)
        self.messages.scheduleDelayedItemsLayout()
        self.thread_composer.clear()
        self.store.drafts[(self.workspace_id, self.channel_id, self.thread_id)] = ""
        QTimer.singleShot(0, self.thread_messages.scrollToBottom)
        self.notify("Reply added to this local preview.")

    def select_tab(self, index):
        if not 0 <= index < len(self.tab_buttons):
            return
        self.pages.setCurrentIndex(index)
        for i, tab in enumerate(self.tab_buttons):
            tab.setChecked(i == index)
        if index == 0 and hasattr(self, "thread_panel"):
            self._adapt_thread()

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
        self.setPalette(palette(self.theme))
        self.setStyleSheet(stylesheet(self.theme, reduced_transparency=self.reduced_transparency))
        self.messages.set_theme(self.theme)
        self.thread_messages.set_theme(self.theme)
        self._apply_materials()
        self.theme_button.setToolTip(f"{self.theme.name.title()} appearance · click to switch")
        for name, action in self.appearance_actions.items():
            action.setChecked(name == mode)
        if persist:
            self.settings.setValue("appearance", mode)
            self.settings.sync()

    def _apply_materials(self):
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
        self.notice.setText("Local preview · messages and new spaces reset when the app closes.")

    def workspace_menu(self):
        menu = QMenu(self)
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
        self.dialog = CreateDialog(
            self,
            workspace=True,
            create=lambda name, topic: self.store.add_workspace(name),
        )
        self.dialog.accepted.connect(lambda: self.switch_workspace(self.dialog.result_object.id))
        self.dialog.open()
        self.dialog.name.setFocus()

    def create_channel(self):
        self.dialog = CreateDialog(
            self,
            workspace=False,
            create=lambda name, topic: self.store.add_channel(self.workspace_id, name, topic),
        )
        self.dialog.accepted.connect(lambda: self.switch_channel(self.dialog.result_object.id))
        self.dialog.open()
        self.dialog.name.setFocus()

    def _render_pages(self):
        # Replace fixture pages when changing workspace; no background integrations.
        builders = (self._project_page, self._builds_page, self._files_page, self._meetings_page)
        for index, builder in enumerate(builders, 1):
            old = self.pages.widget(index)
            self.pages.removeWidget(old)
            old.deleteLater()
            self.pages.insertWidget(index, builder())
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
            "Plans, progress, and reviews will live here.",
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

    def _meetings_page(self):
        page, layout = self._page(
            "WORKSPACE / MEETINGS",
            "Make room for the conversation.",
            "Calls and meeting context are coming in a later release.",
        )
        layout.addWidget(
            self._card(
                "Together, in the same room.",
                "Start a call from a channel, share your screen, and keep the decisions close "
                "to the work. Transcription and AI access will always be explicit choices.",
            )
        )
        layout.addWidget(
            label(
                "No microphone, camera, or recording is active in this preview.", "muted", wrap=True
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
        self.dialog = QDialog(self)
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
        self.dialog = QDialog(self)
        self.dialog.setWindowTitle("About Aedrova preview")
        self.dialog.resize(440, 250)
        layout = QVBoxLayout(self.dialog)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addWidget(BrandMark(112), 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(label("Aedrova", "heading"))
        layout.addWidget(label("Where teams and AI build together.", "muted"))
        layout.addWidget(label("Milestone 2 · Desktop experience", "muted"))
        layout.addWidget(
            label(
                "This is an interactive local preview. Sample conversations and new messages "
                "stay in memory and reset when the app closes. Your appearance and accessibility "
                "preferences "
                "are saved. Account setup is available in the Account menu. Shared chat, agents, "
                "billing, and calls are not connected.",
                wrap=True,
            )
        )
        done = button("Got it", role="primary")
        done.clicked.connect(self.dialog.accept)
        layout.addWidget(done)
        self.dialog.open()

    def show_account(self):
        from aedrova.desktop.account import AccountDialog

        if not hasattr(self, "account_dialog"):
            self.account_dialog = AccountDialog(self, settings=self.settings)
        elif self.account_dialog.service and self.account_dialog.service.user:
            self.account_dialog.refresh()
        self.account_dialog.show()
        self.account_dialog.raise_()
        self.account_dialog.activateWindow()
