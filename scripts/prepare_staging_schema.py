"""Prepare the reviewed schema for a fresh staging project; never execute SQL."""

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGING_REF = "scvmvqlzcqhwrrsiahpj"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "work/staging/schema.sql")
    args = parser.parse_args()
    pieces = [
        f"-- FRESH Aedrova Staging ONLY: {STAGING_REF}. Never run on production.\n"
        "-- Creates app tables/RLS/functions; no users, customer data or credentials.\n"
        "BEGIN;\nDO $$ BEGIN\n"
        " IF to_regclass('public.workspaces') IS NOT NULL THEN\n"
        "  RAISE EXCEPTION 'Not a fresh staging database; stop and review.';\n"
        " END IF;\nEND $$;\n"
    ]
    migrations = sorted((ROOT / "supabase/migrations").glob("*.sql"))
    for path in migrations:
        sql = path.read_text()
        # One atomic transaction: do not leave half-installed app migrations.
        lines = [
            line for line in sql.splitlines() if line.strip().lower() not in {"begin;", "commit;"}
        ]
        pieces.append(f"\n-- Migration: {path.name}\n" + "\n".join(lines) + "\n")
    pieces.append("COMMIT;\nSELECT 'Staging app schema installed' AS result;\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("".join(pieces))
    print(f"Prepared {len(migrations)} ordered migrations: {args.output}")
    print("No database was accessed. Apply only to the named fresh staging project.")


if __name__ == "__main__":
    main()
