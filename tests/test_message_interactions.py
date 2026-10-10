"""Reaction, unsend, emoji selection and existing-message reconciliation journeys."""

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QCursor
from test_connected import row, setup

from aedrova.desktop.connected import message_tree
from aedrova.desktop.conversation import Composer, MessageView, reaction_chips
from aedrova.desktop.emojis import QUICK_EMOJI, EmojiPicker, catalog
from aedrova.desktop.state import Message
from aedrova.desktop.window import AedrovaWindow


def test_full_picker_search_and_combined_emoji(qtbot):
    picker = EmojiPicker()
    qtbot.addWidget(picker)
    assert len(catalog()) > 3900
    picker.search.setText('woman technologist medium skin tone')
    values = [picker.grid.item(i).text() for i in range(picker.grid.count())]
    assert '👩🏽‍💻' in values
    picker.choose(next(picker.grid.item(i) for i in range(picker.grid.count())
                      if picker.grid.item(i).text() == '👩🏽‍💻'))
    assert picker.selected == '👩🏽‍💻'


def test_composer_inserts_emoji_at_cursor_and_preserves_draft(qtbot, monkeypatch):
    composer = Composer()
    qtbot.addWidget(composer)
    composer.editor.setPlainText('Hello team')
    cursor = composer.editor.textCursor()
    cursor.setPosition(6)
    composer.editor.setTextCursor(cursor)
    monkeypatch.setattr('aedrova.desktop.conversation.pick_emoji', lambda _: '👩🏽‍💻')
    composer.insert_emoji()
    assert composer.editor.toPlainText() == 'Hello 👩🏽‍💻team'
    monkeypatch.setattr('aedrova.desktop.conversation.pick_emoji', lambda _: '')
    composer.insert_emoji()
    assert composer.editor.toPlainText() == 'Hello 👩🏽‍💻team'


def test_reaction_bar_plus_and_existing_chip_toggle(qtbot):
    view = MessageView()
    qtbot.addWidget(view)
    view.resize(600, 400)
    message = Message('m', 'You', 'Y', '09:00', 'Hello', mine=True,
                      reactions=[{'emoji': '👍', 'count': 2, 'mine': True}])
    view.show_messages([message])
    view.show()
    emitted = []
    view.reaction_requested.connect(lambda *args: emitted.append(args))
    assert len(QUICK_EMOJI) == 5
    view.react('m', '👍')
    assert emitted == [('m', '👍', False)]
    chips = reaction_chips(message, 600, 70)
    QCursor.setPos(view.viewport().mapToGlobal(chips[0][0].center().toPoint()))
    qtbot.mouseClick(view.viewport(), Qt.MouseButton.LeftButton,
                     pos=chips[0][0].center().toPoint())
    assert len(emitted) == 2
    message.unsent = True
    view.react('m', '🎉')
    assert len(emitted) == 2


def test_local_unsend_preserves_reply_and_clears_file_reactions(qtbot, tmp_path):
    window = AedrovaWindow(settings=QSettings(str(tmp_path / 'ui.ini'), QSettings.Format.IniFormat))
    qtbot.addWidget(window)
    window.send_message('Remove this')
    message = window.channel.messages[-1]
    reply = Message('reply', 'Teammate', 'T', '09:01', 'Keep reply')
    message.replies.append(reply)
    message.attachment = 'file.txt'
    window.react_message(message.id, '🎉', True)
    assert message.reactions[0]['count'] == 1
    window.unsend_message(message.id)
    assert message.unsent and message.body == 'Message unsent.'
    assert message.replies == [reply] and not message.reactions and not message.attachment
    other = window.channel.messages[0]
    body = other.body
    window.unsend_message(other.id)
    assert other.body == body


def test_connected_reconciles_old_sequence_unsend_and_reactions(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    service.message_interactions = lambda ids: [
        {'id': 'm', 'body': 'Hello', 'unsent_at': None,
         'reactions': [{'emoji': '❤️', 'count': 2, 'mine': True}]}]
    window.connected.refresh()
    qtbot.waitUntil(lambda: not window.account_dialog.busy)
    assert window.channel.messages[0].reactions[0]['count'] == 2
    service.message_interactions = lambda ids: [
        {'id': 'm', 'body': 'Message unsent.', 'unsent_at': '2026-10-04', 'reactions': []}]
    window.connected.refresh()
    qtbot.waitUntil(lambda: not window.account_dialog.busy)
    assert window.channel.messages[0].unsent
    assert window.channel.messages[0].body == 'Message unsent.'
    assert not window.channel.messages[0].reactions


def test_message_tree_tracks_ownership_for_thread_replies():
    tree = message_tree([row(), {**row('reply', 'm'), 'sender_id': 'other'}], 'u')
    assert tree[0].mine and not tree[0].replies[0].mine
