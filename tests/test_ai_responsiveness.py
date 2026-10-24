"""Conversation routing, tool-free managed replies, cancellation and evidence boundaries."""

import asyncio
import json
import threading
import time
from types import SimpleNamespace

import httpx
import pytest
from test_connected import setup, snapshot
from test_dots import dot

from aedrova.agents.managed import BuildAccess
from aedrova.agents.replies import needs_sources, reply
from aedrova.agents.runtime import BuildCancelled, LocalRunner


@pytest.mark.parametrize(
    "question",
    [
        "hello",
        "Hi!",
        "Thank you",
        "Who are you?",
        "Explain Python list comprehensions",
        "Draft a launch plan",
    ],
)
def test_general_conversation_needs_no_sources(question):
    assert not needs_sources(question)


@pytest.mark.parametrize(
    "question",
    [
        "What changed?",
        "Summarize our team decisions",
        "What is our revenue?",
        "Read the Notion file",
        "Explain that",
        "Check GitHub issues",
    ],
)
def test_evidence_questions_keep_retrieval(question):
    assert needs_sources(question)


@pytest.mark.parametrize("name", ["Aedrova", "Atlas"])
def test_main_agent_greeting_never_builds_without_buds(qtbot, tmp_path, monkeypatch, name):
    window, _ = setup(qtbot, tmp_path)
    window.account_dialog.snapshot["dots"] = []
    window.account_dialog.snapshot["agent_preferences"] = [{"workspace_id": "w", "nickname": name}]
    answers = []
    monkeypatch.setattr(
        "aedrova.desktop.dot_analysis.start_analysis",
        lambda w, task, **kw: answers.append(task) or True,
    )
    monkeypatch.setattr(
        "aedrova.desktop.builds.start_background_build",
        lambda *a, **k: pytest.fail("Greeting must never create a build"),
    )
    assert window.start_agent_request("@" + name + " hello")
    assert answers == ["hello"]
    assert not window.start_agent_request("ordinary human chat")


def access(provider="codex"):
    return BuildAccess(
        "run",
        provider,
        "gpt-5.3-codex",
        "https://gateway.example/gateway/" + provider + ("/v1" if provider == "codex" else ""),
        "scoped-run-token",
        {"output_tokens": 1024, "run_seconds": 90},
    )


def install_transport(monkeypatch, events=None, status=200, stream=None):
    requests = []
    client = httpx.AsyncClient

    def handle(request):
        requests.append(request)
        if stream:
            return httpx.Response(status, stream=stream)
        body = "".join("data: " + json.dumps(e) + "\n\n" for e in events or [])
        return httpx.Response(status, text=body)

    monkeypatch.setattr(
        "aedrova.agents.replies.httpx.AsyncClient",
        lambda **kw: client(transport=httpx.MockTransport(handle), **kw),
    )
    return requests


def test_managed_answer_streams_once_without_runtime_or_tools(monkeypatch, tmp_path):
    events = [
        {"type": "response.output_text.delta", "delta": "Hello"},
        {"type": "response.output_text.delta", "delta": "!"},
        {"type": "response.completed", "response": {"status": "completed"}},
    ]
    requests = install_transport(monkeypatch, events)
    monkeypatch.setattr(LocalRunner, "run", lambda *a, **k: pytest.fail("No CLI"))
    runner, updates = LocalRunner(lambda _: None), []
    runner.managed = access()
    result = runner.answer("codex", tmp_path, "Say hello", emit=updates.append)
    assert result == "Hello!" and updates == ["Hello", "Hello!"]
    assert len(requests) == 1
    request = requests[0]
    body = json.loads(request.content)
    assert body["tools"] == [] and body["store"] is False and body["stream"] is True
    assert body["max_output_tokens"] == 1024
    assert body["reasoning"] == {"effort": "low"}
    assert request.headers["authorization"] == "Bearer scoped-run-token"
    assert request.url.path == "/gateway/codex/v1/responses"


@pytest.mark.parametrize(
    "events,status",
    [
        ([{"type": "response.output_text.delta", "delta": "partial"}], 200),
        ([{"type": "error", "error": {"message": "private-provider-detail"}}], 200),
        ([{"type": "response.incomplete"}], 200),
        ([], 403),
        ([], 429),
        ([], 502),
    ],
)
def test_failed_or_incomplete_reply_never_counts_as_success(monkeypatch, events, status):
    requests = install_transport(monkeypatch, events, status)
    with pytest.raises(RuntimeError) as error:
        reply(access(), "Hello", threading.Event())
    assert "private-provider-detail" not in str(error.value)
    assert len(requests) == 1  # No hidden retry or unmetered personal fallback.


class WaitingStream(httpx.AsyncByteStream):
    def __init__(self):
        self.closed = False

    async def __aiter__(self):
        await asyncio.sleep(10)
        yield b""

    async def aclose(self):
        self.closed = True


def test_stop_closes_stream_even_before_first_token(monkeypatch):
    stream, cancelled = WaitingStream(), threading.Event()
    requests = install_transport(monkeypatch, stream=stream)
    timer = threading.Timer(0.15, cancelled.set)
    timer.start()
    started = time.monotonic()
    try:
        with pytest.raises(BuildCancelled):
            reply(access(), "Hello", cancelled)
    finally:
        timer.cancel()
    assert time.monotonic() - started < 2
    assert stream.closed and len(requests) == 1


def test_claude_reply_uses_selected_provider_and_requires_completion(monkeypatch):
    requests = install_transport(
        monkeypatch,
        [
            {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "Hi"}},
            {"type": "message_delta", "delta": {"stop_reason": "end_turn"}},
            {"type": "message_stop"},
        ],
    )
    assert reply(access("claude_code"), "Hello", threading.Event()) == "Hi"
    assert requests[0].url.path == "/gateway/claude_code/v1/messages"
    assert json.loads(requests[0].content)["messages"][0]["content"] == "Hello"


@pytest.mark.parametrize("addressed_bud", [False, True])
def test_greeting_skips_evidence_and_tools_but_rechecks_identity(monkeypatch, addressed_bud):
    from aedrova.desktop.dot_analysis import QueryJob

    bud = dot()
    monkeypatch.setattr(
        "aedrova.desktop.dot_analysis.gather",
        lambda *a, **k: pytest.fail("No chat history scan for hello"),
    )
    monkeypatch.setattr(
        "aedrova.desktop.dot_analysis.retrieve",
        lambda *a, **k: pytest.fail("No tool selection for hello"),
    )
    monkeypatch.setattr("aedrova.desktop.dot_analysis.application_ai_origin", lambda: "")
    requests, checks, closed = [], [], []

    def request(path):
        requests.append(path)
        return {"items": [bud]}

    monkeypatch.setattr(
        "aedrova.desktop.dot_analysis.client", lambda _: SimpleNamespace(request=request)
    )

    def authorize(_):
        checks.append(True)
        return snapshot()

    service = SimpleNamespace(
        user=SimpleNamespace(id="u"),
        context_snapshot=authorize,
        close_context=lambda: closed.append(True),
    )
    monkeypatch.setattr(LocalRunner, "run", lambda *a, **kw: "Hello!")
    job = QueryJob(service, "w", "c", "hello", "codex", bud=bud if addressed_bud else None)
    result = []
    job.signals.finished.connect(result.append)
    job.run()
    assert result == [{"text": "Hello!" if addressed_bud else "Hello! How can I help?"}]
    assert len(checks) == 2 and closed == [True]
    assert len(requests) == int(addressed_bud)


def test_provider_named_bud_greeting_does_not_trigger_its_connector():
    from aedrova.desktop.dot_analysis import QueryJob

    bud = dot("GitHub")
    for greeting in ("@GitHub hello", "<@dot:" + bud["id"] + "|GitHub> hello"):
        assert not QueryJob(None, "w", "c", greeting, "codex", bud=bud).sources
    assert QueryJob(None, "w", "c", "@GitHub what changed?", "codex", bud=bud).sources


def test_stream_updates_replace_one_message(qtbot):
    from aedrova.desktop.agent_stream import AgentStream

    feed = AgentStream()
    qtbot.addWidget(feed)
    feed.set_reply("Hel")
    feed.set_reply("Hello")
    assert len(feed.rows) == 1 and feed.toPlainText() == "Hello"
    feed.finish_with_result("Hello!")
    assert len(feed.rows) == 1 and feed.toPlainText() == "Hello!"


def test_greeting_denied_after_membership_changes(monkeypatch):
    from aedrova.desktop.dot_analysis import QueryJob

    checks = []

    def current(_):
        value = snapshot()
        if checks:
            value["members"] = []
        checks.append(True)
        return value

    service = SimpleNamespace(
        user=SimpleNamespace(id="u"), context_snapshot=current, close_context=lambda: None
    )
    monkeypatch.setattr("aedrova.desktop.dot_analysis.application_ai_origin", lambda: "")
    monkeypatch.setattr(LocalRunner, "run", lambda *a, **kw: "Must not be published")
    job = QueryJob(service, "w", "c", "hello", "codex")
    result = []
    job.signals.finished.connect(result.append)
    job.run()
    assert result[0]["error"] and result[0]["text"] != "Must not be published"


def test_included_setup_error_is_distinct_from_network_failure(monkeypatch):
    from aedrova.agents.managed import ManagedClient

    real = httpx.Client

    def handle(request):
        assert request.method == "POST"
        return httpx.Response(403, json={"error": "Included AI access is not configured yet."})

    monkeypatch.setattr(
        "aedrova.agents.managed.httpx.Client",
        lambda **kw: real(transport=httpx.MockTransport(handle), **kw),
    )
    with pytest.raises(RuntimeError, match="hasn’t been enabled"):
        ManagedClient("https://example.test", "private-test-session-000000000001").begin(
            "w", "codex", "request"
        )


def test_general_reply_uses_membership_check_without_channel_inventory(monkeypatch):
    from aedrova.desktop.dot_analysis import QueryJob

    checks = []

    def inventory(_):
        checks.append(True)
        return snapshot()

    service = SimpleNamespace(
        user=SimpleNamespace(id="u"),
        conversation_snapshot=inventory,
        context_snapshot=lambda _: pytest.fail("No channel enumeration for hello"),
        close_context=lambda: None,
    )
    monkeypatch.setattr("aedrova.desktop.dot_analysis.application_ai_origin", lambda: "")
    monkeypatch.setattr(LocalRunner, "run", lambda *a, **kw: "Hello")
    job = QueryJob(service, "w", "c", "hello", "codex")
    results = []
    job.signals.finished.connect(results.append)
    job.run()
    assert checks == [True, True] and results == [{"text": "Hello! How can I help?"}]


def test_lightweight_inventory_is_authenticated_and_user_scoped(monkeypatch):
    from unittest.mock import Mock

    from aedrova.identity.service import Connection, IdentityService

    client = Mock()
    service = IdentityService(
        Connection("https://example.supabase.co", "sb_publishable_abcdefghijk1234567890"),
        client=client,
    )
    service.user = SimpleNamespace(id="u")
    checked = []
    monkeypatch.setattr(service, "_authenticated", lambda: checked.append(True))
    workspaces, members = Mock(), Mock()
    client.table.side_effect = [workspaces, members]
    workspaces.select.return_value.eq.return_value.execute.return_value.data = [{"id": "w"}]
    members.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
        {"workspace_id": "w", "user_id": "u", "role": "member"}
    ]
    result = service.conversation_snapshot("w")
    assert checked == [True] and result["channels"] == []
    assert [c.args[0] for c in client.table.call_args_list] == ["workspaces", "workspace_members"]
    members.select.return_value.eq.return_value.eq.assert_called_once_with("user_id", "u")
