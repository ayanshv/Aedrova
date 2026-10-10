"""Shared meeting announcement, join action and participant presentation."""

from test_connected import setup

from aedrova.desktop.meeting_activity import MeetingAction, ParticipantAvatar, update_meeting_ui


def active(window, *, private=False, channel="c", workspace="w"):
    return {
        "id": "meeting",
        "channel_id": channel,
        "workspace_id": workspace,
        "title": "Team meeting",
        "private": private,
        "participants": [
            {"user_id": "u", "display_name": "Alex"},
            {"user_id": "peer", "display_name": "Robin"},
        ],
    }


def test_start_join_roster_and_ended_state(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    window.open_meeting_hub()
    action = window.meeting_action_layout.itemAt(0).widget()
    assert action.action.text() == "Start meeting"
    window.account_dialog.snapshot["meeting_activity"] = {
        "meetings": [active(window)],
        "preferences": [],
    }
    update_meeting_ui(window)
    action = window.meeting_action_layout.itemAt(0).widget()
    assert action.action.text() == "Join meeting"
    assert action.count.text() == "2 in meeting"
    assert len(action.findChildren(ParticipantAvatar)) == 2
    assert window.meeting_announcements_layout.count() == 1
    banner = window.meeting_announcements_layout.itemAt(0).widget()
    assert banner.action.text() == "Join meeting"
    window.account_dialog.snapshot["meeting_activity"]["meetings"] = []
    update_meeting_ui(window)
    assert window.meeting_announcements_layout.count() == 0
    assert window.meeting_action_layout.itemAt(0).widget().action.text() == "Start meeting"


def test_channel_privacy_and_shared_notification_destination(qtbot, tmp_path, monkeypatch):
    from aedrova.desktop import meeting_call
    from aedrova.desktop.state import Channel

    window, _ = setup(qtbot, tmp_path)
    window.workspace.channels.append(Channel("other", "design", "Design"))
    activity = {"meetings": [active(window, channel="other")], "preferences": []}
    window.account_dialog.snapshot["meeting_activity"] = activity
    update_meeting_ui(window)
    assert window.meeting_announcements_layout.count() == 1
    joined = []
    monkeypatch.setattr(meeting_call, "open_channel_call", lambda w: joined.append(w.channel_id))
    window.meeting_announcements_layout.itemAt(0).widget().action.click()
    assert joined == ["other"]
    window.channel_id = "c"
    activity["meetings"][0]["private"] = True
    update_meeting_ui(window)
    assert window.meeting_announcements_layout.count() == 0
    activity["meetings"][0]["private"] = False
    activity["preferences"] = [{"workspace_id": "w", "announcement_channel": "other"}]
    update_meeting_ui(window)
    assert window.meeting_announcements_layout.count() == 0
    activity["meetings"] = [active(window, workspace="another-team")]
    update_meeting_ui(window)
    assert window.meeting_announcements_layout.count() == 0


def test_card_click_is_explicit_and_avatars_are_accessible(qtbot):
    from aedrova.desktop.theme import LIGHT

    calls = []
    card = MeetingAction(
        LIGHT, {"participants": [{"display_name": "A teammate"}]}, lambda: calls.append(True)
    )
    qtbot.addWidget(card)
    assert not calls
    assert card.findChildren(ParticipantAvatar)[0].accessibleName().endswith("A teammate")
    card.action.click()
    assert calls == [True]


def test_empty_meeting_removes_banner_and_returns_start_state(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    meeting = active(window)
    window.account_dialog.snapshot["meeting_activity"] = {"meetings": [meeting], "preferences": []}
    update_meeting_ui(window)
    assert window.meeting_announcements_layout.count() == 1
    meeting["participants"] = []
    update_meeting_ui(window)
    assert window.meeting_announcements_layout.count() == 0
    assert window.meeting_announcements.isHidden()
    assert window.call_count.isHidden()


def test_meeting_updates_never_show_transient_windows_over_fullscreen_call(qtbot, tmp_path):
    from PySide6.QtCore import QEvent, QObject
    from PySide6.QtWidgets import QApplication, QWidget
    from test_meeting_calls import Backend, Worker

    from aedrova.desktop.meeting_call import MeetingCall
    from aedrova.meetings.devices import DeviceCheck

    window, _ = setup(qtbot, tmp_path)
    call = MeetingCall(window, Worker(), devices=DeviceCheck(backend=Backend()))
    qtbot.addWidget(call)
    call.showFullScreen()
    QApplication.processEvents()
    unexpected = []

    class Watch(QObject):
        def eventFilter(self, watched, event):
            if event.type() == QEvent.Type.Show and isinstance(watched, QWidget):
                if watched.isWindow() and watched not in (call, window):
                    unexpected.append(watched.objectName() or type(watched).__name__)
            return False

    watch = Watch()
    app = QApplication.instance()
    app.installEventFilter(watch)
    try:
        for participants in (True, False, True):
            meeting = active(window)
            if not participants:
                meeting["participants"] = []
            window.account_dialog.snapshot["meeting_activity"] = {
                "meetings": [meeting],
                "preferences": [],
            }
            update_meeting_ui(window)
            QApplication.processEvents()
            assert call.isFullScreen() and call.isVisible()
        assert unexpected == []
    finally:
        app.removeEventFilter(watch)
        call.reject()
