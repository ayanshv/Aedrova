"""Guided helper installation and user-controlled GitHub device authorization."""

import re
import threading
from pathlib import Path

from PySide6.QtCore import QProcess, QProcessEnvironment, QThreadPool, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from aedrova.delivery.github import GitHub, gh_path, github_environment
from aedrova.delivery.installer import VERSION, install
from aedrova.desktop.brand import BrandMark
from aedrova.desktop.dialogs import button, label
from aedrova.desktop.projects import Job


class GitHubSetup(QDialog):
    progress = Signal(str)

    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.job = self.process = None
        self.cancelled = threading.Event()
        self.output = ""
        self.executable = None
        self.setWindowTitle("Aedrova · Connect GitHub")
        self.setMinimumSize(590, 620)
        self.resize(620, 780)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content.setObjectName("AccountPage")
        scroll.setWidget(content)
        outer.addWidget(scroll)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 30, 32, 30)
        layout.setSpacing(18)
        self.brand = BrandMark(58)
        layout.addWidget(self.brand)
        layout.addWidget(label("Your code. Ready to go.", "heading"))
        layout.addWidget(
            label(
                "A small helper connects Aedrova to GitHub, so you can publish reviewed "
                "work without leaving your team.",
                "muted",
                wrap=True,
            )
        )
        layout.addWidget(label("1 · Install GitHub's helper", "title"))
        layout.addWidget(
            label(
                f"GitHub CLI {VERSION} downloads directly from GitHub. Aedrova verifies "
                "it and installs it only for your Mac account. No Homebrew or administrator "
                "password needed. Existing installations are detected automatically.",
                "muted",
                wrap=True,
            )
        )
        self.install_button = button("Install GitHub CLI", role="primary")
        self.install_button.clicked.connect(self.install_helper)
        layout.addWidget(self.install_button)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setAccessibleName("GitHub setup progress")
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)
        layout.addWidget(label("2 · Authorize on GitHub", "title"))
        layout.addWidget(
            label(
                "Sign in on GitHub's website and review its requested permissions. "
                "Your Google login stays separate. Publishing still needs approval each time. "
                "You can connect your GitHub account later from Projects.",
                "muted",
                wrap=True,
            )
        )
        self.login_button = button("Sign in to GitHub", role="outline")
        self.login_button.clicked.connect(self.login)
        layout.addWidget(self.login_button)
        self.code = label("", "display")
        self.code.setAccessibleName("GitHub one-time code")
        self.code.hide()
        layout.addWidget(self.code)
        self.browser_button = button("Copy code & open GitHub", role="outline")
        self.browser_button.clicked.connect(self.open_browser)
        self.browser_button.hide()
        layout.addWidget(self.browser_button)
        self.status = label("", "muted", wrap=True)
        layout.addWidget(self.status)
        row = QHBoxLayout()
        self.cancel_button = button("Cancel", role="outline")
        self.cancel_button.clicked.connect(self.reject)
        self.continue_button = button("Continue to workspace", role="primary")
        self.continue_button.clicked.connect(self.complete)
        row.addWidget(self.cancel_button)
        row.addWidget(self.continue_button)
        layout.addLayout(row)
        self.progress.connect(self.status.setText)
        QApplication.instance().aboutToQuit.connect(self.reject)
        self.timeout = QTimer(self)
        self.timeout.setSingleShot(True)
        self.timeout.timeout.connect(self.login_timeout)
        account = getattr(window, "account_dialog", None)
        if account:
            account.session_closed.connect(self.reject)
        for caption in content.findChildren(QLabel):
            if caption.wordWrap():
                caption.setMinimumHeight(max(0, caption.heightForWidth(526)))
        self.detect()

    def detect(self):
        try:
            self.executable = gh_path()
        except ValueError:
            self.executable = None
        self.install_button.setEnabled(not bool(self.executable))
        self.install_button.setText("Helper ready" if self.executable else "Install GitHub CLI")
        self.login_button.setEnabled(bool(self.executable))
        self.continue_button.setEnabled(bool(self.executable))
        self.status.setText(
            "GitHub CLI detected. Sign in to enable repository access."
            if self.executable
            else "Start with the helper. The download takes a moment."
        )

    def set_busy(self, busy):
        self.install_button.setEnabled(not busy and not bool(self.executable))
        self.login_button.setEnabled(not busy and bool(self.executable))
        self.continue_button.setEnabled(not busy and bool(self.executable))
        self.progress_bar.setVisible(busy)

    def install_helper(self):
        if self.job or self.process or self.executable:
            return
        self.set_busy(True)
        self.job = Job(
            lambda: install(progress=self.progress.emit, cancelled=self.cancelled.is_set)
        )
        self.job.signals.finished.connect(self.installed)
        QThreadPool.globalInstance().start(self.job)

    @Slot(object)
    def installed(self, result):
        self.job = None
        if self.cancelled.is_set():
            return
        self.detect()
        self.set_busy(False)
        self.status.setText(result.get("error", "Helper installed. Next, sign in to GitHub."))

    def login(self):
        if self.job or self.process or not self.executable:
            return
        self.set_busy(True)
        self.output = ""
        self.code.clear()
        self.code.hide()
        self.browser_button.hide()
        self.status.setText("Requesting a one-time code from GitHub…")
        self.process = QProcess(self)
        env = github_environment()
        # Show the browser action here; do not spawn an unattended browser from a worker.
        env.update(GH_BROWSER="/usr/bin/true", BROWSER="/usr/bin/true")
        environment = QProcessEnvironment()
        for key, value in env.items():
            environment.insert(key, value)
        self.process.setProcessEnvironment(environment)
        self.process.setWorkingDirectory(str(Path.home()))
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_login)
        self.process.finished.connect(self.login_finished)
        self.process.errorOccurred.connect(self.login_error)
        self.process.start(
            self.executable,
            [
                "auth",
                "login",
                "--hostname",
                "github.com",
                "--git-protocol",
                "https",
                "--web",
                "--skip-ssh-key",
            ],
        )
        self.process.closeWriteChannel()
        self.timeout.start(10 * 60 * 1000)

    def open_browser(self):
        if self.code.text() and not self.cancelled.is_set():
            QApplication.clipboard().setText(self.code.text())
            QDesktopServices.openUrl(QUrl("https://github.com/login/device"))

    def read_login(self):
        if not self.process:
            return
        self.output = (
            self.output
            + bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace")
        )[-8192:]
        match = re.search(r"code(?:\s*:\s*|\s*\()([A-Z0-9]{4}-[A-Z0-9]{4})", self.output)
        if match:
            self.code.setText(match[1])
            self.code.show()
            self.browser_button.show()
            self.status.setText("Enter this one-time code on GitHub and approve the connection.")

    def login_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.login_finished(1)

    def login_timeout(self):
        if self.process:
            self.process.kill()
        self.status.setText("GitHub sign-in expired. Try Sign in to GitHub again.")

    def login_finished(self, exit_code, *_):
        self.timeout.stop()
        if self.process:
            self.process.deleteLater()
            self.process = None
        self.output = ""
        self.code.clear()
        self.code.hide()
        self.browser_button.hide()
        if self.cancelled.is_set():
            return
        if exit_code:
            self.set_busy(False)
            self.status.setText("GitHub sign-in did not complete. Try again when you're ready.")
            return
        self.status.setText("Checking the authorized GitHub account…")
        self.job = Job(lambda: GitHub().api("GET", "user")["login"])
        self.job.signals.finished.connect(self.verified)
        QThreadPool.globalInstance().start(self.job)

    @Slot(object)
    def verified(self, result):
        self.job = None
        if self.cancelled.is_set():
            return
        self.set_busy(False)
        if "error" in result:
            self.status.setText(result["error"])
        else:
            self.status.setText(
                "Connected as " + result["value"] + ". Choose your repo in Projects."
            )
            self.login_button.setText("Sign in again")

    def complete(self):
        if self.job or self.process or not self.executable:
            return
        self.window.settings.setValue("githubHelperOnboarded", True)
        self.window.settings.sync()
        self.accept()

    def reject(self):
        self.cancelled.set()
        self.timeout.stop()
        if self.process:
            self.process.kill()
        self.code.clear()
        self.output = ""
        super().reject()

    def closeEvent(self, event):  # noqa: N802
        self.reject()
        event.accept()


def open_github_setup(window):
    existing = getattr(window, "github_setup", None)
    if existing and not existing.cancelled.is_set() and (existing.job or existing.process):
        existing.show()
        existing.raise_()
        return
    window.github_setup = GitHubSetup(window)
    window.github_setup.show()
    window.github_setup.raise_()
