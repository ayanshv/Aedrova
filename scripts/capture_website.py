"""Capture real Qt views without OS chrome, using disposable demonstration data."""

from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from aedrova.desktop.window import AedrovaWindow

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "work/website-screenshots"
OUTPUT.mkdir(parents=True, exist_ok=True)
app = QApplication([])
app.setStyle("Fusion")
settings = QSettings(str(OUTPUT / "capture.ini"), QSettings.Format.IniFormat)
settings.clear()
window = AedrovaWindow(settings=settings)
window.resize(1440, 940)
window.show()


def capture(name, theme, tab=0):
    window.set_theme(theme, persist=False)
    window.select_tab(tab)
    if app.focusWidget():
        app.focusWidget().clearFocus()
    QTest.qWait(250)
    # centralWidget is the actual app content, excluding the native menu/title bars.
    if not window.centralWidget().grab().save(str(OUTPUT / name)):
        raise RuntimeError(f"Could not capture {name}")


capture("workspace-dark.png", "dark")
window.open_pinned()
capture("thread-light.png", "light")
window.close_thread()
capture("files-light.png", "light", 3)
capture("projects-dark.png", "dark", 1)
window.select_tab(0)
window.agent_activity(window.workspace_id, "Gathering the team’s requirements")
window.agent_event(
    window.workspace_id, "Reviewing the confirmed direction and the connected project."
)
window.agent_event(window.workspace_id, "Running: python3 -m unittest")
capture("activity-dark.png", "dark")
window.close()
print(f"Saved five distinct desktop views in {OUTPUT}. No remote service was accessed.")
