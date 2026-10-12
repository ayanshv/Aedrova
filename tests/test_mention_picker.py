"""Grouped mentions must select and route the intended participant without sending."""

from PySide6.QtCore import Qt

from aedrova.desktop.conversation import Composer


def composer_with_people(qtbot):
    composer = Composer()
    qtbot.addWidget(composer)
    composer.set_agent_name("Atlas")
    composer.dots = [
        {
            "id": "d1",
            "name": "Orbit",
            "role": "Research",
            "appearance": "research",
            "color": "#70C8B7",
        },
        {"id": "d2", "name": "Spark", "role": "Marketing", "appearance": "marketing"},
    ]
    composer.ai_teammates = [
        {"id": "a1", "config": {"name": "Reviewer", "role": "Review builds"}, "paused": False},
        {"id": "a2", "config": {"name": "Paused"}, "paused": True},
    ]
    composer.people = [{"user_id": "p1", "display_name": "Maya Chen", "username": "maya_chen"}]
    composer.resize(650, 500)
    composer.show()
    composer.editor.setFocus()
    return composer


def test_groups_arrow_selection_avatar_and_routing(qtbot):
    c = composer_with_people(qtbot)
    sent = []
    c.submitted.connect(sent.append)
    qtbot.keyClicks(c.editor, "@")
    rows = [c.mention_list.item(i) for i in range(c.mention_list.count())]
    assert [r.text() for r in rows if not r.data(Qt.ItemDataRole.UserRole)] == [
        "Agents",
        "Buds",
        "People",
        "Notify channel",
    ]
    assert all("Paused" not in r.text() for r in rows)
    orbit = next(
        r for r in rows if r.data(Qt.ItemDataRole.UserRole) == ("Orbit", "<@dot:d1|Orbit>")
    )
    assert not orbit.icon().isNull()
    qtbot.keyClick(c.editor, Qt.Key.Key_Down)  # Reviewer
    qtbot.keyClick(c.editor, Qt.Key.Key_Down)  # Orbit, skipping section heading
    qtbot.keyClick(c.editor, Qt.Key.Key_Return)
    assert c.editor.toPlainText() == "@Orbit "
    assert not sent and c.mention_list.isHidden()
    qtbot.keyClicks(c.editor, "find evidence")
    qtbot.keyClick(c.editor, Qt.Key.Key_Return)
    assert sent == ["<@dot:d1|Orbit> find evidence"]


def test_search_backwards_wrap_escape_and_unicode(qtbot):
    c = composer_with_people(qtbot)
    c.editor.setPlainText("🚀 @orb")
    cursor = c.editor.textCursor()
    cursor.movePosition(cursor.MoveOperation.End)
    c.editor.setTextCursor(cursor)
    qtbot.keyClick(c.editor, Qt.Key.Key_Tab)
    assert c.editor.toPlainText() == "🚀 @Orbit "
    c.editor.clear()
    qtbot.keyClicks(c.editor, "@")
    qtbot.keyClick(c.editor, Qt.Key.Key_Up)
    assert c.mention_choice == ("everyone", "@everyone")
    qtbot.keyClick(c.editor, Qt.Key.Key_Escape)
    assert c.mention_list.isHidden() and c.suggestion.isHidden()
    c.editor.setPlainText("@unknown")
    assert c.mention_list.isHidden()
    c.editor.setPlainText("email@orbit")
    assert c.mention_list.isHidden()
