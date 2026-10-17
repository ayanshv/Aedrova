"""Compile the native adaptive icon before signing a macOS application bundle."""

import hashlib
import plistlib
import shutil
import subprocess
import tempfile
from pathlib import Path


def install(root: Path, contents: Path) -> dict:
    """Install Apple's compiled catalog and compatible ICNS; return bundle metadata.

    Xcode 26+ is required. Never silently ship a static icon after compiler failure.
    Cache by source and compiler version for fast source-preview launches.
    """
    source = root / "branding/Aedrova.icon"
    version = subprocess.run(
        ["xcrun", "actool", "--version"], check=True, capture_output=True
    ).stdout
    digest = hashlib.sha256(version)
    for path in sorted(source.rglob("*")):
        if path.is_file():
            digest.update(str(path.relative_to(source)).encode())
            digest.update(path.read_bytes())
    cache = root / "work/macos-icon" / digest.hexdigest()
    metadata = cache / "info.plist"
    if not all((cache / name).is_file() for name in ("Assets.car", "Aedrova.icns", "info.plist")):
        cache.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache.parent) as directory:
            output = Path(directory)
            subprocess.run(
                [
                    "xcrun",
                    "actool",
                    str(source),
                    "--compile",
                    str(output),
                    "--platform",
                    "macosx",
                    "--minimum-deployment-target",
                    "14.0",
                    "--app-icon",
                    "Aedrova",
                    "--output-partial-info-plist",
                    str(output / "info.plist"),
                    "--output-format",
                    "human-readable-text",
                ],
                check=True,
            )
            for name in ("Assets.car", "Aedrova.icns", "info.plist"):
                if not (output / name).is_file():
                    raise RuntimeError(f"Native icon compiler did not produce {name}")
            cache.mkdir(parents=True, exist_ok=True)
            for name in ("Assets.car", "Aedrova.icns", "info.plist"):
                shutil.copy2(output / name, cache / name)
    resources = contents / "Resources"
    resources.mkdir(parents=True, exist_ok=True)
    for name in ("Assets.car", "Aedrova.icns"):
        shutil.copy2(cache / name, resources / name)
    with metadata.open("rb") as stream:
        info = plistlib.load(stream)
    return {key: info[key] for key in ("CFBundleIconName", "CFBundleIconFile")}
