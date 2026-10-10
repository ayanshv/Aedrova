"""User journeys for new chat controls, with actual Qt widgets and scoped transport."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtGui import QTextCursor
from test_connected import setup

from aedrova.desktop.collaboration import ChatPanel, message_link
from aedrova.desktop.conversation import Composer, SafeDocument, message_urls
from aedrova.desktop.window import AedrovaWindow
from aedrova.identity.link_preview import Metadata, fetch_preview, public_address


def local(qtbot, tmp_path):
    window = AedrovaWindow(settings=QSettings(str(tmp_path / "ui.ini"), QSettings.Format.IniFormat))
    qtbot.addWidget(window)
    window.show()
    return window


def test_rich_text_is_readable_and_html_is_literal(qtbot, tmp_path):
    window = local(qtbot, tmp_path)
    message = window.store.send(
        window.workspace_id,
        window.channel_id,
        "**Bold** and *italic* and `code`\n\n- List\n\n"
        "```python\nprint(1)\n```\n<script>alert(1)</script>",
    )
    document = window.messages.delegate.document(message, 400)
    assert isinstance(document, SafeDocument)
    plain = document.toPlainText()
    assert "**" not in plain
    assert "Bold" in plain and "print(1)" in plain and "<script>alert(1)</script>" in plain
    assert document.loadResource(2, SimpleNamespace()) is None


def test_local_edit_save_quote_and_forward_retains_threads(qtbot, tmp_path):
    window = local(qtbot, tmp_path)
    message = window.store.send(window.workspace_id, window.channel_id, "Original")
    window.store.send(window.workspace_id, window.channel_id, "Reply", message.id)
    window._load_channel()
    window.collaboration.action("saved", message.id)
    assert message.saved
    window.collaboration.action("quote", message.id)
    assert "> You\n> Original" in window.composer.editor.toPlainText()
    window.collaboration.edit(message)
    dialog = window.collaboration.dialogs[-1]
    from PySide6.QtWidgets import QPlainTextEdit, QPushButton

    dialog.findChild(QPlainTextEdit).setPlainText("Updated")
    next(b for b in dialog.findChildren(QPushButton) if b.text() == "Save changes").click()
    assert message.body == "Updated" and message.edited
    assert len(message.replies) == 1
    window.collaboration.action("saved", message.id)
    assert not message.saved


def test_mentions_display_names_but_send_user_ids(qtbot):
    composer = Composer()
    qtbot.addWidget(composer)
    composer.people = [
        {"user_id": "95000000-0000-0000-0000-000000000002", "display_name": "Maya Chen"}
    ]
    composer.editor.setPlainText("@May")
    cursor = composer.editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    composer.editor.setTextCursor(cursor)
    assert composer.mention_start() == 0
    composer.complete_mention()
    assert composer.editor.toPlainText() == "@Maya Chen "
    composer.editor.insertPlainText("hello")
    sent = []
    composer.submitted.connect(sent.append)
    composer._submit()
    assert sent == ["<@95000000-0000-0000-0000-000000000002|Maya Chen> hello"]
    composer.editor.setPlainText("@every")
    cursor = composer.editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    composer.editor.setTextCursor(cursor)
    composer.complete_mention()
    assert composer.editor.toPlainText() == "@everyone "


def test_request_captures_channel_and_updates_only_on_success(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    calls = []
    service.rpc = lambda name, data: calls.append((name, data)) or {}
    window.collaboration.request("edit", {"message": "m", "body": "Edited"})
    qtbot.waitUntil(lambda: not window.account_dialog.busy)
    assert calls[0] == (
        "chat_action",
        {"p_action": "edit", "p_data": {"message": "m", "body": "Edited"}},
    )


def test_inventory_callback_discarded_after_workspace_changes(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    service.chat_inventory = lambda *args: {"messages": []}
    results = []
    window.collaboration.inventory("query", "search", None, results.append)
    window.workspace_id = "another"
    qtbot.waitUntil(lambda: not window.account_dialog.busy)
    assert not results


def test_activity_typing_people_and_signout_clear_private_state(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    data = {
        "chat": {
            "people": [{"user_id": "other", "display_name": "Maya"}],
            "typing": [{"channel_id": "c", "user_id": "other"}],
            "unseen": 2,
        }
    }
    window.collaboration.sync(data)
    assert window.collaboration.typing_label.text() == "Maya is typing…"
    assert window.collaboration.activity_button.text() == "Activity · 2"
    assert window.composer.people[0]["display_name"] == "Maya"
    window.collaboration.panel("activity")
    window.connected.disconnect()
    window.collaboration.pulse()
    assert not window.composer.people
    assert not window.collaboration.dialogs
    assert not window.collaboration.typing_label.text()


def test_saved_search_files_and_empty_state(qtbot, tmp_path):
    window = local(qtbot, tmp_path)
    window.collaboration.action("saved", "p2")
    data = window.collaboration.local_inventory("onboarding", "saved", None)
    assert len(data["messages"]) == 1 and data["messages"][0]["id"] == "p2"
    panel = ChatPanel(window.collaboration, "saved")
    qtbot.addWidget(panel)
    panel.show()
    panel.load()
    assert panel.results.count() == 1
    panel.search.setText("does-not-exist")
    panel.load()
    assert panel.results.count() == 0 and panel.notice.text() == "Nothing here yet."


def test_dropped_files_preserve_thread_destination(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    upload = Mock()
    window.connected.upload = upload
    path = tmp_path / "a.txt"
    path.write_text("a")
    window.thread_id = "root"
    window.collaboration.drop_files([str(path)], window.thread_messages)
    upload.assert_called_once_with(str(path), parent="root")


def test_links_only_navigate_accessible_channels(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    current = window.channel_id
    window.collaboration.open_link(
        message_link(
            "95000000-0000-0000-0000-000000000001",
            "95000000-0000-0000-0000-000000000002",
            "95000000-0000-0000-0000-000000000003",
        )
    )
    assert window.channel_id == current
    assert "unavailable" in window.notice.text()
    assert len(message_urls("https://example.com/a https://example.com/a")) == 1


def test_preview_rejects_private_redirects_and_non_https(monkeypatch):
    monkeypatch.setattr(
        "socket.getaddrinfo", lambda *a, **k: [(None, None, None, None, ("127.0.0.1", 443))]
    )
    with pytest.raises(ValueError):
        public_address("localhost")
    for url in [
        "http://example.com",
        "file:///etc/passwd",
        "https://user:secret@example.com",
        "https://example.com:8443",
    ]:
        with pytest.raises(ValueError):
            fetch_preview(url)
    metadata = Metadata()
    metadata.feed('<title>Example</title><meta property="og:description" content="A description">')
    assert metadata.title == "Example" and metadata.description == "A description"


def test_revoked_channels_close_collaboration_views(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    window.collaboration.sync({"channels": [{"id": "c"}], "chat": {"workspace_id": "w"}})
    window.collaboration.panel("saved")
    assert window.collaboration.dialogs
    window.collaboration.sync({"channels": [], "chat": {"workspace_id": "w"}})
    assert not window.collaboration.dialogs
