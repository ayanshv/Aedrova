"Authenticated orchestration for the existing Space, Bud and connector services."

import json
from datetime import UTC, datetime
from pathlib import Path

from PySide6.QtCore import Qt, QThreadPool, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QListWidgetItem

from aedrova.desktop.first_use_visuals import PURPOSE_ROLES


class JourneyActions:
    def explore(self):
        QDesktopServices.openUrl(QUrl("https://aedrova.com/product"))

    def google_sign_in(self):
        if self.pending or self.signing_in or getattr(self, "transitioning", False):
            return
        self.signing_in = True
        self.sign_in.setEnabled(False)
        self.status.setText("Finish Google sign-in in your browser. Your setup stays here.")
        self.refresh_navigation()
        self.account.start_google()
        if not self.account.busy:
            self.sign_in_finished()

    def sign_in_finished(self):
        if self.signing_in and not self.account.busy:
            self.signing_in = False
            self.sign_in.setEnabled(True)
            self.status.setText(self.account.status.text())
            self.refresh_navigation()

    def authenticated(self):
        if self.closed or not self.account.service or not self.account.service.user:
            return
        self.signing_in = False
        self.owner = str(self.account.service.user.id)
        self.sign_in.hide()
        self.space_form.show()
        self.parent_space.clear()
        self.parent_space.addItem("Independent Space", None)
        for row in self.account.snapshot.get("workspaces", []):
            if row.get("can_manage_billing"):
                self.parent_space.addItem("Subspace of " + row["name"], row["id"])
        self.parent_space.setVisible(self.parent_space.count() > 1)
        self.run(lambda s: s.rpc("get_first_use_progress", {}), self.restore)

    def run(self, operation, complete):
        from aedrova.desktop.account import AccountJob

        if self.pending or self.closed or not self.owner:
            return
        service = self.account.service
        if not service or not service.user or str(service.user.id) != self.owner:
            self.status.setText("Your account changed. Close setup and sign in again.")
            return
        owner = self.owner
        self.pending = True
        self.retry.hide()
        self.refresh_navigation()
        self.status.setText("Saving your setup…")

        def perform():
            try:
                with self.scope.transport_lock:
                    return {"value": operation(service)}
            except Exception as error:
                return {
                    "error": "setup_required"
                    if getattr(error, "code", "") in {"PGRST202", "PGRST205"}
                    else "capacity"
                    if getattr(error, "code", "") == "54000"
                    else "request"
                }

        def finished(result, ok):
            if self.closed:
                return
            self.pending = False
            current = self.account.service
            if (
                not current
                or current is not service
                or not current.user
                or str(current.user.id) != owner
            ):
                self.status.setText("Your account changed. Close setup and sign in again.")
                self.refresh_navigation()
                return
            if not ok or result.get("error"):
                # Existing members can always return to their workspaces, even
                # while the new optional onboarding migration awaits rollout.
                if (
                    self.account.snapshot.get("workspaces")
                    and not self.state
                    and result.get("error") == "setup_required"
                ):
                    self.returning_user()
                    return
                self.status.setText(
                    "This build needs its onboarding database update. Your existing work is safe."
                    if result.get("error") == "setup_required"
                    else (
                        "Your Space has reached its Bud allowance. Continue without another Bud, "
                        "or manage the plan in settings."
                    )
                    if result.get("error") == "capacity"
                    else (
                        "We couldn’t confirm that update. Reload setup before retrying; "
                        "confirmed work will be kept."
                    )
                )
                self.retry.show()
            else:
                self.status.clear()
                try:
                    complete(result["value"])
                except Exception:
                    self.status.setText("Your setup is saved. Reload to finish opening your Space.")
                    self.retry.show()
            self.refresh_navigation()

        self.job = AccountJob(perform)
        self.job.signals.finished.connect(finished)
        QThreadPool.globalInstance().start(self.job)

    def local_key(self):
        return "first-use/" + str(self.owner) + "/draft"

    def draft(self):
        return {
            "name": self.space_name.text().strip(),
            "icon": self.icon_choices.currentData(),
            "purpose": self.purpose.currentData(),
            "description": self.description.text().strip(),
            "goal": self.goal.toPlainText(),
            "automatic": self.automatic.isChecked(),
            "selected_roles": [r for r, b in self.bud_choices.items() if b.isChecked()],
        }

    def save_local(self, *_):
        if not self.owner or self.closed:
            return
        self.window.settings.setValue(
            self.local_key(),
            json.dumps(
                {
                    "revision": self.state.get("revision", 0),
                    "stage": self.stage,
                    "draft": self.draft(),
                    "project_folder": getattr(self, "project_folder", ""),
                }
            ),
        )
        self.window.settings.sync()

    def apply_draft(self, draft):
        draft = draft if isinstance(draft, dict) else {}
        draft = dict(draft)
        for key in ("name", "description", "goal", "icon", "purpose"):
            if key in draft and not isinstance(draft[key], str):
                draft.pop(key)
        if not isinstance(draft.get("selected_roles", []), list):
            draft.pop("selected_roles", None)
        if not isinstance(draft.get("automatic", False), bool):
            draft.pop("automatic", None)
        self.space_name.setText(draft.get("name", ""))
        self.description.setText(draft.get("description", ""))
        for widget, key, default in (
            (self.icon_choices, "icon", "spaces"),
            (self.purpose, "purpose", "software"),
        ):
            widget.setCurrentIndex(max(0, widget.findData(draft.get(key, default))))
        self.automatic.setChecked(bool(draft.get("automatic", False)))
        self.goal.setPlainText(draft.get("goal", "")[:4000])
        for role, choice in self.bud_choices.items():
            choice.setChecked(role in draft.get("selected_roles", []))

    def restore(self, state):
        self.state = state if isinstance(state, dict) else {}
        if self.state.get("completed_at"):
            self.restore_local_project()
            self.run(lambda service: service.snapshot(), self.enter_space)
            return
        if not self.state and self.account.snapshot.get("workspaces"):
            self.returning_user()
            return
        draft = self.state.get("draft", {})
        stage = self.state.get("stage", 1)
        try:
            local = json.loads(self.window.settings.value(self.local_key(), "{}"))
        except (ValueError, TypeError):
            local = {}
        if isinstance(local, dict) and local.get("revision") == self.state.get("revision", 0):
            draft = local.get("draft", draft)
            stage = local.get("stage", stage)
        self.restore_local_project()
        self.apply_draft(draft)
        created = bool(self.state.get("workspace_id"))
        self.space_name.setReadOnly(created)
        self.description.setReadOnly(created)
        self.icon_choices.setEnabled(not created)
        self.purpose.setEnabled(not created)
        self.parent_space.setEnabled(not created)
        self.automatic.setEnabled(not created)
        self.ai_consent.setEnabled(not created)
        self.ai_consent.setChecked(bool(created and self.state.get("ai_reviewed_at")))
        try:
            stage = int(stage)
        except (ValueError, TypeError):
            stage = 2 if created else 1
        self.show_stage(min(5, max(2 if created else 1, stage)))
        self.save_local()
        if created:
            self.status.setText("Your Space is saved. Pick up where you left off.")

    def restore_local_project(self):
        try:
            local = json.loads(self.window.settings.value(self.local_key(), "{}"))
            folder = local.get("project_folder", "") if isinstance(local, dict) else ""
            candidate = (
                Path(folder).expanduser().resolve() if isinstance(folder, str) and folder else None
            )
            if (
                candidate
                and candidate.is_dir()
                and candidate not in (Path.home(), Path(candidate.anchor))
            ):
                self.project_folder = str(candidate)
                self.project_note.setText("Project selected · " + candidate.name)
        except (ValueError, TypeError, OSError):
            pass

    def returning_user(self):
        from aedrova.desktop.onboarding import account_key

        self.window.setup_offered = account_key(self.window)
        self.account.pending_intent = None
        self.closed = True
        self.accept()
        self.account.pages.setCurrentIndex(4)
        self.account.show()
        self.account.raise_()

    def reload_state(self):
        self.run(lambda s: s.rpc("get_first_use_progress", {}), self.restore)

    def persist(self, stage, after):
        draft = self.draft()
        self.run(
            lambda s: s.rpc(
                "save_first_use_progress",
                {
                    "p_revision": self.state.get("revision", 0),
                    "p_stage": stage,
                    "p_draft": draft,
                },
            ),
            lambda state: self.saved(state, after),
        )

    def saved(self, state, after):
        self.state = state
        self.save_local()
        after()

    def advance(self):
        if self.pending or self.signing_in:
            return
        if self.stage == 0:
            self.show_stage(1)
            if self.window.current_user():
                self.authenticated()
        elif self.stage == 1:
            if not self.owner:
                self.google_sign_in()
            elif self.state.get("workspace_id"):
                self.show_stage(2)
            elif not self.space_name.text().strip():
                self.status.setText("Give your Space a name to continue.")
                self.space_name.setFocus()
            elif not self.ai_consent.isChecked():
                self.status.setText("Review and allow your AI setup to continue.")
                self.ai_consent.setFocus()
            else:
                self.persist(1, self.create_space)
        elif self.stage == 3:
            selected = [r for r, c in self.bud_choices.items() if c.isChecked() and not c.active]
            if selected:
                self.run(
                    lambda s: s.rpc("activate_first_use_buds", {"p_roles": selected}),
                    lambda state: self.saved(state, lambda: self.move_to(4)),
                )
            else:
                self.move_to(4)
        elif self.stage == 5:
            self.finish_journey()
        else:
            self.move_to(self.stage + 1)

    def revoke_review(self, *_):
        self.ai_consent.setChecked(False)
        self.save_local()

    def create_space(self):
        parameters = {
            "p_parent": self.parent_space.currentData(),
            "p_allow_ai": self.ai_consent.isChecked(),
        }
        self.run(
            lambda s: s.rpc(
                "create_first_use_space",
                parameters,
            ),
            lambda state: self.saved(state, lambda: self.restore(state)),
        )

    def move_to(self, stage):
        self.persist(stage, lambda: self.show_stage(stage))

    def go_back(self):
        if not self.pending and not getattr(self, "transitioning", False):
            self.show_stage(max(0, self.stage - 1))
            self.save_local()

    def skip_stage(self):
        if self.stage in (2, 3, 4) and not self.pending:
            self.move_to(self.stage + 1)

    def load_capacity(self):
        if self.pending or not self.state.get("workspace_id"):
            return
        self.run(
            lambda s: {
                "capacity": s.bud_capacity(self.state["workspace_id"]),
                "items": s.dots(self.state["workspace_id"])["items"],
            },
            self.capacity_loaded,
        )

    def capacity_loaded(self, result):
        capacity = result["capacity"]
        self.capacity = capacity
        existing = {str(row["id"]) for row in result["items"] if not row.get("deleted_at")}
        active = {
            role: identity
            for role, identity in self.state.get("buds", {}).items()
            if identity in existing
        }
        for role, choice in self.bud_choices.items():
            choice.active = role in active
            if choice.active:
                choice.setChecked(True)
            choice.setEnabled(not choice.active and capacity is not None)
            choice.update()
        if not capacity:
            self.capacity_note.setText(
                "Bud limits are unavailable. Continue now and add Buds in workspace settings."
            )
        else:
            self.capacity_note.setText(
                f"Your Space · {capacity['used']} / {capacity['limit']} Buds "
                f"· {capacity['remaining']} available"
            )
            self.bud_selection_changed()

    def bud_selection_changed(self, *_):
        capacity = getattr(self, "capacity", None)
        if capacity:
            selected = [c for c in self.bud_choices.values() if c.isChecked() and not c.active]
            available = max(0, int(capacity["remaining"]))
            if len(selected) > available:
                sender = self.sender()
                candidates = [sender] if sender in selected else selected[available:]
                for choice in candidates:
                    choice.blockSignals(True)
                    choice.setChecked(False)
                    choice.blockSignals(False)
                self.status.setText(
                    "That reaches your team’s Bud allowance. You can add more on a larger plan."
                )
            count = sum(c.isChecked() and not c.active for c in self.bud_choices.values())
            for choice in self.bud_choices.values():
                choice.setEnabled(not choice.active and (choice.isChecked() or count < available))
        self.save_local()

    def begin_connections(self):
        role = PURPOSE_ROLES[self.purpose.currentData()]
        if role in self.state.get("buds", {}):
            self.run(
                lambda s: s.dots(self.state["workspace_id"]),
                lambda data: self.existing_context_bud(role, data),
            )
        else:
            self.run(
                lambda s: s.rpc("activate_first_use_buds", {"p_roles": [role]}),
                lambda state: self.saved(state, lambda: self.open_connector_gallery(role)),
            )

    def ensure_context_bud(self, role):
        if self.pending:
            return

        def activated(state):
            self.state = state
            self.save_local()
            gallery = self.connector_gallery

            def ready():
                identity = state["buds"][role]
                gallery.bud.setCurrentIndex(gallery.bud.findData(identity))
                gallery.connect_oauth()

            gallery.refresh(on_loaded=ready)

        self.run(lambda s: s.rpc("activate_first_use_buds", {"p_roles": [role]}), activated)

    def existing_context_bud(self, role, data):
        if any(
            str(row["id"]) == self.state["buds"][role] and not row.get("deleted_at")
            for row in data["items"]
        ):
            self.open_connector_gallery(role)
        else:
            self.run(
                lambda s: s.rpc("activate_first_use_buds", {"p_roles": [role]}),
                lambda state: self.saved(state, lambda: self.open_connector_gallery(role)),
            )

    def open_connector_gallery(self, role):
        if self.connector_gallery is None:
            from aedrova.desktop.bud_connectors import ConnectorsDialog

            self.connector_gallery = ConnectorsDialog(
                self.scope,
                selected=self.state.get("buds", {}).get(role),
                host=self.connector_host,
                available_only=True,
            )
            self.connector_layout.addWidget(self.connector_gallery)
            self.connector_gallery.bud.hide()
            self.connector_gallery.filter.hide()
            self.connector_gallery.setMinimumHeight(300 if self.width() < 760 else 420)
            self.connect_button.hide()
        self.connector_gallery.show()

    def invite_teammate(self):
        import re

        address = self.team_email.text().strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", address) or len(address) > 320:
            self.status.setText("Enter a teammate’s email address.")
            self.team_email.setFocus()
            return
        self.run(
            lambda s: s.rpc("invite_first_use_teammate", {"p_email": address}),
            self.invitation_created,
        )

    def invitation_created(self, result):
        self.state = result["progress"]
        if result.get("code"):
            self.local_codes[result["email"]] = result["code"]
        self.team_email.clear()
        self.save_local()
        self.render_invitations()
        self.status.setText(
            "Invitation created. Select it and copy its code to share with your teammate."
            if result.get("code")
            else (
                "This invitation was already created. Use its saved code, or "
                "manage it in workspace settings."
            )
        )

    def load_invitations(self):
        if self.pending or not self.state.get("workspace_id") or not self.state.get("invitations"):
            self.render_invitations()
            return
        self.run(lambda s: s.snapshot().get("invitations", []), self.invitation_status_loaded)

    def invitation_status_loaded(self, rows):
        self.invitation_rows = {str(row["id"]): row for row in rows}
        self.render_invitations()

    def render_invitations(self):
        self.invite_list.clear()
        for email in self.state.get("invitations", {}):
            row = getattr(self, "invitation_rows", {}).get(
                str(self.state["invitations"][email]), {}
            )
            status = "Created · manage in workspace settings"
            if row.get("accepted_at"):
                status = "Accepted"
            elif row.get("revoked_at"):
                status = "Revoked"
            elif row.get("expires_at"):
                expires = datetime.fromisoformat(row["expires_at"].replace("Z", "+00:00"))
                status = "Expired" if expires <= datetime.now(UTC) else "Pending · share its code"
            elif email in self.local_codes:
                status = "Pending · share its code"
            if status in ("Accepted", "Revoked", "Expired"):
                self.local_codes.pop(email, None)
            item = QListWidgetItem(email + "\n" + status)
            item.setData(Qt.ItemDataRole.UserRole, email)
            self.invite_list.addItem(item)
        if self.invite_list.count():
            self.invite_list.setCurrentRow(self.invite_list.count() - 1)
        self.copy_invite.setEnabled(bool(self.local_codes))

    def copy_invitation(self):
        item = self.invite_list.currentItem()
        code = self.local_codes.get(item.data(Qt.ItemDataRole.UserRole)) if item else None
        if code:
            QApplication.clipboard().setText(code)
            self.status.setText("Invitation code copied. Share it only with that teammate.")
        else:
            self.status.setText(
                "Codes are only shown in the session that created them. Manage "
                "this invitation in workspace settings."
            )

    def goal_changed(self):
        text = self.goal.toPlainText()
        self.goal_count.setText(f"{len(text):,} / 4,000") if hasattr(self, "goal_count") else None
        self.refresh_navigation()
        self.save_local()

    def choose_project(self):
        from aedrova.desktop.controls import choose_project

        folder = choose_project(self)
        if folder:
            self.project_folder = folder
            self.project_note.setText("Project selected · " + Path(folder).name)
            self.save_local()

    def start_new_project(self):
        from aedrova.desktop.new_project import NewProjectDialog

        dialog = NewProjectDialog(self)
        if dialog.exec() and dialog.project_path:
            self.project_folder = dialog.project_path
            self.project_note.setText("New project · " + Path(dialog.project_path).name)
            self.save_local()

    def finish_journey(self):
        goal = self.goal.toPlainText().strip()
        if not 0 < len(goal) <= 4000:
            self.status.setText("Describe your project in 1 to 4,000 characters.")
            return
        folder = getattr(self, "project_folder", "")
        if folder and (
            not Path(folder).is_dir()
            or Path(folder).resolve() in (Path.home(), Path(Path(folder).resolve().anchor))
        ):
            self.status.setText("Your project folder is no longer available. Choose it again.")
            return
        self.run(lambda s: s.rpc("complete_first_use", {"p_goal": goal}), self.completed)

    def completed(self, state):
        self.state = state
        self.run(lambda s: s.snapshot(), self.enter_space)

    def enter_space(self, snapshot):
        from aedrova.desktop.onboarding import account_key
        from aedrova.desktop.projects import binding, save_binding

        workspace = self.state["workspace_id"]
        if not any(r["id"] == workspace for r in snapshot["workspaces"]):
            self.status.setText("This Space is no longer available to your account.")
            return
        self.account.pending_workspace = workspace
        self.account.loaded(snapshot)
        draft = self.state.get("draft", {})
        previous = binding(self.window, workspace)
        config = previous or {
            "provider": "auto",
            "agent_nickname": "Aedrova",
            "ai_setup_version": 1,
            "model_policy": "managed",
            "ai_setup_pending": False,
            "auto_plan": bool(draft.get("automatic")),
            "background_build": bool(draft.get("automatic")),
        }
        folder = getattr(self, "project_folder", "")
        if folder and not previous.get("folder"):
            config["folder"] = str(Path(folder).resolve())
        save_binding(self.window, config, workspace)
        key = account_key(self.window)
        for suffix in ("/setup", "/hasCompletedOnboarding"):
            self.window.settings.setValue(key + suffix, True)
        self.window.settings.remove(self.local_key())
        self.window.settings.sync()
        self.window.setup_offered = key
        self.closed = True
        self.accept()
        self.account.open_dashboard()

    def cleanup(self, *_):
        self.save_local()
        self.closed = True
        self.opening_scene.timer.stop()
        self.progress_animation.stop()
        for name in ("transition", "exit_animation", "enter_animation"):
            animation = getattr(self, name, None)
            if animation:
                animation.stop()
        if self.connector_gallery:
            self.connector_gallery.stop_oauth()
        self.local_codes.clear()
        if self.signing_in:
            self.account.cancel_google()
