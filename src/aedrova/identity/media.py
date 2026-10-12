"""Private workspace media API; provider keys never reach the desktop."""

import json

import httpx

from aedrova.agents.managed import validate_origin


class MediaClient:
    def __init__(self, origin, token):
        self.origin, self.token = validate_origin(origin), token

    def request(self, path, body=None):
        with httpx.Client(timeout=35, follow_redirects=False, trust_env=False) as client:
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
