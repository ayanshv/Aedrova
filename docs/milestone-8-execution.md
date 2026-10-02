# Milestone 8 — execution durability

Implemented 2026-09-30 for the local Mac alpha.

## Behavior

- Durable SQLite queue/run history scoped to account and workspace. The private local folder
  uses 0700 permissions, the database 0600. It stores build requests, project settings,
  source channel IDs, result paths and usage; no provider credentials or full chat corpus.
- One autonomous build at a time per Mac queue, with a process lock across app instances.
  Codex inherits the lock while executing, protecting against an orphaned run after app failure.
- Up to ten waiting requests. An identical outstanding request is atomically deduplicated.
  Subsequent successful requests iterate on the prior build's separate copy.
- Queued work begins when its workspace is selected, signed in and connected. Account and
  saved folder/provider/automatic-execution permission are rechecked before dispatch; context
  access is freshly checked by the existing context collector. Changed settings pause work.
- Logout, failure and cancellation pause waiting requests. Restart marks running requests
  interrupted and waiting requests paused. No uncertain coding action is replayed automatically.
- Builds panel supports explicit resume/retry, queued cancellation, saved files and completed
  result review. Retrying an interrupted/failed run creates a new attempt and recollects context;
  it does not resume a provider conversation. Inspect partial files before retrying.
- Saved review rechecks source channel access. Local application and GitHub publication retain
  their separate exact approvals and fresh service authorization.
- Per-attempt/per-phase elapsed time and provider-reported input/output tokens. Missing values
  are unknown, including incomplete/crashed turns. This is local telemetry, not billing or a
  cross-device allowance; M9 owns server-enforced entitlements and usage reservations.
- Existing limits: three-minute context collection, 8 MiB context, 20,000-file/200 MiB snapshots,
  25 MiB per file, thirty-minute provider phases, bounded events/output. New low-disk gate
  requires at least 512 MiB free before snapshotting. Retained results are not auto-deleted.
- Typing @ offers @Aedrova completion in chat and thread composers. Click, Tab or Return
  completes it; Escape dismisses. Completion never itself submits a build.

## Validation and external limits

Python regression and embedded PostgreSQL suites are recorded in work/m8-tests.log and
work/m8-sql.log. Targeted checks cover concurrent duplicate submission, queue limits,
serial execution/iteration, recovery, exclusive locking, scoped history/usage, logout,
changed settings, saved-review access, low disk, actual runtime usage events and mention keys.

A real Codex M8 acceptance attempt successfully planned, wrote calculator.py/test_calculator.py
and ran four generated unittest cases (OK), then reached the account's provider usage limit
before a successful final turn result. It is correctly recorded as failed, with partial files
retained. This is NOT a passed complete live M8 provider acceptance. The previous milestone's
successful real Codex run remains valid for that earlier implementation. No GitHub publication
was attempted. Paid Claude and hosted two-account revocation remain external acceptance gates.

Codex event reference: https://learn.chatgpt.com/docs/non-interactive-mode .

## Owner actions

Required to use the new version: quit the old app and reopen dist/Aedrova.app. Keep one
Aedrova instance open. Enable automatic execution in Projects → Project settings if not already
saved. Open Builds to resume saved requests after a restart; review partial files first.

No new Supabase SQL, OAuth configuration or secrets are needed for M8. For another complete
live Codex acceptance, wait for the provider plan's reset (or manage credits in the provider's
own account), then send a new request. M9 included-AI billing is not active yet. Do not paste
provider secrets into chat. Live GitHub publishing still needs the existing browser authorization
and test-repository acceptance from M7.

M9 remains unstarted pending the owner's sequential milestone approval.
