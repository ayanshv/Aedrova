"""Account/workspace-scoped composer permissions and immediate revocation."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout

from aedrova.agents.permissions import MODES, normalize
from aedrova.desktop.controls import AppDialog
from aedrova.desktop.dialogs import button, label
from aedrova.desktop.icons import icon
from aedrova.desktop.projects import binding
from aedrova.desktop.theme import permission_warning


class FullAccessDialog(AppDialog):
    """One deliberate, project-scoped choice without the native question-mark box."""

    def __init__(self, window):
        super().__init__(window)
        self.setObjectName("FullAccessConfirmation")
        self.setWindowTitle("Aedrova · Project permissions")
        self.setModal(True)
        self.setMinimumWidth(360)
        self.resize(460, 340)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 24)
        layout.setSpacing(14)
        mark = QLabel()
        mark.setFixedSize(32, 32)
        mark.setPixmap(icon("permission_full", permission_warning(window.theme)[0]).pixmap(28, 28))
        mark.setAccessibleName("Full project access")
        layout.addWidget(mark)
        layout.addWidget(label("Allow full project access?", "heading", wrap=True))
        layout.addWidget(
            label(
                "Aedrova can edit files and run commands in this project’s isolated build copy "
                "without asking each time.",
                wrap=True,
            )
        )
        folder = binding(window).get("folder", "")
        scope = label(Path(folder).name if folder else "Current workspace project", wrap=True)
        scope.setObjectName("FullAccessScope")
        scope.setToolTip(folder or "Applies only to this account and workspace’s project.")
        layout.addWidget(scope)
        layout.addWidget(
            label(
                "Applying or publishing still needs review. "
                "Network and secret protections stay on. "
                "You can change this anytime.",
                "muted",
                wrap=True,
            )
        )
        layout.addSpacing(4)
        actions = QHBoxLayout()
        actions.addStretch()
        self.cancel = button("Keep current access", role="outline")
        self.cancel.setMinimumHeight(44)
        self.cancel.setAutoDefault(False)
        self.cancel.setDefault(True)
        self.cancel.clicked.connect(self.reject)
        actions.addWidget(self.cancel)
        self.confirm = button("Enable full access")
        self.confirm.setObjectName("ConfirmFullAccess")
        self.confirm.setMinimumHeight(44)
        self.confirm.setAutoDefault(False)
        self.confirm.clicked.connect(self.accept)
        actions.addWidget(self.confirm)
        layout.addLayout(actions)
        self.cancel.setFocus(Qt.FocusReason.OtherFocusReason)


def key(window, workspace=None):
    user = window.current_user()
    return f"agent-permissions/{user.id}/{workspace or window.workspace_id}" if user else None


def mode(window, workspace=None):
    setting = key(window, workspace)
    return normalize(window.settings.value(setting, "ask")) if setting else "ask"


def sync(window):
    value = mode(window)
    for composer in (window.composer, window.thread_composer):
        control = getattr(composer, "permissions", None)
        if control:
            control.blockSignals(True)
            control.setCurrentIndex(control.findData(value))
            control.setToolTip(MODES[value][1])
            control.setProperty("permissionMode", value)
            control.style().unpolish(control)
            control.style().polish(control)
            control.update()
            control.setEnabled(bool(key(window)))
            control.blockSignals(False)


def change(window, value):
    value = normalize(value)
    setting = key(window)
    if not setting or value == mode(window):
        sync(window)
        return
    previous = mode(window)
    workspace = window.workspace_id
    folder = binding(window, workspace).get("folder")
    if value == "full":
        if FullAccessDialog(window).exec() != QDialog.DialogCode.Accepted:
            sync(window)
            return
        if (
            key(window) != setting
            or mode(window) != previous
            or binding(window, workspace).get("folder") != folder
        ):
            sync(window)
            return

    dialog = getattr(window, "build_dialog", None)
    if dialog and dialog.workspace == window.workspace_id and dialog.pending:
        dialog.invalidate()
    window.settings.setValue(setting, value)
    window.settings.sync()
    sync(window)
