"""Actual public activity presentation, themed menu/selector and keyboard checks."""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QApplication, QDialog, QPushButton

from aedrova.desktop.agent_activity import AgentClock
from aedrova.desktop.agent_stream import AgentStream
from aedrova.desktop.controls import AppMenu, ChoiceBox, choose_teammate
from aedrova.desktop.theme import DARK, LIGHT, stylesheet


def test_command_stream_updates_row_and_expands_output(qtbot):
    stream = AgentStream()
    qtbot.addWidget(stream)
    stream.show()
    stream.add_event("Running: python3 -m unittest")
    assert len(stream.rows) == 1 and stream.rows[0].pending
    stream.add_event("$ python3 -m unittest\nRan 4 tests\nOK\nExit code: 0")
    row = stream.rows[0]
    assert len(stream.rows) == 1 and not row.pending and row.status == "done"
    assert row.details.isHidden()
    row.toggle.setFocus()
    qtbot.keyClick(row.toggle, Qt.Key.Key_Space)
    assert not row.details.isHidden()
    assert "Ran 4 tests" in row.details.toPlainText()
    assert "Ran 4 tests" not in stream.toPlainText()
    stream.add_event("$ false\nExit code: 1")
    assert stream.rows[-1].status == "failed"


def test_activity_plain_text_bounds_and_stop(qtbot):
    stream = AgentStream()
    qtbot.addWidget(stream)
    stream.add_event("<b>Public update</b><script>alert(1)</script>")
    assert stream.rows[0].message.textFormat() == Qt.TextFormat.PlainText
    stream.add_event("Running: unfinished command")
    stream.finish_pending()
    assert stream.rows[-1].status == "stopped" and not stream.running
    for number in range(120):
        stream.add_event(str(number))
    assert len(stream.rows) == 100
    stream.clear()
    assert not stream.toPlainText()


def test_elapsed_clock_tracks_real_time_and_resets(qtbot):
    clock = AgentClock()
    qtbot.addWidget(clock)
    clock.now = lambda: 100
    clock.set_active(True)
    clock.now = lambda: 165
    clock.refresh()
    assert clock.text() == "1:05"
    clock.set_active(False)
    assert not clock.timer.isActive()
    clock.reset()
    assert clock.started is None and clock.isHidden()


def test_popup_and_dropdown_style_matches_both_themes(qtbot):
    parent = QDialog()
    qtbot.addWidget(parent)
    menu = AppMenu(parent)
    menu.addAction("Settings")
    choice = ChoiceBox(parent)
    choice.addItems(["Codex", "Claude Code"])
    for theme in (LIGHT, DARK):
        parent.setStyleSheet(stylesheet(theme))
        assert menu.objectName() == "AppMenu"
        assert menu._menu_style.objectName().lower() == "fusion"
        assert choice._choice_style.objectName().lower() == "fusion"
        assert "QMenu::item:disabled" in parent.styleSheet()
        assert "QFrame#AgentTool" in parent.styleSheet()


def test_teammate_picker_returns_selected_person(qtbot):
    parent = QDialog()
    qtbot.addWidget(parent)

    def select():
        dialog = QApplication.activeModalWidget()
        choice = dialog.findChild(ChoiceBox)
        choice.setCurrentIndex(1)
        next(b for b in dialog.findChildren(QPushButton) if b.text() == "Message").click()

    QTimer.singleShot(50, select)
    assert choose_teammate(parent, ["Alex", "Morgan"]) == ("Morgan", True)


def test_agent_stream_never_overlaps_composer_when_resized(qtbot, tmp_path):
    from test_connected import setup

    window, _ = setup(qtbot, tmp_path)
    window.show()
    window.agent_event("w", "I’m checking the team’s confirmed requirements.")
    window.agent_event("w", "Running: python3 -m unittest")
    window.agent_event("w", "$ python3 -m unittest\nRan 4 tests\nOK\nExit code: 0")
    window.agent_feed.rows[-1].toggle.click()
    window.composer.editor.setPlainText("@")
    for theme in ("light", "dark"):
        window.set_theme(theme, persist=False)
        for width, height in ((900, 650), (1440, 940)):
            window.resize(width, height)
            qtbot.wait(30)
            assert window.messages.isVisible()
            assert window.messages.isAncestorOf(window.agent_feed)
            viewport_bottom = window.messages.mapToGlobal(window.messages.rect().bottomLeft()).y()
            composer_top = window.composer.mapToGlobal(window.composer.rect().topLeft()).y()
            assert viewport_bottom < composer_top
            assert window.agent_feed.inline
            assert not window.agent_feed.verticalScrollBar().isVisible()


def test_popup_depth_keeps_selection_and_stable_geometry(qtbot):
    from PySide6.QtCore import QPoint

    from aedrova.desktop.theme import palette

    parent = QDialog()
    qtbot.addWidget(parent)
    parent.resize(600, 450)
    choice = ChoiceBox(parent)
    choice.setGeometry(24, 24, 250, 44)
    choice.addItems(["First", "Second", "Third"])
    menu = AppMenu(parent)
    selected = []
    menu.addAction("First action", lambda: selected.append("first"))
    second = menu.addAction("Second action", lambda: selected.append("second"))
    for theme in (LIGHT, DARK):
        parent.setPalette(palette(theme))
        parent.setStyleSheet(stylesheet(theme))
        parent.show()
        qtbot.wait(10)
        sizes = []
        for _ in range(3):
            choice.showPopup()
            qtbot.wait(10)
            popup = choice.view().window()
            sizes.append((popup.width(), popup.height()))
            assert popup.mask().isEmpty()
            image = popup.grab().toImage()
            assert image.pixelColor(0, 0).alpha() == 0
            assert 0 < image.pixelColor(10, image.height() // 2).alpha() < 150
            assert image.pixelColor(21, image.height() // 2).alpha() == 255
            choice.hidePopup()
        assert len(set(sizes)) == 1
        choice.setCurrentIndex(0)
        choice.showPopup()
        qtbot.keyClick(choice.view(), Qt.Key.Key_Down)
        qtbot.keyClick(choice.view(), Qt.Key.Key_Return)
        assert choice.currentIndex() == 1
        menu.popup(parent.mapToGlobal(QPoint(120, 150)))
        qtbot.wait(10)
        image = menu.grab().toImage()
        assert menu.mask().isEmpty() and image.pixelColor(0, 0).alpha() == 0
        assert 0 < image.pixelColor(10, image.height() // 2).alpha() < 150
        qtbot.mouseClick(menu, Qt.MouseButton.LeftButton, pos=menu.actionGeometry(second).center())
        assert selected[-1] == "second"
