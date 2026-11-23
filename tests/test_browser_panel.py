"""Run the browser panel checks in their own process.

Chromium keeps process-wide state, and it must start before the rest of the suite creates its
Qt application, so the checks in `isolated_browser_checks.py` get a clean interpreter.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("PySide6.QtWebEngineWidgets")


def test_browser_panel_checks_pass_in_a_clean_process():
    environment = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            str(Path(__file__).with_name("isolated_browser_checks.py")),
        ],
        capture_output=True,
        text=True,
        env=environment,
        timeout=240,
    )
    assert result.returncode == 0, result.stdout[-3000:] + result.stderr[-1500:]
    assert " passed" in result.stdout
