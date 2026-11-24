"""Build an unsigned Windows preview for internal release acceptance."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aedrova.agents.managed import application_origin, connector_origin  # noqa: E402
from aedrova.identity.service import Connection  # noqa: E402


def main():
    if sys.platform != "win32":
        raise SystemExit("Build the Windows preview on Windows.")
    source = ROOT / "src" / "aedrova"
    output = ROOT / "dist" / "windows-preview"
    work = ROOT / "build" / "windows-preview"
    work.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_release_secrets.py"), "--tracked"],
        check=True,
        cwd=ROOT,
    )
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--name",
        "Aedrova",
        "--icon",
        str(source / "desktop/assets/aedrova.ico"),
        "--copy-metadata",
        "aedrova",
        "--paths",
        str(source.parent),
        "--distpath",
        str(output),
        "--workpath",
        str(work),
        "--specpath",
        str(work),
        "--add-data",
        f"{source / 'desktop/assets'}{os.pathsep}aedrova/desktop/assets",
        "--add-data",
        f"{source / 'localization/models.json'}{os.pathsep}aedrova/localization",
    ]
    # The beta build talks to the staging service; its public settings come from the environment.
    connection = Connection.from_environment()
    if connection:
        config_path = work / "public-config.json"
        config_path.write_text(
            json.dumps(
                {
                    "supabase_url": connection.url,
                    "supabase_publishable_key": connection.public_key,
                    "managed_origin": application_origin(),
                    "connector_origin": connector_origin(),
                    "ai_access_mode": "included",
                    "apple_login_enabled": False,
                    "meeting_context_enabled": False,
                    "hosted_calls_enabled": False,
                }
            ),
            encoding="utf-8",
        )
        command.extend(["--add-data", f"{config_path}{os.pathsep}aedrova/desktop/assets"])
    for module in (
        "claude_agent_sdk",
        "faster_whisper",
        "av",
        "onnxruntime",
        "ctranslate2",
        "sentencepiece",
        "keyring",
        "livekit.rtc",
        "livekit.protocol",
    ):
        command.extend(["--collect-all", module])
    for module in ("py3langid", "sacremoses"):
        command.extend(["--collect-data", module])
    subprocess.run([*command, str(ROOT / "scripts" / "app_entry.py")], check=True, cwd=ROOT)
    exe = output / "Aedrova" / "Aedrova.exe"
    report = work / "smoke.json"
    report.unlink(missing_ok=True)
    subprocess.run(
        [str(exe), "--smoke-report", str(report), "--settings-file", str(work / "smoke.ini")],
        check=True,
        timeout=60,
        cwd=ROOT,
    )
    smoke = json.loads(report.read_text(encoding="utf-8"))
    if not smoke["packaged"] or not smoke["screenshot_saved"]:
        raise RuntimeError("The frozen Windows preview did not pass the startup smoke check.")
    with exe.open("rb") as artifact:
        digest = hashlib.file_digest(artifact, "sha256").hexdigest()
    (output / "manifest.json").write_text(
        json.dumps(
            {
                "executable_sha256": digest,
                "scope": "unsigned internal preview",
                "public_release": False,
                "smoke": smoke,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
