"""Conservative local retention: never expire edited work or recovery receipts."""

import fcntl
import hashlib
import json
import os
import shutil
import time
from pathlib import Path
from uuid import UUID, uuid4

CONTEXT_AGE = 24 * 60 * 60
SNAPSHOT_AGE = 30 * 24 * 60 * 60


def fingerprints(root, deadline, *, original=False):
    from aedrova.agents.checkout import EXCLUDED_DIRS, excluded

    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError("Snapshot directory unavailable")
    values, total = {}, 0
    for folder, dirs, files in os.walk(root, followlinks=False):
        if not original and any(name in EXCLUDED_DIRS - {".git"} for name in dirs):
            raise ValueError("Extra build cache/configuration material is preserved")
        dirs[:] = [name for name in dirs if name not in EXCLUDED_DIRS]
        for name in dirs + files:
            if (Path(folder) / name).is_symlink():
                raise ValueError("Linked snapshot material")
        for name in files:
            if time.monotonic() > deadline:
                raise ValueError("Retention comparison deadline")
            path = Path(folder) / name
            relative = path.relative_to(root)
            if original and excluded(relative):
                continue
            stat = path.stat()
            if not path.is_file() or stat.st_size > 25 * 1024 * 1024:
                raise ValueError("Snapshot file exceeds bounds")
            total += stat.st_size
            if total > 200 * 1024 * 1024 or len(values) >= 20000:
                raise ValueError("Snapshot exceeds bounds")
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                while chunk := stream.read(65536):
                    if time.monotonic() > deadline:
                        raise ValueError("Retention comparison deadline")
                    digest.update(chunk)
            after = path.stat()
            if (stat.st_mtime_ns, stat.st_ino, stat.st_size) != (
                after.st_mtime_ns,
                after.st_ino,
                after.st_size,
            ):
                raise ValueError("Snapshot changed during comparison")
            values[relative.as_posix()] = (digest.digest(), bool(stat.st_mode & 0o111))
    return values


def protect(project):
    parent = Path(project).parent
    if parent.is_symlink() or not parent.is_dir():
        raise ValueError("Build retention directory is unavailable.")
    fd = os.open(parent / ".retention.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    lease = os.fdopen(fd, "w")
    try:
        fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        lease.close()
        raise ValueError("This build is active or being cleaned. Retry later.") from None
    return lease


def maintain(directory, *, now=None, dry_run=False, max_snapshots=3, protected=()):
    """At most 3 expensive comparisons; all remaining work is preserved.

    A snapshot expires only when it is 30 days idle, contains no delivery receipts,
    has no project edits and exactly matches its still-existing original project.
    Context-only deletion needs a 24-hour idle interval. Active leases always win.
    """
    root = Path(directory)
    result = {"contexts": [], "snapshots": []}
    if root.is_symlink() or not root.is_dir():
        return result
    now = time.time() if now is None else now
    compared = 0
    deadline = time.monotonic() + 5
    # Bounded directory work per pass; subsequent builds/maintenance handle the rest.
    cursor = root / ".retention-cursor"
    last = ""
    if cursor.is_file() and not cursor.is_symlink() and cursor.stat().st_size <= 36:
        last = cursor.read_text()
    candidates = sorted(root.iterdir(), key=lambda p: p.name)
    candidates = [p for p in candidates if p.name > last] + [
        p for p in candidates if p.name <= last
    ]
    candidates = candidates[:200]
    protected = {Path(path).resolve() for path in protected}
    for parent in candidates:
        try:
            if str(UUID(parent.name)) != parent.name or parent.is_symlink() or not parent.is_dir():
                continue
            if parent.resolve() in protected:
                continue
            marker = parent / "snapshot-info.json"
            if marker.is_symlink() or not marker.is_file() or marker.stat().st_size > 65536:
                continue
            idle = parent / ".last-used"
            stamp = idle if idle.is_file() and not idle.is_symlink() else marker
            age = now - stamp.stat().st_mtime
            if age < CONTEXT_AGE:
                continue
            lease = protect(parent / "project")
            try:
                context = parent / "workspace-context.jsonl"
                if context.is_file() and not context.is_symlink():
                    result["contexts"].append(str(parent))
                    if not dry_run:
                        context.unlink()
                if age < SNAPSHOT_AGE or compared >= max_snapshots:
                    continue
                if any(parent.glob("apply-backup-*")):
                    continue
                # Unknown files can be user recovery material; never discard them.
                if {p.name for p in parent.iterdir()} - {
                    "project",
                    "baseline",
                    "snapshot-info.json",
                    ".retention.lock",
                    ".last-used",
                    "workspace-context.jsonl",
                }:
                    continue
                compared += 1
                source = Path(json.loads(marker.read_text())["source"])
                if (
                    source.is_symlink()
                    or not source.is_absolute()
                    or source
                    in {
                        Path.home(),
                        Path(source.anchor),
                    }
                    or source.resolve().is_relative_to(root.resolve())
                ):
                    continue
                baseline = fingerprints(parent / "baseline", deadline)
                if fingerprints(parent / "project", deadline) != baseline:
                    continue
                original = fingerprints(source, deadline, original=True)
                if original != baseline:
                    continue
                if not shutil.rmtree.avoids_symlink_attacks:
                    continue
                result["snapshots"].append(str(parent))
                if not dry_run:
                    # Rename while holding the lease so new jobs cannot acquire the old path.
                    trash = root / (".expired-" + str(uuid4()))
                    parent.rename(trash)
                    shutil.rmtree(trash)
            finally:
                lease.close()
        except (OSError, ValueError, KeyError, TypeError):
            # Missing/changed/linked files or active jobs are preserved, never followed.
            continue
    if candidates and not dry_run:
        try:
            fd = os.open(cursor, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, "w") as stream:
                stream.write(candidates[-1].name[:36])
        except OSError:
            pass
    return result


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply", action="store_true", help="Apply the conservative retention policy"
    )
    args = parser.parse_args()
    result = maintain(
        Path.home() / "Library/Application Support/Aedrova/builds", dry_run=not args.apply
    )
    print(json.dumps({"dry_run": not args.apply, **result}, indent=2))


if __name__ == "__main__":
    main()
