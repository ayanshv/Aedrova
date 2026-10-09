"""Working account and desktop preferences; no placeholder account actions."""

from datetime import UTC, datetime
from urllib.parse import quote

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from aedrova.agents.managed import ManagedClient, ai_access_mode, application_origin
from aedrova.desktop.controls import AppDialog, ChoiceBox
from aedrova.desktop.design_system import FlowActions, section
from aedrova.desktop.dialogs import button, label


class SettingsDialog(AppDialog):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.setWindowTitle("Aedrova · Settings")
        self.setMinimumWidth(560)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        content = QWidget()
        content.setObjectName("AccountPage")
        scroll.setWidget(content)
        scroll.viewport().setAutoFillBackground(False)
        outer.addWidget(scroll)
        layout = QVBoxLayout(content)
        self.resize(600, 760)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)
        layout.addWidget(label("Settings", "heading"))
        root_layout = layout
        account = getattr(window, "account_dialog", None)
        self.user = account.service.user if account and account.service else None
        self.account = account
        if self.user:
            layout = section(root_layout, "Account", "Your identity across the workspace.")
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
        if self.user:
            from aedrova.desktop.bud_connectors import open_connectors

            layout = section(root_layout, "Connectors", "Bring your tools into your Buds’ work.")
            connectors = button("Manage connectors…", role="outline")
            connectors.clicked.connect(lambda: open_connectors(window))
            layout.addWidget(connectors)
        layout = section(root_layout, "Appearance", "Choose a comfortable way to work.")
        self.appearance = ChoiceBox()
        self.appearance.setAccessibleName("Appearance")
        for text, value in (("Match macOS", "system"), ("Light", "light"), ("Dark", "dark")):
            self.appearance.addItem(text, value)
        self.appearance.setCurrentIndex(self.appearance.findData(window.theme_mode))
        self.appearance.currentIndexChanged.connect(
            lambda: window.set_theme(self.appearance.currentData())
        )
        layout.addWidget(self.appearance)
        self.motion = QCheckBox("Reduce motion")
        self.motion.setChecked(window.reduced_motion)
        self.motion.toggled.connect(window.reduce_motion_action.setChecked)
        layout.addWidget(self.motion)
        self.transparency = QCheckBox("Reduce transparency")
        self.transparency.setChecked(window.reduced_transparency)
        self.transparency.toggled.connect(window.reduce_transparency_action.setChecked)
        layout.addWidget(self.transparency)
        layout = section(root_layout, "Workflow", "Open project files in your preferred editor.")
        self.editor = ChoiceBox()
        self.editor.setAccessibleName("Preferred editor")
        for name in ("Visual Studio Code", "Cursor", "Xcode", "Finder"):
            self.editor.addItem(name)
        self.editor.setCurrentText(window.settings.value("editor", "Visual Studio Code"))
        self.editor.currentTextChanged.connect(
            lambda value: window.settings.setValue("editor", value)
        )
        layout.addWidget(self.editor)
        self.billing_origin = application_origin()
        if self.user:
            layout = section(root_layout, "Plan & AI access")
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
                manage = button("Plan & billing", role="outline")
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
                self.load_balance()
        layout = root_layout
        self.status = label("Preferences are saved on this Mac.", "muted", wrap=True)
        layout.addWidget(self.status)
        actions = FlowActions()
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
        layout.addLayout(actions)

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
                    f"{plan} plan · {remaining}% monthly AI capacity remaining. "
                    + reset
                    + "No automatic overage charges."
                )
            else:
                self.billing_status.setText(
                    "No active Aedrova plan for this workspace. View plans on the website."
                )

        if not self.window.connected.enqueue(
            ("managed-balance", expected, workspace), operation, completed
        ):
            self.billing_status.setText("Connection busy. Refresh usage shortly.")

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
        self.name.clear()
        self.close()
