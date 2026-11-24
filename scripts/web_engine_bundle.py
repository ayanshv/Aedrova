"""Make the packaged Qt WebEngine framework valid, then sign it inside-out.

PyInstaller copies QtWebEngineCore's helper app and resources next to the version folder
(Versions/Resources) instead of inside it (Versions/A/...), so codesign rejects the framework
("embedded framework contains modified or invalid version"). Moving them into place and signing
the helper, the framework and then the app lets the bundle verify and be notarized.
"""

import shutil
import subprocess
import sys
from pathlib import Path


def repair(bundle):
    """Move stray framework content into Versions/A. Returns the frameworks it fixed."""
    fixed = []
    for framework in Path(bundle).rglob("QtWebEngineCore.framework"):
        versions = framework / "Versions"
        stray, version = versions / "Resources", versions / "A"
        if not stray.is_dir() or stray.is_symlink() or not version.is_dir():
            continue
        helpers = stray / "Helpers"
        if helpers.is_dir():
            destination = version / "Helpers"
            if destination.exists():
                shutil.rmtree(destination)
            shutil.move(str(helpers), str(destination))
        resources = stray / "Resources"
        if resources.is_dir():
            destination = version / "Resources"
            destination.mkdir(exist_ok=True)
            for item in resources.iterdir():
                target = destination / item.name
                if not target.exists():
                    shutil.move(str(item), str(target))
        shutil.rmtree(stray)
        fixed.append(framework)
    return fixed


def sign(bundle, identity, entitlements):
    """Sign helper apps, then frameworks, then leave the app itself to the caller."""
    base = ["codesign", "--force", "--sign", identity, "--options", "runtime", "--timestamp"]
    for helper in sorted(Path(bundle).rglob("QtWebEngineProcess.app")):
        subprocess.run([*base, "--entitlements", str(entitlements), str(helper)], check=True)
    for framework in sorted(Path(bundle).rglob("QtWebEngineCore.framework")):
        subprocess.run([*base, str(framework)], check=True)


if __name__ == "__main__":
    app, identity, entitlements = sys.argv[1:4]
    print("repaired:", [str(p) for p in repair(app)])
    sign(app, identity, entitlements)
