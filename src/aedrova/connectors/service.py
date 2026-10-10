"""Read-only, resource-scoped connectors. Tokens never enter shared config or prompts."""

import base64
import hashlib
import json
import re
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

CATALOG = {
    "github": (
        "GitHub",
        "Repository URL or owner/repository",
        "https://github.com/settings/tokens",
    ),
    "figma": ("Figma", "Figma file URL or file key", "https://www.figma.com/settings"),
    "notion": (
        "Notion",
        "Notion page URL or page ID",
        "https://www.notion.so/profile/integrations",
    ),
}
MAX_BYTES = 512 * 1024


class ConnectorError(ValueError):
    pass


def resource_id(kind, value):
    if kind not in CATALOG or not isinstance(value, str) or len(value) > 500:
        raise ConnectorError("Choose a supported tool and a valid resource.")
    value = value.strip()
    if "://" in value:
        url = urlparse(value)
        if url.scheme != "https" or url.username or url.password or url.port:
            raise ConnectorError("Use the tool's HTTPS resource URL.")
        parts = url.path.strip("/").split("/")
        if kind == "github" and url.hostname == "github.com" and len(parts) >= 2:
            value = "/".join(parts[:2]).removesuffix(".git")
        elif kind == "figma" and url.hostname in {"figma.com", "www.figma.com"}:
            if len(parts) < 2 or parts[0] not in {"file", "design", "board"}:
                raise ConnectorError("Use a Figma file or design link.")
            value = parts[1]
        elif kind == "notion" and url.hostname in {"notion.so", "www.notion.so", "notion.site"}:
            match = re.search(
                r"([a-fA-F0-9]{8}(?:-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}|[a-fA-F0-9]{32})$",
                parts[-1],
            )
            value = match[1] if match else ""
        else:
            raise ConnectorError("The resource URL must belong to the selected tool.")
    patterns = {
        "github": r"[A-Za-z0-9_-]{1,100}/[A-Za-z0-9_.-]{1,100}",
        "figma": r"[A-Za-z0-9]{1,100}",
        "notion": r"[a-fA-F0-9]{32}|[a-fA-F0-9]{8}(?:-[a-fA-F0-9]{4}){3}-[a-fA-F0-9]{12}",
    }
    if not re.fullmatch(patterns[kind], value) or ".." in value:
        raise ConnectorError("Enter a valid " + CATALOG[kind][1] + ".")
    return value


def validate_connections(rows):
    if not isinstance(rows, list) or not 1 <= len(rows) <= 3:
        raise ConnectorError("Connect at least one tool (up to three) for this teammate.")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"tool", "resource"}:
            raise ConnectorError("Invalid tool connection; credentials must stay in Keychain.")
        resource_id(row["tool"], row["resource"])
        if row["tool"] in seen:
            raise ConnectorError("Connect one resource per tool for each teammate.")
        seen.add(row["tool"])
    return rows


def github_login_token():
    """Reuse the user's explicit GitHub helper login; never print command output."""
    import subprocess

    from aedrova.delivery.github import gh_path, github_environment

    try:
        result = subprocess.run(
            [gh_path(), "auth", "token", "--hostname", "github.com"],
            env=github_environment(),
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (ValueError, OSError, subprocess.TimeoutExpired):
        pass
    raise ConnectorError(
        "Sign in through Aedrova’s GitHub setup, or paste a read-only GitHub token."
    )


class Vault:
    def __init__(self):
        from keyring.backends.macOS import Keyring

        if sys.platform != "darwin":
            raise ConnectorError("Secure connector storage currently requires macOS.")
        self.backend = Keyring()  # Explicit OS backend; never fall back to a plaintext keyring.

    @staticmethod
    def account(user, workspace, teammate, row):
        return hashlib.sha256(
            json.dumps([user, workspace, teammate, row], sort_keys=True).encode()
        ).hexdigest()

    def get(self, user, workspace, teammate, row):
        try:
            return self.backend.get_password(
                "com.aedrova.connectors", self.account(user, workspace, teammate, row)
            )
        except Exception:
            raise ConnectorError("Unlock macOS Keychain and retry the connection.") from None

    def put(self, user, workspace, teammate, row, token):
        try:
            self.backend.set_password(
                "com.aedrova.connectors", self.account(user, workspace, teammate, row), token
            )
        except Exception:
            raise ConnectorError(
                "Could not save securely in macOS Keychain. Nothing connected."
            ) from None

    def delete(self, user, workspace, teammate, row):
        if self.get(user, workspace, teammate, row) is not None:
            self.backend.delete_password(
                "com.aedrova.connectors", self.account(user, workspace, teammate, row)
            )


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ConnectorError("The provider redirected this request. Reconnect the resource.")


def get_json(url, headers):
    request = Request(url, headers={"User-Agent": "Aedrova/0.1", **headers}, method="GET")
    try:
        with build_opener(NoRedirect()).open(request, timeout=8) as response:
            payload = response.read(MAX_BYTES + 1)
            if len(payload) > MAX_BYTES:
                raise ConnectorError("Resource is too large. Connect a smaller resource.")
            return json.loads(payload)
    except HTTPError as error:
        message = {
            401: "Token expired or invalid. Reconnect this tool.",
            403: "Permission denied or provider quota exceeded. Check token scope.",
            404: "Resource unavailable. Check its link and granted access.",
            429: "Provider rate limit reached. Retry later.",
        }.get(error.code, "Provider unavailable. Retry later.")
        raise ConnectorError(message) from None
    except (URLError, TimeoutError, OSError, ValueError):
        raise ConnectorError("Could not read this tool. Check the connection and retry.") from None


def read(row, token, fetch=None):
    fetch = fetch or get_json
    kind = row["tool"]
    resource = resource_id(kind, row["resource"])
    if not isinstance(token, str) or not 1 <= len(token) <= 4096 or any(c.isspace() for c in token):
        raise ConnectorError("Enter a valid provider token.")
    headers = {"Authorization": "Bearer " + token}
    if kind == "github":
        headers.update(
            {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        )
        root = "https://api.github.com/repos/" + resource
        repo = fetch(root, headers)
        if not isinstance(repo, dict) or not isinstance(repo.get("full_name"), str):
            raise ConnectorError("Invalid GitHub repository response.")
        issues = fetch(root + "/issues?state=open&per_page=10", headers)
        if not isinstance(issues, list):
            raise ConnectorError("Invalid GitHub response.")
        data = {
            "name": repo.get("full_name"),
            "description": repo.get("description"),
            "default_branch": repo.get("default_branch"),
            "open_issues": [
                {k: i.get(k) for k in ("number", "title", "body", "html_url")} for i in issues[:10]
            ],
        }
        # Optional README; repo and issue access above are required to verify the grant.
        try:
            doc = fetch(root + "/readme", headers)
            if doc.get("encoding") == "base64":
                data["readme"] = base64.b64decode(doc.get("content", "")).decode("utf-8")[:16000]
        except (ConnectorError, ValueError, UnicodeDecodeError):
            data["readme"] = "README unavailable."
        coverage = "Repository metadata, first 10 open issues/PRs and up to 16k README characters."
    elif kind == "figma":
        raw = fetch(
            "https://api.figma.com/v1/files/" + resource + "?depth=2", {"X-Figma-Token": token}
        )
        if not isinstance(raw, dict) or not isinstance(raw.get("document"), dict):
            raise ConnectorError("Invalid Figma file response.")
        data = {k: raw.get(k) for k in ("name", "lastModified", "document")}
        coverage = "Selected file structure at depth 2; no rendered images or deeper layers."
    else:
        headers["Notion-Version"] = "2026-03-11"
        raw = fetch(
            "https://api.notion.com/v1/blocks/" + resource + "/children?page_size=100", headers
        )
        if not isinstance(raw, dict) or not isinstance(raw.get("results"), list):
            raise ConnectorError("Invalid Notion page response.")
        data = {"blocks": raw.get("results", []), "has_more": raw.get("has_more", False)}
        coverage = "First 100 direct page blocks; nested blocks and later pages are not included."
    record = {
        "connector_source": kind,
        "resource": resource,
        "citation": "connector:" + kind + ":" + resource,
        "coverage": coverage,
        "untrusted_evidence": data,
    }
    encoded = json.dumps(record, ensure_ascii=False)
    from aedrova.security.credentials import credential_rules

    if token in encoded or credential_rules(encoded.encode()):
        raise ConnectorError("This source contains credentials. Remove them before using it.")
    if len(encoded.encode()) > 64000:
        raise ConnectorError("Selected evidence exceeds 64 KiB. Choose a smaller resource.")
    return record


def evidence(user, workspace, teammate, *, vault=None, fetch=None, cancelled=lambda: False):
    rows = validate_connections(teammate["config"].get("connections"))
    vault = vault or Vault()
    records = []
    for row in rows:
        if cancelled():
            raise InterruptedError("Cancelled")
        token = vault.get(user, workspace, teammate["id"], row)
        if not token:
            raise ConnectorError(
                "Connect " + CATALOG[row["tool"]][0] + " for this teammate on this Mac and account."
            )
        records.append(read(row, token, fetch))
    if cancelled():
        raise InterruptedError("Cancelled")
    return "\n".join(json.dumps(r, ensure_ascii=False) for r in records)
