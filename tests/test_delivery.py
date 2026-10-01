import base64
import hashlib
from dataclasses import replace
from urllib.error import HTTPError
from urllib.request import urlopen

import pytest

from aedrova.agents.checkout import prepare
from aedrova.delivery.files import apply_review, make_review
from aedrova.delivery.github import prepare_publication, publish, repository_name
from aedrova.delivery.preview import StaticPreview


@pytest.fixture
def build(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "existing.py").write_text("value = 1\n")
    (source / "untouched.txt").write_text("keep local work\n")
    project = prepare(source, tmp_path / "builds")
    (project / "existing.py").write_text("value = 2\n")
    (project / "new.py").write_text("hello = True\n")
    return source, project


def test_review_and_apply_preserve_unrelated_changes_and_backup(build):
    source, project = build
    review = make_review(project)
    assert len(review.changes) == 2
    assert "+value = 2" in review.changes[0].diff()
    (source / "untouched.txt").write_text("edited while building")
    receipt = apply_review(review)
    assert (source / "existing.py").read_text() == "value = 2\n"
    assert (source / "untouched.txt").read_text() == "edited while building"
    assert (receipt / "files/existing.py").read_text() == "value = 1\n"
    assert (receipt / "receipt.json").exists()


def test_apply_rejects_source_conflicts_before_any_write(build):
    source, project = build
    (source / "existing.py").write_text("user changes")
    with pytest.raises(ValueError, match="Local files changed"):
        apply_review(make_review(project))
    assert not (source / "new.py").exists()
    assert (source / "existing.py").read_text() == "user changes"


def test_changed_artifact_invalidates_review(build):
    source, project = build
    review = make_review(project)
    (project / "new.py").write_text("changed again")
    with pytest.raises(ValueError, match="changed after review"):
        apply_review(review)
    assert not (source / "new.py").exists()


def test_delete_review_keeps_recovery_copy(build):
    source, project = build
    (project / "existing.py").unlink()
    review = make_review(project)
    receipt = apply_review(review)
    assert not (source / "existing.py").exists()
    assert (receipt / "files/existing.py").read_text() == "value = 1\n"


def test_symlink_destination_never_overwrites_external_file(build, tmp_path):
    source, project = build
    outside = tmp_path / "outside"
    outside.write_text("value = 1\n")
    (source / "existing.py").unlink()
    (source / "existing.py").symlink_to(outside)
    with pytest.raises(ValueError):
        apply_review(make_review(project))
    assert outside.read_text() == "value = 1\n"


def test_secret_path_never_applied(build):
    source, project = build
    (project / ".env").write_text("SECRET=value")
    with pytest.raises(ValueError, match="Protected path"):
        apply_review(make_review(project))
    assert not (source / ".env").exists()


def test_apply_interrupted_midway_rolls_back_owned_writes(build):
    source, project = build
    count = 0

    def guard():
        nonlocal count
        count += 1
        if count == 3:
            raise PermissionError("cancelled")

    with pytest.raises(PermissionError):
        apply_review(make_review(project), guard=guard)
    assert (source / "existing.py").read_text() == "value = 1\n"
    assert not (source / "new.py").exists()


def test_iterations_deliver_cumulative_changes_to_original(build, tmp_path):
    source, project = build
    next_project = prepare(project, tmp_path / "builds")
    (next_project / "third.py").write_text("third = 3")
    review = make_review(next_project)
    assert review.source == source
    assert {c.path for c in review.changes} == {"existing.py", "new.py", "third.py"}
    apply_review(review)
    assert (source / "third.py").exists()


class FakeGitHub:
    def __init__(self, review):
        self.calls = []
        self.head = "base-sha"
        self.private = True
        self.pr_fails = False
        self.tree = []
        for change in review.changes:
            if change.before:
                data = change.before.data
                sha = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
                self.tree.append(
                    {"path": change.path, "type": "blob", "sha": sha, "mode": "100644"}
                )

    def connection(self, repo):
        return {"repository": repo, "branch": "main", "private": self.private}

    def api(self, method, path, payload=None):
        self.calls.append((method, path, payload))
        if method == "GET":
            if "/git/ref/" in path:
                return {"object": {"sha": self.head}}
            if "/git/commits/" in path:
                return {"tree": {"sha": "tree"}}
            if "/git/trees/" in path:
                return {"tree": self.tree, "truncated": False}
        if path.endswith("/pulls"):
            if self.pr_fails:
                raise ValueError("temporary failure")
            return {"html_url": "https://github.com/team/project/pull/1"}
        return {"sha": "created"}


def test_github_scope_exact_patch_new_branch_and_draft_pr(build):
    _, project = build
    review = make_review(project)
    client = FakeGitHub(review)
    approval = prepare_publication(client, "team/project", review, "Feature")
    assert all(method == "GET" for method, _, _ in client.calls)
    result = publish(client, approval, review, authorized=True)
    assert result["url"].endswith("/pull/1")
    blobs = [data for _, path, data in client.calls if path.endswith("/blobs")]
    assert {base64.b64decode(b["content"]) for b in blobs} == {c.after.data for c in review.changes}
    ref = next(data for _, path, data in client.calls if path.endswith("/refs"))
    assert ref["ref"] == "refs/heads/" + approval.branch
    assert not any(method in ("PATCH", "DELETE") for method, _, _ in client.calls)
    pr = next(data for _, path, data in client.calls if path.endswith("/pulls"))
    assert pr["draft"] is True and pr["base"] == "main"
    assert "workspace-context" not in str(client.calls)


@pytest.mark.parametrize("failure", ["unapproved", "expired", "head", "visibility", "artifact"])
def test_publication_rejects_changed_or_unapproved_scope(build, failure):
    _, project = build
    review = make_review(project)
    client = FakeGitHub(review)
    approval = prepare_publication(client, "team/project", review, "Feature")
    if failure == "expired":
        approval = replace(approval, expires=0)
    if failure == "head":
        client.head = "new-head"
    if failure == "visibility":
        client.private = False
    if failure == "artifact":
        (project / "new.py").write_text("changed")
    with pytest.raises((ValueError, PermissionError)):
        publish(client, approval, review, authorized=failure != "unapproved")
    assert all(method == "GET" for method, _, _ in client.calls)


def test_pr_failure_reports_existing_branch_without_claiming_pr(build):
    _, project = build
    review = make_review(project)
    client = FakeGitHub(review)
    approval = prepare_publication(client, "team/project", review, "Feature")
    client.pr_fails = True
    result = publish(client, approval, review, authorized=True)
    assert "/tree/aedrova/" in result["url"]
    assert "do not repeat" in result["message"]


def test_remote_conflicts_fail_before_upload(build):
    _, project = build
    review = make_review(project)
    client = FakeGitHub(review)
    client.tree[0]["sha"] = "someone-elses-work"
    with pytest.raises(ValueError, match="differs"):
        prepare_publication(client, "team/project", review, "Feature")
    assert all(method == "GET" for method, _, _ in client.calls)


@pytest.mark.parametrize(
    "repo",
    [
        "https://evil.test/team/project",
        "../repo",
        "owner/repo?token=x",
        "git@github.com:owner/repo",
    ],
)
def test_repository_input_is_strict(repo):
    with pytest.raises(ValueError):
        repository_name(repo)


def test_local_preview_serves_only_static_snapshot(tmp_path):
    (tmp_path / "index.html").write_text("<h1>Preview</h1>")
    (tmp_path / ".env").write_text("secret")
    (tmp_path / "server.py").write_text("private server code")
    preview = StaticPreview(tmp_path)
    try:
        with urlopen(preview.url) as response:
            assert b"Preview" in response.read()
            assert "connect-src 'none'" in response.headers["Content-Security-Policy"]
        for path in (".env", "server.py", "%2e%2e/.env"):
            with pytest.raises(HTTPError):
                urlopen(preview.url + path)
        assert preview.server.server_address[0] == "127.0.0.1"
    finally:
        preview.close()
    assert not preview.temp.exists()


def test_apply_preserves_restrictive_file_permissions(build):
    source, project = build
    (source / "existing.py").chmod(0o600)
    receipt = apply_review(make_review(project))
    assert (source / "existing.py").stat().st_mode & 0o777 == 0o600
    assert (receipt / "files/existing.py").stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize("kind", ["credential", "workflow"])
def test_publishing_rejects_protected_content_before_network(build, kind):
    _, project = build
    if kind == "credential":
        (project / "new.py").write_text("key = 'sk-proj-" + "x" * 30 + "'")
    else:
        folder = project / ".github/workflows"
        folder.mkdir(parents=True)
        (folder / "run.yml").write_text("on: push")
    review = make_review(project)
    client = FakeGitHub(review)
    with pytest.raises(ValueError):
        prepare_publication(client, "team/project", review, "Feature")
    assert not client.calls


def test_cancelled_publication_uploads_nothing(build):
    _, project = build
    review = make_review(project)
    client = FakeGitHub(review)
    approval = prepare_publication(client, "team/project", review, "Feature")

    def cancel():
        raise PermissionError("cancelled")

    with pytest.raises(PermissionError):
        publish(client, approval, review, authorized=True, guard=cancel)
    assert all(method == "GET" for method, _, _ in client.calls)


def test_selected_project_under_ignored_parent_is_not_silently_empty(tmp_path):
    from aedrova.agents.checkout import git

    git(tmp_path, "init", "-q")
    (tmp_path / ".gitignore").write_text("work/\n")
    source = tmp_path / "work/independent-project"
    source.mkdir(parents=True)
    (source / "app.py").write_text("original = True")
    project = prepare(source, tmp_path / "copies")
    assert (project / "app.py").read_text() == "original = True"
    assert not make_review(project).changes


def test_cancellation_after_last_blob_stops_before_commit(build):
    _, project = build
    review = make_review(project)
    client = FakeGitHub(review)
    approval = prepare_publication(client, "team/project", review, "Feature")

    def guard():
        uploads = sum(path.endswith("/blobs") for _, path, _ in client.calls)
        if uploads == len(review.changes):
            raise PermissionError("cancelled after upload")

    with pytest.raises(PermissionError):
        publish(client, approval, review, authorized=True, guard=guard)
    assert not any(
        method == "POST" and path.endswith(("/trees", "/commits", "/refs", "/pulls"))
        for method, path, _ in client.calls
    )
