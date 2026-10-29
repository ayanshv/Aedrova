"""Managed Claude keeps its scoped gateway and reviewed tool capabilities."""

import sys
from types import SimpleNamespace

from aedrova.agents.managed import BuildAccess
from aedrova.agents.runtime import LocalRunner


def test_managed_sdk_disables_unreviewed_betas_without_relaxing_tool_gates(tmp_path, monkeypatch):
    seen = {}

    class Assistant:
        pass

    class Result:
        is_error = False
        result = "Scoped result"
        usage = {}

    class Text:
        pass

    class Client:
        def __init__(self, options):
            seen.update(options)

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def query(self, prompt):
            assert prompt == "Inspect this synthetic repository"

        async def receive_response(self):
            yield Result()

    monkeypatch.setitem(
        sys.modules,
        "claude_agent_sdk",
        SimpleNamespace(
            AssistantMessage=Assistant,
            ResultMessage=Result,
            TextBlock=Text,
            ClaudeAgentOptions=lambda **kwargs: kwargs,
            ClaudeSDKClient=Client,
            HookMatcher=lambda **kwargs: kwargs,
            PermissionResultDeny=lambda **kwargs: kwargs,
        ),
    )
    monkeypatch.setenv("ANTHROPIC_API_KEY", "personal-key-must-not-be-used")
    runner = LocalRunner(lambda _: None)
    runner.managed = BuildAccess(
        "run",
        "claude_code",
        "claude-sonnet-5-5",
        "https://staging.example/gateway/claude_code",
        "scoped-run-token",
        {},
    )
    assert (
        runner.run("claude_code", tmp_path, "Inspect this synthetic repository", plan=True)
        == "Scoped result"
    )
    assert seen["env"]["ANTHROPIC_API_KEY"] == "scoped-run-token"
    assert seen["env"]["ANTHROPIC_BASE_URL"] == runner.managed.base_url
    assert seen["env"]["CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS"] == "1"
    assert seen["env"]["CLAUDE_CODE_DISABLE_NONSTREAMING_FALLBACK"] == "1"
    assert seen["permission_mode"] == "dontAsk"
    assert seen["sandbox"]["failIfUnavailable"] is True
    assert seen["sandbox"]["allowUnsandboxedCommands"] is False
    assert seen["tools"] == ["Read", "Glob", "Grep"]
