"""Reproducible visual QA snapshots for the milestone 2 local UI."""

import json
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from aedrova.desktop.window import AedrovaWindow

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "work" / "milestone-2"
OUTPUT.mkdir(parents=True, exist_ok=True)
app = QApplication([])
app.setStyle("Fusion")
settings = QSettings(str(OUTPUT / "qa.ini"), QSettings.Format.IniFormat)
window = AedrovaWindow(settings=settings)
window.show()
records = []


def capture(name, widget=None):
    QTest.qWait(150)
    target = widget or window
    saved = target.grab().save(str(OUTPUT / f"{name}.png"))
    if not saved:
        raise RuntimeError(f"Could not save {name}")
    records.append(
        {
            "name": name,
            "width": target.width(),
            "height": target.height(),
            "theme": window.theme.name,
        }
    )


window.set_theme("light", persist=False)
capture("light-chat")
window.open_pinned()
capture("light-thread")
window.set_theme("dark", persist=False)
capture("dark-thread")
window.close_thread()
capture("dark-chat")
window.open_pinned()
window.resize(900, 680)
capture("compact-thread")
window.close_thread()
capture("compact-chat")
window.resize(1440, 940)
window.set_theme("light", persist=False)
window.select_tab(1)
capture("projects")
window.set_theme("dark", persist=False)
capture("dark-projects")
window.set_theme("light", persist=False)
window.resize(900, 680)
capture("compact-projects")
window.resize(1440, 940)
window.select_tab(3)
capture("files")
window.show_document("Product brief.md")
capture("document", window.dialog)
window.dialog.accept()
window.select_tab(0)
window.open_switcher()
window.dialog.search.setText("design")
capture("switcher", window.dialog)
window.dialog.reject()
window.create_workspace()
capture("create-workspace", window.dialog)
window.dialog.reject()
window.switch_channel("ideas")
capture("empty-channel")
window.close()
(OUTPUT / "visual-qa.json").write_text(json.dumps(records, indent=2) + "\n")
print(f"Saved {len(records)} snapshots in {OUTPUT}")
