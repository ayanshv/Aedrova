# Repair roadmap Step 4 — messaging and direct messages

October 15, 2026. Owner approved Step 4; personal interventions collected at the
end. Current desktop source; production and installer promotion remain separate.

## Delivered

- Human conversation rows support drag selection, double-click word selection,
  Shift selection, select-all and copy. Rounded highlights follow individual text
  lines in light/dark themes. Return, header/reply-area clicks and context menus
  retain thread access; body clicks select text. Links, reactions, attachments
  and message actions remain available.
- Main-agent and Bud response labels support mouse/keyboard selection, keyboard
  copy and native text context menus. Plain-text rendering remains in place;
  messages cannot execute HTML or load remote document resources.
- Acceptance compares actual serialized mention tokens and the submitted document
  revision. Sending from the main composer never clears the thread composer, or
  vice versa. Rejected AI requests retain drafts. Accepted private Bud messages
  clear immediately and retry the same pending message ID on failure.
- Delivery receipts cannot erase a new draft with identical text. Failed chat
  sends restore the visible draft; successful retries clear only the untouched
  restored revision. Edits made while work completes are preserved.
- Direct Messages + opens one searchable People/Buds picker. Stable user/Bud IDs
  prevent duplicate-name collisions. Buds use configured artwork and remain
  available without human coworkers. Session/workspace changes during the picker
  invalidate selection. Human DM server idempotency remains. Reopening the same
  Bud conversation focuses its dialog instead of interrupting a pending reply.

## Verification

Final desktop suite: **846 passed**. Ruff and diff checks passed. Actual Qt input
tests cover tokenized main/thread sends, rejection, edited/retyped revisions,
mouse drag, multiline/Unicode and keyboard copy, agent labels, picker search,
empty/duplicate-name states, Bud-only workspaces and delivery/retry races.
Light/dark picker and selection previews inspected in ignored work/messaging-step-4.

All migration/access-rule scripts passed in disposable embedded PostgreSQL,
including human DM isolation, own/member/outsider private Bud histories, removed
membership, deleted Buds, idempotency and rate limits. No hosted migration ran.

Fresh native Google PKCE sessions on real staging verified an owner's saved
question, repeated-ID idempotency, actual streamed OpenAI Bud reply (10 updates,
zero tool activity), assistant save/reopen and a distinct account's denied direct
history-table read, history RPC, writes and spoofed replies. The second account
used its existing Aedrova business Google session. No membership/access rules were
expanded. Incremental usage was 1,992 micro-USD ($0.001992), with zero outstanding
reservations. Temporary sessions were signed out; login URL file/tab removed.
Only synthetic test messages were used. The first cold-service attempt was
incomplete; the next test after health returned HTTP 200 passed. No local provider
fallback or credential changes. Private history stays outside shared channels.

This is not a fresh live two-human conversation/notification test or signed
installer acceptance. Same-workspace member isolation is covered by PostgreSQL;
the live second-account check establishes foreign-account denial, not every
membership lifecycle. Those broader checks remain release acceptance items.

## Final owner actions

None needed now. No SQL, keys, sign-in, purchase or account change requested.
Production promotion remains Step 10 after release gates; this patch does not
update installed app binaries. Obtain approval before Step 5 single-action
connector UX. Live provider certification is Step 6.
