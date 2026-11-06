"""Identity boundary tests. HTTP is mocked; SQL policy tests use real PostgreSQL separately."""

import base64
import json
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest

from aedrova.identity.service import Connection, IdentityService
from supabase import ClientOptions, create_client

KEY = "sb_publishable_abcdefghijk1234567890"
URL = "https://example.supabase.co"


def legacy(role):
    payload = base64.urlsafe_b64encode(json.dumps({"role": role}).encode()).decode().rstrip("=")
    return f"header.{payload}.signature"


@pytest.mark.parametrize("key", [KEY, legacy("anon")])
def test_accept_only_public_key_types(key):
    assert Connection(URL, key).public_key == key


@pytest.mark.parametrize(
    "key",
    [
        "sb_secret_123456789012345",
        legacy("service_role"),
        "garbage",
        "sb_publishable_abcd\nAuthorization: attack",
        "e30.W10.sig",
    ],
)
def test_reject_privileged_or_malformed_keys(key):
    with pytest.raises(ValueError):
        Connection(URL, key)


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com",
        "https://user:pw@example.com",
        "https://example.com/path",
        "https://example.com?key=x",
    ],
)
def test_require_safe_project_origin(url):
    with pytest.raises(ValueError):
        Connection(url, KEY)


def test_local_development_origin_and_no_key_repr():
    config = Connection("http://127.0.0.1:54321", KEY)
    assert KEY not in repr(config)


def test_signout_discards_session_even_when_remote_call_fails():
    client = Mock()
    client.auth.sign_out.side_effect = OSError("offline")
    service = IdentityService(Connection(URL, KEY), client=client)
    service.user = SimpleNamespace(id="user")
    with pytest.raises(OSError):
        service.sign_out()
    assert service.client is None and service.user is None


def test_expired_session_cannot_invoke_rpc():
    client = Mock()
    client.auth.get_session.return_value = None
    service = IdentityService(Connection(URL, KEY), client=client)
    service.user = SimpleNamespace(id="user")
    with pytest.raises(PermissionError):
        service.rpc("create_workspace", {"p_name": "Test"})
    client.rpc.assert_not_called()
    assert service.user is None


def test_upload_cancellation_can_invoke_authenticated_abandon_rpc():
    client = Mock()
    service = IdentityService(Connection(URL, KEY), client=client)
    service.user = SimpleNamespace(id="user")
    client.auth.get_user.return_value.user = service.user
    parameters = {"p_id": "attachment-id"}
    service.rpc("abandon_attachment", parameters)
    client.rpc.assert_called_once_with("abandon_attachment", parameters)


def test_snapshot_requests_personal_active_and_archived_workspaces(monkeypatch):
    client = Mock()
    client.table.return_value.select.return_value.order.return_value.execute.return_value.data = []
    client.table.return_value.select.return_value.execute.return_value.data = []

    def rpc(name, params):
        rows = []
        if name == "list_my_workspaces":
            rows = [{"id": "hidden" if params["p_archived"] else "active", "name": "Team"}]
        return SimpleNamespace(execute=lambda: SimpleNamespace(data=rows))

    client.rpc.side_effect = rpc
    service = IdentityService(Connection(URL, KEY), client=client)
    service.user = SimpleNamespace(id="user")
    monkeypatch.setattr(service, "_authenticated", lambda: None)
    data = service.snapshot()
    assert data["workspaces"][0]["id"] == "active"
    assert data["archived_workspaces"][0]["id"] == "hidden"
    assert not any(call.args == ("workspaces",) for call in client.table.call_args_list)


def test_confirmation_required_signup_does_not_authenticate():
    client = Mock()
    client.auth.sign_up.return_value = SimpleNamespace(
        user=SimpleNamespace(id="user"), session=None
    )
    service = IdentityService(Connection(URL, KEY), client=client)
    assert service.sign_up("a@b.test", "password") is None
    with pytest.raises(PermissionError):
        service.snapshot()


def test_official_sdk_uses_user_bearer_and_disables_persistence():
    requests = []
    user = {
        "id": "00000000-0000-0000-0000-000000000001",
        "email": "test@example.com",
        "aud": "authenticated",
        "app_metadata": {},
        "user_metadata": {},
        "created_at": "2026-09-26T00:00:00Z",
    }

    def respond(request):
        requests.append(request)
        if request.url.path.endswith("/token"):
            return httpx.Response(
                200,
                json={
                    "access_token": "renewed-access"
                    if request.url.params.get("grant_type") == "refresh_token"
                    else "user-access",
                    "refresh_token": "refresh",
                    "expires_in": 3600,
                    "token_type": "bearer",
                    "user": user,
                },
            )
        if request.url.path.endswith("/user"):
            return httpx.Response(200, json=user)
        return httpx.Response(200, json="workspace-id")

    client = create_client(
        URL,
        KEY,
        options=ClientOptions(
            auto_refresh_token=False,
            persist_session=False,
            httpx_client=httpx.Client(transport=httpx.MockTransport(respond)),
        ),
    )
    service = IdentityService(Connection(URL, KEY), client=client)
    service.sign_in("test@example.com", "not-a-real-password")
    client.auth._in_memory_session.expires_at = 1
    assert service.rpc("create_workspace", {"p_name": "Test"}) == "workspace-id"
    assert requests[-1].headers["authorization"] == "Bearer renewed-access"
    assert requests[-1].headers["apikey"] == KEY
    assert client.auth._persist_session is False


def test_frozen_app_ignores_environment_backend_override(monkeypatch):
    import sys

    expected = Connection(URL, KEY)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(Connection, "from_bundle", lambda: expected)
    monkeypatch.setattr(Connection, "from_environment", lambda: pytest.fail("Environment used"))
    assert Connection.for_application() == expected


def test_partial_development_configuration_fails_closed(monkeypatch):
    monkeypatch.setenv("AEDROVA_SUPABASE_URL", URL)
    monkeypatch.delenv("AEDROVA_SUPABASE_PUBLISHABLE_KEY", raising=False)
    with pytest.raises(ValueError):
        Connection.from_environment()


@pytest.mark.parametrize(
    "frozen,project,enabled",
    [
        (False, "https://stage-example.supabase.co", True),
        (True, "https://stage-example.supabase.co", False),
        (False, "https://cpelagtufyocepnqcqqd.supabase.co", False),
    ],
)
def test_source_staging_context_override_cannot_enable_public_build(
    monkeypatch, frozen, project, enabled
):
    import sys

    monkeypatch.setattr(sys, "frozen", frozen, raising=False)
    monkeypatch.setenv("AEDROVA_DEPLOYMENT_ENVIRONMENT", "staging")
    monkeypatch.setenv("AEDROVA_MEETING_CONTEXT_ENABLED", "true")
    service = IdentityService(Connection(project, KEY), client=Mock())
    assert service.meeting_context_enabled is enabled


def test_context_fork_validates_once_on_isolated_client(monkeypatch):
    source_client = Mock()
    source_client.auth.get_session.return_value = SimpleNamespace(
        access_token="private-token", refresh_token="private-refresh"
    )
    source = IdentityService(Connection(URL, KEY), client=source_client)
    source.user = SimpleNamespace(id="user")
    clone = Mock()
    clone.client.auth.set_session.return_value = SimpleNamespace(user=SimpleNamespace(id="user"))
    monkeypatch.setattr("aedrova.identity.service.IdentityService", lambda *a, **kw: clone)
    assert source.fork_for_context() is clone
    source_client.auth.get_user.assert_not_called()
    clone.client.auth.set_session.assert_called_once_with("private-token", "private-refresh")
    assert clone.user.id == "user"

    clone.client.auth.set_session.return_value = SimpleNamespace(user=SimpleNamespace(id="other"))
    with pytest.raises(PermissionError, match="Session changed"):
        source.fork_for_context()
    clone.close_context.assert_called_once()


def test_background_read_validates_once_without_caching_across_actions():
    client = Mock()
    client.auth.get_session.return_value = SimpleNamespace(access_token="private")
    client.auth.get_user.return_value = SimpleNamespace(user=SimpleNamespace(id="user"))
    source = IdentityService(Connection(URL, KEY), client=client)
    source.user = SimpleNamespace(id="user")
    with source.background_read(lambda: False):
        for _ in range(8):
            source._authenticated()
    assert client.auth.get_user.call_count == 1
    source._authenticated()
    assert client.auth.get_user.call_count == 2
    with source.background_read(lambda: False):
        source._authenticated()
    assert client.auth.get_user.call_count == 3


def test_background_read_yields_before_next_query_and_does_not_log_out():
    from threading import Event

    from aedrova.identity.service import ReadInterrupted

    interrupted = Event()
    client = Mock()
    client.auth.get_session.return_value = SimpleNamespace(access_token="private")
    client.auth.get_user.return_value = SimpleNamespace(user=SimpleNamespace(id="user"))
    source = IdentityService(Connection(URL, KEY), client=client)
    source.user = SimpleNamespace(id="user")
    first, later = Mock(), Mock()
    first.execute.side_effect = lambda: interrupted.set() or SimpleNamespace(data=[])
    with pytest.raises(ReadInterrupted):
        with source.background_read(interrupted.is_set):
            source._read(first)
            source._read(later)
    first.execute.assert_called_once()
    later.execute.assert_not_called()
    assert source.user.id == "user"
    interrupted.clear()
    source._authenticated()
    assert client.auth.get_user.call_count == 2


def test_background_read_fails_closed_if_identity_changes():
    client = Mock()
    client.auth.get_session.return_value = SimpleNamespace(access_token="private")
    client.auth.get_user.return_value = SimpleNamespace(user=SimpleNamespace(id="user"))
    source = IdentityService(Connection(URL, KEY), client=client)
    source.user = SimpleNamespace(id="user")
    with pytest.raises(PermissionError, match="account changed"):
        with source.background_read(lambda: False):
            source.user = SimpleNamespace(id="other")
            source._authenticated()
    assert getattr(source._read_state, "batch", None) is None
