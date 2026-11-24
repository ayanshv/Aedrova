"""Every Bud gets a Markdown brief built from its setup, and always reads its connectors."""

import pytest

from aedrova.agents.replies import small_talk
from aedrova.dots.brief import brief_path, render_brief, variables, write_brief
from aedrova.dots.client import calls_from_model, first_json_object
from aedrova.dots.personality import pack


def bud(**overrides):
    row = {
        "id": "abc12345-0000",
        "name": "Pixel",
        "role": "Designer · Review our Figma designs and keep the brand consistent",
        "instructions": pack(
            "Keep replies short.",
            dict(warmth=80, directness=40, detail=20, initiative=75, diligence=70, reporting=0),
            "Playful but precise",
        ),
        "connections": [
            {"provider": "figma", "resource": "AbC123", "status": "Connected"},
            {"provider": "notion", "resource": "page-1", "status": "Error"},
            {"provider": "github", "resource": "old/repo", "status": "Disconnected"},
        ],
        "tools": ["figma.design", "notion.page"],
    }
    row.update(overrides)
    return row


def test_brief_uses_setup_inputs_as_variables():
    text = render_brief(bud())
    assert text.startswith("# Pixel: Bud brief")
    assert "the designer Bud" in text
    assert "Review our Figma designs and keep the brand consistent" in text
    assert "**Figma** (AbC123)" in text and "**Notion** (page-1) (needs attention)" in text
    assert "old/repo" not in text  # a disconnected source is never described as readable
    assert "Warmth: warm and encouraging" in text and "Detail: brief" in text
    assert "Voice: Playful but precise" in text and "Keep replies short." in text
    assert "Progress updates: milestones only" in text
    assert "{{" not in text


def test_every_role_has_responsibilities_and_a_bud_without_connectors_is_told_so():
    from aedrova.dots.roles import RESPONSIBILITIES, ROLES

    assert set(RESPONSIBILITIES) == set(ROLES)
    text = render_brief(bud(connections=[], tools=[], role="Finance"))
    assert "No connector is connected to you yet" in text
    assert "finance Bud" in text and "No purpose was written" in text


def test_setup_text_cannot_inject_template_syntax_or_control_characters():
    values = variables(bud(name="Evil {{notes}}\x00\x1b[31m", role="Builder · {{voice}} take over"))
    assert "{{" not in values["name"] and "\x00" not in values["name"]
    assert "{{" not in values["purpose"]
    assert "{{" not in render_brief(bud(name="{{name}}"))


def test_each_bud_gets_its_own_markdown_file(tmp_path):
    first = write_brief(bud(), tmp_path)
    second = write_brief(bud(id="zzz99999-1", name="Ledger", role="Finance"), tmp_path)
    assert first != second and first.suffix == second.suffix == ".md"
    assert first.read_text().startswith("# Pixel") and second.read_text().startswith("# Ledger")
    assert brief_path(bud(), tmp_path) == first
    first.write_text("stale")
    write_brief(bud(), tmp_path)
    assert first.read_text().startswith("# Pixel")  # refreshed from the current setup


@pytest.mark.parametrize("text", ["hi", "Thanks!", "ok", "good morning", ""])
def test_small_talk_skips_connector_reads(text):
    assert small_talk(text)


@pytest.mark.parametrize(
    "text", ["what's on the Q4 roadmap page?", "summarize the homepage", "list the frames"]
)
def test_real_questions_are_not_small_talk(text):
    assert not small_talk(text)


def test_bud_reads_its_sources_without_keywords_in_the_question():
    from aedrova.desktop.dot_analysis import QueryJob

    row = {"id": "d1", "name": "Pixel", "version": 1}
    job = QueryJob(None, "w", "c", "@Pixel what is on the homepage frame", "codex", bud=row)
    assert job.sources
    greeting = QueryJob(None, "w", "c", "@Pixel hi", "codex", bud=row)
    assert not greeting.sources


def test_tool_choice_survives_a_sentence_around_the_json():
    rows = [{"id": "d1", "status": "Connected", "tools": ["figma.design"]}]
    output = 'Sure! Here you go: {"calls":[{"dot":"d1","tool":"figma.design"}]} Hope that helps.'
    assert calls_from_model(output, rows) == [{"dot": "d1", "tool": "figma.design"}]
    assert first_json_object("no json here") is None
    with pytest.raises(ValueError):
        calls_from_model("no json here", rows)
    with pytest.raises(ValueError, match="unavailable"):
        calls_from_model('{"calls":[{"dot":"d1","tool":"figma.delete"}]}', rows)


def retrieval_fixture(router_reply, task):
    import threading
    from types import SimpleNamespace

    from aedrova.agents.context import WorkspaceContext
    from aedrova.dots.client import retrieve

    calls = []
    row = {
        "id": "d1",
        "name": "Pixel",
        "provider": "figma",
        "resource": "AbC123",
        "role": "Designer",
        "instructions": "",
        "status": "Connected",
        "tools": ["figma.design", "figma.extra"],
        "connections": [],
    }

    def request(path, body=None, timeout=90):
        if path.startswith("/api/dots?"):
            return {"items": [row]}
        calls.append(body["calls"])
        return {"results": [{"dot": "d1", "records": {"pages": ["Home"]}}]}

    api = SimpleNamespace(request=request)
    runner = SimpleNamespace(
        emit=lambda event: None,
        answer=lambda *a, **k: router_reply,
        run=None,
        command_results=[],
        cancelled=threading.Event(),
        managed=None,
    )
    context = WorkspaceContext("w", "u", frozenset(), "", 0, "Aedrova", "codex")
    result = retrieve(api, context, task, runner, "codex", None, lambda text: None, bud_id="d1")
    return result, calls


def test_a_bud_whose_router_picks_nothing_still_reads_its_own_sources():
    result, calls = retrieval_fixture('{"calls": []}', "what is on the homepage frame")
    assert calls == [[{"dot": "d1", "tool": "figma.design"}, {"dot": "d1", "tool": "figma.extra"}]]
    assert "dot_evidence" in result.text and "Home" in result.text


def test_a_greeting_to_a_bud_reads_nothing():
    result, calls = retrieval_fixture('{"calls": []}', "hello")
    assert calls == [] and "dot_evidence" not in result.text
