"""Parse an official Slack public-channel JSON ZIP without extracting files."""

import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit
from zipfile import BadZipFile, ZipFile

MAX_ZIP = 32 * 1024 * 1024
MAX_EXPANDED = 128 * 1024 * 1024
MAX_ROWS = 50_000
SLACK_ID = re.compile(r"C[A-Z0-9]{1,39}")
TIMESTAMP = re.compile(r"[0-9]{1,10}\.[0-9]{6}")
DAILY = re.compile(r"\d{4}-\d{2}-\d{2}\.json")
RESTRICTED = (
    "is_private",
    "is_shared",
    "is_ext_shared",
    "is_org_shared",
    "is_pending_ext_shared",
    "is_group",
    "is_im",
    "is_mpim",
    "is_frozen",
    "pending_shared",
)


def clean(value, limit):
    return (
        value.replace("\0", "").encode("utf-8", "replace").decode()[:limit]
        if isinstance(value, str)
        else ""
    )


def file_links(message):
    links = []
    files = message.get("files")
    for item in (files if isinstance(files, list) else [])[:8]:
        if not isinstance(item, dict):
            continue
        url = clean(item.get("permalink"), 1000)
        try:
            parsed = urlsplit(url)
            if (
                parsed.scheme == "https"
                and parsed.hostname
                and (parsed.hostname == "slack.com" or parsed.hostname.endswith(".slack.com"))
                and not parsed.username
                and not parsed.password
                and all(ord(character) > 32 for character in url)
            ):
                links.append(url)
        except ValueError:
            continue
    return links


def preview(path):
    """Return channel counts and normalized records held locally until confirmation."""
    path = Path(path)
    if not path.is_file():
        raise ValueError("Choose a Slack export ZIP file.")
    if path.stat().st_size > MAX_ZIP:
        raise ValueError("Choose a Slack export ZIP smaller than 32 MB.")
    try:
        with ZipFile(path) as archive:
            return read_archive(archive)
    except (
        BadZipFile,
        ValueError,
        TypeError,
        UnicodeError,
        RecursionError,
        OverflowError,
        NotImplementedError,
        RuntimeError,
    ) as exc:
        if isinstance(exc, ValueError) and str(exc).startswith(("Choose ", "This ", "Slack ")):
            raise
        raise ValueError("Choose a valid Slack public-channel JSON export ZIP.") from exc


def read_archive(archive):
    infos = archive.infolist()
    if (
        len(infos) > 20_000
        or sum(i.file_size for i in infos) > MAX_EXPANDED
        or any(i.file_size > 8 * 1024 * 1024 or i.flag_bits & 1 for i in infos)
    ):
        raise ValueError(
            "This Slack export exceeds the import limits. Export a shorter date range."
        )
    names = {}
    for info in infos:
        name = info.filename.rstrip("/")
        parts = name.split("/")
        if (
            any(part in ("", ".", "..") or ":" in part for part in parts)
            or "\\" in name
            or name in names
            or len(parts) > 3
        ):
            raise ValueError("This ZIP contains an invalid or duplicate entry.")
        names[name] = info
    manifests = [name for name in names if name.split("/")[-1] == "channels.json"]
    if len(manifests) != 1 or manifests[0].count("/") > 1:
        raise ValueError("Choose a Slack JSON export with a public-channel manifest.")
    prefix = manifests[0].removesuffix("channels.json")

    def read(info):
        with archive.open(info) as stream:
            content = stream.read(info.file_size + 1)
        value = json.loads(content)
        if not isinstance(value, list):
            raise ValueError("This Slack export has invalid JSON records.")
        return value

    restricted_names = set()
    for manifest in ("groups.json", "dms.json", "mpims.json"):
        if prefix + manifest in names:
            for item in read(names[prefix + manifest]):
                if isinstance(item, dict):
                    restricted_names.update(
                        (clean(item.get("id"), 40), clean(item.get("name"), 80))
                    )

    channels = {}
    for channel in read(names[manifests[0]]):
        if not isinstance(channel, dict):
            continue
        name, channel_id = clean(channel.get("name"), 80), clean(channel.get("id"), 40)
        if (
            not re.fullmatch(r"[\w-]{1,80}", name)
            or not SLACK_ID.fullmatch(channel_id)
            or any(channel.get(field) for field in RESTRICTED)
            or len(channel.get("shared_team_ids") or []) > 1
            or name in restricted_names
            or channel_id in restricted_names
        ):
            continue
        if name in channels or channel_id in channels.values():
            raise ValueError("This Slack export has duplicate channel metadata.")
        channels[name] = channel_id

    authors = {}
    if prefix + "users.json" in names:
        for user in read(names[prefix + "users.json"]):
            if isinstance(user, dict) and isinstance(user.get("id"), str):
                authors[user["id"]] = clean(user.get("real_name") or user.get("name"), 160)

    records = {}
    skipped = 0
    for name, info in sorted(names.items()):
        if not name.startswith(prefix) or info.is_dir():
            continue
        parts = name[len(prefix) :].split("/")
        if len(parts) != 2 or not DAILY.fullmatch(parts[1]):
            continue
        channel = parts[0]
        if channel not in channels:
            skipped += 1
            continue
        channel_id = channels[channel]
        for message in read(info):
            if not isinstance(message, dict) or message.get("type") != "message":
                continue
            ts = clean(message.get("ts"), 24)
            if not TIMESTAMP.fullmatch(ts):
                continue
            if message.get("subtype") in {
                "message_changed",
                "message_deleted",
                "tombstone",
                "channel_join",
                "channel_leave",
            } or message.get("hidden"):
                continue
            body = clean(message.get("text"), 8000)
            links = file_links(message)
            if not body.strip() and not links:
                continue
            parent = clean(message.get("thread_ts"), 24)
            sender = clean(
                message.get("user") or message.get("username") or message.get("bot_id"), 160
            )
            raw_reactions = message.get("reactions")
            reactions = {}
            for reaction in (raw_reactions if isinstance(raw_reactions, list) else [])[:24]:
                if not isinstance(reaction, dict):
                    continue
                key, count = clean(reaction.get("name"), 80), reaction.get("count")
                if key and type(count) is int and 0 <= count <= 100_000:
                    reactions[key] = count
            records[channel_id, ts] = {
                "channel_id": channel_id,
                "channel_name": channel,
                "source_ts": ts,
                "thread_ts": parent if parent != ts and TIMESTAMP.fullmatch(parent) else None,
                "author": authors.get(sender) or sender or "Unknown author",
                "body": body,
                "links": links,
                "reactions": reactions,
            }
            if len(records) > MAX_ROWS:
                raise ValueError(
                    "This Slack export has over 50,000 messages. Export a shorter date range."
                )
    counts = Counter(row["channel_name"] for row in records.values())
    return list(records.values()), counts, skipped


def upload(service, workspace, rows, cancelled=lambda: False, progress=lambda sent, total: None):
    """Retrying the same selected export resumes its unpublished import.

    `progress(sent, total)` reports whole batches, so a screen can show how far along it is.
    """
    from hashlib import sha256
    from uuid import NAMESPACE_URL, uuid5

    encoded = [
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        for row in sorted(rows, key=lambda row: (row["channel_id"], row["source_ts"]))
    ]
    digest = sha256()
    for row in encoded:
        digest.update(row + b"\n")
    identifier = str(uuid5(NAMESPACE_URL, f"aedrova:slack:{workspace}:{digest.hexdigest()}"))
    parameters = {"p_workspace": workspace, "p_import": identifier}
    user = str(service.user.id)

    batches, batch, size = [], [], 0
    for row in encoded:
        if len(batch) == 200 or size + len(row) > 240_000:
            batches.append(batch)
            batch, size = [], 0
        batch.append(json.loads(row))
        size += len(row)
    batches.append(batch)

    imports = service.rpc("list_slack_imports", {"p_workspace": workspace})
    previous = next((item for item in imports if item["id"] == identifier), {})
    if previous.get("published_at"):
        progress(len(batches), len(batches))
        return previous["message_count"]
    checkpoint = previous.get("next_batch", 0)

    def send(sequence, rows, finish=False):
        if cancelled():
            raise InterruptedError("Import stopped. Choose the same ZIP to resume.")
        if not service.user or str(service.user.id) != user:
            raise PermissionError("The signed-in account changed. Reopen the importer to continue.")
        return service.rpc(
            "write_slack_history",
            {
                **parameters,
                "p_batch": sequence,
                "p_rows": rows,
                "p_finish": finish,
            },
        )

    progress(min(checkpoint, len(batches) - 1), len(batches))
    result = 0
    for sequence, rows_in_batch in enumerate(batches):
        last = sequence == len(batches) - 1
        if sequence >= checkpoint or last:
            result = send(sequence, rows_in_batch, finish=last)
        progress(sequence + 1, len(batches))
    return result
