"""Mentions collect full permitted context and build without displaying the studio."""

import threading

import pytest
from test_connected import setup

from aedrova.agents.checkout import prepare as real_prepare
from aedrova.agents.runtime import LocalRunner
from aedrova.desktop.builds import BuildDialog, start_background_build
from aedrova.desktop.projects import save_binding


def configured(qtbot, tmp_path, monkeypatch):
    window, service = setup(qtbot, tmp_path)
    root = tmp_path / "project"
    root.mkdir()
    service.context_page = lambda channel, after: (
        []
        if after
        else [
            {
                "id": "requirement",
                "channel_id": channel,
                "sequence": 1,
                "body": "Build hello.py",
                "parent_id": None,
            }
        ]
    )
    service.attachments_for = lambda _: []
    save_binding(window, {"folder": str(root), "provider": "codex", "background_build": True})
    monkeypatch.setattr(
        "aedrova.desktop.builds.prepare",
        lambda source, _: real_prepare(source, tmp_path / "copies"),
    )
    return window, service, root


def test_mention_plans_and_builds_without_dialog(qtbot, tmp_path, monkeypatch):
    window, service, root = configured(qtbot, tmp_path, monkeypatch)
    runs = []

    def run(self, provider, project, prompt, *, plan):
        runs.append(plan)
        if plan:
            assert '"id": "requirement"' in (project.parent / "workspace-context.jsonl").read_text()
            return "Implement hello.py. [message:requirement]"
        (project / "hello.py").write_text("hello = True\n")
        return "Implemented hello.py"

    monkeypatch.setattr(LocalRunner, "run", run)
    window.composer.editor.setPlainText("@Aedrova build our feature")
    window.send_message(window.composer.editor.toPlainText())
    dialog = window.build_dialog
    assert not dialog.isVisible()
    assert not window.composer.editor.toPlainText()
    qtbot.waitUntil(lambda: dialog.successful_build, timeout=10000)
    assert runs == [True, False]
    assert not dialog.isVisible() and not dialog.background_run
    assert (dialog.project / "hello.py").exists()
    assert not (root / "hello.py").exists()
    assert "Build ready" in window.build_activity.text()
    assert not window.stop_agent.isVisible()


def test_legacy_planning_consent_does_not_authorize_coding(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    save_binding(window, {"folder": str(tmp_path), "auto_plan": True})
    window.composer.editor.setPlainText("@Aedrova build this")
    window.send_message(window.composer.editor.toPlainText())
    assert not getattr(window, "build_dialog", None)
    assert window.agent_setup_needed
    assert "Project settings" in window.build_activity.text()
    assert window.composer.editor.toPlainText()


def test_new_messages_do_not_interrupt_existing_background_plan(qtbot, tmp_path, monkeypatch):
    window, service, root = configured(qtbot, tmp_path, monkeypatch)
    original = service.context_page
    runs = []

    def run(self, provider, project, prompt, *, plan):
        runs.append(plan)
        if plan:
            service.context_page = lambda channel, after: (
                []
                if after
                else original(channel, 0)
                + [
                    {
                        "id": "new",
                        "channel_id": channel,
                        "sequence": 2,
                        "body": "An unrelated new conversation",
                        "parent_id": None,
                    }
                ]
            )
            return "Implement it. [message:requirement]"
        assert (
            "unrelated new conversation"
            not in (project.parent / "workspace-context.jsonl").read_text()
        )
        return "Completed"

    monkeypatch.setattr(LocalRunner, "run", run)
    assert start_background_build(window, "Build hello")
    qtbot.waitUntil(lambda: window.build_dialog.successful_build, timeout=10000)
    assert runs == [True, False]


def test_changed_requirement_blocks_background_implementation(qtbot, tmp_path, monkeypatch):
    window, service, _ = configured(qtbot, tmp_path, monkeypatch)
    original = service.context_page
    runs = []

    def run(self, provider, project, prompt, *, plan):
        runs.append(plan)
        service.context_page = lambda channel, after: [
            {**r, "body": "Changed requirement"} for r in original(channel, after)
        ]
        return "Implement it. [message:requirement]"

    monkeypatch.setattr(LocalRunner, "run", run)
    start_background_build(window, "Build hello")
    qtbot.waitUntil(lambda: "context changed" in window.build_dialog.status.text(), timeout=10000)
    assert runs == [True]
    assert not window.build_dialog.isVisible()


def test_second_mention_and_stop_while_scanning(qtbot, tmp_path, monkeypatch):
    window, service, _ = configured(qtbot, tmp_path, monkeypatch)
    released = threading.Event()
    started = threading.Event()

    def page(channel, after):
        started.set()
        released.wait(3)
        return []

    service.context_page = page
    monkeypatch.setattr(LocalRunner, "run", lambda *a, **k: pytest.fail("Cancelled before model"))
    assert start_background_build(window, "First")
    qtbot.waitUntil(started.is_set)
    assert start_background_build(window, "Second")
    queue = window.execution_queue
    waiting = next(r for r in queue.ledger.rows("u", "w") if r["task"] == "Second")
    assert waiting["state"] == "queued"
    queue.ledger.update(waiting["id"], "cancelled")
    assert window.build_dialog.request.toPlainText() == "First"
    window.stop_agent.click()
    released.set()
    qtbot.waitUntil(lambda: not window.build_dialog.context_jobs, timeout=5000)
    assert not window.build_dialog.pending and not window.build_dialog.background_run


def test_reconfigured_project_cannot_auto_continue(qtbot, tmp_path, monkeypatch):
    window, service, root = configured(qtbot, tmp_path, monkeypatch)
    dialog = BuildDialog(window)
    qtbot.addWidget(dialog)
    dialog.background_run = True
    dialog.background_settings = (str(root), "codex", True)
    dialog.approved_plan = "Plan"
    save_binding(window, {"folder": str(root), "provider": "codex", "background_build": False})
    dialog.continue_background(dialog.generation)
    assert not dialog.pending and not dialog.background_run
    assert "permissions changed" in dialog.status.text()


@pytest.mark.parametrize(
    ("tool", "data", "allow"),
    [
        ("Write", {"file_path": "hello.py"}, True),
        ("Write", {"file_path": "../outside.py"}, False),
        ("Bash", {"command": "python -m unittest"}, True),
        ("Bash", {"dangerouslyDisableSandbox": True}, False),
        ("WebFetch", {"url": "https://example.com"}, False),
    ],
)
def test_background_routine_approval_respects_scope(
    qtbot, tmp_path, monkeypatch, tool, data, allow
):
    from types import SimpleNamespace

    window, _, root = configured(qtbot, tmp_path, monkeypatch)
    dialog = BuildDialog(window)
    qtbot.addWidget(dialog)
    dialog.project = root
    dialog.pending = True
    dialog.background_run = True
    dialog.background_settings = (str(root), "codex", True)
    dialog.job = SimpleNamespace(runner=LocalRunner(lambda _: None))
    request = {"tool": tool, "data": data, "event": threading.Event(), "allow": False}
    dialog.permission(request)
    assert request["event"].is_set() and request["allow"] is allow
    assert not dialog.permission_box
    dialog.job = None
    dialog.pending = False


def test_provider_failure_stays_in_chat(qtbot, tmp_path, monkeypatch):
    window, _, _ = configured(qtbot, tmp_path, monkeypatch)

    def fail(*args, **kwargs):
        raise RuntimeError("Provider login required")

    monkeypatch.setattr(LocalRunner, "run", fail)
    assert start_background_build(window, "Build hello")
    qtbot.waitUntil(lambda: not window.build_dialog.pending, timeout=5000)
    assert not window.build_dialog.isVisible()
    assert "Needs attention" in window.build_activity.text()
    assert "Provider login required" in window.build_dialog.output.toPlainText()


def test_background_uses_saved_folder_not_manual_studio_override(qtbot, tmp_path, monkeypatch):
    window, _, root = configured(qtbot, tmp_path, monkeypatch)
    dialog = BuildDialog(window)
    window.build_dialog = dialog
    qtbot.addWidget(dialog)
    dialog.repository.setText(str(tmp_path / "wrong-project"))
    started = []

    def start(plan):
        started.append(dialog.repository.text())
        dialog.pending = True

    monkeypatch.setattr(dialog, "start", start)
    assert start_background_build(window, "New request")
    assert started == [str(root)]
    dialog.pending = False


def test_activity_shimmer_respects_motion_visibility_and_completion(qtbot, tmp_path):
    from aedrova.desktop.agent_activity import AgentActivity
    from aedrova.desktop.theme import DARK, LIGHT

    widget = AgentActivity()
    qtbot.addWidget(widget)
    widget.setText("Nova · Running tests")
    widget.show()
    widget.configure(DARK, False, True)
    qtbot.waitUntil(lambda: widget.phase > 0)
    assert widget.timer.isActive()
    widget.configure(LIGHT, True, True)
    assert not widget.timer.isActive() and widget.phase == 0
    assert not widget.grab().isNull()
    widget.configure(LIGHT, False, True)
    widget.hide()
    assert not widget.timer.isActive()
    widget.show()
    widget.configure(DARK, False, False)
    assert not widget.timer.isActive()


def test_activity_feed_is_private_plain_text_and_clears_on_logout(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    window.agent_event("w", "Reading project files <script>untrusted</script>")
    assert "<script>" in window.agent_feed.toPlainText()
    window.agent_event("other", "Private other workspace")
    assert "other workspace" not in window.agent_feed.toPlainText()
    window.account_dialog.session_closed.emit()
    assert not window.agent_feed.toPlainText() and not window.agent_feed.isVisible()


def test_visible_controls_do_not_require_plan_creation(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    dialog = BuildDialog(window)
    qtbot.addWidget(dialog)
    dialog.show()
    assert not dialog.plan_button.isVisible()
    assert not dialog.build_button.isVisible()
    assert dialog.start_button.isVisible()
