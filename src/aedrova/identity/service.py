"""User-token-only access. Sessions live in memory, never QSettings or project files."""

import base64
import json
import os
import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

import httpx

from supabase import ClientOptions, create_client


@dataclass(frozen=True)
class Connection:
    url: str
    public_key: str = field(repr=False)

    def __post_init__(self):
        parsed = urlparse(self.url)
        local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        if (parsed.scheme != "https" and not (local and parsed.scheme == "http")) or (
            not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path not in ("", "/")
        ):
            raise ValueError("Use the HTTPS project URL, or a localhost development URL.")
        key = self.public_key
        if re.fullmatch(r"sb_publishable_[A-Za-z0-9_-]{10,}", key):
            return
        try:
            payload = key.split(".")[1]
            claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
            if claims.get("role") == "anon":
                return
        except (ValueError, IndexError, UnicodeDecodeError, AttributeError):
            pass
        raise ValueError(
            "Use a publishable or legacy anon key. Secret/service-role keys are forbidden."
        )

    @classmethod
    def from_environment(cls):
        url, key = os.getenv("AEDROVA_SUPABASE_URL"), os.getenv("AEDROVA_SUPABASE_PUBLISHABLE_KEY")
        return cls(url.rstrip("/"), key) if url and key else None


class IdentityService:
    def __init__(self, connection, *, client=None):
        self.connection = connection
        self.client = client or create_client(
            connection.url,
            connection.public_key,
            options=ClientOptions(
                persist_session=False,
                auto_refresh_token=False,
                httpx_client=httpx.Client(timeout=15, follow_redirects=False),
            ),
        )
        self.user = None

    def sign_in(self, email, password):
        result = self.client.auth.sign_in_with_password(
            {"email": email.strip(), "password": password}
        )
        self.user = result.user
        return self.user

    def sign_up(self, email, password):
        result = self.client.auth.sign_up({"email": email.strip(), "password": password})
        self.user = result.user if result.session else None
        return self.user

    def verify_email(self, email, code):
        result = self.client.auth.verify_otp(
            {"email": email.strip(), "token": code.strip(), "type": "signup"}
        )
        self.user = result.user
        return self.user

    def sign_out(self):
        try:
            self.client.auth.sign_out({"scope": "local"})
        finally:
            # Discard the entire client even if remote revocation is unavailable.
            self.user = None
            self.client = None

    def _authenticated(self):
        if self.client is None or self.user is None:
            raise PermissionError("Sign in first.")
        # SDK get_session refreshes expired sessions; validate against Auth on each action.
        try:
            session = self.client.auth.get_session()
            if session is None:
                raise PermissionError("Session expired. Sign in again.")
            self.user = self.client.auth.get_user().user
            if self.user is None:
                raise PermissionError("Session expired. Sign in again.")
        except Exception:
            self.user = None
            raise

    def snapshot(self):
        self._authenticated()
        workspaces = self.client.table("workspaces").select("id,name").order("name").execute().data
        memberships = self.client.rpc("list_members", {}).execute().data
        channels = (
            self.client.table("channels")
            .select("id,workspace_id,name,private")
            .order("name")
            .execute()
            .data
        )
        # Every query runs with the user's JWT and is filtered by PostgreSQL RLS.
        invitations = (
            self.client.table("workspace_invitations")
            .select("id,workspace_id,email,role,expires_at,accepted_at,revoked_at")
            .execute()
            .data
        )
        return {
            "workspaces": workspaces,
            "members": memberships,
            "channels": channels,
            "invitations": invitations,
        }

    def rpc(self, name, parameters):
        allowed = {
            "create_workspace",
            "create_channel",
            "create_invitation",
            "accept_invitation",
            "revoke_invitation",
            "set_member_role",
            "remove_member",
            "set_channel_member",
        }
        if name not in allowed:
            raise ValueError("Unsupported account operation")
        self._authenticated()
        return self.client.rpc(name, parameters).execute().data
