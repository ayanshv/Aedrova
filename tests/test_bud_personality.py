from aedrova.dots.personality import DEFAULTS, guidance, pack, progress_emitter, unpack


def test_settings_survive_notes_and_custom_voice_without_granting_authority():
    preferences = {**DEFAULTS, "warmth": 81, "reporting": 43}
    value = pack("Use verified sources.", preferences, "Direct but kind.")
    assert unpack(value) == ("Use verified sources.", preferences, "Direct but kind.")
    prompt = guidance({"instructions": value})
    assert "81" in prompt and "Direct but kind." in prompt
    assert "never override safety" in prompt and "Never claim scheduled" in prompt
    assert unpack("Legacy instructions")[0] == "Legacy instructions"
    malformed = '[Aedrova personality v1]\n{"warmth":true}'
    assert unpack(malformed)[0] == malformed


def test_reporting_throttles_prose_but_retains_tool_events(monkeypatch):
    events = []
    now = [1]
    monkeypatch.setattr("aedrova.dots.personality.time.monotonic", lambda: now[0])
    emit = progress_emitter(events.append, {"instructions": pack("", DEFAULTS, "")})
    emit("Starting")
    emit("More prose")
    emit("Running: tests")
    now[0] = 32
    emit("Checking results")
    assert events == ["Starting", "Running: tests", "Checking results"]
