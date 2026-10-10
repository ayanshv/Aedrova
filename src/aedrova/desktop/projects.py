"""Per-account, per-workspace project bindings kept locally on this Mac."""

import json
import subprocess
from pathlib import Path

from PySide6.QtCore import QObject, QRunnable, QThreadPool, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from aedrova.delivery.github import GitHub, repository_name
from aedrova.desktop.controls import AppDialog, CodingProviderChoice, choose_project
from aedrova.desktop.design_system import FlowActions
from aedrova.desktop.dialogs import button, label


def binding_key(user, workspace):
    return f"projects/{user}/{workspace}"


def binding(window, workspace=None):
    user = window.current_user()
    if not user:
        return {}
    value = window.settings.value(binding_key(str(user.id), workspace or window.workspace_id), "{}")
    try:
        data = json.loads(value)
        return data if isinstance(data, dict) else {}
    except (ValueError, TypeError):
        return {}


def save_binding(window, data, workspace=None):
    user = window.current_user()
    if not user:
        raise PermissionError("Sign in before connecting a project.")
    window.settings.setValue(
        binding_key(str(user.id), workspace or window.workspace_id), json.dumps(data)
    )
    window.settings.sync()


def open_editor(window, project):
    project = Path(project).resolve(strict=True)
    editor = window.settings.value("editor", "Visual Studio Code")
    if editor == "Finder":
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(project)))
        return
    apps = {
        "Visual Studio Code": "com.microsoft.VSCode",
        "Cursor": "com.todesktop.230313mzl4w4u92",
        "Xcode": "com.apple.dt.Xcode",
    }
    if editor not in apps:
        raise ValueError("Choose an installed editor in Settings.")
    try:
        result = subprocess.run(
            ["/usr/bin/open", "-b", apps[editor], str(project)], capture_output=True, timeout=10
        )
    except subprocess.TimeoutExpired as exc:
        raise ValueError("The editor did not respond. Open it and retry.") from exc
    if result.returncode:
        raise ValueError(f"Install {editor}, or choose another editor in Settings.")


class JobSignals(QObject):
    finished = Signal(object)


class Job(QRunnable):
    def __init__(self, operation):
        super().__init__()
        self.operation = operation
        self.signals = JobSignals()

    def run(self):
        try:
            result = {"value": self.operation()}
        except (ValueError, PermissionError) as exc:
            result = {"error": str(exc)}
        except Exception:
            result = {
                "error": "The action did not finish. Check the connection and current "
                "state before retrying."
            }
        self.signals.finished.emit(result)


class ProjectDialog(AppDialog):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.workspace = window.workspace_id
        self.user = str(window.current_user().id)
        self.job = None
        self.connected_repo = ""
        data = binding(window)
        self.setWindowTitle("Aedrova · Project connection")
        self.setMinimumSize(650, 600)
        self.resize(650, 760)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content.setObjectName("AccountPage")
        scroll.setWidget(content)
        outer.addWidget(scroll)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)
        layout.addWidget(label("A home for your team's code.", "heading"))
        layout.addWidget(
            label(
                "This connection is private to your account on this Mac. Build copies "
                "protect your current files.",
                "muted",
                wrap=True,
            )
        )
        self.folder = QLineEdit(data.get("folder", ""))
        self.folder.setAccessibleName("Project folder")
        self.folder.setMinimumHeight(46)
        self.folder.setPlaceholderText("Paste a local folder path or choose a folder")
        row = QHBoxLayout()
        row.addWidget(self.folder, 1)
        choose = button("Choose folder", role="outline")
        choose.clicked.connect(self.choose)
        row.addWidget(choose)
        layout.addLayout(row)
        layout.addWidget(label("GitHub repository · optional", "title"))
        self.repository = QLineEdit(data.get("repository", ""))
        self.repository.setAccessibleName("GitHub repository")
        self.repository.setMinimumHeight(46)
        self.repository.setPlaceholderText("owner/repository")
        self.repository.textChanged.connect(lambda: setattr(self, "connected_repo", ""))
        layout.addWidget(self.repository)
        self.check = button("Check GitHub connection", role="outline")
        self.check.clicked.connect(self.check_github)
        layout.addWidget(self.check)
        setup = button("Set up GitHub · install or sign in", role="outline")
        setup.clicked.connect(self.github_setup)
        layout.addWidget(setup)
        layout.addWidget(
            label(
                "GitHub uses your existing GitHub CLI login. Aedrova never asks for a "
                "token. Publishing requires a separate review and approval.",
                "muted",
                wrap=True,
            )
        )
        layout.addWidget(label("Coding provider", "title"))
        self.provider = CodingProviderChoice()
        self.provider.setAccessibleName("Coding provider")
        preferences = window.account_dialog.snapshot.get("agent_preferences", [])
        default = next(
            (
                p.get("provider", "codex")
                for p in preferences
                if p["workspace_id"] == self.workspace
            ),
            "codex",
        )
        self.provider.setCurrentIndex(self.provider.findData(data.get("provider", default)))
        layout.addWidget(self.provider)
        self.auto_plan = QCheckBox("Let my agent plan and execute automatically")
        self.auto_plan.setChecked(data.get("background_build", data.get("auto_plan", True)))
        layout.addWidget(self.auto_plan)
        layout.addWidget(
            label(
                "Each explicit mention shares your accessible workspace chats with this provider "
                "and authorizes planning, edits and sandboxed test commands in a separate build "
                "copy, without further prompts. Provider usage may be billed. Applying to your "
                "original folder and publishing still require approval. Turn this off anytime.",
                "muted",
                wrap=True,
            )
        )
        self.status = label(
            "Connect once, then start your next build from chat.", "muted", wrap=True
        )
        layout.addWidget(self.status)
        actions = FlowActions()
        disconnect = button("Disconnect project", role="outline")
        disconnect.clicked.connect(self.disconnect)
        save = button("Save connection", role="primary")
        save.clicked.connect(self.save)
        actions.addWidget(disconnect)
        actions.addWidget(save)
        layout.addLayout(actions)
        for caption in content.findChildren(QLabel):
            if caption.wordWrap():
                caption.setMinimumHeight(max(0, caption.heightForWidth(580)))
        window.account_dialog.session_closed.connect(self.revoke)

    def choose(self):
        path = choose_project(self, self.folder.text())
        if path:
            self.folder.setText(path)

    def github_setup(self):
        from aedrova.desktop.github_setup import open_github_setup

        open_github_setup(self.window)

    def check_github(self):
        if self.job:
            return
        try:
            repo = repository_name(self.repository.text())
        except ValueError as exc:
            self.status.setText(str(exc))
            return
        self.check.setEnabled(False)
        self.status.setText("Checking repository access…")
        self.job = Job(lambda: GitHub().connection(repo))
        self.job.signals.finished.connect(self.checked)
        QThreadPool.globalInstance().start(self.job)

    @Slot(object)
    def checked(self, result):
        self.job = None
        self.check.setEnabled(True)
        if not self.user:
            return
        if "error" in result:
            self.status.setText(result["error"])
        else:
            self.connected_repo = result["value"]["repository"]
            self.status.setText(
                "Connected to " + self.connected_repo + ". Each push is reviewed separately."
            )

    def save(self):
        if (
            not self.user
            or self.window.current_user() is None
            or str(self.window.current_user().id) != self.user
        ):
            return
        try:
            root = Path(self.folder.text()).expanduser().resolve(strict=True)
            if not root.is_dir() or root in {Path.home(), Path(root.anchor)}:
                raise ValueError("Choose a specific project folder.")
            repo = repository_name(self.repository.text()) if self.repository.text().strip() else ""
            data = binding(self.window, self.workspace)
            data.update(
                folder=str(root),
                repository=repo,
                auto_plan=self.auto_plan.isChecked(),
                background_build=self.auto_plan.isChecked(),
                provider=self.provider.currentData(),
            )
            save_binding(self.window, data, self.workspace)
            self.stop_revoked_build()
            self.window._render_pages()
            self.accept()
        except (ValueError, OSError) as exc:
            self.status.setText(str(exc))

    def stop_revoked_build(self):
        build = getattr(self.window, "build_dialog", None)
        if build and build.background_run and not build.background_authorized():
            build.cancel()

    def disconnect(self):
        if self.user:
            self.window.settings.remove(binding_key(self.user, self.workspace))
            self.stop_revoked_build()
            self.window._render_pages()
        self.close()

    def revoke(self):
        self.user = ""
        self.folder.clear()
        self.repository.clear()
        self.close()


def open_project(window):
    if not window.current_user():
        window.show_account()
        return
    window.project_dialog = ProjectDialog(window)
    window.project_dialog.show()
