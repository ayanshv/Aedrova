"""One icon set and one motion language."""

import re
from pathlib import Path

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication, QWidget

from aedrova.desktop import motion

DESKTOP = Path(motion.__file__).parent


def test_button_labels_carry_no_typed_arrows():
    """Arrows and chevrons are drawn icons, never characters inside a button's text."""
    pattern = re.compile(r'button\(\s*f?"[^"]*[→↗‹›⌄▸▾][^"]*"')
    offenders = [
        f"{path.name}: {match.group(0)}"
        for path in DESKTOP.glob("*.py")
        for match in pattern.finditer(path.read_text())
    ]
    assert offenders == []


def test_motion_helpers_do_nothing_when_motion_is_reduced(qtbot):
    app = QApplication.instance()
    widget = QWidget()
    qtbot.addWidget(widget)
    previous = app.property("reduceMotion")
    try:
        app.setProperty("reduceMotion", True)
        assert motion.reduced()
        assert motion.fade_in(widget) is None and widget.graphicsEffect() is None
        assert motion.fade_in_window(widget) is None and widget.windowOpacity() == 1.0
        app.setProperty("reduceMotion", False)
        animation = motion.fade_in(widget)
        assert animation is not None and animation.duration() == motion.BASE
    finally:
        app.setProperty("reduceMotion", previous)


def test_three_durations_only(qtbot):
    assert (motion.FAST, motion.BASE, motion.SLOW) == (120, 180, 260)
    assert isinstance(QObject(), QObject)


def test_inset_row_draws_its_chevron(qtbot):
    from aedrova.desktop.dialogs import InsetRow

    row = InsetRow("settings", "Manage buds", "2 Buds")
    qtbot.addWidget(row)
    assert not row.chevron.pixmap().isNull()
    assert row.chevron.text() == ""  # a drawn icon, not a typed "›"
