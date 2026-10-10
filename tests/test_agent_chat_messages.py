"""Agent messages share the timeline without changing durable teammate messages."""

from PySide6.QtCore import QEvent, QSettings
from PySide6.QtWidgets import QApplication
from test_connected import setup

from aedrova.desktop.state import Message
from aedrova.desktop.window import AedrovaWindow


def test_named_agent_message_has_readable_sender_and_timestamp(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    window.account_dialog.snapshot["agent_preferences"] = [
        {"workspace_id": "w", "nickname": "Atlas"}
    ]
    window.agent_event("w", "I’ll review the team’s decisions.\n\nThen I’ll build the changes.")
    row = window.agent_feed.rows[-1]
    assert row.author.text() == "Atlas"
    assert "AM" in row.timestamp.text() or "PM" in row.timestamp.text()
    assert row.timestamp.toolTip()
    assert row.message.font().pixelSize() == 14
    assert window.messages.isAncestorOf(row)
    assert row.message.text().count("\n") == 2


def test_realtime_refresh_preserves_widget_and_message_order(qtbot, tmp_path):
    window = AedrovaWindow(settings=QSettings(str(tmp_path / "ui.ini"), QSettings.Format.IniFormat))
    qtbot.addWidget(window)
    first = Message("one", "Teammate", "T", "10:00 AM", "Build this feature.")
    later = Message("two", "Teammate", "T", "10:01 AM", "Another detail.")
    window.messages.show_messages([first])
    window.agent_event(window.workspace_id, "Working on the feature.")
    identifier = window.messages.agent_message_id
    for _ in range(3):
        window.messages.show_messages([first, later])
        QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        qtbot.wait(10)
        assert window.agent_feed.toPlainText() == "Working on the feature."
        assert [m.id for m in window.messages.model().messages] == ["one", identifier, "two"]
    window.agent_event(window.workspace_id, "Running: python3 -m pytest")
    window.agent_feed.rows[-1].toggle.click()
    assert window.agent_feed.rows[-1].details.isVisibleTo(window.agent_feed)
    assert window.messages.source_messages == [first, later]


def test_agent_reply_does_not_follow_user_into_another_channel(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    window.agent_event("w", "Private build update")
    origin = window.channel_id
    window.channel_id = "different-channel"
    window.messages.set_agent_visible(window.activity_channel == window.channel_id)
    window.messages.show_messages([])
    assert window.messages.model().rowCount() == 0
    window.agent_event("w", "Another private update")
    assert window.messages.model().rowCount() == 0
    window.channel_id = origin
    window.messages.set_agent_visible(True)
    assert window.messages.model().rowCount() == 1
    assert "Another private update" in window.agent_feed.toPlainText()


def test_long_agent_transcript_scrolls_to_last_response(qtbot, tmp_path):
    window = AedrovaWindow(settings=QSettings(str(tmp_path / "ui.ini"), QSettings.Format.IniFormat))
    qtbot.addWidget(window)
    window.resize(900, 650)
    window.show()
    for number in range(12):
        window.agent_event(window.workspace_id, f"Update {number}: " + "Readable progress. " * 12)
    window.messages.scrollToBottom()
    qtbot.wait(100)
    last = window.agent_feed.rows[-1].message
    bottom = last.mapToGlobal(last.rect().bottomLeft()).y()
    viewport = window.messages.viewport()
    assert bottom <= viewport.mapToGlobal(viewport.rect().bottomLeft()).y()
    assert window.messages.verticalScrollBar().maximum() > 0
