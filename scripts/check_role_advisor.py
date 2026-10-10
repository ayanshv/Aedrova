"""Live role suggestion on a synthetic description; no workspace context or secrets."""

import json
from pathlib import Path

from aedrova.teammates.advisor import advise

print("Checking actual Codex role interpretation…", flush=True)
report = {"status": "incomplete", "provider": "codex", "input": "synthetic role only"}
try:
    result = advise(
        "A product researcher who summarizes customer feedback into source-backed requirements",
        "codex",
    )
    assert result["summary"] and result["tools"]
    report.update(status="passed", advice=result)
except Exception as error:
    report.update(status="failed", error_type=type(error).__name__)
p = Path("work/onboarding-refinement/live-role-advice.json")
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(report, indent=2))
print("Live role suggestion: " + report["status"], flush=True)
raise SystemExit(0 if report["status"] == "passed" else 1)
