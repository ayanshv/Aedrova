"""Hosted audio and video calls are optional; local meeting notes work without them."""

import json
import os
import sys
from pathlib import Path


def hosted_calls_enabled():
    """Packaged builds list the choice explicitly; source runs keep the calls available."""
    path = Path(__file__).parent / "assets/public-config.json"
    try:
        configuration = json.loads(path.read_text()) if path.exists() else {}
    except (OSError, ValueError):
        configuration = {}
    if "hosted_calls_enabled" in configuration:
        return configuration["hosted_calls_enabled"] is True
    if not getattr(sys, "frozen", False) and os.getenv("AEDROVA_HOSTED_CALLS_ENABLED"):
        return os.getenv("AEDROVA_HOSTED_CALLS_ENABLED") == "true"
    return True
