"""Working account and desktop preferences; no placeholder account actions."""

from PySide6.QtWidgets import QCheckBox, QDialog, QHBoxLayout, QLineEdit, QVBoxLayout

from aedrova.desktop.controls import ChoiceBox
from aedrova.desktop.dialogs import button, label


class SettingsDialog(QDialog):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.setWindowTitle("Aedrova · Settings")
        self.setMinimumWidth(560)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)
        layout.addWidget(label("Make yourself at home.", "heading"))
        account = getattr(window, "account_dialog", None)
        self.user = account.service.user if account and account.service else None
        self.account = account
        if self.user:
            layout.addWidget(label("ACCOUNT", "section"))
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
                (getattr(self.user, "user_metadata", None) or {}).get("full_name", "")
            )
            self.name.setPlaceholderText("Your display name")
            self.name.setAccessibleName("Display name")
            self.name.setMaxLength(80)
            self.save = button("Save name", role="outline")
            self.save.clicked.connect(self.save_name)
            row.addWidget(self.name, 1)
            row.addWidget(self.save)
            layout.addLayout(row)
        layout.addWidget(label("APPEARANCE", "section"))
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
        layout.addWidget(label("EDITOR", "section"))
        self.editor = ChoiceBox()
        self.editor.setAccessibleName("Preferred editor")
        for name in ("Visual Studio Code", "Cursor", "Xcode", "Finder"):
            self.editor.addItem(name)
        self.editor.setCurrentText(window.settings.value("editor", "Visual Studio Code"))
        self.editor.currentTextChanged.connect(
            lambda value: window.settings.setValue("editor", value)
        )
        layout.addWidget(self.editor)
        self.status = label("Preferences are saved on this Mac.", "muted", wrap=True)
        layout.addWidget(self.status)
        actions = QHBoxLayout()
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
