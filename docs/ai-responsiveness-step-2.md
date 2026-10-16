# Step 2 — AI responsiveness and availability

October 15, 2026. Implementation and local acceptance delivered; hosted staging
activation is still pending. This does not close Step 2's live acceptance gate.
Owner actions are collected at the end.

## What changed

- Main-agent greetings/questions route to read-only answers even with zero Buds;
  explicit build requests retain the existing build queue and approvals.
- General conversation skips workspace history, channel enumeration, connector
  selection and external reads. Fresh user-scoped membership is checked before
  and after inference. Source questions/follow-ups keep the evidence path.
- Included answers and connector selection use the existing metered gateway
  directly instead of launching the coding CLI. No tools are supplied to the
  reply request. Actual builds/planning retain their existing execution runtime.
- General answers stream into one message in main chat and private Bud chat.
  Source-backed answers remain withheld until citations, connector versions and
  channel permissions are rechecked. Private history remains account-owned;
  workspace context stays opt-in. Bud identity/personality are retained.
- Cancel closes an active reply stream even before its first text arrives;
  interrupted/failed/incomplete replies are not saved as completed private answers.
- Run authorization allows up to 90 seconds for the sleeping staging host;
  timeout, disabled setup, provider rejection and budget errors have distinct
  messages. There is no personal-account fallback, silent retry or shared key
  in the desktop.
- Requests retain existing plan output/concurrency/request limits, server cost
  reservations, actual usage reconciliation, owner-shared Free capacity and caps.
  General messages containing recognizable credentials are rejected before inference.

## Verified evidence

- Read-only model/key checks succeeded for the existing configured OpenAI and
  Anthropic credentials. These checks alone do not prove inference availability.
- Real OpenAI request through a disposable loopback copy of the existing gateway:
  first text 2.43 seconds, completion 2.64 seconds. No CLI or tool calls.
- Actual desktop QueryJob paths through that gateway and real OpenAI: main reply
  0.84 seconds with 8 text updates; addressed Bud 1.85 seconds with 23 updates.
  These two requests settled 1,717 micro-USD ($0.001717), with zero reservations
  remaining. Timings are individual observations, not a latency guarantee.
- This test used a disposable SQLite ledger and synthetic identity/Bud inventory.
  It proves the real model + gateway + desktop worker integration, not hosted
  Supabase sessions, private-history isolation or production readiness.
- Anthropic inference rejected the existing key with HTTP 400 and a credit-balance
  error. No private provider diagnostic or key was printed. Do not report Claude
  as available until its provider billing is funded and inference is retested.
- Live staging /health returned 200 with managed_ai_enabled=false and
  checkout_enabled=false. Render confirms the deployed staging revision remains
  e375bdc. Its free-host notice warns waking can take 50 seconds or more.
  Routing fixes cannot eliminate that infrastructure cold-start delay.
- Desktop full suite: 824 passed before the final lightweight-inventory change;
  the final relevant suite is recorded in the milestone entry. Backend gateway,
  budgeting, provider-setup and shared-space suites: 64 passed.
- Ruff and diff checks passed. No database migration is required by these changes.

## Prepared staging configuration

Website repository: deploy/staging-ai.env.example. Validated by loading the real
staging configuration privately with the proposed overlay, without connecting to
its database or uploading secrets. It enables only the funded OpenAI provider,
keeps the existing Free policy (including shared owner/workspace allowance), and
sets company/Free-pool accounting ceilings to 1,000,000 micro-USD per month ($1).
These ceilings cover the staging ledger, including other metered usage; they are
not provider-side billing guarantees. Checkout, releases and development funding
stay off; production and existing connector/database/encryption settings stay intact.
No hosting upgrade, new subscription or production deployment is included.

Rollback: restore the prior staging gateway/model/free/budget settings and redeploy
that service. Do not rotate its database or encryption key, delete usage history,
reset spent allowance or enable local fallback. Retain a snapshot of changed
non-secret settings before applying the overlay.

## Remaining live acceptance gate

After staging activation, verify a freshly signed-in owner can activate its
existing Free plan (no paid checkout), main-agent and Bud greetings stream real
replies, source-backed answers retain permission checks, members share the same
allowance, denied/quota/cancel paths do not start another provider, and all requests
settle. Repeat using the current source preview; an older installed app will not
contain this code until rebuilt. Foreign-account private-history live acceptance
is still a separate open gate from the preceding milestone.

## Owner actions — consolidated handoff

1. **Required to finish hosted OpenAI acceptance:** approve copying the existing
   local OpenAI key into Render → aedrova-beta-staging → Environment as
   AEDROVA_OPENAI_KEY, applying the reviewed deploy/staging-ai.env.example settings,
   and saving/deploying that staging service. This enables metered inference with
   the $1/month staging accounting ceiling. No key belongs in chat. The previous
   speech-only key approval did not cover this new inference purpose. No secret
   was uploaded or inference enabled in Render during this implementation.
2. **When the prepared test needs it:** sign into the current staging preview using
   its fresh login screen. If the chosen workspace has no allowance, its owner/admin
   selects Start Free at the staging /account page; no card/payment is required.
   I will first reuse an existing valid session where possible. Hosted end-to-end
   acceptance remains blocked until valid user authentication and allowance exist.
3. **Only if Claude must also be enabled now:** Anthropic Console → Billing → add
   provider credit privately. This is a payment and must be performed by you.
   After funding, separately enable its server key/model configuration in staging
   and repeat the real metered reply tests. OpenAI work can proceed independently.

No Apple membership, Supabase SQL, paid hosting upgrade or Stripe bank setup is
needed for the OpenAI staging activation above. Production promotion and packaging
remain later roadmap steps. Do not start Step 3 before the owner approves it.

References: official OpenAI streaming guidance
https://developers.openai.com/api/docs/guides/streaming-responses and the configured
GPT-5.3-Codex model documentation
https://developers.openai.com/api/docs/models/gpt-5.3-codex (low reasoning supported).
