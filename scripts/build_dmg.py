"""Create an internal preview or notarized public installer from the built app."""

import argparse
import hashlib
import json
import platform
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


# Finder lays out the installer window: the app on the left, Applications on the right.
LAYOUT = """
tell application "Finder"
    set installer to disk "VOLUME"
    open installer
    set window_ to container window of installer
    set current view of window_ to icon view
    set toolbar visible of window_ to false
    set statusbar visible of window_ to false
    set the bounds of window_ to {200, 120, 860, 548}
    set options to the icon view options of window_
    set arrangement of options to not arranged
    set icon size of options to 112
    set text size of options to 13
    set background picture of options to file ".background:background.png" of installer
    set position of item "Aedrova.app" of window_ to {180, 215}
    set position of item "Applications" of window_ to {480, 215}
    update installer without registering applications
    delay 2
    close window_
end tell
"""


def command(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--notary-profile")
    args = parser.parse_args()
    app = ROOT / "dist/Aedrova.app"
    if not app.is_dir():
        parser.error("Package Aedrova first.")
    command("codesign", "--verify", "--deep", "--strict", str(app))
    signature = command("codesign", "--display", "--verbose=4", str(app)).stderr
    if not args.preview:
        if "Authority=Developer ID Application:" not in signature or not args.notary_profile:
            parser.error(
                "Public installer requires Developer ID signing and a Keychain notary profile."
            )
    if not args.preview:
        with TemporaryDirectory(prefix="aedrova-notary-") as folder:
            archive = str(Path(folder) / "Aedrova.zip")
            command("ditto", "-c", "-k", "--sequesterRsrc", "--keepParent", str(app), archive)
            result = command(
                "xcrun",
                "notarytool",
                "submit",
                archive,
                "--keychain-profile",
                args.notary_profile,
                "--wait",
                "--output-format",
                "json",
            )
            if json.loads(result.stdout).get("status") != "Accepted":
                raise RuntimeError("App notarization failed; no public installer created.")
        command("xcrun", "stapler", "staple", str(app))
        command("xcrun", "stapler", "validate", str(app))
        command("spctl", "--assess", "--type", "execute", str(app))
    target = ROOT / ("work/Aedrova-preview.dmg" if args.preview else "dist/Aedrova.dmg")
    with TemporaryDirectory(prefix="aedrova-installer-") as folder:
        stage = Path(folder) / "stage"
        stage.mkdir()
        shutil.copytree(app, stage / "Aedrova.app", symlinks=True)
        (stage / "Applications").symlink_to("/Applications")
        background = stage / ".background/background.png"
        command(sys.executable, str(ROOT / "scripts/dmg_background.py"), str(background))
        writable = Path(folder) / "installer.dmg"
        command(
            "hdiutil",
            "create",
            "-volname",
            "Aedrova",
            "-srcfolder",
            str(stage),
            "-format",
            "UDRW",
            "-ov",
            str(writable),
        )
        attached = command("hdiutil", "attach", str(writable), "-noverify").stdout
        # Another mounted "Aedrova" volume would make this one "Aedrova 1".
        mount = Path(
            next(
                line.split("\t")[-1].strip()
                for line in attached.splitlines()
                if "/Volumes/" in line
            )
        )
        try:
            command("osascript", "-e", LAYOUT.replace("VOLUME", mount.name))
            command("sync")
        finally:
            command("hdiutil", "detach", str(mount), "-force")
        target.unlink(missing_ok=True)
        command("hdiutil", "convert", str(writable), "-format", "UDZO", "-o", str(target))
    if not args.preview:
        identity = next(
            line.removeprefix("Authority=")
            for line in signature.splitlines()
            if line.startswith("Authority=Developer ID Application:")
        )
        command("codesign", "--sign", identity, "--timestamp", str(target))
        result = command(
            "xcrun",
            "notarytool",
            "submit",
            str(target),
            "--keychain-profile",
            args.notary_profile,
            "--wait",
            "--output-format",
            "json",
        )
        if json.loads(result.stdout).get("status") != "Accepted":
            raise RuntimeError("Notarization failed. Installer remains unavailable for release.")
        command("xcrun", "stapler", "staple", str(target))
        command("xcrun", "stapler", "validate", str(target))
        command(
            "spctl",
            "--assess",
            "--type",
            "open",
            "--context",
            "context:primary-signature",
            str(target),
        )
    with target.open("rb") as stream:
        checksum = hashlib.file_digest(stream, "sha256").hexdigest()
    with (app / "Contents/Info.plist").open("rb") as stream:
        info = plistlib.load(stream)
    manifest = {
        "path": str(target),
        "sha256": checksum,
        "public_release": not args.preview,
        "version": info.get("CFBundleShortVersionString", "0.1.0"),
        "architecture": platform.machine(),
        "minimum_macos": info.get("LSMinimumSystemVersion", "14.0"),
        "size_bytes": target.stat().st_size,
    }
    target.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
