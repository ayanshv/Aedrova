"""Launch source against explicit staging public endpoints, with isolated preferences.

No provider keys, production fallback, frozen release or shared app preferences.
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

from aedrova.agents.managed import validate_origin
from aedrova.identity.service import Connection

ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_HOSTS = {
    "aedrova.com",
    "www.aedrova.com",
    "aedrova-connectors.onrender.com",
    "cpelagtufyocepnqcqqd.supabase.co",
}


def validate(config):
    if config.get("environment") != "staging":
        raise ValueError("Use an explicit staging profile.")
    Connection(config["supabase_url"], config["supabase_publishable_key"])
    for key in ("supabase_url", "managed_origin", "connector_origin"):
        validate_origin(config[key])
        if urlparse(config[key]).hostname in PRODUCTION_HOSTS:
            raise ValueError("Staging must not use production endpoints.")
    if set(config) != {
        "environment",
        "supabase_url",
        "supabase_publishable_key",
        "managed_origin",
        "connector_origin",
    }:
        raise ValueError("Staging public profiles must contain public endpoints and keys only.")
    return config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    config = validate(json.loads(args.config.read_text()))
    if args.check_only:
        print("PASS explicit staging endpoints/public key; no production fallback")
        return
    environment = dict(os.environ)
    environment.update(
        {
            "AEDROVA_SUPABASE_URL": config["supabase_url"],
            "AEDROVA_SUPABASE_PUBLISHABLE_KEY": config["supabase_publishable_key"],
            "AEDROVA_MANAGED_ORIGIN": config["managed_origin"],
            "AEDROVA_CONNECTOR_ORIGIN": config["connector_origin"],
            "AEDROVA_AI_ACCESS_MODE": "included",
        }
    )
    # Separate persisted preferences/project bindings; login sessions stay in memory.
    subprocess.run(
        [
            sys.executable,
            "-m",
            "aedrova.desktop.app",
            "--account",
            "--settings-file",
            str(ROOT / "work/staging/app.ini"),
        ],
        cwd=ROOT,
        env=environment,
        check=True,
    )


if __name__ == "__main__":
    main()
