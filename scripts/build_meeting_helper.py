"""Build the small Apple audio bridge; all product logic remains in Python."""

import os
import platform
import plistlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "work/apple-setup-nov5/aedrova-meeting-audio"


def build(identity=None):
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    info = OUTPUT.with_suffix(".plist")
    info.write_bytes(
        plistlib.dumps(
            {
                "CFBundleIdentifier": "com.aedrova.desktop.meeting-audio",
                "CFBundleName": "Aedrova Meeting Audio",
                "NSMicrophoneUsageDescription": (
                    "Transcribe your voice locally when you start notes."
                ),
                "NSAudioCaptureUsageDescription": (
                    "Transcribe meeting audio locally when you start notes."
                ),
                "NSScreenCaptureUsageDescription": "Capture meeting audio locally, without video.",
            }
        )
    )
    subprocess.run(
        [
            "xcrun",
            "swiftc",
            "-parse-as-library",
            "-swift-version",
            "5",
            "-O",
            "-target",
            f"{platform.machine()}-apple-macos14.0",
            str(ROOT / "src/aedrova/meetings/native/MeetingAudio.swift"),
            "-o",
            str(OUTPUT),
            "-framework",
            "ScreenCaptureKit",
            "-framework",
            "AVFoundation",
            "-framework",
            "AppKit",
            "-Xlinker",
            "-sectcreate",
            "-Xlinker",
            "__TEXT",
            "-Xlinker",
            "__info_plist",
            "-Xlinker",
            str(info),
        ],
        check=True,
    )
    command = [
        "codesign",
        "--force",
        "--sign",
        identity or "-",
        "--options",
        "runtime",
        "--entitlements",
        str(ROOT / "scripts/release-entitlements.plist"),
    ]
    if identity:
        command.append("--timestamp")
    subprocess.run([*command, str(OUTPUT)], check=True)
    subprocess.run(["codesign", "--verify", "--strict", str(OUTPUT)], check=True)
    return OUTPUT


if __name__ == "__main__":
    build(os.getenv("AEDROVA_SIGNING_IDENTITY"))
