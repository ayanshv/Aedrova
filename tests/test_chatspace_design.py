"""Regression journeys for the redesigned conversation and navigation."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QStyleOptionViewItem
from test_connected import setup

from aedrova.desktop.conversation import MessageView, font, reaction_chips
from aedrova.desktop.state import Message


def test_grouped_message_keeps_its_own_reaction_and_thread_target(qtbot):
    view = MessageView()
    qtbot.addWidget(view)
    view.resize(680, 400)
    first = Message("one", "Maya", "MC", "2026-10-06 09:00", "A first thought.", sender_id="maya")
    second = Message(
        "two",
        "Maya",
        "MC",
        "2026-10-06 09:01",
        "And the next detail.",
        sender_id="maya",
        reactions=[{"emoji": "👍", "count": 1, "mine": False}],
    )
    view.show_messages([first, second])
    view.show()
    qtbot.wait(10)
    model = view.model()
    index = model.index(1, 0)
    assert view.delegate.grouped(index)
    option = QStyleOptionViewItem()
    assert (
        view.delegate.sizeHint(option, index).height()
        < view.delegate.sizeHint(option, model.index(0, 0)).height() + 30
    )
    seen = []
    view.reaction_requested.connect(lambda *args: seen.append(args))
    rect = view.visualRect(index)
    doc = view.delegate.document(second, rect.width() - 94)
    top = rect.top() + view.delegate.body_offset(index) + doc.size().height() + 8
    chip = reaction_chips(second, rect.width(), top)[0][0]
    qtbot.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, pos=chip.center().toPoint())
    assert seen == [("two", "👍", True)]
    replies = []
    view.thread_requested.connect(replies.append)
    qtbot.mouseClick(
        view.viewport(), Qt.MouseButton.LeftButton, pos=rect.topLeft() + view.rect().topLeft()
    )
    assert replies == ["two"]


def test_grouping_respects_sender_identity_day_and_message_metadata(qtbot):
    view = MessageView()
    qtbot.addWidget(view)
    messages = [
        Message("a", "Alex", "A", "2026-10-06 09:00", "One", sender_id="a"),
        Message("b", "Alex", "A", "2026-10-06 09:01", "Two", sender_id="b"),
        Message("c", "Alex", "A", "2026-10-07 09:01", "Three", sender_id="b"),
        Message("d", "Alex", "A", "2026-10-07 09:02", "Four", sender_id="b", edited=True),
        Message("e", "Alex", "A", "2026-10-07 09:03", "Five", sender_id="b"),
    ]
    view.show_messages(messages)
    assert [view.delegate.grouped(view.model().index(i, 0)) for i in range(5)] == [
        False,
        False,
        False,
        False,
        True,
    ]
    assert (
        view.delegate.body_offset(view.model().index(3, 0)) > QFontMetrics(font(14, True)).height()
    )


def test_workspace_tools_are_keyboard_reachable_with_a_quiet_rail(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    window.show()
    assert window.workspace_tools.isHidden()
    window.workspace_tools_toggle.setFocus()
    qtbot.keyClick(window.workspace_tools_toggle, Qt.Key.Key_Space)
    assert window.memory_button.isVisible() and window.build_history.isVisible()
    assert window.collaboration.activity_button.isVisible()
    assert len([b for b in window.workspace_buttons.values() if b.isVisible()]) == 1


def test_pin_icon_next_to_reactions_routes_the_hovered_message(qtbot):
    view = MessageView()
    qtbot.addWidget(view)
    view.resize(680, 400)
    message = Message("pin-target", "Maya", "MC", "09:00", "Keep this handy")
    view.show_messages([message])
    view.show()
    qtbot.wait(10)
    qtbot.mouseMove(view.viewport(), view.visualRect(view.model().index(0, 0)).center())
    assert view.pin_button.isVisible()
    assert view.pin_button.toolTip() == "Pin message"
    assert not view.pin_button.icon().isNull()
    actions = []
    view.action_requested.connect(lambda action, identifier: actions.append((action, identifier)))
    view.pin_button.click()
    assert actions == [("pinned", "pin-target")]
    assert not message.pinned and not view.pin_button.isChecked()
    message.pinned = True
    view.update_pin_action(message)
    assert view.pin_button.isChecked() and view.pin_button.toolTip() == "Unpin message"
    view.hover_message = "removed-from-this-channel"
    view.pin_button.click()
    assert len(actions) == 1


def test_pin_icon_uses_existing_local_and_shared_pin_operations(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    window.connected.timer.stop()
    qtbot.waitUntil(lambda: bool(window.channel.messages))
    message = window.channel.messages[0]
    view = window.messages
    view.hover_message = message.id
    calls = []
    service.rpc = lambda name, parameters: calls.append((name, parameters)) or {}
    view.pin_button.click()
    qtbot.waitUntil(lambda: bool(calls))
    assert calls[0] == (
        "chat_action",
        {"p_action": "pinned", "p_data": {"message": message.id, "present": True}},
    )


def test_pin_icon_toggles_local_pin_and_pinned_message_strip(qtbot, tmp_path):
    from test_chat_collaboration import local

    window = local(qtbot, tmp_path)
    message = window.store.send(window.workspace_id, window.channel_id, "An important update")
    window._load_channel()
    window.messages.hover_message = message.id
    window.messages.pin_button.click()
    assert message.pinned and not window.pinned.isHidden()
    window.messages.pin_button.click()
    assert not message.pinned
