"""Working account and desktop preferences; no placeholder account actions."""

from datetime import UTC, datetime
from urllib.parse import quote

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from aedrova.agents.managed import ManagedClient, ai_access_mode, application_origin
from aedrova.desktop.controls import AppDialog, ChoiceBox
from aedrova.desktop.design_system import FlowActions
from aedrova.desktop.dialogs import button, label


class SettingsDialog(AppDialog):
    def __init__(self, window, *, scope="personal"):
        super().__init__(window)
        self.window = window
        self.scope = scope
        title = "Personal settings" if scope == "personal" else "Workspace resources"
        self.setWindowTitle("Aedrova · " + title)
        self.setMinimumSize(720, 540)
        self.resize(820, 600)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        from aedrova.desktop.workspace_settings import WorkspaceSettingsView

        self.view = WorkspaceSettingsView(
            title,
            "Your preferences, across workspaces."
            if scope == "personal"
            else "Team tools and included AI for " + window.workspace.name + ".",
        )
        outer.addWidget(self.view, 1)

        columns = []

        def section(key, title, detail="", symbol="settings", group="Preferences"):
            if columns:
                columns[-1].addStretch(1)
            column = self.view.add_section(key, title, detail, symbol, group=group)
            columns.append(column)
            return column

        account = getattr(window, "account_dialog", None)
        self.user = account.service.user if account and account.service else None
        self.account = account
        if self.user and scope == "personal":
            layout = section(
                "profile", "Profile", "Your identity across workspaces.", "people", "Account"
            )
            layout.addWidget(label(getattr(self.user, "email", None) or "Google account"))
            layout.addWidget(
                label(
                    "Email and sign-in security are managed by your Google account.",
                    "muted",
                    wrap=True,
                )
            )
            row = QHBoxLayout()
            self.name = QLineEdit(
                account.snapshot.get("user_profile", {}).get("display_name")
                or (getattr(self.user, "user_metadata", None) or {}).get("full_name", "")
            )
            self.name.setPlaceholderText("Your display name")
            self.name.setAccessibleName("Display name")
            self.name.setMaxLength(80)
            from aedrova.desktop.profile import open_profile_editor

            full_profile = button("Edit full profile…", role="outline")
            full_profile.clicked.connect(lambda: open_profile_editor(window))
            layout.addWidget(full_profile)
            self.save = button("Save name", role="outline")
            self.save.clicked.connect(self.save_name)
            row.addWidget(self.name, 1)
            row.addWidget(self.save)
            layout.addLayout(row)
        if self.user and scope == "workspace":
            from aedrova.desktop.bud_connectors import open_connectors

            layout = section(
                "integrations",
                "Integrations",
                "Connections remain scoped to each Bud and its authorized tools.",
                "link",
                "Connected tools",
            )
            connectors = button("Manage connectors…", role="outline")
            connectors.clicked.connect(lambda: open_connectors(window))
            layout.addWidget(connectors)
        if scope == "personal":
            layout = section(
                "appearance", "Appearance", "Choose a comfortable way to work.", "appearance"
            )
            self.appearance = ChoiceBox()
            self.appearance.setAccessibleName("Appearance")
            for text, value in (("System default", "system"), ("Light", "light"), ("Dark", "dark")):
                self.appearance.addItem(text, value)
            self.appearance.setCurrentIndex(self.appearance.findData(window.theme_mode))
            self.appearance.currentIndexChanged.connect(
                lambda: window.set_theme(self.appearance.currentData())
            )
            layout.addWidget(self.appearance)
            layout.addStretch(1)
            layout = section(
                "accessibility",
                "Accessibility",
                "Motion and transparency adapt throughout Aedrova.",
                "permission_auto",
            )
            self.motion = QCheckBox("Reduce motion")
            self.motion.setChecked(window.reduced_motion)
            self.motion.toggled.connect(window.reduce_motion_action.setChecked)
            layout.addWidget(self.motion)
            self.transparency = QCheckBox("Reduce transparency")
            self.transparency.setChecked(window.reduced_transparency)
            self.transparency.toggled.connect(window.reduce_transparency_action.setChecked)
            layout.addWidget(self.transparency)
            layout = section(
                "workflow", "Editor", "Your preferred app for opening project files.", "folder"
            )
            self.editor = ChoiceBox()
            self.editor.setAccessibleName("Preferred editor")
            for name in ("Visual Studio Code", "Cursor", "Xcode", "Finder"):
                self.editor.addItem(name)
            self.editor.setCurrentText(window.settings.value("editor", "Visual Studio Code"))
            self.editor.currentTextChanged.connect(
                lambda value: window.settings.setValue("editor", value)
            )
            layout.addWidget(self.editor)
            layout = section(
                "language",
                "Language & translation",
                "Read and write in your preferred language.",
                "context",
            )
            from aedrova.desktop.localization import show_language_settings

            languages = button("Manage languages", role="outline")
            languages.clicked.connect(lambda: show_language_settings(window))
            layout.addWidget(languages)
            layout.addStretch(1)
        if self.user and scope == "personal":
            layout = section(
                "privacy",
                "Privacy & data",
                "Review what reaches AI, export information or request deletion.",
                "permission_ask",
                "Privacy",
            )
            privacy = button("Review data controls…", role="outline")
            privacy.setAccessibleName("Review Aedrova data and AI privacy controls")
            privacy.clicked.connect(
                lambda: QDesktopServices.openUrl(QUrl("https://aedrova.com/data-controls"))
            )
            layout.addWidget(privacy)
        self.billing_origin = application_origin()
        if self.user and scope == "workspace":
            layout = section(
                "billing",
                "Billing & credits",
                "One workspace subscription covers your team.",
                "activity",
                "Plan & governance",
            )
            if ai_access_mode() == "local":
                layout.addWidget(
                    label(
                        "AI builds use your local provider login in this internal "
                        "alpha. Included plan access is being prepared.",
                        "muted",
                        wrap=True,
                    )
                )
            self.billing_status = label(
                "Checking your workspace’s plan…"
                if self.billing_origin
                else (
                    "Included AI is being prepared. This internal alpha uses "
                    "separate provider access."
                ),
                "muted",
                wrap=True,
            )
            layout.addWidget(self.billing_status)
            if self.billing_origin:
                row = QHBoxLayout()
                manage = button("Team plan & billing", role="outline")
                manage.clicked.connect(
                    lambda: QDesktopServices.openUrl(
                        QUrl(
                            self.billing_origin
                            + "/account?workspace="
                            + quote(window.workspace_id, safe="")
                        )
                    )
                )
                refresh = button("Refresh usage", role="outline")
                refresh.clicked.connect(self.load_balance)
                row.addWidget(manage)
                row.addWidget(refresh)
                layout.addLayout(row)
                self.activate_ai = button("Activate included AI", role="primary")
                self.activate_ai.setToolTip(
                    "Activate available free access. No card or subscription."
                )
                self.activate_ai.clicked.connect(self.activate_included_ai)
                self.activate_ai.hide()
                layout.addWidget(self.activate_ai)
                self.load_balance()
        if scope == "personal":
            layout = section(
                "support", "Help & support", "Get help from the Aedrova team.", "smile", "Support"
            )
            for caption, url in (
                ("Help center", "https://aedrova.com/support"),
                ("Contact support", "mailto:contact@aedrova.com"),
                ("Privacy policy", "https://aedrova.com/privacy"),
                ("Terms of service", "https://aedrova.com/terms"),
            ):
                action = button(caption, role="outline")
                action.clicked.connect(
                    lambda checked=False, target=url: QDesktopServices.openUrl(QUrl(target))
                )
                layout.addWidget(action)
            layout.addStretch(1)
            from aedrova import __version__

            layout = section(
                "about", "About Aedrova", "Your team, plus Agents", "spaces", "Support"
            )
            layout.addWidget(label("Version " + __version__, "muted"))
            website = button("Visit aedrova.com", role="outline")
            website.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://aedrova.com")))
            layout.addWidget(website)
            layout.addStretch(1)
            self.view.show_section("profile" if self.user else "appearance")
        elif self.user:
            self.view.show_section("billing")
        if columns:
            columns[-1].addStretch(1)
        self.status = label(
            "Preferences save automatically on this device."
            if scope == "personal"
            else "Workspace access and limits are enforced by the server.",
            "muted",
            wrap=True,
        )
        self.status.setContentsMargins(24, 8, 24, 0)
        outer.addWidget(self.status)
        footer = QWidget()
        footer.setObjectName("SettingsFooter")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(24, 10, 24, 12)
        actions = FlowActions()
        footer_layout.addLayout(actions)
        outer.addWidget(footer)
        if self.user:
            workspace = button("Workspace settings", role="outline")
            workspace.clicked.connect(self.workspace_settings)
            actions.addWidget(workspace)
            signout = button("Log out", role="outline")
            signout.clicked.connect(window.log_out)
            actions.addWidget(signout)
            account.session_closed.connect(self.clear_account)
        done = button("Done", role="primary")
        done.clicked.connect(self.accept)
        actions.addWidget(done)

    def load_balance(self):
        if not self.user or not self.billing_origin or not self.window.connected:
            return
        workspace, expected = self.window.workspace_id, str(self.user.id)
        self.billing_status.setText("Checking your workspace’s plan…")

        def operation():
            try:
                _, _, access, user = self.account.service.realtime_credentials()
                if user != expected:
                    return {"error": "Your account changed. Sign in again."}
                return ManagedClient(self.billing_origin, access).balance(workspace)
            except Exception:
                return {
                    "error": "Could not load included AI usage. Check your connection and retry."
                }

        def completed(result):
            if (
                not self.user
                or str(self.user.id) != expected
                or self.window.workspace_id != workspace
            ):
                return
            self.activate_ai.hide()
            if result.get("status") == "no_plan":
                authorized = any(
                    row.get("workspace_id") == workspace
                    and row.get("user_id") == expected
                    and row.get("role") in {"owner", "admin"}
                    for row in self.account.snapshot.get("members", [])
                )
                self.activate_ai.setVisible(authorized)
                self.activate_ai.setEnabled(authorized)
            if result.get("error"):
                self.billing_status.setText(result["error"])
            elif result.get("status") == "active":
                names = {"free": "Free", "monthly": "Pro", "annual": "Team"}
                plan = names.get(result["plan"], result["plan"].title())
                spent = result.get("monthly_spent", result["spent"])
                budget = max(1, result.get("monthly_budget", result["allowance"]))
                remaining = max(0, min(100, round(100 * (1 - spent / budget))))
                reset = ""
                if result.get("reset_at"):
                    date = datetime.fromtimestamp(result["reset_at"], UTC).strftime("%b %d")
                    reset = f"Resets {date} (UTC). "
                self.billing_status.setText(
                    f"Your team’s {plan} plan · {remaining}% shared monthly AI capacity remaining. "
                    + reset
                    + "One subscription covers your team. No automatic overage charges."
                )
            else:
                self.billing_status.setText(
                    "Included AI is not active for this Space. Its owner or admin can activate "
                    "available free access here, without a card or subscription. Plan limits apply."
                )

        if not self.window.connected.enqueue(
            ("managed-balance", expected, workspace), operation, completed
        ):
            self.billing_status.setText("Connection busy. Refresh usage shortly.")

    def activate_included_ai(self):
        if not self.user or not self.window.connected or getattr(self, "activation_pending", False):
            return
        workspace, expected = self.window.workspace_id, str(self.user.id)
        self.activation_pending = True
        self.activate_ai.setEnabled(False)
        self.billing_status.setText("Activating your Space’s included AI…")

        def operation():
            try:
                _, _, access, user = self.account.service.realtime_credentials()
                if user != expected:
                    return {"error": "Your account changed. Sign in again."}
                return ManagedClient(self.billing_origin, access).activate_free(workspace)
            except RuntimeError as error:
                return {"error": str(error)}
            except Exception:
                return {"error": "Could not confirm activation. Refresh usage before retrying."}

        def completed(result):
            self.activation_pending = False
            if (
                not self.user
                or str(self.user.id) != expected
                or self.window.workspace_id != workspace
            ):
                return
            if result.get("error"):
                self.billing_status.setText(result["error"])
                self.activate_ai.setEnabled(True)
            else:
                self.activate_ai.hide()
                self.load_balance()

        if not self.window.connected.enqueue(
            ("activate-included", expected, workspace), operation, completed
        ):
            self.activation_pending = False
            self.activate_ai.setEnabled(True)
            self.billing_status.setText("Connection busy. Retry activation shortly.")

    def workspace_settings(self):
        self.close()
        self.window.show_account("manage")

    def save_name(self):
        value = self.name.text().strip()
        if not value:
            self.status.setText("Enter your display name.")
            return
        connected = self.window.connected
        if not connected or not connected.active:
            return
        self.save.setEnabled(False)
        self.status.setText("Saving your name…")

        def operation():
            try:
                self.account.service.update_profile(value)
                return {"saved": True}
            except Exception:
                return {"error": "Could not save your name. Check your connection and sign-in."}

        def completed(result):
            if not self.user:
                return
            self.save.setEnabled(True)
            self.status.setText(result.get("error", "Your display name is saved."))
            self.window.update_profile_button()

        if not connected.enqueue(("profile-name", str(self.user.id)), operation, completed):
            self.save.setEnabled(True)
            self.status.setText("Connection busy. Try saving again shortly.")

    def clear_account(self):
        self.user = None
        if hasattr(self, "name"):
            self.name.clear()
        self.close()
