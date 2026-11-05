"""Presentation polish retains the original onboarding and real activation authority."""

from PySide6.QtWidgets import QWidget
from test_connected import setup

from aedrova.agents.managed import ManagedClient
from aedrova.desktop.onboarding_motion import OnboardingStack
from aedrova.desktop.preferences import SettingsDialog


def test_motion_keeps_navigation_immediate_and_respects_reduced_motion(qtbot):
    host = QWidget()
    host.reduced_motion = True
    stack = OnboardingStack(host)
    stack.addWidget(QWidget())
    stack.addWidget(QWidget())
    qtbot.addWidget(host)
    host.resize(320, 240)
    stack.resize(320, 240)
    host.show()
    stack.show()
    qtbot.wait(10)
    stack.setCurrentIndex(1)
    assert stack.currentIndex() == 1 and stack.overlay is None
    host.reduced_motion = False
    stack.setCurrentIndex(0)
    assert stack.currentIndex() == 0 and stack.overlay is not None
    qtbot.waitUntil(lambda: stack.overlay is None)


def test_free_activation_is_explicit_scoped_and_cannot_be_double_clicked(
    qtbot, tmp_path, monkeypatch
):
    window, service = setup(qtbot, tmp_path)
    window.connected.active = False
    service.realtime_credentials = lambda: (None, None, "private-session", "u")
    queued = []
    monkeypatch.setattr(
        window.connected, "enqueue", lambda key, op, done, **kw: queued.append((op, done)) or True
    )
    monkeypatch.setattr(
        "aedrova.desktop.preferences.application_origin", lambda: "https://staging.example"
    )
    widget = SettingsDialog(window)
    qtbot.addWidget(widget)

    _, read_complete = queued.pop()
    read_complete({"status": "no_plan"})
    assert not widget.activate_ai.isHidden()
    calls = []
    monkeypatch.setattr(
        ManagedClient,
        "activate_free",
        lambda self, workspace: calls.append(workspace) or {"status": "active"},
    )
    assert not calls
    widget.activate_included_ai()
    widget.activate_included_ai()
    assert len(queued) == 1
    operation, complete = queued.pop()
    result = operation()
    assert calls == ["w"]
    complete(result)
    assert widget.activate_ai.isHidden()


def test_members_do_not_see_owner_activation_action(qtbot, tmp_path, monkeypatch):
    window, service = setup(qtbot, tmp_path)
    window.connected.active = False
    window.account_dialog.snapshot["members"][0]["role"] = "member"
    queued = []
    monkeypatch.setattr(
        window.connected, "enqueue", lambda key, op, done, **kw: queued.append(done) or True
    )
    monkeypatch.setattr(
        "aedrova.desktop.preferences.application_origin", lambda: "https://staging.example"
    )
    widget = SettingsDialog(window)
    qtbot.addWidget(widget)
    queued.pop()({"status": "no_plan"})
    assert widget.activate_ai.isHidden()


def test_activation_uses_existing_authorized_server_endpoint(monkeypatch):
    client = ManagedClient("https://staging.example", "not-printed")
    calls = []
    monkeypatch.setattr(
        client, "request", lambda path, body: calls.append((path, body)) or {"plan": "free"}
    )
    assert client.activate_free("space/path")["plan"] == "free"
    assert calls == [("/api/free/space%2Fpath", {})]
