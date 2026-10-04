# M13A release hardening — October 3, 2026

Implemented locally. Existing UI and public feature/release flags are unchanged. No hosted
SQL, storage deletion, credential, paid resource, GitHub push or deployment was performed.
The codebase walkthrough remains deferred until the entire application is complete and
deployed. Obtain permission before M14.

## Workspace storage

`supabase/migrations/202610030003_storage_retention.sql` adds a private per-workspace
accounting row, cleanup queue, retired-path registry and service-only claim/finish RPCs.
The technical beta safety ceiling is **1 GiB per workspace**, configurable by a trusted
database operator through `aedrova_private.storage_usage.limit_bytes`; this is not a new
marketed plan allowance or an assertion about measured infrastructure capacity. Existing
over-limit workspaces retain their files and cannot reserve more space until usage falls
or an operator changes the limit. Initial accounting conservatively includes all existing
pending reservations; migration may block uploads briefly and should be staged first.

Every pending reservation charges the full **10 MiB per-file ceiling**, because the caller's
declared byte count is untrusted. Idempotent retries do not charge twice. Finalization
verifies Storage's actual size against the declaration and releases the difference once.
Workspace-row and accounting-row locks prevent concurrent reservations from exceeding the
counter. Hosted multi-worker race/load testing remains an M14 acceptance requirement.

Failed/expired reservations still count until cleanup verifies deletion. Pending uploads
are retired after their one-hour reservation expiry plus a 24-hour grace period. Deleted
attachments/workspaces also create tombstones. The queue then waits another 24 hours to
avoid racing an in-flight upload. Finalized, still-referenced files are never selected.
Retired object paths cannot be reserved again, so a delayed cleanup cannot erase a new
upload at an old path. Compact retired identifiers persist intentionally; they contain
no filenames, file bodies or user IDs and must not be blindly expired.

The website repository's `aedrova_site/storage_cleanup.py` is a dedicated maintenance job,
not a public endpoint. It claims at most 10 objects, validates the entire batch, removes
bytes using the Storage API and only then acknowledges each matching, unexpired lease.
The database independently checks that Storage metadata is gone before releasing space.
Failed deletion, redirects, malformed replies, wrong leases and timeouts leave accounting
in place for safe retry. It never deletes `storage.objects` directly, consistent with
[Supabase's deletion guidance](https://supabase.com/docs/guides/storage/management/delete-objects).

The worker needs a privileged server-only key. Its scope is broad at Supabase, so keep it
in a **dedicated job environment**, never the desktop bundle, public web environment,
browser assets or chat. New secret keys go only in `apikey`; legacy service-role JWTs also
use Bearer authentication. See [Supabase API-key guidance](https://supabase.com/docs/guides/getting-started/api-keys).
No secret was requested or configured during this milestone.

## Local build/context retention

`aedrova.agents.retention` runs conservatively before a new snapshot and is also available
as a dry-run CLI. Per-build file locks protect active execution. Stale crash-left workspace
context expires after **24 hours idle**. Original projects are never modified.

A **30-day-idle** snapshot can be pruned only when all these checks pass: its project still
matches its baseline, its original project still exists and matches that baseline, no
apply/recovery receipts or unknown material exist, and no active lease is held. Unique
agent edits, missing/changed originals, additional hidden cache/config files, symlinks,
recovery backups and snapshots selected as an iteration source are preserved. This is a
redundant-copy policy, not automatic deletion of unfinished builds or recovery work.

Comparison uses streamed hashes, existing file/size caps, a five-second comparison budget
and at most three snapshot comparisons per pass. A rotating cursor bounds each metadata
pass to 200 entries. Linked paths are refused; removal uses Python's symlink-resistant
tree deletion. Ambiguous/unreadable/changed material is retained. These local files rely
on OS permissions; this is not application-level archive encryption or secure disk erasure.

From the desktop repository, inspect without deletion:

```sh
uv run python -m aedrova.agents.retention
```

Apply the same conservative policy explicitly:

```sh
uv run python -m aedrova.agents.retention --apply
```

Automatic passes occur on new builds. When the app is inactive, no continuous scheduled
deletion is claimed; an unattended schedule can be installed during M14 if desired.

## Claude network waits

Explicit Aedrova approval hooks remain in place. Claude now uses `dontAsk` for requests
outside that gate, a denying permission-request hook, early rejection of direct network
clients, and `failIfUnavailable` to prohibit silent sandbox fallback. Installed-runtime
fixtures demonstrate that a forbidden curl command returns a denial without a stall and
that normal project edits still complete. The OS sandbox remains the enforcement boundary;
the command recognizer is an early convenience gate and cannot classify arbitrary scripts.

An approved shell command also has its own deadline: requested timeout (default 120 s),
capped at 300 s plus two seconds of shutdown grace. Post-tool events clear that deadline.
An unrecognized blocked/stalled script therefore cancels with an actionable error rather
than waiting for the 30-minute build limit. Partial work is retained; networking is not
widened. All agent-version upgrades still require sandbox/protocol revalidation.

## Validation

- 473 desktop tests and 231 website/backend tests pass; Ruff passes in both repositories.
- All 23 desktop embedded PostgreSQL scripts pass, including the new quota/retirement
  checks. Tests cover declared-size accounting, retries, foreign workspace denial,
  expired/unclaimed/stale leases, physical-deletion acknowledgment, preserved live files,
  workspace cascade tombstones and counter release exactly once.
- Both installed agents pass normal-edit and outside-file/credential boundary probes.
  The forbidden-network fixture now requires a denial response and fails on a timeout.
- Local-retention tests cover active leases, dry runs, unique edits, recovery receipts,
  source changes, iteration protection and symlink/hidden-material preservation.
- Cleanup-worker fixtures cover protected origins, whole-batch validation, API errors,
  redirects, lost leases and disabled-by-default execution. No live object was removed.
- Source/resource credential-pattern check passes. Linux Docker and hosted physical/
  multi-worker/paid-provider acceptance are still deferred to M14.

## Owner actions — deferred to M14

1. In **Supabase → SQL Editor**, run the desktop repository's
   `supabase/migrations/202610030003_storage_retention.sql` after the previous migrations.
   Never run `supabase/tests` on the hosted database. This unlocks hosted quota/cleanup
   enforcement; it does not activate cleanup by itself. Stage the migration before launch.
2. Configure a **dedicated server maintenance job** using the website repository's
   `deploy/storage-cleanup.env.example`. Use the project URL and a separate Supabase secret
   key stored privately in that job's environment. Leave the flag false until its SQL,
   origin, logs and permissions have been verified. Then enable it and schedule hourly:
   `python -m aedrova_site.storage_cleanup`. Monitor failures/backlog; ten removals per pass
   is a starting bound, not a measured workload recommendation. Hosting approval is needed
   before creating a potentially billable scheduled job.
3. Publish the audited website changes and rebuild the desktop app from this source;
   revalidate the deployed job, real billing/AI/meetings, storage concurrency, backups and
   signed/notarized distribution before opening the public app/paid beta.

No new credentials, SQL execution or purchase is required **now**. These actions block
hosted acceptance/public release, not the completed local M13A implementation.
