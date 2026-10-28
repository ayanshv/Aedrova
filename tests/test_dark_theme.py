"""Exercise rendered message states and media fidelity, not just stylesheet strings."""

import pytest
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap
from PySide6.QtWidgets import QStyle, QStyleOptionViewItem

from aedrova.desktop.conversation import MessageView
from aedrova.desktop.state import Message
from aedrova.desktop.theme import DARK, LIGHT


def contrast(a, b):
    def luminance(color):
        values = QColor(color).getRgbF()[:3]
        values = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in values]
        return sum(v * weight for v, weight in zip(values, (0.2126, 0.7152, 0.0722), strict=True))

    first, second = sorted((luminance(a), luminance(b)))
    return (second + 0.05) / (first + 0.05)


def test_dark_text_and_action_contrast():
    for surface in (DARK.canvas, DARK.bg, DARK.sidebar, DARK.surface, DARK.elevated):
        for text in (DARK.text, DARK.secondary, DARK.muted):
            assert contrast(text, surface) >= 4.5
    for action in (DARK.accent, DARK.accent_hover, DARK.accent_pressed):
        assert contrast(DARK.primary_text, action) >= 4.5
    assert contrast(DARK.accent, DARK.surface) >= 3
    assert len({DARK.canvas, DARK.bg, DARK.sidebar, DARK.surface, DARK.elevated}) == 5


def test_initial_theme_and_switching_preserve_preferences(qtbot, tmp_path):
    from PySide6.QtCore import QSettings

    from aedrova.desktop.window import AedrovaWindow

    settings = QSettings(str(tmp_path / "theme.ini"), QSettings.Format.IniFormat)
    settings.setValue("appearance", "dark")
    settings.setValue("reduceMotion", True)
    window = AedrovaWindow(settings=settings)
    qtbot.addWidget(window)
    assert window.theme is DARK
    assert window.messages.delegate.theme is DARK
    card = window._card("Meeting devices", "Checks stay local.")
    qtbot.addWidget(card)
    assert card.theme is DARK  # Surfaces created after the theme switch inherit it.
    window.set_theme("light")
    assert window.theme is LIGHT and settings.value("appearance") == "light"
    window.set_theme("system")
    assert settings.value("appearance") == "system"
    assert window.reduced_motion
    window.set_theme("dark", persist=False)
    assert settings.value("appearance") == "system"


def render(view, message, theme, state):
    view.set_theme(theme)
    view.show_messages([message])
    image = QImage(1100, 350, QImage.Format.Format_ARGB32)
    image.fill(QColor(theme.bg))
    option = QStyleOptionViewItem()
    option.rect = QRect(0, 0, 1100, 350)
    option.state = state
    painter = QPainter(image)
    view.delegate.paint(painter, option, view.model().index(0, 0))
    painter.end()
    return image


@pytest.mark.parametrize(
    "state",
    [
        QStyle.StateFlag.State_MouseOver,
        QStyle.StateFlag.State_Selected,
        QStyle.StateFlag.State_Selected | QStyle.StateFlag.State_HasFocus,
    ],
)
def test_dark_message_states_do_not_paint_full_width_stripes(qtbot, state):
    view = MessageView()
    qtbot.addWidget(view)
    image = render(view, Message("a", "Maya", "M", "09:00", "Hello"), DARK, state)
    assert image.pixelColor(1080, 100).name() == DARK.bg.lower()


@pytest.mark.parametrize("theme", [LIGHT, DARK])
def test_transparent_image_has_neutral_backing_and_preserves_pixels(qtbot, theme):
    view = MessageView()
    qtbot.addWidget(view)
    source = QPixmap(100, 80)
    source.fill(Qt.GlobalColor.transparent)
    painter = QPainter(source)
    painter.fillRect(20, 20, 60, 40, QColor("#173b27"))
    painter.end()
    view.attachment_previews = {"image": source}
    message = Message(
        "a", "Maya", "M", "09:00", "Proof", attachment="check.png", attachment_id="image"
    )
    image = render(view, message, theme, QStyle.StateFlag.State_Enabled)
    document = view.delegate.document(message, 1100 - 94)
    bottom = view.delegate.body_offset(view.model().index(0, 0)) + document.size().height()
    top = int(bottom + 48 + (170 - 58 - 80) / 2)
    assert image.pixelColor(86 + 2, top + 2).name() == theme.preview.lower()
    assert image.pixelColor(86 + 30, top + 30).name() == "#173b27"
