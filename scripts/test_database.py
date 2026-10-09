"""Run the actual migration/RLS tests in embedded PostgreSQL (not hosted Supabase).

Requires Node 20+ solely for the third-party PGlite PostgreSQL engine. App code is Python.
Downloads the pinned engine to ignored work/, verifies its npm integrity hash, and uses
only a disposable in-memory database. No credentials, hosted database, or Docker needed.
"""

import argparse
import base64
import hashlib
import json
import shutil
import subprocess
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.5.8"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--node", default=shutil.which("node"))
    args = parser.parse_args()
    if not args.node:
        parser.error("Node 20+ is required; pass --node /absolute/path/to/node")
    directory = ROOT / "work" / "pglite"
    directory.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(
        f"https://registry.npmjs.org/@electric-sql/pglite/{VERSION}", timeout=30
    ) as response:
        metadata = json.load(response)
    with urllib.request.urlopen(metadata["dist"]["tarball"], timeout=30) as response:
        archive = response.read()
    expected = metadata["dist"]["integrity"]
    actual = "sha512-" + base64.b64encode(hashlib.sha512(archive).digest()).decode()
    if actual != expected:
        raise RuntimeError("PGlite integrity check failed")
    archive_path = directory / "package.tgz"
    archive_path.write_bytes(archive)
    with tarfile.open(archive_path) as bundle:
        bundle.extractall(directory, filter="data")
    # Thin adapter to the third-party engine; all test logic is versioned SQL.
    runner = directory / "run.mjs"
    runner.write_text("""import {PGlite} from './package/dist/index.js';
import fs from 'node:fs';
let db = new PGlite();
try {
 for(const file of ['supabase/tests/bootstrap.sql',
   'supabase/migrations/202609260001_identity.sql',
   'supabase/migrations/202609270001_agent_onboarding.sql',
   'supabase/migrations/202609270002_messages.sql',
   'supabase/tests/identity.sql','supabase/tests/agent_onboarding.sql',
   'supabase/tests/messages.sql',
   'supabase/migrations/202609280001_communication.sql',
   'supabase/tests/communication.sql',
   'supabase/migrations/202609290001_context_decisions.sql',
   'supabase/tests/context_decisions.sql',
   'supabase/migrations/202610010001_meetings.sql',
   'supabase/tests/meetings.sql',
   'supabase/migrations/202610020001_scalability.sql',
   'supabase/tests/scalability.sql',
   'supabase/migrations/202610020002_workspace_archive.sql',
   'supabase/tests/workspace_archive.sql',
   'supabase/migrations/202610030001_meeting_context.sql',
   'supabase/tests/meeting_context.sql',
   'supabase/migrations/202610030002_meeting_speech_review.sql',
   'supabase/tests/meeting_speech_review.sql',
   'supabase/migrations/202610030003_storage_retention.sql',
   'supabase/tests/storage_retention.sql',
   'supabase/migrations/202610030004_meeting_activity.sql',
   'supabase/tests/meeting_activity.sql',
   'supabase/migrations/202610040001_message_interactions.sql',
   'supabase/tests/message_interactions.sql',
   'supabase/migrations/202610040002_chat_collaboration.sql',
   'supabase/tests/chat_collaboration.sql',
   'supabase/migrations/202610050001_user_profiles.sql',
   'supabase/tests/user_profiles.sql',
   'supabase/migrations/202610060001_product_memory.sql',
   'supabase/migrations/202610060002_memory_conflict_response.sql',
   'supabase/tests/product_memory.sql',
   'supabase/migrations/202610060003_build_reviews.sql',
   'supabase/tests/build_reviews.sql',
   'supabase/migrations/202610060004_ai_teammates.sql',
   'supabase/tests/ai_teammates.sql',
   'supabase/migrations/202610070001_workspace_dots.sql',
   'supabase/tests/workspace_dots.sql',
   'supabase/migrations/202610070002_bud_profiles.sql',
   'supabase/migrations/202610070002_bud_profiles.sql',
   'supabase/tests/bud_profiles.sql',
   'supabase/migrations/202610070003_bud_appearance.sql',
   'supabase/migrations/202610070003_bud_appearance.sql',
   'supabase/tests/bud_appearance.sql',
   'supabase/migrations/202610070004_bud_connectors.sql',
   'supabase/migrations/202610070004_bud_connectors.sql',
   'supabase/tests/bud_connectors.sql']) {
  let sql = fs.readFileSync(file,'utf8');
  // Reproduce the already-activated original function, then verify its additive
  // conflict-response upgrade before running the lifecycle tests.
  if(file === 'supabase/migrations/202610060001_product_memory.sql') {
   sql = sql.replaceAll("errcode='PT409'", "errcode='40001'");
  }
  await db.exec(sql);
  console.log('PASS '+file);
 }
 await db.close();
 db = new PGlite();
 // Hosted projects may have deferred meeting context. Test that installation
 // order separately rather than hiding the dependency behind the full schema.
 for(const file of ['supabase/tests/bootstrap.sql',
   'supabase/migrations/202609260001_identity.sql',
   'supabase/migrations/202609270001_agent_onboarding.sql',
   'supabase/migrations/202609270002_messages.sql',
   'supabase/migrations/202609280001_communication.sql',
   'supabase/migrations/202609290001_context_decisions.sql',
   'supabase/migrations/202610010001_meetings.sql',
   'supabase/migrations/202610020001_scalability.sql',
   'supabase/migrations/202610040001_message_interactions.sql',
   'supabase/migrations/202610060001_product_memory.sql',
   'supabase/migrations/202610060002_memory_conflict_response.sql',
   'supabase/tests/product_memory_without_meetings.sql',
   'supabase/migrations/202610030001_meeting_context.sql',
   'supabase/tests/product_memory_late_meetings.sql']) {
  await db.exec(fs.readFileSync(file,'utf8'));
  console.log('PASS optional-meetings '+file);
 }
} catch(e) {console.error(e.message); process.exitCode=1;} finally {await db.close();}
""")
    subprocess.run([args.node, str(runner)], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
