"""Real Qt input paths for selection, mention sends and the combined DM picker."""

import pytest
from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QApplication
from test_connected import setup
from test_dots import dot

from aedrova.desktop.conversation import Composer, MessageView
from aedrova.desktop.conversation_picker import ConversationPicker
from aedrova.desktop.state import Message


@pytest.mark.parametrize("accepted", [True, False])
@pytest.mark.parametrize("thread", [True, False])
def test_agent_token_send_clears_only_accepted_originating_composer(
    qtbot, tmp_path, monkeypatch, accepted, thread
):
    window, _ = setup(qtbot, tmp_path)
    bud = dot("Orbit")
    window.account_dialog.snapshot["dots"] = [bud]
    composer = window.thread_composer if thread else window.composer
    other = window.composer if thread else window.thread_composer
    composer.mention_tokens = {"Orbit": "<@dot:" + bud["id"] + "|Orbit>"}
    composer.editor.setPlainText("@Orbit hello")
    other.editor.setPlainText("@Orbit hello")
    monkeypatch.setattr("aedrova.desktop.dot_analysis.start_analysis", lambda *a, **k: accepted)
    composer._submit()
    assert composer.editor.toPlainText() == ("" if accepted else "@Orbit hello")
    assert other.editor.toPlainText() == "@Orbit hello"


def test_composer_never_clears_an_edited_revision_even_when_text_is_restored(qtbot):
    composer = Composer()
    qtbot.addWidget(composer)
    composer.editor.setPlainText("hello")
    composer._submit()
    composer.editor.insertPlainText("new")
    composer.editor.setPlainText("hello")
    assert not composer.clear_submission("hello")
    assert composer.editor.toPlainText() == "hello"


def test_inline_agent_and_private_bud_text_support_keyboard_copy(qtbot):
    from aedrova.desktop.agent_stream import ActivityRow

    row = ActivityRow("A real answer\nwith another line", author="Orbit")
    qtbot.addWidget(row)
    row.show()
    row.message.setFocus()
    row.message.setSelection(2, 11)
    qtbot.keySequence(row.message, QKeySequence.StandardKey.Copy)
    assert QApplication.clipboard().text() == "real answer"


def test_message_drag_copies_partial_multiline_unicode_and_keyboard_selection(qtbot):
    view = MessageView()
    qtbot.addWidget(view)
    view.resize(650, 400)
    view.show_messages([Message("m", "Avery", "A", "09:00", "Hello 👋 team\nSecond line")])
    view.show()
    qtbot.wait(30)
    index = view.model().index(0)
    rect = view.visualRect(index)
    top = rect.top() + view.delegate.body_offset(index)
    start = QPoint(75, int(top + 8))
    end = QPoint(145, int(top + 8))
    threads = []
    view.thread_requested.connect(threads.append)
    qtbot.mousePress(view.viewport(), Qt.MouseButton.LeftButton, pos=start)
    qtbot.mouseMove(view.viewport(), end)
    qtbot.mouseRelease(view.viewport(), Qt.MouseButton.LeftButton, pos=end)
    cursor = view.selection_cursor()
    assert cursor and cursor.hasSelection() and not threads
    view.copy_current()
    assert QApplication.clipboard().text() == cursor.selectedText()
    # Exercise actual paint with the rounded selection, then standard keyboard copy.
    assert not view.grab().isNull()
    view.setFocus()
    qtbot.keySequence(view, QKeySequence.StandardKey.SelectAll)
    qtbot.keySequence(view, QKeySequence.StandardKey.Copy)
    assert "Hello 👋 team" in QApplication.clipboard().text()
    assert "Second line" in QApplication.clipboard().text()
    qtbot.keyClick(view, Qt.Key.Key_Escape)
    assert view.text_selection is None


def test_picker_filters_sections_and_keeps_duplicate_names_as_distinct_ids(qtbot):
    buds = [dot("Avery"), {**dot("Research"), "id": "research"}]
    picker = ConversationPicker(None, [{"display_name": "Avery", "user_id": "person-id"}], buds)
    qtbot.addWidget(picker)
    assert picker.selection() == ("person", "person-id")
    picker.search.setText("Research")
    assert picker.selection() == ("bud", "research")
    assert picker.list.item(0).text() == "Buds"
    picker.search.setText("no match")
    assert picker.selection() is None and not picker.start.isEnabled()
    picker.search.clear()
    assert picker.list.count() == 5


def test_dm_picker_includes_buds_without_human_coworkers(qtbot, tmp_path, monkeypatch):
    window, service = setup(qtbot, tmp_path)
    bud = dot("Orbit")
    data = {**window.account_dialog.snapshot, "directory": [], "dots": [bud]}
    service.snapshot = lambda: data
    selected = []
    opened = []

    def choose(_, people, buds):
        selected.append((people, buds))
        return "bud", buds[0]["id"]

    monkeypatch.setattr("aedrova.desktop.connected.choose_conversation", choose)
    monkeypatch.setattr("aedrova.desktop.bud_chat.open_bud_chat", lambda _, id: opened.append(id))
    window.start_dm_button.click()
    qtbot.waitUntil(lambda: bool(opened))
    assert selected[0] == ([], [bud]) and opened == [bud["id"]]


def test_delayed_delivery_receipt_does_not_erase_same_text_new_draft(qtbot, tmp_path, monkeypatch):
    window, _ = setup(qtbot, tmp_path)
    callbacks = []
    monkeypatch.setattr(
        window.connected, "enqueue", lambda key, work, done, **kw: callbacks.append(done) or True
    )
    window.composer.editor.setPlainText("hello")
    window.composer._submit()
    assert not window.composer.editor.toPlainText()
    window.composer.editor.setPlainText("hello")
    callbacks[0](None)
    assert window.composer.editor.toPlainText() == "hello"


def test_retry_receipt_keeps_restored_text_if_user_edits_it(qtbot, tmp_path):
    import httpx

    window, service = setup(qtbot, tmp_path)
    calls = []

    def rpc(*args):
        calls.append(True)
        if len(calls) == 1:
            raise httpx.ConnectError("offline")

    service.rpc = rpc
    window.composer.editor.setPlainText("First message")
    window.send_message("First message")
    qtbot.waitUntil(lambda: len(calls) == 1 and not window.account_dialog.busy)
    window.composer.editor.setPlainText("My next thought")
    window.connected.retry_at = 0
    window.connected.refresh()
    qtbot.waitUntil(lambda: len(calls) == 2 and not window.account_dialog.busy)
    assert window.composer.editor.toPlainText() == "My next thought"
