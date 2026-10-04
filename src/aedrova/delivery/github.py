"""GitHub delivery via the user's OS-backed gh login, outside the agent process.

Only new branches are created. No force push, merge, or token stored by Aedrova.
"""

import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4

from aedrova.delivery.files import check_review
from aedrova.security.credentials import credential_rules


def repository_name(value):
    value = value.strip().removesuffix(".git").removeprefix("https://github.com/")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]{0,38}/[A-Za-z0-9_.-]{1,100}", value):
        raise ValueError("Enter a GitHub repository as owner/repository or its HTTPS URL.")
    return value


def gh_path():
    from aedrova.delivery.installer import managed_path

    try:
        managed = managed_path()
        if managed.is_file() and os.access(managed, os.X_OK):
            return str(managed)
    except ValueError:
        pass
    path = shutil.which("gh")
    if path:
        return path
    for candidate in ("/opt/homebrew/bin/gh", "/usr/local/bin/gh"):
        if Path(candidate).is_file():
            return candidate
    raise ValueError(
        "Open GitHub setup to install the helper and sign in, then check this connection again."
    )


def github_environment():
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GH_", "GITHUB_"))}
    env.update(GH_PROMPT_DISABLED="1", GH_PAGER="cat", NO_COLOR="1")
    return env


class GitHub:
    def api(self, method, endpoint, payload=None):
        executable = gh_path()
        env = github_environment()
        args = [
            executable,
            "api",
            "--hostname",
            "github.com",
            "--method",
            method,
            "-H",
            "Accept: application/vnd.github+json",
            endpoint,
        ]
        if payload is not None:
            args += ["--input", "-"]
        result = subprocess.run(
            args,
            input=json.dumps(payload) if payload is not None else None,
            capture_output=True,
            text=True,
            timeout=90,
            env=env,
            cwd=Path.home(),
        )
        if result.returncode:
            # Provider output may include credentials or private response bodies.
            raise ValueError(
                "GitHub request failed. Check gh auth status, repository permissions and "
                "network access. The remote may have changed; inspect it before retrying."
            )
        return json.loads(result.stdout) if result.stdout.strip() else {}

    def connection(self, repo):
        repo = repository_name(repo)
        data = self.api("GET", f"repos/{repo}")
        if data.get("archived") or not data.get("permissions", {}).get("push"):
            raise ValueError("This GitHub login needs write access to an active repository.")
        return {"repository": repo, "branch": data["default_branch"], "private": data["private"]}


@dataclass(frozen=True)
class Publication:
    repository: str
    base_branch: str
    base_sha: str
    tree_sha: str
    branch: str
    review_digest: str
    title: str
    private: bool
    expires: float


def prepare_publication(client, repo, review, title):
    check_review(review)
    if not review.changes:
        raise ValueError("There are no changes to publish.")
    for change in review.changes:
        if change.path.startswith(".github/workflows/"):
            raise ValueError("Workflow changes need separate manual review and publication.")
        if change.after and credential_rules(change.after.data):
            raise ValueError(f"Potential credential in {change.path}. Remove it before publishing.")
    connection = client.connection(repo)
    repo, branch = connection["repository"], connection["branch"]
    head = client.api("GET", f"repos/{repo}/git/ref/heads/{quote(branch, safe='')}")["object"][
        "sha"
    ]
    commit = client.api("GET", f"repos/{repo}/git/commits/{head}")
    tree_sha = commit["tree"]["sha"]
    tree = client.api("GET", f"repos/{repo}/git/trees/{tree_sha}?recursive=1")
    if tree.get("truncated"):
        raise ValueError("GitHub's tree response was truncated. No partial publication is allowed.")
    entries = {item["path"]: item for item in tree["tree"]}
    for change in review.changes:
        remote = entries.get(change.path)
        if change.before is None:
            matches = remote is None
        else:
            data = change.before.data
            blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            mode = "100755" if change.before.executable else "100644"
            matches = bool(
                remote
                and remote["type"] == "blob"
                and remote["sha"] == blob
                and remote["mode"] == mode
            )
        if not matches:
            raise ValueError(
                f"GitHub differs from the build's starting files at {change.path}. "
                f"Reconcile that file and rebuild before publishing."
            )
    return Publication(
        repo,
        branch,
        head,
        tree_sha,
        "aedrova/" + uuid4().hex[:12],
        review.digest,
        title.strip()[:120] or "Aedrova build",
        connection["private"],
        time.monotonic() + 600,
    )


def publish(
    client, publication, review, *, authorized, progress=lambda _: None, guard=lambda: None
):
    if not authorized or time.monotonic() > publication.expires:
        raise PermissionError("A fresh explicit publication approval is required.")
    check_review(review)
    if review.digest != publication.review_digest:
        raise ValueError("The reviewed files changed. Prepare publication again.")
    guard()
    repo = publication.repository
    connection = client.connection(repo)
    if connection["private"] != publication.private:
        raise ValueError("Repository visibility changed. Prepare publication again.")
    current = client.api(
        "GET", f"repos/{repo}/git/ref/heads/{quote(publication.base_branch, safe='')}"
    )
    if current["object"]["sha"] != publication.base_sha:
        raise ValueError("The GitHub base branch changed. Prepare a new review before pushing.")
    tree = []
    for change in review.changes:
        guard()
        sha = None
        if change.after is not None:
            sha = client.api(
                "POST",
                f"repos/{repo}/git/blobs",
                {"content": base64.b64encode(change.after.data).decode(), "encoding": "base64"},
            )["sha"]
        tree.append(
            {
                "path": change.path,
                "mode": "100755" if change.after and change.after.executable else "100644",
                "type": "blob",
                "sha": sha,
            }
        )
    guard()
    new_tree = client.api(
        "POST", f"repos/{repo}/git/trees", {"base_tree": publication.tree_sha, "tree": tree}
    )["sha"]
    guard()
    commit = client.api(
        "POST",
        f"repos/{repo}/git/commits",
        {"message": publication.title, "tree": new_tree, "parents": [publication.base_sha]},
    )["sha"]
    guard()
    latest = client.api(
        "GET", f"repos/{repo}/git/ref/heads/{quote(publication.base_branch, safe='')}"
    )
    if latest["object"]["sha"] != publication.base_sha:
        raise ValueError(
            "The GitHub base branch changed during upload. No branch created; prepare a new review."
        )
    client.api(
        "POST", f"repos/{repo}/git/refs", {"ref": "refs/heads/" + publication.branch, "sha": commit}
    )
    branch_url = f"https://github.com/{repo}/tree/{publication.branch}"
    progress("Branch published: " + branch_url)
    try:
        pr = client.api(
            "POST",
            f"repos/{repo}/pulls",
            {
                "title": publication.title,
                "head": publication.branch,
                "base": publication.base_branch,
                "draft": True,
                "body": "Changes reviewed and explicitly approved in Aedrova.\n\nReview digest: "
                + review.digest
                + "\n\nReview actual test output before merging. "
                "Publication does not imply tests passed.",
            },
        )
    except (ValueError, TimeoutError, subprocess.TimeoutExpired):
        return {
            "url": branch_url,
            "message": "Branch published, but pull-request creation failed. Open GitHub "
            "to check/create the PR; do not repeat the push.",
        }
    return {
        "url": pr["html_url"],
        "message": "New branch and draft pull request created. Nothing merged.",
    }
