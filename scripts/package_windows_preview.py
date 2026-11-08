"""Build an unsigned Windows preview for internal release acceptance."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


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
        f"{source / 'desktop/assets'}:aedrova/desktop/assets",
        "--add-data",
        f"{source / 'localization/models.json'}:aedrova/localization",
    ]
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
