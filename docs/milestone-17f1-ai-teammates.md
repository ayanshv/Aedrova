# M17F.1 — useful, customizable AI teammates

First useful slice implemented; owner SQL applied and hosted two-account profile acceptance passed.
M17F.2 has not started. M14 activation/signing/live billing remains deferred.

## Current experience

The sidebar's AI teammates button opens the native, theme-aware editor. Owner/admins
create up to 12 active identities per workspace. Members can inspect profiles and assign
work. Name, shape, blue/purple palette, responsibilities, personality, reporting style,
work window and importance persist in Supabase. Pause/remove/edit increments the identity
version; stale queued work and recovered reviews require a fresh assignment. Removal is
soft deletion, preserving identity boundaries. Builder and teammate names cannot collide.

Composer autocomplete displays the configured name and retains a stable identity token.
Send `@Pixel summarize the approved requirements` or an Engineering assignment using your
own teammate's name. Progress and results use that name and character in the existing
chat agent feed. Quiet/milestones/detailed controls progress verbosity; phase/error/final
states remain visible. Characters blink in the editor and respect reduced-motion settings.

Engineering reuses the connected Codex/Claude runner, planning, isolated checkout,
existing test/delivery controls and explicit publication approval. Product/Research use
the read-only planning sandbox for source-backed analysis, never the editing phase.
A project folder, working provider and saved background workflow settings are still
required for this first slice, including analysis roles. No provider is activated here.
Context retrieval reuses the requester's accessible conversations/files, permitted meeting
text and approved Product memory; it is bounded retrieval, not a claim of exhaustive recall.

Current results are private to the assigning user's local agent feed. Run metadata is
scoped/durable locally; this slice does not add a shared cross-device result archive.
Durable shared results, team delegation and management are M17F.2. Explicit teammate-specific
connector/tool grants and Marketing/Design/Finance integrations are M17F.3. No idle polling
starts model runs, no recurring reports are scheduled, and no external messages are sent.

Work windows (5/15/30 minutes per phase) cap runtime, not API charges or reasoning tokens.
Importance is a communication preference, not queue priority or expanded authority. Existing
managed-provider usage limits remain in force; this does not add a per-teammate billing cap.
Profiles reject recognizable credential patterns, not every conceivable secret.

## Owner actions and acceptance

The owner applied `202610060004_ai_teammates.sql` and confirmed Success.
Normal Google OAuth with the approved personal/school accounts passed profile persistence,
safe retries, outsider isolation, member read/owner-admin write boundaries, duplicate actor
names, pause/stale-edit/rename behavior, stable mention resolution, revocation while a
profile still existed, and deletion without identity resurrection. The school account was
removed afterward and the synthetic teammate soft-deleted. Tokens stayed in memory.
Report: `work/m17f1/hosted-teammate-check.json`.

**Required owner action now: none.** Existing provider access and project/background settings
are needed to assign work. No new connector credentials are requested. Ask permission for
M17F.2 before starting shared results/team management. Later provider activation, Apple
signing, live Stripe and final multi-device acceptance remain deferred M14/M18 gates.

## Validation

Full desktop suite: 597 passed. Final focused teammate/execution suite: 36 passed.
Website public-page/navigation/assets suite: 32 passed. Actual PostgreSQL/RLS migration
suites, scoped Ruff, packaged signature and packaged smoke passed. SQL tests cover owner/member/outsider
access, direct-write denial, unique names in both directions, retries, stale versions,
pause/delete and membership revocation. Native light/dark/compact screenshots inspected.

`work/m17f1/live-teammate-check.json` records a successful actual Codex Research worker
on disposable synthetic evidence: approved UTC requirement, unresolved CSV/JSON question,
source citation and unchanged project. No paid Claude execution or hosted end-to-end provider build is claimed by that test.
Hosted profile acceptance is independently recorded above.

Local website copy and real screenshots are prepared with sample-data/rollout labels.
Nothing pushed or deployed. Public site stays waitlist-only.
