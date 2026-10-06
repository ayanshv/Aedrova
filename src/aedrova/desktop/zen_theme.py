"""Shared appearance tokens for onboarding and its painted illustrations."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from aedrova.desktop.theme import DARK, LIGHT, stylesheet


def resolve_theme(mode, scheme=None):
    if scheme is None:
        scheme = QApplication.instance().styleHints().colorScheme()
    return DARK if mode == "dark" or (mode == "system" and scheme == Qt.ColorScheme.Dark) else LIGHT


def visual_theme(widget):
    while widget is not None:
        theme = getattr(widget, "theme", None)
        if theme is not None:
            return theme
        widget = widget.parentWidget()
    return LIGHT


def tone(theme, color):
    if theme.name == "light":
        return color
    value = color.upper()
    if value in {"WHITE", "#FFFFFF", "#F7FAFE"}:
        return theme.bg
    if value in {"#F5F5F7", "#F0F7FF", "#F2F8FF", "#F4F9FF", "#EFF6FF"}:
        return theme.surface
    if value in {"#EDF5FF", "#EAF3FF", "#E0EFFF", "#E2EFFF", "#DCEFFF", "#DFEFFF", "#CBE5FF"}:
        return theme.accent_bg
    if value == "#E8E4FB":
        return "#29263C"
    if value in {"#283A52", "#1D1D1F"}:
        return theme.text
    if value in {"#176CCD", "#175FAD", "#1877DB", "#2367A7", "#1478E8", "#23558A"}:
        return theme.accent_text
    if value == "#4D7198":
        return theme.secondary
    if value in {"#4092E7", "#368BE8"}:
        return theme.accent
    if value in {
        "#DFE7F0",
        "#D8E9FB",
        "#B5D5FA",
        "#DEE7F0",
        "#DCE9F6",
        "#E2ECF6",
        "#DAE7F5",
        "#CAE1F8",
        "#D7E7F7",
        "#C6DEF6",
        "#E8E8EB",
        "#E2EBF5",
        "#C9DEF4",
    }:
        return theme.border
    return color


def onboarding_styles(theme):
    surface = tone(theme, "#F0F7FF")
    hover = "#E7F2FF" if theme.name == "light" else "#243D58"
    pressed = "#D6E9FF" if theme.name == "light" else "#2D4C6D"
    return (
        stylesheet(theme)
        + f"""
        QDialog {{background:{theme.bg};}}
        QScrollArea#ZenSettings {{background:transparent;border:0;}}
        QFrame#ZenSettingsBody {{background:{theme.bg};border:1px solid {tone(theme, "#E2EBF5")};
            border-radius:24px;}}
        QFrame#ZenSettingsBody QLabel[role="muted"] {{font-size:15px;}}
        QPushButton {{background:{surface};color:{tone(theme, "#23558A")};
            text-align:center;border:1px solid {tone(theme, "#C9DEF4")};
            border-radius:18px;padding:14px 24px;}}
        QPushButton:hover {{background:{hover};}}
        QPushButton:pressed {{background:{pressed};}}
        QPushButton:focus {{border:2px solid {tone(theme, "#4092E7")};}}
        QPushButton:disabled {{color:{theme.muted};background:{theme.surface};}}
        QPushButton#ZenSkip {{border:0;background:transparent;color:{theme.muted};padding:8px;}}
    """
    )
