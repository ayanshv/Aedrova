"""Private workspace media API; provider keys never reach the desktop."""

import json
import time
from threading import Lock, Thread

import httpx

from aedrova.agents.managed import validate_origin


class MediaClient:
    def __init__(self, origin, token):
        self.origin, self.token = validate_origin(origin), token

    def request(self, path, body=None):
        # Free staging hosts can take over 35 seconds to wake. Never retry a POST
        # whose publication outcome is ambiguous; allow one bounded verification wait.
        timeout = httpx.Timeout(90 if path == "/api/files/verify" else 35, connect=10)
        with httpx.Client(timeout=timeout, follow_redirects=False, trust_env=False) as client:
            with client.stream(
                "GET" if body is None else "POST",
                self.origin + path,
                headers={"Authorization": "Bearer " + self.token, "Accept-Encoding": "identity"},
                json=body,
            ) as response:
                if response.status_code != 200:
                    raise RuntimeError(
                        "This service is unavailable. Check connection, access and team allowance."
                    )
                data = bytearray()
                for chunk in response.iter_bytes():
                    if len(data) + len(chunk) > 16384:
                        raise ValueError("Invalid media response")
                    data.extend(chunk)
        result = json.loads(data)
        if not isinstance(result, dict):
            raise ValueError("Invalid media response")
        return result


_warm_lock = Lock()
_warm_at = {}


def warm_upload_verifier(origin):
    """Wake only the configured service, at most once/minute on attachment intent."""
    origin = validate_origin(origin)
    with _warm_lock:
        now = time.monotonic()
        if now - _warm_at.get(origin, float("-inf")) < 60:
            return
        _warm_at[origin] = now

    def wake():
        try:
            with httpx.Client(timeout=55, follow_redirects=False, trust_env=False) as client:
                with client.stream("GET", origin + "/health"):
                    pass  # No auth, file data, retained response or automatic retries.
        except httpx.HTTPError:
            pass  # The real authenticated verifier remains authoritative.

    Thread(target=wake, name="aedrova-upload-wake", daemon=True).start()
