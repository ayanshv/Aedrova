"""A web address in a message is a blue, underlined link that opens the site on a click."""

import pytest
from PySide6.QtCore import QSettings

from aedrova.desktop.conversation import autolink_urls
from aedrova.desktop.state import Message
from aedrova.desktop.window import AedrovaWindow


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("see https://example.com/a?b=1 now", "see <https://example.com/a?b=1> now"),
        ("go to https://example.com.", "go to <https://example.com>."),
        ("(https://x.io/p)", "(<https://x.io/p>)"),
        (
            "wiki https://en.wikipedia.org/wiki/Foo_(bar) ok",
            "wiki <https://en.wikipedia.org/wiki/Foo_(bar)> ok",
        ),
        ("https://a.com/x), and https://b.com!", "<https://a.com/x>), and <https://b.com>!"),
    ],
)
def test_bare_addresses_become_links_without_trailing_punctuation(text, expected):
    assert autolink_urls(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "[name](https://a.com)",
        "<https://b.com>",
        "`https://c.com`",
        "```\nhttps://d.com\n```",
        "![image](https://f.com/i.png)",
        "no address here, just https:// text",
    ],
)
def test_existing_links_code_and_images_are_left_alone(text):
    assert autolink_urls(text) == text


def message_window(qtbot, tmp_path):
    window = AedrovaWindow(settings=QSettings(str(tmp_path / "ui.ini"), QSettings.Format.IniFormat))
    qtbot.addWidget(window)
    return window


def test_a_pasted_address_is_a_blue_underlined_link(qtbot, tmp_path):
    window = message_window(qtbot, tmp_path)
    delegate = window.messages.delegate
    message = Message("1", "Ann", "A", "1:00", "go to https://example.com/a?x=1.")
    document = delegate.document(message, 600)
    assert document.toPlainText().startswith("go to https://example.com/a?x=1")
    style = document.find("example.com").charFormat()
    assert style.isAnchor() and style.anchorHref() == "https://example.com/a?x=1"
    assert style.fontUnderline()
    assert style.foreground().color().name().lower() == delegate.theme.link.lower()
    plain = document.find("go to").charFormat()
    assert not plain.isAnchor() and not plain.fontUnderline()
    assert "Link preview" not in document.toPlainText()  # the address itself is the link


def test_clicking_a_link_opens_the_site_and_other_schemes_do_nothing(qtbot, tmp_path, monkeypatch):
    window = message_window(qtbot, tmp_path)
    opened = []
    monkeypatch.setattr(window.messages, "open_link", opened.append)
    message = Message("1", "Ann", "A", "1:00", "https://example.com")
    assert window.messages.activate_message_link(message, "https://example.com")
    assert not window.messages.activate_message_link(message, "file:///etc/passwd")
    assert not window.messages.activate_message_link(message, "javascript:alert(1)")
    assert opened == ["https://example.com"]
