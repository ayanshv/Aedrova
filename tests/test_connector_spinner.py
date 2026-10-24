from aedrova.desktop.spinner import Spinner


def test_spinner_stops_when_idle_or_hidden(qtbot):
    spinner = Spinner()
    qtbot.addWidget(spinner)
    spinner.set_active(True)
    assert spinner.isVisible() and spinner.timer.isActive()
    spinner.hide()
    assert not spinner.timer.isActive()
    spinner.set_active(False)
    assert not spinner.isVisible() and not spinner.timer.isActive()
