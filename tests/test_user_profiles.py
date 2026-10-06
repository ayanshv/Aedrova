from unittest.mock import Mock

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QTextCursor
from test_connected import setup

from aedrova.desktop.conversation import Composer
from aedrova.desktop.profile import (
    Avatar,
    ProfileDialog,
    avatar_png,
    suggested_username,
    validate_profile,
)


def values(**kw):
    return {
        "display_name": "Maya Chen",
        "username": "maya_chen",
        "bio": "Designer",
        "title": "Engineer",
        "status": "Focus",
        "availability": "busy",
        **kw,
    }


def test_validation_and_stable_username():
    assert suggested_username("Māya Chen", "abc-def") == "maya_chen_abcdef"
    assert validate_profile(values())["availability"] == "busy"
    for bad in (
        {"username": "a"},
        {"username": "Bad name"},
        {"bio": "x" * 281},
        {"display_name": " "},
        {"availability": "admin"},
    ):
        with pytest.raises(ValueError):
            validate_profile(values(**bad))


def test_avatar_center_crop_and_round_preview(qtbot, tmp_path):
    image = QImage(400, 200, QImage.Format.Format_RGB32)
    image.fill(Qt.GlobalColor.red)
    file = tmp_path / "photo.png"
    image.save(str(file))
    data = avatar_png(file)
    result = QImage.fromData(data)
    assert result.size().width() == result.size().height() == 256
    avatar = Avatar()
    qtbot.addWidget(avatar)
    avatar.set_photo(data)
    avatar.show()
    assert not avatar.grab().isNull()
    with pytest.raises(ValueError):
        avatar_png(tmp_path / "missing.png")


def test_guided_profile_saves_fields_and_updates_account(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    original_snapshot = service.snapshot
    saved_profile = {}

    def save(data, photo):
        saved_profile.update(data)
        return dict(data)

    service.save_full_profile = Mock(side_effect=save)
    service.snapshot = lambda: {**original_snapshot(), "user_profile": dict(saved_profile)}
    dialog = ProfileDialog(window, window.account_dialog, onboarding=True)
    qtbot.addWidget(dialog)
    dialog.show()
    dialog.name.setText("Maya Chen")
    dialog.username.setText("maya_chen")
    dialog.advance()
    assert dialog.stack.currentIndex() == 1
    dialog.title.setText("Founder")
    dialog.bio.setPlainText("Working together")
    dialog.advance()
    assert dialog.stack.currentIndex() == 2
    dialog.availability.setCurrentIndex(dialog.availability.findData("busy"))
    dialog.status.setText("Focused")
    dialog.status_emoji = "🚀"
    dialog.advance()
    qtbot.waitUntil(lambda: not dialog.saving)
    data = service.save_full_profile.call_args.args[0]
    assert data["profile_completed"] and data["status_emoji"] == "🚀"
    assert data["title"] == "Founder" and data["availability"] == "busy"
    assert window.account_dialog.snapshot["user_profile"]["username"] == "maya_chen"
    assert window.profile_button.toolTip() == "Maya Chen"


def test_username_collision_stays_open_without_losing_values(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    service.save_full_profile = Mock(side_effect=ValueError("That username is already taken"))
    dialog = ProfileDialog(window, window.account_dialog)
    qtbot.addWidget(dialog)
    dialog.show()
    dialog.name.setText("Maya")
    dialog.username.setText("maya_chen")
    dialog.go(2)
    dialog.advance()
    qtbot.waitUntil(lambda: not dialog.saving)
    assert dialog.isVisible() and "taken" in dialog.error.text()
    assert dialog.name.text() == "Maya"


def test_username_mention_and_private_cache_reset(qtbot, tmp_path):
    composer = Composer()
    qtbot.addWidget(composer)
    composer.people = [
        {
            "user_id": "96000000-0000-0000-0000-000000000001",
            "display_name": "Maya Chen",
            "username": "maya_chen",
        }
    ]
    composer.editor.setPlainText("@maya_")
    cursor = composer.editor.textCursor()
    cursor.movePosition(QTextCursor.MoveOperation.End)
    composer.editor.setTextCursor(cursor)
    composer.complete_mention()
    assert composer.editor.toPlainText() == "@maya_chen "
    window, service = setup(qtbot, tmp_path)
    window.collaboration.avatar_images["private"] = object()
    window.collaboration.reset()
    assert not window.collaboration.avatar_images


def test_profile_configuration_does_not_interrupt_simulated_intro(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    data = service.snapshot()
    data["user_profile"] = {"profile_completed": False}
    window.account_dialog.loaded(data)
    qtbot.wait(30)
    assert getattr(window, "profile_dialog", None) is None
