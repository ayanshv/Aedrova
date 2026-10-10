"""Capture actual build-review UI with synthetic data, real diffs and a real local check."""

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

from PySide6.QtCore import QSettings
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from aedrova.agents.checkout import prepare
from aedrova.agents.context import WorkspaceContext
from aedrova.delivery.evidence import command_result, manifest, project_fingerprint
from aedrova.delivery.files import make_review
from aedrova.desktop.build_evidence import SharedBuilds
from aedrova.desktop.window import AedrovaWindow
from aedrova.memory.model import snapshot_record

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "work" / "m16"
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


source_dir = OUTPUT / "sample-project"
source_dir.mkdir(exist_ok=True)
(source_dir / "dates.py").write_text("def timezone():\n    return 'local'\n")
project = prepare(source_dir, OUTPUT / "builds")
(project / "dates.py").write_text("def timezone():\n    return 'UTC'\n")
context = WorkspaceContext(
    workspace_id="w",
    channel_ids=frozenset({"c"}),
    text="",
    user_id="u",
    count=1,
    nickname="Aedrova",
    provider="codex",
)
record = snapshot_record({"items": [row], "total": 1, "truncated": False}, "w", {"c"})
context = replace(context, text=json.dumps(record))
checked = subprocess.run(
    [
        sys.executable,
        "-c",
        "from dates import timezone; assert timezone() == 'UTC'; print('UTC assertion passed')",
    ],
    cwd=project,
    capture_output=True,
    text=True,
)
receipt = command_result("python · verify export timezone", checked.stdout, checked.returncode)
receipt["project_fingerprint"] = project_fingerprint(project)
value = manifest(
    context, "Sample build · Keep exported dates in UTC", "codex", make_review(project), [receipt]
)
value["acceptance_criteria"] = ["Exports explicitly use UTC."]
value["requirements"][0].update(
    assessment="reviewer_verified", files=["dates.py"], checks=[receipt["id"]]
)
service.build_reviews = lambda _: {
    "items": [
        {
            "id": "sample-review",
            "evidence": value,
            "version": 1,
            "source_channels": ["c"],
            "current": True,
        }
    ],
    "setup_required": False,
}
service.build_review_decisions = lambda _: [
    {
        "build_version": 1,
        "decision": "approved",
        "created_at": "2026-10-06T12:00:00Z",
        "note": "Sample review · Checked UTC behavior and the linked file diff.",
    }
]
dialog = SharedBuilds(window)
dialog.show()
for _ in range(200):
    QTest.qWait(10)
    if not dialog.busy and dialog.rows:
        break
if dialog.busy or not dialog.rows:
    raise RuntimeError("Build evidence capture did not load")
for mode in ("light", "dark"):
    window.set_theme(mode, persist=False)
    dialog.resize(1000, 840)
    QTest.qWait(50)
    dialog.grab().save(str(OUTPUT / f"build-review-{mode}.png"))
dialog.resize(780, 700)
QTest.qWait(50)
dialog.grab().save(str(OUTPUT / "build-review-compact.png"))
dialog.reject()
window.connected.disconnect()
window.close()
