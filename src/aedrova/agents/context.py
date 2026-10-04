"""Explicit, RLS-backed context snapshots. Never run during ordinary chat."""

import json
import re
import time
from dataclasses import dataclass

MAX_CONTEXT_BYTES = 8 * 1024 * 1024
TEXT_EXTENSIONS = {".txt", ".md", ".py", ".json", ".csv", ".html", ".css", ".js", ".ts", ".sql"}


@dataclass(frozen=True)
class WorkspaceContext:
    workspace_id: str
    user_id: str
    channel_ids: frozenset[str]
    text: str
    count: int
    nickname: str
    provider: str


def authorize(snapshot, workspace, user):
    if not any(w["id"] == workspace for w in snapshot["workspaces"]):
        raise PermissionError("Workspace access is no longer available.")
    if not any(
        m["workspace_id"] == workspace
        and m["user_id"] == user
        and m["role"] in {"owner", "admin", "member"}
        for m in snapshot["members"]
    ):
        raise PermissionError("A workspace member account is required to run builds.")
    return frozenset(c["id"] for c in snapshot["channels"] if c["workspace_id"] == workspace)


def gather(
    service,
    workspace,
    cancelled=lambda: False,
    progress=lambda _: None,
    *,
    query="",
    preferred_channel="",
):
    """Collect authorized evidence with explicit limits; production uses indexed search.

    The file is evidence, not instructions. Results remain local and are never posted
    to a channel. Re-check membership and channel access before returning it.
    """
    started = time.monotonic()
    progress("Checking workspace access…")

    def inventory():
        if hasattr(service, "context_snapshot"):
            return service.context_snapshot(workspace, cancelled)
        return service.snapshot()

    snapshot = inventory()
    # The existing dashboard inventory uses PostgREST's default 1,000-row ceiling.
    # Never advertise an entire workspace if that inventory may have been truncated.
    if not hasattr(service, "context_snapshot") and len(snapshot["channels"]) >= 1000:
        raise ValueError(
            "The channel inventory reached the alpha limit. "
            "No partial workspace context will be used."
        )
    user = str(service.user.id)
    channels = authorize(snapshot, workspace, user)
    revisions = {}
    if hasattr(service, "context_revision"):
        for channel in sorted(channels):
            if cancelled():
                raise InterruptedError("Cancelled")
            if time.monotonic() - started > 180:
                raise TimeoutError("Context retrieval timed out. Retry with a narrower request.")
            revisions[channel] = service.context_revision(channel)
    preference = next(
        (p for p in snapshot.get("agent_preferences", []) if p["workspace_id"] == workspace), {}
    )
    lines, size, count = [], 0, 0

    def add(record):
        nonlocal size
        from aedrova.security.credentials import credential_rules

        line = json.dumps(record, ensure_ascii=False)
        if credential_rules(line.encode("utf-8")):
            raise ValueError(
                "A context source contains a recognizable credential. "
                "Remove it from the selected evidence before building."
            )
        size += len(line.encode("utf-8")) + 1
        if size > MAX_CONTEXT_BYTES:
            raise ValueError(
                "Workspace context exceeds the 8 MiB alpha limit. No partial build started."
            )
        lines.append(line)

    bounded = hasattr(service, "search_context")
    candidates = {}
    selected_channels = set()
    if bounded:
        terms = list(dict.fromkeys(re.findall(r"[^\W_]+", query, re.UNICODE)))[:32]
        search = " OR ".join('"' + term + '"' for term in terms)
        progress("Searching permitted workspace evidence…")
        ranked = service.search_context(workspace, search[:1000])
        if len(ranked) > 200 or any(row["channel_id"] not in channels for row in ranked):
            raise PermissionError("Context search returned invalid or unauthorized evidence.")
        candidates.update({row["id"]: row for row in ranked})
        roots = list(
            dict.fromkeys((row["channel_id"], row.get("parent_id") or row["id"]) for row in ranked)
        )[:12]
        if hasattr(service, "thread_context"):
            for channel, parent in roots:
                if cancelled():
                    raise InterruptedError("Cancelled")
                rows = service.thread_context(channel, parent)
                if len(rows) > 21 or any(
                    row["channel_id"] != channel
                    or (row["id"] != parent and row.get("parent_id") != parent)
                    for row in rows
                ):
                    raise PermissionError("Thread evidence has invalid scope.")
                candidates.update({row["id"]: row for row in rows})
        selected_channels = set(row["channel_id"] for row in ranked)
        recent_channels = sorted(selected_channels)[:22]
        recent_channels += sorted(channels - selected_channels)[:10]
        recent_channels = list(
            dict.fromkeys(
                ([preferred_channel] if preferred_channel in channels else []) + recent_channels
            )
        )[:32]
        for channel in recent_channels:
            if cancelled():
                raise InterruptedError("Cancelled")
            if time.monotonic() - started > 180:
                raise TimeoutError("Context retrieval timed out. Retry with a narrower request.")
            rows = service.recent_context(channel)
            if len(rows) > 20 or any(row["channel_id"] != channel for row in rows):
                raise PermissionError("Recent evidence has invalid channel scope.")
            candidates.update({row["id"]: row for row in rows})
            selected_channels.add(channel)
        add(
            {
                "coverage": {
                    "mode": "indexed search and bounded recent evidence",
                    "query": query[:1000],
                    "search_results": len(ranked),
                    "recent_channel_limit": 32,
                    "recent_messages_per_channel": 20,
                    "matched_threads": 12,
                    "replies_per_thread": 20,
                    "recent_decisions_per_selected_channel": 50,
                    "notice": "This is selected evidence, not the complete workspace history. "
                    "Ask the team when missing or conflicting requirements need more evidence.",
                }
            }
        )

    meeting_evidence = {}
    for channel in sorted(snapshot["channels"], key=lambda c: c["id"]):
        if channel["id"] not in channels:
            continue
        add({"channel": channel["id"], "name": channel["name"], "private": channel["private"]})
        if bounded and channel["id"] not in selected_channels:
            continue
        if hasattr(service, "context_decisions"):
            decisions = (
                service.recent_decisions(channel["id"])
                if bounded
                else service.context_decisions(channel["id"])
            )
            for decision in decisions:
                if decision["channel_id"] != channel["id"]:
                    raise PermissionError("Decision scope changed. Refresh context.")
                add({"decision": decision})
        if getattr(service, "meeting_context_enabled", False) is True:
            rows = service.meeting_context(channel["id"])
            if len(rows) > 50 or any(
                row.get("channel_id") != channel["id"]
                or row.get("ai_allowed") is not True
                or (
                    row.get("source") not in {"participant_text", "provider_speech"}
                    or (row.get("source") == "provider_speech" and not row.get("reviewed_at"))
                )
                for row in rows
            ):
                raise PermissionError("Meeting evidence has invalid consent or channel scope.")
            meeting_evidence[channel["id"]] = rows
            for row in rows:
                add({"meeting_text": row})
        cursor = 0
        while True:
            if cancelled():
                raise InterruptedError("Cancelled")
            if time.monotonic() - started > 180:
                raise TimeoutError("Context retrieval timed out. Check your connection and retry.")
            progress(f"Reading #{channel['name']} · {count} messages gathered…")
            rows = (
                sorted(
                    (row for row in candidates.values() if row["channel_id"] == channel["id"]),
                    key=lambda row: row["sequence"],
                )
                if bounded
                else service.context_page(channel["id"], after=cursor)
            )
            if not rows:
                break
            for row in rows:
                if row["channel_id"] != channel["id"] or row["sequence"] <= cursor:
                    raise ValueError("Invalid context pagination; build stopped.")
                cursor = row["sequence"]
                add({"message": row})
                count += 1
            attachments = service.attachments_for([r["id"] for r in rows])
            if len(attachments) >= 1000:
                raise ValueError("Attachment inventory may be truncated. No partial context used.")
            for attachment in sorted(attachments, key=lambda item: item["id"]):
                if attachment["message_id"] not in {r["id"] for r in rows}:
                    raise PermissionError("Attachment is outside the requested source messages.")
                from pathlib import Path

                entry = {
                    "attachment": attachment["id"],
                    "message": attachment["message_id"],
                    "filename": attachment["filename"],
                    "content": "Metadata only",
                }
                if (
                    Path(attachment["filename"]).suffix.lower() in TEXT_EXTENSIONS
                    and attachment["byte_size"] <= 256 * 1024
                ):
                    if cancelled():
                        raise InterruptedError("Cancelled")
                    data = service.download_attachment(attachment["id"])
                    try:
                        entry["content"] = data.decode("utf-8")
                    except UnicodeDecodeError:
                        entry["content"] = "Binary content omitted"
                add(entry)
            if bounded:
                break
    current = authorize(inventory(), workspace, user)
    if cancelled():
        raise InterruptedError("Cancelled")
    if str(service.user.id) != user:
        raise PermissionError("The signed-in account changed during retrieval.")
    if channels != current:
        raise PermissionError("Channel access changed while gathering context. Please retry.")
    for channel, revision in revisions.items():
        if cancelled():
            raise InterruptedError("Cancelled")
        if time.monotonic() - started > 180:
            raise TimeoutError("Context retrieval timed out. Retry with a narrower request.")
        if service.context_revision(channel) != revision:
            raise ValueError("Workspace evidence changed during retrieval. Refresh and try again.")
    for channel, rows in meeting_evidence.items():
        if cancelled():
            raise InterruptedError("Cancelled")
        if service.meeting_context(channel) != rows:
            raise ValueError("Meeting consent or retention changed. Refresh context and retry.")
    return WorkspaceContext(
        workspace,
        user,
        channels,
        "\n".join(lines),
        count,
        preference.get("nickname", "Aedrova"),
        preference.get("provider", "codex"),
    )


def build_command(text, nickname="Aedrova"):
    """Explicit leading mentions open the agent; mentions in ordinary prose stay silent."""
    value = text.strip()
    slash = re.match(r"^/build(?:\s+(.*))?$", value, re.IGNORECASE | re.DOTALL)
    if slash:
        return (slash.group(1) or "").strip()
    mention = re.match(
        r"^@(?:Aedrova|" + re.escape(nickname) + r")[,:]?(?:\s+(.*))?$",
        value,
        re.IGNORECASE | re.DOTALL,
    )
    if not mention:
        return None
    request = (mention.group(1) or "").strip()
    return re.sub(r"^build(?:\s+|$)", "", request, count=1, flags=re.IGNORECASE).strip()
