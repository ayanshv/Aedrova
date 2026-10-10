"""Read-only release checks. Updates are explicit downloads, never silent installs."""

import json
import platform
import re
import urllib.error
import urllib.request
from importlib.metadata import PackageNotFoundError, version
from urllib.parse import urlsplit

try:
    VERSION = version("aedrova")
except PackageNotFoundError:
    VERSION = "0.1.0"


def version_tuple(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{1,4}\.\d{1,4}\.\d{1,4}", value):
        raise ValueError("Release information has an invalid version.")
    return tuple(map(int, value.split(".")))


def validate_release(data, machine=None, macos=None):
    if not isinstance(data, dict):
        raise ValueError("Release information is invalid.")
    version_tuple(data.get("version"))
    if data.get("public_release") is not True:
        raise ValueError("The verified public installer is not ready yet.")
    if data.get("architecture") not in ("arm64", "x86_64", "universal2"):
        raise ValueError("Release information has an unsupported architecture.")
    digest = data.get("sha256")
    if not isinstance(digest, str) or not re.fullmatch(r"[a-f0-9]{64}", digest):
        raise ValueError("Release information is missing its verification digest.")
    minimum = data.get("minimum_macos")
    if not isinstance(minimum, str) or not re.fullmatch(r"\d{1,2}\.\d{1,2}", minimum):
        raise ValueError("Release information is missing macOS requirements.")
    current = machine or platform.machine()
    if data["architecture"] not in {current, "universal2"}:
        raise ValueError("This installer is for a different Mac processor. Keep your current app.")
    operating_system = platform.mac_ver()[0] if macos is None else macos
    if operating_system:
        actual = tuple(int(value) for value in operating_system.split(".")[:2])
        required = tuple(int(value) for value in data["minimum_macos"].split("."))
        if actual < required:
            raise ValueError("This release needs a newer macOS version. Keep your current app.")
    return data


def check_release(origin):
    parsed = urlsplit(origin)
    if (
        not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
    ):
        raise ValueError("Configure the verified Aedrova website before checking for updates.")
    if parsed.scheme != "https" and not (
        parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "localhost"}
    ):
        raise ValueError("Configure the verified Aedrova website before checking for updates.")

    class SameOrigin(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            if urlsplit(newurl).netloc != parsed.netloc or urlsplit(newurl).scheme != parsed.scheme:
                raise ValueError("The release service returned an unexpected address.")
            return super().redirect_request(req, fp, code, msg, headers, newurl)

    try:
        with urllib.request.build_opener(SameOrigin()).open(
            origin.rstrip("/") + "/api/release", timeout=10
        ) as response:
            body = response.read(16385)
        if len(body) > 16384:
            raise ValueError("Release information is larger than expected.")
        return validate_release(json.loads(body))
    except urllib.error.HTTPError as exc:
        if exc.code == 503:
            raise ValueError(
                "The verified public installer is not ready yet. Your current app is unchanged."
            ) from None
        raise ValueError("Could not check for updates. Try again shortly.") from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        raise ValueError(
            "Could not reach Aedrova. Your current app is unchanged; try again later."
        ) from None
