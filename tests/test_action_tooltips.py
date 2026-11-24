"""Reply icon tooltips: one at a time, after a pause, and always matching the icon."""

import pytest
from PySide6.QtWidgets import QWidget

from aedrova.desktop.response_actions import ACTION_PREFIX, HoverTip, reply_action_label


def test_labels_match_what_the_icon_shows_now():
    copy, good, bad = (ACTION_PREFIX + name for name in ("copy", "good", "bad"))
    assert reply_action_label(copy) == "Copy response"
    assert reply_action_label(copy, copied=True) == "Copied"
    assert reply_action_label(good) == "Good response"
    assert reply_action_label(good, rating="good") == "Good response (selected)"
    assert reply_action_label(bad, rating="good") == "Bad response"
    assert reply_action_label(ACTION_PREFIX + "pdf").startswith("Save the full response")
    assert reply_action_label(ACTION_PREFIX + "more") is None  # the removed menu button
    assert reply_action_label("https://example.com") is None


@pytest.fixture
def shown(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "PySide6.QtWidgets.QToolTip.showText", lambda pos, text, widget=None: calls.append(text)
    )
    monkeypatch.setattr("PySide6.QtWidgets.QToolTip.hideText", lambda: None)
    monkeypatch.setattr(HoverTip, "DELAY", 30)
    return calls


def test_staying_on_one_icon_shows_one_tooltip_once(qtbot, shown):
    owner = QWidget()
    qtbot.addWidget(owner)
    tip = HoverTip(owner)
    tip.timer.setInterval(30)
    for _ in range(20):  # the pointer jitters over the same icon
        tip.move(("copy", "Copy response"), "Copy response", owner)
    qtbot.wait(120)
    assert shown == ["Copy response"]


def test_crossing_several_icons_quickly_shows_only_the_one_you_stop_on(qtbot, shown):
    owner = QWidget()
    qtbot.addWidget(owner)
    tip = HoverTip(owner)
    tip.timer.setInterval(60)
    for key, text in (
        ("copy", "Copy response"),
        ("good", "Good response"),
        ("bad", "Bad response"),
    ):
        tip.move((key, text), text, owner)
        qtbot.wait(10)  # well under the pause: nothing may flash
    assert shown == []
    qtbot.wait(150)
    assert shown == ["Bad response"]


def test_leaving_cancels_a_pending_tooltip_and_allows_the_next_one(qtbot, shown):
    owner = QWidget()
    qtbot.addWidget(owner)
    tip = HoverTip(owner)
    tip.timer.setInterval(40)
    tip.move(("copy", "Copy response"), "Copy response", owner)
    tip.leave()
    qtbot.wait(120)
    assert shown == []
    tip.move(("copy", "Copy response"), "Copy response", owner)
    qtbot.wait(120)
    assert shown == ["Copy response"]


def test_a_changed_label_on_the_same_icon_is_shown_fresh(qtbot, shown):
    owner = QWidget()
    qtbot.addWidget(owner)
    tip = HoverTip(owner)
    tip.timer.setInterval(30)
    tip.move(("copy", "Copy response"), "Copy response", owner)
    qtbot.wait(100)
    tip.move(("copy", "Copied"), "Copied", owner)  # the icon turned into a check
    qtbot.wait(100)
    assert shown == ["Copy response", "Copied"]


def test_the_live_reply_uses_the_paced_current_label(qtbot, tmp_path, shown):
    from test_connected import setup

    window, _ = setup(qtbot, tmp_path)
    window.activity_channel = window.channel_id
    window.finish_agent_response(window.workspace_id, "A short answer.")
    row = window.agent_feed.reply_row
    row.hover_tip = HoverTip(row)
    row.hover_tip.timer.setInterval(30)
    for _ in range(10):
        row.show_action_tooltip(ACTION_PREFIX + "copy")
    row.copied = True
    row.show_action_tooltip(ACTION_PREFIX + "copy")
    qtbot.wait(120)
    assert shown == ["Copied"]  # the stale "Copy response" never appeared
    row.show_action_tooltip("")
    qtbot.wait(80)
    assert shown == ["Copied"]


def test_icons_carry_no_native_title_tooltip_that_could_double_up():
    from PySide6.QtGui import QTextDocument

    from aedrova.desktop.response_actions import append_response_actions

    document = QTextDocument()
    document.setPlainText("Answer")
    append_response_actions(document, (), "", long_words=900)
    html = document.toHtml()
    assert 'title="' not in html and 'alt="Copy response"' in html
