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


@pytest.mark.parametrize(
    "chosen,observed,idle,minimized,expected,action",
    [
        ("online", "busy", False, False, "online", "profile"),
        ("online", "online", True, False, "away", "profile"),
        ("online", "away", False, False, "online", "profile"),
        ("away", "away", False, False, "away", "heartbeat"),
        ("busy", "busy", True, False, "busy", "heartbeat"),
        ("online", "online", False, True, "away", "profile"),
        ("online", "online", False, False, "online", "heartbeat"),
    ],
)
def test_presence_respects_manual_intent_and_idle(
    qtbot, tmp_path, monkeypatch, chosen, observed, idle, minimized, expected, action
):
    window, service = setup(qtbot, tmp_path)
    service.collaboration_available = True
    collaboration = window.collaboration
    collaboration.timer.stop()
    collaboration.data = {"people": [{"user_id": "u", "availability": observed, "status": "Focus"}]}
    collaboration.last_availability = chosen
    collaboration.last_heartbeat = 0
    collaboration.last_input = 600 if idle else 1000
    monkeypatch.setattr("aedrova.desktop.collaboration.time.monotonic", lambda: 1000)
    monkeypatch.setattr(window, "isVisible", lambda: True)
    monkeypatch.setattr(window, "isMinimized", lambda: minimized)
    calls = []
    monkeypatch.setattr(collaboration, "request", lambda *args: calls.append(args))
    collaboration.pulse()
    assert calls[0][0] == action
    if action == "profile":
        assert calls[0][1] == {"status": "Focus", "availability": expected}
    else:
        assert calls[0][1] == {}
    assert collaboration.last_availability == chosen


def test_confirmed_status_updates_own_cache_only(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    collaboration = window.collaboration
    collaboration.data = {
        "people": [
            {"user_id": "u", "availability": "busy"},
            {"user_id": "other", "availability": "away"},
        ]
    }
    collaboration.remember_status({"availability": "online", "status": "Available"})
    assert collaboration.last_availability == "online"
    assert collaboration.data["people"][0]["status"] == "Available"
    assert collaboration.data["people"][1]["availability"] == "away"
    assert window.account_dialog.snapshot["user_profile"]["availability"] == "online"


def test_team_presence_displays_all_statuses(qtbot, tmp_path):
    window = local(qtbot, tmp_path)
    panel = ChatPanel(window.collaboration, "people")
    qtbot.addWidget(panel)
    panel.loaded(
        {
            "people": [
                {"user_id": str(i), "display_name": name, "availability": value}
                for i, (name, value) in enumerate(
                    [("Maya", "online"), ("Sam", "away"), ("Lee", "busy"), ("Jo", "offline")]
                )
            ]
        }
    )
    assert [panel.results.item(i).text().split("\n")[0] for i in range(4)] == [
        "Maya · Online",
        "Sam · Away",
        "Lee · Do not disturb",
        "Jo · Offline",
    ]


def test_people_tab_is_scoped_and_retargets_on_channel_switch(qtbot, tmp_path, monkeypatch):
    window, _ = setup(qtbot, tmp_path)
    calls = []
    monkeypatch.setattr(
        window.collaboration, "inventory", lambda q, s, c, done: calls.append((c, done))
    )
    window.select_tab(4)
    qtbot.waitUntil(lambda: bool(calls))
    page = window.pages.currentWidget()
    assert window.tab_buttons[4].text() == "People"
    assert page.channel == "c" and calls[-1][0] == "c"
    calls[-1][1](
        {"people": [{"user_id": "peer", "display_name": "Maya", "availability": "online"}]}
    )
    assert page.results.count() == 1
    assert not page.results.item(0).icon().isNull()
    stale = calls[-1][1]
    window.select_tab(0)
    next_channel = window.store.add_channel(window.workspace_id, "private-new")
    window.channel_id = next_channel.id
    window.select_tab(4)
    assert page.channel == next_channel.id and page.results.count() == 0
    stale({"people": [{"user_id": "old", "display_name": "Old conversation"}]})
    assert page.results.count() == 0
    qtbot.waitUntil(lambda: calls[-1][0] == next_channel.id)
    window.connected.disconnect()
    assert page.results.count() == 0


@pytest.mark.parametrize("value", ["online", "away", "busy", "offline"])
def test_presence_indicator_is_drawn_for_every_status(qapp, value):
    from aedrova.desktop.collaboration import presence_icon

    icon = presence_icon(value)
    image = icon.pixmap(16, 16).toImage()
    assert not image.isNull()
    assert image.pixelColor(3, 8).alpha() > 0
    assert (image.pixelColor(8, 8).alpha() == 0) == (value == "offline")
