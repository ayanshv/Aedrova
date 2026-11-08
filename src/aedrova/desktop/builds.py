"""Private local build studio using real provider runtimes."""

import json
import threading
import time
from contextlib import nullcontext
from dataclasses import replace
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from aedrova.agents.checkout import changes, git, prepare
from aedrova.agents.context import authorize, gather
from aedrova.agents.file_lock import open_private_file
from aedrova.agents.managed import ManagedClient, ai_access_mode, application_ai_origin
from aedrova.agents.retrieval import retrieval_record, validate_citations
from aedrova.agents.runtime import (
    CLARIFICATION,
    BuildCancelled,
    LocalRunner,
    clarification_question,
    instructions,
)
from aedrova.desktop.clarification import ClarificationForm
from aedrova.desktop.controls import (
    AppDialog,
    CodingProviderChoice,
    PermissionChoice,
    choose_project,
)
from aedrova.desktop.conversation import markdown_html
from aedrova.desktop.design_system import FlowActions
from aedrova.desktop.dialogs import button, label
from aedrova.desktop.materials import system_font
from aedrova.identity.service import ReadInterrupted


class Signals(QObject):
    progress = Signal(str)
    reply = Signal(str)
    permission = Signal(object)
    finished = Signal(object)


class ContextJob(QRunnable):
    def __init__(
        self,
        service,
        workspace,
        cancelled,
        generation,
        managed_origin="",
        query="",
        preferred_channel="",
        teammate=None,
    ):
        super().__init__()
        self.signals = Signals()
        self.service, self.workspace = service, workspace
        self.cancelled, self.generation = cancelled, generation
        self.managed_origin = managed_origin
        self.query = query
        self.preferred_channel = preferred_channel
        self.teammate = teammate

    def run(self):
        try:
            batch = getattr(self.service, "background_read", None)
            with batch(self.cancelled.is_set) if batch else nullcontext():
                context = gather(
                    self.service,
                    self.workspace,
                    self.cancelled.is_set,
                    self.signals.progress.emit,
                    query=self.query,
                    preferred_channel=self.preferred_channel,
                )
            result = {"context": context}
            if self.teammate:
                live = next(
                    (
                        r
                        for r in self.service.ai_teammates(self.workspace)["items"]
                        if r["id"] == self.teammate["id"]
                    ),
                    None,
                )
                if not live or live["paused"] or live["version"] != self.teammate["version"]:
                    raise PermissionError("Teammate settings changed. Send a fresh assignment.")
                from aedrova.connectors.service import evidence

                self.signals.progress.emit("Reading the teammate’s connected tool resources…")
                external = evidence(
                    str(self.service.user.id),
                    self.workspace,
                    live,
                    cancelled=self.cancelled.is_set,
                )

                authorize(self.service.snapshot(), self.workspace, str(self.service.user.id))
                fresh = next(
                    (
                        r
                        for r in self.service.ai_teammates(self.workspace)["items"]
                        if r["id"] == live["id"]
                    ),
                    None,
                )
                if not fresh or fresh["paused"] or fresh["version"] != live["version"]:
                    raise PermissionError("Teammate settings changed during tool retrieval.")
                context = result["context"]
                result["context"] = replace(context, text=context.text + "\n" + external)
            from aedrova.agents.managed import application_origin

            if application_origin() and self.service.dots(self.workspace)["items"]:
                from aedrova.dots.client import client

                result["dot_client"] = client(self.service)
            if self.managed_origin:
                _, _, access, user = self.service.realtime_credentials()
                if user != str(self.service.user.id):
                    raise PermissionError("Your build account changed. Sign in again.")
                result["managed"] = ManagedClient(self.managed_origin, access)
        except ReadInterrupted:
            result = {"error": "Context collection cancelled."}
        except (PermissionError, ValueError, InterruptedError, TimeoutError) as exc:
            result = {"error": str(exc)}
        except Exception:
            result = {
                "error": "Could not retrieve workspace context. Check your connection "
                "and sign in again before retrying. If context decisions are not configured, "
                "the workspace owner must apply the context scalability SQL migration."
            }
        finally:
            close = getattr(self.service, "close_context", None)
            if close:
                close()
        self.signals.finished.emit({"generation": self.generation, "result": result})


class BuildJob(QRunnable):
    def __init__(
        self, context, repository, task, provider, plan, project=None, approved="", baseline=""
    ):
        super().__init__()
        self.signals = Signals()
        self.baseline = baseline
        self.context, self.repository, self.task = context, repository, task
        self.provider, self.plan, self.project, self.approved = provider, plan, project, approved
        self.teammate = None
        self.bud = None
        self.ledger = None
        self.managed_client = None
        self.dot_client = None
        self.run_id = None
        self.runner = LocalRunner(self.signals.progress.emit, self.permission)

    def permission(self, tool, data):
        request = {"tool": tool, "data": data, "event": threading.Event(), "allow": False}
        self.signals.permission.emit(request)
        deadline = time.monotonic() + self.runner.timeout
        while not request["event"].wait(0.1):
            if time.monotonic() > deadline:
                self.runner.cancel()
                return False
            if self.runner.cancelled.is_set():
                return False
        return request["allow"]

    def run(self):
        context_file = None
        retention_lease = None
        started = time.monotonic()
        try:
            if self.runner.cancelled.is_set():
                raise BuildCancelled()
            if self.provider == "auto":
                from aedrova.agents.routing import choose, runtime_candidates

                candidates = runtime_candidates(managed=self.managed_client is not None)
                if self.managed_client:
                    balance = self.managed_client.balance(self.context.workspace_id)
                    if (
                        type(balance.get("available")) not in {int, float}
                        or balance["available"] <= 0
                    ):
                        raise ValueError(
                            "Your Space has no available AI credit. Check team billing."
                        )
                    configured = {row["provider"] for row in balance.get("coding_providers", [])}
                    if not configured:
                        raise ValueError(
                            "Routing preflight unavailable. Update the server or select a provider."
                        )
                    from dataclasses import replace as candidate_replace

                    candidates = [
                        candidate_replace(
                            row, available=row.available and row.provider in configured
                        )
                        for row in candidates
                    ]
                import os
                import sys

                from aedrova.agents.routing import category, reviewed_candidates

                evaluation = (
                    ""
                    if getattr(sys, "frozen", False)
                    else os.getenv("AEDROVA_ROUTING_EVALUATION_FILE", "")
                )
                if evaluation:
                    candidates = reviewed_candidates(
                        evaluation,
                        candidates,
                        task_category=category(self.task),
                        configuration="aedrova-local-harness-v1",
                    )
                decision = choose(self.task, candidates)
                if decision.provider is None:
                    raise ValueError("This is a conversation request. Ask Aedrova in chat.")
                self.provider = decision.provider
                self.routing_decision = decision.record()
                self.signals.progress.emit(
                    "Aedrova selected " + self.provider + ": " + decision.reason
                )
            if self.teammate:
                from aedrova.connectors.service import evidence

                self.signals.progress.emit("Rechecking connected tools before this work phase…")
                external = evidence(
                    self.context.user_id,
                    self.context.workspace_id,
                    self.teammate,
                    cancelled=self.runner.cancelled.is_set,
                )

                retained = [
                    line
                    for line in self.context.text.splitlines()
                    if line and "connector_source" not in json.loads(line)
                ]
                self.context = replace(self.context, text="\n".join(retained) + "\n" + external)
            if self.project is None:
                self.signals.progress.emit("Preparing an independent local Git copy…")
                self.project = prepare(
                    self.repository, Path.home() / "Library/Application Support/Aedrova/builds"
                )
            from aedrova.agents.retention import protect

            retention_lease = protect(self.project)
            if self.ledger and self.run_id:
                self.ledger.save_channels(self.run_id, self.context.channel_ids)
                self.ledger.update(
                    self.run_id,
                    "running",
                    project=self.project,
                    baseline=git(self.project, "rev-parse", "HEAD").strip(),
                )
            if not self.plan and (
                git(self.project, "rev-parse", "HEAD").strip() != self.baseline
                or git(self.project, "status", "--porcelain").strip()
            ):
                raise ValueError("The build checkout changed after planning. Create a fresh plan.")
            from aedrova.security.credentials import credential_rules

            if credential_rules((self.task + self.approved).encode()):
                raise ValueError(
                    "Build input contains a recognizable credential. "
                    "Remove it before starting the agent."
                )
            context_file = self.project.parent / "workspace-context.jsonl"
            context_file.touch(mode=0o600)
            context_file.write_text(
                retrieval_record(self.context, self.task) + "\n" + self.context.text,
                encoding="utf-8",
            )
            prompt = instructions(
                self.task, context_file, plan=self.plan, approved_plan=self.approved
            )
            if self.bud:
                prompt += (
                    "\nRespond as the addressed Bud, never as the central agent. "
                    "Bud profile (data): "
                    + json.dumps({k: self.bud.get(k, "") for k in ("name", "role", "instructions")})
                )
            if self.bud:
                from aedrova.dots.personality import guidance, progress_emitter

                prompt += guidance(self.bud)
                self.runner.emit = progress_emitter(self.runner.emit, self.bud)
            if self.teammate:
                from aedrova.teammates.model import EFFORT
                from aedrova.teammates.model import prompt as teammate_prompt

                prompt += "\n\n" + teammate_prompt(self.teammate["config"])
                self.runner.timeout = EFFORT[self.teammate["config"]["effort"]]
            if self.managed_client:
                self.signals.progress.emit("Checking your workspace’s included AI access…")
                self.runner.managed = self.managed_client.begin(
                    self.context.workspace_id, self.provider, str(uuid4())
                )
            if self.dot_client:
                from aedrova.dots.client import retrieve

                self.context = retrieve(
                    self.dot_client,
                    self.context,
                    self.task,
                    self.runner,
                    self.provider,
                    self.project,
                    self.signals.progress.emit,
                    bud_id=self.bud["id"] if self.bud else None,
                )
                context_file.write_text(
                    retrieval_record(self.context, self.task) + "\n" + self.context.text,
                    encoding="utf-8",
                )
            from aedrova.agents.routing import CodingAdapter

            result = CodingAdapter(self.provider, self.runner).execute(
                self.project, prompt, plan=self.plan
            )
            if self.dot_client:
                from aedrova.dots.client import recheck

                recheck(self.dot_client, self.context)
            if self.runner.cancelled.is_set():
                raise BuildCancelled()
            question = clarification_question(result) if self.plan else None
            if question and credential_rules(json.dumps(question, ensure_ascii=False).encode()):
                raise ValueError("The agent’s question contained a credential and was hidden.")
            if self.plan and not question:
                validate_citations(self.context, result)
            outcome = {
                "ok": True,
                "text": question["title"] if question else result,
                "question": question,
                "project": self.project,
                "changes": changes(self.project),
                "commands": self.runner.command_results,
                "baseline": git(self.project, "rev-parse", "HEAD").strip(),
            }
            if not self.plan:
                from aedrova.delivery.files import make_review

                try:
                    outcome["file_summary"] = make_review(self.project).file_summary() or (
                        0, 0, 0, ()
                    )
                except (OSError, ValueError):
                    pass  # The review dialog can explain why these files need attention.
        except BuildCancelled:
            outcome = {
                "ok": False,
                "text": "Cancelled. Partial edits are retained in the build folder for review.",
                "project": self.project,
            }
        except (ValueError, TimeoutError, RuntimeError, PermissionError) as exc:
            outcome = {"ok": False, "text": str(exc), "project": self.project}
        except Exception:
            outcome = {
                "ok": False,
                "text": "The provider could not run. Check its "
                "installation, authentication and account access.",
                "project": self.project,
            }
        finally:
            if context_file:
                context_file.unlink(missing_ok=True)
            if retention_lease:
                try:
                    (self.project.parent / ".last-used").touch(mode=0o600)
                except OSError:

                    pass
                finally:
                    retention_lease.close()
            if self.managed_client:
                try:
                    self.managed_client.close()
                except RuntimeError:
                    self.signals.progress.emit(
                        "Build access cleanup could not sync. It expires automatically; "
                        "check workspace usage before retrying."
                    )
                self.runner.managed = None
        if self.ledger and self.run_id:
            decision = getattr(self, "routing_decision", None)
            if decision:
                self.ledger.record_route(
                    self.run_id,
                    "planning" if self.plan else "building",
                    decision,
                    "cancelled"
                    if self.runner.cancelled.is_set()
                    else "completed"
                    if outcome.get("ok")
                    else "failed",
                )
            self.ledger.record_usage(
                self.run_id,
                "planning" if self.plan else "building",
                self.provider,
                time.monotonic() - started,
                self.runner.usage,
            )
        if self.ledger and self.run_id and getattr(self, "interactive_telemetry", False):
            self.ledger.update(
                self.run_id,
                "cancelled"
                if self.runner.cancelled.is_set()
                else "completed"
                if outcome.get("ok")
                else "failed",
            )
        outcome["provider"] = self.provider
        outcome["routing"] = getattr(self, "routing_decision", None)
        outcome["commands"] = self.runner.command_results
        if not self.plan and self.project:
            try:
                path = self.project.parent / "observed-checks.json"
                with open_private_file(path, truncate=True) as stream:
                    stream.write(json.dumps(self.runner.command_results).encode("utf-8"))
            except OSError:
                self.signals.progress.emit(
                    "Observed checks could not be saved locally; "
                    "they remain available until this review closes."
                )
        self.signals.finished.emit(outcome)


class BuildDialog(AppDialog):
    def __init__(self, window, task=""):
        super().__init__(window)
        self.window, self.account = window, window.account_dialog
        self.workspace = window.workspace_id
        self.origin_channel = window.channel_id
        self.user = str(self.account.service.user.id)
        self.context = self.job = self.project = None
        self.approved_plan = ""
        self.clarification = None
        self.question_form = None
        self.baseline = ""
        self.pending = False
        self.collection_cancelled = threading.Event()
        self.generation = 0
        self.context_jobs = {}
        self.context_callbacks = {}
        self.invalidated = False
        self.permission_box = None
        self.context_browser = None
        self.review_dialog = None
        self.successful_build = False
        self.background_run = False
        self.background_transition = False
        self.background_settings = None
        self.run_id = None
        self.execution_queue = None
        self.setWindowTitle("Aedrova · Build with your team’s context")
        self.resize(720, 505)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)
        preferences = self.account.snapshot.get("agent_preferences", [])
        pref = next((p for p in preferences if p["workspace_id"] == self.workspace), {})
        layout.addWidget(label(f"Build with {pref.get('nickname', 'Aedrova')}", "heading"))
        self.introduction = label(
            "Aedrova builds in a separate copy. Review changes before applying them.",
            "muted",
            wrap=True,
        )
        layout.addWidget(self.introduction)
        self.request_toggle = button("Show build request", role="outline")
        self.request_toggle.setCheckable(True)
        self.request_toggle.setChecked(True)
        self.request_toggle.hide()
        self.request_toggle.toggled.connect(self.show_build_request)
        layout.addWidget(self.request_toggle, alignment=Qt.AlignmentFlag.AlignLeft)
        self.setup_fields = QWidget()
        setup = QVBoxLayout(self.setup_fields)
        setup.setContentsMargins(0, 0, 0, 0)
        setup.setSpacing(12)
        layout.addWidget(self.setup_fields)
        self.request = QPlainTextEdit(task)
        self.request.setAccessibleName("Build request")
        self.request.setObjectName("BuildRequest")
        self.request.setPlaceholderText("What would you like to build?")
        self.request.setMaximumHeight(110)
        setup.addWidget(self.request)
        row = QHBoxLayout()
        row.addWidget(label("Project", "muted"))
        self.repository = QLineEdit()
        self.repository.setPlaceholderText("No project selected")
        self.repository.setAccessibleName("Project folder")
        self.repository.setReadOnly(True)
        self.choose = button("Set up project", role="outline")
        self.choose.clicked.connect(self.configure_project)
        self.repository.textChanged.connect(
            lambda path: self.choose.setText("Project settings" if path else "Set up project")
        )
        row.addWidget(self.repository, 1)
        row.addWidget(self.choose)
        self.provider = CodingProviderChoice()
        self.provider.setCurrentIndex(self.provider.findData(pref.get("provider", "auto")))
        setup.addLayout(row)
        self.permissions = PermissionChoice()
        setup.addWidget(self.permissions, alignment=Qt.AlignmentFlag.AlignLeft)
        self.permissions.currentIndexChanged.connect(self.change_permissions)
        self.consent = QCheckBox("Share accessible team context with the AI provider")
        self.consent.setToolTip(
            "This may include private chats you can access and small text attachments."
        )
        setup.addWidget(self.consent)
        details_button = button("Build details", role="outline")
        details_button.setCheckable(True)
        setup.addWidget(details_button, alignment=Qt.AlignmentFlag.AlignLeft)
        details = QWidget()
        details_layout = QVBoxLayout(details)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.addWidget(self.provider, alignment=Qt.AlignmentFlag.AlignLeft)
        self.sources_button = button("Workspace context & decisions", role="outline")
        self.sources_button.clicked.connect(self.open_context)
        details_layout.addWidget(self.sources_button, alignment=Qt.AlignmentFlag.AlignLeft)
        details_layout.addWidget(
            label(
                "Context can include private chats you can access and small text attachments. "
                "Your selected project permissions govern commands. Applying changes and "
                "publishing to GitHub each need your approval.",
                "muted",
                wrap=True,
            )
        )
        if ai_access_mode() == "local":
            details_layout.addWidget(label("Uses your local provider login.", "muted"))
        details.hide()
        details_button.toggled.connect(details.setVisible)
        setup.addWidget(details)
        self.entry_spacer = QWidget()
        layout.addWidget(self.entry_spacer, 1)
        self.status = label("", "muted", wrap=True)
        self.status.setAccessibleName("Build status")
        layout.addWidget(self.status)
        self.question_slot = QVBoxLayout()
        layout.addLayout(self.question_slot)
        self.report_tabs = QTabWidget()
        self.report_tabs.setAccessibleName("Build response and activity")
        self.response = QTextEdit()
        self.response.setObjectName("BuildResponse")
        self.response.setFont(system_font(14))
        self.response.setReadOnly(True)
        self.response.setAccessibleName("Agent response")
        self.response.setPlaceholderText("The agent’s plan and results will appear here.")
        self.report_tabs.addTab(self.response, "Response")
        self.output = QPlainTextEdit()
        self.last_progress = ""
        self.output.setReadOnly(True)
        self.output.setAccessibleName("Build activity")
        self.output.setPlaceholderText("Commands and build activity will appear here.")
        self.output.document().setMaximumBlockCount(5000)
        self.report_tabs.addTab(self.output, "Activity")
        layout.addWidget(self.report_tabs, 1)
        self.report_tabs.hide()
        actions = FlowActions()
        self.plan_button = button("Plan internally", role="primary")
        self.build_button = button("Approve plan && build", role="primary")
        self.cancel_button = button("Cancel run", role="outline")
        self.folder_button = button("Open build folder", role="outline")
        self.build_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.cancel_button.hide()
        self.folder_button.setEnabled(False)
        self.folder_button.hide()
        for control in (
            self.plan_button,
            self.build_button,
            self.cancel_button,
            self.folder_button,
        ):
            actions.addWidget(control)
        layout.addLayout(actions)
        self.plan_button.hide()
        self.build_button.hide()
        self.start_button = button("Start build", role="primary")
        self.start_button.clicked.connect(self.launch_autonomous)
        actions.insertWidget(0, self.start_button)
        self.plan_button.clicked.connect(lambda: self.start(True))
        self.build_button.clicked.connect(lambda: self.start(False))
        self.cancel_button.clicked.connect(self.cancel)
        self.folder_button.clicked.connect(self.open_folder)
        self.review_button = button("Review changes", role="primary")
        self.review_button.setEnabled(False)
        self.review_button.hide()
        self.review_button.clicked.connect(self.open_review)
        actions.addWidget(self.review_button)
        self.question_spacer = QWidget()
        self.question_spacer.hide()
        layout.addWidget(self.question_spacer, 1)
        self.account.session_closed.connect(self.invalidate)
        QApplication.instance().aboutToQuit.connect(self.cancel)
        self.request.textChanged.connect(self.invalidate_plan)
        self.provider.currentIndexChanged.connect(self.invalidate_plan)
        self.consent.toggled.connect(self.invalidate_plan)
        self.repository.textChanged.connect(self.invalidate_plan)
        from aedrova.desktop.projects import binding

        saved = binding(window, self.workspace)
        self.binding_folder = saved.get("folder", "")
        self.repository.setText(saved.get("folder", ""))
        if saved.get("provider") in {"codex", "claude_code", "auto"}:
            self.provider.setCurrentIndex(self.provider.findData(saved["provider"]))
        if saved.get("background_build") or saved.get("auto_plan"):
            self.consent.setChecked(True)
        self.provider.setEnabled(False)
        self.sync_permissions()
        self.request.setFocus()

    def configure_project(self):
        from aedrova.desktop.projects import open_project

        if self.workspace != self.window.workspace_id:
            self.status.setText(
                "Switch back to this workspace before changing its project settings."
            )
            return
        dialog = open_project(self.window)
        if dialog:
            dialog.finished.connect(self.refresh_project)

    def refresh_project(self, result):
        from aedrova.desktop.projects import binding

        if self.invalidated or result != QDialog.DialogCode.Accepted:
            return
        saved = binding(self.window, self.workspace)
        if saved.get("folder", "") != self.binding_folder:
            self.binding_folder = saved.get("folder", "")
            self.repository.setText(self.binding_folder)
        self.provider.setCurrentIndex(self.provider.findData(saved.get("provider", "auto")))
        self.consent.setChecked(bool(saved.get("background_build") or saved.get("auto_plan")))
        self.sync_permissions()

    def sync_permissions(self):
        from aedrova.desktop.agent_permissions import mode, sync_choice

        user = self.window.current_user()
        enabled = bool(
            user
            and str(user.id) == self.user
            and self.window.workspace_id == self.workspace
            and not self.invalidated
            and self.binding_folder_matches()
        )
        value = mode(self.window, self.workspace) if enabled else "ask"
        sync_choice(self.permissions, value, enabled)

    def binding_folder_matches(self):
        from aedrova.desktop.projects import binding

        saved = binding(self.window, self.workspace).get("folder", "")
        return bool(saved and saved == getattr(self, "binding_folder", ""))

    def change_permissions(self, _index):
        from aedrova.desktop.agent_permissions import change

        if self.permissions.isEnabled() and self.binding_folder_matches():
            change(self.window, self.permissions.currentData())

    def launch_autonomous(self):
        from aedrova.desktop.projects import binding

        if self.clarification:
            self.resume_with_answer()
            return
        if self.workspace != self.window.workspace_id:
            self.status.setText("Switch back to this workspace before starting its build.")
            return
        if self.approved_plan:
            self.start(False)
            return
        if not self.request.toPlainText().strip():
            self.status.setText("Describe what you want to build.")
            self.request.setFocus()
            return
        if not self.repository.text():
            self.configure_project()
            return
        if not binding(self.window, self.workspace).get("background_build"):
            self.start(True)
            return
        start_background_build(
            self.window, self.request.toPlainText(), bud=getattr(self, "bud", None)
        )

    def clear_question(self):
        self.clarification = None
        if self.question_form:
            self.question_slot.removeWidget(self.question_form)
            self.question_form.hide()
            self.question_form.deleteLater()
            self.question_form = None
            self.introduction.show()
            self.request_toggle.setChecked(True)
            self.show_build_request(True)
            self.report_tabs.show()
            self.question_spacer.hide()

    def show_build_request(self, visible):
        self.setup_fields.setVisible(visible)
        self.request_toggle.setText("Hide build request" if visible else "Show build request")

    def resume_with_answer(self):
        if not self.clarification or self.pending or self.invalidated:
            return
        user = self.window.current_user()
        if (
            not user
            or str(user.id) != self.user
            or self.workspace != self.window.workspace_id
        ):
            self.status.setText("Return to this workspace to answer.")
            return
        if self.background_run and not self.background_authorized():
            self.cancel()
            self.status.setText("Project permissions changed. Start a new build after setup.")
            return
        answers = self.question_form.answers()
        if answers is None:
            self.status.setText("Complete the required fields to continue.")
            return
        from aedrova.security.credentials import credential_rules

        exchange = json.dumps(
            {"agent_question": self.clarification["title"], "user_answers": answers},
            ensure_ascii=False,
        )
        if credential_rules(exchange.encode()):
            self.status.setText("Remove the credential from your answer before continuing.")
            return
        task = self.request.toPlainText().rstrip() + "\n\nClarification\n" + exchange
        if len(task) > 20000:
            self.status.setText("Shorten the answer to stay under the 20,000-character limit.")
            return
        self.clear_question()
        self.request.setPlainText(task)
        self.start(True)

    def background_authorized(self):
        from aedrova.desktop.projects import binding

        saved = binding(self.window, self.workspace)
        user = self.window.current_user()
        scope = (
            saved.get("folder"),
            saved.get("provider", "codex"),
            saved.get("background_build", False),
        )
        return bool(
            user
            and str(user.id) == self.user
            and scope == self.background_settings
            and scope[2]
            and not self.invalidated
            and not self.collection_cancelled.is_set()
        )

    def continue_background(self, generation):
        self.background_transition = False
        if generation != self.generation or not self.background_run:
            return
        if not self.background_authorized():
            self.stop_before_run("Project permissions changed. Send a new request after setup.")
            return
        self.start(False)

    def open_review(self):
        from aedrova.desktop.review import ReviewDialog

        user = self.window.current_user()
        if (
            user
            and str(user.id) == self.user
            and self.window.workspace_id == self.workspace
            and self.project
            and self.successful_build
            and not self.pending
            and not self.invalidated
        ):
            if self.review_dialog and not self.review_dialog.cancelled.is_set():
                self.review_dialog.show()
                self.review_dialog.raise_()
                return
            self.review_dialog = ReviewDialog(self)
            self.review_dialog.show()

    def open_context(self):
        from aedrova.desktop.context_browser import ContextBrowser

        if self.context_browser and not self.context_browser.closed:
            self.context_browser.raise_()
            return
        self.context_browser = ContextBrowser(self)
        self.context_browser.show()

    def invalidate_plan(self):
        if not self.pending:
            self.approved_plan = ""
            self.build_button.setEnabled(False)
            self.start_button.setText("Start build")

    def choose_folder(self):
        path = choose_project(self, self.repository.text())
        if path:
            self.repository.setText(path)
            self.invalidate_plan()

    def set_busy(self, busy):
        self.pending = busy
        for control in (
            self.choose,
            self.repository,
            self.request,
            self.consent,
            self.plan_button,
            self.start_button,
            self.sources_button,
        ):
            control.setEnabled(not busy and not self.invalidated)
        self.build_button.setEnabled(not busy and bool(self.approved_plan) and not self.invalidated)
        if self.clarification:
            for control in (self.choose, self.request, self.consent):
                control.setEnabled(False)
        self.cancel_button.setVisible(busy or bool(self.clarification))
        self.cancel_button.setEnabled(busy or bool(self.clarification))
        self.review_button.setEnabled(not busy and self.successful_build and not self.invalidated)
        self.review_button.setVisible(self.successful_build and not self.invalidated)
        self.folder_button.setVisible(bool(self.project) and not self.invalidated)
        if self.invalidated:
            self.window.build_activity.hide()
        elif busy:
            self.entry_spacer.hide()
            self.report_tabs.show()
            self.window.agent_activity(self.workspace, "Working · view progress")
        self.window.update_agent_cancel()

    def start(self, plan):
        user = self.window.current_user()
        if not user or str(user.id) != self.user or self.workspace != self.window.workspace_id:
            self.status.setText("Return to this workspace to run the build.")
            return
        if self.review_dialog and self.review_dialog.job:
            self.status.setText("Finish the active delivery action before starting another build.")
            return
        if self.review_dialog:
            self.review_dialog.revoke()
        if self.context_browser and not self.context_browser.closed:
            self.context_browser.close()
        if self.pending or self.invalidated or self.clarification:
            return
        if getattr(self.window, "dot_query", None):
            self.status.setText("Wait for the current response before starting a build.")
            return
        if not self.request.toPlainText().strip():
            self.status.setText("Enter what you want the AI to build in the request field above.")
            self.request.setFocus()
            return
        if not self.repository.text():
            self.status.setText("Choose a project folder. Empty folders are supported too.")
            self.choose.setFocus()
            return
        if not self.consent.isChecked():
            self.status.setText(
                "Enable workspace context sharing to let the AI use your team's chats."
            )
            self.consent.setFocus()
            return
        request = self.request.toPlainText().strip()
        if len(request) > 20000:
            self.status.setText("Keep your build request under 20,000 characters.")
            return
        from aedrova.security.credentials import credential_rules

        if credential_rules(request.encode()):
            self.status.setText("Remove the credential from your request before starting.")
            return
        if not plan and not self.approved_plan:
            return
        if plan:
            if not self.background_run:
                self.window.archive_finished_agent()
                self.window.agent_feed.clear()
                self.window.activity_channel = self.origin_channel
                from aedrova.desktop.dots import shelf_rows

                bud = getattr(self, "bud", None)
                self.window.agent_feed.character_config = (
                    shelf_rows([bud])[0]["config"] if bud else None
                )
            self.window.agent_clock.reset()
        self.generation += 1
        generation = self.generation
        self.collection_cancelled = threading.Event()
        cancelled = self.collection_cancelled
        self.set_busy(True)
        self.status.setText("Checking workspace access…")
        self.window.agent_activity(self.workspace, self.status.text())
        if plan:
            self.successful_build = False
            from aedrova.desktop.projects import binding, save_binding

            saved = binding(self.window, self.workspace)
            if saved:
                saved["provider"] = self.provider.currentData()
                save_binding(self.window, saved, self.workspace)
            self.output.clear()
            self.response.clear()
            self.last_progress = ""
            self.project = None
            self.context = None
            self.folder_button.setEnabled(False)
            self.folder_button.hide()
            self.review_button.hide()
            self.approved_plan = ""
        self.report_tabs.setCurrentWidget(self.output)
        service = self.account.service

        def connect_context():
            try:
                factory = getattr(service, "fork_for_context", None)
                return {
                    "service": factory() if factory else service,
                    "managed_origin": application_ai_origin(),
                }
            except Exception:
                return {"error": "Could not connect to your workspace. Sign in again and retry."}

        def connected(result):
            if generation != self.generation or not self.pending or self.invalidated:
                close = getattr(result.get("service"), "close_context", None)
                if close:
                    close()
                return
            if "error" in result:
                self.stop_before_run(result["error"])
                return
            job = ContextJob(
                result["service"],
                self.workspace,
                cancelled,
                generation,
                result.get("managed_origin", ""),
                query=request,
                preferred_channel=self.origin_channel,
                teammate=getattr(self, "teammate", None),
            )
            self.context_jobs[generation] = job
            self.context_callbacks[generation] = collected
            job.signals.progress.connect(self.context_progress)
            job.signals.finished.connect(self.context_finished)
            QThreadPool.globalInstance().start(job)

        def collected(result):
            if generation != self.generation or not self.pending or self.invalidated:
                return
            if "error" in result:
                self.stop_before_run(result["error"])
                return
            context = result["context"]
            user = self.window.current_user()
            if (
                not user
                or str(user.id) != self.user
                or context.user_id != self.user
                or self.account.service is not service
            ):
                self.invalidate()
                return
            if self.background_run and not self.background_authorized():
                self.stop_before_run(
                    "Project permissions changed. Send a new request after setup."
                )
                return


            if (
                not plan
                and self.background_run
                and (
                    self.context.channel_ids <= context.channel_ids
                    and set(self.context.text.splitlines()) <= set(context.text.splitlines())
                )
            ):
                context = self.context
            if not plan and (
                context.text != self.context.text or context.channel_ids != self.context.channel_ids
            ):
                self.approved_plan = ""
                self.stop_before_run(
                    "Workspace context changed. Send a new build request "
                    "to use the latest requirements."
                )
                return
            self.context = context
            memory = next(
                (
                    json.loads(line)["product_memory_snapshot"]
                    for line in context.text.splitlines()
                    if "product_memory_snapshot" in json.loads(line)
                ),
                {},
            )
            self.memory_revision = memory.get("revision", "")
            self.status.setToolTip("Product memory revision: " + self.memory_revision)
            self.status.setText(
                f"{'Planning' if plan else 'Building'} · {context.count} messages "
                f"across {len(context.channel_ids)} accessible channels"
            )
            self.window.agent_activity(self.workspace, self.status.text())
            self.job = BuildJob(
                context,
                self.repository.text(),
                request,
                self.provider.currentData(),
                plan,
                self.project,
                self.approved_plan,
                self.baseline,
            )
            from aedrova.desktop.agent_permissions import mode

            self.job.runner.permission_mode = mode(self.window, self.workspace)
            self.job.permission_mode = self.job.runner.permission_mode
            self.job.teammate = getattr(self, "teammate", None)
            self.job.bud = getattr(self, "bud", None)
            self.job.managed_client = result.get("managed")
            self.job.dot_client = result.get("dot_client")
            if self.execution_queue and self.run_id:
                self.job.ledger = self.execution_queue.ledger
                self.job.run_id = self.run_id
                self.job.runner.lease_fd = self.execution_queue.lease.fileno()
            if self.job.ledger is None:
                from PySide6.QtCore import QSettings

                from aedrova.agents.ledger import RunLedger

                directory = Path.home() / "Library/Application Support/Aedrova/execution"
                if self.window.settings.format() == QSettings.Format.IniFormat:
                    directory = Path(self.window.settings.fileName()).parent / "execution"
                self.job.ledger = RunLedger(directory)
                self.job.run_id, _ = self.job.ledger.enqueue(
                    self.user,
                    self.workspace,
                    "Interactive build phase",
                    {"request": str(uuid4()), "provider": self.provider.currentData()},
                )
                self.job.ledger.update(self.job.run_id, "running")
            self.job.interactive_telemetry = not bool(self.execution_queue and self.run_id)
            self.job.signals.progress.connect(self.progress)
            self.job.signals.permission.connect(self.permission)
            self.job.signals.finished.connect(self.phase_finished)
            QThreadPool.globalInstance().start(self.job)

        accepted = self.window.connected.enqueue(
            ("build-context", id(self), generation), connect_context, connected, priority=True
        )
        if not accepted:
            self.stop_before_run("The connection is busy. Please retry in a moment.")

    def stop_before_run(self, text):
        self.background_run = False
        self.set_busy(False)
        self.status.setText(text)
        self.response.setPlainText(text)
        self.report_tabs.setCurrentWidget(self.response)
        if self.window.agent_feed.status_row is not None:
            self.window.finish_agent_response(self.workspace, text)

    @Slot(str)
    def context_progress(self, text):
        current = self.context_jobs.get(self.generation)
        if (
            current and self.sender() is current.signals and self.pending
            and not self.invalidated and not self.collection_cancelled.is_set()
        ):
            self.status.setText(text)
            self.window.agent_activity(self.workspace, text)

    @Slot(object)
    def context_finished(self, payload):
        generation = payload["generation"]
        self.context_jobs.pop(generation, None)
        callback = self.context_callbacks.pop(generation, None)
        if generation == self.generation and callback:
            callback(payload["result"])

    @Slot(object)
    def phase_finished(self, result):
        if self.job:
            self.finished(result, self.job.plan)

    @Slot(str)
    def progress(self, text):
        if self.invalidated or text.lstrip().partition("\n")[0].strip() == CLARIFICATION:
            return
        line = text[-50000:]
        if not line or line == self.last_progress:
            return
        self.last_progress = line
        self.output.appendPlainText(line)
        teammate = getattr(self, "teammate", None)
        reporting = teammate["config"]["reporting"] if teammate else "detailed"
        now = time.monotonic()
        if reporting != "quiet" and (
            reporting == "detailed" or now - getattr(self, "last_teammate_update", 0) > 2
        ) and not self.collection_cancelled.is_set():
            self.window.agent_event(self.workspace, text)
            self.last_teammate_update = now

    @Slot(object)
    def permission(self, request):
        try:
            job = self.job
            user = self.window.current_user()
            if (
                self.invalidated
                or not self.pending
                or not job
                or job.runner.cancelled.is_set()
                or not user
                or str(user.id) != self.user
                or self.window.workspace_id != self.workspace
            ):
                return
            from aedrova.agents.permissions import automatic
            from aedrova.desktop.agent_permissions import mode

            selected = mode(self.window, self.workspace)
            if selected != getattr(self.job, "permission_mode", "ask"):
                return
            if self.background_run and not self.background_authorized():
                return
            project = getattr(job, "project", None) or self.project
            if selected == "full" or (
                selected == "auto"
                and project
                and automatic(request["tool"], request["data"], project)
            ):
                request["allow"] = True
                return
            box = QMessageBox(self)
            self.permission_box = box
            self.window.agent_activity(self.workspace, "Action needs your approval")
            box.setWindowTitle("Aedrova · Approve agent action")
            box.setTextFormat(Qt.TextFormat.PlainText)
            box.setText(f"Allow {request['tool']} in this build?")
            detail = request["data"].get("command") or request["data"].get("file_path")
            if isinstance(detail, str):
                box.setInformativeText(detail[:320] + ("…" if len(detail) > 320 else ""))
            box.setDetailedText(json.dumps(request["data"], indent=2))
            box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            box.setDefaultButton(QMessageBox.StandardButton.No)
            box.button(QMessageBox.StandardButton.Yes).setText("Allow once")
            box.button(QMessageBox.StandardButton.No).setText("Deny")
            approved = box.exec() == QMessageBox.StandardButton.Yes
            current = self.window.current_user()
            request["allow"] = (
                approved
                and not self.invalidated
                and self.pending
                and self.job is job
                and not job.runner.cancelled.is_set()
                and current
                and str(current.id) == self.user
                and self.window.workspace_id == self.workspace
                and mode(self.window, self.workspace) == selected
                and (not self.background_run or self.background_authorized())
            )
        finally:
            self.permission_box = None
            request["event"].set()

    def finished(self, result, plan):
        if result.get("provider") in {"codex", "claude_code"}:
            self.provider.blockSignals(True)
            self.provider.setCurrentIndex(self.provider.findData(result["provider"]))
            self.provider.blockSignals(False)
        if self.job and self.job.runner.cancelled.is_set():
            result = {**result, "ok": False, "text": "Cancelled. Review any partial local changes."}
        self.job = None
        if not plan:
            self.command_results = result.get("commands", [])
        self.project = result.get("project")
        self.baseline = result.get("baseline", "")
        if self.invalidated:
            self.set_busy(False)
            self.output.clear()
            self.response.clear()
            return
        self.folder_button.setEnabled(bool(self.project))
        if plan and result["ok"] and result.get("question"):
            self.clarification = result["question"]
            self.approved_plan = ""
            self.question_form = ClarificationForm(self.clarification, self.resume_with_answer)
            self.question_slot.addWidget(self.question_form)
            self.introduction.hide()
            self.request_toggle.hide()
            self.setup_fields.hide()
            self.report_tabs.hide()
            self.question_spacer.show()
            self.set_busy(False)
            self.status.setText("Waiting for your answer")
            self.start_button.setText("Send answer")
            self.window.agent_activity(self.workspace, "Build paused · answer a question")
            self.show()
            self.raise_()
            self.question_form.focus_first()
            return
        if result["ok"]:
            self.response.setHtml(markdown_html(result["text"], base_font=self.response.font()))
        else:
            self.response.setPlainText(result["text"])
        self.report_tabs.setCurrentWidget(self.response)
        self.request_toggle.show()
        self.request_toggle.setChecked(False)
        if result["ok"]:
            self.approved_plan = result["text"] if plan else ""
            self.status.setText(
                (
                    "Plan ready. Starting the build…"
                    if self.background_run
                    else "Review the plan, then approve it to start the build."
                )
                if plan
                else "Run complete. Review the agent’s test results and local changes."
            )
            self.window.agent_activity(
                self.workspace,
                "Plan ready" if plan else "Build ready · review changes",
            )
            if not plan:
                self.successful_build = True
                self.repository.setText(str(self.project))
                if result["changes"].strip():
                    self.output.appendPlainText("Local changes\n" + result["changes"])
        else:
            self.approved_plan = ""
            self.status.setText("Run stopped. See the details below.")
            self.window.agent_activity(self.workspace, "Needs attention · open to continue")
        self.set_busy(False)
        self.start_button.setText(
            "Approve plan and build" if self.approved_plan else "Start build"
        )
        analysis = bool(
            getattr(self, "teammate", None) and self.teammate["config"]["role"] != "engineering"
        )
        if analysis and plan and result["ok"]:
            self.successful_build = True
            self.approved_plan = ""
            self.status.setText(
                "Analysis complete. Sources are cited in the result; no files were edited."
            )
            self.review_button.setEnabled(False)
            self.build_button.setEnabled(False)
        if plan and result["ok"] and self.background_run and not analysis:
            self.background_transition = True
            self.window.agent_activity(self.workspace, "Plan ready · starting background build…")
            generation = self.generation
            QTimer.singleShot(0, lambda: self.continue_background(generation))
        else:
            self.background_run = False
            summary = result.get("file_summary") if result["ok"] and not plan else None
            generation = self.generation
            queue, run_id = self.execution_queue, self.run_id

            def review_current_build():
                if self.generation == generation and not self.invalidated:
                    self.open_review()
                elif queue and run_id and queue.identity() == self.user:
                    queue.show_history(selected_run=run_id)
                else:
                    self.window.notify("This build’s review is no longer open.")

            text = result["text"]
            if result["ok"] and not plan:
                commands = result.get("commands", [])
                passed = sum(check.get("state") == "passed" for check in commands)
                failed = sum(check.get("state") == "failed" for check in commands)
                unknown = len(commands) - passed - failed
                verification = (
                    f"{passed} passed · {failed} failed · {unknown} unverified"
                    if commands else "No command results were recorded."
                )
                text += f"\n\n**Recorded command results**  \n{verification}"
            self.window.finish_agent_response(
                self.workspace, text,
                source_channels=self.context.channel_ids if self.context else (),
                file_summary=summary,
                open_changes=review_current_build if summary else None,
            )
            if (
                result["ok"]
                and self.successful_build
                and not plan
                and not summary
                and self.window.workspace_id == self.workspace
            ):
                feed = self.window.agent_feed
                review = button("Review changes", role="outline")
                review.clicked.connect(review_current_build)
                feed.reply_row.column.addWidget(review, alignment=Qt.AlignmentFlag.AlignLeft)
                feed.changed.emit()
        self.window.build_activity.configure(
            self.window.theme, self.window.reduced_motion, self.background_transition
        )
        self.window.update_agent_cancel()

    def verify_memory(self, force=False):
        if self.invalidated or not self.context or getattr(self, "memory_check_pending", False):
            return
        records = [
            json.loads(line) for line in getattr(self.context, "text", "").splitlines() if line
        ]
        pinned = next((r for r in records if "product_memory_snapshot" in r), None)
        if pinned is None or not hasattr(self.account.service, "memory_list"):
            return
        if not force and time.monotonic() - getattr(self, "memory_check_at", 0) < 15:
            return
        self.memory_check_pending = True
        self.memory_check_at = time.monotonic()
        original_context = self.context

        def checked(payload):
            self.memory_check_pending = False
            if self.invalidated or self.context is not original_context:
                return
            from aedrova.memory.model import snapshot_record

            try:
                if "error" in payload:
                    raise ValueError("Memory verification unavailable")
                current = snapshot_record(payload, self.workspace, self.context.channel_ids)
                changed = current != pinned
            except (PermissionError, ValueError, KeyError):
                changed = True
            if changed:
                self.invalidated = True
                self.cancel()
                self.approved_plan = ""
                self.successful_build = False
                if self.review_dialog:
                    self.review_dialog.revoke()
                self.status.setText(
                    "Product memory changed or could not be verified. "
                    "Start a fresh build before applying changes."
                )
                self.window.agent_activity(self.workspace, self.status.text())

        def operation():
            try:
                return getattr(
                    self.account.service, "memory_context", self.account.service.memory_list
                )(self.workspace)
            except Exception:
                return {"error": "Memory verification unavailable"}

        if not self.window.connected.enqueue(
            ("build-memory", id(self)),
            operation,
            checked,
        ):
            self.memory_check_pending = False

    def verify_access(self, snapshot):
        from aedrova.desktop.agent_permissions import mode

        if self.job and hasattr(self.job, "permission_mode"):
            if self.job.permission_mode != mode(self.window, self.workspace):
                self.cancel()
                return
        bud = getattr(self, "bud", None)
        if bud:
            live = next(
                (
                    r
                    for r in snapshot.get("dots", [])
                    if r["id"] == bud["id"] and r["workspace_id"] == self.workspace
                ),
                None,
            )
            if not live or live["version"] != bud["version"]:
                self.invalidate()
                return
        teammate = getattr(self, "teammate", None)
        if teammate:
            live = next(
                (
                    r
                    for r in snapshot.get("ai_teammates", [])
                    if r["id"] == teammate["id"] and r["workspace_id"] == self.workspace
                ),
                None,
            )
            if not live or live["paused"] or live["version"] != teammate["version"]:
                self.invalidate()
                return
        self.verify_memory()
        if self.background_run and not self.background_authorized():
            self.cancel()
        if self.invalidated:
            return
        try:
            if self.context_browser and not self.context_browser.closed:
                self.context_browser.check_access(snapshot)
            allowed = authorize(snapshot, self.workspace, self.user)
            if self.origin_channel not in allowed:
                self.invalidate()
                return
            if self.context and not self.context.channel_ids <= allowed:
                raise PermissionError()
        except PermissionError:
            self.invalidate()

    def invalidate(self):
        active = self.pending or self.background_transition or self.clarification
        self.invalidated = True
        if self.review_dialog:
            self.review_dialog.revoke()
        if self.context_browser:
            self.context_browser.revoke()
        self.cancel()
        if active and getattr(self.window, "build_dialog", None) is self:
            self.window.agent_feed.clear()
        self.context = None
        self.approved_plan = ""
        self.request.clear()
        self.output.clear()
        self.response.clear()
        self.folder_button.setEnabled(False)
        self.set_busy(bool(self.job))
        self.status.setText("Workspace access changed or you signed out. This build has stopped.")
        self.hide()

    def cancel(self):
        if not (self.pending or self.background_transition or self.clarification):
            return
        self.clear_question()
        self.start_button.setText("Start build")
        self.background_run = False
        self.background_transition = False
        self.collection_cancelled.set()
        self.generation += 1
        if self.job:
            self.job.runner.cancel()
        else:
            self.set_busy(False)
        if self.permission_box:
            self.permission_box.reject()
        self.status.setText("Cancellation requested. Waiting for the provider to stop…")
        if not self.invalidated:
            self.window.agent_activity(
                self.workspace, "Stopping…" if self.job else "Cancelled"
            )
            if not self.job:
                self.window.finish_agent_response(
                    self.workspace,
                    "Cancelled. No further work will start. "
                    "Any partial local changes remain available for review.",
                )
        self.window.update_agent_cancel()

    def open_folder(self):
        if self.project and not self.invalidated:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(self.project)))

    def reject(self):
        if self.background_run:
            self.hide()
        elif self.pending:
            self.cancel()
            self.hide()
        else:
            super().reject()

    def closeEvent(self, event):  # noqa: N802


        if self.pending and not self.background_run:
            self.cancel()
        self.hide()
        event.accept()


def open_build(window, task="", *, bud=None):
    from aedrova.desktop.projects import binding

    if task and binding(window).get("background_build"):
        return (
            start_background_build(window, task, bud=bud)
            if bud
            else start_background_build(window, task)
        )
    existing = getattr(window, "build_dialog", None)
    if existing and existing.clarification and existing.workspace == window.workspace_id:
        existing.show()
        existing.raise_()
        existing.question_form.focus_first()
        return not task
    if existing and existing.pending:
        existing.show()
        existing.raise_()
        window.notify(
            "Your agent is already working. Wait or stop it before starting another build."
        )
        return False
    if existing and not existing.invalidated:
        if (
            existing.workspace == window.workspace_id
            and not getattr(existing, "teammate", None)
            and getattr(existing, "bud", None) == bud
        ):
            if task and not existing.pending:
                existing.origin_channel = window.channel_id
                existing.request.setPlainText(task)
                existing.request_toggle.setChecked(True)
            existing.show()
            existing.raise_()
            existing.activateWindow()
            from aedrova.desktop.projects import binding

            saved = binding(window)
            if task and not existing.pending and saved.get("folder", "") != existing.binding_folder:
                existing.binding_folder = saved.get("folder", "")
                existing.repository.setText(existing.binding_folder)
            return True
    if existing:
        existing.invalidate()
        if not existing.job:
            existing.deleteLater()
    dialog = BuildDialog(window, task)
    dialog.bud = bud
    from aedrova.desktop.dots import shelf_rows

    window.agent_feed.character_config = shelf_rows([bud])[0]["config"] if bud else None
    window.build_dialog = dialog
    dialog.show()
    return True


def start_background_build(window, task, *, bud=None):
    from aedrova.desktop.execution import execution_queue

    return (
        execution_queue(window).submit(task, bud=bud)
        if bud
        else execution_queue(window).submit(task)
    )


def _start_background_build(window, task, *, teammate=None, bud=None, origin_channel=None):
    """A chat mention never opens a dialog or starts a second overlapping run."""
    from aedrova.desktop.projects import binding

    saved = binding(window)
    existing = getattr(window, "build_dialog", None)
    if existing and (existing.pending or existing.background_transition):
        window.notify(
            "Your agent is already working. Stop it or wait before sending another build."
        )
        return False
    if not task.strip():
        window.notify("Tell your agent what to build after its name.")
        return False
    if not saved.get("folder") or not saved.get("background_build"):
        window.agent_setup_needed = True
        window.agent_activity(window.workspace_id, "Enable background builds in Project settings")
        return False
    if existing and existing.review_dialog and existing.review_dialog.job:
        window.notify("Finish the current delivery action before starting another build.")
        return False
    if existing and (existing.invalidated or existing.workspace != window.workspace_id):
        existing.invalidate()
        existing = None
    if existing and (
        getattr(existing, "teammate", None) != teammate or getattr(existing, "bud", None) != bud
    ):
        existing.invalidate()
        existing = None
    dialog = existing or BuildDialog(window, task)
    dialog.teammate = teammate
    dialog.bud = bud
    window.build_dialog = dialog
    window.agent_setup_needed = False
    dialog.request.setPlainText(task)
    if saved["folder"] != dialog.binding_folder:
        dialog.binding_folder = saved["folder"]
        dialog.repository.setText(saved["folder"])
    keep_iteration = False
    if (
        dialog.successful_build
        and dialog.project
        and dialog.repository.text() == str(dialog.project)
    ):
        try:
            info = json.loads((dialog.project.parent / "snapshot-info.json").read_text())
            keep_iteration = Path(info["source"]).resolve() == Path(saved["folder"]).resolve()
        except (OSError, ValueError, KeyError):
            pass
    if not keep_iteration:
        dialog.repository.setText(saved["folder"])
    dialog.provider.setCurrentIndex(dialog.provider.findData(saved.get("provider", "codex")))
    dialog.consent.setChecked(True)
    dialog.background_settings = (saved["folder"], saved.get("provider", "codex"), True)
    dialog.background_run = True
    window.agent_clock.reset()
    dialog.origin_channel = origin_channel or window.channel_id
    window.activity_channel = dialog.origin_channel
    from aedrova.desktop.dots import shelf_rows

    window.agent_feed.character_config = (
        shelf_rows([bud])[0]["config"] if bud else teammate["config"] if teammate else None
    )
    window.archive_finished_agent()
    window.agent_feed.clear()
    window.agent_feed.hide()
    window.last_agent_event = ""
    dialog.introduction.setText(
        "Background build using your saved project permissions. "
        "Keep chatting; progress and Stop are available in chat. Results stay private."
    )
    dialog.hide()
    dialog.start(True)
    if not dialog.pending:
        dialog.background_run = False
        window.agent_activity(dialog.workspace, dialog.status.text())
        return False
    return True
