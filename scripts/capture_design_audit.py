"""Capture the real memory view with clearly synthetic sample data, without network access."""

from pathlib import Path
from types import SimpleNamespace

from PySide6.QtCore import QSettings
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from aedrova.desktop.window import AedrovaWindow

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "work" / "design-audit"
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

from aedrova.desktop.preferences import SettingsDialog
from aedrova.desktop.projects import ProjectDialog
from aedrova.desktop.profile import ProfileDialog
from aedrova.desktop.builds import BuildDialog
from aedrova.desktop.execution import execution_queue, RunHistory
from aedrova.desktop.meeting_setup import MeetingSetup
from aedrova.desktop.meeting_call import MeetingCall, AudioCall
from aedrova.meetings.devices import DeviceCheck
import sys
sys.path.insert(0, str(ROOT / "tests"))
from test_meeting_calls import Backend, Worker

records = []
def capture(name, widget):
    QTest.qWait(80)
    if not widget.grab().save(str(OUTPUT / (name + ".png"))):
        raise RuntimeError("Screenshot failed: " + name)
    records.append(name)

window.show()
for mode in ("light", "dark"):
    window.set_theme(mode, persist=False)
    for index, name in enumerate(("conversation", "project", "work", "files")):
        window.select_tab(index)
        capture(mode + "-" + name, window)
    window.select_tab(0)
    for name, factory in (
        ("settings", lambda: SettingsDialog(window)),
        ("project-connection", lambda: ProjectDialog(window)),
        ("profile", lambda: ProfileDialog(window, window.account_dialog)),
        ("build-studio", lambda: BuildDialog(window)),
        ("queue", lambda: RunHistory(execution_queue(window))),
        ("meeting-devices", lambda: MeetingSetup(window, check=DeviceCheck(backend=Backend()))),
        ("video-call", lambda: MeetingCall(window, Worker(), devices=DeviceCheck(backend=Backend()))),
        ("audio-call", lambda: AudioCall(window, Worker(), devices=DeviceCheck(backend=Backend()))),
    ):
        dialog = factory()
        dialog.show()
        capture(mode + "-" + name, dialog)
        if name == "profile":
            for index in range(1, dialog.stack.count()):
                dialog.stack.setCurrentIndex(index)
                capture(mode + "-profile-" + str(index), dialog)
        dialog.reject()
    window.resize(900, 650)
    capture(mode + "-compact", window)
    window.resize(1440, 940)
window.connected.disconnect()
window.close()
(OUTPUT / "captures.txt").write_text("\n".join(records))
print("Captured", len(records), "real native views without network or device access.")
