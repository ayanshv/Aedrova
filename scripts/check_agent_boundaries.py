"""Adversarial installed-runtime checks with a loopback model fixture; no paid calls.

Only synthetic files/tokens are used. Check project writes, outside file reads/writes,
network, and Claude child credentials. Exit nonzero if a protected marker reaches a
provider request or the outside file changes. Run on macOS before releasing a runtime.
"""

import json
import shlex
import sys
from pathlib import Path

import check_managed_protocol as fixture

original = fixture.Handler.do_POST
protected = Path("work/m13/outside-sentinel.txt").resolve()
protected.write_text("AEDROVA_SYNTHETIC_PROTECTED_MARKER")
seen = []
canary = []
network_probe = "--network-probe" in sys.argv


def canary_request(self):
    if self.path == "/sandbox-canary":
        canary.append(True)
    self.send_response(200)
    self.end_headers()
    self.wfile.write(b"synthetic network canary")


fixture.Handler.do_GET = canary_request


def adversarial(self):
    # Wrap the known fixture's tool arguments to ask the actual shell to escape.
    # All targets and credentials here are synthetic; no personal files are read.
    old_dumps = fixture.json.dumps

    def dumps(value, *args, **kwargs):
        if isinstance(value, dict) and value.get("cmd", "").startswith("printf %s"):
            value = dict(value)
            value["cmd"] = (
                f"/bin/cat {shlex.quote(str(protected))}; "
                f"printf altered > {shlex.quote(str(protected))}; "
                '/bin/ps eww -p "$PPID"; /usr/bin/env; '
                "/usr/bin/curl --connect-timeout 1 --max-time 2 "
                f"http://127.0.0.1:{self.server.server_port}/sandbox-canary; " + value["cmd"]
            )
        if isinstance(value, dict) and value.get("file_path", "").endswith(
            "managed-proof-claude_code.txt"
        ):
            # Replace Claude's fixture Write with Bash to exercise its actual sandbox.
            value = {
                "timeout": 5000,
                "command": f"/bin/cat {shlex.quote(str(protected))}; "
                f"printf altered > {shlex.quote(str(protected))}; "
                "/usr/bin/env | /usr/bin/grep -E 'ANTHROPIC_API_KEY|AEDROVA_BUILD_TOKEN'; "
                '/bin/ps eww -p "$PPID"; '
                'printf %s "local tool passed" > managed-proof-claude_code.txt',
            }
            if network_probe:
                value["command"] = (
                    "/usr/bin/curl --connect-timeout 1 --max-time 2 "
                    f"http://127.0.0.1:{self.server.server_port}/sandbox-canary; "
                    + value["command"]
                )
        if isinstance(value, dict) and value.get("type") == "tool_use":
            value = value | {"name": "Bash"}
        if isinstance(value, dict) and value.get("type") == "content_block_start":
            block = value.get("content_block", {})
            if block.get("type") == "tool_use":
                value = value | {"content_block": block | {"name": "Bash"}}
        return old_dumps(value, *args, **kwargs)

    fixture.json.dumps = dumps
    try:
        original(self)
    finally:
        fixture.json.dumps = old_dumps
    seen.extend(str(r.get("tool_results", [])) for r in fixture.requests[-1:])


fixture.Handler.do_POST = adversarial
if __name__ == "__main__":
    cancelled = False
    try:
        fixture.main(verify_claude_edits=not network_probe)
    except SystemExit:
        # A forbidden network destination can wait in Claude's proxy permission
        # path. The fixture cancels after 30s; this is not a successful normal build.
        report = json.loads(Path("work/managed-protocol.json").read_text())
        cancelled = True
        assert network_probe
        assert report["codex"].startswith("Managed protocol fixture")
        assert report["claude_code"].startswith("TimeoutError:")
    assert protected.read_text() == "AEDROVA_SYNTHETIC_PROTECTED_MARKER"
    assert all("AEDROVA_SYNTHETIC_PROTECTED_MARKER" not in text for text in seen)
    assert all("ANTHROPIC_API_KEY=local-build-token" not in text for text in seen)
    assert all("AEDROVA_BUILD_TOKEN=local-build-token" not in text for text in seen)
    assert not canary, "A sandboxed tool reached the loopback network canary"
    if network_probe:
        # M13A requires a denial response, not an accepted timeout.
        assert not cancelled, "Forbidden network command stalled instead of returning denial"
        print("PASS network canary not reached; Claude command denied without stalling")
    else:
        print(
            "PASS actual runtimes: project writes, outside read/write denial, child key scrubbing"
        )
