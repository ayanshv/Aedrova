"""Suggest local notes from microphone activity; detection never starts recording."""

import sys
import time

from PySide6.QtCore import QObject, QThreadPool, QTimer
from PySide6.QtWidgets import QApplication

from aedrova.desktop.icons import assign
from aedrova.desktop.meeting_listening import ListeningCapsule
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
        self.timer.setInterval(20000)
        self.timer.timeout.connect(self.poll)
        if sys.platform == "darwin" and QApplication.platformName() != "offscreen":
            self.timer.start()
        QApplication.instance().aboutToQuit.connect(self.hide_suggestion)

    def hide_suggestion(self):
        if self.capsule:
            self.capsule.hide()

    def ensure_capsule(self):
        if self.capsule is not None:
            return
        self.capsule = ListeningCapsule(self.window)
        self.capsule.review.setToolTip("Start meeting notes")
        self.capsule.review.setAccessibleName("Start meeting notes")
        self.capsule.review_requested.connect(self.open_notes)
        assign(self.capsule.stop, "close")
        self.capsule.stop.setToolTip("Dismiss suggestion")
        self.capsule.stop.setAccessibleName("Dismiss meeting notes suggestion")
        self.capsule.stop_requested.connect(self.dismiss)

    def enabled(self):
        return self.window.settings.value("meetings/localNotesSuggestions", True, type=bool)

    def set_enabled(self, value):
        self.window.settings.setValue("meetings/localNotesSuggestions", value)
        if not value:
            self.hide_suggestion()

    def poll(self):
        dialog = getattr(self.window, "local_meeting_notes", None)
        if (
            self.job
            or not self.enabled()
            or not self.window.isVisible()
            or time.monotonic() < self.snoozed_until
            or (dialog and (dialog.isVisible() or dialog.capture.active))
        ):
            return
        self.job = ReviewJob(possible_meeting_apps, error="Meeting detection unavailable.")
        self.job.signals.result.connect(self.detected)
        QThreadPool.globalInstance().start(self.job)

    def detected(self, result):
        self.job = None
        data = result.get("value") or {}
        if self.enabled() and data.get("active") and data.get("names"):
            self.ensure_capsule()
            self.capsule.set_state("Take meeting notes?")
            self.capsule.pulse.pending = False
            self.capsule.show_on_side()
        else:
            self.hide_suggestion()

    def dismiss(self):
        self.snoozed_until = time.monotonic() + 30 * 60
        self.hide_suggestion()

    def open_notes(self):
        from aedrova.desktop.local_meeting_notes import open_local_meeting_notes

        self.dismiss()
        open_local_meeting_notes(self.window)
