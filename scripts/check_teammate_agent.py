"""Live Codex read-only specialist acceptance on disposable synthetic evidence."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from aedrova.agents.checkout import prepare
from aedrova.agents.context import WorkspaceContext
from aedrova.desktop import builds
from aedrova.desktop.builds import BuildJob

report = {"status": "incomplete", "provider": "codex", "data": "synthetic only"}
output = Path("work/m17f1/live-teammate-check.json")
output.parent.mkdir(parents=True, exist_ok=True)
with TemporaryDirectory(prefix="aedrova-teammate-") as directory:
    root = Path(directory)
    source = root / "source"
    source.mkdir()
    (source / "README.md").write_text("Synthetic acceptance project. No production files.\n")
    text = "\n".join(
        json.dumps(row)
        for row in [
            {"channel": "c", "name": "product"},
            {
                "message": {
                    "id": "synthetic-brief",
                    "channel_id": "c",
                    "body": "Approved: export dates in UTC. Still undecided: CSV or JSON.",
                    "created_at": "2026-10-06T12:00:00Z",
                    "parent_id": None,
                }
            },
        ]
    )
    context = WorkspaceContext("w", "u", frozenset({"c"}), text, 1, "Aedrova", "codex")
    builds.prepare = lambda source, _: prepare(source, root / "builds")
    job = BuildJob(
        context,
        str(source),
        "Summarize the requirement and identify the unresolved question. Cite the source.",
        "codex",
        True,
    )
    job.teammate = {
        "config": {
            "name": "Pixel",
            "role": "research",
            "shape": "round",
            "color": "#4388F5",
            "personality": "concise",
            "reporting": "quiet",
            "effort": "quick",
            "importance": "normal",
            "responsibilities": "Distinguish approved decisions from open questions.",
        }
    }
    results = []
    job.signals.finished.connect(results.append)
    print("Running actual read-only Research teammate via the app worker…", flush=True)
    job.run()
    if not results or not results[0]["ok"]:
        report.update(status="failed", result=results[0]["text"] if results else "No result")
    else:
        result = results[0]
        assert "message:synthetic-brief" in result["text"]
        assert "UTC" in result["text"] and ("CSV" in result["text"] or "JSON" in result["text"])
        assert result["changes"] in ("", "No changes") or "README.md" not in result["changes"]
        assert (
            source / "README.md"
        ).read_text() == "Synthetic acceptance project. No production files.\n"
        assert len(list(source.iterdir())) == 1
        report.update(status="passed", result=result["text"], read_only="passed", citation="passed")
output.write_text(json.dumps(report, indent=2))
print("Live teammate check: " + report["status"], flush=True)
raise SystemExit(0 if report["status"] == "passed" else 1)
