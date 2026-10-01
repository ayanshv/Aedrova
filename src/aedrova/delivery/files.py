"""Immutable review payloads with optimistic conflict checks and local recovery copies."""

import difflib
import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from aedrova.agents.checkout import EXCLUDED_DIRS, excluded


@dataclass(frozen=True)
class FileVersion:
    data: bytes
    executable: bool = False

    @property
    def digest(self):
        return hashlib.sha256(self.data + bytes([self.executable])).hexdigest()


@dataclass(frozen=True)
class Change:
    path: str
    before: FileVersion | None
    after: FileVersion | None

    def description(self):
        return (
            ("Added" if self.before is None else "Deleted" if self.after is None else "Modified")
            + " · "
            + self.path
        )

    def diff(self):
        old = self.before.data if self.before else b""
        new = self.after.data if self.after else b""
        if len(old) + len(new) > 1024 * 1024:
            return (
                "This file is too large for the inline diff. "
                "Review both versions in your IDE before approving.\nBaseline: ../baseline/"
                + self.path
            )
        if b"\0" in old + new:
            return f"Binary file: {len(old)} → {len(new)} bytes."
        try:
            result = "".join(
                difflib.unified_diff(
                    old.decode().splitlines(keepends=True),
                    new.decode().splitlines(keepends=True),
                    fromfile="before/" + self.path,
                    tofile="after/" + self.path,
                )
            )
        except UnicodeDecodeError:
            return f"Binary file: {len(old)} → {len(new)} bytes."
        if self.before and self.after and self.before.executable != self.after.executable:
            result = (
                f"Executable permission: {self.before.executable} → {self.after.executable}\n"
                + result
            )
        return result or "File added or deleted with empty content."


@dataclass(frozen=True)
class Review:
    project: Path
    source: Path
    changes: tuple[Change, ...]
    digest: str


def inventory(root):
    root = Path(root).resolve(strict=True)
    values, size = {}, 0
    for directory, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [name for name in dirs if name not in EXCLUDED_DIRS]
        for name in dirs + files:
            path = Path(directory) / name
            if path.is_symlink():
                raise ValueError(
                    "Linked files or folders cannot be delivered. Replace the link first."
                )
        for name in files:
            path = Path(directory) / name
            if not path.is_file():
                raise ValueError("Only regular project files can be reviewed.")
            stat = path.stat()
            size += stat.st_size
            if stat.st_size > 25 * 1024 * 1024 or size > 200 * 1024 * 1024 or len(values) >= 20000:
                raise ValueError("Review exceeds the project file or size limit.")
            data = path.read_bytes()
            if path.stat().st_mtime_ns != stat.st_mtime_ns or len(data) != stat.st_size:
                raise ValueError("Files changed during review. Refresh the review.")
            values[path.relative_to(root).as_posix()] = FileVersion(
                data, bool(stat.st_mode & 0o111)
            )
    return values


def make_review(project):
    project = Path(project).resolve(strict=True)
    info = json.loads((project.parent / "snapshot-info.json").read_text())
    baseline = project.parent / "baseline"
    if not baseline.is_dir():
        raise ValueError("This build predates review support. Create a new plan and build first.")
    before, after = inventory(baseline), inventory(project)
    changes = tuple(
        Change(name, before.get(name), after.get(name))
        for name in sorted(before.keys() | after.keys())
        if before.get(name) != after.get(name)
    )
    serialized = [
        (c.path, c.before.digest if c.before else None, c.after.digest if c.after else None)
        for c in changes
    ]
    digest = hashlib.sha256(
        json.dumps([str(project), info["source"], serialized]).encode()
    ).hexdigest()
    return Review(project, Path(info["source"]), changes, digest)


def check_review(review):
    if make_review(review.project).digest != review.digest:
        raise ValueError("Build files changed after review. Refresh and approve the new changes.")
    for change in review.changes:
        path = Path(change.path)
        if path.is_absolute() or ".." in path.parts or excluded(path):
            raise ValueError(f"Protected path cannot be delivered: {change.path}")


def checked_target(root, relative):
    root = root.resolve(strict=True)
    target = root / relative
    if not target.resolve().is_relative_to(root):
        raise ValueError("A target path escapes the project.")
    for node in [target, *target.parents]:
        if node == root:
            break
        if node.is_symlink():
            raise ValueError("The destination contains a symbolic link.")
    if target.exists() and not target.is_file():
        raise ValueError("A destination is no longer a regular file.")
    return target


def read_version(path):
    if not path.exists():
        return None
    return FileVersion(path.read_bytes(), bool(path.stat().st_mode & 0o111))


def apply_review(review, *, guard=lambda: None):
    """Check every touched file before writing; leave unrelated and staged work alone."""
    guard()
    check_review(review)
    root = review.source.resolve(strict=True)
    targets = {c.path: checked_target(root, c.path) for c in review.changes}
    conflicts = [c.path for c in review.changes if read_version(targets[c.path]) != c.before]
    if conflicts:
        raise ValueError(
            "Local files changed since this build started: " + ", ".join(conflicts[:8])
        )
    receipt = review.project.parent / ("apply-backup-" + str(uuid4()))
    receipt.mkdir(mode=0o700)
    (receipt / "receipt.json").write_text(
        json.dumps(
            {
                "target": str(root),
                "review": review.digest,
                "changes": [
                    {"path": c.path, "existed": c.before is not None} for c in review.changes
                ],
            },
            indent=2,
        )
    )
    written = []
    try:
        for change in review.changes:
            guard()
            target = checked_target(root, change.path)
            if read_version(target) != change.before:
                raise ValueError(
                    "A local file changed while applying. Restore using the backup if needed."
                )
            original_mode = target.stat().st_mode & 0o777 if change.before else 0o644
            if change.before:
                backup = receipt / "files" / change.path
                backup.parent.mkdir(parents=True, exist_ok=True)
                backup.write_bytes(change.before.data)
                backup.chmod(original_mode)
            if change.after is None:
                target.unlink()
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                temp = target.parent / (".aedrova-" + str(uuid4()))
                try:
                    temp.write_bytes(change.after.data)
                    mode = original_mode & ~0o111
                    if change.after.executable:
                        mode |= (original_mode & 0o444) >> 2
                    temp.chmod(mode)
                    os.replace(temp, target)
                finally:
                    temp.unlink(missing_ok=True)
            written.append(change)
    except Exception:
        for change in reversed(written):
            target = checked_target(root, change.path)
            # Never overwrite edits made by somebody else during rollback.
            if read_version(target) == change.after:
                if change.before:
                    shutil.copy2(receipt / "files" / change.path, target)
                else:
                    target.unlink(missing_ok=True)
        raise
    return receipt
