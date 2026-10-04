"""Tour navigation cannot perform product actions or share state across accounts."""

from types import SimpleNamespace

import pytest
from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import QWidget

from aedrova.desktop.onboarding import FEATURES, STEPS, SetupDialog, account_key
from aedrova.desktop.window import AedrovaWindow


@pytest.fixture
def window(qtbot, tmp_path):
    widget = AedrovaWindow(
        settings=QSettings(str(tmp_path / "guide.ini"), QSettings.Format.IniFormat)
    )
    qtbot.addWidget(widget)
    widget.show()
    qtbot.waitExposed(widget)
    return widget


def test_implemented_function_coverage():
    expected = {
        "workspaces",
        "channels",
        "invitations",
        "roles",
        "nickname",
        "unread",
        "direct_messages",
        "messages",
        "threads",
        "history",
        "search",
        "decisions",
        "sources",
        "attachments",
        "save_files",
        "project",
        "provider",
        "workflow",
        "permissions",
        "ide",
        "repository",
        "mentions",
        "builds",
        "context",
        "progress",
        "queue",
        "recovery",
        "usage",
        "cancel",
        "approvals",
        "review",
        "apply",
        "preview",
        "github",
        "devices",
        "screen_preview",
        "calls",
        "camera",
        "microphone",
        "sharing",
        "participants",
        "leave_call",
        "account",
        "settings",
        "appearance",
        "accessibility",
        "profile",
        "billing",
        "allowance",
        "logout",
        "help",
        "updates",
    }
    assert FEATURES == expected
    assert len({step.title for step in STEPS}) == len(STEPS)


@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("size", [(900, 650), (1440, 940)])
def test_all_steps_fit_and_do_not_send_or_build(window, qtbot, monkeypatch, theme, size):
    def forbidden(*args):
        pytest.fail("Tour must not trigger a build, message, invitation or external action")

    for action in ("send_message", "start_agent_request", "create_workspace", "show_account"):
        monkeypatch.setattr(window, action, forbidden)
    window.set_theme(theme)
    window.resize(*size)
    window.set_reduced_motion(True)
    window.show_tour()
    tour = window.tour
    for index in range(len(STEPS)):
        tour.show_step(index)
        qtbot.wait(5)
        assert tour.rect().contains(tour.card.geometry())
        assert tour.card.graphicsEffect() is None
        assert tour.next.isVisible()
        assert tour.heading.text() == STEPS[index].title
        if not tour.target_rect.isEmpty():
            assert tour.rect().contains(tour.target_rect)
        assert not tour.grab().isNull()
    tour.advance()
    assert window.tour is None
    assert window.settings.value(account_key(window) + "/status") == "completed"


def test_pause_resume_chapters_and_account_isolation(window, qtbot):
    window.current_user = lambda: SimpleNamespace(id="one")
    window.show_tour()
    window.tour.show_step(8)
    window.activateWindow()
    qtbot.wait(10)
    qtbot.keyClick(window.tour.next, Qt.Key.Key_Escape)
    assert window.tour is None
    window.show_tour()
    assert window.tour.index == 8
    window.tour.chapters.setCurrentText("Meet")
    assert STEPS[window.tour.index].chapter == "Meet"
    window.tour.finish("paused")
    window.current_user = lambda: SimpleNamespace(id="two")
    window.show_tour()
    assert window.tour.index == 0
    window.tour.finish("skipped")
    window.current_user = lambda: SimpleNamespace(id="one")
    window.show_tour()
    assert STEPS[window.tour.index].chapter == "Meet"
    window.tour.finish("paused")


def test_hidden_target_does_not_get_spotlight(window, qtbot):
    window.sidebar.hide()
    window.show_tour()
    window.tour.show_step(0)
    assert window.tour.target_rect.isEmpty()
    window.tour.finish("paused")


def test_setup_back_skip_and_preferences(window, qtbot):
    setup = SetupDialog(window)
    qtbot.addWidget(setup)
    setup.show()
    assert not setup.back.isEnabled()
    setup.advance()
    from aedrova.desktop.controls import ChoiceBox

    appearance = setup.content.findChild(ChoiceBox)
    appearance.setCurrentIndex(appearance.findData("dark"))
    assert window.theme_mode == "dark"
    setup.advance()
    setup.back.click()
    assert setup.step == 1
    setup.defer()
    assert window.settings.value(account_key(window) + "/deferred", False, type=bool)
    assert not window.settings.value(account_key(window) + "/setup", False, type=bool)


def test_completed_tour_can_be_replayed_from_start(window):
    window.show_tour()
    window.tour.show_step(len(STEPS) - 1)
    window.tour.advance()
    window.show_tour()
    assert window.tour.index == 0
    window.tour.finish("skipped")


@pytest.mark.parametrize("theme", ["light", "dark"])
def test_setup_controls_stay_below_description_with_motion(window, qtbot, theme):
    window.set_theme(theme)
    window.set_reduced_motion(False)
    setup = SetupDialog(window)
    qtbot.addWidget(setup)
    setup.show()
    for step in (0, 1, 2, 3, 2, 1, 0):
        setup.show_step(step)
        qtbot.wait(230)
        assert setup.content.mapToGlobal(setup.content.rect().topLeft()).y() >= (
            setup.description.mapToGlobal(setup.description.rect().bottomLeft()).y()
        )
        assert setup.rect().contains(setup.content.geometry())
        for child in setup.content.findChildren(QWidget):
            if child.isVisible() and child.parentWidget() is setup.content:
                assert setup.content.rect().contains(child.geometry())
    setup.reject()
