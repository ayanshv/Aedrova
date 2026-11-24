"""One Markdown brief per Bud, filled in from what was chosen during setup."""

import os
import re
import sys
import unicodedata
from pathlib import Path

from aedrova.dots.personality import unpack
from aedrova.dots.roles import NAMES, RESPONSIBILITIES, ROLES, SOURCE_SCOPE, purpose_from, role_for

TEMPLATE = Path(__file__).parents[1] / "desktop/assets/buds/bud-brief.md"
LEVELS = {
    "warmth": ("reserved and professional", "friendly and balanced", "warm and encouraging"),
    "directness": ("gentle and tactful", "clear and balanced", "direct and to the point"),
    "detail": ("brief", "moderate", "thorough"),
    "initiative": (
        "stay narrowly on what was asked",
        "mention an obvious next step",
        "suggest useful next steps",
    ),
    "diligence": (
        "quick first pass",
        "check the main evidence",
        "carefully cross-check the evidence",
    ),
}


def plain(value, limit=600):
    """Setup text goes in as data: no control characters, no template syntax, bounded length."""
    text = unicodedata.normalize("NFKC", str(value or ""))
    text = "".join(
        c if c in "\n " or not unicodedata.category(c).startswith("C") else " " for c in text
    )
    text = text.replace("{{", "{ {").replace("}}", "} }")
    return re.sub(r"[ \t]+", " ", text).strip()[:limit]


def level(name, number):
    low, mid, high = LEVELS[name]
    return low if number < 35 else high if number >= 70 else mid


def sources(bud):
    rows = []
    for connection in bud.get("connections", []) or []:
        if connection.get("status") not in {"Connected", "Error"}:
            continue
        provider = str(connection.get("provider", ""))
        name = NAMES.get(provider, provider.title() or "Source")
        resource = plain(connection.get("resource", ""), 120)
        scope = SOURCE_SCOPE.get(provider, "the resource it was connected to")
        state = "" if connection.get("status") == "Connected" else " (needs attention)"
        where = f" ({resource})" if resource else ""
        rows.append(f"- **{name}**{where}{state}: {scope}.")
    tools = [plain(t, 60) for t in (bud.get("tools") or [])][:8]
    if rows:
        if tools:
            rows.append("- Tools you may call: " + ", ".join(tools) + ".")
        return "\n".join(rows)
    return (
        "No connector is connected to you yet. You can use only the team's messages, files and "
        "reviewed meeting notes that the person asking is allowed to see. If a question needs a "
        "connector, say which one and ask the team to connect it in your Bud profile."
    )


def variables(bud):
    notes, preferences, voice = unpack(bud.get("instructions", ""))
    key = role_for(bud.get("role", ""))
    purpose = purpose_from(bud.get("role", ""))
    label = ROLES[key][0]
    return {
        "name": plain(bud.get("name", "Your Bud"), 80),
        "role": label.lower(),
        "purpose": plain(purpose, 500)
        or f"No purpose was written. Work as the team's {label.lower()} and ask if unsure.",
        "responsibilities": "\n".join(f"- {line}" for line in RESPONSIBILITIES[key]),
        "sources": sources(bud),
        "warmth": level("warmth", preferences["warmth"]),
        "directness": level("directness", preferences["directness"]),
        "detail": level("detail", preferences["detail"]),
        "initiative": level("initiative", preferences["initiative"]),
        "diligence": level("diligence", preferences["diligence"]),
        "reporting": (
            "milestones only"
            if not preferences["reporting"]
            else f"at most one every {preferences['reporting']} seconds"
        ),
        "voice": plain(voice, 480) or "none set",
        "notes": plain(notes, 600) or "none",
    }


def render_brief(bud):
    text = TEMPLATE.read_text(encoding="utf-8")
    values = variables(bud)
    return re.sub(r"\{\{(\w+)\}\}", lambda m: values.get(m.group(1), ""), text)


def briefs_root():
    if sys.platform == "darwin":
        base = Path.home() / "Library/Application Support"
    else:
        base = Path(os.getenv("LOCALAPPDATA", Path.home() / ".local/share"))
    return base / "Aedrova/Buds"


def brief_path(bud, root=None):
    slug = re.sub(r"[^a-z0-9]+", "-", plain(bud.get("name", "bud"), 40).lower()).strip("-") or "bud"
    identifier = re.sub(r"[^A-Za-z0-9]", "", str(bud.get("id", "")))[:8] or "local"
    return (root or briefs_root()) / f"{slug}-{identifier}.md"


def write_brief(bud, root=None):
    path = brief_path(bud, root)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = render_brief(bud)
    if not path.exists() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")
    return path
