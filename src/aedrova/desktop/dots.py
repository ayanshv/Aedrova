"""Native Dot shelf, provider picker and contextual connection profile."""

from datetime import datetime
from uuid import uuid4

from PySide6.QtCore import Qt, QThreadPool, QUrl
from PySide6.QtGui import QDesktopServices

from aedrova.desktop.controls import AppDialog
from aedrova.desktop.projects import Job
from aedrova.desktop.teammate_habitat import TeamSection
from aedrova.dots.client import client
from aedrova.dots.roles import NAMES, ROLES, purpose_from, role_for, stored_role


def shelf_rows(rows):
    return [
        {
            **row,
            "paused": False,
            "config": {
                "name": row["name"],
                "color": row["color"],
                "shape": row["shape"],
                "appearance": row.get("appearance", "auto"),
                "role": row.get("role", ""),
            },
        }
        for row in rows
    ]


class DotSection(TeamSection):
    def __init__(self, window):
        super().__init__(window)
        self.title.setText("Buds")
        self.habitat.empty.setText("Your startup’s context.\nConnect your first Bud.")
        add = self.add_button
        add.clicked.disconnect()
        add.setAccessibleName("Connect or manage Buds")
        add.setToolTip("Connect or manage Buds")
        add.clicked.connect(lambda: open_dots(window))

    def mention(self, row):
        open_dots(self.window, row["id"])

    def sync(self, rows, workspace):
        cache = getattr(self.window, "dot_connection_states", {})
        user = str(self.window.current_user().id) if self.window.current_user() else ""
        rows = [{**row, **cache.get((user, row["id"], row["version"]), {})} for row in rows]
        self.title.setText("Buds" + (f" · {len(rows)}" if rows else ""))
        self.habitat.sync(shelf_rows(rows), workspace)
        for marble in self.habitat.marbles.values():
            row = marble.widget.row
            marble.widget.setAccessibleName("Open " + row["name"] + " Bud")
            marble.widget.setToolTip(
                row["name"] + " · " + row["provider"].title() + "\nClick to view connection"
            )


class DotDialog(AppDialog):
    def __init__(self, window, selected=None, *, required=False):
        super().__init__(window)
        self.window, self.workspace = window, window.workspace_id
        self.user = str(window.current_user().id)
        self.rows, self.providers, self.job = [], [], None
        self.pending = False
        self.required = required
        from aedrova.desktop.bud_setup import build_setup

        build_setup(self, window)
        self.selected_id = selected
        self.preview()
        self.refresh()

    def run(self, operation, completed):
        if (
            (self.job or self.pending)
            or self.window.workspace_id != self.workspace
            or not self.window.current_user()
            or str(self.window.current_user().id) != self.user
        ):
            return
        # Authorization polling keeps the browser instructions visible.
        loading = not bool(getattr(self, "oauth_state", None))
        self.pending = True
        self.update_controls()
        if loading:
            self.set_loading(self.pages, True, "gallery" if hasattr(self, "cards") else "form")

        def ready(value):
            if "error" in value:
                self.pending = False
                if loading:
                    self.set_loading(self.pages, False)
                self.status.setText(value["error"])
                self.update_controls()
                return
            service = value["service"]

            def work():
                try:
                    return operation(service)
                except RuntimeError as error:
                    raise ValueError(str(error)) from None
                finally:
                    service.close_context()

            self.job = Job(work)

            def finished(result):
                self.job = None
                self.pending = False
                if loading:
                    self.set_loading(self.pages, False)
                if (
                    not self.window.current_user()
                    or str(self.window.current_user().id) != self.user
                    or self.window.workspace_id != self.workspace
                ):
                    self.reject()
                    return
                if "error" in result:
                    self.status.setText(result["error"])
                else:
                    completed(result["value"])
                self.update_controls()

            self.job.signals.finished.connect(finished)
            QThreadPool.globalInstance().start(self.job)

        def fork():
            try:
                return {"service": self.window.account_dialog.service.fork_for_context()}
            except Exception:
                return {"error": "Sign in again before managing Buds."}

        accepted = self.window.connected.enqueue(
            "dot-session-" + str(uuid4()),
            fork,
            ready,
        )
        if not accepted:
            self.pending = False
            if loading:
                self.set_loading(self.pages, False)
            self.status.setText("Reconnect the workspace before managing Buds.")
            self.update_controls()

    def sync_connection_rows(self, rows):
        cache = getattr(self.window, "dot_connection_states", {})
        for row in rows:
            cache[(self.user, row["id"], row["version"])] = {
                "status": row["status"],
                "last_sync": row["last_sync"],
            }
        self.window.dot_connection_states = cache
        self.window.account_dialog.snapshot["dots"] = [
            r
            for r in self.window.account_dialog.snapshot.get("dots", [])
            if r["workspace_id"] != self.workspace
        ] + rows
        self.window.ai_team_section.sync(rows, self.workspace)
        self.window.composer.dots = rows
        self.window.thread_composer.dots = rows

    def refresh(self):
        resume_step = self.pages.currentIndex() if self.current() else None

        def fetch(service):
            api = client(service)
            return api.request("/api/dots/providers")["providers"], api.request(
                "/api/dots?workspace=" + self.workspace
            )["items"]

        def loaded(value):
            self.providers, self.rows = value
            self.sync_connection_rows(self.rows)
            self.provider.blockSignals(True)
            self.provider.clear()
            for provider in self.providers:
                self.provider.addItem(
                    provider["name"]
                    + (
                        ""
                        if provider["available"]
                        else " · Setup required"
                        if provider["id"] == "github"
                        else " · Coming next"
                    ),
                    provider["id"],
                )
            self.provider.blockSignals(False)
            self.role_changed()
            self.list.clear()
            for row in self.rows:
                self.list.addItem(row["name"] + "  ·  " + row["status"])
            index = next((i for i, r in enumerate(self.rows) if r["id"] == self.selected_id), 0)
            if self.rows:
                self.list.setCurrentRow(index)
                self.list.setVisible(True)
            else:
                self.list.setVisible(False)
                self.new_dot()
            if self.after_refresh is not None:
                step, self.after_refresh = self.after_refresh, None
                self.show_step(step)
            elif resume_step is not None and self.rows:
                self.show_step(resume_step)
            self.update_controls()
            callback, self.after_save = getattr(self, "after_save", None), None
            if callback:
                callback(self.current())

        self.run(fetch, loaded)

    def current(self):
        index = self.list.currentRow()
        return self.rows[index] if 0 <= index < len(self.rows) else None

    def admin(self):
        return any(
            m["workspace_id"] == self.workspace
            and m["user_id"] == self.user
            and m["role"] in {"owner", "admin"}
            for m in self.window.account_dialog.snapshot.get("members", [])
        )

    def select(self, index):
        row = self.current()
        if not row:
            return
        self.selected_id = row["id"]
        self.provider.setCurrentIndex(self.provider.findData(row["provider"]))
        self.name.setText(row["name"])
        self.resource.setText(row["resource"])
        self.color.setCurrentIndex(self.color.findData(row["color"]))
        self.shape.setCurrentIndex(self.shape.findData(row["shape"]))
        if self.color.findData(row["color"]) < 0:
            self.color.addItem("Custom", row["color"])
        self.color.setCurrentIndex(self.color.findData(row["color"]))
        self.appearance.setCurrentIndex(self.appearance.findData(row.get("appearance", "auto")))
        self.job_role.blockSignals(True)
        self.job_role.setCurrentIndex(self.job_role.findData(role_for(row.get("role", ""))))
        self.job_role.blockSignals(False)
        self.role.setText(purpose_from(row.get("role", "")))
        self.role_changed()
        self.instructions.setPlainText(row.get("instructions", ""))
        self.provider.setEnabled(False)
        self.resource.setEnabled(False)
        for field in (
            self.name,
            self.role,
            self.job_role,
            self.instructions,
            self.color,
            self.shape,
            self.appearance,
            self.save,
            self.remove,
        ):
            field.setEnabled(self.admin())
        self.connect.setEnabled(bool(row["tools"]))
        self.disconnect.setEnabled(bool(row["tools"]))
        updated = (
            datetime.fromtimestamp(row["last_sync"]).strftime("%b %d, %H:%M")
            if row["last_sync"]
            else "Not read yet"
        )
        self.status.setText(row["status"] + " · Last update: " + updated)
        provider_name = next(
            (p["name"] for p in self.providers if p["id"] == row["provider"]), row["provider"]
        )
        self.summary.setText(
            row["name"]
            if row["name"].casefold() == provider_name.casefold()
            else row["name"] + " · " + provider_name
        )
        self.capabilities.setText(row["permissions"] + "\n" + " · ".join(row["tools"].values()))
        self.preview()
        self.show_step(2)
        self.update_controls()

    def configured_role(self):
        specialty = self.job_role.currentData() or "builder"
        row = self.current()
        old = row.get("role", "") if row else ""
        # Preserve legacy metadata exactly until the owner changes the role or purpose.
        if row and role_for(old) == specialty and purpose_from(old) == self.role.text().strip():
            return old
        return stored_role(specialty, self.role.text())

    def role_changed(self):
        specialty = self.job_role.currentData() or "builder"
        title, core, additional = ROLES[specialty]
        providers = {p["id"]: p for p in self.providers}

        def description(key):
            if key == "llm":
                return "AI model — uses workspace AI access; provider setup required"
            provider = providers.get(key, {})
            state = (
                "available to connect"
                if provider.get("available")
                else "owner setup required"
                if key == "github"
                else "coming next"
            )
            return NAMES[key] + " — " + state

        self.recommendations.setText(
            title
            + " tools\n"
            + "\n".join(description(key) for key in core)
            + "\n\nAlso useful: "
            + ", ".join(NAMES[key] for key in additional)
            + "\nConnect tools in the gallery. Each account authorizes its own access."
        )
        if not self.current() and self.provider.count():
            suggested = next((key for key in core if self.provider.findData(key) >= 0), None)
            if suggested:
                self.provider.setCurrentIndex(self.provider.findData(suggested))
        self.preview()

    def provider_changed(self):
        provider = next((p for p in self.providers if p["id"] == self.provider.currentData()), None)
        if provider:
            if not self.name.text():
                self.name.setText("Orbit")
            self.capabilities.setText(provider["permissions"])
            self.save.setEnabled(self.admin())
            self.resource.setPlaceholderText(
                "owner/repository"
                if provider["id"] == "github"
                else provider.get("resource_hint", "Resource identifier")
            )
            self.update_controls()

    def new_dot(self):
        self.list.setCurrentRow(-1)
        self.selected_id = None
        self.name.setText("Orbit")
        self.appearance.setCurrentIndex(0)
        self.job_role.setCurrentIndex(0)
        self.role.clear()
        self.role_changed()
        self.instructions.clear()
        self.provider.setEnabled(self.admin())
        self.provider.setCurrentIndex(max(0, self.provider.findData("github")))
        self.resource.clear()
        self.resource.setEnabled(self.admin())
        self.name.setEnabled(self.admin())
        self.role.setEnabled(self.admin())
        self.job_role.setEnabled(self.admin())
        self.instructions.setEnabled(self.admin())
        self.color.setEnabled(self.admin())
        self.shape.setEnabled(self.admin())
        self.remove.setEnabled(False)
        self.connect.setEnabled(False)
        self.disconnect.setEnabled(False)
        self.summary.setText("Name it. Make it yours. Connect what matters.")
        self.status.setText("")
        self.provider_changed()
        self.show_step(0)
        self.preview()

    def preview(self):
        self.character.set_config(
            {
                "name": self.name.text() or "Bud",
                "color": self.color.currentData() or "#4388F5",
                "shape": self.shape.currentData() or "round",
                "appearance": self.appearance.currentData() or "auto",
                "role": self.configured_role(),
            }
        )
        for tile, value in self.appearance_buttons:
            tile.setChecked(self.appearance.currentData() == value)
            tile.setEnabled(self.admin())
        for tile, value in self.planet_buttons:
            tile.setChecked(self.shape.currentData() == value)
            tile.setEnabled(self.admin())
        for tile, value in self.swatch_buttons:
            selected = self.color.currentData() == value
            tile.setStyleSheet(
                "QPushButton {background:"
                + value
                + ";border-radius:14px;border:"
                + ("3px solid #FFFFFF" if selected else "2px solid transparent")
                + ";}"
            )
            tile.setEnabled(self.admin())

    def custom_color(self):
        from PySide6.QtGui import QColor
        from PySide6.QtWidgets import QColorDialog

        if not self.admin():
            return
        color = QColorDialog.getColor(QColor(self.color.currentData()), self, "Bud color")
        if color.isValid():
            value = color.name().upper()
            if self.color.findData(value) < 0:
                self.color.addItem("Custom", value)
            self.color.setCurrentIndex(self.color.findData(value))

    def show_step(self, step):
        changed = self.pages.currentIndex() != step
        self.setup_panel.setMinimumWidth(900 if step == 4 else 500)
        self.setup_panel.setMaximumWidth(1120 if step == 4 else 560)
        if step == 4:
            self.setMinimumWidth(960)
            if self.width() < 1100:
                self.resize(1100, max(800, self.height()))
            if self.embedded_connectors is None:
                from aedrova.desktop.bud_connectors import ConnectorsDialog

                self.embedded_connectors = ConnectorsDialog(
                    self.window, self.selected_id, embedded_owner=self
                )
                self.tools_layout.addWidget(self.embedded_connectors)
            else:
                self.embedded_connectors.sync_target()
        else:
            self.setMinimumWidth(600)
        self.pages.setCurrentIndex(step)
        size = {1: 128, 2: 144, 3: 100, 5: 210}.get(step, 100)
        self.character.setFixedSize(size, size)
        self.progress.setText(f"{step + 1} / 6")
        self.dots.setText("  ".join("●" if i == step else "·" for i in range(6)))
        self.back.setVisible(step > 0)
        layout = self.character_layouts.get(step)
        if layout is not None:
            layout.addWidget(self.character, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.character.setVisible(layout is not None)
        self.next.setText(
            "Start chatting →"
            if step == 5
            else "Let’s set up your Bud →"
            if step == 0
            else "Continue →"
        )
        self.exit_button.setText("Close" if self.current() else "Finish later")
        self.update_controls()
        if changed and not self.window.reduced_motion:
            self.transition.stop()
            self.transition.setStartValue(0.45)
            self.transition.setEndValue(1.0)
            self.transition.start()
        else:
            self.opacity.setOpacity(1.0)

    def update_controls(self):
        if not hasattr(self, "next"):
            return
        gallery = getattr(self, "embedded_connectors", None)
        busy = (
            self.pending
            or self.job is not None
            or bool(gallery and (gallery.pending or gallery.job))
        )
        self.back.setEnabled(not busy)
        self.list.setEnabled(not busy)
        self.next.setEnabled(not busy)
        self.new.setEnabled(self.admin() and not busy)
        self.save.setEnabled(
            self.admin()
            and not busy
            and (
                any(
                    p.get("configurable") and p["id"] == self.provider.currentData()
                    for p in self.providers
                )
                or self.current() is not None
            )
        )
        row = self.current()
        provider = next((p for p in self.providers if p["id"] == self.provider.currentData()), {})
        self.connector_gallery.setEnabled(bool(row) and not busy)
        self.connect.setText("Connect " + provider.get("name", "tool"))
        self.connect.setEnabled(bool(row and provider.get("available")) and not busy)
        self.connect.setToolTip(
            ""
            if provider.get("available")
            else "Aedrova’s owner must configure this connector. Your Bud can still be saved."
        )
        legacy_access = bool(
            row
            and row.get("provider") == "github"
            and any("." not in tool for tool in row.get("tools", {}))
        )
        self.disconnect.setText("Disconnect my GitHub OAuth access")
        self.disconnect.setEnabled(legacy_access and not busy)
        # Legacy controls are backing state only; the inline gallery owns the UI.
        self.disconnect.hide()
        self.remove.setEnabled(bool(row) and self.admin() and not busy)
        self.remove.setVisible(bool(row) and self.admin())
        self.connection_hint.setText(
            ""
            if provider.get("available")
            else "Connector setup is pending. Save your Bud now; your workspace owner "
            "must configure this connector before you can connect it. "
            "You can also use a scoped access token in Browse connectors."
        )

    def continue_setup(self):
        step = self.pages.currentIndex()
        if step < 4:
            if step == 2 and not self.name.text().strip():
                self.status.setText("Give your Bud a name first.")
                self.name.setFocus()
                return
            if step == 3 and len(self.instructions.toPlainText()) > 2000:
                self.status.setText("Keep instructions under 2,000 characters.")
                return
            self.show_step(step + 1)
        elif step == 4:
            if (
                self.current()
                and self.current().get("status") == "Connected"
                and not self.has_changes()
            ):
                sources = list(
                    dict.fromkeys(
                        c["provider"].title()
                        for c in self.current().get("connections", [])
                        if c["status"] == "Connected"
                    )
                )
                self.ready_copy.setText(
                    self.name.text()
                    + " · "
                    + (", ".join(sources) if sources else self.provider.currentText())
                )
                self.show_step(5)
            elif self.current() and not self.has_changes():
                self.status.setText("Choose a connector card and authorize a tool to finish setup.")
            else:
                self.save_dot()
        else:
            row = self.current()
            if row:
                name = row["name"]
                self.window.composer.mention_tokens[name] = "<@dot:" + row["id"] + "|" + name + ">"
                cursor = self.window.composer.editor.textCursor()
                cursor.insertText("@" + name + " ")
                self.window.composer.editor.setTextCursor(cursor)
                self.window.composer.editor.setFocus()
            self.accept()

    def has_changes(self):
        row = self.current()
        return not row or any(
            [
                self.name.text().strip() != row["name"],
                self.color.currentData() != row["color"],
                self.shape.currentData() != row["shape"],
                self.appearance.currentData() != row.get("appearance", "auto"),
                self.configured_role() != row.get("role", ""),
                self.instructions.toPlainText().strip() != row.get("instructions", ""),
            ]
        )

    def save_dot(self, checked=False, *, on_saved=None):
        row = self.current()
        if not self.admin():
            self.status.setText("Only workspace owners or admins can configure Buds.")
            return
        if not row and not any(
            p.get("configurable") and p["id"] == self.provider.currentData() for p in self.providers
        ):
            self.status.setText("This tool is not available yet. Choose an available connector.")
            return
        if not self.name.text().strip() or not self.resource.text().strip():
            self.status.setText("Add a Bud name and a tool resource before saving.")
            self.show_step(4 if self.name.text().strip() else 2)
            return
        if len(self.configured_role()) > 240:
            self.status.setText(
                "Shorten the purpose so specialty and purpose fit in 240 characters."
            )
            self.show_step(3)
            return
        if len(self.instructions.toPlainText()) > 2000:
            self.status.setText("Keep instructions under 2,000 characters.")
            self.show_step(3)
            return
        import re

        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 _-]{0,31}", self.name.text().strip()):
            self.status.setText(
                "Use letters, numbers, spaces, hyphens or underscores for the name."
            )
            self.show_step(2)
            return
        if self.provider.currentData() == "github" and not re.fullmatch(
            r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", self.resource.text().strip()
        ):
            self.status.setText("Use a repository identifier like your-team/your-project.")
            return
        parameters = {
            "p_id": row["id"] if row else None,
            "p_workspace": self.workspace,
            "p_version": row["version"] if row else 0,
            "p_provider": self.provider.currentData(),
            "p_resource": self.resource.text().strip(),
            "p_name": self.name.text().strip(),
            "p_color": self.color.currentData(),
            "p_shape": self.shape.currentData(),
            "p_appearance": self.appearance.currentData(),
            "p_role": self.configured_role(),
            "p_instructions": self.instructions.toPlainText().strip(),
        }

        def saved(value):
            self.selected_id = value["id"]
            self.after_refresh = 4
            self.after_save = on_saved
            self.refresh()

        self.run(lambda service: service.save_bud(parameters), saved)

    def open_connectors(self):
        self.show_step(4)

    def authorize(self):
        row = self.current()
        if not row:
            return
        if row["provider"] != "github":
            self.open_connectors()
            return
        self.status.setText("Connecting… Authorize only the repository you selected.")
        self.run(
            lambda service: client(service).request(
                "/api/dots/connect", {"workspace": self.workspace, "dot": row["id"]}
            ),
            lambda value: (
                QDesktopServices.openUrl(QUrl(value["url"])),
                self.status.setText("Complete GitHub authorization, then click Refresh."),
            ),
        )

    def disconnect_dot(self):
        row = self.current()
        if row:

            def disconnected(value):
                self.refresh()
                if not value["provider_revoked"]:
                    self.status.setText(
                        "Access removed. Revoke Aedrova in GitHub → Settings → Applications too."
                    )

            self.run(
                lambda service: client(service).request(
                    "/api/dots/disconnect", {"workspace": self.workspace, "dot": row["id"]}
                ),
                disconnected,
            )

    def done(self, result):
        if self.required and result == self.DialogCode.Accepted:
            row = self.current()
            if (
                not row
                or row.get("status") != "Connected"
                or self.has_changes()
                or self.pages.currentIndex() != 5
            ):
                self.status.setText("Finish configuring a Bud and connect one tool to continue.")
                return
        if self.embedded_connectors:
            self.embedded_connectors.stop_oauth()
            self.embedded_connectors.credential.clear()
        super().done(result)

    def remove_dot(self):
        row = self.current()
        if row:
            self.run(
                lambda service: client(service).request(
                    "/api/dots/remove",
                    {"workspace": self.workspace, "dot": row["id"], "version": row["version"]},
                ),
                lambda _value: self.refresh(),
            )


def open_dots(window, selected=None):
    if not window.connected or not window.current_user():
        window.notify("Sign in to connect Buds.")
        return
    dialog = DotDialog(window, selected)
    window.dots_dialog = dialog
    dialog.open()
