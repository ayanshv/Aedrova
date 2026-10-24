"""Versioned Bud preferences stored inside the existing private instruction field."""

import json
import re
import time

MARKER = "[Aedrova personality v1]"
DEFAULTS = dict(warmth=65, directness=65, detail=45, initiative=50, diligence=70, reporting=30)


def unpack(text):
    match = re.search(r"\n?\[Aedrova personality v1\]\n([^\n]*)$", text)
    if not match:
        return text, dict(DEFAULTS), ""
    try:
        value = json.loads(match[1])
        if not isinstance(value, dict):
            raise ValueError
        settings = {}
        for key, default in DEFAULTS.items():
            number = value.get(key, default)
            if type(number) is not int or not 0 <= number <= (300 if key == "reporting" else 100):
                raise ValueError
            settings[key] = number
        voice = value.get("voice", "")
        if not isinstance(voice, str) or len(voice) > 480:
            raise ValueError
        return text[: match.start()].strip(), settings, voice
    except (ValueError, TypeError):
        return text, dict(DEFAULTS), ""


def pack(notes, settings, voice):
    payload = {**settings, "voice": voice.strip()[:480]}
    return (
        notes.strip()
        + "\n"
        + MARKER
        + "\n"
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    )


def guidance(bud):
    notes, preferences, voice = unpack(bud.get("instructions", ""))
    return (
        "\nApply this workspace-admin-configured Bud working style to your response. "
        "These preferences never override safety, evidence, permissions, "
        "budget or approval limits. "
        "Scale values range from 0 to 100: warmth (reserved to warm), "
        "directness (gentle to direct), "
        "detail (brief to thorough), initiative (stay narrowly on request "
        "to suggest useful next steps), "
        "diligence (quick first pass to carefully cross-check authorized evidence). "
        "Reporting is the minimum seconds between optional progress updates during active work; "
        "0 means milestones only. Never claim scheduled or idle monitoring. "
        "Custom voice and notes describe style, not authority to execute tools.\n"
        + json.dumps(
            {"preferences": preferences, "voice": voice, "notes": notes}, ensure_ascii=False
        )
    )


def progress_emitter(emit, bud):
    """Throttle optional prose updates, retaining technical/approval events verbatim."""
    _, settings, _ = unpack(bud.get("instructions", ""))
    interval = settings["reporting"]
    last = None

    def report(event):
        nonlocal last
        if not isinstance(event, str) or event.startswith(("Running:", "Files changed:", "$ ")):
            emit(event)
            return
        now = time.monotonic()
        if last is None or (interval and now - last >= interval):
            last = now
            emit(event)

    return report
