# M15 — source-backed product memory

M15 implementation and hosted Product Memory acceptance completed October 6, 2026.
The owner applied both migrations. Two normal Google accounts passed the live persistence,
lifecycle, freshness and privacy checks. Existing M14 production setup remains deferred;
no successful paid-provider build or public release is claimed by this milestone.

## What is built

Open **Product memory** beside the conversation tabs in a signed-in shared workspace.
Record goals, requirements, constraints, decisions and questions with linked evidence.
Find accessible messages, or use Build → Workspace context → Add to product memory for
chat, attachment and consented meeting sources. No provider call occurs in these views.

New entries are proposals. Approval is explicit; unresolved conflicts and open questions
cannot become approved requirements. Select another same-channel entry to flag a conflict,
then resolve it before approval. Edit/retire entries, or approve a new replacement that
atomically marks the prior entry superseded. Versioned history records the actor/time.
Approval records a teammate's decision, not proof of unanimous agreement. Semantic conflict
extraction is not automatic; the agent is instructed to ask when evidence conflicts.

Memory lives in Supabase with RLS and server-authorized writes. Sources are resolved
against current message/file/transcript records on reads; deleted, unsent or AI-withdrawn
sources purge derived entries/history. Source edits mark entries stale until reviewed.
Workspace membership and channel visibility apply to current entries and history.
Cross-channel merges are not allowed: use separate entries to preserve private boundaries.

A build's workspace-context JSONL contains a pinned SHA-256 memory snapshot, entry versions
and resolved source citations. Ranked retrieval recognizes `memory:<id>` references.
Only approved fresh entries are current; pending questions/proposals/conflicts remain
clearly identified. Retired/superseded entries are omitted from build memory but remain
available in the UI. Build context is checked twice during collection and again before
execution, and active/saved build checks compare memory at most once per 15 seconds using
the existing dashboard refresh queue. Changed/unverifiable memory stops the run and blocks
review/apply until a fresh build. The build status tooltip exposes the pinned revision.
This does not undo already executed local sandbox actions or recall provider input.

Use existing PostgreSQL full-text indexes for source and memory search; no embedding/model
calls or passive semantic extraction are added. Memory revisions invalidate existing
channel context counters, so indexes are generated from fresh authorized snapshots instead
of retaining a shared stale cache. Supported small text files reuse the existing reader;
other files/designs supply provenance metadata, not automatic visual interpretation.

Current limits: up to 200 matched entries in the UI, 100 history revisions per read,
16 same-channel citations per entry, 160 title characters and 8,000 detail characters.
Builds refuse truncated active memory rather than silently omitting requirements. Retire
obsolete active entries if the inventory reaches this limit. Freshness/membership checks
are not an exhaustive semantic understanding of every conversation in the workspace.

## Website

Prepared local preview-labelled Product memory section with actual light/dark desktop
captures using synthetic sample data. No push, deployment or public feature activation.
The public website remains waitlist-only. Local website wording reflects validated
hosted memory while clearly retaining the public rollout gate.

## Owner actions and hosted acceptance

**No further owner action is required for M15.** The owner confirmed both SQL migrations:
`202610060001_product_memory.sql` and `202610060002_memory_conflict_response.sql`.
The additive conflict patch returns PT409 instead of retryable SQLSTATE 40001 for explicit
stale edits, preserving existing tables/data and all authorization/source/version checks.

`python scripts/check_hosted_memory.py` completed with normal personal/school Google
sign-ins, credentials only in memory and synthetic fixtures in a dedicated test workspace.
Live checks passed: proposal persistence; explicit approval/history; stale-version denial;
outsider denial; shared member visibility; private entry/source/history isolation; denied
private/direct-table writes; changed source freshness and stale approval denial; reviewed
source updates; atomic replacement; retirement omitted from active context; source unsend
purging entries/history; removed-member denial. Report:
`work/m15/hosted-memory-check.json`. The second account was removed from the test workspace.
Synthetic fixtures from interrupted attempts remain labelled in separate test workspaces.
The actual desktop successfully loaded the hosted Product Memory inventory.

Meeting transcripts and speech review remain optional. When meeting context is installed
later, use the updated `202610030001_meeting_context.sql`; it automatically attaches memory
privacy cleanup. Without speech review, only participant-written meeting text can be
memory evidence. Hosted meeting-source acceptance and an actual paid-provider build with
memory are deferred external gates at M14/M18, not claimed from local tests. Local SQL tests
cover meeting-text correction and AI withdrawal, and local build tests cover snapshot
invalidation/cancellation. M14 stays deferred. M16 requires explicit owner permission.

## Validation

Hosted conflict fix: **105 focused app tests passed**, all PostgreSQL/RLS suites
passed (including upgrading the original conflict function and the optional-meeting
installation path), scoped Ruff/diff checks passed. The preview was rebuilt and its
signature/packaged smoke verified. Hosted stale-edit rejection now passes with the applied additive SQL.

Missing-meeting-schema repair: the complete PostgreSQL suite passes, plus a separate
fresh-database installation without transcript tables, chat-backed save/read/withdrawal,
missing-meeting-source denial, late meeting installation/privacy cleanup, and exclusion
of unreviewed provider speech without the speech-review schema. Scoped Ruff and diff
whitespace checks pass. Hosted activation and lifecycle/privacy checks now pass.

Full desktop suite: **572 passed**. After final UI/source/guide updates, **104 focused
regressions passed**. Website public-page suite: **32 passed**. All existing and new
PostgreSQL migration/RLS tests passed in PGlite, including rate-limit exhaustion.
Scoped Ruff, diff whitespace, Apple Development bundle signature and packaged launch
smoke checks passed; rebuilt app reopened to sign-in.

Python UI/context/queue regression tests, actual PostgreSQL migration/RLS tests in PGlite,
light/dark captures, compact UI checks, website page tests, scoped lint and rebuilt bundle
smoke/signature checks. See task report for final counts. SQL tests cover privacy, edit
conflicts, supersession, source deletion, attachment integrity changes, corrected meeting
text, AI withdrawal, rate-limited writes and direct-table/anonymous write denial. These
local tests do not replace hosted Supabase or real provider acceptance.
