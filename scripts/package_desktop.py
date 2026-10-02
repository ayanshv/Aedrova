"""Package the current desktop preview. Ad-hoc signed; not for public distribution."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from aedrova.agents.managed import application_origin
from aedrova.agents.runtime import executable
from aedrova.identity.service import Connection

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT / "scripts/check_release_secrets.py")], check=True)
configuration_args = []
signing_args = []
identity = os.getenv("AEDROVA_SIGNING_IDENTITY", "")
if identity:
    if not identity.startswith("Developer ID Application:"):
        raise ValueError("Public distribution requires a Developer ID Application identity.")
    if not application_origin().startswith("https://"):
        raise ValueError("Public builds require the configured HTTPS managed service origin.")
    signing_args = [
        "--codesign-identity",
        identity,
        "--osx-entitlements-file",
        str(ROOT / "scripts/release-entitlements.plist"),
    ]
asset_args = []
codex_binary = Path(os.getenv("AEDROVA_CODEX_BINARY", executable("codex")))
version = subprocess.run(
    [str(codex_binary), "--version"], check=True, capture_output=True, text=True
)
if version.stdout.strip() != "codex-cli 0.155.1":
    raise ValueError("Package the protocol-tested Codex CLI 0.155.1; retest upgrades first.")
subprocess.run(["codesign", "--verify", "--strict", str(codex_binary)], check=True)
signature = subprocess.run(
    ["codesign", "--display", "--verbose=4", str(codex_binary)],
    check=True,
    capture_output=True,
    text=True,
).stderr
if "TeamIdentifier=2DC432GLL2" not in signature:
    raise ValueError("Use the official OpenAI-signed Codex runtime.")
with codex_binary.open("rb") as stream:
    runtime_hash = hashlib.file_digest(stream, "sha256").hexdigest()
runtime_manifest = ROOT / "work/runtime-manifest.json"
runtime_manifest.parent.mkdir(parents=True, exist_ok=True)
runtime_manifest.write_text(json.dumps({"codex_version": "0.155.1", "source_sha256": runtime_hash}))
vendor_binary = ROOT / "work/vendor-codex/codex"
vendor_binary.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(codex_binary, vendor_binary)
codex_binary = vendor_binary
asset_args.extend(
    [
        "--add-binary",
        f"{codex_binary}:aedrova/agents/bin",
        "--add-data",
        f"{ROOT / 'src/aedrova/desktop/assets/licenses'}:aedrova/desktop/assets/licenses",
        "--add-data",
        f"{runtime_manifest}:aedrova/desktop/assets",
    ]
)
for asset in ("aedrova.png", "aedrova.icns", "google-g.png"):
    asset_args.extend(
        ["--add-data", f"{ROOT / 'src/aedrova/desktop/assets' / asset}:aedrova/desktop/assets"]
    )
connection = Connection.from_environment() or Connection.from_bundle()
if connection:
    config_path = ROOT / "work" / "public-config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        json.dumps(
            {
                "supabase_url": connection.url,
                "supabase_publishable_key": connection.public_key,
                "managed_origin": application_origin(),
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
        "--collect-all",
        "claude_agent_sdk",
        "--name",
        "Aedrova",
        "--icon",
        str(ROOT / "src/aedrova/desktop/assets/aedrova.icns"),
        *asset_args,
        "--osx-bundle-identifier",
        "com.aedrova.desktop" if identity else "com.aedrova.desktop.preview",
        *signing_args,
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
