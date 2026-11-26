"""The "New messages" line and the arrow that returns to it."""

import pytest

from aedrova.desktop.conversation import UNREAD_HEIGHT, MessageView
from aedrova.desktop.state import Message
from aedrova.desktop.theme import DARK, LIGHT


def messages(count=30):
    return [
        Message(f"m{i}", "Maya" if i % 2 else "Jamie", "M", "9:00 AM", f"Message {i}\n\nmore")
        for i in range(count)
    ]


def make_view(qtbot, theme=LIGHT):
    view = MessageView()
    qtbot.addWidget(view)
    view.delegate.theme = theme
    view.resize(700, 480)
    view.show()
    view.show_messages(messages())
    return view


def test_the_first_unread_message_gets_room_for_the_line(qtbot):
    view = make_view(qtbot)
    plain = view.delegate.sizeHint(None, view.model().index(10)).height()
    view.set_unread("m10")
    assert view.delegate.sizeHint(None, view.model().index(10)).height() == plain + UNREAD_HEIGHT
    assert view.delegate.sizeHint(None, view.model().index(11)).height() > 0


def test_the_unread_message_always_shows_its_author(qtbot):
    view = make_view(qtbot)
    view.set_unread("m10")
    assert not view.delegate.grouped(view.model().index(10))


def test_clearing_the_line_removes_the_room(qtbot):
    view = make_view(qtbot)
    plain = view.delegate.sizeHint(None, view.model().index(10)).height()
    view.set_unread("m10")
    view.set_unread("")
    assert view.delegate.sizeHint(None, view.model().index(10)).height() == plain


def test_the_arrow_shows_only_while_the_line_is_above_the_screen(qtbot):
    view = make_view(qtbot)
    view.set_unread("m3")
    view.verticalScrollBar().setValue(0)
    view.update_unread_jump()
    assert not view.unread_jump.isVisible()
    view.scrollToBottom()
    view.update_unread_jump()
    assert view.unread_jump.isVisible()


def test_the_arrow_returns_to_the_line_and_then_hides(qtbot):
    view = make_view(qtbot)
    view.set_unread("m3")
    view.scrollToBottom()
    view.update_unread_jump()
    view.jump_to_unread()
    qtbot.wait(50)
    view.update_unread_jump()
    assert not view.unread_jump.isVisible()
    index = view.unread_index()
    assert view.visualRect(index).top() <= 4


def test_no_line_means_no_arrow(qtbot):
    view = make_view(qtbot)
    view.scrollToBottom()
    view.update_unread_jump()
    assert not view.unread_jump.isVisible()


@pytest.mark.parametrize("theme", [LIGHT, DARK])
def test_the_line_paints(qtbot, theme):
    view = make_view(qtbot, theme)
    view.set_unread("m8")
    image = view.grab().toImage()
    assert not image.isNull()
