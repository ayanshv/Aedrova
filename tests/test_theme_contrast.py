"""Text in both themes stays readable: WCAG AA (4.5:1) for every text and surface pairing."""

import pytest

from aedrova.desktop.theme import DARK, LIGHT


def luminance(color):
    color = color.lstrip("#")
    channels = [int(color[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(first, second):
    high, low = sorted((luminance(first), luminance(second)), reverse=True)
    return (high + 0.05) / (low + 0.05)


SURFACES = ("bg", "surface", "canvas", "sidebar", "hover")


@pytest.mark.parametrize("theme", [LIGHT, DARK], ids=lambda t: t.name)
@pytest.mark.parametrize("ink", ["text", "secondary", "muted", "link"])
@pytest.mark.parametrize("surface", SURFACES)
def test_text_roles_meet_aa_on_every_surface(theme, ink, surface):
    ratio = contrast(getattr(theme, ink), getattr(theme, surface))
    assert ratio >= 4.5, f"{theme.name}: {ink} on {surface} is {ratio:.2f}:1"


@pytest.mark.parametrize("theme", [LIGHT, DARK], ids=lambda t: t.name)
def test_selected_and_primary_text_meet_aa(theme):
    assert contrast(theme.accent_text, theme.accent_bg) >= 4.5
    assert contrast(theme.primary_text, theme.accent) >= 4.5
    assert contrast(theme.muted, theme.accent_bg) >= 4.5
