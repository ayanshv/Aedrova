"""Targeted tools, central-agent routing and the native Dot surface."""

import json
import threading
from types import SimpleNamespace
from uuid import uuid4

import pytest
from PySide6.QtCore import Qt
from test_connected import setup

from aedrova.agents.context import WorkspaceContext
from aedrova.desktop.conversation import Composer
from aedrova.dots.client import calls_from_model, mention, retrieve


def dot(name="GitHub", tools=None):
    return dict(
        id=str(uuid4()),
        workspace_id="w",
        provider="github",
        name=name,
        resource="owner/repo",
        status="Connected",
        tools=tools or {"changes": "Recent commits"},
        shape="round",
        color="#4388F5",
        version=1,
        last_sync=0,
        permissions="Read only",
    )


def test_targeted_multiple_sources_and_no_unrelated_provider_fetch():
    rows = [dot("GitHub"), dot("GitHub Docs"), dot("Other")]
    calls = [{"dot": r["id"], "tool": "changes"} for r in rows[:2]]
    requested = []

    def request(path, body=None, **_kwargs):
        requested.append((path, body))
        if body is None:
            return {"items": rows}
        return {
            "results": [{"dot": c["dot"], "tool": c["tool"], "records": []} for c in body["calls"]]
        }

    runner = SimpleNamespace(
        emit=lambda _: None,
        cancelled=threading.Event(),
        command_results=[],
        run=lambda *args, **kwargs: json.dumps({"calls": calls}),
    )
    context = WorkspaceContext("w", "u", frozenset(), "", 0, "Aedrova", "codex")
    events = []
    result = retrieve(
        SimpleNamespace(request=request),
        context,
        "What changed?",
        runner,
        "codex",
        ".",
        events.append,
    )
    assert requested[1][1]["calls"] == calls
    assert rows[2]["id"] not in result.text
    assert events[-1] == "Analyzing: GitHub · GitHub Docs"
    assert "dot_evidence" in result.text


def test_model_selects_empty_and_zero_connected_dots_make_no_tool_call():
    for rows in [[], [dot()]]:
        requests = []

        def request(path, *_args, captured=requests, sources=rows, **_kwargs):
            captured.append(path)
            return {"items": sources}

        runner = SimpleNamespace(
            emit=lambda _: None, command_results=[], run=lambda *args, **kwargs: '{"calls":[]}'
        )
        context = WorkspaceContext("w", "u", frozenset(), "", 0, "Aedrova", "codex")
        assert (
            retrieve(
                SimpleNamespace(request=request),
                context,
                "Hello team",
                runner,
                "codex",
                ".",
                lambda _: None,
            )
            == context
        )
        assert len(requests) == 1


@pytest.mark.parametrize(
    "output",
    [
        '{"calls":[{"dot":"other","tool":"changes"}]}',
        '{"calls":[{"dot":{},"tool":"changes"}]}',
        '{"calls":[],"url":"http://evil"}',
        '{"calls":null}',
        "not JSON",
    ],
)
def test_untrusted_model_selection_cannot_expand_authority(output):
    with pytest.raises(ValueError):
        calls_from_model(output, [dot()])


def test_dot_completion_retains_source_id_and_click_opens_profile(qtbot, tmp_path, monkeypatch):
    composer = Composer()
    qtbot.addWidget(composer)
    row = dot()
    composer.dots = [row]
    composer.show()
    composer.editor.setFocus()
    qtbot.keyClicks(composer.editor, "@git")
    assert "Bud" in composer.suggestion.text()
    qtbot.keyClick(composer.editor, Qt.Key.Key_Tab)
    assert composer.editor.toPlainText() == "@GitHub "
    assert composer.mention_tokens["GitHub"] == "<@dot:" + row["id"] + "|GitHub>"
    assert mention("Email@GitHub", [row]) is None
    assert mention("Hey @GitHub what changed?", [row]) == row
    window, _ = setup(qtbot, tmp_path)
    opened = []
    monkeypatch.setattr("aedrova.desktop.dots.open_dots", lambda window, key: opened.append(key))
    window.ai_team_section.sync([row], "w")
    window.ai_team_section.habitat.wake(row["id"])
    assert opened == [row["id"]]


def test_dot_question_routes_to_central_analysis_and_build_keeps_existing_queue(
    qtbot, tmp_path, monkeypatch
):
    window, _ = setup(qtbot, tmp_path)
    window.account_dialog.snapshot["dots"] = [dot()]
    requests = []
    monkeypatch.setattr(
        "aedrova.desktop.dot_analysis.start_analysis", lambda w, task: requests.append(task) or True
    )
    assert window.start_agent_request("@GitHub what changed?")
    assert window.start_agent_request("@Aedrova explain recent deployments")
    assert requests == ["@GitHub what changed?", "explain recent deployments"]
    builds = []
    monkeypatch.setattr(
        "aedrova.desktop.builds.start_background_build", lambda w, task: builds.append(task) or True
    )
    assert window.start_agent_request("@Aedrova build a status page with @GitHub")
    assert builds == ["a status page with @GitHub"]


def test_dot_evidence_can_be_cited_without_existing_message_sources():
    from aedrova.agents.retrieval import validate_citations

    row = dot()
    citation = "dot:" + row["id"] + ":changes"
    context = WorkspaceContext(
        "w",
        "u",
        frozenset(),
        json.dumps(
            {
                "dot_evidence": {
                    "dot": row["id"],
                    "name": row["name"],
                    "tool": "changes",
                    "citation": citation,
                    "coverage": "10 newest",
                    "records": [],
                    "untrusted": True,
                }
            }
        ),
        0,
        "Aedrova",
        "codex",
    )
    assert validate_citations(context, "Reviewed [" + citation + "]") == [citation]


def test_native_dot_profile_and_picker_states_in_both_themes(qtbot, tmp_path, monkeypatch):
    from aedrova.desktop.dots import DotDialog

    rows = [
        dot(),
        {
            **dot("Product analytics"),
            "provider": "posthog",
            "status": "Needs authorization",
            "tools": {},
        },
    ]
    providers = [
        dict(id="github", name="GitHub", available=True, permissions="Read-only repository"),
        dict(id="posthog", name="PostHog", available=False, permissions="Analytics coming next"),
    ]

    class API:
        def request(self, path):
            return {"providers": providers} if path.endswith("providers") else {"items": rows}

    window, service = setup(qtbot, tmp_path)
    service.fork_for_context = lambda: service
    service.close_context = lambda: None
    monkeypatch.setattr("aedrova.desktop.dots.client", lambda service: API())

    def enqueue(_key, operation, completed, **_kwargs):
        completed(operation())
        return True

    window.connected.enqueue = enqueue
    dialog = DotDialog(window)
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitUntil(lambda: bool(dialog.rows) and not dialog.job)
    assert dialog.summary.text().startswith("GitHub")
    assert dialog.connect.isEnabled() and dialog.disconnect.isEnabled()
    dialog.rows[0]["status"] = "Needs authorization"
    dialog.select(0)
    assert dialog.disconnect.isEnabled()
    dialog.list.setCurrentRow(1)
    assert not dialog.connect.isEnabled()
    assert "Needs authorization" in dialog.status.text()
    dialog.new_dot()
    assert dialog.resource.isEnabled() and not dialog.connect.isEnabled()
    dialog.provider.setCurrentIndex(dialog.provider.findData("posthog"))
    assert not dialog.save.isEnabled()
    for mode in ("light", "dark"):
        window.set_theme(mode)
        dialog.resize(620, 720)
        dialog.list.setCurrentRow(0)
        qtbot.wait(30)
        import os

        if os.environ.get("AEDROVA_CAPTURE_DOTS"):
            from pathlib import Path

            directory = Path("work/dots")
            directory.mkdir(exist_ok=True)
            dialog.grab().save(str(directory / (mode + "-profile.png")))
            window.ai_team_section.sync(rows, "w")
            qtbot.wait(80)
            window.grab().save(str(directory / (mode + "-workspace.png")))
        for control in (dialog.save, dialog.connect, dialog.disconnect, dialog.remove):
            assert control.geometry().width() >= control.minimumSizeHint().width()
    dialog.reject()


def test_cross_source_query_job_selects_fetches_and_answers_with_citations(monkeypatch):
    from test_connected import snapshot

    from aedrova.desktop.dot_analysis import QueryJob

    row = dot()
    citation = "dot:" + row["id"] + ":changes"
    context = WorkspaceContext("w", "u", frozenset({"c"}), "", 0, "Aedrova", "codex")
    monkeypatch.setattr("aedrova.desktop.dot_analysis.gather", lambda *a, **k: context)
    monkeypatch.setattr("aedrova.desktop.dot_analysis.application_ai_origin", lambda: "")
    paths = []

    class API:
        def request(self, path, body=None, **_kwargs):
            paths.append(path)
            if body:
                return {
                    "results": [
                        {
                            "dot": row["id"],
                            "dot_version": 1,
                            "name": "GitHub",
                            "tool": "changes",
                            "citation": citation,
                            "coverage": "10 newest",
                            "records": [{"kind": "CodeChange", "summary": "Updated sign in"}],
                            "untrusted": True,
                        }
                    ]
                }
            return {"items": [row]}

    monkeypatch.setattr("aedrova.desktop.dot_analysis.client", lambda service: API())
    calls = []

    def run(self, provider, project, prompt, *, plan):
        calls.append(prompt)
        assert plan is True
        if len(calls) == 1:
            return json.dumps({"calls": [{"dot": row["id"], "tool": "changes"}]})
        assert "central Aedrova" in prompt
        evidence = (project / "context.jsonl").read_text()
        assert "Updated sign in" in evidence and "untrusted" in evidence
        return "Sign in changed. [" + citation + "]"

    monkeypatch.setattr("aedrova.agents.runtime.LocalRunner.run", run)
    closed = []
    service = SimpleNamespace(
        context_snapshot=lambda _: snapshot(), close_context=lambda: closed.append(True)
    )
    job = QueryJob(service, "w", "c", "What changed?", "codex")
    results = []
    job.signals.finished.connect(results.append)
    job.run()
    assert len(calls) == 2 and paths[1] == "/api/dots/tools"
    assert results == [{"text": "Sign in changed. [" + citation + "]"}]
    assert closed == [True]


def test_dot_revocation_during_model_reasoning_withholds_result():
    from aedrova.dots.client import recheck

    row = dot()
    context = WorkspaceContext(
        "w",
        "u",
        frozenset(),
        json.dumps({"dot_evidence": {"dot": row["id"], "dot_version": 1}}),
        0,
        "Aedrova",
        "codex",
    )
    api = SimpleNamespace(request=lambda *a: {"items": [{**row, "status": "Needs authorization"}]})
    with pytest.raises(PermissionError, match="access changed"):
        recheck(api, context)


def test_dot_working_state_uses_existing_chat_cancel_control(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    cancelled = []
    window.dot_query = SimpleNamespace(
        workspace="w", runner=SimpleNamespace(cancel=lambda: cancelled.append(True))
    )
    window.agent_activity("w", "Analyzing: GitHub")
    assert not window.stop_agent.isHidden()
    window.cancel_agent()
    assert cancelled == [True]
    window.dot_query = None
    window.finish_agent_response("w", "Source analysis complete.")
    assert window.stop_agent.isHidden()
    assert "Source analysis complete." in window.agent_feed.toPlainText()
