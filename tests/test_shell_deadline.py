import asyncio

import pytest

from aedrova.agents.runtime import LocalRunner, network_command


@pytest.mark.parametrize(
    "command",
    [
        "curl https://example.com",
        "/usr/bin/curl --max-time 2 x",
        "echo x; wget x",
        "env NAME=x ssh x",
        "nc 127.0.0.1 123",
    ],
)
def test_direct_network_clients_rejected(command):
    assert network_command(command)


@pytest.mark.parametrize(
    "command", ["python3 -m pytest", "git diff", "echo 'curling'", "cat curl.txt"]
)
def test_normal_offline_commands_still_available(command):
    assert not network_command(command)


def test_unrecognized_stalled_shell_cancels_without_waiting_whole_build(tmp_path, monkeypatch):
    import claude_agent_sdk as sdk

    monkeypatch.setenv("ANTHROPIC_API_KEY", "synthetic")
    stopped = []

    class Client:
        def __init__(self, options):
            self.options = options

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            stopped.append(True)

        async def query(self, prompt):
            hook = self.options.hooks["PreToolUse"][0].hooks[0]
            result = await hook(
                {
                    "tool_name": "Bash",
                    "tool_input": {"command": "python3 local_task.py", "timeout": 1},
                },
                None,
                None,
            )
            assert result["hookSpecificOutput"]["permissionDecision"] == "allow"

        async def receive_response(self):
            await asyncio.sleep(20)
            yield None

    monkeypatch.setattr(sdk, "ClaudeSDKClient", Client)
    runner = LocalRunner(lambda _: None, lambda *args: True, timeout=10)
    with pytest.raises(TimeoutError, match="shell command exceeded"):
        runner.run("claude_code", tmp_path, "synthetic request", plan=False)
    assert stopped == [True]
