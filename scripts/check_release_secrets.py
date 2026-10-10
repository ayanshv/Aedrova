"""Baseline leak check for first-party runtime sources and optional packaged resources.

Detects common credential formats and accidental environment-file inclusion. Reports
paths and rule names only, never matching credential values. Not a complete security audit.
"""

import argparse
import subprocess
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
    parser.add_argument("--tracked", action="store_true", help="Also scan all Git-tracked files")
    args = parser.parse_args()
    paths = list((ROOT / "src").rglob("*.py"))
    paths += list((ROOT / "src/aedrova/desktop/assets").rglob("*"))
    if args.app:
        # Third-party binaries are covered by dependency review, not this source pattern check.
        paths += list((args.app / "Contents/Resources/aedrova").rglob("*"))
        paths += [p for p in args.app.rglob("*") if p.name.startswith(".env")]
    findings = inspect_paths(paths)
    if args.tracked:
        names = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
        for name in filter(None, names):
            path = ROOT / name
            if "node_modules" in path.parts:
                findings.append((name, "tracked-vendor-directory"))
            if path.is_file():
                if path.name.startswith(".env") and not path.name.endswith(".example"):
                    findings.append((name, "tracked-environment-file"))
                findings.extend((name, rule) for rule in credential_rules(path.read_bytes()))
    for path, rule in findings:
        print(f"FAIL {rule}: {path}")
    if findings:
        raise SystemExit(1)
    print("PASS baseline runtime-source/resource secret patterns and environment-file exclusion")


if __name__ == "__main__":
    main()
