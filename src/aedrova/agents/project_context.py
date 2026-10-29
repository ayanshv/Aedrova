"""Bounded read-only evidence from the user's explicitly connected project.

No commands, dependency traversal, symlinks, persistent index or absolute paths sent.
"""

import hashlib
import json
import os
import re
import stat
from pathlib import Path

from aedrova.agents.checkout import excluded, git
from aedrova.security.credentials import credential_rules

TEXT_TYPES = {
    ".md",
    ".txt",
    ".py",
    ".toml",
    ".json",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".html",
    ".css",
    ".sql",
    ".yaml",
    ".yml",
    ".rs",
    ".go",
}
OMIT = {"work", "dist", "build", "coverage", "vendor", "target", "logs"}


def read_local(root, relative):
    if os.open in os.supports_dir_fd:
        descriptors = [os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)]
        try:
            for part in relative.parts[:-1]:
                descriptors.append(
                    os.open(
                        part,
                        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                        dir_fd=descriptors[-1],
                    )
                )
            descriptor = os.open(
                relative.name,
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                dir_fd=descriptors[-1],
            )
            with os.fdopen(descriptor, "rb") as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_size > 32768:
                    return None
                return stream.read(32769)
        finally:
            for descriptor in reversed(descriptors):
                os.close(descriptor)
    # On Windows reject reparse/symlink paths before and after the bounded read.
    source = root / relative
    if any(
        (root / Path(*relative.parts[:i])).is_symlink() for i in range(1, len(relative.parts) + 1)
    ):
        return None
    if not source.resolve().is_relative_to(root):
        return None
    with source.open("rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > 32768:
            return None
        data = stream.read(32769)
    return data if source.resolve().is_relative_to(root) and not source.is_symlink() else None


def project_evidence(folder, question, cancelled=lambda: False):
    root = Path(folder).expanduser().resolve(strict=True)
    if not root.is_dir() or root in {Path.home().resolve(), Path(root.anchor)}:
        raise ValueError("Reconnect a specific project folder in Project settings.")
    candidates, seen = [], 0
    permitted = None
    if (root / ".git").exists():
        # Respect ignored/untracked-private files as well as our own denylist.
        permitted = set(
            git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z").split("\0")
        )
    for directory, dirs, files in os.walk(root, followlinks=False):
        if cancelled():
            raise InterruptedError("Reply stopped.")
        dirs[:] = sorted(
            d
            for d in dirs
            if not excluded(Path(d)) and d not in OMIT and not (Path(directory) / d).is_symlink()
        )
        for name in sorted(files):
            seen += 1
            if seen > 10000:
                break
            relative = (Path(directory) / name).relative_to(root)
            if permitted is not None and relative.as_posix() not in permitted:
                continue
            if excluded(relative) or ".private." in name or any(p in OMIT for p in relative.parts):
                continue
            if relative.suffix.lower() in TEXT_TYPES and not (root / relative).is_symlink():
                candidates.append(relative)
        if seen > 10000:
            break
    terms = set(re.findall(r"[a-zA-Z0-9_]{3,}", question.casefold()))

    def rank(path):
        name = path.as_posix().casefold()
        return (
            0 if path.name.casefold().startswith("readme") else 1,
            -sum(term in name for term in terms),
            len(path.parts),
            name,
        )

    records, total = [], 0
    for relative in sorted(candidates, key=rank)[:64]:
        if cancelled():
            raise InterruptedError("Reply stopped.")
        source = root / relative
        # Reject linked ancestors too, including a link swapped during enumeration.
        if any(
            (root / Path(*relative.parts[:i])).is_symlink()
            for i in range(1, len(relative.parts) + 1)
        ):
            continue
        try:
            data = read_local(root, relative)
            if data is None or len(data) > 32768 or b"\0" in data or credential_rules(data):
                continue
            text = data.decode("utf-8")
        except (OSError, UnicodeError):
            continue
        # Never follow a path that changed during the read.
        if source.is_symlink() or not source.resolve().is_relative_to(root):
            continue
        text = text[:8000]
        if total + len(text.encode()) > 64000:
            break
        total += len(text.encode())
        record = {
            "path": relative.as_posix(),
            "text": text,
            "truncated": len(data.decode("utf-8")) > len(text),
        }
        record["citation"] = (
            "project:"
            + hashlib.sha256((relative.as_posix() + "\0" + text).encode()).hexdigest()[:24]
        )
        records.append({"project_file": record})
    coverage = {
        "project_coverage": {
            "name": root.name,
            "files_read": len(records),
            "candidate_files": len(candidates),
            "untrusted": True,
            "notice": "Selected local text only; excludes secrets, binary, linked/generated files. "
            "Not a complete project audit. File paths are relative to the connected folder.",
        }
    }
    return "\n".join(json.dumps(r, ensure_ascii=False) for r in [coverage, *records])
