"""Personal settings that change how messages look, send and notify."""

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from test_connected import setup

from aedrova.desktop import conversation
from aedrova.desktop.preferences import SettingsDialog


def teardown_function():
    conversation.set_text_scale(1.0)
    conversation.MessageEditor.send_requires_modifier = False


def dialog_for(qtbot, tmp_path, monkeypatch):
    monkeypatch.setattr("aedrova.desktop.preferences.application_origin", lambda: "")
    window, _ = setup(qtbot, tmp_path)
    dialog = SettingsDialog(window)
    qtbot.addWidget(dialog)
    return window, dialog


def press(editor, key, modifiers=Qt.KeyboardModifier.NoModifier):
    editor.keyPressEvent(QKeyEvent(QEvent.Type.KeyPress, key, modifiers))


def test_personal_settings_gain_message_notification_and_typing_controls(
    qtbot, tmp_path, monkeypatch
):
    _, dialog = dialog_for(qtbot, tmp_path, monkeypatch)
    for page in ("messages", "notifications", "privacy"):
        assert page in dialog.view.pages
    assert hasattr(dialog, "share_typing") and hasattr(dialog, "activity_alerts")


def test_text_size_scales_message_fonts_and_is_remembered(qtbot, tmp_path, monkeypatch):
    window, dialog = dialog_for(qtbot, tmp_path, monkeypatch)
    base = conversation.font(14).pixelSize()
    dialog.text_size.setCurrentIndex(dialog.text_size.findData(1.3))
    assert conversation.font(14).pixelSize() > base
    assert window.settings.value("textScale", type=float) == 1.3
    dialog.text_size.setCurrentIndex(dialog.text_size.findData(1.0))
    assert conversation.font(14).pixelSize() == base


def test_send_key_setting_changes_what_enter_does(qtbot, tmp_path, monkeypatch):
    window, dialog = dialog_for(qtbot, tmp_path, monkeypatch)
    editor = conversation.MessageEditor()
    qtbot.addWidget(editor)
    sent = []
    editor.submitted.connect(lambda: sent.append(1))
    press(editor, Qt.Key.Key_Return)
    assert sent == [1]
    dialog.send_key.setCurrentIndex(dialog.send_key.findData(True))
    press(editor, Qt.Key.Key_Return)
    assert sent == [1]
    press(editor, Qt.Key.Key_Return, Qt.KeyboardModifier.ControlModifier)
    assert sent == [1, 1]


def test_typing_and_activity_alert_choices_are_saved(qtbot, tmp_path, monkeypatch):
    window, dialog = dialog_for(qtbot, tmp_path, monkeypatch)
    assert window.settings.value("shareTyping", True, type=bool) is True
    dialog.share_typing.setChecked(False)
    dialog.activity_alerts.setChecked(False)
    assert window.settings.value("shareTyping", True, type=bool) is False
    assert window.settings.value("notifyActivity", True, type=bool) is False
