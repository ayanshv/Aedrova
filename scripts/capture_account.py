"""Capture the actual unconfigured account UI without accessing any service."""

from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from aedrova.desktop.window import AedrovaWindow

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "work" / "milestone-3"
OUTPUT.mkdir(parents=True, exist_ok=True)
app = QApplication([])
app.setStyle("Fusion")
window = AedrovaWindow(settings=QSettings(str(OUTPUT / "capture.ini"), QSettings.Format.IniFormat))
window.show()
window.show_account()
for mode in ("light", "dark"):
    window.set_theme(mode, persist=False)
    QTest.qWait(200)
    if not window.account_dialog.grab().save(str(OUTPUT / f"account-{mode}.png")):
        raise RuntimeError("Screenshot failed")
window.account_dialog.close()
window.close()
