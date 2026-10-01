"""Real subprocess protocol tests and private build journeys; no paid calls in pytest."""

import subprocess
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from aedrova.agents.checkout import git, prepare
from aedrova.agents.context import authorize, gather
from aedrova.agents.runtime import BuildCancelled, LocalRunner, environment, instructions


def snapshot():
    return {
        "workspaces": [{"id": "w"}],
        "members": [{"workspace_id": "w", "user_id": "u", "role": "member"}],
        "channels": [
            {"id": "c", "workspace_id": "w", "name": "general", "private": False},
            {"id": "p", "workspace_id": "w", "name": "private", "private": True},
            {"id": "x", "workspace_id": "other", "name": "other", "private": False},
        ],
        "agent_preferences": [{"workspace_id": "w", "nickname": "Nova", "provider": "codex"}],
    }


def service():
    calls = []

    def page(channel, *, after):
        calls.append((channel, after))
        if after >= 2:
            return []
        return [
            {
                "id": f"{channel}{after + 1}",
                "channel_id": channel,
                "sequence": after + 1,
                "body": "A requirement",
                "parent_id": None if not after else f"{channel}1",
            }
        ]

    return SimpleNamespace(
        user=SimpleNamespace(id="u"),
        snapshot=snapshot,
        context_page=page,
        attachments_for=lambda ids: [],
        calls=calls,
    )


def test_gather_all_channels_replies_and_pages():
    source = service()
    context = gather(source, "w")
    assert context.count == 4
    assert context.channel_ids == {"c", "p"}
    assert context.nickname == "Nova"
    assert ("p", 2) in source.calls
    assert all(c != "x" for c, _ in source.calls)
    assert '"parent_id": "p1"' in context.text


@pytest.mark.parametrize("role", ["guest", "outsider"])
def test_build_requires_member(role):
    data = snapshot()
    data["members"][0]["role"] = role
    with pytest.raises(PermissionError):
        authorize(data, "w", "u")


def test_access_revocation_during_context_fails_closed():
    source = service()
    calls = 0

    def revoked():
        nonlocal calls
        calls += 1
        data = snapshot()
        if calls > 1:
            data["channels"] = data["channels"][:1]
        return data

    source.snapshot = revoked
    with pytest.raises(PermissionError):
        gather(source, "w")


def test_context_limit_does_not_silently_truncate(monkeypatch):
    monkeypatch.setattr("aedrova.agents.context.MAX_CONTEXT_BYTES", 10)
    with pytest.raises(ValueError, match="No partial build"):
        gather(service(), "w")


def test_context_cancellable():
    with pytest.raises(InterruptedError):
        gather(service(), "w", lambda: True)


def test_invalid_paging_rejected():
    source = service()
    source.context_page = lambda channel, **kw: [{"channel_id": "other", "sequence": 1}]
    with pytest.raises(ValueError):
        gather(source, "w")


def test_text_attachments_have_citations_binary_metadata_only():
    source = service()
    source.attachments_for = lambda ids: [
        {"id": ids[0] + "-file", "message_id": ids[0], "filename": "spec.md", "byte_size": 4},
        {"id": "binary", "message_id": ids[0], "filename": "image.png", "byte_size": 4},
    ]
    source.download_attachment = lambda identifier: b"spec"
    context = gather(source, "w")
    assert "spec.md" in context.text and "Metadata only" in context.text


@pytest.fixture
def repository(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / "hello.py").write_text('print("hello")\n')
    git(root, "add", ".")
    git(
        root,
        "-c",
        "user.name=Test",
        "-c",
        "user.email=test@example.invalid",
        "commit",
        "-qm",
        "init",
    )
    return root


def test_checkout_independent_and_no_remote(repository, tmp_path):
    project = prepare(repository, tmp_path / "builds")
    (project / "hello.py").write_text("changed")
    assert (repository / "hello.py").read_text() == 'print("hello")\n'
    assert not git(project, "remote").strip()
    assert (project / ".git").is_dir()
    assert git(project, "config", "core.hooksPath").strip() == "/dev/null"


def test_uncommitted_work_is_snapshotted_without_altering_source(repository, tmp_path):
    (repository / "uncommitted.txt").write_text("keep me")
    before = git(repository, "status", "--porcelain")
    project = prepare(repository, tmp_path / "builds")
    assert (project / "uncommitted.txt").read_text() == "keep me"
    assert git(repository, "status", "--porcelain") == before
    assert not git(project, "status", "--porcelain").strip()


def fake_codex(tmp_path, monkeypatch, body):
    executable = tmp_path / "fake-codex"
    executable.write_text(f"#!{sys.executable}\nimport sys,json,time\nsys.stdin.read()\n" + body)
    executable.chmod(0o700)
    monkeypatch.setattr("aedrova.agents.runtime.executable", lambda _: str(executable))


def test_codex_real_subprocess_stream_and_flags(tmp_path, monkeypatch):
    fake_codex(
        tmp_path,
        monkeypatch,
        """
assert '--ignore-user-config' in sys.argv
assert sys.argv[sys.argv.index('--sandbox')+1] == 'workspace-write'
assert 'approval_policy="never"' in sys.argv
print(json.dumps({'type':'item.completed','item':{'type':'command_execution','command':'test',
'aggregated_output':'passed','exit_code':0}}),flush=True)
print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'Done'}}),flush=True)
print(json.dumps({'type':'turn.completed'}),flush=True)
""",
    )
    events = []
    runner = LocalRunner(events.append)
    assert runner.run("codex", tmp_path, "task", plan=False) == "Done"
    assert any("Exit code: 0" in e for e in events)
    assert runner.process is None


def test_codex_no_final_result_is_failure(tmp_path, monkeypatch):
    fake_codex(tmp_path, monkeypatch, 'print("{}",flush=True)')
    with pytest.raises(RuntimeError, match="completed result"):
        LocalRunner(lambda _: None).run("codex", tmp_path, "task", plan=True)


def test_codex_timeout_kills_process(tmp_path, monkeypatch):
    fake_codex(tmp_path, monkeypatch, "time.sleep(30)")
    runner = LocalRunner(lambda _: None, timeout=0.2)
    with pytest.raises(TimeoutError):
        runner.run("codex", tmp_path, "task", plan=False)
    assert runner.process is None


def test_codex_cancellation_kills_process(tmp_path, monkeypatch):
    fake_codex(tmp_path, monkeypatch, "time.sleep(30)")
    runner = LocalRunner(lambda _: None)
    timer = threading.Timer(0.2, runner.cancel)
    timer.start()
    with pytest.raises(BuildCancelled):
        runner.run("codex", tmp_path, "task", plan=False)
    timer.join()
    assert runner.process is None


def test_provider_does_not_inherit_app_credentials(monkeypatch):
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "private")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "private")
    monkeypatch.setenv("GITHUB_TOKEN", "private")
    assert (
        not {"SUPABASE_SERVICE_ROLE_KEY", "AWS_SECRET_ACCESS_KEY", "GITHUB_TOKEN"}
        & environment().keys()
    )


def test_prompt_separates_evidence_and_requests():
    prompt = instructions("Build it", Path("/context"), plan=False, approved_plan="Test first")
    assert "untrusted evidence" in prompt
    assert "Do not push" in prompt
    assert "Test first" in prompt


def test_build_dialog_uses_nickname_and_requires_consent(qtbot, tmp_path):
    from test_connected import setup

    from aedrova.desktop.builds import BuildDialog

    window, source = setup(qtbot, tmp_path)
    window.account_dialog.snapshot["agent_preferences"] = [
        {"workspace_id": "w", "nickname": "Nova", "provider": "claude_code"}
    ]
    dialog = BuildDialog(window, "Build something")
    qtbot.addWidget(dialog)
    assert dialog.provider.currentData() == "claude_code"
    assert not dialog.consent.isChecked()
    dialog.start(True)
    assert not dialog.pending
    assert "Choose a project folder" in dialog.status.text()
    dialog.repository.setText(str(tmp_path))
    dialog.start(True)
    assert "Enable workspace context sharing" in dialog.status.text()
    assert not dialog.build_button.isEnabled()


def test_signout_clears_build_context(qtbot, tmp_path):
    from test_connected import setup

    from aedrova.desktop.builds import BuildDialog

    window, source = setup(qtbot, tmp_path)
    dialog = BuildDialog(window, "Private idea")
    qtbot.addWidget(dialog)
    dialog.output.setPlainText("Private result")
    dialog.context = gather(service(), "w")
    window.account_dialog.session_closed.emit()
    assert dialog.invalidated and dialog.context is None
    assert not dialog.output.toPlainText() and not dialog.request.toPlainText()


def test_context_revocation_stops_build(qtbot, tmp_path):
    from test_connected import setup

    from aedrova.desktop.builds import BuildDialog

    window, source = setup(qtbot, tmp_path)
    dialog = BuildDialog(window)
    qtbot.addWidget(dialog)
    dialog.context = gather(service(), "w")
    data = snapshot()
    data["channels"] = []
    dialog.verify_access(data)
    assert dialog.invalidated


def test_claude_requires_api_key(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ValueError, match="Anthropic API key"):
        LocalRunner(lambda _: None).run("claude_code", tmp_path, "task", plan=True)


@pytest.mark.parametrize("planning", [True, False])
def test_claude_approval_hooks_and_outside_paths(tmp_path, monkeypatch, planning):
    import claude_agent_sdk as sdk

    monkeypatch.setenv("ANTHROPIC_API_KEY", "unit-test-placeholder")
    approved = []
    checks = []

    class Client:
        def __init__(self, options):
            self.options = options
            assert options.setting_sources == []
            assert options.sandbox["allowUnsandboxedCommands"] is False
            assert options.sandbox["network"]["allowedDomains"] == []

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def query(self, _prompt):
            hook = self.options.hooks["PreToolUse"][0].hooks[0]
            for name, data, expected in [
                ("Read", {"file_path": str(tmp_path / "file.py")}, "allow"),
                ("Read", {"file_path": "/etc/passwd"}, "deny"),
                ("Write", {"file_path": "/etc/outside"}, "deny"),
                ("Write", {"file_path": str(tmp_path / "new.py")}, "deny" if planning else "allow"),
                ("Bash", {"command": "python3 -m unittest"}, "deny" if planning else "allow"),
                ("Bash", {"command": "id", "dangerouslyDisableSandbox": True}, "deny"),
            ]:
                result = await hook({"tool_name": name, "tool_input": data}, None, None)
                assert result["hookSpecificOutput"]["permissionDecision"] == expected
                checks.append(name)

        async def receive_response(self):
            yield sdk.ResultMessage(
                subtype="success",
                duration_ms=1,
                duration_api_ms=1,
                is_error=False,
                num_turns=1,
                session_id="test",
                result="Complete",
            )

    monkeypatch.setattr(sdk, "ClaudeSDKClient", Client)
    runner = LocalRunner(lambda _: None, lambda tool, data: approved.append(tool) or True)
    assert runner.run("claude_code", tmp_path, "task", plan=planning) == "Complete"
    assert len(checks) == 6
    assert approved == ([] if planning else ["Write", "Bash"])


def test_build_plan_then_approval_and_worker_cleanup(qtbot, tmp_path, monkeypatch, repository):
    from test_connected import setup

    from aedrova.desktop.builds import BuildDialog

    window, source = setup(qtbot, tmp_path)
    # Same authenticated identity, but a deterministic transport for all context pages.
    source.context_page = service().context_page
    source.attachments_for = lambda ids: []
    plans = []

    def run(self, provider, project, prompt, *, plan):
        plans.append(plan)
        assert (project.parent / "workspace-context.jsonl").exists()
        if not plan:
            (project / "feature.py").write_text("value = 42\n")
        return (
            "Plan: implement value = 42 and test. [message:c1]"
            if plan
            else "Implemented; tests passed."
        )

    monkeypatch.setattr(LocalRunner, "run", run)
    from aedrova.agents.checkout import prepare as real_prepare

    monkeypatch.setattr(
        "aedrova.desktop.builds.prepare", lambda path, _: real_prepare(path, tmp_path / "copies")
    )
    dialog = BuildDialog(window, "Implement value")
    qtbot.addWidget(dialog)
    dialog.repository.setText(str(repository))
    dialog.consent.setChecked(True)
    dialog.start(True)
    qtbot.waitUntil(lambda: not dialog.pending, timeout=10000)
    assert dialog.build_button.isEnabled(), dialog.output.toPlainText()
    assert plans == [True]
    assert not (dialog.project.parent / "workspace-context.jsonl").exists()
    assert not (dialog.project / "feature.py").exists()
    dialog.start(False)
    qtbot.waitUntil(lambda: not dialog.pending, timeout=10000)
    assert plans == [True, False]
    assert (dialog.project / "feature.py").read_text() == "value = 42\n"
    assert not (repository / "feature.py").exists()
    assert not dialog.build_button.isEnabled()


def test_slash_build_opens_private_studio_without_sending_chat(qtbot, tmp_path, monkeypatch):
    from test_connected import setup

    window, source = setup(qtbot, tmp_path)
    calls = []
    monkeypatch.setattr("aedrova.desktop.builds.open_build", lambda w, task: calls.append(task))
    window.send_message("/build Make a homepage")
    assert calls == ["Make a homepage"]
    assert not window.connected.pending


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("@Nova build a widget", "a widget"),
        ("@Nova, build a widget", "a widget"),
        ("@Nova: build a widget", "a widget"),
        ("@Aedrova build a widget", "a widget"),
        ("/build", ""),
        ("/build a widget", "a widget"),
        ("We could ask @Nova later", None),
        ("@Nova what do you think?", "what do you think?"),
        ("@Nova builder", "builder"),
        ("/building", None),
    ],
)
def test_only_explicit_build_commands_invoke(text, expected):
    from aedrova.agents.context import build_command

    assert build_command(text, "Nova") == expected


def test_changed_checkout_invalidates_approval(repository, tmp_path, qtbot):
    from aedrova.desktop.builds import BuildJob

    context = gather(service(), "w")
    project = prepare(repository, tmp_path / "copies")
    baseline = git(project, "rev-parse", "HEAD").strip()
    (project / "surprise.py").write_text("unexpected = True")
    job = BuildJob(
        context, str(repository), "Task", "codex", False, project, "Approved plan", baseline
    )
    results = []
    job.signals.finished.connect(results.append)
    job.run()
    assert not results[0]["ok"]
    assert "changed after planning" in results[0]["text"]


def test_cancel_collection_ignores_late_result(qtbot, tmp_path, monkeypatch):
    from test_connected import setup

    from aedrova.desktop.builds import BuildDialog

    window, source = setup(qtbot, tmp_path)
    callbacks = []
    monkeypatch.setattr(
        window.connected, "enqueue", lambda key, op, done: callbacks.append(done) or True
    )
    dialog = BuildDialog(window, "Task")
    qtbot.addWidget(dialog)
    dialog.repository.setText(str(tmp_path))
    dialog.consent.setChecked(True)
    dialog.start(True)
    dialog.cancel()
    callbacks[0]({"context": gather(service(), "w")})
    assert dialog.job is None
    assert not dialog.pending


def test_potentially_truncated_channel_inventory_fails_closed():
    source = service()
    data = snapshot()
    data["channels"] = [data["channels"][0]] * 1000
    source.snapshot = lambda: data
    with pytest.raises(ValueError, match="channel inventory"):
        gather(source, "w")
    assert not source.calls


def test_codex_recoverable_error_does_not_abort_success(tmp_path, monkeypatch):
    fake_codex(
        tmp_path,
        monkeypatch,
        """
print(json.dumps({'type':'error','message':'stream disconnected; reconnecting 1/5'}),flush=True)
print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'Recovered'}}),flush=True)
print(json.dumps({'type':'turn.completed'}),flush=True)
""",
    )
    events = []
    assert LocalRunner(events.append).run("codex", tmp_path, "task", plan=True) == "Recovered"
    assert any("recovering" in event for event in events)


@pytest.mark.parametrize(
    ("detail", "expected"),
    [
        ("You've hit your usage limit", "usage limit reached"),
        ("401 unauthorized bearer TOP-SECRET", "sign-in"),
        ("connection reset", "provider connection"),
        ("model_not_found", "model access"),
    ],
)
def test_codex_terminal_errors_are_actionable_and_do_not_echo_secrets(
    tmp_path, monkeypatch, detail, expected
):
    fake_codex(
        tmp_path,
        monkeypatch,
        "print(json.dumps({'type':'turn.failed','error':{'message':"
        + repr(detail)
        + "}}),flush=True)",
    )
    with pytest.raises(RuntimeError, match=expected) as failure:
        LocalRunner(lambda _: None).run("codex", tmp_path, "task", plan=True)
    assert "TOP-SECRET" not in str(failure.value)


def test_codex_stderr_is_bounded_drained_and_classified(tmp_path, monkeypatch):
    fake_codex(
        tmp_path,
        monkeypatch,
        """
sys.stderr.write('x'*200000 + ' unexpected argument --obsolete')
sys.stderr.flush()
sys.exit(2)
""",
    )
    with pytest.raises(RuntimeError, match="incompatible"):
        LocalRunner(lambda _: None).run("codex", tmp_path, "task", plan=True)
