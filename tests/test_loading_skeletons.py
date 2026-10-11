"""Loading placeholders stay responsive and release the screen after failures."""

from threading import Event

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from test_account import dialog

from aedrova.desktop.loading import set_loading
from aedrova.desktop.theme import DARK, LIGHT, palette, stylesheet


def test_loading_success_and_failure_restore_content(qtbot, tmp_path):
    account = dialog(qtbot, tmp_path)
    for fail in (False, True):
        release = Event()

        def operation(release=release, fail=fail):
            release.wait(timeout=3)
            if fail:
                raise ValueError("private-provider-detail")
            return True

        account.run(operation, lambda _: account.status.setText("Ready"))
        try:
            assert account._loading_skeleton.isVisible()
            assert not account.status.isVisible()
            account.resize(900, 650)
            qtbot.waitUntil(lambda: account._loading_skeleton.size() == account.pages.size())
        finally:
            release.set()
        qtbot.waitUntil(lambda: not account.busy)
        assert not account._loading_skeleton.isVisible()
        assert not account._loading_skeleton.timer.isActive()
        assert account.pages.isEnabled()
        assert account.status.isVisible()
        assert "private-provider-detail" not in account.status.text()


def test_skeleton_theme_reduced_motion_and_close(qtbot):
    owner = QWidget()
    owner.reduced_motion = True
    qtbot.addWidget(owner)
    layout = QVBoxLayout(owner)
    target = QWidget()
    owner.status = QLabel("Status")
    layout.addWidget(target)
    layout.addWidget(owner.status)
    owner.resize(640, 520)
    owner.show()
    for theme in (LIGHT, DARK):
        owner.theme = theme
        owner.setPalette(palette(theme))
        owner.setStyleSheet(stylesheet(theme))
        set_loading(owner, target, True, "gallery")
        skeleton = owner._loading_skeleton
        assert skeleton.isVisible()
        assert not skeleton.timer.isActive()
        frame = skeleton.grab().toImage()
        assert frame.pixelColor(1, 1).name() == theme.bg.lower()
        assert frame.pixelColor(30, 35) != frame.pixelColor(1, 1)
        set_loading(owner, target, False)
    owner.reduced_motion = False
    set_loading(owner, target, True, "feed")
    assert skeleton.timer.isActive()
    owner.close()
    assert not skeleton.timer.isActive()
