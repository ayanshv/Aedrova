"""Workspace mentions and the changing agent transcript's physical scroll boundary."""

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import QApplication
from test_connected import setup

from aedrova.agents.context import build_command
from aedrova.desktop.agent_stream import AgentStream
from aedrova.desktop.conversation import Composer, MessageView


@pytest.mark.parametrize(
    "name,prefix", [("Atlas", "@at"), ("Team Pilot", "@team p"), ("Élan", "@é")]
)
@pytest.mark.parametrize("key", [Qt.Key.Key_Tab, Qt.Key.Key_Return])
def test_custom_mention_completion_is_the_build_command(qtbot, name, prefix, key):
    composer = Composer()
    qtbot.addWidget(composer)
    composer.show()
    composer.set_agent_name(name)
    sent = []
    composer.submitted.connect(sent.append)
    composer.editor.setPlainText(prefix)
    cursor = composer.editor.textCursor()
    cursor.movePosition(cursor.MoveOperation.End)
    composer.editor.setTextCursor(cursor)
    assert composer.suggestion.isVisible()
    assert composer.suggestion.text().startswith("@" + name)
    qtbot.keyClick(composer.editor, key)
    assert composer.editor.toPlainText() == "@" + name + " "
    assert not sent
    assert build_command("@" + name + " build the feature", name) == "the feature"
    assert build_command("@Aedrova build the feature", name) == "the feature"
    composer.editor.setPlainText("email@example.com")
    assert composer.suggestion.isHidden()


def test_workspace_name_updates_both_composers_and_click(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    window.account_dialog.snapshot["agent_preferences"] = [
        {"workspace_id": "w", "nickname": "Atlas"},
        {"workspace_id": "other", "nickname": "Pilot"},
    ]
    window._load_channel()
    for composer in (window.composer, window.thread_composer):
        assert composer.agent_name == "Atlas"
        composer.editor.clear()
        composer.mention.click()
        assert composer.editor.toPlainText() == "@Atlas "
        assert "Atlas" in composer.mention.accessibleName()
    window.account_dialog.snapshot["agent_preferences"][0]["nickname"] = "Orbit"
    window._load_channel()
    assert window.composer.agent_name == window.thread_composer.agent_name == "Orbit"
    window.account_dialog.snapshot["agent_preferences"] = []
    window._load_channel()
    assert window.composer.agent_name == "Aedrova"


def scroll_past_bottom(view):
    viewport = view.viewport()
    event = QWheelEvent(
        QPointF(20, 20), QPointF(viewport.mapToGlobal(QPoint(20, 20))),
        QPoint(0, -240), QPoint(0, -120), Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier, Qt.ScrollPhase.ScrollUpdate, False,
    )
    QApplication.sendEvent(viewport, event)


def test_transcript_shrink_resize_and_repeated_scroll_stop_at_final_message(qtbot):
    view = MessageView()
    feed = AgentStream()
    view.attach_agent_feed(feed)
    qtbot.addWidget(view)
    view.resize(700, 400)
    view.show()
    view.set_agent_visible(True)
    for number in range(12):
        feed.appendPlainText(f"Update {number}: " + "Readable progress. " * 12)
    qtbot.wait(50)
    view.scrollToBottom()
    qtbot.wait(50)
    assert view.verticalScrollBar().maximum() > 0
    for text in ("Final result. " * 200, "Finished. Here is the result."):
        feed.finish_with_result(text)
        view.set_agent_visible(True)
        for width in (450, 900):
            view.resize(width, 400)
            qtbot.wait(50)
            view.scrollToBottom()
            qtbot.wait(50)
            for _ in range(8):
                scroll_past_bottom(view)
                scroll_past_bottom(feed)
            qtbot.wait(30)
            bar = view.verticalScrollBar()
            assert bar.value() == bar.maximum()
            last = feed.rows[-1]
            bottom = last.mapToGlobal(last.rect().bottomLeft()).y()
            top = view.viewport().mapToGlobal(QPoint(0, 0)).y()
            assert top <= bottom <= top + view.viewport().height()
            if len(text) > 100:
                assert bottom >= top + view.viewport().height() - 3
            else:
                assert bar.maximum() == 0
            assert feed.height() == view.visualRect(view.model().index(0)).height()
