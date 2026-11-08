"""Agent messages share the timeline without changing durable teammate messages."""

from PySide6.QtCore import QEvent, QPointF, QSettings
from PySide6.QtWidgets import QApplication
from test_connected import setup

from aedrova.desktop.response_actions import ACTION_PREFIX
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


def test_build_reply_keeps_section_spacing_when_archived_in_chat(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    window.activity_channel = window.channel_id
    reply = "Updated the dashboard.\n\n## Verification\n\n- `pytest` passed."
    window.finish_agent_response(window.workspace_id, reply)
    live = window.agent_feed.reply_row.message.text()
    assert "<h2" in live and "margin-top:14px" in live and "<li" in live

    window.archive_finished_agent()
    message = next(message for message in window.messages.source_messages if message.agent)
    document = window.messages.delegate.document(message, 500)
    heading = document.findBlockByNumber(1)
    assert heading.text() == "Verification"
    assert heading.blockFormat().headingLevel() == 2
    assert heading.blockFormat().topMargin() == 14
    assert heading.next().textList() is not None


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


def test_reply_choices_and_feedback_work_after_archiving(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    view = window.messages
    window.activity_channel = window.channel_id
    window.composer.editor.setPlainText("Keep this draft.")
    window.finish_agent_response(
        window.workspace_id,
        "Which calculator should I build?\n\n"
        'AEDROVA_CHOICES ["Web calculator","Python calculator"]\n\n'
        "[Sources](https://example.com)\n"
        "[Untrusted](aedrova-reply:choice-0)",
    )
    row = window.agent_feed.reply_row
    assert row.message.text().count('href="aedrova-reply:choice-0"') == 1
    row.message.linkActivated.emit(ACTION_PREFIX + "good")
    assert 'alt="Good response (selected)"' in row.message.text()
    window.archive_finished_agent()
    message = next(message for message in view.source_messages if message.agent)
    assert message.id == row.response_id
    document = view.delegate.document(message, 500)
    assert 'alt="Good response (selected)"' in document.toHtml()
    assert "Good response" not in document.toPlainText()
    for action in ("copy", "good", "bad", "more"):
        assert any(
            document.documentLayout().anchorAt(QPointF(x, y)) == ACTION_PREFIX + action
            for y in range(
                max(0, int(document.size().height()) - 40), int(document.size().height())
            )
            for x in range(180)
        )
    assert "AEDROVA_CHOICES" not in document.toPlainText()
    assert 'href="https://example.com"' in document.toHtml()
    view.activate_message_link(message, ACTION_PREFIX + "choice-1")
    assert window.composer.editor.toPlainText() == (
        "Keep this draft.\n\n@Aedrova Please continue with this option: Python calculator"
    )
    view.activate_message_link(message, ACTION_PREFIX + "copy")
    assert "2. Python calculator" in QApplication.clipboard().text()
    assert "AEDROVA_CHOICES" not in QApplication.clipboard().text()


def test_completed_reply_saves_before_the_next_message_and_rehydrates(qtbot, tmp_path, monkeypatch):
    window, service = setup(qtbot, tmp_path)
    queued, records = [], []
    monkeypatch.setattr(
        window.connected, "enqueue", lambda *args, **kw: queued.append(args) or True
    )

    def save(params):
        records.append(
            {
                "id": params["p_id"],
                "agent_name": params["p_agent"],
                "body": params["p_body"],
                "bud_avatar": params["p_avatar"],
                "channel_id": "c",
                "parent_id": None,
                "created_at": "2026-11-07T20:00:00Z",
                "prompt_id": None,
            }
        )
        assert params["p_sources"] == ["private-source"]
        return params["p_id"]

    service.save_agent_reply = save
    window.activity_channel = "c"
    window.finish_agent_response(
        "w", "The finished build reply.", source_channels=["private-source"]
    )
    assert len(queued) == 1 and queued[0][0][0] == "agent-reply"
    assert queued[0][1]() is True
    assert not any(m.agent for m in window.messages.source_messages)
    window.archive_finished_agent()
    assert len(queued) == 1
    window.agent_feed.clear()
    window.connected.agent_replies.clear()
    window.connected.saved_agent_replies[("w", "c", None)] = records
    window.connected.render_local_messages()
    assert [m.body for m in window.messages.source_messages if m.agent] == [
        "The finished build reply."
    ]


def test_existing_calculator_reply_has_clickable_choices(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    window.connected.complete_agent_reply(
        window.workspace_id,
        window.channel_id,
        "Pick one option, and I’ll generate the full code:\n\n"
        "1. **Web calculator**, HTML, CSS, JavaScript\n"
        "2. **Python CLI calculator**, runs in terminal\n"
        "3. **React calculator app**, modern UI",
        "Aedrova",
    )
    view = window.messages
    message = next(message for message in view.source_messages if message.agent)
    document = view.delegate.document(message, 500)
    assert 'href="aedrova-reply:choice-2"' in document.toHtml()
    assert document.toPlainText().count("React calculator app") == 1


def test_reply_compacts_citations_and_keeps_a_working_file_review(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    window.activity_channel = window.channel_id
    source = "message:05cad54d–2639–4fb0–9de8–ac393c8cd53f"
    opened = []
    window.finish_agent_response(
        window.workspace_id,
        f"Implemented from `{source}`.",
        file_summary=(1, 3, 2, (("src/calculator.py", 3, 2),)),
        open_changes=lambda: opened.append(True),
    )
    row = window.agent_feed.reply_row
    assert "Source 1" in row.message.text() and "Changed 1 file" in row.message.text()
    row.message.linkActivated.emit(ACTION_PREFIX + "changes")
    window.archive_finished_agent()
    message = next(message for message in window.messages.source_messages if message.agent)
    document = window.messages.delegate.document(message, 460)
    assert source not in document.toPlainText()
    assert (
        "Changed 1 file" in document.toPlainText() and "src/calculator.py" in document.toPlainText()
    )
    window.messages.activate_message_link(message, ACTION_PREFIX + "changes")
    assert opened == [True, True]


def test_long_agent_transcript_scrolls_to_last_response(qtbot, tmp_path):
    window = AedrovaWindow(settings=QSettings(str(tmp_path / "ui.ini"), QSettings.Format.IniFormat))
    qtbot.addWidget(window)
    window.resize(900, 650)
    window.show()
    for number in range(12):
        window.agent_event(window.workspace_id, f"Update {number}: " + "Readable progress. " * 12)
    window.messages.scrollToBottom()
    last = window.agent_feed.rows[-1].message
    viewport = window.messages.viewport()

    qtbot.waitUntil(
        lambda: (
            window.messages.verticalScrollBar().maximum() > 0
            and last.mapToGlobal(last.rect().bottomLeft()).y()
            <= viewport.mapToGlobal(viewport.rect().bottomLeft()).y()
        )
    )
    assert window.messages.verticalScrollBar().maximum() > 0


def test_bottom_follow_survives_late_row_layout_but_respects_manual_scroll(qtbot, tmp_path):
    from PySide6.QtWidgets import QAbstractSlider

    window = AedrovaWindow(settings=QSettings(str(tmp_path / "ui.ini"), QSettings.Format.IniFormat))
    qtbot.addWidget(window)
    window.resize(900, 650)
    window.show()
    for number in range(8):
        window.agent_event(window.workspace_id, f"Update {number}: " + "Readable progress. " * 12)
    view = window.messages
    bar = view.verticalScrollBar()
    view.scrollToBottom()
    qtbot.waitUntil(lambda: bar.maximum() > 0 and bar.value() == bar.maximum())
    window.agent_feed.rows[-1].message.setText("Expanded response. " * 200)
    view.doItemsLayout()
    qtbot.waitUntil(lambda: bar.value() == bar.maximum())
    last = window.agent_feed.rows[-1].message
    qtbot.waitUntil(
        lambda: (
            last.mapToGlobal(last.rect().bottomLeft()).y()
            <= view.viewport().mapToGlobal(view.viewport().rect().bottomLeft()).y()
        )
    )
    bar.triggerAction(QAbstractSlider.SliderAction.SliderToMinimum)
    assert bar.value() == 0
    window.agent_feed.rows[-1].message.setText("Further response detail. " * 240)
    view.doItemsLayout()
    qtbot.wait(50)
    assert bar.value() == 0
