"""Execution permission gates, scoped persistence and real stdio request/reply tests."""

import sys
import threading
from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QMessageBox
from test_connected import setup

from aedrova.agents.permissions import automatic, normalize
from aedrova.agents.runtime import LocalRunner
from aedrova.desktop.agent_permissions import change, mode, sync
from aedrova.desktop.builds import BuildDialog


@pytest.mark.parametrize("value", [None, "unknown", [], {}, 1])
def test_invalid_modes_fail_closed(value):
    assert normalize(value) == "ask"


@pytest.mark.parametrize(
    "command,allowed",
    [
        ("python -m pytest -q tests/test_feature.py", True),
        ("pytest -x", True),
        ("python -c 'print(1)'", False),
        ("pytest -p external", False),
        ("pytest ../../outside", False),
        ("pytest; curl example.com", False),
        ("$(curl example.com)", False),
    ],
)
def test_auto_command_review(tmp_path, command, allowed):
    assert automatic("Bash", {"command": command}, tmp_path) is allowed


def test_auto_edit_review_blocks_escape_and_secrets(tmp_path):
    assert automatic("Write", {"file_path": "app.py"}, tmp_path)
    assert not automatic("Write", {"file_path": "../secret.py"}, tmp_path)
    assert not automatic("Edit", {"paths": ["app.py", ".env"]}, tmp_path)
    assert not automatic("Edit", {"paths": []}, tmp_path)


def test_dropdown_scoped_persistent_and_thread_synced(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    assert mode(window) == "ask"
    window.composer.permissions.setCurrentIndex(window.composer.permissions.findData("auto"))
    assert mode(window) == "auto"
    assert window.thread_composer.permissions.currentData() == "auto"
    assert mode(window, "other-workspace") == "ask"
    service.user = SimpleNamespace(id="different")
    sync(window)
    assert mode(window) == "ask"
    assert window.composer.permissions.currentData() == "ask"
    service.user = SimpleNamespace(id="u")
    sync(window)
    assert window.composer.permissions.currentData() == "auto"


def test_full_access_requires_explicit_selection_confirmation(qtbot, tmp_path, monkeypatch):
    window, _ = setup(qtbot, tmp_path)
    monkeypatch.setattr(QMessageBox, "question", lambda *a: QMessageBox.StandardButton.No)
    change(window, "full")
    assert mode(window) == "ask"
    monkeypatch.setattr(QMessageBox, "question", lambda *a: QMessageBox.StandardButton.Yes)
    change(window, "full")
    assert mode(window) == "full"
    assert window.thread_composer.permissions.currentData() == "full"


@pytest.mark.parametrize(
    "selected,answer,expected,prompts",
    [
        ("ask", False, False, 1),
        ("ask", True, True, 1),
        ("auto", False, True, 0),
        ("full", False, True, 0),
    ],
)
def test_actual_build_gate(qtbot, tmp_path, monkeypatch, selected, answer, expected, prompts):
    window, _ = setup(qtbot, tmp_path)
    window.settings.setValue("agent-permissions/u/w", selected)
    dialog = BuildDialog(window)
    qtbot.addWidget(dialog)
    dialog.pending = True
    dialog.project = tmp_path
    dialog.job = SimpleNamespace(runner=LocalRunner(lambda _: None), permission_mode=selected)
    asked = []

    def decide(box):
        asked.append(box.windowTitle())
        return QMessageBox.StandardButton.Yes if answer else QMessageBox.StandardButton.No

    monkeypatch.setattr(QMessageBox, "exec", decide)
    request = {
        "tool": "Write",
        "data": {"file_path": "hello.py"},
        "event": threading.Event(),
        "allow": False,
    }
    dialog.permission(request)
    assert request["allow"] is expected and request["event"].is_set()
    assert len(asked) == prompts
    dialog.pending = False
    dialog.job = None


def test_permission_change_cancels_old_run(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    invalidated = []
    window.build_dialog = SimpleNamespace(
        workspace="w", pending=True, invalidate=lambda: invalidated.append(True)
    )
    change(window, "auto")
    assert invalidated == [True]
    del window.build_dialog


def fake_server(tmp_path, monkeypatch, *, decision="decline", wrong_scope=False):
    binary = tmp_path / "fake-server"
    body = """
import sys,json
assert 'app-server' in sys.argv
assert 'permissions.aedrova.network.enabled=false' in sys.argv
assert 'shell_environment_policy.inherit="none"' in sys.argv
assert any(x.startswith('permissions.aedrova.filesystem=') for x in sys.argv)
def read(): return json.loads(sys.stdin.readline())
def send(v): print(json.dumps(v),flush=True)
x=read();assert x['method']=='initialize';send({'id':x['id'],'result':{}})
assert read()['method']=='initialized'
x=read(); assert x['method']=='thread/start';assert x['params']['ephemeral']
send({'id':x['id'],'result':{'thread':{'id':'thread'}}})
x=read();assert x['method']=='turn/start';send({'id':x['id'],'result':{'turn':{'id':'turn'}}})
send({'method':'item/started','params':{'threadId':'thread','turnId':'turn',
'item':{'id':'item','type':'commandExecution','command':'python -m pytest -q'}}})
send({'id':91,'method':'item/commandExecution/requestApproval',
'params':{'threadId':THREAD,'turnId':'turn','itemId':'item','command':'python -m pytest -q'}})
x=read(); assert x=={'id':91,'result':{'decision':DECISION}},x
# A newly introduced permissions request can never expand filesystem/network authority.
send({'id':92,'method':'item/permissions/requestApproval','params':{'threadId':'thread','turnId':'turn','permissions':{'network':{'enabled':True}}}})
assert read()['result']['permissions']=={}
send({'method':'item/completed','params':{'threadId':'thread','turnId':'turn','item':{'id':'message','type':'agentMessage','text':'Finished'}}})
send({'method':'turn/completed','params':{'threadId':'thread','turn':{'id':'turn','status':'completed'}}})
sys.stdin.read()
""".replace("THREAD", repr("other" if wrong_scope else "thread")).replace(
        "DECISION", repr(decision)
    )
    binary.write_text(f"#!{sys.executable}\n" + body)
    binary.chmod(0o700)
    monkeypatch.setattr("aedrova.agents.runtime.executable", lambda _: str(binary))


@pytest.mark.parametrize("allow", [True, False])
def test_real_stdio_waits_for_actual_permission(tmp_path, monkeypatch, allow):
    fake_server(tmp_path, monkeypatch, decision="accept" if allow else "decline")
    asked = []

    def approve(tool, data):
        asked.append((tool, data))
        return allow

    runner = LocalRunner(lambda _: None, approve, timeout=5)
    runner.permission_mode = "ask"
    assert runner.run("codex", tmp_path, "test", plan=False) == "Finished"
    assert asked[0][0] == "Bash"
    assert runner.process is None


def test_other_turn_request_never_prompts_or_executes(tmp_path, monkeypatch):
    fake_server(tmp_path, monkeypatch, wrong_scope=True)
    runner = LocalRunner(lambda _: None, lambda *_: pytest.fail("cross-scope approval"), timeout=5)
    runner.permission_mode = "ask"
    assert runner.run("codex", tmp_path, "test", plan=False) == "Finished"


def test_auto_requests_human_for_unreviewed_command(qtbot, tmp_path, monkeypatch):
    window, _ = setup(qtbot, tmp_path)
    window.settings.setValue("agent-permissions/u/w", "auto")
    dialog = BuildDialog(window)
    qtbot.addWidget(dialog)
    dialog.pending = True
    dialog.project = tmp_path
    dialog.job = SimpleNamespace(runner=LocalRunner(lambda _: None), permission_mode="auto")
    prompts = []

    def refuse(box):
        prompts.append(box)
        return QMessageBox.StandardButton.No

    monkeypatch.setattr(QMessageBox, "exec", refuse)
    request = {
        "tool": "Bash",
        "data": {"command": "python custom_script.py"},
        "event": threading.Event(),
        "allow": False,
    }
    dialog.permission(request)
    assert len(prompts) == 1 and not request["allow"] and request["event"].is_set()
    dialog.job = None
    dialog.pending = False


def test_changed_permission_during_prompt_cannot_approve(qtbot, tmp_path, monkeypatch):
    window, _ = setup(qtbot, tmp_path)
    dialog = BuildDialog(window)
    qtbot.addWidget(dialog)
    dialog.pending = True
    dialog.project = tmp_path
    dialog.job = SimpleNamespace(runner=LocalRunner(lambda _: None), permission_mode="ask")

    def changed(box):
        window.settings.setValue("agent-permissions/u/w", "auto")
        return QMessageBox.StandardButton.Yes

    monkeypatch.setattr(QMessageBox, "exec", changed)
    request = {
        "tool": "Write",
        "data": {"file_path": "x.py"},
        "event": threading.Event(),
        "allow": False,
    }
    dialog.permission(request)
    assert not request["allow"] and request["event"].is_set()
    dialog.job = None
    dialog.pending = False


def test_cancellation_during_approval_stops_provider(tmp_path, monkeypatch):
    from aedrova.agents.runtime import BuildCancelled

    fake_server(tmp_path, monkeypatch)
    runner = LocalRunner(lambda _: None, timeout=5)
    runner.permission_mode = "ask"

    def cancel(*_):
        runner.cancel()
        return False

    runner.approve = cancel
    with pytest.raises(BuildCancelled):
        runner.run("codex", tmp_path, "test", plan=False)
    assert runner.process is None


def test_managed_approval_runtime_cannot_use_personal_auth(tmp_path, monkeypatch):
    from pathlib import Path

    from aedrova.agents.managed import BuildAccess

    personal = tmp_path / "personal-codex"
    personal.mkdir()
    (personal / "auth.json").write_text('{"test":"personal-auth-must-not-be-used"}')
    monkeypatch.setenv("CODEX_HOME", str(personal))
    fake_server(tmp_path, monkeypatch)
    binary = tmp_path / "fake-server"
    source = binary.read_text().replace(
        "import sys,json",
        "import sys,json,os\nfrom pathlib import Path\n"
        "assert not (Path(os.environ['CODEX_HOME'])/'auth.json').exists()\n"
        "assert os.environ['AEDROVA_BUILD_TOKEN']=='synthetic-scoped-token'\n"
        "assert any('https://staging.example/gateway/codex' in a for a in sys.argv)",
    )
    binary.write_text(source)
    runner = LocalRunner(lambda _: None, timeout=5)
    runner.permission_mode = "ask"
    runner.managed = BuildAccess(
        "run",
        "codex",
        "test-model",
        "https://staging.example/gateway/codex",
        "synthetic-scoped-token",
        {},
    )
    assert runner.run("codex", tmp_path, "test", plan=False) == "Finished"
    assert Path(personal / "auth.json").is_file()


def test_new_project_does_not_inherit_full_authority(qtbot, tmp_path):
    from aedrova.desktop.projects import save_binding

    window, _ = setup(qtbot, tmp_path)
    save_binding(window, {"folder": str(tmp_path / "original")})
    window.settings.setValue("agent-permissions/u/w", "full")
    save_binding(window, {"folder": str(tmp_path / "different")})
    assert mode(window) == "ask"
    assert window.composer.permissions.currentData() == "ask"
