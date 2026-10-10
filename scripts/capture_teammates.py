"""Capture the native teammate editor with labelled sample data and no network calls."""

from pathlib import Path
from types import SimpleNamespace

from PySide6.QtCore import QSettings
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from aedrova.desktop.ai_teammates import TeammatesDialog
from aedrova.desktop.window import AedrovaWindow

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "work" / "m17f1"
OUTPUT.mkdir(parents=True, exist_ok=True)
app = QApplication([])
app.setStyle("Fusion")
window = AedrovaWindow(settings=QSettings(str(OUTPUT / "capture.ini"), QSettings.Format.IniFormat))
window.show_account()
snapshot = {
    "workspaces": [{"id": "w", "name": "Product memory preview"}],
    "channels": [{"id": "c", "workspace_id": "w", "name": "product", "private": False}],
    "members": [{"workspace_id": "w", "user_id": "u", "role": "owner"}],
    "invitations": [],
    "agent_preferences": [],
}
source = {
    "kind": "message",
    "id": "sample-source",
    "channel_id": "c",
    "citation": "message:sample-source",
    "fingerprint": "sample",
    "body": "We agreed: exported dates should use UTC. Keep the timezone explicit.",
}
row = {
    "id": "sample-memory",
    "workspace_id": "w",
    "channel_id": "c",
    "version": 3,
    "kind": "constraint",
    "state": "approved",
    "fresh": True,
    "title": "One timezone. Clear exports.",
    "body": "Use UTC for exported dates.\nShow the timezone alongside each timestamp.",
    "sources": [source],
    "resolved_sources": [source],
    "updated_by": "u",
    "updated_at": "2026-10-06T12:00:00Z",
}
service = SimpleNamespace(
    user=SimpleNamespace(id="u"),
    snapshot=lambda: snapshot,
    message_page=lambda *a, **k: [],
    attachments_for=lambda *_: [],
    realtime_credentials=lambda: None,
    rpc=lambda *a: None,
    memory_list=lambda *a: {"items": [row], "total": 1, "truncated": False},
)
window.account_dialog.service = service
window.account_dialog.loaded(snapshot)
window.account_dialog.open_dashboard()
window.connected.timer.stop()

teammate = {
    "id": "sample-teammate",
    "workspace_id": "w",
    "version": 1,
    "paused": False,
    "config": {
        "name": "Pixel",
        "role": "product",
        "shape": "round",
        "color": "#4388F5",
        "personality": "supportive",
        "reporting": "milestones",
        "effort": "balanced",
        "importance": "normal",
        "responsibilities": "Clarify requirements and draft specifications with source citations.",
    },
}
snapshot["ai_teammates"] = [teammate]
service.ai_teammates = lambda *_: {"items": [teammate], "setup_required": False}
window._load_channel()
dialog = TeammatesDialog(window)
dialog.show()
for _ in range(100):
    QTest.qWait(10)
    if not dialog.busy:
        break
if dialog.busy:
    raise RuntimeError("Teammate preview did not load")
dialog.list.setCurrentRow(0)
for mode in ("light", "dark"):
    window.set_theme(mode, persist=False)
    dialog.resize(820, 900)
    QTest.qWait(50)
    dialog.grab().save(str(OUTPUT / f"teammate-{mode}.png"))
dialog.resize(640, 700)
QTest.qWait(50)
dialog.grab().save(str(OUTPUT / "teammate-compact.png"))
dialog.reject()
window.connected.disconnect()
window.close()
