"""A themed, asynchronous release check with an explicit website handoff."""

from PySide6.QtCore import QThreadPool, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QVBoxLayout

from aedrova.agents.managed import application_origin
from aedrova.delivery.releases import VERSION, check_release, version_tuple
from aedrova.desktop.controls import AppDialog
from aedrova.desktop.dialogs import button, label
from aedrova.desktop.projects import Job


class ReleaseDialog(AppDialog):
    def __init__(self, window):
        super().__init__(window)
        self.setWindowTitle("Aedrova · Updates")
        self.resize(520, 340)
        self.origin = application_origin()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(16)
        layout.addWidget(label("Ready for what’s next.", "heading", wrap=True))
        layout.addWidget(label(f"You’re using Aedrova {VERSION}.", "muted"))
        self.status = label(
            "Check for a verified release. Nothing is installed automatically.", "muted", wrap=True
        )
        layout.addWidget(self.status)
        self.check = button("Check for updates", role="primary")
        self.check.clicked.connect(self.refresh)
        layout.addWidget(self.check)
        self.download = button("Open download page", role="outline")
        self.download.setEnabled(False)
        self.download.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(self.origin.rstrip("/") + "/download"))
        )
        layout.addWidget(self.download)
        layout.addWidget(
            label(
                "To update: quit Aedrova, replace it in Applications, then reopen. "
                "Your account and local project files stay in place. "
                "Keep the previous app until the replacement works.",
                "muted",
                wrap=True,
            )
        )

    def refresh(self):
        if not self.origin:
            self.status.setText(
                "The public release service is being prepared. No update is available yet."
            )
            return
        self.check.setEnabled(False)
        self.download.setEnabled(False)
        self.status.setText("Checking the verified release…")
        self.job = Job(lambda: check_release(self.origin))
        self.job.signals.finished.connect(self.completed)
        QThreadPool.globalInstance().start(self.job)

    def completed(self, result):
        self.check.setEnabled(True)
        if result.get("error"):
            self.status.setText(result["error"])
            return
        release = result["value"]
        newer = version_tuple(release["version"]) > version_tuple(VERSION)
        self.status.setText(
            (f"Aedrova {release['version']} is available." if newer else "You’re up to date.")
            + f" Requires macOS {release['minimum_macos']} or later. "
            "The download is signed and notarized."
        )
        self.download.setEnabled(newer)
