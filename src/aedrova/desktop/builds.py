"""Private local build studio using real provider runtimes."""

import json
import threading
import time
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import QObject, QRunnable, Qt, QThreadPool, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QVBoxLayout,
)

from aedrova.agents.checkout import changes, git, prepare
from aedrova.agents.context import authorize, gather
from aedrova.agents.managed import ManagedClient, ai_access_mode, application_ai_origin
from aedrova.agents.retrieval import retrieval_record, validate_citations
from aedrova.agents.runtime import BuildCancelled, LocalRunner, instructions
from aedrova.desktop.controls import AppDialog, ChoiceBox, choose_project
from aedrova.desktop.dialogs import button, label


class Signals(QObject):
    progress = Signal(str)
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
    ):
        super().__init__()
        self.signals = Signals()
        self.service, self.workspace = service, workspace
        self.cancelled, self.generation = cancelled, generation
        self.managed_origin = managed_origin
        self.query = query
        self.preferred_channel = preferred_channel

    def run(self):
        try:
            result = {
                "context": gather(
                    self.service,
                    self.workspace,
                    self.cancelled.is_set,
                    self.signals.progress.emit,
                    query=self.query,
                    preferred_channel=self.preferred_channel,
                )
            }
            if self.managed_origin:
                _, _, access, user = self.service.realtime_credentials()
                if user != str(self.service.user.id):
                    raise PermissionError("Your build account changed. Sign in again.")
                result["managed"] = ManagedClient(self.managed_origin, access)
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
        self.ledger = None
        self.managed_client = None
        self.run_id = None
        self.runner = LocalRunner(self.signals.progress.emit, self.permission)

    def permission(self, tool, data):
        request = {"tool": tool, "data": data, "event": threading.Event(), "allow": False}
        self.signals.permission.emit(request)
        while not request["event"].wait(0.1):
            if self.runner.cancelled.is_set():
                return False
        return request["allow"]

    def run(self):
        context_file = None
        started = time.monotonic()
        try:
            if self.runner.cancelled.is_set():
                raise BuildCancelled()
            if self.project is None:
                self.signals.progress.emit("Preparing an independent local Git copy…")
                self.project = prepare(
                    self.repository, Path.home() / "Library/Application Support/Aedrova/builds"
                )
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
            context_file = self.project.parent / "workspace-context.jsonl"
            context_file.touch(mode=0o600)
            context_file.write_text(
                retrieval_record(self.context, self.task) + "\n" + self.context.text,
                encoding="utf-8",
            )
            prompt = instructions(
                self.task, context_file, plan=self.plan, approved_plan=self.approved
            )
            if self.managed_client:
                self.signals.progress.emit("Checking your workspace’s included AI access…")
                self.runner.managed = self.managed_client.begin(
                    self.context.workspace_id, self.provider, str(uuid4())
                )
            result = self.runner.run(self.provider, self.project, prompt, plan=self.plan)
            if self.runner.cancelled.is_set():
                raise BuildCancelled()
            if self.plan:
                validate_citations(self.context, result)
            outcome = {
                "ok": True,
                "text": result,
                "project": self.project,
                "changes": changes(self.project),
                "baseline": git(self.project, "rev-parse", "HEAD").strip(),
            }
        except BuildCancelled:
            outcome = {
                "ok": False,
                "text": "Cancelled. Partial edits are retained in the build folder for review.",
                "project": self.project,
            }
        except (ValueError, TimeoutError, RuntimeError) as exc:
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
            self.ledger.record_usage(
                self.run_id,
                "planning" if self.plan else "building",
                self.provider,
                time.monotonic() - started,
                self.runner.usage,
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
        self.resize(800, 740)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)
        preferences = self.account.snapshot.get("agent_preferences", [])
        pref = next((p for p in preferences if p["workspace_id"] == self.workspace), {})
        layout.addWidget(label("BUILD TOGETHER", "section"))
        layout.addWidget(label(f"Build with {pref.get('nickname', 'Aedrova')}", "heading"))
        self.introduction = label(
            "Your agent plans, codes and tests using your saved project permissions. "
            "Enable automatic planning and execution in Project settings to begin.",
            "muted",
            wrap=True,
        )
        if ai_access_mode() == "local":
            self.introduction.setText(
                self.introduction.text() + " This internal build uses your local provider login."
            )
        layout.addWidget(self.introduction)
        row = QHBoxLayout()
        self.repository = QLineEdit()
        self.repository.setPlaceholderText("Choose a project folder")
        self.repository.setAccessibleName("Project folder")
        self.repository.setReadOnly(True)
        self.choose = button("Project settings", role="outline")
        self.choose.clicked.connect(self.configure_project)
        row.addWidget(self.repository, 1)
        row.addWidget(self.choose)
        self.provider = ChoiceBox()
        self.provider.addItem("Codex", "codex")
        self.provider.addItem("Claude Agent", "claude_code")
        self.provider.setCurrentIndex(1 if pref.get("provider") == "claude_code" else 0)
        row.addWidget(self.provider)
        layout.addLayout(row)
        layout.addWidget(label("What would you like to build?", "title"))
        self.request = QPlainTextEdit(task)
        self.request.setAccessibleName("Build request")
        self.request.setObjectName("BuildRequest")
        self.request.setPlaceholderText("What should we build? Include how you’ll know it works.")
        self.request.setMaximumHeight(110)
        layout.addWidget(self.request)
        self.consent = QCheckBox("Share accessible workspace context with the selected AI provider")
        layout.addWidget(self.consent)
        self.consent.hide()
        self.sources_button = button("Workspace context & decisions", role="outline")
        self.sources_button.clicked.connect(self.open_context)
        layout.addWidget(self.sources_button)
        layout.addWidget(
            label(
                "Context includes your accessible private chats and small text attachments. "
                "Coding happens in a separate local copy of your project files. Your original "
                "folder stays intact. Codex runs without network access for commands; Claude asks "
                "before edits and commands. Review changes after building; local "
                "application and GitHub "
                "publication each require your approval.",
                "muted",
                wrap=True,
            )
        )
        self.status = label(
            "Describe what you want to build. Your agent handles the plan and execution.",
            "muted",
            wrap=True,
        )
        self.status.setAccessibleName("Build status")
        layout.addWidget(self.status)
        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setPlaceholderText(
            "Your plan, live activity and test results will appear here."
        )
        self.output.document().setMaximumBlockCount(5000)
        layout.addWidget(self.output, 1)
        actions = QHBoxLayout()
        self.plan_button = button("Plan internally", role="primary")
        self.build_button = button("Approve plan && build", role="primary")
        self.cancel_button = button("Cancel run", role="outline")
        self.folder_button = button("Open build folder", role="outline")
        self.build_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.folder_button.setEnabled(False)
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
        self.review_button = button("Review & deliver…", role="outline")
        self.review_button.setEnabled(False)
        self.review_button.clicked.connect(self.open_review)
        layout.addWidget(self.review_button)
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
        if saved.get("provider") in {"codex", "claude_code"}:
            self.provider.setCurrentIndex(self.provider.findData(saved["provider"]))
        if saved.get("background_build") or saved.get("auto_plan"):
            self.consent.setChecked(True)
        self.provider.setEnabled(False)

    def configure_project(self):
        from aedrova.desktop.projects import open_project

        if self.workspace != self.window.workspace_id:
            self.status.setText(
                "Switch back to this workspace before changing its project settings."
            )
            return
        open_project(self.window)

    def launch_autonomous(self):
        from aedrova.desktop.projects import binding, open_project

        if self.workspace != self.window.workspace_id:
            self.status.setText("Switch back to this workspace before starting its build.")
            return
        if not binding(self.window, self.workspace).get("background_build"):
            open_project(self.window)
            return
        start_background_build(self.window, self.request.toPlainText())

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
            self.background_run = False
            self.status.setText("Project permissions changed. Send a new request after setup.")
            self.window.agent_activity(self.workspace, self.status.text())
            return
        self.start(False)

    def open_review(self):
        from aedrova.desktop.review import ReviewDialog

        if self.project and self.successful_build and not self.pending and not self.invalidated:
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
        self.cancel_button.setEnabled(busy)
        self.review_button.setEnabled(not busy and self.successful_build and not self.invalidated)
        if self.invalidated:
            self.window.build_activity.hide()
        elif busy:
            self.window.agent_activity(self.workspace, "Working · view progress")
        self.window.update_agent_cancel()

    def start(self, plan):
        if self.review_dialog and self.review_dialog.job:
            self.status.setText("Finish the active delivery action before starting another build.")
            return
        if self.review_dialog:
            self.review_dialog.revoke()
        if self.context_browser and not self.context_browser.closed:
            self.context_browser.close()
        if self.pending or self.invalidated:
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
        if len(self.request.toPlainText()) > 20000:
            self.status.setText("Keep your build request under 20,000 characters.")
            return
        if not plan and not self.approved_plan:
            return
        self.generation += 1
        generation = self.generation
        self.collection_cancelled = threading.Event()
        cancelled = self.collection_cancelled
        self.set_busy(True)
        self.status.setText("Checking access and gathering workspace context…")
        self.window.agent_activity(self.workspace, self.status.text())
        if plan:
            self.successful_build = False
            from aedrova.desktop.projects import binding, save_binding

            saved = binding(self.window, self.workspace)
            if saved:
                saved["provider"] = self.provider.currentData()
                save_binding(self.window, saved, self.workspace)
            self.output.clear()
            self.project = None
            self.context = None
            self.folder_button.setEnabled(False)
            self.approved_plan = ""
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
                self.status.setText(result["error"])
                self.window.agent_activity(self.workspace, result["error"])
                self.set_busy(False)
                return
            job = ContextJob(
                result["service"],
                self.workspace,
                cancelled,
                generation,
                result.get("managed_origin", ""),
                query=self.request.toPlainText(),
                preferred_channel=self.origin_channel,
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
                self.status.setText(result["error"])
                self.window.agent_activity(self.workspace, result["error"])
                self.set_busy(False)
                return
            context = result["context"]
            if self.background_run and not self.background_authorized():
                self.background_run = False
                self.status.setText("Project permissions changed. Send a new request after setup.")
                self.window.agent_activity(self.workspace, self.status.text())
                self.set_busy(False)
                return
            # Appended conversation does not invalidate a background plan. Its original
            # evidence must still exist unchanged; edits/deletions/retired decisions do.
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
                self.status.setText(
                    "Workspace context changed. Send a new build request "
                    "to use the latest requirements."
                )
                self.window.agent_activity(self.workspace, self.status.text())
                self.set_busy(False)
                return
            self.context = context
            self.status.setText(
                f"{'Planning' if plan else 'Building'} · {context.count} messages "
                f"across {len(context.channel_ids)} accessible channels"
            )
            self.window.agent_activity(self.workspace, self.status.text())
            self.job = BuildJob(
                context,
                self.repository.text(),
                self.request.toPlainText().strip(),
                self.provider.currentData(),
                plan,
                self.project,
                self.approved_plan,
                self.baseline,
            )
            self.job.managed_client = result.get("managed")
            if self.execution_queue and self.run_id:
                self.job.ledger = self.execution_queue.ledger
                self.job.run_id = self.run_id
                self.job.runner.lease_fd = self.execution_queue.lease.fileno()
            self.job.signals.progress.connect(self.progress)
            self.job.signals.permission.connect(self.permission)
            self.job.signals.finished.connect(self.phase_finished)
            QThreadPool.globalInstance().start(self.job)

        accepted = self.window.connected.enqueue(
            ("build-context", id(self), generation), connect_context, connected
        )
        if not accepted:
            self.set_busy(False)
            self.status.setText("The connection is busy. Please retry in a moment.")

    @Slot(str)
    def context_progress(self, text):
        if self.pending and not self.invalidated and not self.collection_cancelled.is_set():
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
        if not self.invalidated:
            if not self.output.toPlainText().endswith(text[-50000:]):
                self.output.appendPlainText(text[-50000:])
                self.window.agent_event(self.workspace, text)

    @Slot(object)
    def permission(self, request):
        try:
            if self.invalidated or not self.pending or self.job.runner.cancelled.is_set():
                return
            if self.background_run:
                # Runtime gates already constrain file paths and require the sandbox.
                # Recheck saved authority for every automatic tool approval.
                path = Path(request["data"].get("file_path", "."))
                if not path.is_absolute():
                    path = self.project / path
                scoped_edit = request["tool"] in {
                    "Edit",
                    "Write",
                } and path.resolve().is_relative_to(self.project.resolve())
                request["allow"] = self.background_authorized() and (
                    scoped_edit
                    or (
                        request["tool"] == "Bash"
                        and not request["data"].get("dangerouslyDisableSandbox")
                    )
                )
                return
            box = QMessageBox(self)
            self.permission_box = box
            self.window.agent_activity(self.workspace, "Action needs your approval")
            box.setWindowTitle("Aedrova · Approve Claude action")
            box.setTextFormat(Qt.TextFormat.PlainText)
            box.setText(
                f"Allow {request['tool']} in this build?\nReview the exact action below. "
                "Do not approve pushes, deployments or credential access."
            )
            box.setDetailedText(json.dumps(request["data"], indent=2))
            box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            box.setDefaultButton(QMessageBox.StandardButton.No)
            request["allow"] = box.exec() == QMessageBox.StandardButton.Yes
        finally:
            self.permission_box = None
            request["event"].set()

    def finished(self, result, plan):
        if self.job and self.job.runner.cancelled.is_set():
            result = {**result, "ok": False, "text": "Cancelled. Review any partial local changes."}
        self.job = None
        self.project = result.get("project")
        self.baseline = result.get("baseline", "")
        if self.invalidated:
            self.set_busy(False)
            self.output.clear()
            return
        self.folder_button.setEnabled(bool(self.project))
        self.progress(result["text"])
        if result["ok"]:
            self.approved_plan = result["text"] if plan else ""
            self.status.setText(
                "Plan prepared. Your agent will continue using the saved execution setting."
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
                self.progress("Local changes:\n" + result["changes"])
                self.progress(
                    "Ready for your next request. New plans will start from this "
                    "build's files so you can keep iterating."
                )
        else:
            self.approved_plan = ""
            self.status.setText("Run stopped. See the details below.")
            self.window.agent_activity(self.workspace, "Needs attention · open to continue")
        self.set_busy(False)
        if plan and result["ok"] and self.background_run:
            self.background_transition = True
            self.window.agent_activity(self.workspace, "Plan ready · starting background build…")
            generation = self.generation
            QTimer.singleShot(0, lambda: self.continue_background(generation))
        else:
            self.background_run = False
        self.window.build_activity.configure(
            self.window.theme, self.window.reduced_motion, self.background_transition
        )
        self.window.update_agent_cancel()

    def verify_access(self, snapshot):
        if self.background_run and not self.background_authorized():
            self.cancel()
        if self.invalidated:
            return
        try:
            if self.context_browser and not self.context_browser.closed:
                self.context_browser.check_access(snapshot)
            allowed = authorize(snapshot, self.workspace, self.user)
            if self.context and not self.context.channel_ids <= allowed:
                raise PermissionError()
        except PermissionError:
            self.invalidate()

    def invalidate(self):
        self.invalidated = True
        if self.review_dialog:
            self.review_dialog.revoke()
        if self.context_browser:
            self.context_browser.revoke()
        self.cancel()
        self.context = None
        self.approved_plan = ""
        self.request.clear()
        self.output.clear()
        self.folder_button.setEnabled(False)
        self.set_busy(bool(self.job))
        self.status.setText("Workspace access changed or you signed out. This build has stopped.")
        self.hide()

    def cancel(self):
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
                self.workspace, "Cancelled · partial files remain for review"
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
        else:
            super().reject()

    def closeEvent(self, event):  # noqa: N802
        if self.background_run:
            self.hide()
            event.ignore()
        elif self.pending:
            self.cancel()
            event.ignore()
        else:
            super().closeEvent(event)


def open_build(window, task=""):
    from aedrova.desktop.projects import binding

    if task and binding(window).get("background_build"):
        start_background_build(window, task)
        return
    existing = getattr(window, "build_dialog", None)
    if existing and not existing.invalidated:
        if existing.workspace == window.workspace_id or existing.pending:
            if task and not existing.pending:
                existing.request.setPlainText(task)
            existing.show()
            existing.raise_()
            existing.activateWindow()
            from aedrova.desktop.projects import binding

            saved = binding(window)
            if task and not existing.pending and saved.get("folder", "") != existing.binding_folder:
                existing.binding_folder = saved.get("folder", "")
                existing.repository.setText(existing.binding_folder)
            return
    if existing:
        existing.invalidate()
        if not existing.job:
            existing.deleteLater()
    dialog = BuildDialog(window, task)
    window.build_dialog = dialog
    dialog.show()
    from aedrova.desktop.projects import binding


def start_background_build(window, task):
    from aedrova.desktop.execution import execution_queue

    return execution_queue(window).submit(task)


def _start_background_build(window, task):
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
    dialog = existing or BuildDialog(window, task)
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
