"""Mentions anywhere retain their full prompt and the ordinary message receipt."""

from datetime import UTC, datetime

import pytest
from test_connected import row, setup
from test_dots import dot

from aedrova.agents.context import build_command


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("hey @aedrova wya", "hey wya"),
        ("Can you @NOVA explain this?", "Can you explain this?"),
        ("@Aedrova, hello", "hello"),
        ("Please help @Aedrova", "Please help"),
        ("Ask @Aedrova-bot later", None),
        ("mail@Aedrova.com", None),
        ("@@Aedrova hello", None),
        ("ordinary team chat", None),
        ("@Novation hello", None),
    ],
)
def test_explicit_mentions_anywhere_keep_surrounding_text(text, expected):
    assert build_command(text, "Nova") == expected


@pytest.mark.parametrize("thread", [False, True])
def test_prompt_survives_thinking_result_second_prompt_and_refresh(
    qtbot, tmp_path, monkeypatch, thread
):
    window, service = setup(qtbot, tmp_path)
    qtbot.waitUntil(
        lambda: (
            bool(window.channel.messages)
            and not window.connected.current_action
            and not window.connected.queue
        )
    )
    saved = [row()]
    calls = []

    def rpc(name, params):
        if name == "send_message":
            calls.append(dict(params))
            saved.append(
                {
                    "id": params["p_id"],
                    "sender_id": "u",
                    "body": params["p_body"],
                    "channel_id": "c",
                    "parent_id": params["p_parent"],
                    "sequence": len(saved) + 1,
                    "created_at": datetime.now(UTC).isoformat(),
                }
            )
        return None

    service.rpc = rpc
    service.message_page = lambda *args, **kwargs: list(saved)
    requests = []

    def answer(w, task, **kwargs):
        requests.append(task)
        w.activity_channel = "c"
        w.agent_activity("w", "Thinking…")
        return True

    monkeypatch.setattr("aedrova.desktop.dot_analysis.start_analysis", answer)
    composer = window.thread_composer if thread else window.composer
    if thread:
        window.thread_id = "m"
    submit = window.send_reply if thread else window.send_message
    texts = ["hey @aedrova wya", "also @Aedrova explain that"]
    for text in texts:
        composer.editor.setPlainText(text)
        submit(text)
        assert composer.editor.toPlainText() == ""
        # Local echo is present before the asynchronous backend has acknowledged it.
        assert any(item["body"] == text for item in window.connected.outbox.values())
        view = window.thread_messages if thread else window.messages
        assert text in [item.body for item in view.conversation_model.messages]
        window.finish_agent_response("w", "Here is the answer.")
        qtbot.waitUntil(lambda: not window.connected.current_action and not window.connected.queue)
        window.connected.refresh()
        qtbot.waitUntil(lambda: not window.connected.current_action and not window.connected.queue)
        window.connected.render_local_messages()
        messages = [m for root in window.channel.messages for m in [root, *root.replies]]
        assert all(t in [m.body for m in messages] for t in texts[: len(calls)])
    assert requests == ["hey wya", "also explain that"]
    assert len(calls) == 2 and len({c["p_id"] for c in calls}) == 2
    assert all(c["p_parent"] == ("m" if thread else None) for c in calls)


def test_bud_with_preceding_text_keeps_identity_and_full_request(qtbot, tmp_path, monkeypatch):
    window, _ = setup(qtbot, tmp_path)
    bud = dot()
    window.account_dialog.snapshot["dots"] = [bud]
    requests = []
    monkeypatch.setattr(
        "aedrova.desktop.dot_analysis.start_analysis",
        lambda w, task, **kw: requests.append((task, kw.get("bud"))) or True,
    )
    text = "hey @GitHub what changed?"
    window.composer.editor.setPlainText(text)
    window.send_message(text)
    assert requests == [("hey what changed?", bud)]
    assert any(m.body == text for m in window.channel.messages)


def test_rejected_agent_request_retains_draft_without_false_sent_message(
    qtbot, tmp_path, monkeypatch
):
    window, _ = setup(qtbot, tmp_path)
    monkeypatch.setattr(
        "aedrova.desktop.dot_analysis.start_analysis", lambda *args, **kwargs: False
    )
    text = "hey @Aedrova hello"
    window.composer.editor.setPlainText(text)
    window.send_message(text)
    assert window.composer.editor.toPlainText() == text
    assert not window.connected.outbox


def test_accepted_slash_command_remains_private(qtbot, tmp_path, monkeypatch):
    window, _ = setup(qtbot, tmp_path)
    monkeypatch.setattr("aedrova.desktop.builds.open_build", lambda *args, **kwargs: True)
    window.composer.editor.setPlainText("/build private task")
    window.send_message("/build private task")
    assert window.composer.editor.toPlainText() == ""
    assert not window.connected.outbox
