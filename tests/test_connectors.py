"""Resource and credential boundaries, actual teammate context path and native gating."""

import base64
import json
from types import SimpleNamespace

import pytest
from test_ai_teammates import profile
from test_connected import setup

from aedrova.agents.context import WorkspaceContext
from aedrova.agents.retrieval import ContextIndex, validate_citations
from aedrova.connectors.service import (
    ConnectorError,
    NoRedirect,
    Vault,
    evidence,
    read,
    resource_id,
    validate_connections,
)
from aedrova.desktop.ai_teammates import TeammatesDialog
from aedrova.teammates.advisor import suggest_locally


def test_resource_urls_cannot_change_provider_host_or_escape_scope():
    assert resource_id("github", "https://github.com/owner/repo.git") == "owner/repo"
    assert resource_id("figma", "https://www.figma.com/design/AbC/design") == "AbC"
    page = "abcd1234" * 4
    assert resource_id("notion", "https://www.notion.so/Project-" + page) == page
    for kind, value in [
        ("github", "https://evil.test/owner/repo"),
        ("github", "owner/../../evil"),
        ("figma", "https://www.figma.com@evil.test/file/key/name"),
        ("figma", "https://www.figma.com/file/key?token=abc#fragment"),
        ("notion", "not-a-page"),
        ("unknown", "value"),
    ]:
        if "?token" in value:  # Queries are ignored and never forwarded to the API.
            assert resource_id(kind, value) == "key"
        else:
            with pytest.raises(ValueError):
                resource_id(kind, value)
    with pytest.raises(ConnectorError):
        NoRedirect().redirect_request(None, None, 302, "", {}, "https://evil.test")


def fake_fetch(url, headers):
    if "api.github.com" in url:
        assert headers["Authorization"] == "Bearer test-token"
        if "/issues?" in url:
            return [{"number": 1, "title": "Fix export", "body": "Keep UTC"}]
        if url.endswith("/readme"):
            return {"encoding": "base64", "content": base64.b64encode(b"Project docs").decode()}
        return {"full_name": "owner/repo", "description": "Our product", "default_branch": "main"}
    if "api.figma.com" in url:
        assert headers == {"X-Figma-Token": "test-token"}
        assert url.endswith("?depth=2")
        return {"name": "Design", "document": {"children": []}}
    assert "api.notion.com" in url and headers["Notion-Version"] == "2026-03-11"
    return {
        "results": [{"paragraph": {"rich_text": [{"plain_text": "Research"}]}}],
        "has_more": True,
    }


@pytest.mark.parametrize(
    "kind,resource",
    [
        ("github", "owner/repo"),
        ("figma", "AbC"),
        ("notion", "abcd1234" * 4),
    ],
)
def test_adapters_verify_and_return_bounded_citable_evidence_without_tokens(kind, resource):
    record = read({"tool": kind, "resource": resource}, "test-token", fake_fetch)
    assert record["citation"] == f"connector:{kind}:{resource}"
    assert record["coverage"] and "test-token" not in json.dumps(record)
    context = WorkspaceContext("w", "u", frozenset(), json.dumps(record), 0, "Aedrova", "codex")
    index = ContextIndex(context)
    assert len(index.sources) == 1 and index.sources[0].decision == "external_untrusted"
    index.close()
    assert validate_citations(context, "Source " + record["citation"]) == [record["citation"]]
    with pytest.raises(ValueError):
        validate_citations(context, "connector:github:other/repo")


def test_invalid_payload_credentials_and_limits_fail_closed():
    row = {"tool": "figma", "resource": "File"}
    for payload in [
        [],
        {},
        {"document": {"secret": "test-token"}},
        {"document": {"text": "x" * 65000}},
    ]:
        with pytest.raises(ConnectorError):
            read(row, "test-token", lambda *_, payload=payload: payload)
    for rows in [None, [], [{**row, "token": "secret"}], [row, row]]:
        with pytest.raises(ConnectorError):
            validate_connections(rows)
    with pytest.raises(ConnectorError):
        read(row, "token\nheader", fake_fetch)


def test_vault_keys_bind_account_workspace_actor_and_exact_resource():
    row = {"tool": "github", "resource": "owner/repo"}
    original = Vault.account("u", "w", "actor", row)
    assert all(
        Vault.account(*scope, row) != original
        for scope in [
            ("other", "w", "actor"),
            ("u", "other", "actor"),
            ("u", "w", "other"),
        ]
    )
    assert Vault.account("u", "w", "actor", {**row, "resource": "other/repo"}) != original
    assert "owner/repo" not in original


def test_assignment_requires_current_account_grant_and_cancellation():
    row = profile()
    row["config"]["connections"] = [{"tool": "github", "resource": "owner/repo"}]
    calls = []
    vault = SimpleNamespace(get=lambda *a: calls.append(a) or "test-token")
    text = evidence("u", "w", row, vault=vault, fetch=fake_fetch)
    assert "Project docs" in text and calls[0][:3] == ("u", "w", row["id"])
    with pytest.raises(ConnectorError):
        evidence("other", "w", row, vault=SimpleNamespace(get=lambda *_: None), fetch=fake_fetch)
    with pytest.raises(InterruptedError):
        evidence("u", "w", row, vault=vault, fetch=fake_fetch, cancelled=lambda: True)
    row["config"].pop("connections")
    with pytest.raises(ConnectorError):
        evidence("u", "w", row, vault=vault, fetch=fake_fetch)


def test_editor_requires_connected_tool_and_automatically_suggests_without_granting(
    qtbot, tmp_path
):
    window, service = setup(qtbot, tmp_path)
    service.ai_teammates = lambda _: {"items": [], "setup_required": False}
    dialog = TeammatesDialog(window)
    qtbot.addWidget(dialog)
    qtbot.waitUntil(lambda: not dialog.busy)
    dialog.role_input.setText("A designer who reviews our brand")
    dialog.role_changed()
    dialog.role_timer.stop()  # No paid model calls in tests.
    assert dialog.suggested_tools == ["figma"]
    assert dialog.connectors.kind.currentData() == "figma"
    assert not dialog.connectors.rows
    dialog.persist()
    assert "Connect at least one" in dialog.status.text()
    assert "token" not in dialog.config()
    dialog.reject()
    assert not dialog.role_timer.isActive()
    assert suggest_locally("Software engineer") == ["github"]
    assert suggest_locally("Marketing strategist") == ["notion"]


def test_context_job_reads_connectors_rechecks_profile_and_never_runs_on_revocation(monkeypatch):
    from threading import Event

    from aedrova.desktop.builds import ContextJob

    row = profile()
    row["workspace_id"] = "w"
    row["config"]["connections"] = [{"tool": "github", "resource": "owner/repo"}]
    snapshot = {
        "workspaces": [{"id": "w"}],
        "channels": [],
        "members": [{"workspace_id": "w", "user_id": "u", "role": "owner"}],
    }
    context = WorkspaceContext("w", "u", frozenset(), "", 0, "Aedrova", "codex")
    service = SimpleNamespace(
        user=SimpleNamespace(id="u"),
        snapshot=lambda: snapshot,
        ai_teammates=lambda _: {"items": [row]},
    )
    monkeypatch.setattr("aedrova.desktop.builds.gather", lambda *a, **k: context)
    calls = []
    monkeypatch.setattr(
        "aedrova.connectors.service.evidence",
        lambda *a, **k: calls.append(a) or '{"external":"evidence"}',
    )
    result = []
    job = ContextJob(service, "w", Event(), 1, teammate=row)
    job.signals.finished.connect(result.append)
    job.run()
    assert calls and '"external"' in result[0]["result"]["context"].text

    def revoked(*a, **k):
        snapshot["members"] = []
        return "{}"

    monkeypatch.setattr("aedrova.connectors.service.evidence", revoked)
    job.run()
    assert "error" in result[-1]["result"]


def test_disconnected_tool_stops_next_phase_before_checkout_or_provider(monkeypatch, tmp_path):
    from aedrova.agents.runtime import LocalRunner
    from aedrova.desktop.builds import BuildJob

    row = profile()
    context = WorkspaceContext("w", "u", frozenset(), "", 0, "Aedrova", "codex")
    calls, results = [], []

    def disconnected(*a, **k):
        raise ConnectorError("Connect GitHub for this teammate on this Mac and account.")

    monkeypatch.setattr("aedrova.connectors.service.evidence", disconnected)
    monkeypatch.setattr(LocalRunner, "run", lambda *a, **k: calls.append("provider"))
    monkeypatch.setattr("aedrova.desktop.builds.prepare", lambda *a: calls.append("checkout"))
    job = BuildJob(context, "owner/repo", "Implement", "codex", False)
    job.teammate = row
    job.signals.finished.connect(results.append)
    job.run()
    assert not calls and not results[0]["ok"]
    assert "Connect GitHub" in results[0]["text"]
