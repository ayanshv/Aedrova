"""Independent local Git copies; the user's checkout is never edited implicitly."""

import os
import shutil
import subprocess
from pathlib import Path
from uuid import uuid4


def git(root, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull, GIT_TERMINAL_PROMPT="0")
    result = subprocess.run(
        [
            "git",
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "core.fsmonitor=false",
            "-C",
            str(root),
            *args,
        ],
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
    )
    if result.returncode:
        raise ValueError(
            "Git operation failed. Select a local repository with a committed history."
        )
    return result.stdout


EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".next",
    ".cache",
    ".pytest_cache",
    ".codex",
    ".claude",
}


def excluded(path):
    return (
        any(part in EXCLUDED_DIRS for part in path.parts)
        or path.name == ".DS_Store"
        or path.name.startswith(".env")
        or path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}
        or path.name in {"id_rsa", "id_ed25519", "credentials.json"}
    )


def prepare(repository, builds):
    """Snapshot current files, including uncommitted work, without changing the source."""
    import json

    root = Path(repository).expanduser().resolve(strict=True)
    if not root.is_dir() or root in {Path.home().resolve(), Path(root.anchor)}:
        raise ValueError("Choose a specific project folder, not your home or disk root.")
    try:
        if not (root / ".git").exists():
            raise ValueError(
                "Selected folder is an independent project, not its parent repository."
            )
        tracked = git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z")
        candidates = [Path(name) for name in tracked.split("\0") if name]
    except ValueError:
        candidates = []
        for directory, dirs, files in os.walk(root, followlinks=False):
            dirs[:] = [name for name in dirs if name not in EXCLUDED_DIRS]
            for name in dirs:
                if (Path(directory) / name).is_symlink():
                    raise ValueError(
                        "Project contains linked folders. Choose their actual folder "
                        "or remove the link before creating a snapshot."
                    ) from None
            candidates.extend((Path(directory) / name).relative_to(root) for name in files)
    if len(candidates) > 20000:
        raise ValueError("Project exceeds the 20,000-file snapshot limit. Choose a smaller folder.")
    Path(builds).mkdir(parents=True, exist_ok=True, mode=0o700)
    if shutil.disk_usage(builds).free < 512 * 1024 * 1024:
        raise ValueError("Free at least 512 MiB on this Mac before starting another build.")
    destination = Path(builds) / str(uuid4())
    destination.mkdir(parents=True, mode=0o700)
    project = destination / "project"
    project.mkdir(mode=0o700)
    size, copied, omitted = 0, 0, 0
    for relative in sorted(set(candidates)):
        if excluded(relative):
            omitted += 1
            continue
        source = root / relative
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or not source.resolve().is_relative_to(root)
        ):
            raise ValueError("A project link points outside the selected folder. Snapshot stopped.")
        if not source.is_file():
            continue
        stat = source.stat()
        size += stat.st_size
        if stat.st_size > 25 * 1024 * 1024 or size > 200 * 1024 * 1024:
            raise ValueError("Snapshot exceeds the 25 MiB per-file / 200 MiB total limit.")
        target = project / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        data = source.read_bytes()
        if source.stat().st_mtime_ns != stat.st_mtime_ns or len(data) != stat.st_size:
            raise ValueError("A project file changed while copying. Please create the plan again.")
        target.write_bytes(data)
        target.chmod(0o755 if stat.st_mode & 0o111 else 0o644)
        copied += 1
    inherited = root.parent / "snapshot-info.json"
    if (
        root.name == "project"
        and root.parent.parent.resolve() == Path(builds).resolve()
        and inherited.is_file()
    ):
        if not (root.parent / "baseline").is_dir():
            raise ValueError(
                "This older build has no review baseline. "
                "Select the original project and create a new plan."
            )
        original = json.loads(inherited.read_text())["source"]
        shutil.copytree(root.parent / "baseline", destination / "baseline")
    else:
        original = str(root)
        shutil.copytree(project, destination / "baseline")
    git(project, "init", "-q")
    git(project, "config", "core.hooksPath", "/dev/null")
    git(project, "add", "--force", "--all")
    git(
        project,
        "-c",
        "user.name=Aedrova",
        "-c",
        "user.email=build@aedrova.local",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "--allow-empty",
        "-qm",
        "Local project snapshot",
    )
    (destination / "snapshot-info.json").write_text(
        json.dumps(
            {
                "source": original,
                "files": copied,
                "excluded_files": omitted,
                "note": "Secrets, runtime configuration and dependency folders are excluded. "
                "The original folder is unchanged.",
            },
            indent=2,
        )
    )
    return project


def changes(project):
    return git(project, "status", "--short") + "\n" + git(project, "diff", "--stat", "HEAD")
