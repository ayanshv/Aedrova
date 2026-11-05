# ruff: noqa: E501
"""Restore a synthetic PostgreSQL backup and rerun real application access rules.

Uses the pinned PGlite engine already verified by scripts/test_database.py.
No hosted database, customer data, credentials, provider or payment is accessed.
"""

import argparse
import json
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
CHECKS = (
    "verified_uploads",
    "voice_messages",
    "bud_conversations",
    "bud_plan_limits",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--node", required=True)
    parser.add_argument("--pglite", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    migrations = sorted((ROOT / "supabase/migrations").glob("*.sql"))
    checks = list(CHECKS)
    if any(path.name.endswith("_shared_agent_work.sql") for path in migrations):
        checks.append("shared_agent_work")
    tests = [ROOT / "supabase/tests" / (name + ".sql") for name in checks]
    with TemporaryDirectory(prefix="aedrova-recovery-") as directory:
        folder = Path(directory)
        manifest = folder / "manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "bootstrap": str(ROOT / "supabase/tests/bootstrap.sql"),
                    "migrations": [str(path) for path in migrations],
                    "tests": [str(path) for path in tests],
                }
            )
        )
        runner = folder / "restore.mjs"
        runner.write_text(
            "import {PGlite} from "
            + json.dumps(args.pglite.resolve().as_uri())
            + ";\n"
            + r"""import fs from 'node:fs';
import crypto from 'node:crypto';
const manifest=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const backup=process.argv[3];
let db=new PGlite();
const assert=(ok,message)=>{if(!ok) throw new Error(message);};
async function fingerprint() {
 const rows=await db.query("SELECT schemaname,tablename,policyname,roles,cmd,qual,with_check FROM pg_policies ORDER BY schemaname,tablename,policyname");
 const roles=await db.query("SELECT rolname,rolsuper,rolcreaterole,rolcreatedb,rolcanlogin,rolbypassrls FROM pg_roles ORDER BY rolname");
 const grants=await db.query("SELECT grantee,table_schema,table_name,privilege_type FROM information_schema.role_table_grants WHERE table_schema IN ('public','storage') ORDER BY 1,2,3,4");
 const state=await db.query('SELECT id,body,channel_id FROM public.messages ORDER BY id');
 return crypto.createHash('sha256').update(JSON.stringify([rows.rows,roles.rows,grants.rows,state.rows])).digest('hex');
}
try {
 await db.exec(fs.readFileSync(manifest.bootstrap,'utf8'));
 for(const file of manifest.migrations) await db.exec(fs.readFileSync(file,'utf8'));
 await db.exec(`INSERT INTO auth.users(id,email,email_confirmed_at) VALUES
 ('f6100000-0000-0000-0000-000000000001','restore-owner@test.local',now()),
 ('f6100000-0000-0000-0000-000000000002','restore-outsider@test.local',now());
 SET ROLE authenticated;
 SET request.jwt.claim.sub='f6100000-0000-0000-0000-000000000001';`);
 const workspace=(await db.query("SELECT public.onboard_workspace('Recovery fixture','Aedrova','codex')::text AS id")).rows[0].id;
 const channel=(await db.query('SELECT id::text FROM public.channels WHERE workspace_id=$1 LIMIT 1',[workspace])).rows[0].id;
 await db.query("SELECT public.send_message($1,$2,'Synthetic recovery evidence')",['f6200000-0000-0000-0000-000000000001',channel]);
 await db.exec('RESET ROLE');
 const before=await fingerprint();
 const archive=await db.dumpDataDir('gzip');
 fs.writeFileSync(backup,Buffer.from(await archive.arrayBuffer()),{mode:0o600});
 const digest=crypto.createHash('sha256').update(fs.readFileSync(backup)).digest('hex');
 await db.exec("DELETE FROM public.messages; INSERT INTO auth.users(id,email) VALUES ('f6100000-0000-0000-0000-000000000003','after-backup@test.local')");
 await db.close();
 db=new PGlite({loadDataDir:new Blob([fs.readFileSync(backup)])});
 assert(await fingerprint()===before,'Restored schema, roles, permissions or content changed');
 assert((await db.query("SELECT count(*)::int AS n FROM auth.users WHERE email='after-backup@test.local'")).rows[0].n===0,'Recovery did not return to the backup point');
 await db.exec("SET ROLE authenticated; SET request.jwt.claim.sub='f6100000-0000-0000-0000-000000000001'");
 assert((await db.query('SELECT count(*)::int AS n FROM public.messages')).rows[0].n===1,'Owner cannot read recovered work');
 await db.exec("SET request.jwt.claim.sub='f6100000-0000-0000-0000-000000000002'");
 assert((await db.query('SELECT count(*)::int AS n FROM public.messages')).rows[0].n===0,'Recovered data leaked to outsider');
 await db.exec('RESET ROLE');
 await db.exec("DELETE FROM public.workspaces WHERE name='Recovery fixture'");
 await db.exec("DELETE FROM auth.users WHERE id IN ('f6100000-0000-0000-0000-000000000001','f6100000-0000-0000-0000-000000000002')");
 for(const file of manifest.tests) {
  await db.exec(fs.readFileSync(file,'utf8'));
  console.log('PASS restored '+file.split('/').pop());
 }
 console.log(JSON.stringify({status:'passed',scope:'synthetic local PostgreSQL only',migrations:manifest.migrations.length,restoredAccessSuites:manifest.tests.length,backupSha256:digest,bytes:fs.statSync(backup).size,rolePolicyAndDataFingerprint:before,pointInTimeVerified:true}));
} catch(error) { console.error(error.message); process.exitCode=1; } finally { await db.close(); }
"""
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w") as report:
            subprocess.run(
                [args.node, str(runner), str(manifest), str(folder / "synthetic-postgres.tgz")],
                check=True,
                stdout=report,
                timeout=180,
            )


if __name__ == "__main__":
    main()
