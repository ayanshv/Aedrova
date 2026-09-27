"""Build a local unsigned feasibility .app; release signing is milestone 11."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
subprocess.run(
    [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        "Aedrova-Probe",
        "--osx-bundle-identifier",
        "com.aedrova.probe",
        "--paths",
        str(ROOT / "src"),
        "--specpath",
        str(ROOT / "work"),
        "--distpath",
        str(ROOT / "dist"),
        "--workpath",
        str(ROOT / "build"),
        str(ROOT / "scripts" / "desktop_entry.py"),
    ],
    cwd=ROOT,
    check=True,
)
