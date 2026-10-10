"""Ephemeral full-text index of an already-authorized, freshly collected corpus.

No shared disk cache, credentials, embeddings service, or inferred team decisions.
"""

import hashlib
import json
import re
import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    citation: str
    message_id: str
    channel: str
    body: str
    parent_id: str | None
    created_at: str
    decision: str
    confirmed_by: str
    fingerprint: str
    attachment: str = ""
    meeting: str = ""
    speaker: str = ""
    offset_ms: int = 0
    memory_id: str = ""

    def record(self):
        return vars(self)


class ContextIndex:
    def __init__(self, context):
        self.connection = sqlite3.connect(":memory:")
        self.connection.execute(
            "CREATE VIRTUAL TABLE evidence USING fts5(body, channel, tokenize='porter unicode61')"
        )
        self.sources = []
        records = [json.loads(line) for line in context.text.splitlines() if line]
        channels = {r["channel"]: r["name"] for r in records if "channel" in r}
        messages = {
            r["message"]["id"]: r["message"] for r in records if isinstance(r.get("message"), dict)
        }
        decisions = {r["decision"]["message_id"]: r["decision"] for r in records if "decision" in r}
        self.memory_snapshot = next(
            (r["product_memory_snapshot"] for r in records if "product_memory_snapshot" in r), {}
        )
        for record in records:
            if "connector_source" not in record:
                continue
            from aedrova.connectors.service import resource_id

            kind, resource = record["connector_source"], record["resource"]
            resource_id(kind, resource)
            citation = "connector:" + kind + ":" + resource
            if record.get("citation") != citation:
                raise PermissionError("Invalid connector evidence citation.")
            body = record["coverage"] + "\n" + json.dumps(record["untrusted_evidence"])
            self._add(
                Source(
                    citation,
                    citation,
                    "Connected " + kind,
                    body,
                    None,
                    "",
                    "external_untrusted",
                    "",
                    hashlib.sha256(body.encode()).hexdigest(),
                )
            )
        for record in records:
            dot = record.get("dot_evidence")
            if dot is None:
                continue
            from uuid import UUID

            if (
                dot.get("untrusted") is not True
                or dot.get("citation") != "dot:" + str(UUID(dot["dot"])) + ":" + dot["tool"]
            ):
                raise PermissionError("Invalid Dot evidence citation.")
            body = dot["coverage"] + "\n" + json.dumps(dot["records"])
            self._add(
                Source(
                    dot["citation"],
                    dot["citation"],
                    "Dot " + dot["name"],
                    body,
                    None,
                    "",
                    "external_untrusted",
                    "",
                    hashlib.sha256(body.encode()).hexdigest(),
                )
            )
        for item in self.memory_snapshot.get("items", []):
            if item["channel_id"] not in context.channel_ids:
                raise PermissionError("Memory is outside this context scope.")
            state = item["state"] if item["fresh"] else "stale"
            self._add(
                Source(
                    "memory:" + item["id"],
                    item["id"],
                    channels.get(item["channel_id"], "channel"),
                    item["title"] + "\n" + item["body"],
                    None,
                    item["updated_at"],
                    "memory_" + state,
                    item["updated_by"],
                    str(item["version"]),
                    memory_id=item["id"],
                )
            )
        for identifier, message in messages.items():
            if message["channel_id"] not in context.channel_ids:
                raise PermissionError("Evidence contains a channel outside this snapshot.")
            body = message["body"]
            decision = decisions.get(identifier, {})
            state = "discussion"
            if decision:
                state = (
                    "retired"
                    if not decision["confirmed"]
                    else ("confirmed" if decision["source_body"] == body else "stale")
                )
            self._add(
                Source(
                    f"message:{identifier}",
                    identifier,
                    channels.get(message["channel_id"], "channel"),
                    body,
                    message.get("parent_id"),
                    message.get("created_at", ""),
                    state,
                    decision.get("confirmed_by", ""),
                    hashlib.sha256(body.encode()).hexdigest(),
                )
            )
        for record in records:
            meeting = record.get("meeting_text")
            if meeting is None:
                continue
            if (
                meeting.get("channel_id") not in context.channel_ids
                or meeting.get("ai_allowed") is not True
                or meeting.get("source") not in {"participant_text", "provider_speech"}
                or (meeting.get("source") == "provider_speech" and not meeting.get("reviewed_at"))
            ):
                raise PermissionError("Meeting text lacks authorized scope and consent.")
            self._add(
                Source(
                    "meeting:" + meeting["id"],
                    "meeting:" + meeting["id"],
                    channels.get(meeting["channel_id"], "channel"),
                    meeting["body"],
                    None,
                    meeting["created_at"],
                    (
                        "confirmed_meeting_decision"
                        if meeting.get("confirmed_decision")
                        else "reviewed_speech"
                        if meeting["source"] == "provider_speech"
                        else "participant_text"
                    ),
                    meeting.get("reviewed_by") or "",
                    hashlib.sha256(meeting["body"].encode()).hexdigest(),
                    meeting=meeting["meeting_id"],
                    speaker=meeting["speaker_id"],
                    offset_ms=meeting["offset_ms"],
                )
            )
        for record in records:
            if "attachment" not in record:
                continue
            message = messages.get(record["message"])
            if message is None:
                raise PermissionError("Attachment has no permitted source message.")
            body = record["content"]
            self._add(
                Source(
                    f"attachment:{record['attachment']}",
                    message["id"],
                    channels.get(message["channel_id"], "channel"),
                    body,
                    message.get("parent_id"),
                    message.get("created_at", ""),
                    "attachment",
                    "",
                    hashlib.sha256(body.encode()).hexdigest(),
                    record["filename"],
                )
            )

    def _add(self, source):
        self.sources.append(source)
        self.connection.execute(
            "INSERT INTO evidence(rowid, body, channel) VALUES (?, ?, ?)",
            (len(self.sources), source.body, source.channel),
        )

    def search(self, query, limit=12):
        reference = query.strip().strip("[]")
        exact = [s for s in self.sources if reference in {s.citation, s.message_id}]
        if exact:
            return exact[:limit]
        # Quote individual terms: punctuation/FTS operators can never become query syntax.
        terms = list(dict.fromkeys(re.findall(r"[^\W_]+", query.lower(), re.UNICODE)))[:64]
        if not terms:
            return self.sources[:limit]
        expression = " OR ".join('"' + term + '"' for term in terms)
        rows = self.connection.execute(
            "SELECT rowid FROM evidence WHERE evidence MATCH ? "
            "ORDER BY bm25(evidence), rowid LIMIT ?",
            (expression, min(max(limit, 1), 200)),
        )
        return [self.sources[row[0] - 1] for row in rows]

    def retrieve(self, query):
        matches = self.search(query)
        selected = {s.citation: s for s in matches}
        # Retain nearby thread evidence, including contradictions rather than picking a winner.
        roots = {s.parent_id or s.message_id for s in matches[:4]}
        related = [s for s in self.sources if (s.parent_id or s.message_id) in roots]
        for source in related[:24]:
            selected[source.citation] = source
        decisions = [s for s in self.sources if s.decision in {"confirmed", "stale", "retired"}]
        return {
            "retrieval": {
                "query": query,
                "method": "FTS5 BM25 with thread expansion",
                "matched": len(matches),
                "total_sources": len(self.sources),
                "sources": [s.record() for s in selected.values()],
                "decision_inventory": [s.record() for s in decisions],
                "product_memory": self.memory_snapshot,
                "notice": "Ranked leads, not exhaustive requirements. Full evidence follows. "
                "Confirmed means a member recorded this message, not unanimous agreement. "
                "Stale/retired decisions are not current. Resolve conflicts with the user.",
            }
        }

    def close(self):
        self.connection.close()


def retrieval_record(context, query):
    index = ContextIndex(context)
    try:
        return json.dumps(index.retrieve(query), ensure_ascii=False)
    finally:
        index.close()


def validate_citations(context, plan):
    """Verify source existence, not whether a model's interpretation is correct."""
    index = ContextIndex(context)
    try:
        available = {s.citation for s in index.sources}
        cited = set(
            re.findall(
                r"(?:message|attachment|meeting|memory):[A-Za-z0-9_-]+"
                r"|connector:(?:github|figma|notion):[A-Za-z0-9_./-]+"
                r"|dot:[a-f0-9-]{36}:[a-z_]+",
                plan,
            )
        )
        unknown = cited - available
        if unknown:
            raise ValueError(
                "Plan contains unknown source citations. Create a fresh plan: "
                + ", ".join(sorted(unknown)[:5])
            )
        if available and not cited:
            raise ValueError(
                "The plan omitted source citations. Create a fresh plan before approval."
            )
        return sorted(cited)
    finally:
        index.close()
