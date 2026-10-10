"""Validated memory snapshots and reproducible build provenance."""

import hashlib
import json

KINDS = ("goal", "requirement", "constraint", "decision", "question")
STATES = ("proposal", "approved", "conflict", "retired", "superseded")


def snapshot_record(payload, workspace, channels):
    items = payload.get("items", [])
    if len(items) > 200:
        raise ValueError("Memory inventory exceeded its limit. Narrow the search.")
    seen = set()
    for item in items:
        if (
            item["workspace_id"] != workspace
            or item["channel_id"] not in channels
            or item["id"] in seen
        ):
            raise PermissionError("Product memory returned invalid scope.")
        seen.add(item["id"])
        if item["kind"] not in KINDS or item["state"] not in STATES:
            raise ValueError("Invalid product memory state.")
        sources = item.get("resolved_sources", [])
        if not sources or any(s["channel_id"] != item["channel_id"] for s in sources):
            raise PermissionError("Product memory citation is outside its scope.")
    ordered = sorted(items, key=lambda item: item["id"])
    digest = hashlib.sha256(json.dumps(ordered, sort_keys=True).encode()).hexdigest()
    return {
        "product_memory_snapshot": {
            "revision": digest,
            "items": ordered,
            "total": payload.get("total", len(items)),
            "truncated": payload.get("truncated", False),
            "setup_required": payload.get("setup_required", False),
            "notice": "Only approved, fresh entries are current requirements. "
            "Proposals, questions and conflicts need human review. "
            "This snapshot pins selected knowledge, not unanimous team agreement.",
        }
    }
