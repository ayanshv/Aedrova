"""User-token-only access. Sessions live in memory, never QSettings or project files."""

import base64
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

import httpx
from supabase_auth.errors import AuthRetryableError

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
        if bool(url) != bool(key):
            raise ValueError("Both public connection settings are required.")
        return cls(url.rstrip("/"), key) if url and key else None

    @classmethod
    def from_bundle(cls):
        path = Path(__file__).parents[1] / "desktop" / "assets" / "public-config.json"
        if not path.exists():
            return None
        config = json.loads(path.read_text())
        return cls(config["supabase_url"], config["supabase_publishable_key"])

    @classmethod
    def for_application(cls):
        # A distributed app cannot be redirected by ambient environment or old QSettings.
        if getattr(sys, "frozen", False):
            return cls.from_bundle()
        return cls.from_environment() or cls.from_bundle()


class IdentityService:
    def __init__(self, connection, *, client=None):
        self.connection = connection
        self._transport = (
            httpx.Client(timeout=15, follow_redirects=False) if client is None else None
        )
        self.is_context_clone = False
        self.client = client or create_client(
            connection.url,
            connection.public_key,
            options=ClientOptions(
                flow_type="pkce",
                persist_session=False,
                auto_refresh_token=False,
                httpx_client=self._transport,
            ),
        )
        self.user = None

    def fork_for_context(self):
        """Called in the serialized transport worker; never expose tokens to UI/logs."""
        self._authenticated()
        session = self.client.auth.get_session()
        fork = IdentityService(self.connection)
        fork.is_context_clone = True
        try:
            result = fork.client.auth.set_session(session.access_token, session.refresh_token)
            fork.user = result.user
            if fork.user is None or str(fork.user.id) != str(self.user.id):
                raise PermissionError("Session changed. Sign in again.")
            return fork
        except Exception:
            fork.close_context()
            raise

    def close_context(self):
        if self.is_context_clone and self._transport:
            self._transport.close()
            self.client = None
            self.user = None

    def google_authorization_url(self, redirect):
        result = self.client.auth.sign_in_with_oauth(
            {
                "provider": "google",
                "options": {"redirect_to": redirect, "scopes": "openid email profile"},
            }
        )
        return result.url

    def finish_google_sign_in(self, code):
        result = self.client.auth.exchange_code_for_session({"auth_code": code})
        if result.session is None or result.user is None:
            raise PermissionError("Sign-in did not return a session")
        self.user = result.user
        return self.user

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

    def update_profile(self, name):
        self._authenticated()
        name = name.strip()
        if not 1 <= len(name) <= 80:
            raise ValueError("Display name must be 1–80 characters.")
        self.user = self.client.auth.update_user({"data": {"full_name": name}}).user

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
        except (httpx.TransportError, AuthRetryableError):
            raise
        except Exception:
            self.user = None
            raise

    def snapshot(self):
        self._authenticated()
        workspaces = self.client.table("workspaces").select("id,name").order("name").execute().data
        memberships = self.client.rpc("list_members", {}).execute().data
        channels = (
            self.client.table("channels")
            .select("id,workspace_id,name,private,kind,dm_low,dm_high")
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
            "directory": self.client.rpc("team_directory", {}).execute().data,
            "unread": self.client.rpc("unread_counts", {}).execute().data,
            "agent_preferences": self.client.table("workspace_agent_preferences")
            .select("workspace_id,nickname,provider")
            .execute()
            .data,
            "workspaces": workspaces,
            "members": memberships,
            "channels": channels,
            "invitations": invitations,
        }

    def rpc(self, name, parameters):
        allowed = {
            "start_direct_message",
            "mark_channel_read",
            "reserve_attachment",
            "finish_attachment",
            "send_message",
            "create_workspace",
            "onboard_workspace",
            "set_agent_preferences",
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

    def messages(self, channel_id):
        self._authenticated()
        rows = (
            self.client.table("messages")
            .select("id,channel_id,sender_id,body,parent_id,created_at")
            .eq("channel_id", channel_id)
            .order("created_at", desc=True)
            .order("id", desc=True)
            .limit(500)
            .execute()
            .data
        )
        return list(reversed(rows))

    def message_page(self, channel_id, *, before=None, after=None, parent=None, limit=100):
        self._authenticated()
        return (
            self.client.rpc(
                "message_page",
                {
                    "p_channel": channel_id,
                    "p_before": before,
                    "p_after": after,
                    "p_parent": parent,
                    "p_limit": limit,
                },
            )
            .execute()
            .data
        )

    def context_page(self, channel_id, *, after=0):
        """All roots AND replies, filtered by the signed-in user's existing RLS."""
        self._authenticated()
        return (
            self.client.table("messages")
            .select("id,channel_id,sender_id,body,parent_id,created_at,sequence")
            .eq("channel_id", channel_id)
            .gt("sequence", after)
            .order("sequence")
            .limit(100)
            .execute()
            .data
        )

    def context_revision(self, channel):
        self._authenticated()
        return self.client.rpc("context_revision", {"p_channel": channel}).execute().data

    def context_snapshot(self, workspace, cancelled=lambda: False):
        """Scoped inventory with keyset paging instead of dashboard row ceilings."""
        self._authenticated()
        channels, cursor = [], None
        while True:
            if cancelled():
                raise InterruptedError("Cancelled")
            query = (
                self.client.table("channels")
                .select("id,workspace_id,name,private")
                .eq("workspace_id", workspace)
                .order("id")
                .limit(100)
            )
            if cursor:
                query = query.gt("id", cursor)
            page = query.execute().data
            if not page:
                break
            if cursor and page[-1]["id"] <= cursor:
                raise ValueError("Invalid channel inventory pagination.")
            channels.extend(page)
            cursor = page[-1]["id"]
            if len(channels) > 10000:
                raise ValueError("Workspace exceeds the 10,000-channel context limit.")
        return {
            "workspaces": self.client.table("workspaces")
            .select("id,name")
            .eq("id", workspace)
            .execute()
            .data,
            "members": self.client.table("workspace_members")
            .select("workspace_id,user_id,role")
            .eq("workspace_id", workspace)
            .eq("user_id", str(self.user.id))
            .execute()
            .data,
            "channels": channels,
            "agent_preferences": self.client.table("workspace_agent_preferences")
            .select("workspace_id,nickname,provider")
            .eq("workspace_id", workspace)
            .execute()
            .data,
        }

    def context_decisions(self, channel_id):
        self._authenticated()
        rows, cursor = [], None
        while True:
            query = (
                self.client.table("context_decisions")
                .select("*")
                .eq("channel_id", channel_id)
                .order("message_id")
                .limit(100)
            )
            if cursor:
                query = query.gt("message_id", cursor)
            page = query.execute().data
            if not page:
                return rows
            rows.extend(page)
            cursor = page[-1]["message_id"]
            if len(rows) > 20000:
                raise ValueError("Decision inventory exceeds the supported limit.")

    def set_context_decision(self, message_id, body, confirmed):
        self._authenticated()
        return (
            self.client.rpc(
                "set_context_decision",
                {
                    "p_message": message_id,
                    "p_body": body,
                    "p_confirmed": confirmed,
                },
            )
            .execute()
            .data
        )

    def attachments_for(self, message_ids):
        self._authenticated()
        if not message_ids:
            return []
        return (
            self.client.table("attachments")
            .select("id,channel_id,message_id,filename,byte_size,sha256,object_path")
            .in_("message_id", message_ids)
            .execute()
            .data
        )

    def realtime_credentials(self):
        # Called only by the serialized transport worker, after a validated read.
        session = self.client.auth.get_session()
        return (
            self.connection.url,
            self.connection.public_key,
            session.access_token,
            str(self.user.id),
        )

    def upload_attachment(self, identifier, channel_id, path, parent=None):
        from aedrova.identity.transfers import read_upload

        name, data, digest = read_upload(path)
        object_path = self.rpc(
            "reserve_attachment",
            {
                "p_id": identifier,
                "p_channel": channel_id,
                "p_filename": name,
                "p_size": len(data),
                "p_sha256": digest,
            },
        )
        try:
            self.client.storage.from_("aedrova-files").upload(
                object_path, data, {"content-type": "application/octet-stream", "upsert": "false"}
            )
        except Exception:
            # An upload may have succeeded before its response was lost. The server checks
            # the reserved immutable path and actual stored size before publishing it.
            return self.rpc("finish_attachment", {"p_id": identifier, "p_parent": parent})
        return self.rpc("finish_attachment", {"p_id": identifier, "p_parent": parent})

    def download_attachment(self, identifier):
        from aedrova.identity.transfers import MAX_BYTES

        self._authenticated()
        records = (
            self.client.table("attachments")
            .select("id,object_path,byte_size,sha256,message_id")
            .eq("id", identifier)
            .execute()
            .data
        )
        if len(records) != 1 or not records[0]["message_id"]:
            raise PermissionError("Attachment unavailable")
        record = records[0]
        if not 1 <= record["byte_size"] <= MAX_BYTES:
            raise ValueError("Invalid attachment size")
        path = record["object_path"]
        if not re.fullmatch(r"[a-f0-9-]{36}/[a-f0-9-]{36}/[a-f0-9-]{36}", path):
            raise ValueError("Invalid object path")
        token = self.client.auth.get_session().access_token
        headers = {"apikey": self.connection.public_key, "Authorization": "Bearer " + token}
        content = bytearray()
        with httpx.Client(timeout=30, follow_redirects=False) as client:
            with client.stream(
                "GET",
                self.connection.url + "/storage/v1/object/authenticated/aedrova-files/" + path,
                headers=headers,
            ) as response:
                response.raise_for_status()
                for chunk in response.iter_bytes():
                    if len(content) + len(chunk) > record["byte_size"]:
                        raise ValueError("Attachment exceeded declared size")
                    content.extend(chunk)
        if (
            len(content) != record["byte_size"]
            or hashlib.sha256(content).hexdigest() != record["sha256"]
        ):
            raise ValueError("Attachment integrity check failed")
        return bytes(content)
