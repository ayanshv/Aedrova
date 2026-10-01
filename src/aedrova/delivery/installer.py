"""Explicit, per-user installation of a pinned official GitHub CLI release.

Hashes from https://api.github.com/repos/cli/cli/releases/tags/v2.102.0.
No shell scripts, package manager, administrator permissions or PATH changes.
"""

import hashlib
import io
import os
import platform
import shutil
import stat
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

VERSION = "2.102.0"
CHECKSUMS = {
    "arm64": "da922c20d1792e5b2cbf375593d7a658acf034c12c84e007e71c76ef959c337e",
    "amd64": "b245f24eb2bf5f75b426b4c26da3651a107f8d5b6f4fddfbfccc5679041378b3",
}
MAX_ARCHIVE = 40 * 1024 * 1024
MAX_BINARY = 100 * 1024 * 1024


def architecture():
    if platform.system() != "Darwin":
        raise ValueError("This guided installer supports macOS. Install from cli.github.com.")
    arch = {"arm64": "arm64", "aarch64": "arm64", "x86_64": "amd64"}.get(platform.machine())
    if not arch:
        raise ValueError("This Mac architecture is not supported by the guided installer.")
    return arch


def install_root():
    return Path.home() / "Library/Application Support/Aedrova/tools/github-cli"


def managed_path():
    return install_root() / VERSION / architecture() / "gh"


class GitHubRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlsplit(newurl)
        if parsed.scheme != "https" or parsed.hostname not in {
            "github.com",
            "release-assets.githubusercontent.com",
            "objects.githubusercontent.com",
        }:
            raise ValueError("GitHub's download redirected to an unexpected host.")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download(arch, progress, cancelled):
    name = f"gh_{VERSION}_macOS_{arch}.zip"
    request = urllib.request.Request(
        f"https://github.com/cli/cli/releases/download/v{VERSION}/{name}",
        headers={"User-Agent": "Aedrova-desktop"},
    )
    opener = urllib.request.build_opener(GitHubRedirect())
    data = bytearray()
    started = time.monotonic()
    with opener.open(request, timeout=20) as response:
        while True:
            if cancelled():
                raise InterruptedError("Download cancelled.")
            if time.monotonic() - started > 300:
                raise TimeoutError("GitHub download timed out.")
            block = response.read(128 * 1024)
            if not block:
                break
            data.extend(block)
            if len(data) > MAX_ARCHIVE:
                raise ValueError("GitHub download exceeds the expected size limit.")
            progress(f"Downloading GitHub CLI · {len(data) / 1024 / 1024:.1f} MB")
    return bytes(data)


def install(*, progress=lambda _: None, cancelled=lambda: False, root=None, fetch=download):
    arch = architecture()
    progress("Downloading GitHub's official CLI…")
    data = fetch(arch, progress, cancelled)
    if cancelled():
        raise InterruptedError("Download cancelled.")
    if len(data) > MAX_ARCHIVE or hashlib.sha256(data).hexdigest() != CHECKSUMS[arch]:
        raise ValueError("Download verification failed. Nothing was installed. Try again later.")
    progress("Verified download. Installing for your Mac account…")
    prefix = f"gh_{VERSION}_macOS_{arch}"
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        if len(archive.namelist()) != len(set(archive.namelist())):
            raise ValueError("Invalid GitHub archive: duplicate paths.")
        binary = archive.getinfo(prefix + "/bin/gh")
        license_file = archive.getinfo(prefix + "/LICENSE")
        for entry, limit in ((binary, MAX_BINARY), (license_file, 100000)):
            if entry.file_size > limit or stat.S_ISLNK(entry.external_attr >> 16):
                raise ValueError("Invalid GitHub archive member.")
        # Read only these exact members. Never extract paths from an archive to disk.
        executable, license_text = archive.read(binary), archive.read(license_file)
    base = Path(root) if root is not None else install_root()
    destination = base / VERSION / arch
    destination.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    staging = Path(tempfile.mkdtemp(prefix=".install-", dir=destination.parent))
    try:
        (staging / "gh").write_bytes(executable)
        (staging / "gh").chmod(0o700)
        (staging / "LICENSE").write_bytes(license_text)
        if cancelled():
            raise InterruptedError("Installation cancelled.")
        if destination.exists():
            raise ValueError("A managed installation already exists. Reopen setup to detect it.")
        os.rename(staging, destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    progress("GitHub CLI is installed.")
    return destination / "gh"
