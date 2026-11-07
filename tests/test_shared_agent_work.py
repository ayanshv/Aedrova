import pytest
from test_builds import service

from aedrova.agents.context import gather
from aedrova.agents.replies import needs_sources
from aedrova.agents.retrieval import ContextIndex, validate_citations
from aedrova.agents.shared_work import recheck


def work(**updates):
    return dict(
        id="work1",
        workspace_id="w",
        channel_id="c",
        source_channels=["c"],
        agent_name="Research Bud",
        body="Launch research found three customer segments",
        created_at="2026-11-01T00:00:00Z",
        **updates,
    )


def test_both_agents_retrieve_attributed_work_and_announce_it():
    source = service()
    source.shared_agent_work = lambda *a, **kw: {"items": [work()], "setup_required": False}
    progress = []
    context = gather(source, "w", progress=progress.append, query="Research Bud findings")
    index = ContextIndex(context)
    try:
        hits = index.retrieve("customer segments")["retrieval"]["sources"]
        shared = next(r for r in hits if r["citation"] == "agent-work:work1")
        assert shared["decision"] == "agent_untrusted"
        assert "Research Bud" in shared["channel"]
        assert any("Consulting shared work from Research Bud" in p for p in progress)
        validate_citations(context, "Based on agent-work:work1, three segments were proposed.")
        with pytest.raises(ValueError, match="unknown source"):
            validate_citations(context, "agent-work:invented")
    finally:
        index.close()
    assert needs_sources("Use the Research Bud findings")
    assert needs_sources("What does the other agent know?")
    assert not needs_sources("hello")
    recheck(source, context)


@pytest.mark.parametrize(
    "changed",
    [
        {"workspace_id": "other"},
        {"channel_id": "hidden"},
        {"source_channels": ["c", "hidden"]},
        {"source_channels": []},
    ],
)
def test_shared_work_requires_original_source_access(changed):
    source = service()
    row = {**work(), **changed}
    source.shared_agent_work = lambda *a, **kw: {"items": [row]}
    with pytest.raises(PermissionError, match="outside"):
        gather(source, "w")


def test_revoked_or_changed_work_is_withheld_after_reasoning():
    source = service()
    source.shared_agent_work = lambda *a, **kw: {"items": [work()]}
    context = gather(source, "w")
    source.shared_agent_work = lambda *a, **kw: {"items": []}
    with pytest.raises(PermissionError, match="access changed"):
        recheck(source, context)


def test_missing_migration_is_explicit_without_blocking_existing_context():
    source = service()
    source.shared_agent_work = lambda *a, **kw: {"items": [], "setup_required": True}
    progress = []
    context = gather(source, "w", progress=progress.append)
    assert context.count == 4
    assert any("database update" in p for p in progress)


def test_private_bud_history_is_not_collected():
    source = service()
    source.bud_conversation = lambda *a: pytest.fail("Private history must not be read")
    context = gather(source, "w")
    assert "private_conversation" not in context.text


def test_shared_build_reviews_remain_attributed_untrusted_and_rechecked():
    source = service()
    row = dict(
        id="review1",
        workspace_id="w",
        channel_id="c",
        source_channels=["c"],
        evidence={"task": "Export CSV", "checks": []},
        current=True,
        updated_at="2026-11-01",
        receipts=[{"kind": "local_apply"}],
    )
    source.build_reviews = lambda _: {"items": [row], "setup_required": False}
    context = gather(source, "w")
    index = ContextIndex(context)
    try:
        hit = next(r for r in index.sources if r.citation == "build-review:review1")
        assert hit.decision == "shared_build_untrusted" and "local_apply" in hit.body
        validate_citations(context, "See build-review:review1")
    finally:
        index.close()
    recheck(source, context)
    source.build_reviews = lambda _: {"items": [], "setup_required": False}
    with pytest.raises(PermissionError, match="review"):
        recheck(source, context)


def test_channel_reply_syncs_optimistically_with_provenance(qtbot, tmp_path, monkeypatch):
    from test_connected import setup

    window, service = setup(qtbot, tmp_path)
    service.save_shared_agent_work = lambda params: params["p_id"]
    queued = []
    monkeypatch.setattr(
        window.connected, "enqueue", lambda *args, **kwargs: queued.append(args) or True
    )
    window.finish_conversation_response(
        "w", "c", None, "Research result", "Research Bud", source_channels=["c"]
    )
    assert window.connected.agent_replies[("w", "c")][-1]["body"] == "Research result"
    assert queued[0][0][0] == "shared-agent-work"
    assert queued[0][1]()
    assert service.user.id == "u"


def test_private_channel_conversations_are_not_exported_to_shared_work(
    qtbot, tmp_path, monkeypatch
):
    from test_connected import setup

    window, service = setup(qtbot, tmp_path)
    service.save_shared_agent_work = lambda _: pytest.fail("DM must not export work")
    window.account_dialog.snapshot["channels"][0]["kind"] = "dm"
    queued = []
    monkeypatch.setattr(
        window.connected, "enqueue", lambda *args, **kwargs: queued.append(args) or True
    )
    window.finish_conversation_response(
        "w", "c", None, "Private answer", "Research Bud", source_channels=["c"]
    )
    assert not queued
