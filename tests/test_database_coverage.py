"""New database migrations must not silently escape the release RLS harness."""

import re
from pathlib import Path


def test_every_migration_is_included_in_database_runner():
    root = Path(__file__).resolve().parents[1]
    runner = (root / "scripts/test_database.py").read_text()
    included = set(re.findall(r"'supabase/migrations/([^']+\.sql)'", runner))
    migrations = {path.name for path in (root / "supabase/migrations").glob("*.sql")}
    assert migrations
    assert migrations <= included, f"Untested migrations: {sorted(migrations - included)}"
