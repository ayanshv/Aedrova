"""Visual regressions that previously hid controls or content in narrow/dark layouts."""

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QPalette, QTextCursor
from PySide6.QtWidgets import QLabel, QMessageBox, QScrollArea
from test_connected import setup
from test_meeting_calls import Backend, Worker

from aedrova.desktop.account import AccountDialog
from aedrova.desktop.meeting_call import MeetingCall
from aedrova.desktop.meeting_setup import MeetingSetup
from aedrova.desktop.preferences import SettingsDialog
from aedrova.desktop.theme import DARK
from aedrova.meetings.devices import DeviceCheck


def test_dark_scroll_panels_and_live_theme_change(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    window.set_theme("dark", persist=False)
    dialogs = [SettingsDialog(window), MeetingSetup(window, check=DeviceCheck(backend=Backend()))]
    for dialog in dialogs:
        qtbot.addWidget(dialog)
        dialog.show()
        qtbot.wait(10)
        scroll = dialog.findChild(QScrollArea)
        # Sample an unoccupied corner of the scroll content, not just its palette.
        image = scroll.widget().grab().toImage()
        assert image.pixelColor(2, 2).name().upper() == DARK.bg
        assert dialog.palette().color(QPalette.ColorRole.Window).name().upper() == DARK.bg
    window.set_theme("light", persist=False)
    for dialog in dialogs:
        assert dialog.palette().color(QPalette.ColorRole.Window).name() == "#ffffff"
        dialog.close()


def test_workspace_admin_has_no_horizontal_scrolling_at_minimum_width(qtbot, tmp_path):
    widget = AccountDialog(
        settings=QSettings(str(tmp_path / "visual.ini"), QSettings.Format.IniFormat)
    )
    qtbot.addWidget(widget)
    widget.pages.setCurrentIndex(1)
    widget.resize(600, 540)
    widget.show()
    qtbot.wait(10)
    scroll = widget.pages.currentWidget()
    assert scroll.horizontalScrollBar().maximum() == 0
    for control in [widget.agent_name, widget.agent_provider, widget.save_agent, widget.role]:
        assert control.width() >= control.minimumSizeHint().width()


def test_roster_refresh_hides_old_labels_and_remains_scrollable(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    worker = Worker()
    call = MeetingCall(window, worker, devices=DeviceCheck(backend=Backend()), channel_name="Team")
    qtbot.addWidget(call)
    call.resize(800, 650)
    call.show()
    call.participants_button.setChecked(True)
    previous = call.participant_panel.findChildren(QLabel)
    call.render_roster(
        [{"id": str(i), "name": "A long teammate name " + str(i)} for i in range(16)]
    )
    assert all(label.isHidden() for label in previous if label.text() in {"You", "Muted"})
    scroll = call.participant_panel.findChild(QScrollArea)
    qtbot.waitUntil(lambda: scroll.verticalScrollBar().maximum() > 0)
    scroll.verticalScrollBar().setValue(scroll.verticalScrollBar().maximum())
    last_name = [label for label in scroll.findChildren(QLabel) if label.text().endswith("15")][0]
    name_y = last_name.mapTo(scroll.viewport(), last_name.rect().topLeft()).y()
    assert name_y < scroll.viewport().height()
    assert call.participants_button.objectName() == "CallControl"
    call.close()


def test_confirmation_dialog_uses_current_app_palette(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    window.set_theme("dark", persist=False)
    box = QMessageBox(window)
    qtbot.addWidget(box)
    box.setText("Review the changes before applying them.")
    box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    box.show()
    assert box.palette().color(QPalette.ColorRole.Window).name().upper() == DARK.bg
    assert box.palette().color(QPalette.ColorRole.WindowText).name().upper() == DARK.text
    box.close()


def test_compact_chat_keeps_composer_and_footer_separate_during_activity(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    window.resize(900, 650)
    window.agent_event(window.workspace_id, "Running: python3 -m pytest")
    window.agent_event(window.workspace_id, "$ python3 -m pytest\n8 passed\nExit code: 0")
    window.agent_feed.rows[-1].toggle.click()
    window.composer.editor.setPlainText("@")
    cursor = window.composer.editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    window.composer.editor.setTextCursor(cursor)
    window.show()
    qtbot.wait(20)
    assert window.composer.height() >= window.composer.minimumSizeHint().height()
    assert window.composer.send.height() >= window.composer.send.minimumSizeHint().height()
    area = window.composer.parentWidget()
    assert area.height() >= area.minimumSizeHint().height()
    footer = area.layout().itemAt(area.layout().count() - 1).widget()
    assert window.composer.geometry().bottom() < footer.geometry().top()


def test_profile_popup_mouse_activation_and_theme(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    window.show()
    for mode in ("light", "dark"):
        window.set_theme(mode, persist=False)
        qtbot.mouseClick(window.profile_button, Qt.MouseButton.LeftButton)
        qtbot.waitUntil(lambda: window.profile_menu.isVisible())
        assert window.profile_menu.palette().color(
            QPalette.ColorRole.Window
        ) == window.palette().color(QPalette.ColorRole.Window)
        assert any(action.text() == "Settings…" for action in window.profile_menu.actions())
        window.profile_menu.close()
