"""Native connector gallery with real verification and per-account access management."""

import re
import time
from urllib.parse import urlencode, urlparse

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from aedrova.agents.managed import connector_origin
from aedrova.desktop.ai_teammates import Character
from aedrova.desktop.connector_icons import connector_pixmap
from aedrova.desktop.controls import AppDialog, ChoiceBox
from aedrova.desktop.dialogs import button, label
from aedrova.desktop.dots import DotDialog
from aedrova.dots.client import client
from aedrova.dots.roles import ROLES, recommendation_set, role_for

HELP = {
    "github": (
        "Use a fine-grained GitHub token for this repository only. Read: Metadata, "
        "Contents, Issues, Pull requests and Deployments."
    ),
    "supabase": (
        "Use a Supabase Management API personal access token. Only project metadata is "
        "retrieved; no database rows or API keys."
    ),
    "figma": (
        "Use a Figma personal access token with file_content:read for an accessible "
        "file. Enter its file key, not its URL."
    ),
    "notion": (
        "Use an internal Notion integration token with Read content, and share only "
        "this page with the integration."
    ),
    "stripe": (
        "Use a restricted Stripe key (rk_test_ or rk_live_) with read access to Account "
        "and Balance. Enter the matching acct_ account ID."
    ),
    "instagram": (
        "Use an Instagram Login access token with instagram_business_basic for a "
        "Business or Creator account. Enter the Instagram user ID. Provider app "
        "approval is required for public use."
    ),
    "tiktok": (
        "Use a TikTok Display API user access token with user.info.basic and "
        "video.list. Enter its matching open_id. Provider app approval is required for "
        "public use."
    ),
    "search": (
        "Use a Brave Search API subscription token. Enter a research topic. Searches "
        "use your provider allowance; up to five snippets are retrieved."
    ),
    "vercel": (
        "Use a Vercel access token scoped to the appropriate team. Enter its prj_ "
        "project ID. Only project metadata and deployments are retrieved."
    ),
}
RESOURCE_HELP = {
    "github": (
        "Open your repository on GitHub. From github.com/owner/repository, copy owner/repository."
    ),
    "supabase": "Open your project in Supabase → Project Settings → General → Reference ID. "
    "You can also copy the value after /project/ in the dashboard URL. "
    "Paste only the project reference, not a password or API key.",
    "figma": (
        "Open your Figma file. Copy the key after /design/ or /file/ in its URL, "
        "before the file name."
    ),
    "notion": "Open the shared Notion page → Share → Copy link. Copy the 32-character page ID "
    "at the end of the path, with or without hyphens; leave out the query string.",
    "stripe": (
        "Open Stripe → Settings → Business → Account details. Copy your account ID beginning acct_."
    ),
    "instagram": "Use the Instagram user ID returned by your authorized professional account’s "
    "profile API. This is a numeric ID, not your @handle.",
    "tiktok": "For browser sign-in, enter me to select the authorized TikTok account. "
    "For a scoped token, use open_id from TikTok’s authorization token response. "
    "This is not your username.",
    "search": (
        "Enter the topic your Bud should research, such as competitor pricing. "
        "No project ID is needed."
    ),
    "vercel": (
        "Open your Vercel project → Settings → General → Project ID. Copy the value beginning prj_."
    ),
}

GLYPHS = {
    "github": "GH",
    "supabase": "↯",
    "figma": "F",
    "notion": "N",
    "stripe": "S",
    "instagram": "◎",
    "tiktok": "♪",
    "search": "⌕",
    "vercel": "▲",
}


def normalize_resource(provider, value):
    """Accept ordinary provider links without widening the authorized resource scope."""
    value = value.strip()
    if "://" not in value:
        return value
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.username or parsed.password:
        raise ValueError("Paste a secure provider link without credentials.")
    host, parts = (parsed.hostname or "").lower(), parsed.path.strip("/").split("/")
    if provider == "github" and host == "github.com" and len(parts) >= 2:
        return "/".join(parts[:2]).removesuffix(".git")
    if (
        provider == "figma"
        and host in {"figma.com", "www.figma.com"}
        and len(parts) >= 2
        and parts[0] in {"file", "design", "board"}
    ):
        return parts[1]
    if provider == "supabase" and host == "supabase.com" and "project" in parts:
        index = parts.index("project") + 1
        if index < len(parts):
            return parts[index]
    if provider == "notion" and (
        host == "notion.so" or host.endswith(".notion.so") or host.endswith(".notion.site")
    ):
        match = re.search(
            r"([a-fA-F0-9]{32}|[a-fA-F0-9]{8}(?:-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12})$", parts[-1]
        )
        if match:
            return match.group(1)
    raise ValueError("Use a link to the selected provider’s resource, or its resource ID.")


class ConnectorsDialog(AppDialog):
    run = DotDialog.run

    def __init__(self, window, selected=None, *, on_change=None, embedded_owner=None):
        super().__init__(embedded_owner or window)
        self.embedded_owner = embedded_owner
        if embedded_owner is not None:
            self.setWindowFlags(Qt.WindowType.Widget)
        self.window, self.workspace = window, window.workspace_id
        self.user = str(window.current_user().id)
        self.job, self.pending = None, False
        self.rows, self.providers = [], []
        self.selected, self.selected_provider, self.on_change = selected, None, on_change
        self.role_target = None
        self.cards, self.grid_layouts = [], []
        self.oauth_state, self.oauth_deadline = "", 0
        self.oauth_timer = QTimer(self)
        self.oauth_timer.setInterval(3000)
        self.oauth_timer.timeout.connect(self.poll_oauth)
        self.setObjectName("EmbeddedConnectors" if embedded_owner else "Connectors")
        self.setWindowTitle("Aedrova · Connectors")
        self.setMinimumSize(0 if embedded_owner else 760, 0 if embedded_owner else 620)
        if embedded_owner is None:
            self.resize(1120, 820)
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        rail = QFrame(self)
        rail.setObjectName("ConnectorRail")
        rail.setFixedWidth(180)
        navigation = QVBoxLayout(rail)
        navigation.setContentsMargins(18, 28, 18, 24)
        back = button("‹  Back to app")
        back.clicked.connect(self.accept)
        navigation.addWidget(back)
        navigation.addSpacing(22)
        navigation.addWidget(label("WORKSPACE", "muted"))
        navigation.addWidget(label("Connectors", "subheading"))
        navigation.addWidget(label("Your tools.\nYour Buds.", "muted", wrap=True))
        navigation.addStretch()
        navigation.addWidget(
            label("Your account’s access\nRead-only connections", "muted", wrap=True)
        )
        root.addWidget(rail)
        rail.setVisible(embedded_owner is None)
        main = QVBoxLayout()
        main.setContentsMargins(0, 0, 0, 0) if embedded_owner else main.setContentsMargins(
            30, 28, 30, 24
        )
        main.setSpacing(12 if embedded_owner else 18)
        root.addLayout(main, 1)
        header = QHBoxLayout()
        header.addWidget(label("Connectors", "heading"))
        header.addStretch()
        refresh = button("Refresh")
        refresh.clicked.connect(self.refresh)
        header.addWidget(refresh)
        main.addLayout(header)
        controls = QHBoxLayout()
        self.bud = ChoiceBox(self)
        self.bud.setAccessibleName("Bud to connect")
        self.bud.currentIndexChanged.connect(self.bud_changed)
        self.filter = ChoiceBox(self)
        self.filter.addItem("All tools", "all")
        for key, (name, _, _) in ROLES.items():
            self.filter.addItem(name + " tools", key)
        self.filter.currentIndexChanged.connect(self.rebuild_gallery)
        self.search = QLineEdit(self)
        self.search.setPlaceholderText("Find a connector…")
        self.search.setAccessibleName("Search connectors")
        self.search.textChanged.connect(self.rebuild_gallery)
        controls.addWidget(self.bud, 1)
        controls.addWidget(self.filter)
        controls.addWidget(self.search, 1)
        main.addLayout(controls)
        self.bud.setVisible(embedded_owner is None)
        self.pages = QStackedWidget(self)
        main.addWidget(self.pages, 1)
        self.gallery = QScrollArea(self)
        self.gallery.setWidgetResizable(True)
        self.gallery.setFrameShape(QFrame.Shape.NoFrame)
        self.gallery.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.pages.addWidget(self.gallery)
        detail = QWidget(self)
        form = QVBoxLayout(detail)
        form.setContentsMargins(0, 4, 0, 4)
        form.setSpacing(14)
        back_tools = button("‹  All connectors")
        back_tools.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        form.addWidget(back_tools, alignment=Qt.AlignmentFlag.AlignLeft)
        self.detail_heading = label("", "heading")
        self.detail_copy = label("", "muted", wrap=True)
        self.detail_copy.setTextFormat(Qt.TextFormat.PlainText)
        form.addWidget(self.detail_heading)
        form.addWidget(self.detail_copy)
        self.resource_label = label("Resource link or ID", "muted")
        form.addWidget(self.resource_label)
        self.resource = QLineEdit(self)
        self.resource.setMaxLength(2048)
        self.resource.setAccessibleName("Connector resource")
        form.addWidget(self.resource)
        self.resource_help = label("", "muted", wrap=True)
        self.resource_help.setTextFormat(Qt.TextFormat.PlainText)
        self.resource_help.setAccessibleName("Where to find the resource ID")
        form.addWidget(self.resource_help)
        expiry = QHBoxLayout()
        expiry.addWidget(label("Remove Aedrova’s access after", "muted"))
        self.hours = QSpinBox(self)
        self.hours.setRange(1, 2160)
        self.hours.setValue(24)
        self.hours.setSuffix(" hours")
        self.hours.setAccessibleName("Connection lifetime in hours")
        expiry.addWidget(self.hours)
        expiry.addStretch()
        form.addLayout(expiry)
        self.oauth = button("Connect account", role="primary")
        self.oauth.clicked.connect(self.connect_oauth)
        form.addWidget(self.oauth, alignment=Qt.AlignmentFlag.AlignLeft)
        self.oauth_hint = label("", "muted", wrap=True)
        form.addWidget(self.oauth_hint)
        self.advanced = button("Use an access token instead")
        self.advanced.setCheckable(True)
        self.token_panel = QWidget(self)
        token_form = QVBoxLayout(self.token_panel)
        token_form.setContentsMargins(0, 0, 0, 0)
        self.advanced.toggled.connect(self.show_token_fields)
        form.addWidget(self.advanced)
        form.addWidget(self.token_panel)
        token_form.addWidget(label("Scoped access token", "muted"))
        self.credential = QLineEdit(self)
        self.credential.setEchoMode(QLineEdit.EchoMode.Password)
        self.credential.setMaxLength(4096)
        self.credential.setAccessibleName("Private provider access token")
        self.credential.setPlaceholderText("Paste securely here")
        token_form.addWidget(self.credential)
        token_form.addWidget(
            label(
                "Your token is encrypted on Aedrova’s service. It is never sent to the AI or "
                "shared with teammates.",
                "muted",
                wrap=True,
            )
        )
        self.connect = button("Verify & connect", role="primary")
        self.connect.clicked.connect(self.connect_tool)
        token_form.addWidget(self.connect, alignment=Qt.AlignmentFlag.AlignLeft)
        self.existing = QWidget(self)
        self.existing_layout = QVBoxLayout(self.existing)
        self.existing_layout.setContentsMargins(0, 8, 0, 0)
        form.addWidget(self.existing)
        form.addStretch()
        details = QScrollArea(self)
        details.setWidgetResizable(True)
        details.setFrameShape(QFrame.Shape.NoFrame)
        details.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        details.setWidget(detail)
        self.pages.addWidget(details)
        success = QWidget(self)
        success_layout = QVBoxLayout(success)
        success_layout.setContentsMargins(24, 24, 24, 24)
        success_layout.addStretch()
        self.success_bud = Character(parent=success, reduced_motion=window.reduced_motion)
        self.success_bud.setFixedSize(160, 160)
        success_layout.addWidget(self.success_bud, alignment=Qt.AlignmentFlag.AlignHCenter)
        success_layout.addSpacing(12)
        check = label("✓", "subheading")
        check.setAccessibleName("Connection verified")
        success_layout.addWidget(check, alignment=Qt.AlignmentFlag.AlignHCenter)
        success_layout.addSpacing(26)
        self.success_heading = label("", "heading")
        self.success_copy = label("", "muted", wrap=True)
        for item in (self.success_heading, self.success_copy):
            item.setAlignment(Qt.AlignmentFlag.AlignCenter)
            item.setTextFormat(Qt.TextFormat.PlainText)
            success_layout.addWidget(item)
        success_layout.addSpacing(16)
        success_layout.addWidget(
            label("Verified access · Read-only", "muted"), alignment=Qt.AlignmentFlag.AlignHCenter
        )
        back_connected = button("Connect another tool", role="primary")
        back_connected.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        success_layout.addSpacing(24)
        success_layout.addWidget(back_connected, alignment=Qt.AlignmentFlag.AlignHCenter)
        success_layout.addWidget(
            label("Disconnect anytime in your Bud’s settings.", "muted"),
            alignment=Qt.AlignmentFlag.AlignHCenter,
        )
        success_layout.addStretch()
        self.pages.addWidget(success)
        selection = QWidget(self)
        selection_layout = QVBoxLayout(selection)
        selection_layout.setContentsMargins(28, 28, 28, 28)
        selection_layout.addWidget(label("Choose what your Bud can read", "heading"))
        self.selection_copy = label("", "muted", wrap=True)
        selection_layout.addWidget(self.selection_copy)
        self.resource_picker = ChoiceBox(self)
        self.resource_picker.setAccessibleName("Authorized resources")
        selection_layout.addWidget(self.resource_picker)
        self.selection_link = QLineEdit(self)
        self.selection_link.setPlaceholderText("Paste your Figma file link")
        self.selection_link.setAccessibleName("Authorized Figma file link")
        selection_layout.addWidget(self.selection_link)
        self.selection_submit = button("Connect selected resource", role="primary")
        self.selection_submit.clicked.connect(self.select_oauth_resource)
        selection_layout.addWidget(self.selection_submit)
        self.selection_retry = button("Sign in again")
        self.selection_retry.clicked.connect(self.connect_oauth)
        selection_layout.addWidget(self.selection_retry)
        selection_layout.addStretch()
        self.pages.addWidget(selection)
        self.status = label("Loading connectors…", "muted", wrap=True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        main.addWidget(self.status)
        self.refresh()

    def update_controls(self):
        busy = (
            self.pending
            or self.job is not None
            or bool(
                self.embedded_owner and (self.embedded_owner.pending or self.embedded_owner.job)
            )
        )
        self.bud.setEnabled(not busy)
        can_connect = bool(self.bud.currentData()) or bool(
            self.embedded_owner and self.embedded_owner.admin()
        )
        self.connect.setEnabled(can_connect and not busy)
        self.connect.setText(
            "Save Bud & connect"
            if self.embedded_owner and not self.embedded_owner.current()
            else "Verify & connect"
        )
        self.oauth.setEnabled(
            can_connect
            and not busy
            and bool(
                self.selected_provider
                and (
                    self.selected_provider.get("oauth_available")
                    or self.selected_provider.get("managed_available")
                )
            )
        )
        self.resource.setEnabled(not busy)
        self.credential.setEnabled(not busy)
        self.hours.setEnabled(not busy)
        self.selection_submit.setEnabled(not busy)
        self.selection_retry.setEnabled(not busy)
        self.resource_picker.setEnabled(not busy)
        self.selection_link.setEnabled(not busy)
        for card in self.cards:
            card.setEnabled(not busy and bool(card.property("providerAvailable")) and can_connect)
        if self.embedded_owner:
            self.embedded_owner.update_controls()

    def refresh(self, *, on_loaded=None):
        selected = self.bud.currentData() or self.selected

        def fetch(service):
            api = client(service)
            providers = api.request("/api/buds/connectors")["providers"]
            rows = api.request("/api/dots?workspace=" + self.workspace)["items"]
            return providers, rows

        def loaded(value):
            self.providers, self.rows = value
            DotDialog.sync_connection_rows(self, self.rows)
            if self.selected_provider:
                refreshed = next(
                    (p for p in self.providers if p["id"] == self.selected_provider["id"]), None
                )
                if refreshed:
                    self.selected_provider = refreshed
                    self.auth_details(refreshed)
            self.bud.blockSignals(True)
            self.bud.clear()
            for row in self.rows:
                self.bud.addItem(row["name"], row["id"])
            if self.embedded_owner:
                current = self.embedded_owner.current()
                selected_bud = current["id"] if current else None
                self.bud.setCurrentIndex(self.bud.findData(selected_bud))
                if current:
                    fresh = next((r for r in self.rows if r["id"] == current["id"]), None)
                    if fresh:
                        current.update(fresh)
                self.embedded_owner.update_controls()
            else:
                self.bud.setCurrentIndex(max(0, self.bud.findData(selected)))
            self.bud.blockSignals(False)
            self.apply_role_filter()
            self.rebuild_gallery()
            self.refresh_existing()
            self.status.setText(
                "Choose a tool to connect."
                if self.rows
                else "Choose a tool. Your Bud will be saved when you connect."
                if self.embedded_owner
                else "Create a Bud first, then connect its tools here."
            )
            if self.on_change:
                self.on_change()
            if on_loaded:
                on_loaded()

        self.run(fetch, loaded, recovery=True)

    def bud_changed(self):
        self.credential.clear()
        self.pages.setCurrentIndex(0)
        self.apply_role_filter()
        self.rebuild_gallery()

    def sync_target(self):
        self.stop_oauth()
        if self.embedded_owner:
            current = self.embedded_owner.current()
            self.bud.blockSignals(True)
            self.bud.clear()
            if current:
                self.bud.addItem(current["name"], current["id"])
            self.bud.blockSignals(False)
            self.credential.clear()
            self.pages.setCurrentIndex(0)
            self.apply_role_filter()
            self.rebuild_gallery()

    def row(self):
        if self.embedded_owner:
            return {
                **(self.embedded_owner.current() or {"connections": []}),
                "role": self.embedded_owner.configured_role(),
            }
        return next((r for r in self.rows if r["id"] == self.bud.currentData()), {})

    def apply_role_filter(self):
        row = self.row()
        role = role_for(row.get("role", ""))
        target = (row.get("id"), role)
        if target != self.role_target:
            self.role_target = target
            self.filter.blockSignals(True)
            self.filter.setCurrentIndex(max(0, self.filter.findData(role)))
            self.filter.blockSignals(False)
            self.search.blockSignals(True)
            self.search.clear()
            self.search.blockSignals(False)

    def show_confirmation(self, provider, bud_id):
        row = self.row()
        if row.get("id") != bud_id:
            return
        self.success_bud.set_config(row)
        self.success_heading.setText(provider["name"] + " is connected.")
        self.success_copy.setText(
            row["name"]
            + " can now access: "
            + provider["description"]
            + "\nMention @"
            + row["name"]
            + " in your conversation."
        )
        self.pages.setCurrentIndex(2)
        self.status.setText("Connected. Your Bud’s access has been verified.")

    def rebuild_gallery(self):
        body = QWidget(self.gallery)
        body.setObjectName("ConnectorGallery")
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 4, 8)
        layout.setSpacing(16 if self.embedded_owner else 22)
        banner = QFrame(body)
        banner.setObjectName("ConnectorFeature")
        featured = QVBoxLayout(banner)
        featured.setContentsMargins(20, 12, 20, 12)
        featured.setSpacing(6)
        featured.addWidget(label("Put your tools in the conversation.", "subheading"))
        featured.addWidget(
            label(
                "Give your Bud connected context. You choose the resource and keep control of "
                "access.",
                "muted",
                wrap=True,
            )
        )
        layout.addWidget(banner)
        self.cards, self.grid_layouts = [], []
        role = self.filter.currentData()
        allowed = None if role == "all" else recommendation_set(role)
        query = self.search.text().casefold()
        groups = {}
        for provider in self.providers:
            if allowed is not None and provider["id"] not in allowed:
                continue
            if query and query not in (provider["name"] + " " + provider["description"]).casefold():
                continue
            groups.setdefault(provider["group"], []).append(provider)
        recommended = recommendation_set(role_for(self.row().get("role", "")))
        for group, providers in groups.items():
            layout.addWidget(label(group.upper(), "muted"))
            grid = QGridLayout()
            grid.setSpacing(14)
            self.grid_layouts.append(grid)
            columns = 3 if self.width() >= (790 if self.embedded_owner else 1080) else 2
            for column_index in range(columns):
                grid.setColumnStretch(column_index, 1)
            for index, provider in enumerate(providers):
                card = QFrame(body)
                card.setObjectName("ConnectorCard")
                column = QVBoxLayout(card)
                column.setContentsMargins(16, 14, 16, 14)
                column.setSpacing(8)
                heading = QHBoxLayout()
                glyph = label(GLYPHS.get(provider["id"], "↗"), "subheading")
                glyph.setObjectName("ConnectorGlyph")
                glyph.setAlignment(Qt.AlignmentFlag.AlignCenter)
                glyph.setFixedSize(36, 36)
                mark = connector_pixmap(provider["id"])
                if not mark.isNull():
                    glyph.setPixmap(mark)
                glyph.setAccessibleName(provider["name"] + " app icon")
                heading.addWidget(glyph)
                heading.addWidget(label(provider["name"], "subheading"), 1)
                column.addLayout(heading)
                copy = label(provider["description"], "muted", wrap=True)
                copy.setMinimumHeight(42)
                column.addWidget(copy)
                connected = any(
                    c["provider"] == provider["id"] and c["status"] == "Connected"
                    for c in self.row().get("connections", [])
                )
                column.addWidget(
                    label(
                        "Service setup required"
                        if not provider.get("available")
                        else "Connected to this Bud"
                        if connected
                        else "Suggested for this Bud"
                        if provider["id"] in recommended
                        else "Available",
                        "muted",
                    )
                )
                action = button("Manage" if connected else "Connect")
                action.setProperty("providerAvailable", provider.get("available", False))
                action.setAccessibleName(
                    ("Manage " if connected else "Connect ") + provider["name"]
                )
                action.clicked.connect(lambda checked=False, p=provider: self.open_provider(p))
                column.addWidget(action, alignment=Qt.AlignmentFlag.AlignLeft)
                self.cards.append(action)
                grid.addWidget(card, index // columns, index % columns)
            layout.addLayout(grid)
        if not groups:
            layout.addWidget(label("No matching connectors.", "muted"))
        layout.addStretch()
        old = self.gallery.takeWidget()
        self.gallery.setWidget(body)
        if old:
            old.deleteLater()
        self.update_controls()

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        if hasattr(self, "providers") and hasattr(self, "gallery"):
            columns = 3 if self.width() >= (790 if self.embedded_owner else 1080) else 2
            if getattr(self, "columns", None) != columns:
                self.columns = columns
                self.rebuild_gallery()

    def open_provider(self, provider):
        self.stop_oauth()
        self.selected_provider = provider
        self.detail_heading.setText(provider["name"])
        self.auth_details(provider)
        self.resource.setText(
            self.row().get("resource", "") if self.row().get("provider") == provider["id"] else ""
        )
        if provider["id"] == "tiktok" and provider.get("oauth_available"):
            self.resource.setText("me")
        self.resource.setPlaceholderText("Paste a resource link or " + provider["resource_hint"])
        automatic = bool(provider.get("oauth_available"))
        self.resource.setVisible(not automatic)
        self.resource_label.setVisible(not automatic)
        self.advanced.setChecked(False)
        self.token_panel.setVisible(self.advanced.isChecked())
        self.show_token_fields(self.advanced.isChecked())
        link_help = {
            "github": "Paste your repository’s GitHub link. We’ll select that repository.",
            "figma": "Paste your Figma file link. We’ll extract the file key for you.",
            "notion": "Paste the shared Notion page link. We’ll extract its page ID.",
            "supabase": "Paste your Supabase dashboard project link. We’ll select that project.",
        }
        self.resource_help.setText(
            "Sign in first. Choose what your Bud can read when you return."
            if automatic
            else link_help.get(provider["id"], RESOURCE_HELP[provider["id"]])
        )
        self.credential.clear()
        self.refresh_existing()
        self.pages.setCurrentIndex(1)
        (self.oauth if automatic else self.resource).setFocus()

    def show_token_fields(self, visible):
        self.token_panel.setVisible(visible)
        for control in (self.resource, self.resource_label, self.resource_help):
            control.setVisible(visible)

    def auth_details(self, provider):
        managed = bool(provider.get("managed_available"))
        self.oauth.setText("Enable web search" if managed else "Connect account")
        self.detail_copy.setText(
            "Search the web through Aedrova. No extra account or API key is needed. "
            "Daily usage limits apply."
            if managed
            else provider["permissions"]
            if provider.get("oauth_available")
            else "Account sign-in is not available for this service yet. "
            "Advanced token setup is optional below."
        )
        self.oauth.setVisible(bool(provider.get("oauth_supported") or managed))
        self.oauth_hint.setVisible(bool(provider.get("oauth_supported") or managed))
        self.oauth_hint.setText(
            "Choose a research topic for your Bud. No codes or keys to copy."
            if managed
            else "Sign in and approve read-only access. Finish here without copying codes or IDs."
            if provider.get("oauth_available")
            else provider.get("oauth_setup_hint")
            or "Account sign-in needs Aedrova’s provider app setup. A scoped token works below."
        )
        self.update_controls()

    def refresh_existing(self):
        while self.existing_layout.count():
            item = self.existing_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not self.selected_provider:
            return
        for connection in self.row().get("connections", []):
            if connection["provider"] != self.selected_provider["id"]:
                continue
            row = QHBoxLayout()
            copy = label(connection["resource"] + " · " + connection["status"], "muted", wrap=True)
            copy.setTextFormat(Qt.TextFormat.PlainText)
            row.addWidget(copy, 1)
            disconnect = button("Disconnect")
            disconnect.clicked.connect(lambda checked=False, c=connection: self.disconnect_tool(c))
            row.addWidget(disconnect)
            wrapper = QWidget(self.existing)
            wrapper.setLayout(row)
            self.existing_layout.addWidget(wrapper)

    def stop_oauth(self):
        self.oauth_timer.stop()
        self.oauth_state = ""

    def connect_oauth(self):
        provider = self.selected_provider
        resource = "me" if provider and provider["id"] == "tiktok" else ""
        if not provider or not (
            provider.get("oauth_available") or provider.get("managed_available")
        ):
            self.status.setText("Provider account sign-in needs owner setup first.")
            return
        if self.embedded_owner and self.embedded_owner.has_changes():
            owner = self.embedded_owner
            if not owner.current():
                owner.provider.setCurrentIndex(owner.provider.findData(provider["id"]))
                # A disconnected draft needs a nonempty legacy metadata field.
                # This is not an authorization or a readable resource.
                owner.resource.setText(
                    "selection/pending" if provider["id"] == "github" else "pending"
                )

            def saved(_row):
                self.rows = owner.rows
                self.bud.blockSignals(True)
                self.bud.clear()
                self.bud.addItem(owner.current()["name"], owner.current()["id"])
                self.bud.blockSignals(False)
                self.resource.setText(resource)
                self.connect_oauth()

            owner.save_dot(on_saved=saved)
            return
        if not self.bud.currentData():
            self.status.setText("Choose a Bud first.")
            return
        if provider.get("managed_available"):
            self.pages.setCurrentIndex(3)
            self.resource_picker.setVisible(False)
            self.selection_link.setVisible(True)
            self.selection_link.setPlaceholderText("What should your Bud research?")
            self.selection_copy.setText(
                "Choose a research topic. Aedrova handles the connection; daily usage limits apply."
            )
            self.selection_submit.setText("Enable web search")
            return
        self.selection_submit.setText("Connect selected resource")
        self.selection_link.setPlaceholderText("Paste a Figma file link")
        self.stop_oauth()
        body = {
            "workspace": self.workspace,
            "dot": self.bud.currentData(),
            "provider": provider["id"],
            "resource": resource,
            "hours": self.hours.value(),
        }

        def started(value):
            state = value.get("state", "")
            origin = connector_origin()
            if (
                not re.fullmatch(r"[A-Za-z0-9_-]{40,100}", state)
                or not origin
                or value.get("url") != origin.rstrip("/") + "/buds/authorize/" + state
            ):
                self.status.setText("The service returned an invalid authorization link.")
                return
            if not QDesktopServices.openUrl(QUrl(value["url"])):
                self.status.setText("Your browser could not open. Try Connect account again.")
                return
            self.oauth_state, self.oauth_deadline = state, time.monotonic() + 600
            self.oauth_timer.start()
            self.status.setText("Finish authorization in your browser. This Bud will update here.")

        self.run(lambda service: client(service).request("/api/buds/oauth/start", body), started)

    def poll_oauth(self):
        if not self.oauth_state or self.pending or self.job:
            return
        if time.monotonic() >= self.oauth_deadline or not self.isVisible():
            self.stop_oauth()
            self.status.setText("Authorization expired. Try Connect account again.")
            return
        state = self.oauth_state
        self.oauth_timer.stop()

        def checked(value):
            if state != self.oauth_state:
                return
            if value.get("status") == "connected":
                self.stop_oauth()
                provider, bud_id = dict(self.selected_provider), self.bud.currentData()
                self.refresh(on_loaded=lambda: self.show_confirmation(provider, bud_id))
            elif value.get("status") == "choose_resource":
                self.resource_picker.clear()
                self.resource_picker.addItem("Choose a resource…", "")
                for row in value.get("resources", []):
                    self.resource_picker.addItem(row["name"], row["id"])
                link = bool(value.get("requires_link"))
                self.resource_picker.setVisible(not link)
                self.selection_link.setVisible(link)
                self.selection_copy.setText(
                    "Paste a Figma file link. Your Bud will only read that file."
                    if link
                    else "Select from your account. Your Bud will only use this resource."
                    if value.get("resources")
                    else "No resources found. Share a page or install Aedrova on a repository, "
                    "then reconnect."
                )
                self.pages.setCurrentIndex(3)
                self.status.setText("Account authorized. Choose a resource to finish.")
            elif value.get("status") == "failed":
                self.stop_oauth()
                self.status.setText("Authorization did not complete. Try Connect account again.")
            else:
                self.status.setText("Waiting for authorization in your browser…")
                self.oauth_timer.start()

        self.run(
            lambda service: client(service).request(
                "/api/buds/oauth/status?" + urlencode({"state": state})
            ),
            checked,
        )

    def select_oauth_resource(self):
        if self.selected_provider and self.selected_provider.get("managed_available"):
            topic = self.selection_link.text().strip()
            if not 3 <= len(topic) <= 200:
                self.status.setText("Enter a research topic of 3–200 characters.")
                return
            body = {
                "workspace": self.workspace,
                "dot": self.bud.currentData(),
                "topic": topic,
                "hours": self.hours.value(),
            }
            provider, bud_id = dict(self.selected_provider), self.bud.currentData()
            self.run(
                lambda service: client(service).request("/api/buds/connections/search", body),
                lambda _value: self.refresh(
                    on_loaded=lambda: self.show_confirmation(provider, bud_id)
                ),
            )
            return
        if not self.oauth_state or not self.selected_provider:
            return
        if time.monotonic() >= self.oauth_deadline:
            self.stop_oauth()
            self.status.setText("Authorization expired. Connect account again.")
            return
        try:
            resource = (
                normalize_resource("figma", self.selection_link.text())
                if self.selection_link.isVisible()
                else self.resource_picker.currentData()
            )
        except ValueError as error:
            self.status.setText(str(error))
            return
        if not resource:
            self.status.setText("Choose what your Bud may read.")
            return
        body = {"state": self.oauth_state, "resource": resource}

        def connected(_value):
            self.stop_oauth()
            provider, bud_id = dict(self.selected_provider), self.bud.currentData()
            self.refresh(on_loaded=lambda: self.show_confirmation(provider, bud_id))

        self.run(lambda service: client(service).request("/api/buds/oauth/select", body), connected)

    def connect_tool(self):
        if not self.selected_provider or (not self.bud.currentData() and not self.embedded_owner):
            self.status.setText("Choose a Bud and a tool first.")
            return
        try:
            resource = normalize_resource(self.selected_provider["id"], self.resource.text())
        except ValueError as error:
            self.status.setText(str(error))
            return
        credential = self.credential.text().strip()
        if not resource or not credential:
            self.status.setText("Add the resource and access token first.")
            return
        if self.embedded_owner and self.embedded_owner.has_changes():
            owner = self.embedded_owner
            if not owner.current():
                owner.provider.setCurrentIndex(
                    owner.provider.findData(self.selected_provider["id"])
                )
                owner.resource.setText(resource)

            def saved(_row):
                self.rows = owner.rows
                self.bud.blockSignals(True)
                self.bud.clear()
                self.bud.addItem(owner.current()["name"], owner.current()["id"])
                self.bud.blockSignals(False)
                self.resource.setText(resource)
                self.credential.setText(credential)
                self.connect_tool()

            owner.save_dot(on_saved=saved)
            return
        body = {
            "workspace": self.workspace,
            "dot": self.bud.currentData(),
            "provider": self.selected_provider["id"],
            "resource": resource,
            "credential": credential,
            "hours": self.hours.value(),
        }
        self.credential.clear()
        self.status.setText("Verifying access to your selected resource…")

        def operation(service):
            try:
                return client(service).request("/api/buds/connections", body, timeout=70)
            except RuntimeError as exc:
                raise ValueError(str(exc).replace(credential, "[redacted]")) from None
            finally:
                body["credential"] = ""

        provider, bud_id = dict(self.selected_provider), self.bud.currentData()

        def connected(_value):
            self.refresh(on_loaded=lambda: self.show_confirmation(provider, bud_id))

        self.run(operation, connected)

    def disconnect_tool(self, connection):
        body = {
            "workspace": self.workspace,
            "dot": self.bud.currentData(),
            "connection": connection["id"],
        }

        def removed(_value):
            self.refresh()
            self.status.setText(
                "Access removed from Aedrova. Revoke the token in the provider’s settings too."
            )

        self.run(
            lambda service: client(service).request("/api/buds/connections/disconnect", body),
            removed,
        )

    def done(self, result):
        self.stop_oauth()
        self.credential.clear()
        super().done(result)


def open_connectors(window, selected=None, on_change=None):
    if not window.current_user():
        window.show_account()
        return
    window.connectors_dialog = ConnectorsDialog(window, selected, on_change=on_change)
    window.connectors_dialog.show()
