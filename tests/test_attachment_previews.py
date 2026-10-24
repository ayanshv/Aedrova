from types import SimpleNamespace
from unittest.mock import Mock

from aedrova.desktop.attachment_previews import AttachmentPreviews, preview_height


def test_previews_are_bounded_and_discard_late_workspace_result(qtbot):
    from PySide6.QtWidgets import QWidget

    window = QWidget()
    qtbot.addWidget(window)
    window.messages = Mock()
    window.thread_messages = Mock()
    calls = []
    connected = Mock()
    connected.enqueue.side_effect = lambda key, operation, loaded: (
        calls.append((key, operation, loaded)) or True
    )
    scope = ["workspace-a"]
    preview = AttachmentPreviews(window, lambda: connected, lambda: scope[0])
    messages = [SimpleNamespace(attachment_id=str(i), attachment=f"{i}.txt") for i in range(20)]
    preview.load(messages)
    assert len(calls) == 8
    preview.load(messages)
    assert len(calls) == 8
    scope[0] = "workspace-b"
    calls[0][2](b"Private old workspace content")
    assert not preview.cache
    preview.clear()


def test_preview_policy_avoids_auto_document_execution():
    assert preview_height("photo.png") > 58
    assert preview_height("note.md") > 58
    assert preview_height("document.pdf") == 58
    assert preview_height("document.docx") == 58
    assert preview_height("voice.wav") == 58
