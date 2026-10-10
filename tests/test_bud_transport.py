import pytest

from aedrova.agents.managed import ManagedClient
from aedrova.dots.client import BudClient


def test_sleeping_host_timeout_is_specific_to_bud_transport(monkeypatch):
    observed = []

    def request(self, path, body=None, *, timeout=20):
        observed.append(timeout)
        return {"providers": []}

    monkeypatch.setattr(ManagedClient, "request", request)
    bud = BudClient("https://connections.example", "private-session")
    assert bud.request("/api/buds/connectors") == {"providers": []}
    bud.request("/api/buds/connectors", timeout=5)
    ManagedClient("https://ai.example", "private-session").request("/api/balance/test")
    assert observed == [90, 5, 20]


@pytest.mark.parametrize("message", [
    "Could not reach Aedrova’s included AI service. No local provider fallback was started.",
    "This Bud needs authorization.",
])
def test_bud_network_message_preserves_authorization_errors(monkeypatch, message):
    def request(*args, **kwargs):
        raise RuntimeError(message)

    monkeypatch.setattr(ManagedClient, "request", request)
    with pytest.raises(RuntimeError) as error:
        BudClient("https://connections.example", "private-session").request("/api/dots")
    if message.startswith("Could not reach"):
        assert "Bud connector service" in str(error.value)
        assert "included AI" not in str(error.value)
    else:
        assert str(error.value) == message
