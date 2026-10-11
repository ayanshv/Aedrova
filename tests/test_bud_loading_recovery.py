"""Slow Bud reads never trap the setup screen or overwrite a retry's results."""

from threading import Event
from types import MethodType, SimpleNamespace

from PySide6.QtWidgets import QLabel, QStackedWidget, QVBoxLayout, QWidget

from aedrova.desktop.controls import AppDialog
from aedrova.desktop.dots import DotDialog


def loader(qtbot):
    window = QWidget()
    qtbot.addWidget(window)
    window.workspace_id = "workspace"
    window.current_user = lambda: SimpleNamespace(id="user")
    queued = []
    window.connected = SimpleNamespace(
        enqueue=lambda key, operation, completed: queued.append((operation, completed)) or True
    )
    dialog = AppDialog(window)
    qtbot.addWidget(dialog)
    dialog.window = window
    dialog.workspace, dialog.user = "workspace", "user"
    dialog.pending, dialog.job = False, None
    dialog._load_timeout_ms = 20
    dialog.update_controls = lambda: None
    dialog.refresh = lambda: None
    layout = QVBoxLayout(dialog)
    dialog.pages = QStackedWidget()
    dialog.pages.addWidget(QLabel("Bud configuration"))
    layout.addWidget(dialog.pages)
    dialog.status = QLabel("Ready")
    layout.addWidget(dialog.status)
    dialog.run = MethodType(DotDialog.run, dialog)
    dialog.show()
    return dialog, queued


def test_stalled_queue_releases_skeleton_and_discards_late_session(qtbot):
    dialog, queue = loader(qtbot)
    applied, closed = [], []
    dialog.run(lambda _: True, applied.append, recovery=True)
    assert dialog._loading_skeleton.isVisible()
    qtbot.waitUntil(lambda: not dialog.pending)
    assert not dialog._loading_skeleton.isVisible()
    assert dialog._load_retry.isVisible()
    assert "taking longer" in dialog.status.text()
    queue[0][1]({"service": SimpleNamespace(close_context=lambda: closed.append(True))})
    assert closed == [True] and not applied


def test_late_worker_cannot_overwrite_successful_retry(qtbot):
    dialog, queue = loader(qtbot)
    release = Event()
    applied, closed = [], []
    service = SimpleNamespace(close_context=lambda: closed.append(True))
    dialog.run(lambda _: release.wait(timeout=3) and "old", applied.append, recovery=True)
    queue[0][1]({"service": service})
    try:
        qtbot.waitUntil(lambda: not dialog.pending)
        assert dialog.job is None and dialog._load_retry.isVisible()
        dialog._load_timeout_ms = 1000
        dialog.run(lambda _: "new", applied.append, recovery=True)
        queue[1][1]({"service": service})
        qtbot.waitUntil(lambda: applied == ["new"])
    finally:
        release.set()
    qtbot.waitUntil(lambda: not dialog._bud_jobs)
    assert applied == ["new"] and len(closed) == 2
    assert not dialog.pending and not dialog._loading_skeleton.isVisible()


def test_display_failure_restores_retry_instead_of_skeleton(qtbot):
    dialog, queue = loader(qtbot)

    def broken(_):
        raise ValueError("private-detail")

    dialog.run(lambda _: {}, broken, recovery=True)
    queue[0][1]({"service": SimpleNamespace(close_context=lambda: None)})
    qtbot.waitUntil(lambda: not dialog.pending)
    assert dialog._load_retry.isVisible()
    assert not dialog._loading_skeleton.isVisible()
    assert "private-detail" not in dialog.status.text()
