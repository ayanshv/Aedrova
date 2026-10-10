"""Baseline leak check for first-party runtime sources and optional packaged resources.

Detects common credential formats and accidental environment-file inclusion. Reports
paths and rule names only, never matching credential values. Not a complete security audit.
"""

import argparse
from pathlib import Path

from aedrova.security.credentials import credential_rules

ROOT = Path(__file__).resolve().parents[1]


def inspect_paths(paths):
    findings = []
    for path in paths:
        if not path.is_file():
            continue
        if path.name == ".env" or path.name.startswith(".env."):
            findings.append((str(path), "environment-file"))
        data = path.read_bytes()
        findings.extend((str(path), rule) for rule in credential_rules(data))
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
