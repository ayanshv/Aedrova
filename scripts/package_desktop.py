"""Package the current desktop preview. Ad-hoc signed; not for public distribution."""

import json
import subprocess
import sys
from pathlib import Path

from aedrova.identity.service import Connection

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT / "scripts/check_release_secrets.py")], check=True)
configuration_args = []
asset_args = []
for asset in ("aedrova.png", "aedrova.icns"):
    asset_args.extend(
        ["--add-data", f"{ROOT / 'src/aedrova/desktop/assets' / asset}:aedrova/desktop/assets"]
    )
connection = Connection.from_environment()
if connection:
    config_path = ROOT / "work" / "public-config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "supabase_url": connection.url,
                "supabase_publishable_key": connection.public_key,
            }
        )
    )
    configuration_args = ["--add-data", f"{config_path}:aedrova/desktop/assets"]
else:
    print("Building an unconfigured preview; Google login requires owner configuration.")

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
        *asset_args,
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
        *configuration_args,
        str(ROOT / "scripts" / "app_entry.py"),
    ],
    cwd=ROOT,
    check=True,
)
