"""Classify failures without exposing provider payloads or credentials."""

import httpx
from supabase_auth.errors import AuthRetryableError


def retryable(error):
    if isinstance(error, (httpx.TransportError, AuthRetryableError, TimeoutError, ConnectionError)):
        return True
    code = str(getattr(error, "code", ""))
    status = getattr(error, "status", getattr(error, "status_code", None))
    return code.startswith(("08", "53", "57")) or status in (408, 429, 500, 502, 503, 504)
