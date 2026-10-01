"""Regression tests for real button clicks, queued sends and message geometry."""

import threading
from pathlib import Path

from PySide6.QtCore import QPoint, Qt
from PySide6.QtWidgets import QStyleOptionViewItem
from test_connected import setup

from aedrova.agents.checkout import git, prepare
from aedrova.desktop.builds import BuildDialog
from aedrova.desktop.conversation import MESSAGE_ROLE, MessageView
from aedrova.desktop.state import Message


def test_empty_build_request_focuses_visible_editor(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    dialog = BuildDialog(window)
    qtbot.addWidget(dialog)
    dialog.show()
    dialog.repository.setText(str(tmp_path))
    dialog.consent.setChecked(True)
    qtbot.mouseClick(dialog.plan_button, Qt.MouseButton.LeftButton)
    assert not dialog.pending
    assert "Enter what you want" in dialog.status.text()
    assert dialog.request.accessibleName() == "Build request"
    assert dialog.request.objectName() == "BuildRequest"


def test_queued_send_appears_before_network_finishes(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    qtbot.waitUntil(lambda: not window.account_dialog.busy)
    release = threading.Event()
    started = threading.Event()

    def busy():
        started.set()
        release.wait(3)
        return True

    window.account_dialog.run(busy, lambda _: None)
    qtbot.waitUntil(started.is_set)
    sends = []
    service.rpc = lambda name, data: sends.append(data) or data.get("p_id")
    window.composer.editor.setPlainText("Instant feedback")
    window.send_message("Instant feedback")
    assert window.composer.editor.toPlainText() == ""
    assert not sends
    assert window.channel.messages[-1].body == "Instant feedback"
    assert window.channel.messages[-1].delivery == "Sending…"
    release.set()
    # No timer/poll/manual refresh: completion must drain the queued send immediately.
    qtbot.waitUntil(lambda: bool(sends) and not window.account_dialog.busy, timeout=2000)
    assert window.channel.messages[-1].delivery == ""


def test_send_priority_preserves_message_order(qtbot, tmp_path):
    window, service = setup(qtbot, tmp_path)
    qtbot.waitUntil(lambda: not window.account_dialog.busy)
    window.connected.retry_at = float("inf")
    window.connected.enqueue(("read", "c"), lambda: None, lambda _: None)
    window.send_message("First")
    window.send_message("Second")
    queued = list(window.connected.queue)
    assert [a[0][0] for a in queued] == ["send", "send", "read"]
    assert [window.connected.outbox[a[0][1]]["body"] for a in queued[:2]] == ["First", "Second"]


def test_new_folder_gets_private_git_snapshot(tmp_path):
    source = tmp_path / "new-project"
    source.mkdir()
    project = prepare(source, tmp_path / "builds")
    assert not (source / ".git").exists()
    assert git(project, "rev-parse", "HEAD").strip()
    assert not git(project, "status", "--porcelain").strip()


def test_snapshot_excludes_secrets_dependencies_and_external_links(tmp_path):
    import pytest

    source = tmp_path / "source"
    source.mkdir()
    (source / "app.py").write_text("answer = 42")
    (source / ".env").write_text("DUMMY_VALUE=do-not-copy")
    (source / "node_modules").mkdir()
    (source / "node_modules" / "module.js").write_text("ignored")
    project = prepare(source, tmp_path / "builds")
    assert (project / "app.py").exists()
    assert not (project / ".env").exists()
    assert not (project / "node_modules").exists()
    (source / "escape.py").symlink_to(Path(__file__).resolve())
    with pytest.raises(ValueError, match="outside"):
        prepare(source, tmp_path / "builds")


def test_message_refresh_keeps_scrolled_position(qtbot):
    view = MessageView()
    qtbot.addWidget(view)
    view.resize(480, 300)
    view.show()
    messages = [
        Message(str(i), "Teammate", "T", "2026-09-28 23:11", "Message " + str(i)) for i in range(80)
    ]
    view.show_messages(messages)
    qtbot.waitUntil(lambda: view.verticalScrollBar().maximum() > 500)
    view.scrollTo(view.model().index(20), view.ScrollHint.PositionAtTop)
    qtbot.wait(50)
    anchor = view.indexAt(QPoint(100, 1)).data(MESSAGE_ROLE).id
    view.show_messages(messages + [Message("new", "You", "Y", "2026-09-28 23:12", "new")])
    qtbot.wait(50)
    assert view.indexAt(QPoint(100, 1)).data(MESSAGE_ROLE).id == anchor


def test_message_header_and_long_body_fit_row(qtbot, tmp_path):
    from math import ceil

    from PySide6.QtGui import QFontMetrics

    from aedrova.desktop.conversation import font

    view = MessageView()
    qtbot.addWidget(view)
    view.resize(350, 350)
    view.show()
    message = Message(
        "long",
        "An exceptionally long teammate name",
        "AT",
        "2026-09-28 23:11",
        "A long message with wrapping. " * 10,
        decision=True,
        attachment="notes.txt",
    )
    view.show_messages([message])
    qtbot.wait(50)
    size = view.delegate.sizeHint(QStyleOptionViewItem(), view.model().index(0))
    body = view.delegate.document(message, view.viewport().width() - 94)
    assert (
        size.height()
        >= 18 + QFontMetrics(font(14, True)).height() + 6 + ceil(body.size().height()) + 58 + 22
    )
    assert view.grab().save(str(tmp_path / "timestamp-layout.png"))
