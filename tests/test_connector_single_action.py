"""Customer connection entry has one action and never asks for developer secrets."""

import time

import pytest
from PySide6.QtWidgets import QLineEdit, QPushButton, QSpinBox
from test_bud_connectors import gallery as _gallery

connector_gallery = _gallery


@pytest.mark.parametrize("provider_id", ["github", "figma", "notion", "stripe", "tiktok"])
def test_disconnected_detail_has_one_connection_action_and_no_inputs(
    connector_gallery, provider_id
):
    dialog, _, _, providers = connector_gallery
    provider = next(p for p in providers if p["id"] == provider_id)
    provider.update(oauth_available=True, oauth_supported=True, permissions="Read-only access")
    dialog.open_provider(provider)
    assert dialog.oauth.text() == "Connect your account" and dialog.oauth.isEnabled()
    detail = dialog.pages.widget(1)
    assert not [w for w in detail.findChildren(QLineEdit) if w.isVisible()]
    assert not [w for w in dialog.findChildren(QSpinBox) if w.isVisible()]
    actions = [w.text() for w in detail.findChildren(QPushButton) if w.isVisible()]
    assert actions == ["‹  All connectors", "Connect your account"]
    assert not dialog.legacy_setup.isVisible()
    assert "24 hours" in dialog.access_note.text()


def test_unconfigured_provider_is_honest_without_manual_setup_fallback(connector_gallery):
    dialog, _, _, providers = connector_gallery
    dialog.open_provider(providers[0])
    assert dialog.oauth.isVisible() and not dialog.oauth.isEnabled()
    assert dialog.oauth.text() == "Connect your account"
    assert "not configured" in dialog.detail_copy.text()
    assert "token" not in dialog.oauth_hint.text()


def test_confirm_requires_verified_matching_provider_not_just_callback(connector_gallery):
    dialog, _, _, providers = connector_gallery
    dialog.open_provider(providers[0])
    dialog.rows[0]["status"] = "Connected"
    dialog.show_confirmation(providers[0], "bud-1")
    assert dialog.pages.currentIndex() == 1
    assert "verified access is not available" in dialog.status.text()
    dialog.rows[0]["connections"] = [
        dict(provider="notion", resource="page", status="Connected", id="other")
    ]
    dialog.show_confirmation(providers[0], "bud-1")
    assert dialog.pages.currentIndex() == 1


def test_connected_detail_uses_separate_management_view(connector_gallery):
    dialog, _, _, providers = connector_gallery
    dialog.rows[0]["connections"] = [
        dict(provider="github", resource="team/app", status="Connected", id="grant")
    ]
    providers[0]["available"] = False
    dialog.filter.setCurrentIndex(dialog.filter.findData("all"))
    dialog.rebuild_gallery()
    assert next(c for c in dialog.cards if c.accessibleName() == "Manage GitHub").isEnabled()
    dialog.open_provider(providers[0])
    assert dialog.oauth.text() == "Manage access" and dialog.oauth.isEnabled()
    assert not dialog.existing.isVisible()
    dialog.oauth.click()
    assert dialog.pages.currentIndex() == 4 and dialog.existing.isVisible()
    assert any(
        w.text() == "Disconnect" and w.isVisible()
        for w in dialog.existing.findChildren(QPushButton)
    )


def test_late_start_response_cannot_open_browser_for_another_provider(
    connector_gallery, monkeypatch
):
    dialog, _, _, providers = connector_gallery
    provider = {**providers[0], "oauth_available": True}
    dialog.open_provider(provider)
    calls = []
    monkeypatch.setattr(dialog, "run", lambda work, done, **kw: calls.append(done))
    monkeypatch.setattr(
        "aedrova.desktop.bud_connectors.connector_origin", lambda: "https://service.test"
    )
    monkeypatch.setattr(
        "aedrova.desktop.bud_connectors.QDesktopServices.openUrl",
        lambda *_: pytest.fail("Stale grant must not open"),
    )
    dialog.connect_oauth()
    dialog.open_provider(providers[1])
    state = "a" * 43
    calls[0]({"state": state, "url": "https://service.test/buds/authorize/" + state})
    assert not dialog.oauth_state


def test_empty_discovery_exposes_only_reconnect_then_restarts_fresh(connector_gallery, monkeypatch):
    dialog, _, _, providers = connector_gallery
    dialog.open_provider({**providers[0], "oauth_available": True})
    dialog.oauth_state = "a" * 43
    dialog.oauth_deadline = time.monotonic() + 600

    class API:
        def request(self, *args):
            return {"status": "choose_resource", "resources": []}

    monkeypatch.setattr("aedrova.desktop.bud_connectors.client", lambda _: API())
    dialog.poll_oauth()
    assert not dialog.selection_submit.isVisible() and not dialog.resource_picker.isVisible()
    assert dialog.selection_retry.isVisible()
    fresh = []
    monkeypatch.setattr(dialog, "connect_oauth", lambda: fresh.append(dialog.oauth_state))
    dialog.selection_retry.click()
    assert fresh == [""]


def test_waiting_action_polls_instead_of_creating_a_duplicate_grant(connector_gallery, monkeypatch):
    dialog, _, _, providers = connector_gallery
    dialog.open_provider({**providers[0], "oauth_available": True})
    dialog.oauth_state = "a" * 43
    dialog.auth_details(dialog.selected_provider)
    polled = []
    monkeypatch.setattr(dialog, "poll_oauth", lambda: polled.append(True))
    dialog.oauth.click()
    assert dialog.oauth.text() == "Check connection" and polled == [True]
