import json
from types import SimpleNamespace
from uuid import uuid4

import pytest

from aedrova.agents.replies import needs_sources
from aedrova.dots.client import research_source_links


def test_account_bud_citations_are_bound_to_bud_connection_and_tool():
    from aedrova.agents.context import WorkspaceContext
    from aedrova.agents.retrieval import validate_citations

    bud, connection = str(uuid4()), str(uuid4())
    citation = f"bud:{bud}:{connection}:search"
    evidence = {
        "dot": bud,
        "connection_id": connection,
        "tool": "search",
        "name": "Research",
        "citation": citation,
        "untrusted": True,
        "coverage": "Live cited search",
        "records": {"summary": "Verified finding"},
    }

    def context(value):
        return WorkspaceContext(
            "w", "u", frozenset(), json.dumps({"dot_evidence": value}), 0, "Aedrova", "auto"
        )

    assert validate_citations(context(evidence), f"Finding [{citation}]") == [citation]
    for field, value in (
        ("dot", str(uuid4())),
        ("connection_id", str(uuid4())),
        ("tool", "profile"),
        ("untrusted", False),
    ):
        with pytest.raises(PermissionError, match="Invalid Dot evidence"):
            validate_citations(context({**evidence, field: value}), f"Finding [{citation}]")
    with pytest.raises(ValueError, match="unknown source"):
        validate_citations(context(evidence), f"Finding [bud:{bud}:{uuid4()}:search]")


def test_research_questions_retrieve_but_greetings_do_not():
    assert needs_sources("Research current competitors with sources")
    assert needs_sources("Investigate battery recycling")
    assert not needs_sources("hello")


def test_addressed_research_shortcut_requires_exact_unambiguous_authorized_tool():
    from aedrova.dots.client import direct_research_call

    row = {
        "id": "bud",
        "tools": {"grant.search": "Web search"},
        "connections": [{"id": "grant", "provider": "search", "status": "Connected"}],
    }
    assert direct_research_call([row], "Research current sources", "bud") == [
        {"dot": "bud", "tool": "grant.search"}
    ]
    assert direct_research_call([row], "hello", "bud") is None
    assert direct_research_call([row], "research", None) is None
    assert direct_research_call([row], "research", "another") is None
    row["connections"][0]["status"] = "Error"
    assert direct_research_call([row], "Research current sources", "bud") == [
        {"dot": "bud", "tool": "grant.search"}
    ]
    assert (
        direct_research_call(
            [{**row, "tools": {"grant.search": "Search", "other.page": "Page"}}], "research", "bud"
        )
        is None
    )
    row["connections"][0]["status"] = "Needs authorization"
    assert direct_research_call([row], "research", "bud") is None


def test_only_actual_search_evidence_can_add_safe_deduplicated_source_links():
    records = {
        "sources": [
            {"url": "https://example.com/a(b)"},
            {"url": "https://example.com/a(b)"},
            {"url": "file:///etc/passwd"},
            {"url": "https://user:pass@example.com"},
        ]
    }
    context = SimpleNamespace(
        text="Not JSON\n" + json.dumps({"dot_evidence": {"provider": "search", "records": records}})
    )
    links = research_source_links(context)
    assert links == "\n\nSources: [Source 1](https://example.com/a%28b%29)"
    context.text = json.dumps({"dot_evidence": {"provider": "notion", "records": records}})
    assert research_source_links(context) == ""


def test_native_research_links_are_clickable_and_never_open_local_files(qtbot, monkeypatch):
    from PySide6.QtCore import Qt

    from aedrova.desktop.agent_stream import ActivityRow

    opened = []
    monkeypatch.setattr("aedrova.desktop.agent_stream.webbrowser.open", opened.append)
    row = ActivityRow("Answer. [Source 1](https://example.com/report)")
    qtbot.addWidget(row)
    assert row.message.textInteractionFlags() & Qt.TextInteractionFlag.LinksAccessibleByMouse
    row.message.linkActivated.emit("https://example.com/report")
    row.message.linkActivated.emit("file:///etc/passwd")
    row.message.linkActivated.emit("https://user:secret@example.com/")
    assert opened == ["https://example.com/report"]
