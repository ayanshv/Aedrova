"""Strict, short-lived room access received from the trusted Aedrova backend."""

import base64
import json
import time
from dataclasses import dataclass, field
from urllib.parse import urlparse
from uuid import UUID

import httpx

from aedrova.agents.managed import ManagedClient


@dataclass(frozen=True)
class MeetingAccess:
    meeting_id: str
    workspace_id: str
    channel_id: str
    user_id: str
    url: str
    token: str = field(repr=False)
    expires_at: int

    @classmethod
    def parse(cls, result, *, workspace, channel, user, now=None):
        now = time.time() if now is None else now
        try:
            meeting = str(UUID(result["meeting_id"]))
            if (result["workspace_id"], result["channel_id"], result["user_id"]) != (
                workspace,
                channel,
                user,
            ):
                raise ValueError("scope")
            parsed = urlparse(result["url"])
            if (
                parsed.scheme != "wss"
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.query
                or parsed.fragment
                or parsed.path not in {"", "/"}
            ):
                raise ValueError("url")
            token = result["token"]
            if not isinstance(token, str) or len(token) > 8192 or len(token.split(".")) != 3:
                raise ValueError("token")
            payload = token.split(".")[1]
            claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
            # Server is the trust boundary; these checks prevent confused-room client mistakes.
            grant = claims["video"]
            room = f"aedrova-{workspace}-{channel}-{meeting}"
            expiry = result["expires_at"]
            if (
                claims["sub"] != user
                or grant.get("room") != room
                or grant.get("roomJoin") is not True
                or grant.get("roomAdmin")
                or grant.get("canPublishData") is not False
                or type(expiry) is not int
                or not now < expiry <= now + 330
                or claims["exp"] != expiry
            ):
                raise ValueError("grant")
        except (KeyError, TypeError, ValueError, UnicodeDecodeError) as error:
            raise RuntimeError(
                "Aedrova returned invalid meeting access. No device was started."
            ) from error
        return cls(meeting, workspace, channel, user, result["url"], token, expiry)


class MeetingRequestError(RuntimeError):
    """Only curated, credential-free messages are safe to show in the call UI."""


class MeetingClient(ManagedClient):
    def request(self, path, body=None, *, timeout=20):
        try:
            with httpx.Client(timeout=timeout, follow_redirects=False, trust_env=False) as client:
                response = client.request(
                    "GET" if body is None else "POST",
                    self.origin + path,
                    headers={"Authorization": "Bearer " + self._access_token},
                    json=body,
                )
            if response.status_code in {401, 403}:
                raise MeetingRequestError(
                    "Cannot access this call. Sign in again or ask your workspace owner."
                )
            if response.status_code in {404, 405}:
                raise MeetingRequestError(
                    "Meeting service is not configured. Contact your workspace owner."
                )
            if response.status_code != 200:
                raise MeetingRequestError(
                    "Meeting service is temporarily unavailable. Wait a moment and try again."
                )
            return response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise MeetingRequestError(
                "Cannot reach the meeting service. Check your connection and try again."
            ) from error

    def start(self, channel):
        channel = str(UUID(channel))
        existing = self.request("/api/meetings/channel/" + channel)
        if existing:
            return str(UUID(existing[0]["id"]))
        return str(UUID(self.request("/api/meetings/start/" + channel, {})["meeting"]))

    def capabilities(self):
        try:
            result = self.request("/api/meetings/capabilities")
        except RuntimeError:
            # Older/offline servers cannot opt a call into new text permissions.
            return {"meeting_text": False, "audio_transcription": False}
        return result if isinstance(result, dict) else {"meeting_text": False}

    def consent(self, meeting, transcription, ai_context):
        return self.request(
            "/api/meetings/consent",
            {
                "meeting": meeting,
                "transcription": transcription,
                "ai_context": ai_context,
            },
        )

    def append_text(self, meeting, *, identifier, permit, body, offset_ms=0):
        if permit is None or permit.meeting_id != meeting:
            raise PermissionError("Current unanimous consent is required.")
        return self.request(
            "/api/meetings/text",
            {
                "meeting": meeting,
                "identifier": identifier,
                "revision": permit.revision,
                "roster": sorted(permit.participants),
                "body": body,
                "offset_ms": offset_ms,
            },
        )

    def transcribe(self, meeting, chunk):
        if chunk.permit is None or chunk.permit.meeting_id != meeting:
            raise PermissionError("Current microphone consent is required.")
        return self.request(
            "/api/meetings/speech",
            {
                "meeting": meeting,
                "identifier": chunk.identifier,
                "revision": chunk.permit.revision,
                "roster": sorted(chunk.permit.participants),
                "audio": base64.b64encode(chunk.audio).decode("ascii"),
                "offset_ms": chunk.offset_ms,
            },
            timeout=40,
        )

    def transcript(self, meeting, page=0):
        return self.request("/api/meetings/transcript/" + str(UUID(meeting)) + "?page=" + str(page))

    def history(self, channel):
        return self.request("/api/meetings/history/" + str(UUID(channel)))

    def review(self, identifier, version, body, decision=False):
        return self.request(
            "/api/meetings/transcript/review",
            {
                "identifier": identifier,
                "version": version,
                "body": body,
                "decision": decision,
            },
        )

    def withdraw_text(self, meeting, delete=False):
        return self.request("/api/meetings/text/withdraw", {"meeting": meeting, "delete": delete})

    def pulse(self, meeting):
        return self.request("/api/meetings/pulse", {"meeting": meeting})

    def leave(self, meeting):
        return self.request("/api/meetings/leave", {"meeting": meeting})

    def end(self, meeting):
        return self.request("/api/meetings/end", {"meeting": meeting})

    def join(self, meeting, *, workspace, channel, user):
        result = self.request("/api/meetings/join", {"meeting": meeting})
        return MeetingAccess.parse(result, workspace=workspace, channel=channel, user=user)


def transport_failure(error):
    """Classify HTTP authentication failures without echoing credential-bearing errors."""
    seen = set()
    while error is not None and id(error) not in seen:
        seen.add(id(error))
        if getattr(error, "status", None) in {401, 403}:
            return (
                "LiveKit rejected the project credentials (401/403). Check that the "
                "URL, API key and paired API secret all belong to the same project. "
                "No physical device capture or transcription was started."
            )
        error = error.__context__
    return (
        "Meeting transport check did not pass. Check the local LiveKit configuration "
        "and network. No physical device capture or transcription was started."
    )
