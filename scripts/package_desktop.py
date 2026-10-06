"""Package the current desktop preview. Development previews and gated public distribution."""

import hashlib
import json
import os
import plistlib
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

from aedrova.agents.managed import application_origin
from aedrova.agents.runtime import executable
from aedrova.identity.service import Connection

ROOT = Path(__file__).resolve().parents[1]
subprocess.run([sys.executable, str(ROOT / "scripts/check_release_secrets.py")], check=True)
configuration_args = []
signing_args = []
release_identity = os.getenv("AEDROVA_SIGNING_IDENTITY", "")
preview_identity = os.getenv("AEDROVA_PREVIEW_SIGNING_IDENTITY", "")
if release_identity and preview_identity:
    raise ValueError("Choose either release or development signing, not both.")
if preview_identity and not preview_identity.startswith("Apple Development:"):
    raise ValueError("Development previews require an Apple Development identity.")
ai_mode = os.getenv("AEDROVA_AI_ACCESS_MODE", "included" if release_identity else "local")
if ai_mode not in {"local", "included"}:
    raise ValueError("Choose local or included AI access.")
if release_identity and ai_mode != "included":
    raise ValueError("Public paid builds require included AI access; local fallback is forbidden.")
identity = release_identity or preview_identity
if release_identity:
    if not identity.startswith("Developer ID Application:"):
        raise ValueError("Public distribution requires a Developer ID Application identity.")
    if not application_origin().startswith("https://"):
        raise ValueError("Public builds require the configured HTTPS managed service origin.")
if identity:
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
code_mode_host = codex_binary.resolve().with_name("codex-code-mode-host")
if not code_mode_host.is_file():
    raise ValueError("The Codex runtime requires its matching codex-code-mode-host companion.")
subprocess.run(["codesign", "--verify", "--strict", str(code_mode_host)], check=True)
host_signature = subprocess.run(
    ["codesign", "--display", "--verbose=4", str(code_mode_host)],
    check=True,
    capture_output=True,
    text=True,
).stderr
if "TeamIdentifier=2DC432GLL2" not in host_signature:
    raise ValueError("Use the official OpenAI-signed Codex execution helper.")
with code_mode_host.open("rb") as stream:
    host_hash = hashlib.file_digest(stream, "sha256").hexdigest()
runtime_manifest = ROOT / "work/runtime-manifest.json"
runtime_manifest.parent.mkdir(parents=True, exist_ok=True)
runtime_manifest.write_text(
    json.dumps(
        {
            "codex_version": "0.155.1",
            "source_sha256": runtime_hash,
            "code_mode_host_sha256": host_hash,
        }
    )
)
vendor_binary = ROOT / "work/vendor-codex/codex"
vendor_binary.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(codex_binary, vendor_binary)
vendor_host = vendor_binary.with_name("codex-code-mode-host")
shutil.copy2(code_mode_host, vendor_host)
codex_binary = vendor_binary
asset_args.extend(
    [
        "--add-binary",
        f"{codex_binary}:aedrova/agents/bin",
        "--add-binary",
        f"{vendor_host}:aedrova/agents/bin",
        "--add-data",
        f"{ROOT / 'src/aedrova/desktop/assets/licenses'}:aedrova/desktop/assets/licenses",
        "--add-data",
        f"{runtime_manifest}:aedrova/desktop/assets",
    ]
)
for asset in ("aedrova.png", "aedrova.icns", "google-g.png", "emoji.json"):
    asset_args.extend(
        ["--add-data", f"{ROOT / 'src/aedrova/desktop/assets' / asset}:aedrova/desktop/assets"]
    )
asset_args.extend(
    [
        "--add-data",
        f"{ROOT / 'src/aedrova/desktop/assets/onboarding'}:aedrova/desktop/assets/onboarding",
    ]
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
                "ai_access_mode": ai_mode,
                "meeting_context_enabled": os.getenv("AEDROVA_MEETING_CONTEXT_ENABLED") == "true",
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
        "--copy-metadata",
        "aedrova",
        "--collect-all",
        "claude_agent_sdk",
        "--collect-all",
        "livekit.rtc",
        "--collect-all",
        "livekit.protocol",
        "--name",
        "Aedrova",
        "--icon",
        str(ROOT / "src/aedrova/desktop/assets/aedrova.icns"),
        *asset_args,
        "--osx-bundle-identifier",
        "com.aedrova.desktop" if release_identity else "com.aedrova.desktop.preview",
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

# Qt's macOS permission API requires usage descriptions in the application bundle.
# Re-sign the outer bundle after editing; preserve the vendor runtime's own signature.
bundle = ROOT / "dist/Aedrova.app"
info_path = bundle / "Contents/Info.plist"
with info_path.open("rb") as stream:
    info = plistlib.load(stream)
info.update(
    {
        "CFBundleShortVersionString": (
            tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
        ),
        "CFBundleVersion": tomllib.loads((ROOT / "pyproject.toml").read_text())["project"][
            "version"
        ],
        "LSMinimumSystemVersion": "14.0",
        "NSCameraUsageDescription": (
            "Use your camera when you enable a meeting or local camera check."
        ),
        "CFBundleURLTypes": [
            {"CFBundleURLName": "com.aedrova.chat", "CFBundleURLSchemes": ["aedrova"]}
        ],
        "NSMicrophoneUsageDescription": (
            "Use your microphone when you enable a meeting or local microphone check."
        ),
    }
)
with info_path.open("wb") as stream:
    plistlib.dump(info, stream)
resign = ["codesign", "--force", "--sign", identity or "-"]
if identity:
    resign.extend(
        ["--options", "runtime", "--entitlements", str(ROOT / "scripts/release-entitlements.plist")]
    )
subprocess.run([*resign, str(bundle)], check=True)
subprocess.run(["codesign", "--verify", "--strict", str(bundle)], check=True)
