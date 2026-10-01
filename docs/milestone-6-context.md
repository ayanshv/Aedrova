# Milestone 6 — Project context

Implemented for internal alpha. The owner applied the migration; live search, decision confirmation/retirement, citation lookup and Codex planning passed on 2026-09-29. See `milestone-6-hosted-check.md`. Live two-account revocation remains unverified; local access-control tests pass.

## Setup reference — already completed for this project

Do not rerun the migration on this configured project. These steps are retained for fresh setups.

1. Open the existing Aedrova project in **Supabase → SQL Editor → New query**.
2. Paste the entire `supabase/migrations/202609290001_context_decisions.sql` file and click **Run**
   once. Earlier migrations must already be applied. This adds decision records, RLS-protected
   confirmation/retirement and context revision counters. It does not change your OAuth setup.
3. Save unsent drafts, quit the older app, then open
   `/Users/ayanshvarma/Documents/Aedrova/dist/Aedrova.app` and sign in.
4. Open **Builds → Start a build → Workspace context & decisions**. Search for a harmless
   requirement you have already discussed. Select its message, click **Confirm decision**, and
   check that its status changes. Use **Retire decision** when it no longer applies.
5. Create a small Codex plan referencing that requirement. Check the source citation against
   the context browser: you can paste `message:<id>` into search to find the exact message.
6. With a second account, verify that a private-channel requirement/decision is absent unless
   that account is allowed to read the channel. Revoke access and verify the view is cleared.

The SQL is required for hosted context search and builds in this version. No new keys, OAuth
changes, vector service, or provider payment is required for context search. Current Codex
execution uses your existing local login. Claude model execution still needs its alpha API
setup; that is optional for this milestone's context acceptance and is not implemented by this
migration. The planned managed provider billing remains milestone 9.

## What changed

- Private, provider-free source search in the existing build window, styled for dark and light.
- A fresh in-memory SQLite FTS5 index for each authorized corpus. No shared persistent index or
  embedding service. BM25 lexical ranking, English word stemming and bounded thread expansion
  supply relevant leads; the full permitted corpus remains available to the agent.
- Explicit member-confirmed decisions with source body and recorder. Retirement is supported.
  An edited source makes its earlier confirmation stale. Confirmation records one member's
  judgment, not unanimous agreement. Ordinary chat never becomes a decision automatically.
- Agent prompts include ranked evidence, the decision inventory, channel/thread/source metadata
  and content fingerprints. Plans must contain existing source citations before approval.
  Citation checks establish that a source exists, not that the model interpreted it correctly.
- Scoped channel keyset paging and final access checks. Revision counters detect message,
  attachment, decision and channel metadata changes during paged gathering. Mixed snapshots
  fail and ask for refresh. Before implementation the entire corpus is gathered again;
  changed evidence invalidates the approved plan.
- Source deletion cascades to its decision record. A new index is built only from fresh permitted
  evidence. Closing/revoking the browser clears its index; detected access loss cancels builds.

## Evidence

- 190 full-suite Python tests passed. All 24 context tests passed again after the final
  browser cleanup change.
- All embedded PostgreSQL migration and RLS suites passed, including decision provenance,
  retirement, stale confirmation rejection, private-source isolation, revocation, deletion,
  revision changes and denied anonymous access.
- A real authenticated Codex planning run read a synthetic confirmed requirement, returned its
  valid `message:acceptance-1` citation and left project files untouched. The new code path was
  tested through the actual Create plan button. No private hosted messages were used.
- The provider-free Qt journey exercised search, confirmation, retirement and revocation. Dark
  and light screenshots were inspected. The rebuilt app passed its packaged launch, ad-hoc signature verification and baseline
  release secret-pattern scan. Ad-hoc signing is not notarization or release approval.

## Limits and next gate

Retrieval is lexical, not semantic embedding search. The small deterministic evaluation corpus
covers six relevance queries, thread contradictions, no-match behavior and isolation; it does
not establish production retrieval quality across languages or large real teams. The source
browser shows up to 200 matches. Context limits remain 8 MiB, 256 KiB per text attachment and
10,000 channels. Unsupported attachments retain metadata. No audio/video transcription yet.

The browser is a labeled snapshot; refresh it to see changes. Detection cannot retract evidence
already sent to a model. No durable audit history, semantic conflict solver or permanent agent
memory is claimed. An approved build may still need human review of source interpretation.

Milestone 7, requiring owner approval: first improve the account menu/logout, working settings
and dropdown/menu consistency, then chat-to-IDE builds, project bindings, code review/diffs,
safe application of changes, GitHub connection and approved push/PR delivery. Later owner steps
will include selecting a project/IDE and authorizing repository access. None is required now.
