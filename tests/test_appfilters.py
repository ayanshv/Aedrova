from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import QApplication

from aedrova.desktop import appfilters


class Watcher(QObject):
    def __init__(self):
        super().__init__()
        self.seen = 0

    def eventFilter(self, watched, event):  # noqa: N802
        self.seen += 1
        return False


def test_filters_are_lifted_while_a_page_exists_and_come_back_afterwards(qtbot, monkeypatch):
    monkeypatch.setattr(appfilters, "RESUME_DELAY", 20)
    registry = appfilters.Registry()
    registry.resume_timer.setInterval(20)
    watcher, ticks = Watcher(), []
    registry.install(watcher, lambda: ticks.append(1))
    app = QApplication.instance()
    app.sendEvent(app, QEvent(QEvent.Type.User))
    assert watcher.seen > 0
    before = watcher.seen
    registry.hold("browser")
    assert registry.suspended
    app.sendEvent(app, QEvent(QEvent.Type.User))
    assert watcher.seen == before  # nothing application-wide looks at events now
    registry.tick_timer.setInterval(10)
    qtbot.waitUntil(lambda: bool(ticks), timeout=2000)  # stand-ins keep the features alive
    registry.hold("second")
    registry.release("browser")
    qtbot.wait(80)
    assert registry.suspended  # another holder still has a page
    registry.release("second")
    qtbot.waitUntil(lambda: not registry.suspended, timeout=2000)
    app.sendEvent(app, QEvent(QEvent.Type.User))
    assert watcher.seen > before
    registry.holders.clear()
    app.removeEventFilter(watcher)


def test_a_filter_installed_while_paused_waits_for_the_resume(qtbot):
    registry = appfilters.Registry()
    registry.hold("browser")
    watcher = Watcher()
    registry.install(watcher)
    app = QApplication.instance()
    app.sendEvent(app, QEvent(QEvent.Type.User))
    assert watcher.seen == 0
    registry.release("browser")
    qtbot.waitUntil(lambda: not registry.suspended, timeout=3000)
    app.sendEvent(app, QEvent(QEvent.Type.User))
    assert watcher.seen > 0
    app.removeEventFilter(watcher)
