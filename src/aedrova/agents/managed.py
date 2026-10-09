"""Short-lived build credentials. Shared model-provider keys never reach this module."""

import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

import httpx


def validate_origin(value):
    parsed = urlparse(value)
    local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if (parsed.scheme != "https" and not (local and parsed.scheme == "http")) or (
        not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise ValueError("Managed access requires a secure Aedrova server address.")
    return value.rstrip("/")


def application_origin():
    path = Path(__file__).parents[1] / "desktop/assets/public-config.json"
    bundled = json.loads(path.read_text()).get("managed_origin", "") if path.exists() else ""
    value = (
        bundled if getattr(sys, "frozen", False) else os.getenv("AEDROVA_MANAGED_ORIGIN", bundled)
    )
    return validate_origin(value) if value else ""


def connector_origin():
    """Independent Bud endpoint; AI and meeting traffic retain their existing origin."""
    path = Path(__file__).parents[1] / "desktop/assets/public-config.json"
    config = json.loads(path.read_text()) if path.exists() else {}
    value = config.get("connector_origin", "")
    if not getattr(sys, "frozen", False):
        value = os.getenv("AEDROVA_CONNECTOR_ORIGIN", value)
    return validate_origin(value) if value else application_origin()


def ai_access_mode():
    """Build authentication is an explicit product mode, independent of meetings.

    Missing modes in older server-connected builds stay included (fail closed).
    Frozen apps ignore environment overrides so gateway failures never fall back.
    """
    path = Path(__file__).parents[1] / "desktop/assets/public-config.json"
    config = json.loads(path.read_text()) if path.exists() else {}
    mode = config.get("ai_access_mode", "included" if application_origin() else "local")
    if not getattr(sys, "frozen", False):
        mode = os.getenv("AEDROVA_AI_ACCESS_MODE", mode)
    if mode not in {"included", "local"}:
        raise ValueError("Invalid AI access mode. Rebuild with local or included access.")
    return mode


def application_ai_origin():
    if ai_access_mode() == "local":
        return ""
    origin = application_origin()
    if not origin:
        raise ValueError("Included AI needs the configured Aedrova service. Contact the owner.")
    return origin


@dataclass(frozen=True)
class BuildAccess:
    id: str
    provider: str
    model: str
    base_url: str
    token: str = field(repr=False)
    limits: dict = field(default_factory=dict)


class ManagedClient:
    def __init__(self, origin, access_token):
        self.origin = validate_origin(origin)
        self._access_token = access_token
        self._run_id = ""

    def request(self, path, body=None, *, timeout=20):
        try:
            with httpx.Client(timeout=timeout, follow_redirects=False, trust_env=False) as client:
                response = client.request(
                    "GET" if body is None else "POST",
                    self.origin + path,
                    headers={"Authorization": "Bearer " + self._access_token},
                    json=body,
                )
            data = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise RuntimeError(
                "Could not reach Aedrova’s included AI service. No local provider "
                "fallback was started. Check your connection and retry."
            ) from exc
        if response.status_code != 200:
            message = data.get("error") if isinstance(data, dict) else None
            if isinstance(message, str) and self._access_token not in message:
                raise RuntimeError(message[:350])
            raise RuntimeError("Aedrova could not authorize this workspace’s included AI.")
        return data

    def balance(self, workspace):
        from urllib.parse import quote

        return self.request("/api/balance/" + quote(workspace, safe=""))

    def begin(self, workspace, provider, request_id):
        result = self.request(
            "/api/runs", {"workspace": workspace, "provider": provider, "request_id": request_id}
        )
        suffix = "/gateway/" + provider + ("/v1" if provider == "codex" else "")
        if (
            not isinstance(result, dict)
            or result.get("base_url") != self.origin + suffix
            or not re.fullmatch(r"[A-Za-z0-9._:-]{1,100}", str(result.get("model", "")))
            or not re.fullmatch(r"[A-Za-z0-9_-]{20,100}", str(result.get("id", "")))
            or not re.fullmatch(r"[A-Za-z0-9_-]{32,150}", str(result.get("token", "")))
        ):
            raise RuntimeError(
                "Included AI returned invalid build access. No provider was started."
            )
        limits = result.get("limits", {})
        if not isinstance(limits, dict) or any(
            type(v) is not int or not 0 < v <= 1_000_000_000 for v in limits.values()
        ):
            raise RuntimeError("Included AI returned invalid execution limits.")
        self._run_id = result["id"]
        return BuildAccess(
            result["id"], provider, result["model"], result["base_url"], result["token"], limits
        )

    def close(self):
        try:
            if self._run_id:
                self.request("/api/runs/" + self._run_id + "/close", {})
        finally:
            self._run_id = ""
            self._access_token = ""
