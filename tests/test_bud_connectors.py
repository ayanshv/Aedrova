"""Gallery hierarchy, actual connection handoff and credential-safe UI states."""

from copy import deepcopy
from types import SimpleNamespace

import pytest
from test_connected import setup

from aedrova.desktop.bud_connectors import ConnectorsDialog
from aedrova.desktop.theme import DARK, LIGHT, palette, stylesheet


@pytest.fixture
def gallery(qtbot, tmp_path, monkeypatch):
    window, service = setup(qtbot, tmp_path)
    providers = [
        dict(
            id=key,
            name=name,
            group=group,
            description=description,
            resource_hint=hint,
            available=True,
        )
        for key, name, group, description, hint in [
            ("github", "GitHub", "Code & delivery", "Repository changes", "owner/repository"),
            ("figma", "Figma", "Design & knowledge", "Design file context", "file key"),
            ("notion", "Notion", "Design & knowledge", "Shared page content", "page UUID"),
            ("stripe", "Stripe", "Finance", "Account balance", "acct_ account ID"),
            ("tiktok", "TikTok", "Marketing", "Recent public videos", "open_id"),
            ("search", "Web search", "Research", "Search results", "research topic"),
        ]
    ]
    rows = [
        dict(
            id="bud-1",
            workspace_id=window.workspace_id,
            version=1,
            status="Needs authorization",
            last_sync=0,
            shape="orb",
            color="#7AAEF5",
            name="Orbit",
            provider="github",
            resource="team/project",
            role="Designer",
            connections=[],
        )
    ]
    sent = []

    class API:
        def request(self, path, body=None, **kwargs):
            if path == "/api/buds/connectors":
                return {"providers": deepcopy(providers)}
            if path.startswith("/api/dots?"):
                return {"items": deepcopy(rows)}
            sent.append((path, deepcopy(body)))
            if path.endswith("disconnect"):
                rows[0]["connections"] = []
                return {"disconnected": True, "provider_revoked": False}
            rows[0]["connections"].append(
                dict(
                    id="connection-1",
                    provider=body["provider"],
                    resource=body["resource"],
                    status="Connected",
                    version="connection-1",
                )
            )
            return {"connected": True, "id": "connection-1"}

    monkeypatch.setattr("aedrova.desktop.bud_connectors.client", lambda service: API())
    monkeypatch.setattr(
        ConnectorsDialog,
        "run",
        lambda self, operation, completed, **kwargs: completed(operation(service)),
    )
    dialog = ConnectorsDialog(window, "bud-1")
    qtbot.addWidget(dialog)
    dialog.show()
    return dialog, sent, rows, providers


def test_gallery_hierarchy_filters_and_native_themes(gallery, qtbot):
    dialog, _, _, _ = gallery
    assert dialog.filter.currentData() == "designer"
    assert len(dialog.cards) == 2
    dialog.filter.setCurrentIndex(dialog.filter.findData("all"))
    assert len(dialog.cards) == 6
    dialog.filter.setCurrentIndex(dialog.filter.findData("designer"))
    assert {card.accessibleName() for card in dialog.cards} == {"Connect Figma", "Connect Notion"}
    dialog.search.setText("figma")
    assert len(dialog.cards) == 1
    for theme in [LIGHT, DARK]:
        dialog.setStyleSheet(stylesheet(theme))
        dialog.setPalette(palette(theme))
        dialog.resize(760, 680)
        qtbot.wait(30)
        assert dialog.columns == 2
        assert not dialog.grab().isNull()
        assert dialog.gallery.horizontalScrollBar().maximum() == 0


def test_verify_flow_clears_password_and_reloads_real_connection(gallery):
    dialog, sent, rows, providers = gallery
    dialog.open_provider(next(p for p in providers if p["id"] == "figma"))
    dialog.connect_tool()
    assert not sent and "Add the resource" in dialog.status.text()
    dialog.resource.setText("designFile")
    dialog.credential.setText("private-token-fixture")
    dialog.connect_tool()
    assert sent[-1][0] == "/api/buds/connections"
    assert sent[-1][1]["dot"] == "bud-1"
    assert sent[-1][1]["credential"] == "private-token-fixture"
    assert dialog.credential.text() == ""
    assert "Connected" in dialog.status.text()
    assert dialog.pages.currentIndex() == 2
    assert dialog.success_heading.text() == "Figma is connected."
    assert "Orbit" in dialog.success_copy.text()
    assert len(rows[0]["connections"]) == 1
    dialog.disconnect_tool(rows[0]["connections"][0])
    assert "Revoke the token" in dialog.status.text()
    assert rows[0]["connections"] == []


def test_ai_rechecks_individual_connection_after_model_work():
    import json

    from aedrova.dots.client import recheck

    source = {"dot": "bud", "dot_version": 1, "connection_id": "c1", "connection_version": "c1"}
    context = SimpleNamespace(workspace_id="w", text=json.dumps({"dot_evidence": source}))
    api = SimpleNamespace(
        request=lambda path: {
            "items": [dict(id="bud", status="Connected", version=1, connections=[])]
        }
    )
    with pytest.raises(PermissionError, match="Connector access changed"):
        recheck(api, context)
    api.request = lambda path: {
        "items": [
            dict(
                id="bud",
                status="Connected",
                version=1,
                connections=[dict(id="c1", status="Connected", version="c1")],
            )
        ]
    }
    recheck(api, context)


@pytest.mark.parametrize(
    "role", ["builder", "designer", "marketing", "finance", "research", "product"]
)
def test_selected_bud_defaults_to_role_tools(gallery, role):
    from aedrova.dots.roles import recommendation_set

    dialog, _, rows, _ = gallery
    rows[0]["role"] = role
    dialog.refresh()
    assert dialog.filter.currentData() == role
    assert all(card.property("providerAvailable") for card in dialog.cards)
    expected = {p["name"] for p in dialog.providers if p["id"] in recommendation_set(role)}
    assert {card.accessibleName().removeprefix("Connect ") for card in dialog.cards} == expected
    dialog.filter.setCurrentIndex(dialog.filter.findData("all"))
    dialog.refresh()
    assert dialog.filter.currentData() == "all"


def test_confirmation_stays_inline_and_readable_in_both_themes(gallery, qtbot, tmp_path):
    dialog, _, _, providers = gallery
    for theme in (LIGHT, DARK):
        dialog.setStyleSheet(stylesheet(theme))
        dialog.setPalette(palette(theme))
        dialog.resize(1000, 760)
        dialog.show_confirmation(providers[1], "bud-1")
        qtbot.wait(20)
        assert not dialog.success_bud.isWindow()
        assert dialog.success_bud.isVisible()
        assert dialog.success_heading.geometry().bottom() < dialog.pages.height()
        assert dialog.success_copy.geometry().bottom() < dialog.pages.height()
        assert dialog.grab().save(str(tmp_path / ("confirmation-" + theme.name + ".png")))


def test_resource_lookup_help_covers_every_supported_connector(gallery):
    from aedrova.desktop.bud_connectors import HELP, RESOURCE_HELP

    assert RESOURCE_HELP.keys() == HELP.keys()
    dialog, _, _, providers = gallery
    for provider in providers:
        dialog.open_provider(provider)
        assert dialog.resource_help.text()
        assert (
            "Paste" in dialog.resource_help.text()
            if provider["id"] in {"github", "figma", "notion"}
            else dialog.resource_help.text() == RESOURCE_HELP[provider["id"]]
        )
    supabase = {
        **providers[0],
        "id": "supabase",
        "name": "Supabase",
        "oauth_supported": True,
        "oauth_available": False,
        "oauth_setup_hint": "Supabase requires an HTTPS callback.",
    }
    dialog.open_provider(supabase)
    assert "Paste your Supabase dashboard project link" in dialog.resource_help.text()
    assert "HTTPS" in dialog.oauth_hint.text()
    assert not dialog.oauth.isEnabled()


@pytest.mark.parametrize(
    "provider,url,expected",
    [
        ("github", "https://github.com/team/project/tree/main", "team/project"),
        ("figma", "https://www.figma.com/design/abc123/My-file", "abc123"),
        ("supabase", "https://supabase.com/dashboard/project/abcdefgh/settings", "abcdefgh"),
        (
            "notion",
            "https://www.notion.so/My-page-0123456789abcdef0123456789abcdef?source=copy",
            "0123456789abcdef0123456789abcdef",
        ),
    ],
)
def test_resource_links_preserve_exact_scope(provider, url, expected):
    from aedrova.desktop.bud_connectors import normalize_resource

    assert normalize_resource(provider, url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "https://github.com.evil.test/team/project",
        "http://github.com/team/project",
        "https://token@github.com/team/project",
    ],
)
def test_resource_links_reject_foreign_hosts_and_credentials(url):
    from aedrova.desktop.bud_connectors import normalize_resource

    with pytest.raises(ValueError):
        normalize_resource("github", url)


@pytest.mark.parametrize("provider_id", ["github", "notion", "figma", "tiktok"])
def test_account_sign_in_requires_no_id_or_token(gallery, monkeypatch, provider_id):
    dialog, _, _, providers = gallery
    provider = next(p for p in providers if p["id"] == provider_id)
    provider.update(oauth_available=True, oauth_supported=True, permissions="Read-only")
    dialog.open_provider(provider)
    assert not dialog.resource.isVisible() and not dialog.credential.isVisible()
    calls = []
    state, origin = "a" * 43, "https://connections.test"
    monkeypatch.setattr("aedrova.desktop.bud_connectors.connector_origin", lambda: origin)
    monkeypatch.setattr("aedrova.desktop.bud_connectors.QDesktopServices.openUrl", lambda url: True)

    class API:
        def request(self, path, body=None):
            calls.append((path, body))
            return {"state": state, "url": origin + "/buds/authorize/" + state}

    monkeypatch.setattr("aedrova.desktop.bud_connectors.client", lambda _: API())
    dialog.connect_oauth()
    assert calls[0][1]["resource"] == ("me" if provider_id == "tiktok" else "")
    assert "credential" not in calls[0][1]


def test_authorized_account_picker_connects_only_selected_resource(gallery, monkeypatch):
    dialog, _, _, providers = gallery
    provider = {
        **providers[0],
        "oauth_available": True,
        "oauth_supported": True,
        "permissions": "Read-only",
    }
    dialog.open_provider(provider)
    dialog.oauth_state = "a" * 43
    import time

    dialog.oauth_deadline = time.monotonic() + 600
    calls = []

    class API:
        def request(self, path, body=None):
            calls.append((path, body))
            if path.startswith("/api/buds/oauth/status"):
                return {
                    "status": "choose_resource",
                    "resources": [{"id": "team/app", "name": "Team app"}],
                    "requires_link": False,
                }
            return {"id": "verified"}

    monkeypatch.setattr("aedrova.desktop.bud_connectors.client", lambda _: API())
    dialog.poll_oauth()
    assert dialog.pages.currentIndex() == 3
    assert dialog.resource_picker.itemText(1) == "Team app"
    dialog.select_oauth_resource()
    assert len(calls) == 1
    dialog.resource_picker.setCurrentIndex(1)
    confirmed = []
    monkeypatch.setattr(dialog, "refresh", lambda *, on_loaded: confirmed.append(True))
    dialog.select_oauth_resource()
    assert calls[-1][1] == {"state": "a" * 43, "resource": "team/app"}
    assert not dialog.oauth_state and confirmed


def test_managed_search_uses_topic_only_without_tokens_or_browser(gallery, monkeypatch):
    dialog, _, rows, providers = gallery
    provider = next(p for p in providers if p["id"] == "search")
    provider.update(managed_available=True, oauth_supported=False, oauth_available=False)
    dialog.open_provider(provider)
    assert dialog.oauth.isVisible() and dialog.oauth.isEnabled()
    assert dialog.oauth.text() == "Enable web search"
    assert not dialog.credential.isVisible()
    monkeypatch.setattr(
        "aedrova.desktop.bud_connectors.QDesktopServices.openUrl",
        lambda *_: pytest.fail("Managed search must not open external login"),
    )
    dialog.connect_oauth()
    assert dialog.pages.currentIndex() == 3
    assert not dialog.resource_picker.isVisible()
    assert dialog.selection_link.isVisible()
    sent = []

    class API:
        def request(self, path, body):
            sent.append((path, body))
            return {"connected": True}

    monkeypatch.setattr("aedrova.desktop.bud_connectors.client", lambda *_: API())
    monkeypatch.setattr(dialog, "refresh", lambda **kwargs: None)
    dialog.selection_link.setText("launch research")
    dialog.select_oauth_resource()
    assert sent[0][0] == "/api/buds/connections/search"
    assert set(sent[0][1]) == {"workspace", "dot", "topic", "hours"}
    assert sent[0][1]["topic"] == "launch research"
