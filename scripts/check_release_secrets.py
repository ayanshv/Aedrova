"""Baseline leak check for first-party runtime sources and optional packaged resources.

Detects common credential formats and accidental environment-file inclusion. Reports
paths and rule names only, never matching credential values. Not a complete security audit.
"""

import argparse
import base64
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "private-key": rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    "supabase-secret": rb"sb_secret_[A-Za-z0-9_-]{20,}",
    "google-client-secret": rb"GOCSPX-[A-Za-z0-9_-]{20,}",
    "provider-secret": rb"sk-(?:proj-|ant-)[A-Za-z0-9_-]{20,}",
    "github-token": rb"gh[pousr]_[A-Za-z0-9]{30,}",
    "stripe-secret": rb"sk_live_[A-Za-z0-9]{20,}",
    "aws-access-key": rb"AKIA[A-Z0-9]{16}",
}


def inspect_paths(paths):
    findings = []
    for path in paths:
        if not path.is_file():
            continue
        if path.name == ".env" or path.name.startswith(".env."):
            findings.append((str(path), "environment-file"))
        data = path.read_bytes()
        for token in re.findall(rb"eyJ[A-Za-z0-9_-]+\.([A-Za-z0-9_-]+)\.[A-Za-z0-9_-]+", data):
            try:
                claims = json.loads(base64.urlsafe_b64decode(token + b"=" * (-len(token) % 4)))
                if isinstance(claims, dict) and claims.get("role") == "service_role":
                    findings.append((str(path), "supabase-service-role-jwt"))
            except (ValueError, UnicodeDecodeError):
                pass
        for name, pattern in PATTERNS.items():
            if re.search(pattern, data):
                findings.append((str(path), name))
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", type=Path)
    args = parser.parse_args()
    paths = list((ROOT / "src").rglob("*.py"))
    paths += list((ROOT / "src/aedrova/desktop/assets").rglob("*"))
    if args.app:
        # Third-party binaries are covered by dependency review, not this source pattern check.
        paths += list((args.app / "Contents/Resources/aedrova").rglob("*"))
        paths += [p for p in args.app.rglob("*") if p.name.startswith(".env")]
    findings = inspect_paths(paths)
    for path, rule in findings:
        print(f"FAIL {rule}: {path}")
    if findings:
        raise SystemExit(1)
    print("PASS baseline runtime-source/resource secret patterns and environment-file exclusion")


if __name__ == "__main__":
    main()
