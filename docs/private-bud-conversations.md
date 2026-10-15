# Private Bud conversations and coworker DM discovery

October 14, 2026. Source implementation delivered; hosted acceptance is pending
the additive staging migration below. No public release gates changed.

## Experience

- A + beside DIRECT MESSAGES opens the existing coworker picker. It reuses the
  existing server start_direct_message operation, membership checks and unique
  human DM identity. Reopening the same coworker does not create another channel.
  Stale picker results cannot switch the user back into a different workspace.
- Clicking a Bud opens a private conversation. Configure in that view opens the
  existing editor; the Bud section's + still manages/creates Buds. No inference
  starts until the user sends a message, including with reduced motion enabled.
- Ordinary text addresses the selected Bud without an @mention. Configured name,
  sculpted avatar, personality instructions, provider and authorized connector
  reads reuse the existing QueryJob/runtime/connector path.
- Workspace context is OFF by default and resets after each explicit opt-in.
  Authorized connector reads are available as disclosed above the conversation.
  Included workspace evidence goes through existing membership/source/citation
  checks. Private history never enters shared channels, notifications, search,
  product memory or another user's context.
- These private replies provide answers and drafts. Code execution/build changes
  remain in the existing Build studio with approval controls; private chat does
  not silently run a background executable build or post into the open channel.
- Account-owned history survives reopening and is available through the same
  signed-in account's database access. UI reads the latest 100 messages; model
  history is bounded to 40 recent messages / 240 KB. Those limits are disclosed
  in the feed's accessibility description and tooltip.
- Plain text, emoji, multiline input, keyboard send, cancel, safe retries,
  skeleton loading and loading timeout recovery are supported. Attachments/voice
  remain in existing workspace chats; they are not exposed as dead controls here.
  New questions have an immediate local echo while persistence runs in background.

## Storage and boundaries

New public.bud_messages table is separate from ordinary chat. Authenticated users
get SELECT only under RLS: their own user_id plus current owner/admin/member access
to the Bud's workspace. Workspace owners/admins have no app-level exception to
read coworkers' private histories. Deleted Buds are hidden; removed members lose
access. Account or hard Bud deletion cascades to this history. Soft removal hides
history; it does not claim provider revocation or immediate physical deletion.
Operator/support data-deletion procedures still apply; direct history deletion
and older-message pagination are not added to this view.

Writes use append_bud_message only. A server-verified user is required; body limit
20,000 characters; 30 new messages per minute per user across Buds, serialized with
a user advisory lock. Message UUID retries are idempotent. One assistant response
per owned user question prevents duplicate replies and cross-user reply injection.
The role is derived from a verified parent, not an arbitrary supplied role field.
Assistant text is client-supplied output, not a server-authenticated action, billing
assertion, business fact or shared evidence. AI caps continue through the existing
managed runtime when configured; no free/unlimited inference path was introduced.

Logout/workspace/service changes dismiss private UI; cancellation suppresses late
answers. Context and connector access are rechecked before releasing an answer.
Recognizable credentials are blocked before private inference. No plaintext local
conversation file or QSettings history is introduced.

## Validation

Full desktop regression suite: **795 passed**. Final focused private-chat checks:
**9 passed**. Ruff and diff whitespace checks pass. Complete embedded PostgreSQL
migration/RLS suite passes, including this migration and the optional-meeting order.
One existing Python audioop deprecation warning remains, unrelated to this feature.

Focused desktop tests cover immediate echo, saved/reopened history, duplicate-safe
retry, failed-load skeleton recovery, logout cancellation, full reply persistence
with an isolated provider fixture, default no-workspace-context versus opt-in,
Bud-only retrieval, coworker DM creation/reopening, and reduced-motion interaction.
Real embedded PostgreSQL migration/RLS tests cover cross-member and outsider reads,
cross-user reply spoofing, direct-write denial, message limits, idempotency, one
reply per question, rate limits, removal and deleted Buds. These are real PostgreSQL
checks in a disposable database, not proof of a hosted deployment.

Visual inspection: light, charcoal dark and compact native Qt renderings under
work/bud-chat/{light,dark,compact}.png using clearly synthetic conversation data.
Live storage, a real provider reply in this new view, and second-account hosted
isolation remain required after the staging migration. Existing Instagram OAuth
acceptance does not substitute for this new conversation acceptance.

## Required owner action — staging only

In Supabase → **Aedrova Staging** (scvmvqlzcqhwrrsiahpj) → SQL Editor → New query,
run the contents of:

`/Users/ayanshvarma/Documents/Aedrova/supabase/migrations/202610140001_bud_conversations.sql`

Run only in Staging, not the original production project. Reply **success** or
paste the error without secrets. This installs private history, access rules and
the two RPCs. It blocks live saved Bud conversation validation. No Render change,
new credential, paid plan, production migration or installer release is needed
for this step. Afterward, restart the updated source staging app, verify a private
reply/reopen under the signed-in test account, then verify the second account cannot
read it. Production installation remains a separate release gate.

## Hosted acceptance progress after owner migration confirmation

The owner reported success. Restarted the updated source staging app and signed
into the original first test account through normal Google OAuth. In the existing
synthetic Beta isolation 1 eb8958 workspace, clicking the Marketing Bud opened
private history with workspace context unchecked. A non-sensitive greeting request
saved successfully and reappeared on closing/reopening the private view. The team
channel did not receive it. Retry reused the saved question rather than creating
another question. The independent first user-JWT probe also passed direct table and
RPC reads of its own history and repeated-UUID idempotency against real staging.
Evidence: ignored work/bud-chat/hosted-acceptance.json and hosted-private-history.png.

The first included-AI call timed out while the free staging host woke. Retrying
afterward returned the explicit server denial: **Included AI access is not
configured yet.** No real model answer was generated or saved, and no local
credential/runtime fallback bypassed the gateway. Completing the answer test needs
staging gateway/model/key activation with server spending limits. The existing
speech-only key deployment approval does not authorize a new generation-key
transmission to Render. Proposed next approval: use the existing OpenAI key in
Render aedrova-beta-staging only, deploy matching capped inference configuration,
with a $1/month staging accounting budget and no production/checkout activation.
Provider/model rate validation and actual enforcement must precede any inference.

The native + button correctly reports that this test workspace needs an invited
teammate; it has no second member, so live human DM creation/reopening is not claimed.
That flow's automated desktop and PostgreSQL checks remain passed.

The hosted outsider permission probe authenticated its first session and opened
Safari's second Google account chooser. Owner must select the SECOND registered
staging test account (different from the original account) to finish foreign history
read/write/reply rejection checks. No new workspace membership is being granted.
Sessions stay only in memory; the bounded sign-in wait expires after 15 minutes.
Same-workspace coworker isolation remains covered by the local PostgreSQL suite;
it is not certified by an outsider check. The overall hosted acceptance gate is open.
