"""Observed local build evidence; provider prose never establishes a passed check."""

import hashlib
import json
from pathlib import PurePosixPath

from aedrova.security.credentials import credential_rules

MAX_COMMANDS = 100


def project_fingerprint(project):
    from aedrova.delivery.files import inventory

    values = inventory(project)
    return hashlib.sha256(
        json.dumps(sorted((name, version.digest) for name, version in values.items())).encode()
    ).hexdigest()


def command_result(command, output, exit_code):
    """Normalize a completed CLI/tool event. Unknown exits remain unverified."""
    command, output = str(command)[:2000], str(output)
    code = exit_code if type(exit_code) is int else None
    if credential_rules((command + output).encode()):
        command, output = "Command withheld: credential detected", "Output withheld"
    digest = hashlib.sha256(output.encode()).hexdigest()
    return {
        "id": hashlib.sha256((command + digest + str(code)).encode()).hexdigest(),
        "command": command,
        "output": output[-8000:],
        "output_digest": digest,
        "exit_code": code,
        "state": "passed" if code == 0 else "failed" if code is not None else "unverified",
        "origin": "local_provider_tool_event",
        "truncated": len(output) > 8000,
    }


def requirement_snapshot(context):
    record = next(
        (
            json.loads(line)["product_memory_snapshot"]
            for line in getattr(context, "text", "").splitlines()
            if "product_memory_snapshot" in json.loads(line)
        ),
        {},
    )
    return record


def manifest(context, task, provider, review, commands):
    memory = requirement_snapshot(context)
    requirements = []
    for row in memory.get("items", []):
        if row["state"] == "approved" and row["fresh"]:
            requirements.append(
                {
                    "id": row["id"],
                    "version": row["version"],
                    "kind": row["kind"],
                    "title": row["title"],
                    "body": row["body"],
                    "sources": row["sources"],
                    "channel_id": row["channel_id"],
                    "assessment": "not_assessed",
                    "files": [],
                    "checks": [],
                }
            )
    files, budget = [], 60000
    if len(review.changes) > 200:
        raise ValueError("More than 200 changed files. Narrow this build before sharing evidence.")
    for change in review.changes:
        diff = change.diff()
        if credential_rules(diff.encode()):
            raise ValueError("A diff contains a recognizable credential. Remove it before sharing.")
        excerpt = diff[: max(0, min(budget, 10000))]
        budget -= len(excerpt)
        files.append(
            {
                "path": change.path,
                "before": change.before.digest if change.before else None,
                "after": change.after.digest if change.after else None,
                "diff": excerpt,
                "truncated": len(excerpt) < len(diff),
            }
        )
    value = {
        "task": task[:20000],
        "provider": provider,
        "memory_revision": memory.get("revision", ""),
        "requirements": requirements,
        "files": files,
        "checks": list({c["id"]: c for c in commands[:MAX_COMMANDS]}.values()),
        "checks_truncated": len(commands) > MAX_COMMANDS,
        "project_fingerprint": project_fingerprint(review.project),
        "review_digest": review.digest,
        "acceptance_criteria": [],
        "notice": "Observed local evidence. Requirement assessments are human review claims; "
        "command success alone does not prove a requirement is complete.",
    }
    validate(value)
    return value


def validate(value):
    encoded = json.dumps(value, ensure_ascii=False)
    if len(encoded.encode()) > 250000:
        raise ValueError("Build evidence exceeds the sharing limit. Narrow the build.")
    if credential_rules(encoded.encode()):
        raise ValueError("Evidence contains a recognizable credential. Remove it before sharing.")
    if not value.get("task", "").strip() or len(value.get("files", [])) > 200:
        raise ValueError("A build request and bounded file evidence are required.")
    files = {item["path"] for item in value["files"]}
    for path in files:
        parsed = PurePosixPath(path)
        if parsed.is_absolute() or ".." in parsed.parts or "\\" in path:
            raise ValueError("Evidence paths must stay within the build project.")
    if len(files) != len(value["files"]):
        raise ValueError("Changed file paths must be unique.")
    criteria = value.get("acceptance_criteria", [])
    if len(criteria) > 50 or any(
        not isinstance(c, str) or not 1 <= len(c) <= 2000 for c in criteria
    ):
        raise ValueError("Use up to 50 concise acceptance criteria, each under 2,000 characters.")
    checks = {item["id"]: item for item in value["checks"]}
    if len(checks) != len(value["checks"]) or len(checks) > MAX_COMMANDS:
        raise ValueError("Observed check identifiers must be unique and bounded.")
    for check in checks.values():
        code = check.get("exit_code")
        state = (
            "passed"
            if type(code) is int and code == 0
            else "failed"
            if type(code) is int
            else "unverified"
        )
        if check["state"] != state:
            raise ValueError("Check state must match an observed integer exit code.")
    for row in value["requirements"]:
        if not set(row["files"]) <= files or not set(row["checks"]) <= checks.keys():
            raise ValueError("Requirement links must refer to actual file and command evidence.")
        if row["assessment"] not in {"not_assessed", "needs_work", "reviewer_verified"}:
            raise ValueError("Unknown requirement assessment.")
        if row["assessment"] == "reviewer_verified" and (
            not row["files"]
            or not row["checks"]
            or any(
                checks[key]["state"] != "passed"
                or checks[key].get("project_fingerprint") != value["project_fingerprint"]
                for key in row["checks"]
            )
        ):
            raise ValueError(
                "Verified requirements need changed files and passed checks for the current files."
            )
    return value
