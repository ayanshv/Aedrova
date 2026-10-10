"""Capture the native teammate editor with labelled sample data and no network calls."""

from pathlib import Path
from types import SimpleNamespace

from PySide6.QtCore import QSettings
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from aedrova.desktop.window import AedrovaWindow
from aedrova.desktop.zen_onboarding import ZenOnboarding

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "work" / "onboarding-refinement"
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

window.reduced_motion = True
window.resize(1440, 940)
profiles = []
for i, name in enumerate(["Pixel", "Orbit", "Echo", "Scout", "Milo", "Blue"]):
    profiles.append(
        {
            "id": "sample-" + name,
            "workspace_id": "w",
            "version": 1,
            "paused": False,
            "config": {
                "name": name,
                "role": "research",
                "role_label": "Product researcher",
                "shape": "round",
                "color": ["#4388F5", "#7775ED", "#56A8F5"][i % 3],
                "personality": "concise",
                "reporting": "quiet",
                "effort": "quick",
                "importance": "normal",
                "responsibilities": "Review accessible evidence.",
            },
        }
    )
snapshot["ai_teammates"] = profiles
service.ai_teammates = lambda *_: {"items": profiles, "setup_required": False}
window._load_channel()
for mode in ("light", "dark"):
    window.set_theme(mode, persist=False)
    QTest.qWait(60)
    window.grab().save(str(OUTPUT / ("workspace-" + mode + ".png")))
    flow = ZenOnboarding(window)
    flow.reduced = True
    flow.show()
    flow.resize(1120, 820)
    for stage in (0, 1, 3, 4, 5, 6, 7, 8, 9, 10):
        flow.show_stage(stage)
        QTest.qWait(60)
        flow.grab().save(str(OUTPUT / ("onboarding-" + mode + "-" + str(stage) + ".png")))
    flow.resize(640, 620)
    flow.show_stage(7)
    QTest.qWait(60)
    flow.grab().save(str(OUTPUT / ("onboarding-" + mode + "-compact.png")))
    flow.reject()
window.connected.disconnect()
window.close()
