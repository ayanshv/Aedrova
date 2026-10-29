"""Account/workspace-scoped composer permissions and immediate revocation."""

from PySide6.QtWidgets import QMessageBox

from aedrova.agents.permissions import MODES, normalize


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
            control.setEnabled(bool(key(window)))
            control.blockSignals(False)


def change(window, value):
    value = normalize(value)
    setting = key(window)
    if not setting or value == mode(window):
        sync(window)
        return
    if value == "full":
        answer = QMessageBox.question(
            window,
            "Enable full project access?",
            MODES[value][1] + "\nOnly choose this for a project you trust.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            sync(window)
            return
    # Changing authority never silently escalates an already-running task.
    dialog = getattr(window, "build_dialog", None)
    if dialog and dialog.workspace == window.workspace_id and dialog.pending:
        dialog.invalidate()
    window.settings.setValue(setting, value)
    window.settings.sync()
    sync(window)
