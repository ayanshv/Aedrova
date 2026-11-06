# Shared context between Aedrova and Buds

Implemented in local source November 1, 2026. The owner confirmed running the staging migration on November 3. Live cross-agent
acceptance remains pending; the SQL action should not be repeated.

## Behavior

Successful Aedrova and Bud responses in workspace channels are saved as attributed,
untrusted shared work, after their existing authorization/citation checks. Saving
runs in the request queue after the local reply appears. Stable request IDs make
network retries idempotent. A failed save leaves the reply visible and explicitly
reports that shared context did not sync. Existing local-only replies are not
silently uploaded or backfilled.

Workspace-aware queries and builds gather up to 30 recent authorized shared-work
records, plus up to 10 existing shared build reviews and their delivery receipts.
These enter the same searchable evidence index as chat and product memory. Source
references use `agent-work:<id>` and `build-review:<id>`. This is bounded selected
evidence, not an exhaustive permanent memory of every agent action.

Thinking reports “Looking for shared Aedrova and Bud work…”, then “Consulting shared
work from <names>…” only after the records were actually read. Existing shared
builds report “Reading shared build reviews and delivery receipts…”. These are
retrieval status messages, not simulated agent-to-agent conversations. Literal
main-agent greetings keep their fast, tool-free path.

The main agent and Buds retain independent personalities and permissions. Prior
agent text is not a verified accomplishment, human decision, instruction, or tool
approval. Shared build receipts describe recorded delivery state; they do not grant
execution or publication permission. Models receive explicit guidance to attribute
prior work, cite it, verify evidence, and surface conflicts.

## Boundaries

- Workspace membership and channel access are enforced by database RLS.
- Records retain original source channel IDs. A reader must still be authorized for
  every original channel, including private channels; derivation cannot broaden
  access. Reads are fresh, without a shared authorization cache.
- Private Bud DM history, direct/group DMs, raw provider tokens and tool grants are
  excluded. A private Bud conversation may read permitted workspace evidence only
  through its existing per-reply opt-in; it does not publish its answer to this log.
- Local build files remain private. Only build reviews already explicitly shared
  through the existing review system enter shared retrieval.
- Chat answers recheck shared records and source access after inference; changed or
  revoked records withhold the result. Builds use the existing fresh context and
  approved-plan comparison between phases, with existing review/apply boundaries.
- Writes validate size, source scope, credentials, idempotent identity and a
  30/minute per-user server budget. No direct authenticated table writes are granted.
- Workspace/channel/account deletion cascades stored work. Removing access to an
  original source immediately hides derived work through RLS.

## Required staging activation

Owner: Supabase > **Aedrova Staging** (project `scvmvqlzcqhwrrsiahpj`) > SQL Editor >
New query. Run only:
`/Users/ayanshvarma/Documents/Aedrova/supabase/migrations/202611010001_shared_agent_work.sql`.
Do not run it in production. This adds the restricted shared-work table, read policy
and idempotent write function. No payment or provider key is needed.

Then Command-Q Aedrova and reopen
`/Users/ayanshvarma/Documents/Aedrova/work/staging/Open Latest Aedrova Staging.command`.
A live check should ask a Bud for a channel proposal, then ask Aedrova (and a second
Bud) to use that Bud's findings, and verify named Thinking status and citations.
Private-source checks must use a second account without that private-channel access.
Until migration and live acceptance, shared context remains pending activation.

## Verification

186 focused tests passed for context retrieval, Bud conversations, response
latency/routing, optimistic publication, identity, and chat integration. Disposable
PostgreSQL migration/RLS checks passed, including idempotency, forbidden direct
writes, oversized payloads, private-derived evidence, direct-message exclusion,
outsiders and revoked membership. Ruff and whitespace checks passed. Evidence is
saved in work/shared-agent-context/{acceptance,database}.log. These are local checks;
the staging migration and live cross-agent test remain open.

November 3 update: owner reports the staging migration ran and was saved. The
manual database action is complete by owner report. Restart and live acceptance
remain to be verified.
