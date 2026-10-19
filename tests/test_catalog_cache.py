from types import SimpleNamespace

from aedrova.agents.managed import ManagedClient
from aedrova.dots import client as buds


def test_catalog_cache_is_bounded_scoped_and_never_authoritative(monkeypatch):
    calls = []
    now = [0]
    monkeypatch.setattr(buds.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(buds, "connector_origin", lambda: "https://example.com")

    def request(self, path, body=None, **kwargs):
        calls.append(path)
        return {"providers": [{"name": "GitHub"}]}

    monkeypatch.setattr(ManagedClient, "request", request)
    session = ["token-a", "user-a"]
    service = SimpleNamespace(
        user=SimpleNamespace(id="user-a"),
        realtime_credentials=lambda: (None, None, *session),
    )
    api = buds.client(service)
    api.request("/api/buds/connectors")["providers"].clear()
    assert buds.client(service).request("/api/buds/connectors")["providers"]
    assert len(calls) == 1
    for _ in range(2):
        api.request("/api/dots?workspace=private")
    assert len(calls) == 3  # Access-sensitive state always comes from the server.
    now[0] = 31
    api.request("/api/buds/connectors")
    assert len(calls) == 4
    api.request("/api/buds/connections/disconnect", {"id": "fixture"})
    api.request("/api/buds/connectors")
    assert len(calls) == 6
    session[0] = "rotated-token"
    buds.client(service).request("/api/buds/connectors")
    assert len(calls) == 7
    service.user.id, session[1] = "user-b", "user-b"
    buds.client(service).request("/api/buds/connectors")
    assert len(calls) == 8


def test_icon_buttons_have_action_tooltips(qtbot):
    from aedrova.desktop.dialogs import button
    from aedrova.desktop.icons import assign
    from aedrova.desktop.materials import SpringButton

    close = button("×", "Close dialog")
    qtbot.addWidget(close)
    assert close.toolTip() == "Close dialog"
    control = SpringButton()
    qtbot.addWidget(control)
    control.setAccessibleName("Open settings")
    assign(control, "settings")
    assert control.toolTip() == "Open settings"
    control.setToolTip("Custom help")
    assign(control, "settings")
    assert control.toolTip() == "Custom help"
