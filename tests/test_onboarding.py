"""The tour is short, tags real controls, and cannot perform product actions."""

from types import SimpleNamespace

import pytest
from PySide6.QtCore import QSettings, Qt

from aedrova.desktop.onboarding import STEPS, account_key, resolve
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


def test_the_tour_is_short_and_every_tag_is_one_line():
    assert 6 <= len(STEPS) <= 10
    assert len({step.title for step in STEPS}) == len(STEPS)
    for step in STEPS:
        assert len(step.title.split()) <= 4, step.title
        assert len(step.text.split()) <= 14, step.text


def test_the_tour_covers_the_parts_people_use_first():
    targets = {step.target for step in STEPS}
    assert {
        "workspace_title",
        "invite_teammates_button",
        "ai_team_section",
        "channel_list",
        "composer",
        "composer.permissions",
        "primary_navigation",
        "workspace_usage",
        "profile_button",
    } <= targets


@pytest.mark.parametrize("theme", ["light", "dark"])
@pytest.mark.parametrize("size", [(900, 650), (1440, 940)])
def test_every_visible_tag_fits_and_nothing_is_sent_or_built(
    window, qtbot, monkeypatch, theme, size
):
    def forbidden(*args):
        pytest.fail("Tour must not trigger a build, message, invitation or external action")

    for action in ("send_message", "start_agent_request", "create_workspace", "show_account"):
        monkeypatch.setattr(window, action, forbidden)
    window.set_theme(theme)
    window.resize(*size)
    window.set_reduced_motion(True)
    window.show_tour()
    tour = window.tour
    seen = []
    for index in range(len(STEPS)):
        tour.show_step(index)
        qtbot.wait(5)
        step = STEPS[tour.index]
        if not resolve(window, step.target):
            continue
        seen.append(step.title)
        assert tour.rect().contains(tour.card.geometry())
        assert not tour.target_rect.isEmpty()
        assert tour.parentWidget().rect().contains(tour.target_rect)
        assert not tour.card.geometry().intersects(tour.target_rect), step.title
        assert tour.heading.text() == step.title
        assert not tour.grab().isNull()
    assert len(seen) >= 6
    tour.advance()
    while window.tour is not None:
        tour.advance()
    assert window.settings.value(account_key(window) + "/status") == "completed"


def test_steps_with_nothing_to_show_are_skipped_not_faked(window, qtbot):
    window.set_reduced_motion(True)
    window.workspace_usage.hide()  # no AI allowance in a local preview
    window.show_tour()
    tour = window.tour
    titles = []
    tour.show_step(0)
    for _ in range(len(STEPS)):
        titles.append(tour.heading.text())
        previous = tour.index
        tour.advance()
        if window.tour is None:
            break
        assert tour.index != previous
    assert "Your AI allowance" not in titles
    assert tour.progress.text().endswith(str(len(titles))) or window.tour is None


def test_pause_resume_and_account_isolation(window, qtbot):
    window.set_reduced_motion(True)
    window.current_user = lambda: SimpleNamespace(id="one")
    window.show_tour()
    window.tour.show_step(3)
    stopped_at = window.tour.index
    window.activateWindow()
    qtbot.wait(10)
    qtbot.keyClick(window.tour.next, Qt.Key.Key_Escape)
    assert window.tour is None
    window.show_tour()
    assert window.tour.index == stopped_at
    window.tour.finish("paused")
    window.current_user = lambda: SimpleNamespace(id="two")
    window.show_tour()
    assert window.tour.index == 0
    window.tour.finish("skipped")
    window.current_user = lambda: SimpleNamespace(id="one")
    window.show_tour()
    assert window.tour.index == stopped_at
    window.tour.finish("paused")


def test_completed_tour_can_be_replayed_from_the_start(window):
    window.set_reduced_motion(True)
    window.show_tour()
    while window.tour is not None:
        window.tour.advance()
    window.show_tour()
    assert window.tour.index == 0
    window.tour.finish("skipped")


def test_first_run_offers_the_tour_once_and_never_after_it_was_answered(window):
    window.set_reduced_motion(True)
    window.start_first_tour()
    assert window.tour is not None
    window.tour.finish("skipped")
    window.start_first_tour()
    assert window.tour is None  # skipped means skipped
    window.settings.setValue(account_key(window) + "/status", "paused")
    window.start_first_tour()
    assert window.tour is None  # a paused tour waits for the person, not for us


def test_clicking_the_dimmed_window_does_nothing(window, qtbot):
    window.set_reduced_motion(True)
    window.show_tour()
    tour = window.tour
    before = tour.index
    qtbot.mouseClick(tour, Qt.MouseButton.LeftButton, pos=tour.rect().center())
    assert window.tour is tour and tour.index == before
    tour.finish("paused")


def test_the_tour_waits_for_an_open_dialog_instead_of_being_skipped(window, qtbot):
    from PySide6.QtWidgets import QDialog

    window.set_reduced_motion(True)
    dialog = QDialog(window)
    qtbot.addWidget(dialog)
    dialog.show()
    window.start_first_tour()
    assert window.tour is None
    dialog.close()
    qtbot.waitUntil(lambda: window.tour is not None, timeout=3000)
    window.tour.finish("skipped")
