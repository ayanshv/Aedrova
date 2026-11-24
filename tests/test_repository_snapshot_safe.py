"""Aedrova builds in its own checkout refuse any file that looks like a credential.

A test fixture holding a literal private-key header once blocked every build in this project
("Potential hardcoded credential in tests/..."), so keep fixtures from tripping that scan.
"""

import subprocess
from pathlib import Path

import pytest

from aedrova.agents.checkout import excluded
from aedrova.security.credentials import credential_rules

ROOT = Path(__file__).resolve().parents[1]


def test_no_tracked_file_would_block_a_project_snapshot():
    try:
        listing = subprocess.run(
            ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("git is not available")
    blocked = []
    for name in listing.decode().split("\0"):
        relative = Path(name)
        path = ROOT / relative
        if not name or excluded(relative) or not path.is_file():
            continue
        if path.stat().st_size <= 25 * 1024 * 1024 and credential_rules(path.read_bytes()):
            blocked.append(name)
    assert not blocked, f"Build the credential-looking text at runtime in: {blocked}"
