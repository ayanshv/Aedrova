"""Local execution authority. Never grants connector or workspace membership."""

import re
import shlex
from pathlib import Path

MODES = {
    "ask": ("Ask for approval", "Ask before edits and commands that need permission."),
    "auto": (
        "Approve for me",
        "Automatically approve project edits and bounded test commands; ask for other actions.",
    ),
    "full": (
        "Full access",
        "Run project edits and commands without prompts in the isolated build copy. "
        "Applying or publishing still requires review. Network and secret protections remain.",
    ),
}


def normalize(mode):
    return mode if isinstance(mode, str) and mode in MODES else "ask"


def automatic(tool, data, project):
    """Conservative allowlist, not an LLM's claim that its own action is safe."""
    root = Path(project).resolve()
    if tool in {"Edit", "Write"}:
        paths = data.get("paths") or [data.get("file_path", "")]
        if not paths or not all(isinstance(p, str) and p for p in paths):
            return False
        from aedrova.agents.checkout import excluded

        for name in paths:
            path = Path(name)
            path = (root / path).resolve() if not path.is_absolute() else path.resolve()
            if not path.is_relative_to(root) or excluded(path.relative_to(root)):
                return False
        return True
    if tool != "Bash" or data.get("dangerouslyDisableSandbox"):
        return False
    # Shell syntax, custom executables and arbitrary Python are human-reviewed.
    command = data.get("command", "")
    if not isinstance(command, str) or re.search(r"[;&|`$<>\n\r]", command):
        return False
    try:
        args = shlex.split(command)
    except ValueError:
        return False
    if not args:
        return False
    prefix = args[:3] == ["python", "-m", "pytest"] or args[:3] == ["python3", "-m", "pytest"]
    if not prefix and args[0] != "pytest":
        return False
    # Loading external plugins/config or pointing a test runner outside its copy needs approval.
    flags = {"-q", "-v", "-vv", "-x", "--disable-warnings", "--strict-markers"}
    for arg in args[3:] if prefix else args[1:]:
        if arg in flags:
            continue
        if arg.startswith("-") or "=" in arg:
            return False
        path = (root / arg.split("::", 1)[0]).resolve()
        if not path.is_relative_to(root):
            return False
    return True
