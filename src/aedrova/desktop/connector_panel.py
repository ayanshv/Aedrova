"""Native explicit resource grants for a teammate, with OS-only credential storage."""

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QLineEdit, QVBoxLayout, QWidget

from aedrova.connectors.service import CATALOG, Vault, github_login_token, read, resource_id
from aedrova.desktop.controls import ChoiceBox
from aedrova.desktop.design_system import FlowActions
from aedrova.desktop.dialogs import button, label


class ConnectorPanel(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.editor, self.rows = editor, []
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.addWidget(label("Connect their tools", "sectionLabel"))
        layout.addWidget(
            label(
                "Required · Connect at least one resource. Read-only evidence is sent to your AI "
                "provider when you assign work. Tokens stay in this Mac’s Keychain, never in chat.",
                "muted",
                wrap=True,
            )
        )
        self.kind = ChoiceBox()
        for key, (name, _, _) in CATALOG.items():
            self.kind.addItem(name, key)
        layout.addWidget(self.kind)
        self.resource = QLineEdit()
        self.resource.setAccessibleName("Tool resource URL or ID")
        self.token = QLineEdit()
        self.token.setEchoMode(QLineEdit.EchoMode.Password)
        self.token.setPlaceholderText("Read-only access token · stored in Keychain")
        self.token.setAccessibleName("Connector access token")
        self.token.setMaxLength(4096)
        layout.addWidget(self.resource)
        layout.addWidget(self.token)
        actions = FlowActions()
        self.help = button("Get token ↗", role="outline")
        self.connect = button("Verify & connect", role="primary")
        self.disconnect = button("Disconnect selected tool", role="outline")
        for control in (self.help, self.connect, self.disconnect):
            actions.addWidget(control)
        layout.addLayout(actions)
        self.status = label("No tools connected yet.", "muted", wrap=True)
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        layout.addWidget(self.status)
        self.kind.currentIndexChanged.connect(self.changed)
        self.connect.clicked.connect(self.attach)
        self.disconnect.clicked.connect(self.detach)
        self.help.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(CATALOG[self.kind.currentData()][2]))
        )
        self.changed()

    def changed(self):
        key = self.kind.currentData()
        row = next((r for r in self.rows if r["tool"] == key), None)
        self.resource.setText(row["resource"] if row else "")
        self.resource.setPlaceholderText(CATALOG[key][1])
        self.token.clear()
        self.token.setPlaceholderText(
            "Optional · use your signed-in GitHub account, or paste a read-only token"
            if key == "github"
            else "Read-only access token · stored in Keychain"
        )

    def load(self, rows):
        self.rows = [dict(r) for r in rows]
        self.changed()
        self.render()

    def render(self):
        self.status.setText(
            "\n".join(
                CATALOG[r["tool"]][0] + " · " + r["resource"] + " · read-only · verify on this Mac"
                for r in self.rows
            )
            or "No tools connected yet. Connect one to save this teammate."
        )

    def permissions(self, busy, editable):
        self.setEnabled(not busy)
        self.resource.setReadOnly(not editable)
        self.connect.setEnabled(not busy and (editable or bool(self.editor.selected)))
        self.disconnect.setEnabled(not busy and bool(self.rows))

    def attach(self):
        editor = self.editor
        if editor.busy or not editor.valid():
            return
        try:
            row = {
                "tool": self.kind.currentData(),
                "resource": resource_id(self.kind.currentData(), self.resource.text()),
            }
        except ValueError as error:
            self.status.setText(str(error))
            return
        token = self.token.text().strip()
        self.token.clear()
        identity = editor.selected["id"] if editor.selected else editor.draft_id
        saved_rows = editor.selected["config"].get("connections", []) if editor.selected else []
        user, workspace = editor.user, editor.workspace
        self.status.setText("Verifying read-only resource access…")

        def work(service):
            snapshot = service.snapshot()
            if not any(
                m["user_id"] == user
                and m["workspace_id"] == workspace
                and (
                    m["role"] in {"owner", "admin"} or (m["role"] == "member" and row in saved_rows)
                )
                for m in snapshot["members"]
            ):
                raise PermissionError("Only owners/admins may change the teammate's resources.")
            credential = token or (github_login_token() if row["tool"] == "github" else "")
            read(row, credential)
            # Bound to the exact account/workspace/teammate/resource; never shared in config.
            Vault().put(user, workspace, identity, row, credential)
            return row

        def done(result):
            current = editor.selected["id"] if editor.selected else editor.draft_id
            if current != identity:
                return
            old = next((r for r in self.rows if r["tool"] == row["tool"]), None)
            if old and old != row:
                Vault().delete(user, workspace, identity, old)
            self.rows = [r for r in self.rows if r["tool"] != row["tool"]] + [result]
            self.render()
            self.status.setText(
                self.status.text().replace("verify on this Mac", "verified on this Mac")
            )
            editor.status.setText(
                "Tool connected. Save teammate to apply this resource grant."
                if editor.editable()
                else "Tool connected for your assignments on this Mac."
            )

        editor.run("connect", work, done)

    def detach(self):
        editor = self.editor
        if editor.busy or not editor.valid():
            return
        key = self.kind.currentData()
        row = next((r for r in self.rows if r["tool"] == key), None)
        if not row:
            return
        identity = editor.selected["id"] if editor.selected else editor.draft_id

        def work(_):
            Vault().delete(editor.user, editor.workspace, identity, row)
            return row

        def done(_):
            if editor.editable():
                self.rows = [r for r in self.rows if r != row]
            self.changed()
            self.render()
            editor.status.setText(
                "Disconnected on this Mac. "
                + (
                    "Save to remove the shared resource grant."
                    if editor.editable()
                    else "Your account no longer grants access to this tool."
                )
            )

        editor.run("disconnect", work, done)
