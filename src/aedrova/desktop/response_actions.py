"""Render local controls for agent replies without treating model links as actions."""

import json
import re
from base64 import b64encode
from functools import lru_cache
from html import escape

from PySide6.QtCore import QBuffer, QIODevice, QUrl
from PySide6.QtGui import QColor, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextDocument

from aedrova.desktop.icons import icon

ACTION_PREFIX = "aedrova-reply:"
SOURCE_PREFIX = "aedrova-source:"
_DASHES = str.maketrans("‐‑‒–—−", "------")
_SOURCE = re.compile(
    r"(?<![\w:/])(?:message|attachment|meeting|memory|agent[-‐‑‒–—−]work|"
    r"build[-‐‑‒–—−]review):[a-f0-9]{8}(?:[-‐‑‒–—−][a-f0-9]{4}){3}"
    r"[-‐‑‒–—−][a-f0-9]{12}(?![\w/-])|(?<![\w:/])project:[a-f0-9]{24}(?![\w/-])",
    re.IGNORECASE,
)
CHOICE_MARKER = "AEDROVA_CHOICES "
REPLY_ACTIONS = (
    ("copy", "Copy response", "copy"),
    ("good", "Good response", "thumb_up"),
    ("bad", "Bad response", "thumb_down"),
    ("more", "More options", "more_chat"),
)
REPLY_ACTION_LABELS = {ACTION_PREFIX + action: title for action, title, _ in REPLY_ACTIONS}


def citations(text):
    return tuple(
        dict.fromkeys(match[0].translate(_DASHES).lower() for match in _SOURCE.finditer(text))
    )


def compact_citations(document, *, color):
    """Change the display only. Keep identifiers intact in copied source text."""
    numbered, edits = {}, []
    block = document.begin()
    while block.isValid():
        if not block.blockFormat().nonBreakableLines():
            fragments = block.begin()
            while not fragments.atEnd():
                fragment = fragments.fragment()
                if not fragment.charFormat().isAnchor():
                    text = fragment.text()
                    for match in _SOURCE.finditer(text):
                        source = match[0].translate(_DASHES).lower()
                        number = numbered.setdefault(source, len(numbered) + 1)
                        start = len(text[:match.start()].encode("utf-16-le")) // 2
                        end = len(text[:match.end()].encode("utf-16-le")) // 2
                        edits.append((fragment.position() + start, fragment.position() + end,
                                      source, number))
                fragments += 1
        block = block.next()
    cursor = QTextCursor(document)
    for start, end, source, number in reversed(edits):
        cursor.setPosition(start)
        cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
        style = QTextCharFormat()
        style.setAnchor(True)
        style.setAnchorHref(SOURCE_PREFIX + source)
        style.setToolTip(source)
        style.setForeground(QColor(color))
        cursor.insertText(f"Source {number}", style)


@lru_cache(maxsize=48)
def action_image(name, color):
    image = icon(name, color).pixmap(40, 40).toImage()
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    image.save(buffer, "PNG")
    return "data:image/png;base64," + b64encode(bytes(buffer.data())).decode("ascii"), image


def streaming_body(text):
    body, separator, line = text.rpartition("\n")
    if separator and line and CHOICE_MARKER.startswith(line):
        return body.rstrip()
    return text.partition("\n" + CHOICE_MARKER)[0]


def response_parts(text):
    body, separator, payload = text.strip().rpartition("\n" + CHOICE_MARKER)
    if separator:
        payload, _, suffix = payload.partition("\n")
        body = "\n\n".join(part.strip() for part in (body, suffix) if part.strip())
        try:
            options = json.loads(payload)
        except ValueError:
            options = None
        if (
            isinstance(options, list)
            and 2 <= len(options) <= 5
            and all(
                isinstance(option, str)
                and 1 <= len(option.strip()) <= 240
                and "\n" not in option
                and "\r" not in option
                for option in options
            )
        ):
            options = tuple(dict.fromkeys(option.strip() for option in options))
            return body, options if len(options) >= 2 else ()
        return body, ()

    match = re.search(
        r"(?im)^(?:[^\n]*\b(?:pick|choose|select)\b[^\n]*\boption\b[^\n]*:)\s*\n"
        r"(?P<options>(?:[ \t]*\d+[.)][ \t]+[^\n]+\n?){2,})",
        text,
    )
    if not match or text[:match.start()].count("```") % 2:
        return text, ()
    options = tuple(
        re.sub(r"^[ \t]*\d+[.)][ \t]+", "", line).replace("**", "").strip()
        for line in match.group("options").splitlines()
    )
    if len(options) > 5 or any(not option or len(option) > 240 for option in options):
        return text, ()
    start, end = match.span("options")
    return (text[:start].rstrip() + "\n\n" + text[end:].lstrip()).strip(), options


def append_response_actions(
    document, options, rating, *, choice_color="#1759bf", action_color="#525d6b",
    file_summary=None, card_background="",
):
    block = document.begin()
    while block.isValid():
        fragments = block.begin()
        while not fragments.atEnd():
            fragment = fragments.fragment()
            style = fragment.charFormat()
            if style.anchorHref().casefold().startswith((ACTION_PREFIX, SOURCE_PREFIX)):
                cursor = QTextCursor(document)
                cursor.setPosition(fragment.position())
                cursor.setPosition(
                    fragment.position() + fragment.length(), QTextCursor.MoveMode.KeepAnchor
                )
                style.setAnchor(False)
                style.setAnchorHref("")
                style.setFontUnderline(False)
                cursor.setCharFormat(style)
                # Editing a fragment invalidates the current iterator. Restart the block.
                fragments = block.begin()
                continue
            fragments += 1
        block = block.next()
    compact_citations(document, color=choice_color)
    cursor = QTextCursor(document)
    cursor.movePosition(QTextCursor.MoveOperation.End)
    for index, option in enumerate(options):
        cursor.insertBlock(QTextBlockFormat(), QTextCharFormat())
        cursor.insertHtml(
            f'<a href="{ACTION_PREFIX}choice-{index}" '
            f'style="text-decoration:none;font-weight:600;color:{choice_color}">'
            f'›&nbsp; {escape(option)}</a>'
        )
    if file_summary:
        append_file_summary(cursor, file_summary, card_background)
    cursor.insertBlock(QTextBlockFormat(), QTextCharFormat())
    links, images = [], set()
    for action, title, glyph in REPLY_ACTIONS:
        selected = rating == action
        label = title + (" (selected)" if selected else "")
        url, image = action_image(glyph, choice_color if selected else action_color)
        document.addResource(QTextDocument.ResourceType.ImageResource, QUrl(url), image)
        images.add(url)
        links.append(
            f'<a href="{ACTION_PREFIX}{action}" title="{label}">'
            f'<img src="{url}" width="19" height="19" alt="{label}" /></a>'
        )
    cursor.insertHtml("&nbsp;&nbsp;&nbsp;".join(links))
    return images


def append_file_summary(cursor, summary, background):
    total, additions, deletions, files = summary
    title = f"Changed {total} " + ("file" if total == 1 else "files")
    rows = []
    for path, plus, minus in files:
        numbers = change_numbers(plus, minus)
        wrapped_path = "&#8203;".join(
            escape(path[i : i + 28]) for i in range(0, len(path), 28)
        )
        rows.append(
            f'<tr><td>{wrapped_path}</td><td align="right">{numbers}</td></tr>'
        )
    remaining = total - len(files)
    footer = f"<tr><td>+ {remaining} more</td><td></td></tr>" if remaining else ""
    cursor.insertBlock(QTextBlockFormat(), QTextCharFormat())
    cursor.insertHtml(
        f'<table cellspacing="0" cellpadding="6" width="100%" bgcolor="{background}">'
        f'<tr><td><b>{title}</b> &nbsp; {change_numbers(additions, deletions)}</td>'
        f'<td align="right"><a href="{ACTION_PREFIX}changes">Review changes</a></td></tr>'
        + "".join(rows) + footer + "</table>"
    )
    cursor.movePosition(QTextCursor.MoveOperation.End)


def change_numbers(plus, minus):
    if plus is None:
        return "No line count"
    return f'<span style="color:#238852">+{plus}</span> <span style="color:#d84f5f">−{minus}</span>'
