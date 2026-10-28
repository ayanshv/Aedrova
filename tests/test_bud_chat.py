"""Private conversations must never route through shared message sending/context."""

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from test_connected import setup
from test_dots import dot

from aedrova.desktop.bud_chat import BudChat


def ready_chat(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    # Settle initial dashboard sync before replacing its shared fake RPC transport.
    qtbot.waitUntil(lambda: bool(window.channel.messages) and not window.account_dialog.busy
                    and not window.connected.current_action and not window.connected.queue)
    history, calls = [], []

    def rpc(name, params):
        calls.append((name, dict(params)))
        if name == "bud_conversation":
            return list(history)
        assert name == "append_bud_message"  # Never send_message or a channel RPC.
        row = {
            "id": params["p_id"],
            "body": params["p_body"],
            "role": "assistant" if params.get("p_reply_to") else "user",
            "created_at": datetime.now(UTC).isoformat(),
        }
        history.append(row)
        return row

    service.rpc = rpc
    dialog = BudChat(window, dot())
    qtbot.addWidget(dialog)
    qtbot.waitUntil(lambda: dialog.loaded)
    return window, service, dialog, history, calls


def test_private_history_reopens_without_posting_to_channel(qtbot, tmp_path):
    window, service, dialog, history, calls = ready_chat(qtbot, tmp_path)
    answers = []
    dialog.answer = answers.append
    dialog.composer.editor.setPlainText("Private idea")
    dialog.send("Private idea")
    assert dialog.pending_message["p_body"] == "Private idea"  # Immediate local echo.
    qtbot.waitUntil(lambda: len(answers) == 1)
    assert history[0]["body"] == "Private idea"
    assert window.channel.messages[0].body == "Hello"
    dialog.reject()
    reopened = BudChat(window, dot())
    qtbot.addWidget(reopened)
    qtbot.waitUntil(lambda: reopened.loaded)
    assert reopened.history == history
    assert not reopened.workspace_context.isChecked()
    assert not reopened.retry.isHidden()
    assert all(name in {"bud_conversation", "append_bud_message"} for name, _ in calls)


def test_load_failure_removes_skeleton_and_keeps_composer_disabled(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    service.rpc = lambda *_: (_ for _ in ()).throw(PermissionError("migration missing"))
    dialog = BudChat(window, dot())
    qtbot.addWidget(dialog)
    qtbot.waitUntil(lambda: not dialog.busy)
    assert not dialog.loaded and not dialog.composer.isEnabled()
    assert not dialog.retry.isHidden()
    assert "Couldn’t save or load" in dialog.status.text()


def test_signout_discards_private_ui_and_cancels_job(qtbot, tmp_path):
    window, _, dialog, _, _ = ready_chat(qtbot, tmp_path)
    cancelled = []
    dialog.history.append({"role": "user", "body": "private"})
    dialog.job = SimpleNamespace(runner=SimpleNamespace(cancel=lambda: cancelled.append(True)))
    window.account_dialog.session_closed.emit()
    assert dialog.closed and dialog.history == [] and cancelled == [True]


def test_dm_button_uses_existing_coworker_flow(qtbot, tmp_path, monkeypatch):
    window, _ = setup(qtbot, tmp_path)
    started = []
    monkeypatch.setattr(window.connected, "start_dm", lambda: started.append(True))
    window.start_dm_button.click()
    assert started == [True]
    assert window.start_dm_button.accessibleName() == "New direct message"


def test_coworker_picker_creates_and_reopens_server_dm(qtbot, tmp_path, monkeypatch):
    from test_connected import snapshot

    window, service = setup(qtbot, tmp_path)
    data = snapshot()
    data["directory"] = [
        {"workspace_id": "w", "user_id": "u", "display_name": "You"},
        {"workspace_id": "w", "user_id": "v", "display_name": "Avery"},
    ]
    service.snapshot = lambda: data
    window.account_dialog.snapshot = data
    opened = []

    def rpc(name, params):
        assert name == "start_direct_message" and params == {"p_workspace": "w", "p_user": "v"}
        opened.append(True)
        if len(opened) == 1:
            data["channels"].append(
                {
                    "id": "dm",
                    "workspace_id": "w",
                    "name": "",
                    "kind": "dm",
                    "private": True,
                    "dm_low": "u",
                    "dm_high": "v",
                }
            )
        return "dm"

    service.rpc = rpc
    monkeypatch.setattr(
        "aedrova.desktop.connected.choose_conversation",
        lambda _, people, buds: ("person", people[0]["user_id"]),
    )
    window.start_dm_button.click()
    qtbot.waitUntil(lambda: window.channel_id == "dm")
    assert window.dm_list.item(0).text().endswith("Avery")
    window.start_dm_button.click()
    qtbot.waitUntil(lambda: len(opened) == 2)
    assert len([c for c in window.workspace.channels if c.direct]) == 1


@pytest.mark.parametrize("include_workspace", [False, True])
def test_private_job_context_is_opt_in_and_retains_bud_personality(monkeypatch, include_workspace):

    from test_connected import snapshot

    from aedrova.agents.context import WorkspaceContext
    from aedrova.desktop.dot_analysis import QueryJob

    bud = dot()
    paths, gathered, prompts, closed = [], [], [], []
    context = WorkspaceContext("w", "u", frozenset({"c"}), "", 0, "Aedrova", "codex")

    def gather(*args, **kwargs):
        gathered.append(True)
        return context

    def retrieve(api, context, *args, **kwargs):
        assert kwargs["bud_id"] == bud["id"]
        assert context.channel_ids == (frozenset({"c"}) if include_workspace else frozenset())
        return context

    def run(self, provider, project, prompt, *, plan):
        assert plan is True
        prompts.append(prompt)
        evidence = (project / "context.jsonl").read_text()
        assert "My private question" in evidence
        assert "private_conversation" in evidence
        assert "Respond as the addressed Bud" in prompt
        assert "private conversation" in prompt
        return "A private draft."

    monkeypatch.setattr("aedrova.desktop.dot_analysis.gather", gather)
    monkeypatch.setattr("aedrova.desktop.dot_analysis.retrieve", retrieve)
    monkeypatch.setattr("aedrova.desktop.dot_analysis.application_ai_origin", lambda: "")
    monkeypatch.setattr("aedrova.agents.runtime.LocalRunner.run", run)

    def api_request(path, *args):
        paths.append(path)
        return {"items": [bud]}

    monkeypatch.setattr(
        "aedrova.desktop.dot_analysis.client",
        lambda _: SimpleNamespace(
            request=api_request,
        ),
    )
    service = SimpleNamespace(
        user=SimpleNamespace(id="u"),
        context_snapshot=lambda _: snapshot(),
        close_context=lambda: closed.append(True),
    )
    job = QueryJob(
        service,
        "w",
        "",
        "Help",
        "codex",
        bud=bud,
        private_history=[{"role": "user", "body": "My private question"}],
        include_workspace=include_workspace,
    )
    results = []
    job.signals.finished.connect(results.append)
    job.run()
    assert bool(gathered) == include_workspace
    assert results == [{"text": "A private draft."}] and closed == [True]
    assert len(prompts) == 1 and paths == ["/api/dots?workspace=w"]


def test_retry_does_not_duplicate_saved_question(qtbot, tmp_path):
    _, service, dialog, history, _ = ready_chat(qtbot, tmp_path)
    original = service.rpc
    failed = []

    def fail_once(name, params):
        if name == "append_bud_message" and not failed:
            failed.append(params["p_id"])
            raise TimeoutError()
        return original(name, params)

    service.rpc = fail_once
    answered = []
    dialog.answer = answered.append
    dialog.send("A private retry")
    qtbot.waitUntil(lambda: not dialog.busy)
    assert not dialog.retry.isHidden()
    dialog.retry.click()
    qtbot.waitUntil(lambda: len(answered) == 1)
    assert history[0]["id"] == failed[0]
    assert len(history) == 1


def test_private_reply_is_persisted_with_bud_identity_and_no_shared_feed(
    qtbot,
    tmp_path,
    monkeypatch,
):
    from test_connected import snapshot

    _, service, dialog, history, _ = ready_chat(qtbot, tmp_path)
    closed = []
    service.fork_for_context = lambda: SimpleNamespace(
        user=SimpleNamespace(id="u"),
        context_snapshot=lambda _: snapshot(),
        close_context=lambda: closed.append(True),
    )
    monkeypatch.setattr("aedrova.desktop.dot_analysis.application_ai_origin", lambda: "")
    monkeypatch.setattr(
        "aedrova.desktop.dot_analysis.client",
        lambda _: SimpleNamespace(
            request=lambda *_: {"items": [dialog.bud]},
        ),
    )
    monkeypatch.setattr(
        "aedrova.desktop.dot_analysis.retrieve", lambda api, context, *a, **k: context
    )
    monkeypatch.setattr("aedrova.agents.runtime.LocalRunner.run", lambda *a, **k: "A useful draft.")
    dialog.send("Please help")
    qtbot.waitUntil(lambda: len(dialog.history) == 2 and not dialog.busy)
    assert history[-1]["role"] == "assistant"
    assert history[-1]["body"] == "A useful draft."
    assert dialog.history == history and closed == [True]
    assert dialog.host.agent_feed.toPlainText() == ""
    assert dialog.composer.isEnabled()
