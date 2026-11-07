"""Channel-scoped collaboration evidence, never a grant or verified achievement."""

import json


def record(row, workspace, channels):
    sources = set(row.get("source_channels", []))
    if (
        row.get("workspace_id") != workspace
        or row.get("channel_id") not in channels
        or not sources
        or row["channel_id"] not in sources
        or not sources <= channels
    ):
        raise PermissionError("Shared agent work is outside this context scope.")
    return {"shared_agent_work": row}


def recheck(service, context):
    used = [
        json.loads(line)["shared_agent_work"]
        for line in context.text.splitlines()
        if line and "shared_agent_work" in json.loads(line)
    ]
    builds = [
        json.loads(line)["shared_build_review"]
        for line in context.text.splitlines()
        if line and "shared_build_review" in json.loads(line)
    ]
    if builds:
        fresh_builds = {r["id"]: r for r in service.build_reviews(context.workspace_id)["items"]}
        if any(fresh_builds.get(r["id"]) != r for r in builds):
            raise PermissionError("Shared build review or source access changed. Please retry.")
    if not used:
        return
    fresh = service.shared_agent_work(context.workspace_id, identifiers=[r["id"] for r in used])
    rows = {r["id"]: r for r in fresh["items"]}
    if fresh.get("setup_required") or any(rows.get(r["id"]) != r for r in used):
        raise PermissionError("Shared agent work or its source access changed. Please retry.")


def build_record(row, workspace, channels):
    record(row, workspace, channels)
    return {"shared_build_review": row}
