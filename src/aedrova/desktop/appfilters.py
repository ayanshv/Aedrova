"""Application-wide event filters, which can be paused while the built-in browser is open.

Qt WebEngine's internal objects crash PySide when an application-wide Python filter is asked
to look at them (the first focus event on a page recurses and the app dies). Filters that must
see every event register here instead of installing themselves, so they can all be lifted
while a page exists and put back once it is gone. While they are lifted the app still works:
tooltips fall back to the system's, translation rescans on a timer, and idle time is read from
the pointer.
"""

from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QApplication

RESUME_DELAY = 600  # let a closed page finish being torn down before filters look at events


class Registry(QObject):
    def __init__(self):
        super().__init__()
        self.filters = []
        self.holders = set()
        self.ticks = []
        self.suspended = False
        self.resume_timer = QTimer(self)
        self.resume_timer.setSingleShot(True)
        self.resume_timer.timeout.connect(self.resume_if_free)
        self.tick_timer = QTimer(self)
        self.tick_timer.setInterval(1500)
        self.tick_timer.timeout.connect(self.tick)

    def application(self):
        return QApplication.instance()

    def install(self, watcher, tick=None):
        """Install an application-wide filter now, or when the browser lets go of the app."""
        self.filters.append(watcher)
        if tick is not None:
            self.ticks.append(tick)
        if not self.suspended:
            self.application().installEventFilter(watcher)

    def hold(self, who):
        """A page exists: take every filter off, and keep them off until it is released."""
        self.holders.add(who)
        self.resume_timer.stop()
        if self.suspended:
            return
        self.suspended = True
        for watcher in self.filters:
            self.application().removeEventFilter(watcher)
        self.tick_timer.start()

    def release(self, who):
        self.holders.discard(who)
        if not self.holders:
            self.resume_timer.start(RESUME_DELAY)

    def resume_if_free(self):
        if self.holders or not self.suspended:
            return
        self.suspended = False
        self.tick_timer.stop()
        for watcher in self.filters:
            self.application().installEventFilter(watcher)

    def tick(self):
        for callback in list(self.ticks):
            try:
                callback()
            except RuntimeError:  # its owner was deleted
                self.ticks.remove(callback)


registry = Registry()


def install(watcher, tick=None):
    registry.install(watcher, tick)
