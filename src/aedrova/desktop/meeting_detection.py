"""Suggest local notes from microphone activity; detection never starts recording."""

import sys
import time

from PySide6.QtCore import QObject, QThreadPool, QTimer
from PySide6.QtWidgets import QApplication

from aedrova.desktop.meeting_suggestion import MeetingSuggestion
from aedrova.desktop.meeting_transcript import ReviewJob
from aedrova.meetings.local_capture import possible_meeting_apps


class MeetingDetection(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.job = None
        self.snoozed_until = 0
        self.capsule = None
        self.timer = QTimer(self)
        self.timer.setInterval(4000)
        self.timer.timeout.connect(self.poll)
        if sys.platform == "darwin" and QApplication.platformName() != "offscreen":
            self.timer.start()
            QTimer.singleShot(0, self.poll)
        QApplication.instance().aboutToQuit.connect(self.hide_suggestion)

    def hide_suggestion(self):
        if self.capsule:
            self.capsule.hide()

    def ensure_capsule(self):
        if self.capsule is not None:
            return
        self.capsule = MeetingSuggestion(self.window)
        self.capsule.review_requested.connect(self.open_notes)
        self.capsule.stop_requested.connect(self.dismiss)
        self.capsule.disable_requested.connect(self.turn_off)
        self.capsule.expired.connect(self.snooze_briefly)

    def enabled(self):
        return self.window.settings.value("meetings/localNotesSuggestions", True, type=bool)

    def set_enabled(self, value):
        self.window.settings.setValue("meetings/localNotesSuggestions", value)
        if not value:
            self.hide_suggestion()
        elif self.timer.isActive():
            self.poll()

    def can_suggest(self):
        dialog = getattr(self.window, "local_meeting_notes", None)
        return (
            self.enabled()
            and self.window.isVisible()
            and time.monotonic() >= self.snoozed_until
            and not (dialog and (dialog.isVisible() or dialog.capture.active))
        )

    def poll(self):
        if self.job or not self.can_suggest():
            return
        self.job = ReviewJob(possible_meeting_apps, error="Meeting detection unavailable.")
        self.job.signals.result.connect(self.detected)
        QThreadPool.globalInstance().start(self.job)

    def detected(self, result):
        self.job = None
        data = result.get("value") or {}
        if self.can_suggest() and data.get("active") and data.get("names"):
            self.ensure_capsule()
            self.capsule.set_state("Take meeting notes?")
            if not self.capsule.isVisible():
                self.capsule.show_on_side()
        else:
            self.hide_suggestion()

    def dismiss(self):
        self.snoozed_until = time.monotonic() + 30 * 60
        self.hide_suggestion()

    def snooze_briefly(self):
        self.snoozed_until = time.monotonic() + 5 * 60

    def turn_off(self):
        self.set_enabled(False)

    def open_notes(self):
        from aedrova.desktop.local_meeting_notes import open_local_meeting_notes

        self.dismiss()
        open_local_meeting_notes(self.window)
