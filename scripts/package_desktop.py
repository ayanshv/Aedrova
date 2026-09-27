"""Package the current desktop preview. Ad-hoc signed; not for public distribution."""

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
        "Aedrova",
        "--icon",
        str(ROOT / "src/aedrova/desktop/assets/aedrova.icns"),
        "--add-data",
        f"{ROOT / 'src/aedrova/desktop/assets'}:aedrova/desktop/assets",
        "--osx-bundle-identifier",
        "com.aedrova.desktop.preview",
        "--paths",
        str(ROOT / "src"),
        "--specpath",
        str(ROOT / "work"),
        "--distpath",
        str(ROOT / "dist"),
        "--workpath",
        str(ROOT / "build"),
        str(ROOT / "scripts" / "app_entry.py"),
    ],
    cwd=ROOT,
    check=True,
)
