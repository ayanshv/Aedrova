"""The desktop receives only scoped run access and never shared provider credentials."""

import pytest
from test_builds import fake_codex

from aedrova.agents.managed import BuildAccess, ManagedClient, validate_origin
from aedrova.agents.runtime import LocalRunner


@pytest.mark.parametrize(
    "value",
    [
        "http://public.example",
        "https://user:pass@example.com",
        "https://example.com/path",
        "https://example.com?key=secret",
        "https://example.com#fragment",
        "file:///tmp",
    ],
)
def test_managed_origin_rejects_insecure_or_credential_bearing_addresses(value):
    with pytest.raises(ValueError):
        validate_origin(value)


def test_loopback_preview_and_secure_production_origin():
    assert validate_origin("http://127.0.0.1:8090/") == "http://127.0.0.1:8090"
    assert validate_origin("https://aedrova.example/") == "https://aedrova.example"


def access():
    return {
        "id": "r" * 32,
        "token": "t" * 64,
        "model": "gpt-5.3-codex",
        "base_url": "https://aedrova.example/gateway/codex/v1",
    }


def test_managed_begin_validates_gateway_and_hides_opaque_credentials(monkeypatch):
    client = ManagedClient("https://aedrova.example", "private-session")
    monkeypatch.setattr(client, "request", lambda *a: access())
    build = client.begin("space", "codex", "request")
    assert build.token == "t" * 64 and build.token not in repr(build)
    forged = access() | {"base_url": "https://attacker.example/gateway/codex/v1"}
    monkeypatch.setattr(client, "request", lambda *a: forged)
    with pytest.raises(RuntimeError, match="invalid"):
        client.begin("space", "codex", "request")


def test_failed_close_still_drops_account_credentials(monkeypatch):
    client = ManagedClient("https://aedrova.example", "private-session")
    client._run_id = "some-run"

    def fail(*a):
        raise RuntimeError("Offline")

    monkeypatch.setattr(client, "request", fail)
    with pytest.raises(RuntimeError):
        client.close()
    assert client._run_id == client._access_token == ""


def test_managed_codex_uses_opaque_environment_not_shared_keys_or_argv(tmp_path, monkeypatch):
    fake_codex(
        tmp_path,
        monkeypatch,
        """
import os
assert os.environ['AEDROVA_BUILD_TOKEN'] == 'opaque-build-token'
assert 'opaque-build-token' not in ' '.join(sys.argv)
assert 'OPENAI_API_KEY' not in os.environ
assert 'ANTHROPIC_API_KEY' not in os.environ
assert 'model_provider="aedrova_managed"' in sys.argv
assert 'model_providers.aedrova_managed.request_max_retries=0' in sys.argv
assert '--ephemeral' in sys.argv
assert 'read-only' in sys.argv
print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'Done'}}),flush=True)
print(json.dumps({'type':'turn.completed'}),flush=True)
""",
    )
    monkeypatch.setenv("OPENAI_API_KEY", "must-not-forward")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "must-not-forward")
    runner = LocalRunner(lambda _: None)
    runner.managed = BuildAccess(
        "run",
        "codex",
        "gpt-5.3-codex",
        "https://aedrova.example/gateway/codex/v1",
        "opaque-build-token",
    )
    assert runner.run("codex", tmp_path, "request", plan=True) == "Done"


def test_provider_mismatch_stops_before_spawn(tmp_path):
    runner = LocalRunner(lambda _: None)
    runner.managed = BuildAccess(
        "run",
        "claude_code",
        "claude-sonnet-5-5",
        "https://aedrova.example/gateway/claude_code",
        "opaque",
    )
    with pytest.raises(ValueError, match="match"):
        runner.run("codex", tmp_path, "request", plan=True)


def test_packaged_runtime_prefers_bundled_codex_and_fails_closed_if_missing(tmp_path, monkeypatch):
    import sys

    import aedrova.agents.runtime as runtime

    monkeypatch.setattr(runtime, "__file__", str(tmp_path / "runtime.py"))
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(
        runtime.shutil, "which", lambda _: pytest.fail("No external runtime fallback")
    )
    with pytest.raises(ValueError, match="bundled"):
        runtime.executable("codex")
    bundled = tmp_path / "bin/codex"
    bundled.parent.mkdir()
    bundled.write_text("synthetic executable fixture")
    bundled.chmod(0o700)
    assert runtime.executable("codex") == str(bundled)
