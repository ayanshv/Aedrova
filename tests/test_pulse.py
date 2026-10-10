"""Native Pulse journeys, responsive rendering and return to existing conversation."""

import time
from pathlib import Path

import pytest
from test_connected import setup

from aedrova.desktop.pulse import ActivityChart


def overview():
    now = int(time.time())
    return {
        "workspace": "w",
        "period": "7d",
        "sources": [
            {
                "id": "github",
                "name": "GitHub",
                "provider": "github",
                "status": "Connected",
                "last_sync": now,
                "cached": 1,
                "version": 1,
            }
        ],
        "metrics": [
            {
                "id": "github:changes",
                "metric": "changes",
                "category": "Engineering",
                "label": "Commits observed",
                "value": 3,
                "unit": "observed",
                "period": "7d",
                "dot": "github",
                "dot_name": "GitHub",
                "updated_at": now,
                "stale": False,
                "coverage": "Most recent 10 records; no complete-history claim",
                "comparison": "Unavailable: bounded source history",
                "trend": [0, 0, 1, 0, 1, 0, 1],
                "citation": "dot:github:changes",
                "source_url": "https://github.com/owner/repo",
                "items": [
                    {
                        "id": "1",
                        "title": "Improve onboarding",
                        "detail": "Review the sign-in handoff",
                        "timestamp": now,
                    }
                ],
            }
        ],
        "signals": [
            {
                "metric_id": "github:changes",
                "source": "GitHub",
                "title": "Improve onboarding",
                "timestamp": now,
            }
        ],
    }


def page(qtbot, tmp_path, monkeypatch):
    window, service = setup(qtbot, tmp_path)
    window.account_dialog.snapshot["dots"] = [
        {
            "id": "github",
            "workspace_id": "w",
            "name": "GitHub",
            "provider": "github",
            "resource": "owner/repo",
            "version": 1,
            "shape": "round",
            "color": "#4388F5",
        }
    ]
    fixture_snapshot = dict(window.account_dialog.snapshot)
    service.snapshot = lambda: fixture_snapshot
    window._load_channel()
    service.fork_for_context = lambda: service
    service.close_context = lambda: None
    requests = []

    class API:
        def request(self, path, body=None, **kwargs):
            requests.append((path, body))
            return overview()

    monkeypatch.setattr("aedrova.desktop.pulse.client", lambda _: API())
    window.connected.enqueue = lambda key, operation, complete, **kwargs: (
        complete(operation()),
        True,
    )[1]
    window.open_pulse()
    qtbot.waitUntil(lambda: bool(window.pulse_page.data) and not window.pulse_page.pending)
    return window, window.pulse_page, requests


def test_primary_navigation_and_conversation_handoff(qtbot, tmp_path, monkeypatch):
    window, pulse, requests = page(qtbot, tmp_path, monkeypatch)
    assert window.pages.currentWidget() is pulse
    assert window.header.isHidden() and window.primary_navigation.isHidden()
    assert all(not tab.isChecked() for tab in window.tab_buttons)
    assert window.dot_connection_states[("u", "github", 1)]["status"] == "Connected"
    assert all(body is None for _, body in requests)  # Opening never refreshes every provider.
    pulse.ask()
    assert window.pages.currentIndex() == 0 and not window.header.isHidden()
    assert window.composer.editor.toPlainText().startswith("@Aedrova")
    assert window.channel.messages[0].body == "Hello"


def test_pin_order_scope_drilldown_and_draft_actions(qtbot, tmp_path, monkeypatch):
    window, pulse, _ = page(qtbot, tmp_path, monkeypatch)
    metric = pulse.data["metrics"][0]
    pulse.pin(metric)
    assert pulse.pins() == [metric["id"]]
    pulse.user = "another-user"
    assert not pulse.pins()
    pulse.user = "u"
    pulse.open_detail(metric)
    assert pulse.detail.isVisible()
    pulse.detail.accept()
    pulse.discuss(metric)
    assert metric["coverage"] in window.composer.editor.toPlainText()
    assert "dot:github:changes" in window.composer.editor.toPlainText()
    pulse.build(metric)
    assert window.composer.editor.toPlainText() == "@Aedrova, build "
    assert not getattr(window, "build_dialog", None)  # Draft only; no unattended build.


def test_investigation_uses_existing_central_agent(qtbot, tmp_path, monkeypatch):
    window, pulse, _ = page(qtbot, tmp_path, monkeypatch)
    tasks = []
    monkeypatch.setattr(
        "aedrova.desktop.dot_analysis.start_analysis", lambda w, task: tasks.append(task)
    )
    pulse.investigate(pulse.data["metrics"][0])
    assert window.pages.currentIndex() == 0
    assert "@GitHub" in tasks[0] and "causality" in tasks[0]


def test_selected_refresh_and_periods_do_not_fan_out(qtbot, tmp_path, monkeypatch):
    _, pulse, requests = page(qtbot, tmp_path, monkeypatch)
    pulse.load("github")
    qtbot.waitUntil(lambda: not pulse.pending)
    assert requests[-1][1]["dot"] == "github"
    for index in range(5):
        pulse.period.setCurrentIndex(index)
        qtbot.waitUntil(lambda: not pulse.pending)
    assert pulse.period.currentData() == "12m"
    assert requests[-1][1] is None and "12m" in requests[-1][0]


def test_logout_clears_privileged_overview_and_detail(qtbot, tmp_path, monkeypatch):
    window, pulse, _ = page(qtbot, tmp_path, monkeypatch)
    pulse.open_detail(pulse.data["metrics"][0])
    window.connected.disconnect()
    assert not pulse.data and pulse.detail is None


@pytest.mark.parametrize("mode", ["light", "dark"])
def test_visual_states_at_laptop_and_desktop_widths(qtbot, tmp_path, monkeypatch, mode):
    window, pulse, _ = page(qtbot, tmp_path, monkeypatch)
    window.set_theme(mode)
    output = Path("work/pulse")
    output.mkdir(parents=True, exist_ok=True)
    for width, height in [(1440, 940), (900, 650)]:
        window.resize(width, height)
        qtbot.wait(50)
        assert pulse.width() > 450
        assert pulse.scroll.horizontalScrollBar().maximum() == 0
        assert pulse.findChildren(ActivityChart)
        assert window.grab().save(str(output / f"{mode}-{width}.png"))
    pulse.open_detail(pulse.data["metrics"][0])
    qtbot.wait(30)
    assert pulse.detail.grab().save(str(output / f"{mode}-detail.png"))


def test_read_error_clears_old_data_and_open_detail(qtbot, tmp_path, monkeypatch):
    _, pulse, _ = page(qtbot, tmp_path, monkeypatch)
    pulse.open_detail(pulse.data["metrics"][0])
    detail = pulse.detail

    class API:
        def request(self, *args, **kwargs):
            raise RuntimeError("Access changed. Reconnect this source.")

    monkeypatch.setattr("aedrova.desktop.pulse.client", lambda _: API())
    pulse.load()
    qtbot.waitUntil(lambda: not pulse.pending)
    assert not pulse.data and not detail.isVisible()
    assert "Access changed" in pulse.status.text()


def test_empty_state_does_not_invent_metrics(qtbot, tmp_path, monkeypatch):
    _, pulse, _ = page(qtbot, tmp_path, monkeypatch)
    pulse.data = {"metrics": [], "sources": [], "signals": []}
    pulse.render()
    assert not pulse.findChildren(ActivityChart) or all(
        not chart.isVisible() for chart in pulse.findChildren(ActivityChart)
    )
    from PySide6.QtWidgets import QLabel

    assert any(widget.text() == "Connect your stack." for widget in pulse.findChildren(QLabel))


def test_source_filter_metric_selection_and_records(qtbot, tmp_path, monkeypatch):
    from PySide6.QtWidgets import QLabel

    _, pulse, _ = page(qtbot, tmp_path, monkeypatch)
    second = dict(
        pulse.data["metrics"][0],
        id="another:changes",
        dot="another",
        dot_name="Second repo",
        value=8,
    )
    pulse.data["metrics"].append(second)
    pulse.data["sources"].append(dict(pulse.data["sources"][0], id="another", name="Second repo"))
    pulse.select_metric(second["id"])
    assert pulse.selected_metric == second["id"]
    pulse.filter_source("github")
    assert pulse.selected_metric == "github:changes"
    pulse.switch_view(True)
    qtbot.wait(20)
    assert any(
        w.text() == "Improve onboarding" and w.isVisible() for w in pulse.findChildren(QLabel)
    )
    assert all(not chart.isVisible() for chart in pulse.findChildren(ActivityChart))
    pulse.filter_source("")
    pulse.switch_view(False)
    qtbot.wait(20)
    assert any(chart.isVisible() for chart in pulse.findChildren(ActivityChart))


def test_chart_hover_shows_observed_interval(qtbot, tmp_path, monkeypatch):
    from PySide6.QtCore import QEvent, QPointF, Qt
    from PySide6.QtGui import QMouseEvent
    from PySide6.QtWidgets import QApplication

    _, pulse, _ = page(qtbot, tmp_path, monkeypatch)
    qtbot.wait(30)
    chart = next(c for c in pulse.findChildren(ActivityChart) if c.isVisible())
    position = QPointF(chart.width() - 20, 40)
    event = QMouseEvent(
        QEvent.Type.MouseMove,
        position,
        position,
        Qt.MouseButton.NoButton,
        Qt.MouseButton.NoButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QApplication.sendEvent(chart, event)
    assert chart.hover == len(chart.values) - 1
    QApplication.sendEvent(chart, QEvent(QEvent.Type.Leave))
    assert chart.hover is None
