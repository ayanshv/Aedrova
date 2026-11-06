"""Real two-connection revocation regression in a disposable loopback database."""

import argparse
import json
import os
import threading
import time
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

ROOT = Path(__file__).resolve().parents[1]
OWNER = "f7100000-0000-0000-0000-000000000001"
MEMBER = "f7100000-0000-0000-0000-000000000002"
FIX = "202611050001_shared_work_revocation_lock.sql"


def connection(dsn, actor=None):
    value = psycopg.connect(dsn, autocommit=True)
    value.execute("SET statement_timeout='10s'")
    if actor:
        value.execute("SET ROLE authenticated")
        value.execute("SELECT set_config('request.jwt.claim.sub',%s,false)", (actor,))
    return value


def race(dsn, *, fixed, private=False):
    with connection(dsn) as admin, connection(dsn, OWNER) as owner:
        admin.execute(
            "INSERT INTO auth.users(id,email,email_confirmed_at) VALUES(%s,%s,now()),"
            "(%s,%s,now()) ON CONFLICT(id) DO NOTHING",
            (OWNER, "race-owner@test.local", MEMBER, "race-member@test.local"),
        )
        workspace = owner.execute(
            "SELECT public.onboard_workspace(%s,'Aedrova','codex')", ("Race " + uuid4().hex,)
        ).fetchone()[0]
        channel = owner.execute(
            "SELECT id FROM public.channels WHERE workspace_id=%s LIMIT 1", (workspace,)
        ).fetchone()[0]
        invitation = owner.execute(
            "SELECT public.create_invitation(%s,%s,'member')", (workspace, "race-member@test.local")
        ).fetchone()[0]
        with connection(dsn, MEMBER) as member:
            member.execute("SELECT public.accept_invitation(%s)", (invitation,))
        sources = [channel]
        if private:
            source = owner.execute(
                "SELECT public.create_channel(%s,%s,true)", (workspace, "private-source")
            ).fetchone()[0]
            owner.execute("SELECT public.set_channel_member(%s,%s,true)", (source, MEMBER))
            sources.append(source)
        owner.execute("BEGIN")
        if private:
            owner.execute("SELECT public.set_channel_member(%s,%s,false)", (source, MEMBER))
        else:
            owner.execute("SELECT public.remove_member(%s,%s)", (workspace, MEMBER))
        result, pid_ready = {}, threading.Event()

        def write():
            with connection(dsn, MEMBER) as member:
                result["pid"] = member.info.backend_pid
                pid_ready.set()
                try:
                    member.execute(
                        "SELECT public.save_shared_agent_work(%s,%s,%s,%s,%s,%s)",
                        (
                            uuid4(),
                            workspace,
                            channel,
                            "Research Bud",
                            "Synthetic race evidence",
                            sources,
                        ),
                    )
                    result["outcome"] = "inserted"
                except psycopg.Error as error:
                    result["outcome"] = error.sqlstate

        worker = threading.Thread(target=write, daemon=True)
        worker.start()
        try:
            assert pid_ready.wait(3), "Writer did not connect"
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                wait = admin.execute(
                    "SELECT wait_event_type FROM pg_stat_activity WHERE pid=%s", (result["pid"],)
                ).fetchone()
                if wait and wait[0] == "Lock":
                    break
                time.sleep(0.02)
            else:
                raise AssertionError("Writer did not reach the intentional lock contention")
            owner.execute("COMMIT")
            worker.join(10)
            assert not worker.is_alive(), "Writer did not finish"
            assert result.get("outcome") == ("42501" if fixed else "inserted"), result
            count = admin.execute(
                "SELECT count(*) FROM public.shared_agent_work WHERE workspace_id=%s", (workspace,)
            ).fetchone()[0]
            assert count == (0 if fixed else 1)
            return {
                "fixed": fixed,
                "revocation": "private-source" if private else "workspace",
                "outcome": result["outcome"],
                "late_rows": count,
            }
        finally:
            if owner.info.transaction_status != psycopg.pq.TransactionStatus.IDLE:
                owner.execute("ROLLBACK")
            worker.join(10)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dsn-env", default="AEDROVA_TEST_DATABASE_URL")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    dsn = os.environ[args.dsn_env]
    host = conninfo_to_dict(dsn).get("host", "")
    if host not in {"127.0.0.1", "localhost", "::1"} and not host.startswith("/"):
        raise SystemExit("Use an isolated local PostgreSQL server only")
    database = "aedrova_security_" + uuid4().hex
    target = make_conninfo(dsn, dbname=database)
    with connection(dsn) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
        try:
            with connection(target) as db:
                db.execute((ROOT / "supabase/tests/bootstrap.sql").read_text())
                for path in sorted((ROOT / "supabase/migrations").glob("*.sql")):
                    if path.name != FIX:
                        db.execute(path.read_text())
            results = [race(target, fixed=False)]
            with connection(target) as db:
                db.execute((ROOT / "supabase/migrations" / FIX).read_text())
            results += [race(target, fixed=True), race(target, fixed=True, private=True)]
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps({"status": "passed", "results": results}, indent=2))
            print(
                "PASS original race reproduced; fixed workspace and private-source "
                "revocations deny late writes"
            )
        finally:
            admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(database)))


if __name__ == "__main__":
    main()
