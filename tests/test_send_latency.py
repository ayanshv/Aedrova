"""Local echoes remain usable while delivery waits, and never duplicate after acknowledgment."""

from threading import Event

from test_reaction_latency import ready


def test_instant_echo_before_dispatch_then_slow_delivery(qtbot, tmp_path):
    window, service = ready(qtbot, tmp_path)
    entered, release = Event(), Event()
    writes = []

    def rpc(name, params):
        if name == "send_message":
            writes.append(params)
            entered.set()
            assert release.wait(5)
        return params.get("p_id")

    service.rpc = rpc
    resets = []
    window.messages.model().modelReset.connect(lambda: resets.append(True))
    try:
        window.composer.editor.setPlainText("Instant message")
        window.send_message("Instant message")
        message = window.channel.messages[-1]
        assert message.body == "Instant message"
        assert not window.composer.editor.toPlainText()
        assert not entered.is_set()  # The echo precedes even network dispatch.
        assert message.id in window.messages.send_animations
        assert not resets  # Existing rows aren't reconstructed for a tail append.
        qtbot.waitUntil(entered.is_set)
        window.composer.editor.setPlainText("Next draft")
        assert window.channel.messages[-1].body == "Instant message"
    finally:
        release.set()
    qtbot.waitUntil(lambda: not window.account_dialog.busy)
    assert window.composer.editor.toPlainText() == "Next draft"
    assert not window.connected.outbox[message.id]["delivery"]
    assert len([m for m in window.channel.messages if m.id == message.id]) == 1


def test_reduce_motion_and_reply_echo(qtbot, tmp_path):
    window, _ = ready(qtbot, tmp_path)
    window.set_reduced_motion(True)
    window.open_thread("m")
    window.thread_composer.editor.setPlainText("Immediate reply")
    window.send_reply("Immediate reply")
    reply = window.channel.messages[0].replies[-1]
    assert reply.body == "Immediate reply"
    assert not window.thread_composer.editor.toPlainText()
    assert not window.thread_messages.send_animations


def test_delivery_acknowledgment_does_not_change_message_grouping(qtbot, tmp_path):
    from aedrova.desktop.state import Message

    window, _ = ready(qtbot, tmp_path)
    first = Message("first", "You", "Y", "2026-10-07 12:00", "First", mine=True, sender_id="u")
    second = Message(
        "second",
        "You",
        "Y",
        "2026-10-07 12:00",
        "Second",
        mine=True,
        sender_id="u",
        delivery="Sending…",
    )
    window.messages.show_messages([first, second])
    index = window.messages.model().index(1)
    assert window.messages.delegate.grouped(index)
    second.delivery = ""
    assert window.messages.delegate.grouped(index)
    second.delivery = "Not sent · retry"
    assert not window.messages.delegate.grouped(index)
