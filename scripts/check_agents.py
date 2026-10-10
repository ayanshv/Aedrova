"""Repeatable real runtime probes. --live-codex explicitly makes billable model calls."""

import argparse
import asyncio
import json
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

from aedrova.agents.checkout import git, prepare
from aedrova.agents.runtime import LocalRunner, instructions


async def handshake(cli_path=None):
    with TemporaryDirectory(prefix="aedrova-agent-handshake-") as directory:
        options = ClaudeAgentOptions(
            cwd=directory,
            tools=[],
            setting_sources=[],
            permission_mode="default",
            cli_path=cli_path,
        )
        async with asyncio.timeout(30):
            async with ClaudeSDKClient(options=options) as client:
                if not await client.get_server_info():
                    raise RuntimeError("Claude runtime did not initialize")


def live_codex():
    with TemporaryDirectory(prefix="aedrova-live-build-") as directory:
        root = Path(directory)
        source = root / "source"
        source.mkdir()
        subprocess.run(["git", "init", "-q", str(source)], check=True)
        git(
            source,
            "-c",
            "user.name=Aedrova test",
            "-c",
            "user.email=test@example.invalid",
            "commit",
            "--allow-empty",
            "-qm",
            "Synthetic fixture",
        )
        project = prepare(source, root / "builds")
        evidence = project.parent / "workspace-context.jsonl"
        evidence.write_text(
            json.dumps(
                {
                    "message": {
                        "id": "synthetic-1",
                        "body": "Implement greet(name) returning Hello, name! "
                        "and test Alice and Bob.",
                    }
                }
            )
        )
        request = (
            "Create greeting.py with greet(name) and test_greeting.py using unittest. "
            "Follow the synthetic workspace requirement. Run python3 -m unittest."
        )
        runner = LocalRunner(print, timeout=180)
        plan = runner.run("codex", project, instructions(request, evidence, plan=True), plan=True)
        if git(project, "status", "--porcelain").strip():
            raise AssertionError("Planning modified the checkout")
        runner.run(
            "codex",
            project,
            instructions(request, evidence, plan=False, approved_plan=plan),
            plan=False,
        )
        if not (project / "greeting.py").exists() or not (project / "test_greeting.py").exists():
            raise AssertionError("Expected implementation and tests are missing")
        subprocess.run([sys.executable, "-m", "unittest"], cwd=project, check=True)
        subprocess.run(
            [
                sys.executable,
                "-c",
                'from greeting import greet; assert greet("Alice") == "Hello, Alice!"; '
                'assert greet("Bob") == "Hello, Bob!"',
            ],
            cwd=project,
            check=True,
        )
        if (source / "greeting.py").exists():
            raise AssertionError("Original checkout was modified")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live-codex", action="store_true")
    parser.add_argument("--claude-cli", type=Path)
    args = parser.parse_args()
    asyncio.run(handshake(args.claude_cli.resolve() if args.claude_cli else None))
    report = {
        "claude_runtime_handshake": "passed; no model request",
        "claude_paid_build": "not tested; owner API setup required",
        "codex_live_build": "not requested",
    }
    if args.live_codex:
        live_codex()
        report["codex_live_build"] = "passed; real planning, file edits and independent tests"
    Path("work").mkdir(exist_ok=True)
    Path("work/agent-checks.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
