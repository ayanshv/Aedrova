"""Rendered reply safety, causal ordering, scoped history and local project evidence."""

import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from test_connected import row, setup, snapshot

from aedrova.agents.context import WorkspaceContext
from aedrova.agents.project_context import project_evidence
from aedrova.agents.retrieval import validate_citations
from aedrova.desktop.agent_stream import ActivityRow
from aedrova.desktop.connected import message_tree
from aedrova.desktop.conversation import markdown_document


def test_bold_code_and_hostile_markup_are_rendered_safely(qtbot):
    text = '**Aedrova** uses `code`. <img src="file:///tmp/private.png">'
    widget = ActivityRow(text)
    qtbot.addWidget(widget)
    document = markdown_document(text)
    assert "**" not in document.toPlainText()
    cursor = document.find("Aedrova")
    assert cursor.charFormat().fontWeight() >= 600
    assert "<img src=" not in widget.message.text()
    assert "&lt;img" in widget.message.text()
    image = ActivityRow("![image](file:///tmp/private.png)")
    qtbot.addWidget(image)
    assert "<img " not in image.message.text()
    widget.set_message("Now **finished**")
    assert "**" not in widget.message.text()


def test_order_normalizes_offsets_and_pending_rows():
    earlier = dict(row("prompt"), created_at="2026-10-24T12:00:00-07:00", sequence=4)
    later = dict(row("answer"), created_at="2026-10-24T19:00:01Z", sequence=5)
    pending = dict(row("pending"), created_at="2026-10-24T19:00:00.500000+00:00", local=True)
    assert [m.id for m in message_tree([later, pending, earlier], "u")] == [
        "prompt",
        "pending",
        "answer",
    ]


@pytest.mark.parametrize("thread", [False, True])
def test_each_reply_stays_between_its_prompt_and_the_next_prompt(qtbot, tmp_path, thread):
    window, service = setup(qtbot, tmp_path)
    qtbot.waitUntil(lambda: not window.connected.current_action and not window.connected.queue)
    if thread:
        window.thread_id = "m"
    parent = "m" if thread else None
    now = datetime.now(UTC)
    first = dict(
        row("first", parent),
        body="@Aedrova first",
        created_at=(now - timedelta(seconds=2)).isoformat(),
    )
    window.connected.cache["c"] = {"m": row(), "first": first}
    window.finish_conversation_response("w", "c", parent, "**First answer**", "Aedrova")
    second = dict(
        row("second", parent),
        body="@Aedrova second",
        created_at=(now + timedelta(seconds=1)).isoformat(),
    )
    window.connected.cache["c"]["second"] = second
    window.finish_conversation_response("w", "c", parent, "Second answer", "Aedrova")
    window.connected.render_local_messages()
    messages = window.channel.messages[0].replies if thread else window.channel.messages
    # The artificial second prompt is in the future; real sent timestamps below
    # deliberately establish causality without relying on dictionary insertion.
    for r in window.connected.agent_replies[("w", "c")]:
        if r["body"] == "Second answer":
            r["created_at"] = (now + timedelta(seconds=2)).isoformat()
    window.connected.render_local_messages()
    messages = window.channel.messages[0].replies if thread else window.channel.messages
    assert [m.body for m in messages][-4:] == [
        "@Aedrova first",
        "**First answer**",
        "@Aedrova second",
        "Second answer",
    ]
    assert not window.agent_feed.toPlainText()
    assert window.connected.with_agent_replies([], "other", "c") == []
    assert window.connected.with_agent_replies([], "w", "private") == []
    window.connected.disconnect()
    assert not window.connected.agent_replies


def test_project_evidence_reads_current_files_excludes_secrets_links_and_generated(tmp_path):
    project = tmp_path / "app"
    project.mkdir()
    (project / "README.md").write_text("Aedrova builds collaboration tools.")
    (project / "main.py").write_text('def greet(): return "hello"')
    (project / ".env").write_text("PRIVATE_CONFIG=yes")
    (project / "notes.private.json").write_text('{"private":true}')
    (project / "work").mkdir()
    (project / "work" / "draft.md").write_text("DO_NOT_SHARE")
    outside = tmp_path / "outside.md"
    outside.write_text("OUTSIDE_FOLDER")
    (project / "linked.md").symlink_to(outside)
    body = project_evidence(project, "summarize project")
    assert "collaboration tools" in body and "def greet" in body
    assert all(
        s not in body for s in ["PRIVATE_CONFIG", "DO_NOT_SHARE", "OUTSIDE_FOLDER", "private.json"]
    )
    assert str(tmp_path) not in body
    records = [json.loads(line) for line in body.splitlines()]
    citation = records[1]["project_file"]["citation"]
    context = WorkspaceContext("w", "u", frozenset(), body, 0, "Aedrova", "codex")
    assert validate_citations(context, "[" + citation + "]") == [citation]
    with pytest.raises(ValueError, match="unknown source"):
        validate_citations(context, "project:" + "f" * 24)
    (project / "README.md").write_text("Updated current project.")
    assert "Updated current project" in project_evidence(project, "project summary")
    with pytest.raises(InterruptedError):
        project_evidence(project, "project", lambda: True)


def test_query_job_supplies_connected_project_and_exact_runtime_identity(monkeypatch, tmp_path):
    from aedrova.agents.runtime import LocalRunner
    from aedrova.desktop.dot_analysis import QueryJob

    (tmp_path / "README.md").write_text("A bounded project summary from the connected folder.")
    context = WorkspaceContext("w", "u", frozenset({"c"}), "", 0, "Aedrova", "codex")
    monkeypatch.setattr("aedrova.desktop.dot_analysis.gather", lambda *a, **kw: context)
    monkeypatch.setattr(
        "aedrova.desktop.dot_analysis.application_ai_origin", lambda: "https://ai.example"
    )
    monkeypatch.setattr("aedrova.desktop.dot_analysis.client", lambda _: object())
    monkeypatch.setattr("aedrova.desktop.dot_analysis.retrieve", lambda api, ctx, *a, **kw: ctx)
    access = SimpleNamespace(model="configured-model")
    monkeypatch.setattr(
        "aedrova.desktop.dot_analysis.ManagedClient",
        lambda *a: SimpleNamespace(begin=lambda *a: access, close=lambda: None),
    )

    def answer(self, provider, project, prompt, **kw):
        assert "configured-model" in prompt and "You are Aedrova" in prompt
        assert "bounded project summary" in kw["context"]
        evidence = [json.loads(line) for line in kw["context"].splitlines() if line]
        citation = next(r["project_file"]["citation"] for r in evidence if "project_file" in r)
        return "Connected project summary [" + citation + "]"

    monkeypatch.setattr(LocalRunner, "answer", answer)
    service = SimpleNamespace(
        user=SimpleNamespace(id="u"),
        context_snapshot=lambda _: snapshot(),
        realtime_credentials=lambda: (None, None, "token", None),
        close_context=lambda: None,
    )
    job = QueryJob(service, "w", "c", "summarize project", "codex", project_folder=str(tmp_path))
    results = []
    job.signals.finished.connect(results.append)
    job.run()
    assert results and not results[0].get("error"), results


def test_actual_chat_job_finishes_without_reordering_or_replacing_prompts(
    qtbot, tmp_path, monkeypatch
):
    from aedrova.agents.runtime import LocalRunner
    from aedrova.desktop.projects import save_binding

    window, service = setup(qtbot, tmp_path)
    qtbot.waitUntil(lambda: not window.connected.current_action and not window.connected.queue)
    service.context_snapshot = lambda _: snapshot()
    service.conversation_snapshot = lambda _: snapshot()
    service.close_context = lambda: None
    service.fork_for_context = lambda: service
    saved = [row()]

    def rpc(name, params):
        if name == "send_message":
            saved.append(
                dict(
                    row(params["p_id"], params["p_parent"]),
                    body=params["p_body"],
                    sequence=len(saved) + 1,
                    created_at=datetime.now(UTC).isoformat(),
                )
            )

    service.rpc = rpc
    service.message_page = lambda *a, **kw: list(saved)
    monkeypatch.setattr("aedrova.desktop.dot_analysis.application_ai_origin", lambda: "")
    project = tmp_path / "connected-project"
    project.mkdir()
    (project / "README.md").write_text("Our project is an accessible team workspace.")
    save_binding(window, {"folder": str(project), "provider": "auto"})

    def answer(self, provider, project, prompt, **kwargs):
        records = [json.loads(line) for line in kwargs["context"].splitlines() if line]
        source = next(r["project_file"] for r in records if "project_file" in r)
        return "**Accessible team workspace** [" + source["citation"] + "]"

    monkeypatch.setattr(LocalRunner, "answer", answer)
    for question in ["@Aedrova hello", "Please @Aedrova summarize the project"]:
        window.composer.editor.setPlainText(question)
        window.send_message(question)
        qtbot.waitUntil(lambda: not window.dot_query, timeout=10000)
        qtbot.waitUntil(lambda: not window.connected.current_action and not window.connected.queue)
    window.connected.render_local_messages()
    # Initial history loading is independent of these four new messages.
    bodies = [m.body for m in window.messages.conversation_model.messages if m.body != "Hello"]
    assert bodies[:3] == [
        "@Aedrova hello",
        "Hello! How can I help?",
        "Please @Aedrova summarize the project",
    ]
    assert bodies[3].startswith("**Accessible team workspace**")
    assert len(bodies) == 4
    assert not window.agent_feed.toPlainText()
    assert window.composer.editor.toPlainText() == ""


def test_completed_build_answer_survives_next_request_and_signout_clears_it(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    qtbot.waitUntil(lambda: not window.connected.current_action and not window.connected.queue)
    window.activity_channel = "c"
    window.agent_feed.set_reply("**Build finished**")
    window.finish_agent_response("w", "**Build finished**")
    window.archive_finished_agent()
    window.archive_finished_agent()
    window.agent_feed.clear()
    window.connected.render_local_messages()
    assert [m.body for m in window.channel.messages].count("**Build finished**") == 1
    window.connected.disconnect()
    assert window.completed_agent_response is None
    assert not window.connected.agent_replies
