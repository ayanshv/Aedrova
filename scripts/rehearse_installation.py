"""Rehearse preview installation/replacement/rollback in a disposable Applications folder.

Never touches /Applications, real settings, projects or public release configuration.
Both copies use the same preview version; this checks replacement mechanics, not a
different-version migration or fresh-Mac/Gatekeeper acceptance.
"""

import hashlib
import json
import plistlib
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtCore import QSettings

from aedrova.delivery.releases import validate_release

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "work/m14-installation"


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=180)


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)
    image = ROOT / "work/Aedrova-preview.dmg"
    metadata = json.loads(image.with_suffix(".manifest.json").read_text())
    assert metadata["public_release"] is False, "Use an internal preview only."
    with image.open("rb") as stream:
        assert hashlib.file_digest(stream, "sha256").hexdigest() == metadata["sha256"]
    assert image.stat().st_size == metadata["size_bytes"]
    try:
        validate_release(metadata)
    except ValueError as error:
        assert "not ready" in str(error)
    else:
        raise AssertionError("Preview must not be accepted by the public updater.")
    run("hdiutil", "verify", str(image))
    evidence = {"public_release": False, "version": metadata["version"], "checks": []}
    with TemporaryDirectory(prefix="aedrova-m14-") as directory:
        root = Path(directory)
        mount = root / "mounted"
        mount.mkdir()
        attached = False
        try:
            run(
                "hdiutil", "attach", str(image), "-readonly", "-nobrowse", "-mountpoint", str(mount)
            )
            attached = True
            assert (mount / "Applications").is_symlink()
            assert (mount / "Applications").readlink() == Path("/Applications")
            source = mount / "Aedrova.app"
            with (source / "Contents/Info.plist").open("rb") as stream:
                info = plistlib.load(stream)
            assert info["CFBundleShortVersionString"] == metadata["version"]
            run("codesign", "--verify", "--deep", "--strict", str(source))
            evidence["checks"].append("DMG digest, size, integrity, link, version and signature")
            applications = root / "Applications"
            applications.mkdir()
            installed = applications / "Aedrova.app"
            previous = applications / "Aedrova.previous.app"
            preferences = root / "preferences.ini"
            settings = QSettings(str(preferences), QSettings.Format.IniFormat)
            settings.setValue("appearance", "light")
            settings.setValue("editor", "Visual Studio Code")
            settings.setValue("rehearsal/marker", "preserve across replacement")
            settings.sync()
            project = root / "user-project/main.py"
            project.parent.mkdir()
            project.write_text("# User-owned project: must survive replacement.\n")
            project_digest = hashlib.sha256(project.read_bytes()).hexdigest()

            def launch(stage, theme):
                run("codesign", "--verify", "--deep", "--strict", str(installed))
                report = REPORTS / f"{stage}.json"
                result = run(
                    str(installed / "Contents/MacOS/Aedrova"),
                    "--demo",
                    "--settings-file",
                    str(preferences),
                    "--theme",
                    theme,
                    "--smoke-report",
                    str(report),
                )
                (REPORTS / f"{stage}.log").write_text(result.stdout + result.stderr)
                smoke = json.loads(report.read_text())
                assert smoke["packaged"] and smoke["screenshot_saved"]
                assert smoke["theme"] == theme and smoke["tabs"] >= 5
                assert smoke["messages"] > 0
                preserved = QSettings(str(preferences), QSettings.Format.IniFormat)
                assert preserved.value("appearance") == "light"
                assert preserved.value("editor") == "Visual Studio Code"
                assert preserved.value("rehearsal/marker") == "preserve across replacement"
                assert hashlib.sha256(project.read_bytes()).hexdigest() == project_digest
                evidence["checks"].append(
                    f"{stage}: signed packaged launch, settings/project retained"
                )

            run("ditto", str(source), str(installed))
            launch("installed-light", "light")
            installed.rename(previous)
            run("ditto", str(source), str(installed))
            launch("replacement-dark", "dark")
            installed.rename(applications / "Aedrova.replacement.app")
            previous.rename(installed)
            launch("rollback-light", "light")
        finally:
            if attached:
                run("hdiutil", "detach", str(mount))
    evidence["limitations"] = [
        "Same-version preview replacement; no released version upgrade was available.",
        "Same Mac, demo data and isolated preferences; no live account migration tested.",
        "Apple Development preview; Developer ID/notarization/fresh-Mac acceptance pending.",
    ]
    (REPORTS / "acceptance.json").write_text(json.dumps(evidence, indent=2) + "\n")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
