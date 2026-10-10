"""Local durable queue. No provider output, credentials or chat corpus is persisted here."""

import fcntl
import hashlib
import json
import os
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4


class RunLedger:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.directory.chmod(0o700)
        self.path = self.directory / "runs.sqlite3"
        fd = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o600)
        os.close(fd)
        self.path.chmod(0o600)
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY, user TEXT NOT NULL, workspace TEXT NOT NULL,
                    task TEXT NOT NULL, settings TEXT NOT NULL, fingerprint TEXT NOT NULL,
                    state TEXT NOT NULL, created REAL NOT NULL, updated REAL NOT NULL,
                    project TEXT NOT NULL DEFAULT '', baseline TEXT NOT NULL DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS usage (
                    run_id TEXT NOT NULL, phase TEXT NOT NULL, provider TEXT NOT NULL,
                    seconds REAL NOT NULL, input_tokens INTEGER, output_tokens INTEGER,
                    PRIMARY KEY(run_id, phase)
                );
            """)

        with self.connect() as db:
            columns = {row[1] for row in db.execute("PRAGMA table_info(runs)")}
            if "channels" not in columns:
                db.execute("ALTER TABLE runs ADD COLUMN channels TEXT NOT NULL DEFAULT '[]'")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def lock(self):
        fd = os.open(self.directory / "execution.lock", os.O_CREAT | os.O_RDWR, 0o600)
        stream = os.fdopen(fd, "w")
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            stream.close()
            return None
        return stream

    def recover(self):
        """Caller owns the execution lock. Never automatically replay uncertain actions."""
        with self.connect() as db:
            db.execute(
                "UPDATE runs SET state='interrupted', updated=? WHERE state='running'",
                (time.time(),),
            )
            db.execute(
                "UPDATE runs SET state='paused', updated=? WHERE state='queued'", (time.time(),)
            )

    def enqueue(self, user, workspace, task, settings):
        task = task.strip()
        if not task or len(task) > 20000:
            raise ValueError("Build requests must contain 1–20,000 characters.")
        scope = json.dumps(settings, sort_keys=True)
        fingerprint = hashlib.sha256((task + scope).encode()).hexdigest()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            duplicate = db.execute(
                "SELECT id FROM runs WHERE user=? AND workspace=? AND fingerprint=? "
                "AND state IN ('queued','running','paused')",
                (user, workspace, fingerprint),
            ).fetchone()
            if duplicate:
                return duplicate[0], False
            count = db.execute(
                "SELECT count(*) FROM runs WHERE state IN ('queued','paused')"
            ).fetchone()[0]
            if count >= 10:
                raise ValueError("The queue is full (10 requests). Cancel a queued request first.")
            run_id = str(uuid4())
            now = time.time()
            db.execute(
                "INSERT INTO runs (id,user,workspace,task,settings,fingerprint,state,"
                "created,updated,project,baseline) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                (run_id, user, workspace, task, scope, fingerprint, "queued", now, now, "", ""),
            )
            return run_id, True

    def rows(self, user, workspace):
        with self.connect() as db:
            return [
                dict(row)
                for row in db.execute(
                    "SELECT * FROM runs WHERE user=? AND workspace=? "
                    "ORDER BY created DESC LIMIT 100",
                    (user, workspace),
                )
            ]

    def update(self, run_id, state, *, project="", baseline=""):
        with self.connect() as db:
            db.execute(
                "UPDATE runs SET state=?,updated=?,project=CASE WHEN ?='' THEN project ELSE ? END, "
                "baseline=CASE WHEN ?='' THEN baseline ELSE ? END WHERE id=?",
                (
                    state,
                    time.time(),
                    str(project or ""),
                    str(project or ""),
                    baseline,
                    baseline,
                    run_id,
                ),
            )

    def save_channels(self, run_id, channels):
        with self.connect() as db:
            db.execute(
                "UPDATE runs SET channels=? WHERE id=?", (json.dumps(sorted(channels)), run_id)
            )

    def pause_user(self, user):
        with self.connect() as db:
            db.execute(
                "UPDATE runs SET state='paused',updated=? WHERE user=? AND state='queued'",
                (time.time(), user),
            )

    def record_usage(self, run_id, phase, provider, seconds, usage):
        def tokens(key):
            value = usage.get(key)
            return value if type(value) is int and value >= 0 else None

        with self.connect() as db:
            db.execute(
                "INSERT OR REPLACE INTO usage VALUES (?,?,?,?,?,?)",
                (
                    run_id,
                    phase,
                    provider,
                    max(0, seconds),
                    tokens("input_tokens"),
                    tokens("output_tokens"),
                ),
            )

    def usage(self, run_id, user, workspace):
        with self.connect() as db:
            return [
                dict(row)
                for row in db.execute(
                    "SELECT usage.* FROM usage JOIN runs ON runs.id=usage.run_id "
                    "WHERE run_id=? AND user=? AND workspace=?",
                    (run_id, user, workspace),
                )
            ]
