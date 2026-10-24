"""Local source-only macOS bundle for truthful staging permission acceptance.

Not an installer or public distribution. Contains no credentials; imports source
and dependencies from this checkout. A stable bundle ID lets macOS present explicit
camera/microphone consent instead of silently rejecting an unbundled Python process.
"""

import os
import plistlib
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

from macos_icon import install as install_macos_icon


def prepare(root: Path, environment: dict[str, str]) -> Path:
    bundle = root / "work/staging/Aedrova Staging.app"
    contents = bundle / "Contents"
    binary = contents / "MacOS/AedrovaStaging"
    binary.parent.mkdir(parents=True, exist_ok=True)
    source = Path(sys.executable).resolve()
    if not binary.exists() or binary.stat().st_mtime_ns != source.stat().st_mtime_ns:
        shutil.copy2(source, binary)
    info = {
        "CFBundleName": "Aedrova Staging",
        "CFBundleDisplayName": "Aedrova Staging",
        "CFBundleIdentifier": "com.aedrova.desktop.staging.source",
        "CFBundleExecutable": binary.name,
        "CFBundlePackageType": "APPL",
        "CFBundleVersion": "1",
        "NSHighResolutionCapable": True,
        "NSMicrophoneUsageDescription": (
            "Dictate an editable chat draft or enable meeting audio when you choose to."
        ),
        "NSCameraUsageDescription": "Enable video in a meeting when you choose to.",
    }
    info.update(install_macos_icon(root, contents))
    with (contents / "Info.plist").open("wb") as stream:
        plistlib.dump(info, stream)
    subprocess.run(
        ["codesign", "--force", "--sign", "-", str(bundle)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # The relocated interpreter needs its original standard library and this
    # checkout's virtualenv packages. Never copy credentials or a virtualenv.
    environment["PYTHONHOME"] = sys.base_prefix
    environment["PYTHONPATH"] = os.pathsep.join(
        [str(root / "src"), sysconfig.get_path("purelib"), sysconfig.get_path("platlib")]
    )
    return binary
