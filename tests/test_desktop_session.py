import json
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
from PySide6.QtCore import QSettings
from supabase_auth.errors import AuthApiError

from aedrova.desktop.account import AccountDialog
from aedrova.identity.service import Connection, IdentityService
from aedrova.identity.session_vault import SessionVault
from supabase import ClientOptions, create_client

CONNECTION = Connection("https://desktop-test.example", "sb_publishable_test_only_1234")
SLOT = "0" * 32
USER = {
    "id": "00000000-0000-0000-0000-000000000001",
    "email": "desktop-test@example.com",
    "aud": "authenticated",
    "app_metadata": {},
    "user_metadata": {},
    "created_at": "2026-09-26T00:00:00Z",
}


class CredentialStore:
    def __init__(self):
        self.values = {}

    def get_password(self, service, name):
        return self.values.get((service, name))

    def set_password(self, service, name, value):
        self.values[service, name] = value

    def delete_password(self, service, name):
        del self.values[service, name]


def test_restart_rotates_refresh_token_and_does_not_store_access_token():
    store = CredentialStore()
    vault = SessionVault(CONNECTION.url, store)
    other = SessionVault("https://another-project.example", store)
    requests = []

    def respond(request):
        requests.append(json.loads(request.content)["refresh_token"])
        return httpx.Response(
            200,
            json={
                "access_token": "access-only-in-memory",
                "refresh_token": f"rotated-{len(requests)}",
                "expires_in": 3600,
                "token_type": "bearer",
                "user": USER,
            },
        )

    client = create_client(
        CONNECTION.url,
        CONNECTION.public_key,
        options=ClientOptions(
            auto_refresh_token=False,
            persist_session=False,
            httpx_client=httpx.Client(transport=httpx.MockTransport(respond)),
        ),
    )
    vault.save(SLOT, "previous-token")
    service = IdentityService(CONNECTION, client=client)
    user, saved = service.restore_session(vault, SLOT)
    assert str(user.id) == USER["id"] and saved
    assert list(store.values.values()) == ["rotated-1"]
    client.auth.refresh_session()
    assert requests == ["previous-token", "rotated-1"]
    assert vault.read(SLOT) == "rotated-2" and other.read(SLOT) is None


def test_revoked_refresh_token_is_discarded():
    vault = SessionVault(CONNECTION.url, CredentialStore())
    vault.save(SLOT, "revoked-token")
    client = Mock()
    client.auth.refresh_session.side_effect = AuthApiError("revoked", 400, "session_not_found")
    service = IdentityService(CONNECTION, client=client)
    assert service.restore_session(vault, SLOT) == (None, False)
    assert service.user is None and vault.read(SLOT) is None


def account(qtbot, tmp_path, service):
    settings = QSettings(str(tmp_path / "account.ini"), QSettings.Format.IniFormat)
    dialog = AccountDialog(settings=settings, factory=lambda _: service)
    dialog.session_vault = SessionVault(CONNECTION.url, CredentialStore())
    dialog.session_connection = CONNECTION
    dialog.set_session_slot(SLOT)
    qtbot.addWidget(dialog)
    dialog.show()
    return dialog


def test_restored_session_reopens_only_an_authorized_remembered_workspace(qtbot, tmp_path):
    from test_connected import snapshot

    service = Mock(connection=CONNECTION, user=SimpleNamespace(id="u", email="u@example.com"))
    service.restore_session.return_value = service.user, True
    service.snapshot.return_value = snapshot()
    dialog = account(qtbot, tmp_path, service)
    opened = []
    dialog.dashboard_requested.connect(lambda: opened.append(dialog.workspace_id()))
    dialog.settings.setValue("lastWorkspace/desktop-test.example/u", "w")
    dialog.restore_session()
    qtbot.waitUntil(lambda: opened == ["w"])

    dialog.settings.setValue("lastWorkspace/desktop-test.example/u", "formerly-authorized")
    dialog.show()
    dialog.restore_session()
    qtbot.waitUntil(lambda: not dialog.awaiting_sign_in_snapshot and not dialog.busy)
    assert opened == ["w"]
    assert dialog.settings.value("lastWorkspace/desktop-test.example/u") is None


def test_offline_restore_can_retry_and_offline_signout_forgets_session(qtbot, tmp_path):
    service = Mock(connection=CONNECTION, user=None)
    service.restore_session.side_effect = [httpx.ConnectError("offline"), (None, False)]
    service.sign_out.side_effect = httpx.ConnectError("offline")
    dialog = account(qtbot, tmp_path, service)
    dialog.restore_session()
    qtbot.waitUntil(lambda: dialog.session_restore_failed)
    assert dialog.saved_session_slot() == SLOT
    dialog.recover_workspace.click()
    qtbot.waitUntil(lambda: not dialog.busy)
    assert dialog.saved_session_slot() is None and service.restore_session.call_count == 2

    dialog.set_session_slot(SLOT)
    dialog.session_vault.save(SLOT, "refresh-token")
    dialog.service = service
    dialog.sign_out()
    assert dialog.saved_session_slot() is None
    qtbot.waitUntil(lambda: not dialog.busy)
    assert dialog.session_vault.read(SLOT) is None
    service.sign_out.assert_called_once_with()
