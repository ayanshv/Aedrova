"""A reply too long for the chat shows its opening and offers the whole thing as a file."""

from pathlib import Path

import pytest
from test_connected import setup

from aedrova.desktop.response_actions import (
    ACTION_PREFIX,
    LONG_REPLY_CHARS,
    long_reply,
    write_reply_file,
)

SECTION = "## Plan\n\nThis paragraph explains one part of the plan in plain words. " * 3
LONG = "\n\n".join(f"{SECTION}\n\nPart {n} ends here." for n in range(12))
SHORT = "A short answer, with `code`, that belongs in the chat."


def test_short_replies_are_left_alone():
    assert long_reply(SHORT) is None
    assert long_reply("x" * LONG_REPLY_CHARS) is None


def test_long_replies_get_a_preview_and_a_word_count():
    preview, words = long_reply(LONG)
    assert len(preview) < len(LONG) / 3 and preview.endswith("…")
    assert words == len(LONG.split())
    assert preview.startswith("## Plan")


def test_a_tall_reply_of_short_lines_counts_as_long():
    tall = "\n".join(f"- item {n}" for n in range(60))
    assert long_reply(tall) is not None


def test_preview_never_leaves_a_code_block_open():
    text = "Intro paragraph.\n\n```python\n" + "print('x')\n" * 400 + "```\n\nEnd."
    preview, _ = long_reply(text)
    assert preview.count("```") % 2 == 0


def test_pdf_and_markdown_files_are_really_written(qtbot, tmp_path):
    body = "# Report\n\nHello **world**.\n\n- one\n- two"
    pdf, md = tmp_path / "out.pdf", tmp_path / "out.md"
    write_reply_file(pdf, body, "pdf")
    write_reply_file(md, body, "md")
    assert pdf.read_bytes().startswith(b"%PDF") and pdf.stat().st_size > 800
    assert md.read_text().startswith("# Report")


def archived_long_reply(window):
    window.activity_channel = window.channel_id
    window.finish_agent_response(window.workspace_id, LONG)
    window.archive_finished_agent()
    return next(m for m in window.messages.source_messages if m.agent)


def test_a_long_reply_in_the_conversation_is_a_preview_with_save_links(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    message = archived_long_reply(window)
    document = window.messages.delegate.document(message, 600)
    html = document.toHtml()
    assert "Part 11 ends here" not in document.toPlainText()  # the tail is not in the chat
    assert "Full response" in document.toPlainText() and "words" in document.toPlainText()
    assert ACTION_PREFIX + "pdf" in html and ACTION_PREFIX + "markdown-file" in html
    assert document.size().height() < 700


def test_a_short_reply_in_the_conversation_is_unchanged(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    window.activity_channel = window.channel_id
    window.finish_agent_response(window.workspace_id, SHORT)
    window.archive_finished_agent()
    message = next(m for m in window.messages.source_messages if m.agent)
    document = window.messages.delegate.document(message, 600)
    assert "Full response" not in document.toPlainText()
    assert ACTION_PREFIX + "pdf" not in document.toHtml()


def test_the_live_reply_shows_the_same_preview(qtbot, tmp_path):
    window, _ = setup(qtbot, tmp_path)
    window.activity_channel = window.channel_id
    window.finish_agent_response(window.workspace_id, LONG)
    live = window.agent_feed.reply_row.message.text()
    assert "Part 11 ends here" not in live
    assert ACTION_PREFIX + "pdf" in live and "Save as Markdown" in live


@pytest.mark.parametrize("action,kind", [("pdf", "pdf"), ("markdown-file", "md")])
def test_saving_writes_the_full_text_and_opens_it(qtbot, tmp_path, monkeypatch, action, kind):
    window, _ = setup(qtbot, tmp_path)
    message = archived_long_reply(window)
    target = tmp_path / f"saved.{kind}"
    monkeypatch.setattr(
        "PySide6.QtWidgets.QFileDialog.getSaveFileName",
        lambda *a, **k: (str(target), ""),
    )
    opened = []
    monkeypatch.setattr(
        "PySide6.QtGui.QDesktopServices.openUrl", lambda url: opened.append(url.toLocalFile())
    )
    window.messages.activate_message_link(message, ACTION_PREFIX + action)
    assert target.is_file() and opened == [str(target)]
    if kind == "md":
        assert "Part 11 ends here" in target.read_text()  # the whole reply, not the preview
    else:
        assert target.read_bytes().startswith(b"%PDF")
    assert "Saved" in window.notice.text()


def test_cancelling_the_save_dialog_writes_nothing(qtbot, tmp_path, monkeypatch):
    window, _ = setup(qtbot, tmp_path)
    message = archived_long_reply(window)
    monkeypatch.setattr("PySide6.QtWidgets.QFileDialog.getSaveFileName", lambda *a, **k: ("", ""))
    window.messages.activate_message_link(message, ACTION_PREFIX + "pdf")
    assert not list(Path(tmp_path).glob("*.pdf"))
