## October 24 — signed-in native chat follow-up; step 2 not yet certified

Owner completed Google sign-in. Dashboard dismissal, two native chronological greeting
exchanges, prompt/answer retention, empty composer/no stale Thinking row, DM picker
opening, loaded Bud capacity and Finish later returning to chat passed live. Existing
TikTok Bud still needs authorization; fresh-account tour, full connector OAuth lifecycle
and other open acceptance gates remain. Public health probe timed out; meeting health
503. Paid configuration remains deferred, with no new owner payment action now.
Prelaunch #1 is still OPEN; do not start #2 as though acceptance is complete.
See [native evidence and remaining boundaries](staging-chat-repairs-2026-10-24.md).

## October 24 — chronological chat, Markdown and connected-project replies

Implemented separate chronological conversational replies, normalized sent timestamps,
request-before-response causality and originating thread/channel placement. Safe Markdown
now renders agent/Bud text; connected-project questions receive bounded, secret-filtered,
read-only local evidence with checked citations. General greetings avoid project/connector
retrieval. Exact managed model identity is supplied truthfully. Completed build answers
are retained before the next request clears activity. Logout clears private session caches.
Central-agent replies remain session-only; durable/cross-device assistant history is not
claimed. User prompts retain existing shared RPC persistence.

Final desktop suite: 978 passed; backend payment-free selection: 101 passed.
Ruff/diff/secret-pattern checks pass; latest source staging is open at Google sign-in.
Full native onboarding and remaining live connector certification are still blocked on
that sign-in/consent, and funded AI/meeting/activation gates remain deferred. Stage 1 is
OPEN, not launch-approved. Consolidated owner action and verification:
[Chat repairs and staging acceptance](staging-chat-repairs-2026-10-24.md).

## October 24 — all owner-paid configuration deferred to final launch gates

Owner requires every action that would charge them to be consolidated at the final
paid launch gates. Complete payment-free preparation/testing first; never submit
payments on their behalf. This includes hosting/meeting guard upgrades, provider
funding, automatic replenishment and any other charge-triggering setup. No payment
action is required now. Existing approved resources may be used within their limits.
Actual Claude coding, reliable meetings and other paid-dependent acceptance remain
OPEN until funded and tested, before launch. This changes sequencing, not closure
criteria, and does not authorize production promotion. Exact policy and order:
[Final paid launch gates](final-paid-launch-gates.md).

## October 24 — approved Claude staging activation; API funding gate remains

Owner approved existing Anthropic key transfer to Render staging and combined
config/models.beta.json. Saved exactly those private settings; both providers now
appear in authenticated preflight. Model metadata validates the configured Sonnet
model. Fixed a real gateway TypeError on nested tool-schema type properties and
deployed ebb36c6 only to existing Free staging. Current managed Claude suppresses
unreviewed CLI beta capabilities and automatic non-streaming fallback while retaining
sandbox/tool/cost gates. 627 backend / 970 desktop tests pass; final 34 managed checks pass.

Actual Claude coding is **NOT VERIFIED**: Anthropic's no-generation count endpoint
rejects with a credit-balance error (HTTP 400); this is an API-account funding gate,
not a need for a new key. Owner must personally review/add API credits at
platform.claude.com/settings/billing for the key's organization, and may defer this
to final paid setup. No payment, upgrade, refill, allowance or production change.
Exact evidence/handoff: [Claude staging acceptance](claude-staging-acceptance-2026-10-24.md).
Next: finish the live managed Claude task after funding, then new-workspace free AI
activation and other existing Stage 1 checks. Overall Stage 1 remains OPEN.

## October 24 — mention routing and sent-prompt retention fixed

Owner explicitly authorized these fixes before the remaining Stage 1 prerequisites.
Agent mentions now match anywhere with proper name/email boundaries; text before
and after the mention is retained. Addressed Bud identity remains selected and a
central-agent request mentioning a Bud keeps the central recipient. Accepted mention
prompts now use the normal optimistic channel/thread outbox and backend message RPC;
thinking/result updates do not replace the user message. Receipts, refresh and a
second prompt preserve history; rejected requests keep drafts. Slash /build commands
retain their private Build Room behavior. No backend migration or provider change.

Focused regression group: 135 passed, followed by 14 mention-specific checks including
private slash behavior. Full desktop suite result is recorded in staging acceptance.
Reloaded source staging with the fixes; Google requested the previous account's
passkey, so native live sign-in/listening requires the owner. The login screen is
ready, without a stuck pending authentication. No credentials were changed.
Remaining Stage 1 provider/meeting/activation/connector gates are unchanged; no launch
or Stage 2 completion is implied.

## October 24 — Stage 1 live follow-up; gate remains open

Full desktop suite: **954 passed**. Latest backend suite: **621 passed**; the
focused build/retrieval group also passed 73 checks after planning wording was
clarified. Actual two-account staging acceptance verified Free Bud capacity,
simultaneous last-slot enforcement, deletion restoring capacity, Auto save/readback,
private verified uploads/cancellation, Bud history separation and owner/member
Online/Away/Do not disturb visibility. Temporary hosted fixtures were cleaned up.

Fixed Stripe external-test install URL validation without relaxing its HTTPS/host/
path restrictions; restored previously approved staging Stripe settings. Backend
candidate 1b155eb is deployed only on aedrova-beta-staging from
codex/stage1-acceptance. Production and checkout remain unchanged. Large CLI harnesses
now use bounded official provider token counts when the conservative byte estimate
exceeds context capacity; limits/reservations and failure closure remain enforced.
50/51 hosted boundary checks pass; meeting health is still 503. Native GitHub
confirmation and Bud Finish later → highlight tour resume were observed; the full
hardware/two-device tour is not certified.

Latest actual Auto → Codex planning/implementation/tests/review/apply passed in a
disposable project; originals stayed unchanged until guarded apply and fixtures
were cleaned up. Stage 1 is **OPEN** pending both configured providers,
new-workspace allowance activation, full connector live acceptance, and meeting
infrastructure/physical checks. Existing Anthropic key validates against provider
metadata but is not deployed to staging; obtain specific approval for that transfer.
Search remains unconfigured. Owner must personally approve/pay any hosting charge;
never submit it for them. Consolidated exact handoff and evidence are in
[staging acceptance](staging-acceptance-2026-10-24.md).

Owner explicitly queued mention-anywhere parsing and sent-prompt preservation
**after Stage 1 completes**. Saved those requirements; do not silently reorder them
or represent either as fixed before implementation and tests.

## October 24 — owner reports Bud quota migration installed

Owner reports `202610240001_bud_plan_limits.sql` ran in staging. Record the manual
installation as reported complete; authenticated RPC readback, paid-tier boundaries
and concurrent creation still need hosted acceptance. No repeat SQL action requested.
Restart the source staging launcher to load the desktop counter. Website capacity
copy remains a local source change pending publication. Prelaunch gate 1 remains
PARTIAL / OPEN; no production migration, deployment or launch approval is implied.

## October 24 — approved Bud limits implemented in source

Owner approved Free 1 / Pro 5 / Team 15 / Enterprise explicitly contracted capacity,
shared per subscription including subspaces. New migration
`202610240001_bud_plan_limits.sql` reads verified private billing, replaces legacy
universal 12-cap and serializes creation with a root-scoped transaction lock.
Saved Buds survive downgrades; edits/deletion remain allowed and new creation is
blocked at/above capacity. Desktop shows a quiet count/tier in setup; website plan
cards list capacities. AI allowances, prices and subscriptions are unchanged.

80 focused desktop tests and the embedded PostgreSQL migration/access suites passed;
35 website public-page tests passed. Hosted concurrent-creator and live plan-change
acceptance are still pending. Website source updated locally, not publicly deployed.
Required owner action: Supabase → Aedrova Staging → SQL Editor → New query → run
`supabase/migrations/202610240001_bud_plan_limits.sql` only in Staging, then restart
the staging app with its launcher. Until installation hosted enforcement retains
the old cap. Production installation is a separate release step. No payment,
credential, production data or deployment change was performed. Step 1 stays open.

## October 24 — conversation People tab and proposed Bud capacity

Added People beside Conversation/Project/Work/Files. It uses the current channel's
authorized people inventory, refreshes while visible and opens teammate profiles.
Online/Away/Do not disturb/Offline have green/amber/red/hollow indicators plus
readable labels; previous-channel responses are invalidated when switching scope,
and sign-out clears the embedded list. Local changes require restarting staging.

Owner validation pending: Free 1, Pro 5, Team 15 Buds per workspace, Enterprise an
explicit contracted capacity. See [proposal](bud-plan-limits-proposal.md). This
does not change entitlements or enforce quotas yet. Bud counts never multiply AI
usage allowance. No migration, hosted deployment, subscription or payment change.

## October 24 — teammate availability verification

Online, Away, Do not disturb and automatic Offline are shown in Workspace tools →
People & presence and individual profiles. Fixed stale Do not disturb overriding
a newly selected Online status; confirmed saves update the local personal cache.
Idle (five minutes), minimized and hidden windows report Away while preserving
manual Away/Do not disturb intent. Unchanged presence uses heartbeat without
rewriting custom status. Server presence expires after 90 seconds without a heartbeat.
36 focused desktop tests passed. Embedded PostgreSQL migration/access suites passed,
including owner reading teammate Away/Do not disturb, teammate reading owner Online,
offline expiry/recovery, inability to edit someone else's status and outsider denial.
These are local automated checks, not a fresh two-device hosted acceptance run.
No migration, credential or owner setup is required; restart staging via
`uv run python scripts/run_staging.py --config work/staging/public-config.json`
from the project folder to load the source changes. Launch step 1 stays open.

## October 24 — responsive navigation and focused workspace settings

Owner requested rounded profile artwork, immediate DM selection, focused channel
creation and simplified settings. Local source now uses session-scoped cached
pickers/results, background transport without full-page navigation locks, deferred
settings saves with session/logout guards, and five focused settings sections.
See [UI audit and evidence](ui-responsiveness-2026-10-24.md). Full suite: 933 passed
before final focused refinements. Native live recheck requires unlocking the Mac
and restarting staging; no production deployment or new SQL was performed.
Prelaunch step 1 remains PARTIAL / OPEN with the same provider/meeting blockers.

## October 24 — prelaunch step 1: staging acceptance

Owner approved starting staging acceptance. **PARTIAL / OPEN**, not release approval.
Fresh app/backend suites: 924 / 598 passing tests. Hosted anonymous boundaries,
two-account file/Bud privacy and one bounded live Codex reply passed. Meeting health
is 503; Stripe OAuth and managed Search are unavailable in the inspected catalog.
See [current evidence and consolidated owner dependencies](staging-acceptance-2026-10-24.md).
The database runner now includes the Auto preference migration and permission tests.
No production, hosting purchase, payment setup or new provider grant was performed.
Do not mark this gate complete or start the next phase without resolving applicable
acceptance requirements and obtaining owner approval.

## October 7 — M17G: AI economics and sustainable plan allowances

**Status: planned; implementation requires owner approval.** Run after the builder,
AI teammates, Dots and planned background workflows are implemented, before remaining
M14 production billing/provider activation and M18 launch. Updated remaining order:
M17F → M17 → M17A–M17E → M17G → remaining M14 → M18 → deployed-codebase walkthrough.

Objective: measure realistic team workloads and establish useful, sustainable included
AI access before finalizing public plan promises. Current configured baselines are
$49/month with $10 of provider usage (20.4% of gross plan revenue at full utilization)
and $10/week with $1 (10%). These are capped budget scenarios, not measured average
customer costs, profit margins or unlimited-build commitments.

Deliverables and acceptance:
- Benchmark representative small, medium and large coding tasks, context gathering,
  teammate assignments, Dots reports and background work. Record actual input/output/
  cached/reasoning usage, retries, failures, task outcomes and cost; measure what useful
  work each allowance buys. Clearly separate measured data from extrapolation.
- Meter every paid model request against one shared workspace allowance, including
  builders, mini teammates and background work. Audit paths for unmetered spend.
  Attribute costs to workspace, task, provider and model without logging secrets or
  private prompt contents. Account separately for transcription and other paid tools.
- Validate atomic reservations, concurrent users, account/workspace isolation,
  cancellation, uncertain provider charges, renewals and exhausted allowances. Stop
  before further billable work when funds are insufficient; no automatic overages,
  silent refill or fallback to an unmetered provider. Reconcile usage with provider
  billing and test explicit credit purchases through Stripe test mode.
- Produce measured low/typical/heavy usage scenarios and per-plan contribution after
  API usage, payment fees, hosting, meetings and storage. Include capacity/rate-limit
  behavior and sensitivity to provider price/model changes. Do not treat API budget
  as total operating cost or turn the tiny local proof build into an average estimate.
- Recommend final allowances, pricing/top-up margins, background-work cadence and
  economical model routing based on results. Present trade-offs and obtain owner
  approval before changing prices, public allowances or activating real checkout.
  Publish clear usage/remaining-budget and pause/resume states with useful next actions.

### M17G / M14B — automatic provider funding from revenue

**Planned, not activated.** Owner requested automatic API payments funded by Aedrova
subscription revenue. Build the accounting and guardrails in M17G; configure real
payment methods and provider auto-recharge during remaining M14B, before M18 launch.

- Planned payment flow: customer subscriptions → Stripe payouts → Aedrova business
  bank account → linked business payment card → OpenAI prepaid automatic recharge.
  Use supported provider billing controls; do not invent a direct Stripe-to-OpenAI
  transfer API or automatically modify financial accounts through scraping.
- Distinguish gross sales, refunds/disputes/fees, net collected revenue, settled
  payouts, cash reserves and actual provider costs. Set an owner-approved AI budget
  policy using measured M17G costs; a percentage allocation is accounting, not a
  guarantee that money has already reached the bank or provider.
- Configure an approved recharge threshold, amount and monthly recharge limit.
  Provider recharge limits do not replace Aedrova's per-workspace and global usage
  controls. Company funding must never silently refill customers' allowances or
  create customer overage charges. Keep a cash buffer for payout delays/refunds.
- Monitor supported provider cost/usage data and available funding signals; show
  reconciliation and stale/unavailable data clearly. Alert on nearing budget,
  failed recharge, delayed payouts and insufficient reserves. Pause new unfunded
  billable work gracefully; preserve tasks and reconcile in-flight charges.
- Test duplicate/out-of-order Stripe events, refunds, payout/recharge failures,
  delayed financial data, budget exhaustion and restart recovery with fixtures and
  sandbox support. Do not run real recharge purchases without explicit approval.

**Owner action now: none. Required later in M14B:** complete live Stripe verification,
configure Stripe payouts to the business bank account, provide the business payment
method directly in OpenAI billing, approve the initial reserve and recharge settings,
and personally complete any purchase/payment confirmation. Walk through these one
requirement per response; never request bank/card credentials in chat. Activation
requires live acceptance and owner approval, not merely saved configuration.

Owner action now: **none** to schedule this milestone. At execution, disclose a bounded
paid benchmark budget and get approval for any additional spend not already authorized;
provide secure provider setup steps if needed. Live Stripe, production hosting and
Apple/Windows signing remain deferred to remaining M14. Advertise verified included
AI limits on the website alongside implementation, without implying unlimited usage.

# Delivery gates

## October 7 — Dots replace prototype mini teammates

Owner explicitly authorized the attached Dots architecture request. Implemented the
native Dot shelf/profile/mentions, central targeted source selection, read-only query
path, server-encrypted per-user grants, GitHub App OAuth, bounded GitHub tools, signed
event invalidation and versioned shared identities/RLS. Legacy resource metadata is
migrated; legacy credentials require explicit reauthorization. Legacy specialist tasks
pause. Existing coding queue/checkouts/evidence/delivery and original chibi rendering
remain. Registry-only Stripe/Supabase/Vercel/PostHog and migrated Figma/Notion sources
are unavailable until their server adapters are completed.

**Owner action now:** apply `202610070001_workspace_dots.sql`; create/install a read-only
GitHub App; configure server OAuth credentials and the existing encryption key; complete
same-account authorization and live acceptance. Exact instructions: [dots.md](dots.md).
No push, website deployment, public release or live credential setup is claimed complete.
Do not start the next provider/milestone without asking. M14 remains after feature work.

## October 6 — Workroom product redesign

Owner authorized a structural frontend redesign through the attached design brief.
Implemented compact workspace navigation, responsive context/review/editor layouts,
shared neutral/blue typography and controls, grouped settings, refreshed onboarding and
matching local website styles/screenshots. No schema or permission changes.
See [design-audit.md](design-audit.md) for scope, captures, test results and limitations.
No new owner configuration is required; website publication and M17F.2 remain approval-gated.

## October 6 — real teammate connectors brought forward

Owner authorized scoped GitHub, Figma and Notion read-only tool connections, automatic
role-based/real-provider suggestions and a mandatory verified connection for saving/running
a teammate. macOS Keychain credentials are isolated per user/workspace/actor/resource;
config contains no tokens. Every work phase rechecks access. GitHub live API and native
Keychain acceptance passed; Figma/Notion live checks require owner-granted resources.
No SQL migration needed. See [teammate-connectors.md](teammate-connectors.md) for exact
in-app setup, bounded coverage, limitations and validation. M17F.2 remains approval-gated.

## October 6 — onboarding, custom-role sliders and living teammate UI refinement

Owner approved a reference-led App onboarding/chatspace redesign and animated teammate shelf.
Implemented Dub/Linear-style centered forms with Aedrova blue, preserved setup/profile/auth
flow and controls tour, free-text roles with real explicit provider tool suggestions,
styled sliders and a persistent-identity marble shelf. Reduced motion/hidden timers never
run a model. See [onboarding-teammate-refinement.md](onboarding-teammate-refinement.md).
No new SQL or owner credentials required; suggestions use existing local provider login
and allowance. Tool recommendations are advisory; unavailable connectors remain labelled.
M17F.2 shared results/team management has not started and still needs approval.

## October 6 — M17F.1 first useful slice and hosted profiles complete

Native customizable characters/profiles, `@name` assignments, named chat progress/results
and bounded specialist execution are implemented. Engineering reuses coding/delivery;
Product/Research run read-only analysis. Real Codex Research passed on synthetic evidence.
Owner SQL applied. Normal personal/school OAuth checks passed profile persistence, retries,
owner/admin writes, member reads, outsider isolation, unique actor names, pause/stale edits,
rename/stable mentions, revocation with existing profiles and deletion. Test member removed.
See [milestone-17f1-ai-teammates.md](milestone-17f1-ai-teammates.md).

Validation: 597 desktop tests, final 36 focused tests, 32 website page checks; actual
PostgreSQL/RLS suites, scoped lint, packaged signature and smoke passed. Hosted report:
`work/m17f1/hosted-teammate-check.json`. **Owner action now: none for this slice.**

M17F.2 shared results/team management requires fresh permission. Per-teammate tool/resource
grants, connectors, custom roles/colors and stronger server-side effort/priority controls
remain planned in subsequent slices. Current effort is a timeout; importance is a tone
preference. Results remain private to the initiating user. Paid Claude/final release gates
stay M14/M18. Local website previews are labelled; nothing pushed/deployed.

## October 6 — AI Teammates moved ahead of M17

Owner requested the mini/cute AI Teammates next, ahead of continuous delivery and migration.
M17F.1 implementation was approved; its current acceptance gate is documented above. Revised remaining feature order:
M17F → M17 → M17A–M17E → remaining M14 → M18 → deployed-codebase walkthrough.
M15 memory and M16 evidence are available foundations. Reuse existing agent/build task
infrastructure; do not assume the not-yet-built M17 shared work-item model exists.

The first implementation slice must demonstrate useful work, not just character CRUD:
persistent customizable identities, native mentions/results and a real bounded specialist
task through an available existing provider. Connectors expand capabilities in subsequent
slices with explicit grants and owner setup. No connectors/provider subscriptions are
activated by this planning change. Obtain approval before implementation and between slices.


## October 6 — M16 implementation and hosted shared-review checks complete

M16 now links approved memory/citations to actual diffs and observed command receipts,
acceptance criteria and versioned peer reviews. Passing checks must match the final local
file fingerprint. Scope checks, withdrawal cleanup, safe retries and explicit publication
approval remain enforced. See [milestone-16-build-reviews.md](milestone-16-build-reviews.md).

The owner applied `202610060003_build_reviews.sql`. The live personal/school-account
probe passed real local diff/check persistence, idempotent retries, exact-version peer
approval, outsider/private-channel isolation, direct-write denial, source staleness,
withdrawal cleanup and member revocation while evidence still existed.
Report: `work/m16/hosted-build-review-check.json` (no credentials).

**Owner action now: none for the implemented shared-review workflow.** M17 has not started
and requires approval. The real owner-approved GitHub test PR and paid Claude/provider
activation remain explicitly deferred external acceptance at M14/M18.

Validation: full desktop suite 587 passed; final focused review/connection checks 22 passed;
website suite 247 passed; actual PostgreSQL/RLS suites, scoped Ruff, packaged signature
and smoke passed. Light/dark/compact review captures inspected.

Live Codex planning/edit/test probe passed. Paid Claude, an owner-approved real GitHub test
PR and final provider/release acceptance are not claimed complete; unavailable external
activation remains deferred to M14/M18. Local website preview copy/captures are prepared,
with pending rollout labels; nothing pushed/deployed. AI Teammates connector requirements
remain recorded for M17F. M17 is continuous team delivery and requires fresh approval.


## October 6 — M15 implementation and hosted memory acceptance complete

Source-backed Product memory UI, revision/history and approval/conflict lifecycle, RLS/RPC
storage, permission/freshness checks and pinned build memory are implemented. Both SQL
migrations were applied by the owner. Live personal/school-account acceptance passed for
persistence, lifecycle, stale edits, private isolation, withdrawal and member revocation.
See [milestone-15-product-memory.md](milestone-15-product-memory.md).

Validation: prior complete desktop suite 572 passed; latest focused suite 105 passed;
actual PostgreSQL/RLS suites passed (including missing/late meeting schema and the
conflict-function upgrade); rebuilt signature/smoke and scoped lint passed. Public-page
suite previously 32 passed. No successful live paid-provider build or hosted meeting-source
acceptance is claimed; those external acceptance gates remain required at M14/M18.

**Owner action now: none for M15. M16 was approved and is in progress; see the latest entry above.** Local website screenshots/copy are prepared; nothing pushed or
publicly enabled. M14 setup remains deferred until feature implementation is complete.
AI Teammates M17F now explicitly includes scoped external app connectors for Marketing,
Generation/Design, Finance and Builder roles. No connector accounts are required now.


## October 5 — authoritative order: build features before remaining M14

Owner explicitly deferred remaining M14 until all planned feature implementation is built.
This ordering supersedes prior entries that call Apple enrollment the current gate or
place M14 before M15. Completed M14A work remains complete; pending acceptance is not waived.

1. **M15:** persistent product memory, approved decisions, citations and scoped retrieval.
2. **M16:** traceable builds and shared review with real test/diff evidence.
3. **M17:** continuous team delivery and handoffs.
4. **M17A–M17E:** guided Slack/Teams migration and context continuity.
5. **M17F.1–M17F.4:** persistent customizable AI Teammates and scoped external app
   connectors for marketing, generation/design, finance and builder workflows, using
   existing infrastructure.
6. **Remaining M14:** production owner setup/signing/live Stripe/hosting/provider activation,
   hosted meeting/hardware acceptance, Windows compatibility/build/distribution and final
   installer/update rehearsals for the completed feature set.
7. **M18:** final expanded security/production acceptance and explicitly authorized launch.
8. **Entire-codebase walkthrough:** after everything is complete and deployed.

Do independently available feature work first. Defer Apple enrollment, paid hosting,
live Stripe activation, signing and release purchases to remaining M14. Still disclose
feature-specific SQL, test-tenant/export/provider or access requirements when actually
needed; staging/local checks do not establish live acceptance. Record any unavailable
external tests and finish them at M14/M18 before advertising public availability. No
public product release, migration of real customer data or payment activation is authorized
by this reordering. The existing waitlist website remains live.

**Next task: M15 implementation**, subject to explicit owner approval. This request
changes the plan only. Do not continue asking about Apple enrollment during feature work;
resume that one-requirement-at-a-time walkthrough when remaining M14 begins.


## October 5 — M17F AI Teammates added as a major differentiator

Add **M17F.1–M17F.4** before M18: persistent specialist identities/character customization,
quick creation/native chat, permission-scoped execution and meeting context, then live
acceptance/UI polish and website advertising alongside the main builder. Shape, color,
name, personality, reporting cadence, effort and importance are explicit controls. Reuse
existing agent/task/context/usage infrastructure; passive presence consumes no model credits.
See [ai-teammates-roadmap.md](ai-teammates-roadmap.md). Planning only; attached implementation
commands are requirements for that future milestone, not permission to start now.
No owner action required for this addition. M14 Apple enrollment remains the current gate.


## October 5 — Slack and Teams migration milestones added

Add **M17A–M17E**, after M17 and before M18, for migration foundation/preview, Slack
imports, Teams imports plus Microsoft account linking, staged cutover/rollback, and
permission-scoped context continuity with real pilot acceptance. See
[migration-roadmap.md](migration-roadmap.md) for deliverables, platform limits and checks.
Planning only: no implementation, website availability claims or deployment authorized.
No owner action required now; real exports and tenant/admin permissions come at delivery.
The final codebase walkthrough remains after the entire app is complete and deployed.


## October 5 — M14D Windows desktop distribution added

Owner requested a Windows build. Add **M14D — Windows compatibility, installer and
release acceptance** after M14C; finish before M18 public cross-platform launch. This
plans the work only; it does not claim Windows support or authorize starting implementation.

Deliverables:
- Audit platform-specific paths, keychain/session storage, keyboard shortcuts, file/folder
  selection, IDE launching, GitHub CLI and Codex/Claude integration on Windows.
- Adapt camera, microphone, audio calls, video calls and screen sharing to Windows,
  preserving explicit permissions and the existing workspace/context security boundaries.
- Build on a Windows CI runner and produce a versioned downloadable installer (.exe),
  with uninstall support and release digests; never treat a macOS bundle as a Windows build.
- Sign Windows release artifacts and implement verified Windows update installation,
  rollback/recovery and clear failure messages using the existing release trust model.
- Add website platform-aware download choices when an approved Windows release is ready;
  preserve the waitlist/public-release gates until acceptance passes.

Acceptance: clean install, launch, Google callback/onboarding, chat/reactions/files,
local agent build/review, GitHub authorization, meetings and screen sharing, light/dark
and display scaling, upgrade/recovery, uninstall and security regression checks on an
actual supported Windows environment. Publish supported Windows versions/architectures
only after verification. Include Windows CI and release code in the final codebase walkthrough.

Owner actions: **none required now**. At M14D, walk through Windows code-signing
setup and arrange a Windows test device or VM; explain available signing options/costs
before requesting a purchase. Never request certificate secrets in chat. M14B's current
Apple Developer enrollment requirement remains the next owner setup step.


## October 5 — requested core chat collaboration expansion

Owner confirmed the reaction SQL was applied. Existing workspaces, channels/private access,
DMs, threads, uploads, unread counts, invitations and roles reviewed. Missing chat actions,
group DMs, rich text, mentions, search/activity/files/saved/pinned tools, channel topics/posting,
typing, presence, profiles and notifications implemented locally. See `docs/chat-collaboration.md`.
New `202610040002_chat_collaboration.sql` must be run once by the owner, followed by an app
restart; hosted two-account acceptance remains pending. No public push/deploy or M14 purchase
occurred. Return to M14 requirement 1: confirm Apple enrollment purchase and active/pending status.


## October 3 — M14A local rehearsal complete; M14B/C remain deferred

Owner authorized resuming M14. The actual signed preview DMG passed integrity/digest,
mounted signature/version/link checks and isolated installation, replacement and rollback
launches, retaining synthetic settings/project files. Both themes inspected. Replacement
uses the same preview version; no real version migration or fresh-Mac acceptance claimed.
Malformed update-field types now fail with readable validation errors; real loopback HTTP
checks cover compatible newer metadata, closed/invalid/oversized/preview responses and
cross-origin redirects. 503 desktop tests, 247 website/backend tests, all 25 desktop SQL
files, private ledger/meeting schema checks, scoped Ruff, secret scan and rebuilt preview
checks pass. See [milestone-14-local-rehearsal.md](milestone-14-local-rehearsal.md).

No hosted migration, purchase, public flag, push or deployment changed. **M14 overall is
not complete:** M14B owner signing/paid hosting/live billing/provider setup and M14C hosted
two-physical-Mac meeting/context acceptance remain deferred. No owner action is required
for local rehearsal; reopen the rebuilt preview for the fix. Announcement SQL activation
remains unconfirmed. Ask permission before M14B/C or independent M15 implementation;
do not waive the release gates when proceeding with locally available work.

## October 3 — differentiation milestones added; authoritative next sequence

See [differentiation-roadmap.md](differentiation-roadmap.md) for deliverables and acceptance
criteria. This sequence supersedes earlier forward-looking launch/walkthrough ordering;
historical implementation and test records below remain intact.

- **M14:** remaining local release rehearsal, deferred M14B owner production setup and
  **M14C final hosted meeting acceptance**. Meetings finish at M14C only after real provider,
  consent/context, permissions/recovery and two-physical-Mac checks pass. M10/M12 local
  implementation is not complete hosted acceptance. **M14D** adds Windows compatibility,
  installer/signing, verified updates and Windows acceptance (see October 5 entry above).
- **M15:** persistent, editable product memory with approved decisions, source citations,
  conflict review, freshness and permission-scoped retrieval.
- **M16:** traceable builds linking agreed requirements to code, actual tests and shared
  PR review; retain explicit publishing approval.
- **M17:** continuous team delivery and handoffs, reviewed learning back into memory,
  visible product differentiation and measured workflow evidence.
- **M17A–M17E:** guided Slack/Teams migration, identity/permission mapping, safe
  catch-up/rollback and cited historical context; see [migration-roadmap.md](migration-roadmap.md).
- **M17F:** persistent, customizable AI Teammates as a major product pillar; see
  [ai-teammates-roadmap.md](ai-teammates-roadmap.md).
- **M18:** security and production acceptance for the expanded product, then authorized
  public launch. The waitlist website remains live while product capabilities stay gated.
- **Entire-codebase walkthrough:** after the entire application is complete and deployed,
  including M15–M18; historical M13B label does not change that timing.

Only roadmap edits are authorized by this request. Ask before starting a new implementation
milestone. Owner paid/account/second-Mac actions remain deferred; no secrets or purchases
are required for this planning task. Announcement SQL activation remains unconfirmed.

## October 3 — meeting actions and announcements implemented; SQL activation pending

Start/Join meeting, shared channel announcement preference, circular participant photos
and counts are implemented. 493 desktop tests and 25 embedded SQL files pass; signed
preview, packaged smoke and compact theme visuals pass. See `meeting-announcements.md`.
Owner must run `202610030004_meeting_activity.sql` in Supabase and reopen the app before
shared live-account acceptance. Do not claim hosted activation complete; ask before
validation or resuming the remaining M14 release rehearsal.

## October 3 — workspace mentions and chat scroll boundary complete

Mention suggestions now use the team agent nickname in both composers. Final agent
results replace progress without leaving stale blank scroll space; repeated wheel
scrolling, shrinking results and resized layouts are checked. 490 desktop tests, Ruff,
visual and signed packaged smoke checks pass. See `agent-chat-polish.md`. No owner SQL
or public deployment changed. Reopen the rebuilt app; ask before resuming local M14.

## October 3 — working-message and build-onboarding follow-up complete

Live status/time/Stop are now in the agent chat message; transient updates disappear
on completion, leaving the final result. Getting started includes project connection,
provider/editor and explicit automatic planning/execution. Folder selection uses native
macOS UI. See `agent-chat-polish.md`; 482 desktop tests and packaged/visual checks pass.
No SQL or public deployment changed. Owner should reopen the rebuilt app; ask permission
before resuming the remaining M14 local release rehearsal.

## October 3 — requested agent chat presentation polish complete

Agent responses now appear within the conversation with the team nickname, avatar,
sent time/date, teammate typography and spacing. Expandable tools and build controls
remain; originating-channel visibility and realtime/widget lifetime are checked.
477 desktop tests, Ruff, visual checks and rebuilt-preview validation pass. See
`agent-chat-polish.md`. No SQL/deployment/paid setup changed. Ask permission before
resuming the remaining M14 local installation/update rehearsal.

## October 3 — owner setup walkthrough deferred (M14B)

Owner explicitly requested a later guided walkthrough for **Apple Developer ID, Render
and Stripe**, saved here. Schedule **M14B — guided production account and release setup**
when the owner has the required account details and payment access. Continue independently
available local M14 preparation first. Ask permission before starting M14B; do not request
these details or purchase services during local preparation.

Walk the owner through the actual dashboards and local tools, one step at a time:

- Apple Developer Program enrollment/team access, Developer ID Application certificate
  and private key via Keychain, notarytool Keychain profile, signing/notarization/stapling,
  Gatekeeper verification and public installer/update acceptance. Distinguish existing
  Apple Development preview signing from Developer ID public distribution.
- Render: existing website/Supabase setup, explicit recurring-cost approval, always-on
  compute and Blueprint consistency, private server environment, independent meeting
  guard/maintenance jobs, TLS/domain, health checks, GitHub deployment, rollback and logs.
  Review actual prices before purchase; no new Render PostgreSQL is assumed.
- Stripe: truthful business verification/payout setup, live-versus-sandbox separation,
  approved weekly/monthly prices, Aedrova branding and portal, private keys, signed webhook
  destination, subscription/allowance integration, failure recovery and launch gates.
  Use sandbox for payment testing; never request private keys or financial details in chat.

Explain what each action unlocks and verify it before proceeding. Owner-only identity,
banking/payment and account approval actions stay with the owner. Keep public checkout,
managed AI, meetings and installer publication gated until their acceptance checks pass.
This walkthrough precedes the corresponding public release activation; it cannot be
postponed past publishing a paid/signed app. The separate **entire-codebase walkthrough**
remains after the entire application is complete and deployed.

## October 3 — M14 local preparation authorized; meeting recovery in progress

Owner approved credential-free local release preparation, keeping Stripe activation, paid
hosting and public signing deferred. Initial regression: 473 desktop / 243 website tests,
23 embedded SQL scripts, private ledger schema, SDK handshake and installed-agent boundary
fixtures pass. Preview packaging passed. Owner then reported meeting failure: the local
API had stopped and the rehearsal preview incorrectly targeted the public waitlist origin.
Rebuilt with local port 8090, local AI mode and the existing Apple Development signature;
restarted local API, verified readiness and synthetic LiveKit media transport. No public
meeting/checkout/AI/release flags were enabled. Owner signed-in physical call retry remains
pending. M14 is NOT complete; continue the isolated installation/update rehearsal next.


## October 3 — M13A local release hardening complete; stop before M14

The owner approved M13A. Workspace quota accounting, service-only leased orphan cleanup,
safe local build/context retention and Claude forbidden-network wait handling are implemented.
473 desktop tests, 231 website/backend tests and all 23 embedded PostgreSQL scripts pass;
Ruff and installed-agent boundary/normal-edit fixtures pass. Full policy and exact deferred
owner actions are in `milestone-13a-release-hardening.md`. No hosted SQL, object deletion,
credential, purchase, push or deployment was performed. UI and live release flags are intact.
Next: M14 owner setup, staging deployment and hosted acceptance, then release activation.
Obtain permission before starting. Codebase walkthrough follows the entire app's completion
and deployment; do not start it now.

## October 3 — next step: M13A release hardening; walkthrough deferred until after deployment

The owner moved the entire-codebase walkthrough to after the entire application is
complete and deployed. Do not start M13B before that condition is met. The next proposed
implementation task is **M13A — remaining release hardening**: aggregate workspace storage
quotas, safe orphan-upload cleanup, explicit local build/context retention and cleanup,
and handling of Claude forbidden-network waits. Add meaningful regression checks and
revalidate the agent boundaries. Keep existing UI/features and live release gates intact.
This task is proposed, not authorized yet; ask permission before implementation. Complete
independent code preparation before requesting necessary owner SQL/configuration actions.
M14 remains final hosted acceptance, owner setup and deployment/release activation.

## October 3 — M13 local security audit complete

The owner authorized the final safety/security audit. Verified fixes cover coding runtime
read boundaries and credential scrubbing, hardcoded/context credential filtering, local
preview Host/Origin protection, private-input validation, bounded gateway/speech processing
and a website cryptography dependency update. See `milestone-13-security-audit.md` for scope,
evidence and remaining risks. 452 desktop tests, 216 website/backend tests, all 21 desktop
SQL scripts and the private website ledger/meeting PostgreSQL checks pass. Installed-agent
synthetic boundary tests pass; Claude forbidden-network tools can wait until cancellation.
These changes are local, not deployed or rebuilt into a new public installer. M14 release
gates and remaining storage/retention/load engineering are not waived. No owner credentials,
purchase or migration is required now. Ask permission before M13A; it has not started.


## October 3 — M12D local speech and review complete; stop before M13

The owner approved M12D and explicitly required a stop before M13. Native opt-in microphone
chunks, server-only bounded speech ingestion/reservations, transcript review/corrections,
confirmed decisions, post-call browsing, privacy withdrawal/deletion and reviewed agent
citations are implemented locally. See `milestone-12-speech-review.md` for the exact boundaries,
verification and M14 owner actions. Both server capabilities and the public desktop context
flag remain disabled. No hosted SQL, provider key, paid resource or deployment was activated.
438 desktop tests, 213 website/backend tests and all 21 embedded PostgreSQL scripts pass.
Local fixture acceptance does not replace real provider/physical/hosted acceptance at M14.
Ask the owner for permission before M13; M13 has not started.

## October 3 — M12C historical delivery; codebase walkthrough added

Owner approved the local meeting consent/storage/context task. Incremental SQL,
user-token API, gated privacy controls and meeting citations are implemented locally;
see `milestone-12-meeting-context.md`. Automatic speech capture/provider ingest and a
transcript review/editor are not yet implemented. No hosted migration, credentials or
paid setup is required now; those actions remain in M14. Ask permission before the next
speech/review implementation task and keep unvalidated public capabilities disabled.

**M13B — entire-codebase walkthrough (owner-requested milestone, deferred)** follows
completion and deployment of the entire application, including M14 acceptance/release.
Walk through the actual
final code, not a hypothetical architecture: repository/folder map; Python/Qt app startup,
onboarding and UI; Supabase auth/schema/RLS/realtime; agent context/planning/execution,
local files and GitHub delivery; FastAPI website/waitlist; Stripe/managed AI/usage;
LiveKit/meeting consent/transcripts; tests, configuration, secrets and failure handling;
CI/deployment, Mac packaging and updates. Explain key files and one complete flow from
user action to storage/provider and back. Provide practical steps for finding/editing
features, testing, publishing and debugging; distinguish local code from live validation.
Use a guided explanation and diagrams, with time for the owner's questions. The request
adds this milestone; do not start that walkthrough before the agreed implementation work.


## Latest owner direction — October 3: M14 deferred meeting activation

The owner requested moving the required actions from the shared meeting staging handoff
to the latest milestone. **M14 is the final owner setup and hosted meeting acceptance gate**.
Defer paid Render API/worker approval and creation, shared secret entry, the internal app's
hosted-origin rebuild/installation and two-Mac physical validation until M14. No hosting
purchase, new credential request or second-device request is required now. Keep the
prepared Blueprint and bounded/sanitized guard implementation available.

M12 continues with independently testable feature/integration implementation. M13 remains
the safety audit and release preparation; those checks cannot substitute for M14's live
meeting validation. Meeting hosting, recording/transcription and meeting-to-agent context
must remain unavailable publicly until their relevant live/consent gates pass in M14.
This deferral does not declare M10/M12 meeting acceptance complete, authorize paid
resources, or waive signing, billing or any other public release gate. Website waitlist
stays live. Ask permission before the next implementation task.


October 3 — M12B shared meeting deployment preparation approved. The waitlist site is
live on aedrova.com; certificates, readiness and www redirect passed. Separate Render
API/guard deployment configuration is in the website repository's
`deploy/render-meetings.yaml` and `docs/render-meetings.md`. It reuses restricted Supabase
with bounded pools. Paid service approval and owner secret entry are required before
live meeting acceptance; no paid services or transcription enabled by this preparation.
Two-Mac hardware acceptance remains deferred until a second Mac is available.

Domain follow-up, October 2: owner confirms applying workspace archive SQL, bought
aedrova.com at Cloudflare (registrar email verified) and selected Render. Website-only
deployment is now requested. Render authorization/hosting/private PostgreSQL/server
secrets and DNS/TLS/OAuth acceptance remain pending; preparation is in the website
repository docs/domain-deployment.md. Apple Developer/signing remains at M13. Domain
ownership does not enable live checkout, managed AI, meetings or public DMG downloads.

M12 started — October 2, 2026: owner approved remaining integration work and explicitly
deferred Apple Developer enrollment/signing setup and custom-domain setup to the latest
possible stage. Keep both out of M12 prerequisites. Developer ID/notarization/fresh-Mac
acceptance remain mandatory before public DMG release in the M13 launch gate; a custom
domain is optional, and a provider's stable HTTPS URL can support hosted acceptance.
Neither public download nor live checkout is enabled by this approval.

M12A — personal workspace cleanup: Archive for me and Restore are implemented.
Personal archival does not delete chats/files, change permissions or affect teammates
or subscriptions. Finish local active builds/calls before archiving; controls enforce
this and recheck at confirmation. Archived-only accounts get a restore screen instead
of a forced new-workspace wizard. New SQL 202610020002_workspace_archive.sql must be
applied by the owner before this rebuilt desktop can load its workspace inventory.
Local test evidence and the next-task handoff are in milestone-12-workspace-cleanup.md.
M12 is not complete: consented transcription/meeting context and the remaining integration
acceptance follow, with task-by-task owner permission as previously requested.

Pre-M12 hardening — October 2, 2026: owner requested audit-first production reliability
work. Incremental backend/database/AI/context/realtime bounds and sanitized observability
are implemented; 408 desktop and 154 website tests pass. Full audit is in the website
repository docs/production-readiness-audit.md; updates are explained in app-updates.md.
Owner confirmed applying 202610020001_scalability.sql on October 2, 2026.
The hosted search RPC rejects anonymous execution (401 / 42501); authenticated
indexed-context and rate-budget acceptance still require a signed-in check.
Hosted load, PostgreSQL concurrency, storage quotas, realtime fan-out, commercial AI and
public signing acceptance remain open. No large-scale capacity claim or M12 start.

Current M11 update — October 2, 2026: owner approved M11. Local optional setup,
17-step chaptered spotlight tour, explicit update checks and installer/download preparation
are implemented and tested (404 desktop / 135 website tests). See
`milestone-11-release.md` for exact owner actions and verification. Public acceptance
remains blocked by Developer ID/notarization, stable HTTPS hosting/managed services
and a fresh-Mac test. No public download, live checkout, push or deployment was enabled.
M12 still requires permission. Older status entries below are historical.


Current task update — October 2, 2026: owner requested the M9 Stripe configuration and
checkout acceptance before M11. Plans/onboarding/account/confirmation and isolated sandbox
configuration and real Stripe sandbox acceptance are complete. Both approved plans, signed
webhooks, portal cancellation, declined payment/3DS, timed renewal/failure/recovery and replay
checks passed. New invoice API and workspace-selection defects are fixed; 132 website and
15 desktop managed-access tests pass. Owner credential/redirect setup is complete.
See website `docs/stripe-sandbox-setup.md`. No live checkout or M11 approval is implied.
After sandbox acceptance, ask permission again before starting M11.

Current status — October 2, 2026: the final UI polish of implemented desktop and
website surfaces is locally verified; see `final-ui-polish.md`. M11 has not started
and requires fresh owner approval. M9 code is locally verified, but paid-beta activation
still requires Stripe/provider/server setup, measured usage and live acceptance.

The owner deferred the remaining M10 work because shared hosting and a second Mac are
unavailable. Preserve the tested local call implementation. Move shared HTTPS deployment,
two-device physical audio acceptance, consented transcription and scoped meeting context
into **M12's deferred meeting completion**. M10 is not fully accepted. Those prerequisites
do not block the approved visual pass or a separately approved M11 preparation task.

Next sequence: M11 premium desktop setup/tour and Mac distribution preparation (approval
required) → M12 deferred meeting completion and remaining PRD integration gaps → M9
commercial activation acceptance when owner setup is ready → M13 final safety/public
launch gate. A purchased domain remains optional during preparation; public notarized
release and paid access remain gated.

The following October 1 sequence is historical and is superseded by this status.

## Current next-task sequence — October 1, 2026

Completed this task: hosted two-account meetings with the owner's approved school
account, generated camera/screen frames, repeated heartbeats, scoped/private-channel
negative checks, leave/rejoin, server-forced membership removal, cached-token rejection,
and host end. This is two real authenticated accounts on one Mac, not two-device
physical audio acceptance. Report: `work/hosted-meeting-check.json`.

Fixed a rapid Google-sign-in listener reuse bug and the meeting-origin/AI-authentication
coupling. The internal development package explicitly uses local provider access;
commercial releases explicitly require included access and cannot fall back to personal
credentials. Real local Codex file creation passed in an isolated test project. Managed
API execution and paid checkout still require owner commercial credentials/configuration.

The owner authorized completing the remaining M10 scope on October 1. Hosting and a
second Mac are currently unavailable (owner confirmed). M10C deployment preparation
now includes a non-root container, separate worker command, durable external-guard
health, fail-closed joins, atomic duplicate-lease rejection and a credential-safe HTTPS
preflight. No deployment or Docker image build has been performed. See the website
repository's `docs/meeting-hosting.md` for exact setup and physical acceptance checks.
M10 remains in progress; transcription/retrieval are not implemented or enabled.
Resume already-authorized M10 when the live media prerequisites are available; request
permission before moving to M9 activation, M11 or another milestone.

Proceed through these remaining tasks:

1. **M10C — shared HTTPS service and two-device call acceptance.** Prepare a shared
   service address using a hosting provider's HTTPS URL; a purchased/custom domain is
   not required. Keep the independently supervised access guard, encrypted durable
   leases and logging redaction. Owner needs a second Mac and two Google accounts in
   the same test workspace/channel. Validate microphone/speaker audio in both directions,
   headphones and speaker echo, camera/screen rendering, device stop/permissions,
   network loss/reconnection, leave/rejoin and host end. Do not expose the localhost API
   publicly or transmit deployment credentials without separate approval/setup.
2. **M10D — consented transcription.** After the media gate passes, implement explicit
   per-participant transcription/AI-context consent, a clear active indicator, revocation
   on roster/revision changes, speaker attribution and retention/deletion controls. Select
   and configure a server-side speech provider; no credentials in the app. Validate consent
   races, participant removal and failed/partial transcripts before enabling the feature.
3. **M10E — meeting context for the agent.** Scoped meeting transcripts, reviewed decisions
   and citations enter workspace retrieval. Verify cross-workspace/private-channel isolation,
   revoked access, expired retention and precise context-to-build behavior. Finish M10 only
   after live acceptance; no silent recording or automatic consent.
4. **M9 activation follow-up — managed AI and Stripe test acceptance.** Owner configures
   commercial provider billing/keys and server models, Stripe test Prices/webhooks and hosted
   service secrets. Verify real Codex/Claude gateway builds, measured costs, allowance stops,
   subscription lifecycle and reconciliation. Keep $10/week, $49/month and Enterprise
   Contact Us presentation; approve any later allowance adjustments before live checkout.
5. **M11 — Mac release and website delivery.** Developer ID signing/notarization (development
   signing is insufficient), distributable DMG, updates/recovery, fresh-Mac acceptance and
   hosted website/download flow. Complete premium setup and the skippable dashboard tour,
   covering all implemented functions; verify website onboarding, real screenshots and billing
   continuity. A custom domain can remain a final launch follow-up.
6. **M12 — remaining feature/integration completion.** Reconcile the PRD with implemented
   features and website claims; finish any confirmed gaps in files/design/decision context,
   GitHub/IDE acceptance, provider parity and workspace management, including archiving test
   workspaces. Extend platforms/multi-repo only after the agreed macOS scope is accepted.
7. **M13 — final app safety audit and public launch.** Audit secrets in source/history/builds,
   dependencies, auth/tenant isolation, rate limits, billing/usage abuse, hidden administrative
   access, prompt injection/tool approvals, redaction, backup/incident recovery and release
   artifacts. Resolve findings before public paid access. A custom domain and final live-key
   checkout/release switches belong to this launch gate, not the current local test task.

No new owner SQL or secrets are required for the completed two-account/local-AI fixes.
Next-task manual setup: second Mac availability and a shared HTTPS hosting environment.
Commercial AI setup instructions remain in the website's `docs/owner-setup.md`, section 4.

Earlier status:  M7 and its guided GitHub CLI setup follow-up are implemented and locally verified; live GitHub publication still needs owner browser authorization and acceptance in a test repository. M8 local execution durability is implemented; its complete live Codex acceptance reached a provider quota limit. See `milestone-7-delivery.md`.

Earlier milestones: milestones 1 and 2 complete. Milestone 3 Google login and the first chat migration are confirmed by the owner; the owner has confirmed that messages do not leak between separate workspaces. Milestone 4 code is implemented and locally tested, including DMs, attachments, unread state, keyset history, private realtime invalidations and reconnect/retries. The owner confirms applying the final communication migration and clarifies that the two-account observation was a successful isolation check, not a delivery failure. Same-workspace delivery and remaining hosted acceptance scenarios are not established by that check. The owner moved the full safety audit to the end of feature development; it is now milestone 13.

The owner requested sequential milestones. At the end of each: run necessary checks,
report evidence and limitations, then ask permission before beginning the next.
Never interpret a passed unit test as a passed live integration.

1. **Feasibility and contracts** — Python desktop/history probe, package launch, SDK handshake,
   synthetic media interoperability, permissions/context/build/approval contracts and documented limits.
2. **Desktop shell and visual system** — workspace/channel/tab navigation, chat and thread layout,
   keyboard behavior, accessibility and light/dark themes with realistic fixtures.
3. **Identity and tenant isolation** — Google-only Supabase login, team agent nickname onboarding,
   invitations, roles, private channels,
   data/storage/realtime policies; negative cross-tenant tests.
4. **Reliable communication** — messages, threads, DMs, attachments, unread state, reconnect and retries.

5. **First real build** — implemented for internal alpha with actual Codex execution verified,
   a Claude Agent SDK adapter, permitted workspace context, plan approval, independent local Git
   copies, tests, cancellation and streamed results. Claude paid execution and signed-in hosted
   context-to-build acceptance still require owner setup/checks; see `milestone-5-local-builds.md`.
6. **Project context** — implemented and locally verified: ephemeral FTS5 retrieval, thread
   expansion, explicit member-confirmed/retired decisions, source browser, validated citation IDs,
   scoped channel pagination and revision checks for edits/deletions during collection.
   Owner applied `202609290001_context_decisions.sql`; hosted search, decision confirmation/retirement and cited Codex planning passed. See `milestone-6-hosted-check.md`.
7. **Account usability, chat-to-IDE builds, review and delivery** — start with an account/UI
   usability slice: make the bottom-left account control open a real menu with clear logout,
   current account/profile and meaningful available workspace/account actions. Build matching
   settings with working preferences; hide unavailable functions instead of inert placeholders.
   Audit dropdowns, menus, dialogs, focus/keyboard states and light/dark themes for consistency
   with Aedrova's Apple-inspired design. Test logout cleanup and all exposed account actions.
   Then finish the native end-to-end flow: a team
   agrees in chat, invokes its named agent, and the agent retrieves permitted workspace evidence
   without requiring the user to re-enter the discussion. Bind the workspace to a local project
   and connected GitHub repository, reuse that binding for subsequent requests, show progress and
   actionable questions in the chat flow, and open the resulting code in VS Code or the chosen IDE.
   Provide diffs, safe application of approved changes to the selected project, exact approvals,
   GitHub push/PR and one preview provider. Preserve uncommitted user work; pushes require approval.
8. **Execution durability** — queue/recovery, resource limits, concurrency, idempotency and usage ledger.
9. **Stripe paid beta and included AI** — one Aedrova subscription includes an explicitly defined
   workspace AI allowance and a choice of supported Codex/OpenAI or Claude models. Customers
   do not supply provider keys or purchase separate provider subscriptions. Aedrova pays provider
   API usage through its own commercial accounts. Implement a server-side provider gateway,
   Stripe subscriptions, signed/idempotent webhooks, entitlements, atomic usage reservation and
   reconciliation, concurrent-run limits, visible balances and opt-in top-ups. Never embed shared
   provider credentials in the desktop app; local coding runtimes authenticate to the gateway with
   scoped, short-lived Aedrova credentials. Verify each runtime's gateway compatibility before launch.
   Keep local-file execution and user tool approvals. Pricing and included amounts require measured
   costs and owner approval; no unlimited-usage promises or automatic overage charges by default.
   Requires a distributable beta installer from an early slice of milestone 11.
10. **Meetings** — room calls, devices, sharing, consent/transcription and meeting-to-build retrieval.
11. **Mac release preparation** — website/DMG/signing/notarization, updates, fresh-Mac installation,
    backups/recovery, crash reporting and operations.
12. **Expansion** — second provider, more integrations/environments/platforms and multi-repo agents.
13. **Application safety and release audit** — run the full safety review after feature development and before public launch. Audit source, history, dependencies and release artifacts for secrets; review tenant/session permissions and hidden administrative access; harden server-enforced rate limits, quotas, signup/invitation abuse controls, file cleanup, audit logs/redaction and incident recovery. Review agent prompt injection, checkout isolation, tool approvals and network access. This is the rescheduled full audit, formerly 4A.

Essential access checks, isolation, safe credential handling, and explicit code execution/push approvals remain part of implementing each feature. The rescheduled full audit does not remove existing protections. Milestone 5 was explicitly approved and implemented. Milestone 6 was approved and implemented; the owner applied its migration and the single-account hosted context-to-plan acceptance passed. Live two-account revocation remains unverified; local isolation suites pass. Milestone 7 was approved. Its account, project binding, local review/application, IDE, static preview and GitHub delivery code is implemented; see `milestone-7-delivery.md`. Live GitHub acceptance still requires owner authentication. Milestone 8 was approved and locally implemented; see milestone-8-execution.md. Milestone 9 was subsequently approved; see its latest delivery record below.

Live model execution, connected Supabase/GitHub/Stripe, conferencing and release signing require
appropriate service accounts at their milestones. Local protocol probes do not replace those gates.


## Included AI product decision — 2026-09-28

The owner requested one native Aedrova payment covering both the workspace and its coding AI.
This is the intended customer experience. Milestone 5's local Codex login / developer Anthropic
API key is an internal-alpha arrangement, not the intended paid-customer onboarding flow.
The roadmap requirement is recorded; the managed gateway and billing are not implemented yet.
No provider billing or Stripe accounts were created or charged by this documentation change.

Required later: owner enables billing for Aedrova's OpenAI Platform and Anthropic Console
accounts, completes Stripe business/payment onboarding, and approves plan prices/allowances.
Provider secrets are configured only in the backend deployment's secret store. These actions
block a live managed paid beta, not current local-alpha development. No action is needed now.

Provider references: https://developers.openai.com/codex/auth and
https://code.claude.com/docs/en/agent-sdk/overview . API-funded use is distinct from including
an individual ChatGPT/Claude consumer subscription; do not describe the plan as reselling those
subscriptions. Customer-facing provider packaging remains subject to applicable provider terms.


## Native build workflow confirmation — 2026-09-28

The owner confirmed the desired final journey: teammates converse and agree, then say
“@AgentNickname, build our newest feature, [feature]”. The named agent searches the entire
chatspace the requester is authorized to access, identifies the relevant requirements and
confirmed decisions, builds in the connected local project usable from their IDE, and can
push to the connected GitHub repository after approval. Do not make the customer manually
reconstruct context or supply provider keys. Do not interpret all chat as approved requirements.

Milestone 6 supplies context retrieval and citations; milestone 7 owns the integrated chat,
project/IDE and GitHub delivery journey; milestone 9 removes the alpha provider setup via
managed AI billing. This request records future scope only and does not authorize starting
milestone 6 or 7. The owner tried the alpha flow but Claude execution could not complete
without its API setup; do not record that attempt as successful live Claude validation.

No owner configuration is needed to start milestone 6 development. If it introduces a Supabase
migration or hosted service, provide the exact owner steps at handoff before claiming hosted
acceptance. Later milestone 7 requires the owner to select a local project/IDE and authorize
GitHub repository access; milestone 9 requires provider billing and backend secret setup.

Milestone 6 delivery: 190 Python tests and all embedded PostgreSQL suites pass. Real Codex
planning consumed synthetic indexed context and produced valid citations. Claude paid execution
and hosted workspace acceptance are not implied by those results. No milestone 7 work started.


The owner requested the account/settings/menu consistency slice at the Milestone 6 handoff.
It is recorded as the first part of Milestone 7; the request is not approval to start that
milestone. Account deletion, billing and other destructive or unavailable backend actions must
not be represented as working controls before their actual implementation and verification.


## Distribution and guided onboarding — owner direction, 2026-09-29

After finishing M7 and its checks, implement a guided GitHub CLI installation step: detect
existing installations, explain why the helper is needed, offer one explicit installation
button, show progress/retry, and guide the user through GitHub's own browser authorization.
The application should handle download and verification without terminal commands or an
administrator password wherever possible. Do not silently install executables. GitHub
connection should be offered during onboarding and remain available from Projects.

Integrate the separate marketing/download website into **M9's paid-beta release slice**
(dependent on the early signing/DMG work from M11). Keep its backend in Python and its visual
identity consistent with the desktop app. Explain the PRD's complete journey simply: private
channels/rooms, teammates, decisions and sources, a named Codex/Claude agent, local IDE builds,
review/testing/approved GitHub delivery, and consented meeting transcription as context.
Show unshipped capabilities as forthcoming until their milestone passes; do not advertise
video calling/transcription as available before M10. Keep integration expansion claims accurate.

Website journey: clear feature examples → short, friendly, skippable questions such as team
size and referral source → transparent payment plans → Google account/checkout as needed →
correct Mac download → short installation guidance. Preserve progress/back navigation; do
not make optional marketing answers a purchase gate. Plan pricing/allowances still need owner
approval and cost evidence; PRD illustrative prices are not approved billing configuration.
Owner later supplies domain/DNS access, Stripe business setup, provider billing, privacy/terms
copy, and Apple Developer signing/notarization credentials. These do not block M7/M8.

Add **M11a: premium desktop onboarding**, iterating its basic setup during M9 beta:
- Short form steps with Next/Back, restrained transitions and clear progress to configure
  account/workspace, agent nickname/provider entitlement, local project/IDE/GitHub and workflow.
- A first-dashboard interactive tour with dimmed backdrop, spotlight and anchored labels.
  Every actually available function must have a tour step: navigation/channels/threads/DMs,
  invitations/roles, search/decisions/sources, attachments/history, named-agent planning/builds,
  tool approvals/cancellation, review/application/IDE/preview/GitHub, settings/accessibility/
  logout, billing/usage, and (after M10) calls/devices/sharing/recording consent/transcripts.
- Complete coverage via short task-based chapters, not one forced marathon. Skip, pause,
  resume, previous/next and replay from Help; never perform a destructive or billable action
  just to advance a tour. Remember completion per account and tour version.
- Support keyboard focus, screen readers, reduced motion/transparency, both themes, resizing,
  missing integrations and different membership roles. Never spotlight unavailable controls.
- Add a feature-to-tour coverage check so future features cannot silently miss onboarding.

The PRD remains the feature reference, with the owner's Python/macOS-first direction taking
precedence over its original web-first platform ordering. The website and full animated tour
are scheduled work; this roadmap entry does not claim they are implemented.

Guided GitHub setup is now implemented and tested after the M7 checks. The M9 website and M11a animated tour remain planned, not started.


## M7 autonomous-agent follow-up — 2026-09-30

Implemented: saved automatic planning/execution permission, background mentions, inline public
activity/actions with reduced-motion-aware shimmer, Stop, and corrected Codex stream recovery
and terminal error reporting. No visible Create plan step remains. See `autonomous-agent.md`
for setup, tests, provider limitations and still-outstanding live GitHub authorization.
M8 was approved and locally implemented; M9 retains included AI subscription billing.

## M8 delivery — 2026-09-30

Durable local queue/recovery, concurrency and duplicate prevention, scoped run history, usage telemetry,
resource gates and @Aedrova keyboard/click completion implemented. 276 Python tests and all embedded
PostgreSQL suites pass; package/signature/secrets checks pass. A real Codex attempt wrote the feature
and passed four generated tests but reached provider quota before its final success result; complete
live M8 provider acceptance remains unverified. No new SQL or OAuth setup. See milestone-8-execution.md.
The owner separately authorized an agent-working UI and component/menu consistency follow-up after M8.
At this earlier handoff M9 had not started; see its latest delivery record below.

## Agent working UI delivery — 2026-09-30

The owner’s separately authorized follow-up adds Codex-style public agent updates and expandable
commands/files, elapsed time, shimmer and distinct terminal states in chat; account/workspace/message
menus and the remaining DM selector now share Aedrova’s themed controls. See agent-working-ui.md.
The remainder of the dashboard and branding retain their existing layout. At this earlier handoff M9 had not started; see its latest delivery record below.

Final combined M8/UI regression: 282 tests passed, database suites passed, both-theme synthetic
visuals and resize checks passed, package launch/signature/baseline secret checks passed. See
agent-working-ui.md. The live Codex quota limitation is recorded in milestone-8-execution.md.

## M9 implementation and local verification — 2026-09-30

The owner approved the separate Python website and Stripe/managed AI work. Prices: $10/week,
$49/month and negotiated enterprise; delegated initial allowances: $1/week, $10/month, one run
per workspace, no automatic overages. Optional explicit $10 credit purchases provide $5 usage.
Implemented private billing ledger, signed/idempotent/canonical webhooks, allowance/credit
reservation and reconciliation, provider gateway, ephemeral desktop access, fresh membership
checks, usage/settings, public app configuration, original Aedrova naming, actual desktop site
captures, five-second scenery rotation, and installer/notarization tooling. Codex and Claude
runtimes are bundled; managed builds never fall back to a customer's personal provider login.

294 desktop tests and 72 website tests pass; existing PostgreSQL suites and new private billing
DDL validation pass. Installed runtimes completed local file writes through loopback protocol
fixtures. Preview package/DMG, both-theme smoke, signature and baseline secret checks pass.
These are not live paid-provider, real PostgreSQL concurrency, Stripe, website OAuth or public
signing acceptance. Owner setup instructions are required before calling M9 or the paid beta
live-ready. Website remote is connected; no push/deployment occurred. No M10 work was started.

## Domain deferral — 2026-10-01

Custom domain purchase, DNS setup and final production URL configuration move to
M11 release preparation. They do not block M10 meetings or local feature work.
M9 live acceptance remains pending; localhost development can continue, and a
stable host-provided HTTPS staging URL can be evaluated separately if needed.
OAuth redirects, Stripe webhooks and desktop managed origin must use the actual
chosen environment URL and be reconfigured and verified before public release.
No deployment, public checkout activation or M10 implementation is authorized
by this roadmap adjustment alone.

## M10 started — 2026-10-01

Implemented channel-scoped meeting/consent SQL, guarded room credential issuance,
client credential validation, fail-closed capture permits and a two-peer synthetic
media acceptance harness. Calls, device capture, transcription and meeting-to-agent
retrieval are not yet available. LiveKit Cloud project configuration and the meeting
SQL migration are the next owner actions; see milestone-10-meetings.md. The final
media client must pass the architecture's two-participant gate before integration.
Do not start M11 or mark M10 complete based on these foundation checks.

M10 live transport follow-up: corrected LiveKit credentials pass two-peer synthetic
audio/camera/screen-share reception, Qt pixel checks and forced TURN relay. Owner
confirms applying meeting SQL. Native physical capture/playback, echo handling,
reconnection, participant revocation and consented transcription/retrieval remain
required before calls can be advertised or M10 marked complete.

M10 task 1: native local meeting-device setup is implemented. Camera/screen preview,
microphone meter and generated speaker tone require explicit enablement; device
cleanup and stale callback protection are covered by automated tests. Packaged macOS
usage descriptions and release device entitlements were added. Owner hardware
permission/preview verification remains required; see docs/milestone-10-meetings.md.
Do not start the next task (real-device media validation and channel call connection)
without the owner's permission. M10 is not complete and calls remain gated.

M10 task 2 code: candidate native channel calls and durable Cloud access revocation
are implemented and tested with synthetic media; 356 desktop and 96 backend tests
pass. Live Cloud worker video/removal/cached-token rejection passed. Physical device,
echo, true network reconnect and hosted two-account acceptance remain open. Keep
meetings disabled pending owner device preflight; continue this approved task's live
validation when ready. Do not start transcription/AI meeting context without asking
after call validation. A separate supervised lease guard is required for production.

### Profile customization (before M14)
- Added three-step personal profile onboarding and account/settings editing: avatar,
  display name, username, bio, job title, custom status/emoji and availability.
- Shared names, profile cards, username mentions and private chat avatars integrated.
- Owner must apply `202610050001_user_profiles.sql` after chat collaboration SQL,
  then restart and validate a real avatar/profile update. Local tests do not assert
  hosted completion. Exact Shotbase onboarding replication awaits an optional recording.
- M14 remains gated by release requirements; Apple Developer enrollment is the active
  owner step. No website deployment or GitHub push is part of this profile change.

### Call bar navigation refinement (before M14)
- Replaced Meetings tab with a compact phone/video/options bar in the chat header.
- Audio/video entry points join the existing channel meeting transport and request
  only the corresponding devices; mute choices survive reconnects.
- Active calls show Join labels and participant counts. Announcement join cards,
  device checks, announcement settings and transcript history remain accessible.
- No new migration or owner configuration required for this change. Existing meeting
  service and macOS permissions still apply. M14 enrollment gate remains unchanged.

### Reaction latency fix (before M14)
- Added immediate shared reaction feedback, coalesced rapid toggles, targeted server
  confirmation and priority over background work.
- Slow polling preserves pending intent; failed saves roll back without clearing chat.
- Covered delayed requests, rapid toggles, failure recovery, counts, priority and logout.
- No new migration or owner setup required; M14 release enrollment gate stays unchanged.


### October 5 — simulated introduction replacement

The five-stage Zen introduction replaces the guided setup. Permission/device/project
configuration is deferred to feature settings; completion does not grant authority.
See `docs/zen-onboarding.md` for integration and animation limits. No SQL or new
owner credentials are required. M14 enrollment/release work remains a separate gate.


### October 5 — white onboarding with guided configuration

Expanded the introduction into 12 screens and real optional profile, appearance,
project/workflow, GitHub and meeting-device setup. Saved grants remain explicit,
scoped to the account/workspace, and do not start work. See `docs/zen-onboarding.md`.
No new SQL is required. M14 Apple enrollment/release setup remains separate.

## October 7 — Startup Pulse command center

Implemented the workspace Pulse surface over Dots: cached authorized source evidence,
GitHub engineering observations, period filters, drill-down, pin/order, source-backed
changes, central-agent investigation and conversation/build drafts. See `docs/pulse.md`.
No new Supabase migration. GitHub App consent/server configuration and live acceptance
remain required. Business/product analytics need real provider adapters; unavailable
figures stay hidden. Next staged adapter: Stripe, then Supabase/PostHog, Vercel/Linear,
then supported comparisons/anomaly insights and approved action workflows. Obtain owner
permission before each next implementation task. M14 remains deferred until feature work.

### Pulse dashboard design refinement — October 7, 2026

Implemented the owner's analytics-dashboard reference in the native Pulse page:
responsive metric summaries, source filter, chart/records switch, hover interval
readouts, source health and recent activity. Existing Dots and agent workflows are
preserved. The paid OpenAI key is owner-held and still needs secure server setup;
this change does not enable provider spending or deploy the website.

### Instant message delivery and OpenAI setup — October 7, 2026

Outgoing channel messages/replies paint their local echo before deferred network
dispatch. New tail messages insert incrementally rather than resetting the feed.
A 260 ms scale/fade/upward animation follows the existing Reduce Motion setting.
Pending transport stays in the background; failures retain the visible retry state
and recoverable draft, and acknowledgments preserve subsequent typing.

Secure OpenAI-only server setup is prepared in the website repository. Owner-held
credentials are absent from current server environment files. Run the hidden-input
`Aedrova_site/scripts/setup_openai.py` command, then reply ready. It verifies model
access without paid inference, writes the Git-ignored key file with 0600 permissions,
and leaves activation explicit. Workspace allowance and included-mode desktop live
acceptance remain required before claiming the OpenAI connection is operational.
No new SQL, deployment or public checkout activation is part of this task.

Validation: all 646 desktop tests and all 289 shared-server tests pass. Focused
checks cover slow transport, immediate echo before dispatch, draft preservation,
no duplicate acknowledgment, stable message grouping, reduced motion and replies.
OpenAI setup tests cover read-only model probing, provider failures, private file
permissions, OpenAI-only configuration and explicit loopback activation. Rebuilt
preview passes deep/strict signature verification and packaged launch smoke.
Live paid inference remains untested until the owner installs the server key.

### Local managed OpenAI acceptance — October 7, 2026

Owner credential setup completed. Actual model access and paid Responses requests
passed. Fresh Google authorization, a workspace-scoped gateway token, and the
bundled Codex runtime successfully created and verified a local proof file in an
isolated temporary Git project. No user project changes were applied or published.
The signed preview now uses included AI at loopback port 8090; no provider key is
bundled. Production deployment and Claude provider activation remain pending.

Aedrova showcase (`6047c111-9eda-477d-a0d1-e9d5d831227e`) has an owner-only $2
local development allowance, expiring after 24 hours, with one concurrent build and
no automatic replenishment. It is explicitly not a Stripe subscription. Usage was
reconciled with no outstanding reservations. This grant is disabled for production,
public origins, PostgreSQL, checkout and release configurations. Other workspaces
need a separately reviewed allowance; other accounts cannot spend this grant.

Validation: 646 desktop tests, 298 server tests, lint, packaged launch smoke and
strict/deep signature verification passed. Actual authenticated gateway and local
file creation passed. Interactive in-chat acceptance still needs the owner's
chosen project and a task in the funded workspace. No new Supabase SQL is required.
Next proposed task: validate real AI teammate assignments and connector evidence
against this OpenAI connection, then configure a chosen useful workspace for the
owner. Request permission before starting that task; M14 remains deferred.

### October 7 — stray participant window removed

Fixed the unused participant label's ownership: it is now a hidden child of the
channel header. Removed the resize handler that exposed it as a standalone window.
This prevents the blank “Your team” popup during account launch and resizing.
Added a regression check for parentage, top-level window enumeration and visibility
across wide/narrow resizing and account launch. Rebuilt the signed preview; account
launch smoke and strict/deep signing checks passed. Already-running older instances
must be quit and reopened to load the replacement binary; no SQL or credentials.

### Buds refinement — October 7

- Dots presentation renamed Buds; stable IDs, routes and grant boundaries retained.
- Four-step setup, editable role/instructions, planet/moon/ringed styles, custom colors.
- Draft saving separated from actual GitHub authorization; no simulated Connected states.
- Local launcher enables Buds and loads optional ignored connector credentials.
- Empty meeting announcements hidden; neutral charcoal dark theme.
- Additive SQL: `202610070002_bud_profiles.sql`. Owner must run before hosted notes work.
- Next: real GitHub Bud connection and permission/revocation acceptance, then Stripe
  source adapter and Pulse revenue evidence. Require user permission before starting.

### Bud sculpted artwork refinement

- Reference-derived six-character atlas integrated into the native shared renderer.
- Independent appearance tiles and role matching; body tinting cached, no idle API costs.
- Appearance persistence uses additive `202610070003_bud_appearance.sql`, after profiles SQL.
- Existing per-user tool grants, access checks, versions and mention identifiers retained.

### Bud onboarding visual refinement

Reference-led six-step native configuration with warm-white/charcoal material,
image-led appearance choices, compact color configuration, purpose guidance,
real tool authorization, reduced-motion-aware fades and retained drafts on Back.
No new SQL or external setup is introduced by this UI-only change. Owner reports
the previously requested SQL ran; live GitHub OAuth acceptance remains pending.

### Bud specialty connector rollout

- Delivered: six explicit specialties with persisted optional purposes, independent
  character appearance, and curated primary/additional connector recommendations.
  Setup labels availability accurately; no SQL change for presets.
- Next task, approval required: support multiple individually authorized connections
  per Bud (additive schema, encrypted per-user grants, resource scopes, revocation,
  isolation tests). Keep legacy single-provider profiles compatible.
- Adapter order: validate GitHub live; Figma/Notion/Google Drive; Supabase/Linear/Vercel;
  Stripe and aggregate finance tools; approved Search; social analytics followed by
  Instagram/TikTok publishing with explicit approval; supplementary tools afterward.
- Product reuses approved connectors across domains; role suggestions confer no access.
- Owner/provider setup and real acceptance tests are gates for each adapter. No fake
  connected states. M14 remains after remaining feature work.

### Bud connector implementation and gallery — October 7

Delivered locally: reference-led categorized connector gallery, role suggestions,
search, multiple per-user encrypted resource grants, and ten read-only adapters
(GitHub, Supabase, Figma, Notion, Stripe balance, Instagram, TikTok, Brave Search,
Vercel, Linear). Existing GitHub OAuth remains compatible. AI tool selection uses
individual connection IDs and rechecks authorization after reads/reasoning.

Owner required: run `202610070004_bud_connectors.sql` and authorize a selected
provider through its masked token field. Live acceptance and public deployment are
pending. Social app consent/review and general OAuth refresh remain future work.
See `docs/bud-connectors.md` for exact scopes and limitations. Additional preset
tools remain unavailable until their adapters ship; roles never confer access.
Next task, approval required: live acceptance and guided OAuth connections. M14
remains deferred until remaining features are built and validated.

### Fullscreen focus recovery — October 7

Workspace rail refresh previously showed an unparented selected button before
adding it to the sidebar. This briefly created a native top-level window, which
could steal activation and switch macOS fullscreen Spaces. Controls are now
parented by the rail layout before visibility changes. Native Cocoa and offscreen
regression tests observe Show events during repeated workspace changes and verify
there are no transient button windows, fullscreen remains active, and composer
focus stays intact. Rebuilt signed preview; owner must quit/reopen an older running
instance to load the fix. No SQL, credentials or provider changes are required.

### Inline Bud setup connector gallery — October 7

Replaced step 5's recommendation text/dropdown form with the existing connector
gallery inside the setup panel: featured introduction, category headings, three
columns of cards, role filtering, search, and inline scrollable connection details.
The panel widens for this step and returns to its compact layout elsewhere. New
Buds save before connecting; changed profiles save before authorization so grants
are bound to the updated version. Pending verification disables navigation and
Bud switching; selecting a new Bud clears the old connection target and token.
No backend/API changes or new SQL are introduced by this UI fix. Prior connector
migration and provider authorization remain necessary for real connections.
Guided OAuth work is already approved; live owner credentials remain a separate
acceptance gate. M14 stays deferred.

### Guided Bud account connections — October 8

Delivered locally: confidential browser OAuth for GitHub Apps, Figma, Notion,
Supabase Management API and Linear; same-Google-account browser binding, PKCE
where supported, single-use expiring encrypted state, real verification reads,
automatic encrypted refresh and grant lifetime enforcement. The native gallery
shows account sign-in only where supported and configured, saves profile changes
before authorization, polls completion without stealing focus, and updates the
Bud shelf/composer immediately. Scoped token connections remain for all ten
read adapters; social native OAuth and external writes remain future work.

Owner gate: register provider apps and put their ID/secret pairs in the server’s
ignored `.env.dots`; then perform live consent/read/refresh/revocation acceptance.
Start with one private GitHub App and a selected test repository. None of the
five credential pairs was populated at handoff; no live success is claimed.
The existing 202610070004 connector migration remains a prerequisite, with no
new shared SQL for OAuth. Exact steps: server checkout `docs/bud-oauth.md`.
No push, deployment or waitlist-mode changes. M14 remains deferred.


### GitHub Bud live acceptance and meeting focus — October 8

Owner created/installed the private GitHub App and saved its local credentials.
Live OAuth authorization, repository reading and capped local AI admission passed.
The owner confirmed the rebuilt Bud replies now work with the configured identity,
and confirmed the meeting announcement parenting fix resolves fullscreen focus loss.
The connection confirmation page now includes the Bud and a separated checkmark.

Remaining connector acceptance: real refresh/expiry/disconnect tests and each other
provider’s registration/consent. Next proposed task, permission required: connect
Supabase to the Builder Bud and validate the combined GitHub/Supabase workflow.
Current Supabase adapter reads project metadata only; database rows and schema
access must not be advertised as implemented. Designer Figma/Notion acceptance and
Finance Stripe/Pulse evidence follow. M14 remains the final release gate.

### Role-filtered connectors and unified confirmations — October 8

Approved implementation completed: the gallery defaults to each Bud’s specialty,
including unsaved role changes; explicit All tools overrides survive refresh.
All ten supported read adapters retain real verification. Token connections now
show an inline Bud confirmation; OAuth and legacy GitHub callbacks share the
same browser confirmation design with service-specific capability text.
GitHub live acceptance passed previously. Supabase, Figma, Notion, Linear and
other provider accounts still require credentials/consent and live acceptance.
Next owner requirement: register a Supabase OAuth app with Projects Read only
and the local /buds/oauth/supabase/callback redirect. This blocks live Supabase
Bud access; it does not block the completed UI or require another migration.

Validation: desktop full suite 686 passed; service full suite 367 passed.
Changed-file lint, strict/deep preview signing verification and packaged smoke
passed. Light/dark native confirmations visually reviewed. No public deployment.

### Resource ID help and Supabase HTTPS gate — October 8

Added inline resource lookup instructions for all ten supported connectors.
Supabase credentials are configured, but its provider rejected HTTP localhost
redirects. Supabase OAuth now explicitly requires HTTPS and blocks invalid
starts before creating state. Other loopback providers and scoped-token readers
are preserved. Next owner action is approval/configuration of an isolated HTTPS
connector service, then registering its exact Supabase callback. The public
waitlist website remains unchanged. Focused validation: 29 desktop and 69
service tests passed; changed-file lint passed. Live Supabase remains pending.


### Bud-led onboarding and simpler connector setup — October 9

Research now defaults to teal in the app, matching the website. Website Buds are
immediately below the hero and appear above inner-page content. Control tours
illuminate actual controls without an external outline. Completing first-run
onboarding opens the six-step Bud configuration and requires a saved Bud with
one verified connected tool before workspace handoff. Cancelling returns to setup;
existing completed accounts retain access.

Configured OAuth is the primary connector path, advanced tokens are collapsible,
TikTok selects the authorized account automatically, and GitHub/Figma/Notion/
Supabase resource links are parsed locally. Provider consent and selecting a
specific authorized resource remain intentional. Token-only adapters still need
the provider’s scoped key; unconfigured OAuth requires developer registration.
The account-mismatch browser page is branded; API authorization remains strict.

### Planned: Marketing Bud media studio (after connector acceptance)

Build image generation with OpenAI and a separately evaluated video provider.
Use brand references, platform aspect-ratio presets and explicit drafts; show
progress, cancellation and preview before download or publishing. Enforce plan
budgets, reserve estimated costs, cap video duration/quality and concurrency,
and never promise unlimited media. Separate read-only social connectors from
publishing grants. Require approval for every external post. Validate failed
jobs, refunds of unused reservations, retention/deletion and content safety.
Advertise only capabilities delivered and tested. No media generation added yet.

### Planned: final Beta completion and M14 release gate

Finish connector consent/refresh/revocation and role acceptance; then run a
full regression, permissions/privacy audit, onboarding light/dark/responsive
checks, multi-account collaboration and two-device meeting acceptance.
Create signed/notarized macOS DMG with clean-machine install/update/rollback
checks. Add Windows packaging on Windows CI, signed installer, clean-machine
acceptance, microphone/camera/screen-share and updater checks. Resolve platform
incompatibilities before advertising Windows availability. Archive reproducible
artifacts and release notes; maintain waitlist until release approval.

Owner actions later: Apple Developer membership and Developer ID signing setup;
Windows signing provider enrollment; Render always-on paid hosting; live Stripe
business verification and billing configuration; second device for meetings.
Walk through one requirement per response at release time. These gates block
public Beta distribution, not current UI work. Codebase walkthrough stays after
complete deployment. M14 remains deferred until feature completion.

### Connector and required Bud onboarding validation — October 10

Owner approved this validation task. Full desktop suite: 701 passed. Full website /
service suite: 391 passed. After routing fixes and additional onboarding coverage,
71 focused desktop tests passed; lint and whitespace checks passed.

Fixed addressed Bud routing for names matching Aedrova / the central agent nickname,
and for a short recipient name followed by a longer Bud name in the request. Explicit
Bud tokens retain identity. Central-agent requests with incidental Bud mentions keep
their existing routing. Added verified-tool onboarding acceptance tests: final-stage
handoff required, disconnected/error/revoked grants rejected, edited Bud settings rejected.

Live UI acceptance confirmed existing Google sign-in returned to the desktop and
hosted Bud setup loaded. Earlier GitHub, Supabase, Figma, Notion and TikTok sandbox
reads remain recorded evidence, not fresh refresh/disconnect acceptance. Existing
Pebble/Orbit grants were not located in the inspected signed-in workspaces. Fresh
Google-account onboarding and live source-backed Bud responses remain pending.
No production grant was forcibly expired or disconnected for this test pass.

Owner required now: reopen the rebuilt preview, sign in with the Google account
owning Pebble/Orbit, select the workspace containing those Buds, and leave it open.
This identifies the existing grants for live read/refresh validation without broader
permissions. A new provider consent requires explicit approval at the consent step.
No new SQL is required. Stripe/Instagram/Brave/Vercel credential and consent gates
remain as detailed in docs/bud-connectors.md. Do not claim connector acceptance or
fresh-account acceptance complete until their live checks pass.

Marketing media studio and final Beta/DMG/Windows work remain planned, not started.
M14 remains deferred. Continue this acceptance task after the account/workspace is
identified, then report and request permission before the next feature milestone.

### Sign-in-first Bud connections — October 10

Owner authorized simplifying the connector experience. GitHub, Supabase and
Notion now offer named resource choices after browser OAuth; TikTok selects
its authorized account. Figma uses sign-in followed by a file link. Tokens/IDs
are removed from the normal pre-login flow, with token setup available only
under an explicit advanced option. No broader provider scopes or SQL changes.

398 website/service tests and 56 focused desktop checks passed. Connector
service branch contains the selection API and private temporary-token handling.
Real post-consent discovery/selection remains a live acceptance gate; these
checks do not certify all provider registrations for public customers.
Owner required now: quit Aedrova (⌘Q) and reopen the rebuilt preview at
`/Users/ayanshvarma/Documents/Aedrova/dist/Aedrova.app` to use the new flow.
Stripe, Instagram, Vercel and Search still need outstanding provider support /
setup before login-only connections can be offered. M14 remains deferred;
request owner approval before the next feature milestone.

### All-provider sign-in workflow — October 10

Owner requested completing the login-first experience for every existing connector.
Added Stripe Apps OAuth and Instagram Login with automatic account binding, plus
Vercel integration OAuth with a named project picker and team-scoped reads. Existing
five OAuth connectors remain intact. Search uses an authenticated Enable web search
flow, an owner-funded server key and durable global/workspace daily caps; there is
no fabricated Search OAuth. Personal token paths remain an advanced fallback.
Confidential exchanges, grant lifetimes, read verification and inline confirmations
are preserved. Managed grants store no shared key. No new SQL migration.

Local validation: 411 service tests; 57 focused native tests; rebuilt desktop and
verified its deep code signature. Live account acceptance is NOT complete: Stripe
stops at owner passkey/2FA, Meta requires developer registration, Vercel requires
new app registration/terms, and Brave Search requires a funded key. Registration,
review, live token renewal/revocation and fresh customer grants remain blockers.
Exact setup: ../Aedrova_site/docs/account-connector-setup.md. First owner action is
Stripe passkey verification in the prepared login tab; never send credentials in
chat. M14 and public billing/release gates remain deferred.

### Immediate connector/UI fixes and final launch roadmap — October 10

Connector service 60d532d deployed Live on Render (dep-db4v3pqd0e5s73djuas0).
Readiness returned 200; Stripe/Instagram/Vercel callbacks without OAuth state were
rejected with 403; unrelated /plans remained 404. Malformed unauthenticated Search
POST was rejected with 422 before any grant. This is deployment smoke evidence,
not provider/customer acceptance. Existing owner setup gates remain.

Fixed native connector confirmation compression with a scroll-safe minimum-sized
layout, separate Bud/check/text/button spacing and quieter embedded secondary
action. Logout queues once behind a current request and discards local identity
even if remote logout fails. New project/onboarding automatic planning defaults
on; explicit saved opt-outs and original-folder/publishing approvals remain.

Saved every owner release requirement in docs/final-beta-launch-plan.md with
traceability and gates; source phase proposal in docs/release-plan-source.md.
These phases are PLANNING ONLY. Pulse removal, billing launch, installer publication
and broad feature/security work have NOT started. M14 remains deferred.
First personal connector setup action remains Stripe passkey/Touch ID/2FA in the
prepared tab; registration/review/key/live validation gates prevent claiming all
connectors complete. No new SQL required. Ask approval before Phase 1.

Immediate-fix validation: 90 focused native tests passed; the final confirmation
subset passed all 25 checks after the visual refinement. Ruff and diff checks
passed. Rebuilt dist/Aedrova.app and verified its deep code signature. UI proof:
work/connector-confirmation-fixed.png. Source fixes/roadmap pushed as 2ae2c8f;
connector deployment evidence pushed as 8a77e33 on the website branch. The currently
running application must be quit/reopened to load these changes; no forced restart.


## Stripe customer workflow preparation — October 10

Owner deferred developer business verification and requested readiness for customer
login/account selection. Stripe App v0.1.0 is registered and approved for testing.
OAuth code binds the Stripe-selected account, verifies read access before Connected,
and returns to the Bud confirmation without customer keys or manual codes. Focused
HTTP regression tests cover successful binding, account mismatch and denied balance
access. These are local tests, not fresh-customer/live acceptance.
Aedrova developer verification, external testing, server credentials and public Stripe
review remain gates; a verified customer account cannot bypass them. This preparation
does not activate billing or public installation. Final-Beta Phase 1 is next and still
requires explicit owner approval. No Final-Beta phase was started in this task.

## Final-Beta Phase 1 — October 10 (authorized, in progress)

Owner approved Phase 1 and created Aedrova Staging (scvmvqlzcqhwrrsiahpj).
Hosted dashboard verified healthy and initially unmigrated; production/waitlist data
not copied or changed. Frozen inventory and all setup/acceptance gates saved in
`docs/final-beta-phase-1.md`. Pulse removed from app navigation/menu/module and service
routes; meeting heartbeats and stored data preserved. Native release CI added across
Linux/macOS/Windows plus real PostgreSQL migration/RLS tests. Service CI expanded to
tracked-secret, private-schema, regression and image readiness checks. Explicit staging
profiles/server guards reject known production targets and live billing/release flags.
Both GitHub repositories have secret/push protection enabled, 0 collaborators and no
branch protection/rulesets. Vendor node_modules removed from Git tracking, kept locally.
Next owner action: run work/staging/schema.sql ONLY in the new staging SQL Editor.
Private role credentials, HTTPS staging server and Google staging auth remain subsequent
setup gates. Source/local test results do not certify all connectors or launch readiness.
Phase 2/public billing/downloads/M14 not started. No staging payment/upgrade requested.

Phase 1 execution evidence: desktop a7efded and service a2b1423 pushed to their
existing feature branches. Local 725 native/409 service tests passed; both SQL suites
passed. Service GitHub CI 38078223509 passed all steps. Native CI PostgreSQL passed;
Windows test collection exposed existing Unix-only fcntl imports in ledger/retention.
Windows remains an explicit release blocker, not skipped or certified. Local macOS
preview rebuilt, signature/resource scan passed, packaged smoke confirms four pages.
Owner ran the 23-migration staging bundle successfully; hosted Table Editor verified
new app tables. Next required owner step: run the service sql/supabase-website.sql
in Aedrova Staging to create the restricted NOLOGIN role/private backend schema.
Private password, service origin and Google staging OAuth remain subsequent steps.

Owner completed the private staging role LOGIN/password SQL successfully. Actual
staging pooler login verified as aedrova_website with aedrova_billing search_path;
public.workspaces SELECT denied (42501). Separate staging encryption key and private
Render environment prepared locally, configuration validation passed. Free HTTPS
service creation and staging Google OAuth remain required; no cloud secrets uploaded.

## Staging HTTPS service — October 10

Owner explicitly approved uploading staging-only database/encryption credentials to
Render and deploying the free service. Created aedrova-beta-staging,
service srv-db58sn8473hc73a9n3qg, deploy dep-db58sn8473hc73a9n580, commit e3da1d7.
Render reports Deploy succeeded | Live. Origin:
https://aedrova-beta-staging.onrender.com. Auto-deploy off; free $0/month compute.
Fresh external GET / and /health/ready return 200 (readiness reports ready).
/auth/google returns 303 to scvmvqlzcqhwrrsiahpj.supabase.co with redirect_to
https://aedrova-beta-staging.onrender.com/auth/callback. /api/pulse remains 404.
Credentials are stored only in Render environment and ignored restricted local files.
Public staging desktop profile saved in work/staging/public-config.json; check-only
validation passed. Production origin/database credentials were not used.

Google provider is disabled in Aedrova Staging. Exact provider callback verified:
https://scvmvqlzcqhwrrsiahpj.supabase.co/auth/v1/callback.
Next owner requirement: create a separate Google Cloud project named Aedrova Staging
(Google Cloud project selector > New project > name > Create); do not enable billing.
Then configure a testing consent screen/client, test users and staging redirect URLs.
This blocks staging end-to-end login; Phase 1 remains in progress.
No Phase 2/M14/public billing/download activation. Windows fcntl remains a release gate.

Owner reports creating the separate Aedrova Staging Google Cloud project. Current
agent browser project selector (amillum account context) returns no Aedrova matches.
Requested public Google Project ID to select the correct project/account before OAuth
configuration. Do not infer that creation failed or configure amillum as staging.
Staging Render service is live; Google sign-in acceptance remains blocked.

Owner supplied Google staging Project ID aedrova-staging, number 7280065225.
Direct in-app browser project URL opens only a partially loaded Google welcome page;
API navigation aborts, so project access/consent setup not yet independently verified.
Next owner requirement: in the owner's working browser, select aedrova-staging >
APIs & Services > OAuth consent screen (Google Auth Platform) > Get started.
Set app name Aedrova Staging, a support email available in dropdown, External audience
in Testing, contact aedrovaai@gmail.com. Owner must personally review/accept any policy
agreement on creation. OAuth client/secret/allowlist and sign-in validation follow.
Do not reuse amillum/production OAuth credentials. Phase 1 remains in progress.

Owner reports staging Google consent-screen initialization completed. Next owner
requirement in project aedrova-staging: Google Auth Platform > Clients > Create client,
Web application, name Aedrova Staging Web, authorized redirect URI exactly
https://scvmvqlzcqhwrrsiahpj.supabase.co/auth/v1/callback. Keep client secret/private
JSON outside Git/chat; install directly into staging Supabase provider in a later step.
OAuth client creation, test-user enrollment, Supabase provider/URL configuration and
end-to-end login still pending; Phase 1 remains in progress.

Owner reports Aedrova Staging Web OAuth client created and staging Supabase Google
provider credentials saved. Secrets supplied directly by owner, not received in chat.
Next requirement: in Google Cloud project aedrova-staging > Google Auth Platform >
Audience > Test users > Add users, add the Google account used to test desktop login
and Save. Keep publishing status Testing. A second independently controlled tester
account will be needed for multi-user isolation acceptance. Redirect allowlist and
end-to-end login remain subsequent gates; Phase 1 is not complete.

Owner reports Google staging test user added. Next requirement: Supabase project
Aedrova Staging > Authentication > URL Configuration: Site URL
https://aedrova-beta-staging.onrender.com; redirect URLs exactly
https://aedrova-beta-staging.onrender.com/auth/callback and
http://127.0.0.1:43827/auth/**. Native code uses random PKCE callback paths under
/auth/ on the fixed loopback port; narrow path wildcard is required. Do not add
production URLs or broad domain wildcards. Owner saves this configuration.
Staging login/end-to-end isolation acceptance still pending; Phase 1 remains open.

Owner reports staging Site URL and exact web/native redirect allowlist saved.
Started isolated source staging launcher successfully (separate public-config.json and
app.ini). Existing production app shares a display name; source process was stopped
without closing the user's packaged app, avoiding accidental production sign-in.
Opened web staging /auth/google for initial OAuth return validation. Free Render
instance cold-start pending; next owner action is Google account selection/consent
in staging web login. Browser/native session and multi-user isolation not yet verified.
Phase 1 remains in progress.

Fresh staging readiness HTTP 200 confirmed after cold start. /auth/google returns
303 to staging Supabase with correct staging /auth/callback. In-app browser remains
on Render interstitial; fresh login tab redirect blocked by client. Owner handoff:
open https://aedrova-beta-staging.onrender.com/auth/google in Safari/normal browser,
select registered Google test user and complete consent; report signed in or error.
No authenticated login acceptance claimed. Native and multi-user tests still pending.

## Staging Google login — owner confirmation

Owner enabled the staging Google provider and reports successfully signing in with
the registered test user. Independent /auth/v1/settings verification confirms
external.google=true for scvmvqlzcqhwrrsiahpj. Browser session/desktop handoff has
not been independently inspected; multi-user workspace isolation remains pending.
Next owner requirement: Google Cloud project aedrova-staging > Google Auth Platform
> Audience > Test users > Add users: add a second Google account under the owner's
control and Save. This enables two-user staging isolation validation. Do not send
credentials or use a production workspace. Phase 1 remains in progress; later phases
and public billing/download activation remain gated.

Owner reports second Google staging test user added. Started a staging-only hosted
isolation probe using existing native PKCE/loopback OAuth code (no production
endpoints, session tokens kept in memory). First browser login is awaiting owner
account selection. Subsequent second distinct login is explicitly paused. Probe
will create two disposable staging workspaces/messages, verify own reads and
bidirectional foreign workspace/channel/message/member reads and message writes
are denied, then unsend probe messages and archive workspaces. This does not
certify meeting media, AI context isolation or desktop UI handoff. Phase 1 remains
in progress until actual results and other release gates are recorded.

First real staging native OAuth callback succeeded (ACCOUNT_1_SIGNED_IN). The
probe then exited with EOFError because the background command has no interactive
stdin; local test session was signed out by cleanup. Replaced stdin pause with a
bounded local signal-file wait and restarted first login. Owner must sign in again
with the original test account before the second distinct account handoff. No
isolation tests have run yet; do not treat this runner issue as a Google failure.

Restarted first staging OAuth session verified successful and retained in memory.
Released bounded signal-file pause; second staging Google sign-in opened. Owner
must choose the second distinct registered test account (Use another account if
Google selects the original). Two-user isolation probes run after that callback;
results are not yet available. Phase 1 remains in progress.

## Hosted two-account isolation result

Both real staging Google OAuth sessions succeeded and authenticated distinct users.
Created two disposable staging workspaces with one probe message each. In both
directions, each account could read its own message, and reads of the other
workspace, channel, message and membership rows returned no data. Sending a message
into the other account's channel was rejected with PostgreSQL 42501. These
specific hosted isolation checks PASSED; this is not full AI-context/security
certification or desktop UI acceptance.

Cleanup failed because the local probe sent p_id rather than p_message to
unsend_message. Helper corrected; sessions were signed out. Two disposable staging
workspaces/messages remain (no production mutations); cleanup is outstanding.
Evidence: ignored work/staging/isolation-report.json, status
isolation_passed_cleanup_failed. Do not require repeated sign-ins solely to hide
this test-runner issue.

Remote CI run 38078880708 independently verified: PostgreSQL RLS, macOS desktop
and Ubuntu desktop passed; Windows desktop failed. Existing Unix-only fcntl
imports in agents/ledger.py and agents/retention.py remain the next baseline
engineering blocker. Phase 1 is still in progress; hosted merge protections,
Windows CI and desktop UI acceptance remain gates. No owner setup action is
required immediately while engineering addresses the Windows blocker.

## October 10 — portability fixes and deferred handoff

Owner requested independent completion without setup interruptions, with owner
actions saved for the end. Added `docs/phase-1-owner-handoff.md`.

Implemented native nonblocking Windows CRT byte-range leases alongside POSIX
flock; secure final-component opening rejects Windows reparse points and POSIX
symlinks before truncation. Locks are released when streams close and descriptors
are not inherited implicitly. Execution and retention no longer import fcntl on
Windows. Build-check receipts use the same safe file opener. Added real second-
process exclusion/reacquisition, symlink target-preservation, and error-classification
tests; all six new lease tests passed in the first actual Windows runner (the full
Windows job reached 675 passing tests rather than failing collection).

Remote run 38109927599 at e5d1499: PostgreSQL and macOS passed; Linux reported
one existing agent-feed visibility bug (730 passed); Windows reported 53 failures,
675 passed and six teardown errors. These are not silently skipped. Fixed the
agent-event stack switch so the transcript is visible when it contains rows, and
strengthened its existing layout regression to assert visibility. Also fixed Windows
agent timestamps (unsupported %- modifiers), explicit UTF-8 emoji catalog loading,
and GitHub login's synchronous FailedToStart race. The updated focused suites
passed 77 tests locally; full local baseline passed 731 tests before these follow-ups.
Source/secret checks and ordered SQL/RLS/optional-meeting checks passed.

Remaining Windows failures include Unix-only synthetic executable fixtures/runtime
pipe/process handling, POSIX permission assertions versus Windows ACL semantics,
conservative retention behavior on platforms without safe rmtree, and font/layout
differences. Windows distribution and full Phase 1 sign-off remain blocked; no
Windows installer or universal cross-platform readiness is claimed. Follow-up remote
CI is required for the final revision. Owner interventions stay deferred as requested.
No production merge/deployment, Phase 2, M14 or paid download activation performed.


## October 10 — final Phase 1 baseline verification

Hosted staging setup, separate Google OAuth and bidirectional two-account row
isolation are verified. Staging readiness returned 200, Google provider enabled,
and the removed Pulse route returned 404 during this final pass. Production and
public release/billing gates remain unchanged.

Native revision 2d93e52 fixes Windows bounded provider pipe reads, process-tree
lifetime containment with a kill-on-close job, portable synthetic subprocess helpers,
filesystem-specific permission preservation assertions, conservative retention
expectations and responsive connector/account/project layouts. No tests are skipped
to claim Windows readiness. Follow-up wraps the connector gallery banner and adds a
real spawned-command cancellation regression. Full updated local suite: 732 passed;
Ruff, tracked secret-pattern and compile checks passed. Ordered migration/RLS and
optional-meeting-order checks passed. Final remote evidence is recorded below when
complete; independent code completion does not waive the owner acceptance gates.

Owner handoff: docs/phase-1-owner-handoff.md. Required to close Phase 1: source
staging desktop login/workspace/sign-out acceptance and active main-branch PR/check
protections in both repositories. Two disposable isolation workspaces remain as
optional cleanup, not a failing isolation check. Windows CI is regression evidence,
not certification of installer signing, Windows ACL privacy or live provider sandbox
behavior; those remain later-phase gates. Obtain new approval for Phase 2 only after
reporting these results and outstanding owner actions.


## Final verified result — October 10, 2026

**Independent Phase 1 engineering complete; owner sign-off pending.** Frozen
native code revision **8a98c27**, [Release candidate run 38111786891](https://github.com/ayanshv/Aedrova/actions/runs/38111786891):
all four jobs **passed**. Ubuntu **732 passed** (304.70s), macOS **732 passed**
(334.33s), Windows **732 passed** (391.76s), plus PostgreSQL migration/RLS checks.
The Windows run includes native cross-process leases, bounded pipe handling,
process cancellation including spawned commands, and compact layout checks. No
Windows tests were excluded to achieve this result. Local final suite **732 passed**
(103.65s); source/secret-pattern/compile checks and ordered SQL/RLS/optional-meeting
checks passed. CI evidence is retained in job artifacts; local copies/report are
ignored under work/staging.

Service companion revision **1a183ff**, [Website checks run 38111715356](https://github.com/ayanshv/Aedrova-website/actions/runs/38111715356):
**passed**, including backend regressions, private PostgreSQL access/lease checks,
container build and startup/readiness. Only documentation differs from deployed
staging service **e3da1d7**; auto-deploy is off. Production remains unchanged.

The final evidence/documentation commit changes no runtime or test code and does
not rerun the unchanged tested baseline. These are baseline regression results,
not live connector/model/meeting or signed-installer certification.

To fully close Phase 1, the owner must confirm (1) source staging desktop Google
return, workspace entry and sign-out acceptance, and (2) active main-branch PR /
required CI / no force-push / no deletion protections in both repositories. Exact
commands, check names and locations: docs/phase-1-owner-handoff.md. Staging fixture
cleanup is optional housekeeping. No new payment, production secret, production
merge/deploy, public billing/download activation or Phase 2 execution is required
or authorized by this result. Phase 2 remains permission-gated after this handoff.

## Owner confirmation and Phase 2 authorization

October 10, 2026: owner reports both required actions completed (staging desktop
acceptance and GitHub main-branch rulesets) and explicitly approves starting Phase 2.
Phase 1 is closed on that owner acceptance; this is not a separate automated
re-inspection of the desktop journey or hosted rulesets. Phase 2 connector/provider
validation is now authorized. Public launch, production merges, billing/downloads
and later phases remain gated. The subsequent Finish later fix passed 55 focused
Bud/onboarding tests and is included in the source handoff.

## Final-Beta Phase 2 — authorized and started

Owner confirmed Phase 1 desktop acceptance and both main-branch protection actions,
then approved Phase 2. Initial connector/provider audit and implementation evidence
are in docs/final-beta-phase-2.md. Native connector checks:72 passed; service:426
passed. OpenAI metadata access verified without inference. Anthropic private setup
and explicit local opt-in implemented; its actual key/model/inference acceptance
and fresh-customer connector lifecycle/provider registration gates remain open.
Next owner requirement: private Anthropic setup. Later phases remain gated.

### Phase2: Anthropic verified; Stripe owner form prepared

Anthropic private setup/model access verified (metadata only, no inference). Initial
Phase2 native and website CI green. Corrected Sonnet5.5 cache-read pricing and
blocked client-selected premium inference modes outside metering. Service430 tests
pass locally. Stripe external testing remains business-verification blocked. Open
owner form: Settings→Business→Business details→Edit. First step is completing
industry, website and product description privately. Full evidence in Phase2 doc.

### Stripe business information saved — service agreement handoff

Owner reported saved; dashboard independently confirms business website
https://aedrova.com, public name Aedrova, and industry/product description provided.
Business information no longer shows Incomplete. Opened Service agreement → Review
without submitting. Next owner requirement: review the Stripe Services Agreement
and Acquirer Disclosure in the open Terms of service modal; click Continue personally
only if authorized and in agreement. The modal also includes consent to Stripe text
messages and a representation that business information is complete/correct. No
agreement accepted by the agent. Representative/public details/descriptor still
incomplete; full verification and Stripe external testing remain blocked. Phase2
is active; no later phase or live billing enabled.

### Stripe agreement completed — public support details handoff

Owner reports agreement done; independent dashboard observation shows Service
agreement no longer listed as Incomplete. Opened Public details → Edit public
details → Add customer support details without entering/submitting fields. Next
owner requirement is to complete truthful support phone/address/email/URL and
applicable published privacy/terms URLs, then Save personally. Business name and
website already show Aedrova/https://aedrova.com. The form defaults to showing the
support phone on receipts/invoices; owner must choose the appropriate public
contact information. Representative and descriptor remain Incomplete. Full Stripe
verification/external testing and Phase2 acceptance remain open; no billing enabled.

### October 11 — public policies/support update authorized

Owner authorized replacing website Privacy/Terms, adding Customer support with
(408) 634-5254, pushing/merging the website update as needed, and entering/saving
https://aedrova.com/privacy, /terms and /support in Stripe. Isolated website PR4
uses codex/legal-support-refresh from main to avoid publishing unfinished connector
changes. Local website suite392 passed. Documents describe conditional Beta features
and actual privacy/connector limits; no legal-compliance guarantee or fabricated
company identity/address. Paid-launch legal/business review remains a gate.
Publication and Stripe Save verification will be recorded after checks complete.

### October11 — policies live and Stripe URLs saved

Website PR4 https://github.com/ayanshv/Aedrova-website/pull/4 merged after green
CI38120908946; main commit8bb942d, mainCI38121001131 also green. Render website
srv-db0a8o7avr4c73eqcj4g auto-deploymentdep-db5jhsmk1f9s73eeecdg succeeded.
Live browser verification confirms new Privacy/Terms effectiveOctober11 and Support
with authorized phone(408)634-5254. Waitlist retained; release/billing gates untouched.
Current website development branch integrates the same pages:431 tests passed,
tracked secret check passed.

Entered https://aedrova.com/support, https://aedrova.com/privacy and
https://aedrova.com/terms into configured Stripe form and clicked Save under explicit
owner authorization. Modal closed; Customer-facing information no longer Incomplete
and saved Terms plus other provided URLs appear. No private address guessed/entered.
Stripe still marks representative/statement descriptor incomplete. Active Account
status task: Provide an external account; Stripe says no bank account on file.
Opened task details, no bank information entered. Next owner requirement: click
Start on this task and provide their valid bank account privately/personally.
This is Stripe account readiness, not evidence of full connector external-testing
acceptance. No later milestone started. Legal/business identity and jurisdiction
review remain required before paid public Beta; policies are not a compliance guarantee.

### October11 — current public contact email

Owner changed public contact/support email to contact@aedrova.com. Website
Support, Privacy, Terms, footer and setup guidance updated in isolated PR5.
Historical Phase1 Google registration evidence retains its original account value.
Stripe already shows contact@aedrova.com; no additional Stripe edit is needed.
Next owner requirement remains the open Stripe external bank-account task.

### October11 — team pricing / shared Space implementation authorized

Owner is completing Stripe bank setup and authorized unmistakable per-team pricing
plus attached independent Space/nested subspace requirements, source pushes/merges.
Implemented within existing architecture; see docs/space-billing.md for exact
migration, flags, Stripe presentation and activation gates. Paid prices unchanged,
waitlist retained. New migration needs owner execution in Aedrova Staging before
root sharing is enabled; no fixture or production reset. Cluely footer/legal-depth
study explicitly deferred to Phase5 in the launch plan. Stop after this task and
ask whether the owner finished Stripe bank setup; do not begin another phase.


## October 11 — owner defers remaining Stripe setup

Owner explicitly deferred remaining Stripe account/bank configuration until release
preparation, immediately before packaging and launch. Stop recurring bank-setup
prompts until that gate. Continue non-Stripe connector/provider work under existing
Phase 2 authorization; this deferral does not certify their outstanding live
acceptance or mark Phase 2 complete. Stripe Bud external-customer acceptance remains
a distinct deferred gate from Aedrova subscription billing. Complete both at the
release-preparation checkpoint, alongside Phase 6 billing lifecycle acceptance,
before Phase 8 final packaging/release sign-off or Phase 9 paid launch. Public
checkout and downloads remain gated and the website stays waitlist-only. Phase 3
(meetings, voice and file context) remains the next major phase and requires owner
authorization before implementation starts.

## October 11 — Phase 2 checks and explicitly requested meeting wrap-up

Owner approved Phase 3 following non-Stripe checks, then directly requested an
editable end-of-meeting transcript screen with Confirm. Implemented this specific
feature under that direct authorization, while leaving Phase 2 live provider gates
open. See docs/final-beta-phase-2.md for fresh native/backend, runtime and credential
metadata checks and the prepared, unsubmitted private Vercel connector registration.
See docs/final-beta-phase-3.md for the new owner/admin wrap-up screen, atomic review,
empty-room closure, consent preservation, local SQL/HTTP/native verification and the
exact required staging migration. No Stripe setup, paid launch, production migration
or release activation occurred; remaining Phase 3 voice/file work is not complete.

Final verification: 739 desktop tests and 441 development backend tests passed.
All embedded PostgreSQL migration/RLS scripts passed, including the new wrap-up
closure/permission/atomicity/consent tests. Scoped application lint, tracked-secret
checks and whitespace checks passed. Both native theme captures were inspected.
Source delivery is to existing development branches only; no production auto-deploy
or hosted migration is initiated by this checkpoint. Owner next action: run
`supabase/migrations/202610110002_meeting_wrapup.sql` once in Aedrova Staging's SQL
Editor, then report success for the matching staged deployment/live test.

Final follow-up handles an admin leaving seconds before the last participant:
bounded, server-authorized background polling (up to 60 seconds), cancelled on
account/workspace/new-call changes or destroyed windows. The final follow-up passed
39 focused native call/header/speech/wrap-up checks, lint and a rerun of all actual
embedded PostgreSQL migration/RLS scripts. The full 739-test run above predates
this one added polling regression test; it is not claimed as a 740-test full run.


## October 11 — wrap-up staging migration and deployment verified

Owner reported success running the new wrap-up migration in Aedrova Staging.
Read-only public PostgREST probes resolve both `meeting_wrapup_status` and
`confirm_meeting_transcript`, returning 42501 permission denial to unauthenticated
callers rather than missing-function errors. This confirms function installation
and anonymous execution denial, not authenticated hosted behavior.

Manually deployed backend commit `1149e72` on existing free service
`srv-db58sn8473hc73a9n3qg`; Render deploy `dep-db65s4h42hec73b13mp0` visibly succeeded.
`/health/ready` returns 200 ready. Matching native source commit `31e2ec8` launched
through the isolated staging public profile. No production deployment or credentials
changed, no new paid service, no automatic recording or capability activation.

`/health/meetings` returns 503 unavailable and the new wrap-up endpoint returns the
configured meeting-text-disabled denial (403). Existing staging meetings, context,
and speech capability gates remain off. Hosted two-account/end-of-meeting/edit/
Confirm/withdrawal acceptance is therefore still blocked by the separately deferred
meeting API/guard/LiveKit and server speech activation requirements. Owner's SQL
step is complete; no further SQL is requested now. Paid hosting, provider costs and
physical two-Mac testing remain owner release-preparation actions as already deferred;
do not enable these gates just to make a smoke test pass. Phase 2 remains open.
Evidence: `work/meeting-wrapup/staging-deployed.png`.

## October 11 — speech grant fix verified; activation pending hosting

Owner brought meeting transcription activation forward and ran the staging-only
speech grants. Both restricted backend EXECUTE privileges and the prepared speech/
database preflight pass. Backend `ebd9f25` is pushed; source staging can opt into
meeting context without enabling it in frozen/public builds. Full checks: 743
native and 444 backend tests passed. Provider metadata access succeeds; actual
microphone transcription and two-device acceptance are not yet verified.

Required owner action now: Render → aedrova-beta-staging → Compute → Save selected
$7/month plan. Separate $7/month guard also required (about $14/month base hosting,
excluding usage/taxes). Agent prepared but did not submit either charge. Credential
transfer, hosted activation and real consent/review acceptance remain pending; do
not mark transcription or Phase 3 complete. See docs/final-beta-phase-3.md and the
backend transcription-staging-activation.md. Stripe remains deferred until release.
Additional scattered homepage Buds merged in website PR #8; waitlist mode retained.

## October 12 — owner cannot upgrade hosting yet

Owner reports they cannot upgrade Render now. Defer the staging API and independent
meeting-guard charges; do not submit purchases or enable hosted transcription.
Code, narrow SQL grants and preflight preparation are saved. Actual hosted audio,
consent/review/withdrawal and two-device acceptance remain blocked; transcription
and Phase 3 are not complete. Local implementation and non-hosted checks can
continue without this purchase. Resume hosting setup when owner is ready.

## October 12 — Phase 3 verified uploads and composer voice draft

Owner authorized upload safety and chat voice-to-text. Implemented local/server file
inspection, restricted verification-only publication, cancellable composer progress,
and existing storage/quota controls. Owner ran 202610120001_verified_uploads.sql in
Staging; restricted backend EXECUTE verified. New microphone controls in channel/thread
composers use explicit permission, reactive level feedback, editable results and no
automatic send. Dictation has its own server capability and bounded plan accounting;
it does not require paid meeting hosting. See docs/final-beta-chat-media.md for limits,
tests and activation/manual gates. Do not mark Phase 3 or physical speech acceptance
complete; production/public release and meeting gates remain unchanged.

Staging activation follow-up: owner explicitly approved the existing OpenAI key
transfer and bounded Free chat dictation. Render 36aba62 deployed successfully on
the existing free service; health ready 200 and unauthenticated capability denial
403. The existing disposable Beta isolation 1 eb8958 workspace activated Free in
its authenticated owner UI (100% capacity, 0/40 requests). Matching source app
launched against staging. Owner native sign-in/physical speech and actual hosted
upload/provider acceptance still pending. No payment, meeting activation or
production change occurred. Both repositories are pushed; Phase 3 remains open.

### Bud personality, motion and defer handoff — October 12

Seven-step Bud setup now includes continuous working-style controls and custom
personality text. Existing versioned instructions persist settings; read-only answers
and Builder prompts apply them. Reporting preferences throttle optional prose during
active work only. Eye-only blinking covers native Bud surfaces and website placements,
with reduced-motion support. Explicit Finish later resumes the controls highlights
rather than leaving the intro blocked; setup is recorded as deferred, not authorized.
See `docs/bud-personality-and-motion.md` for limits and required source-preview restart.
Phase 3 live microphone/upload acceptance and earlier deferred hosting gates remain.

### October 12 — live media acceptance and macOS source-launcher fix

Owner signed in. Actual staging native upload publication passed hosted verification;
malformed PNG and 10 MiB + 1 byte input were rejected without chat publication. New
session retained the verified attachment. Microphone format is supported. Live start
exposed missing macOS usage descriptions in the plain Python source launcher. Fixed
run_staging.py to create a local staging-only source bundle; corrected app launches,
signs in with existing Google session and reaches microphone permission. Owner's real
recording/Done handoff is pending. No SQL/payment/key setup required. More live media
and Bud acceptance remains; do not mark Phase 3 complete. See phase-3-live-acceptance.md.

### October 12 — owner switches chat microphone to voice messages

Owner requests iMessage-style recordings instead of speech-to-text. Default composer microphone
now records locally, previews, and explicitly sends a bounded private WAV attachment; inline
playback uses existing verified download/access controls. No transcription/API credits consumed.
Owner reports staging 202610120002_voice_messages.sql installed. Matching backend deployment
and actual voice send/playback acceptance remain required. Original optional dictation module
is retained but not mounted in the composer. No meeting or production activation.
See docs/voice-messages.md. Fixed macOS source permission bundle, native audio enum callback,
and background-result delivery after Qt shutdown during live testing.

Voice follow-up: local capture uses the microphone's native format with continuous
conversion/resampling; duration is five minutes within the existing 10 MiB upload cap.
Matching staging backend e375bdc is Live. Owner sent revised eight-second recording and
reports distortion mostly gone; publication/persistence and text preview passed. Residual
audio quality, other live acceptance cases and Phase 3 remain open. No owner SQL/key/payment
step is required for this voice update. No production or meeting activation.

### October 12 — Phase 3 hosted media acceptance continued

Private-channel threaded synthetic upload/download and both cancellation boundaries
passed live staging. Fixed cancellation RPC missing from client allowlist. Fixed native
accessible Bud appearance selection so the actual specialty follows its artwork;
all six role paths covered. Native Finish later returned to chat; full tour handoff
and model personality acceptance remain open. Native suite 779 passed; lint, secret
scan and diff checks pass. Remaining required-now action: sign in with a second,
distinct staging Google test account in Safari's explicit chooser to finish file
isolation acceptance. No production activation, paid hosting or Phase 4 start.
See docs/phase-3-live-acceptance.md for exact remaining gates and probe instructions.

### Phase 3 acceptance follow-up — second-account credential handoff

Owner reported second-account sign-in, but the old Supabase OAuth state expired.
Fresh hosted run passed private-thread upload/download and both cancellation checks
again. Second account is signed out in Safari; Google requires its password and no
existing autofill completed it. Required owner action: complete that Google sign-in
privately (or request a fresh link if expired). Foreign-workspace/private-channel
isolation, physical playback/quality, required-Bud tour handoff/model behavior and
meeting hosting acceptance remain open. No Phase 4 execution authorized yet.

## October 12 — Phase 4 approved; grouped mentions and compact UX

Owner approved starting Phase 4 while Phase 3 acceptance remains open. Implemented
one grouped mention catalog for typed search and the toolbar: Agents, configured
Buds, People and channel notifications, with keyboard selection and existing routing.
The inline window-child picker sits above the composer without opening another
native window or squeezing chat. Bud connector cards now adapt to compact widths
without forced window enlargement. Settings has a persistent action footer.
See docs/final-beta-phase-4.md for review coverage, evidence and remaining live gate.
No SQL, hosting, production activation or customer purchase flow was changed.

## October 12 — Phase 5 approved; trust pages and privacy operations

Owner approved Phase 5 and reiterated the Cluely footer/reference. Expanded original
privacy/terms/support disclosures and four-column public footer; added data controls,
service providers, cookies/storage, acceptable use and security/availability pages.
Desktop Settings now links to the public Data & AI guide. Verified waitlist-removal
operator tooling preserves account sessions and fails closed on damaged encryption.
No production records were removed, new permissions granted, or payments enabled.
See docs/final-beta-phase-5.md for the actual data map, reference retrieval limits,
request runbook and release gates. This is implementation progress, not legal approval
or completion of full account/workspace export/deletion acceptance. Operator identity,
counsel/processing contracts/business readiness and earlier live gates remain open.
Phase 6 still requires separate owner approval; live Stripe setup remains deferred
until the prelaunch/packaging checkpoint.

Phase 5 follow-up: owner requested substantially deeper Privacy and Terms. Expanded
original policies into 25/27 sections with detailed data handling and commercial/legal
allocation; accessible full contents and unchanged URLs. Business-only liability and
covered third-party claims clauses require qualified counsel's review. Actual operator
identity and existing privacy/live gates remain open; Phase 6 is not yet approved.

## October 12 — public AI discovery and website attribution before Phase 6

Owner requested AI/search discovery and a referral question in WEBSITE introduction,
then the legal operator detail again. Added factual public product guide, metadata,
canonical/schema, robots and sitemap; no inclusion/ranking/endorsement guarantee.
Public search/retrieval is separated from OpenAI/Anthropic training. Google-Extended
allows public marketing content for its combined Gemini grounding/training purpose.
Private routes remain protected; non-public deployments exclude indexing.
Website Plans entry points now use the optional introduction, available in waitlist
mode, with explicit AI source choices. Optional source/detail accompany later waitlist
registration in encrypted existing records and private CSV export; no SQL is needed.
Native onboarding, auth, payments and downloads remain unchanged/gated. Search-console
ownership/submissions, actual public crawler access and ongoing factual coverage are
unverified rollout requirements. See docs/ai-discovery-and-attribution.md.
Phase 6 is not started. Actual legal operator name is still the next required detail.

Discovery publication: website PR #12 merged, production-based suite 407 passed,
staging 470, lint/JS syntax and CI image smoke passed. Local browser/mobile flow
verified. Public robots retrieval remains blocked and search-console submissions
are unverified; no actual LLM citation or recommendation was established. Required
legal operator detail remains pending; Phase 6 stays unstarted.


### October 12 — Google Search Console ownership and sitemap submission

Owner added DNS TXT and approved verification; Domain property ownership verified.
Homepage is indexed and Google's live homepage/sitemap fetches succeed. Corrected
public machine discovery files' noindex headers in website PR #13; 407 tests and
PR/main CI pass. Merged 1a72b9a, deployed origin confirms header absent. Resubmitted
canonical sitemap with Google success acknowledgement; report still “Couldn't fetch”
and zero pages immediately afterward, so processing acceptance remains pending.
No further DNS action now; keep verification TXT. No security weakening or indexing
promise. Evidence: work/phase-5-trust/gsc-sitemap-result.png and discovery documentation.

Saved owner's credit-conscious Mac/Windows download priority in final-beta-launch-plan.md.
Local certificate inventory has Apple Development only, no Developer ID Application;
public Mac signing/notarization remains blocked. Windows packaging/signing/clean-machine
acceptance remain open despite previous Windows regression success. No installers
published or waitlist/billing gates changed. Legal operator name remains the next
required detail; Phase 6 remains unstarted.


### October 12 — legal operator deliberately pending

Owner confirms Aedrova currently operates under its brand name; no registered legal
entity or ownership structure is confirmed. Keep the internal legal operator field
as [Legal operator — to be confirmed]. Do not infer a company, individual contracting
party, incorporation status or ownership from the brand or founder account. Finalize
Privacy/Terms against the actual operator after the owner confirms registration and
ownership. Stop repeating the legal-name question until that information is available.
This does not prevent release-candidate engineering; legal/business sign-off remains
a public paid-launch gate. Next proposed work is Mac/Windows release-candidate
packaging and website download preparation, with public distribution still gated.


## October 13 — pre-Apple launch checks authorized and executed

Owner resumed independent launch-gate engineering ahead of membership. Desktop
782 and backend 487 tests pass; full lint/secret checks pass. Added omitted voice
migration/test to PostgreSQL runner; private voice and full RLS runs pass. Backend
private schema checks pass. New lifecycle/recovery/operations tests and bounded
read-only monitor delivered; no provider charge or live payments/download activation.
See docs/pre-apple-launch-gates.md for completed checks versus actual outstanding
owner/hosted gates, and website docs/prelaunch-operations.md for incident/restore steps.
Legal operator remains deliberately pending. Sign in with Apple is queued for active
membership. Current work does not close all phases or approve public go/no-go.


Windows CI follow-up: backend CI 38494165863 and app PostgreSQL/Mac/Linux jobs passed.
Windows run 38494283627 exposed two voice preview cleanup failures (780 passed):
QMediaPlayer held the WAV file after clearing its source. Dispose now destroys the
media backend synchronously before removing the temporary file and is idempotent.
Added an immediate/repeated-disposal regression and an early voice gate on all CI
platforms. Eight local voice tests and lint pass; follow-up Windows CI remains needed.
Staging readiness timed out twice; public website origin returned 200 ready. No
hosting upgrade, production restart or public availability certification was performed.


## Final automated result — October 13

Source bb2c9e4 passed full release-candidate CI 38495242441: macOS, Windows,
Ubuntu and PostgreSQL/RLS all green. Local final desktop suite: 783 passed.
Backend source 0ecd826 passed CI 38494165863, including 487 tests, private
PostgreSQL schema checks and deployment-image build/startup. Lint/secret checks pass.
Windows cleanup correction is validated on the actual Windows runner; no tests skipped.
No signed installer or physical-device certification is implied by these results.

Render runtime logs show repeated readiness 200s on the free staging instance;
this session's direct HTTPS probes still timed out and its browser request was
blocked by client. Do not diagnose those as proven application/hosting failure or
certify always-on availability. Free-instance sleeping remains a disclosed gate.
No hosting, credential, payment or deployment setting was changed.

Owner provided purchase confirmation for Apple Developer Program membership.
Purchase is completed; activation details are still to be emailed. Do not treat
receipt as active membership, copy its private order identifier into source, infer
legal operator identity, or start signing/Apple OAuth before activation is confirmed.
Required next owner action: Apple Developer → Account → verify active membership,
then reply “Apple membership active.” All other live/owner gates above stay open.


## October 13 — new-user audit before Apple setup

Owner requested a thorough first-run/build/Bud/connector audit and fixes, then
asked to finish. Real isolated staging Google sign-in, synthetic workspace creation,
required profile/project/Bud onboarding, Marketing role filtering, Finish later →
controls tour, command menu, chat send and builder queue were exercised. Fixed
theme and tab accessibility selection, dynamic action labels, nested profile
scrolling, real-stage accessibility copy, unavailable connector labels, private Git
config sandbox reads and scoped current-session build failure details.
785 desktop and 487 backend tests pass; Ruff and tracked-secret checks pass.
Real local Codex generation/tests passed; installed Codex/Claude tool execution and
Git checks passed with loopback model fixtures (not paid Claude inference).
Live staging included AI rejects as unconfigured; Instagram/TikTok login is also
unavailable there. No provider-wide acceptance, public gates, Apple setup, billing,
hosting purchase or signed installers enabled. Full evidence and precise next
setup requirements are in docs/new-user-flow-audit.md. No new SQL needed.

Audit final detail: native-menu logout passed and returned to Google sign-in; the
isolated source audit instance was closed. Found and fixed Account reopening staying
on the prior workspace-created confirmation while refresh fails. All 49 focused
account/identity/connected/baseline checks passed after that final correction.
The synthetic staging workspace is retained as labeled audit evidence.

## October 14 — TikTok staging setup

Approved existing TikTok sandbox credentials are deployed privately on
aedrova-beta-staging and its HTTPS callback is registered alongside the old one.
Render deployment dep-db80612j9qps73b4soq0 is Live; readiness returned 200 and
58 focused backend OAuth tests passed. A real Marketing Bud in the synthetic Beta
isolation workspace offers Connect TikTok and opens Google → TikTok sign-in
without manual codes/IDs. The owner signed in, but TikTok returned
non_sandbox_target; the sandbox still lists only @aedrova. Fresh staging consent,
callback/profile/public-video acceptance and refresh remain open. No production
gate, new scope, new target, purchase or SQL change. Exact evidence and owner steps
are in the website repository docs/social-connectors.md. Theme illustrations now
crop at bottom-right; 26 onboarding tests passed and commit 089fc75 is pushed.

## October 14 — branded website error pages

Instagram's unavailable login button now says Sign-in setup pending; this is a
service configuration blocker, not a reason to enable unsupported OAuth. 25
connector UI tests pass; source commit d596973 is pushed.
Website PR #15 merged isolated branded browser error pages with existing Buds,
Aedrova typography, blue controls, dark/system styles and recovery/support links.
432 production-candidate tests, 512 development-backend tests, and 13 independent
Worker tests pass. Render deployment of 2f083e4 is Live; real public 404 is branded
with embedded artwork and restrictive hashed CSP. API contracts stay unchanged.
The independent Cloudflare origin-outage fallback is prepared but NOT routed.
Safari loads the owner's free Cloudflare account, but automation cannot activate
its Worker creation button. Owner action: Cloudflare → Workers & Pages → Create
app → Start with Hello World → name aedrova-error-fallback → deploy on existing free
plan; leave it open and reply created. Do not add routes until the tested code is
installed. Host-origin 502 coverage remains blocked on this setup. Browser DNS,
certificate warning and failures before Worker execution cannot all be customized.
Full steps/evidence: website docs/branded-error-pages.md. No SQL needed.

## October 14 — Instagram staging live grant verified; TikTok provider limit

Instagram app 2156018749127516 (Aedrova Buds-IG), under parent 3077883259220045,
is configured for the exact staging HTTPS callback and instagram_business_basic
only. Approved private credentials are deployed on staging (dep-db85045g1s2s7392hcs0,
Live). Owner accepted @aedrova_ai tester invitation and personally allowed the
read-only profile/media grant. Branded callback and native Connected status passed;
connect requires successful live profile AND posts reads before saving the grant.
No manual user codes/IDs, publishing/messages, production change or purchase.
Refresh/revocation/reconnect and public Meta review remain open; Phase 2 is not closed.

TikTok sandbox target confirmation resolved to @aedrova. Fresh staging login is now
blocked by TikTok's "Maximum number of attempts reached" response. No more login
attempts until the provider restriction clears, then one callback/profile/video
acceptance check remains. No fixed cooldown is promised. DM + and Bud DM assessment
are queued after social OAuth completion, per owner instruction.

Owner created the free Cloudflare Worker (actual name aedrovaerrorfallback); starter
is still unrouted and unmodified while social OAuth is prioritized. Host-outage
fallback remains unfinished. Source evidence and exact acceptance limits are in
website docs/social-connectors.md. No new SQL or credentials are required now.

## October 14 — coworker DM discovery and private Bud conversations approved

Owner approved the coworker DM + button and private Bud conversations after the
social OAuth status report. Implemented the + using the existing picker/server DM
operation, with stale-workspace guards. Bud shelf clicks now open a private chat;
Configure retains the existing editor. Ordinary messages address that Bud directly.
Private replies use the existing configured personality/provider and Bud-scoped
connector retrieval; workspace context is explicit opt-in per reply and off by
default. Executable builds remain in the existing Build studio with approvals.

Added account-owned bud_messages storage, RLS and authenticated bounded/idempotent
RPCs, deliberately outside team channels/search/notifications. Other members and
workspace owners cannot read another user's history through app permissions.
Source supports reopened history, local echo, retries, skeleton recovery, cancel,
logout isolation and light/dark/compact layouts. Tests use a provider fixture;
hosted private-chat acceptance is NOT claimed yet. Details and scope limits are in
docs/private-bud-conversations.md.

Required owner action at the end: Supabase → Aedrova Staging → SQL Editor → New
query → run supabase/migrations/202610140001_bud_conversations.sql from this repo.
Only Staging, not production. This blocks live saved history/provider/isolation
acceptance. No Render deployment, new credentials or payment required. TikTok
attempt restriction, public provider review, outage fallback and release gates
remain open. No signing, Apple OAuth, packaging or public activation performed.

Validation: 795 full desktop tests passed; final private-chat subset 9 passed.
Complete embedded PostgreSQL migration/RLS suite, Ruff and diff checks passed.
Light, dark and compact Qt previews inspected with synthetic data. Hosted acceptance
is still blocked on the owner-applied staging migration above.

Owner subsequently reported migration success. Real staging private question
save/reopen, exclusion from team chat, and first-account user-JWT table/RPC reads
and duplicate-safe retry are verified. Native DM + returns the correct invite-first
empty state in the one-member test workspace. Hosted foreign-account probe is at
the second Google staging test account chooser; owner selection is still required.
Actual Bud inference is blocked by the server's explicit “Included AI access is not
configured yet” denial after a cold-host timeout. No model reply/fallback or public
activation is claimed. Next setup approval must specifically cover the existing
OpenAI key to Render staging for capped inference (proposed $1/month accounting
budget), matching backend deployment, and no production/checkout change. Existing
speech-only approval is insufficient for this new credential purpose. See
docs/private-bud-conversations.md for evidence and exact pending actions.

Second-account sign-in follow-up: owner said signed in; actual browser result was
Supabase bad_oauth_state (expired), not the probe's native callback. Renewed first
session and reverified own history/idempotency. Second OAuth is now held locally
until the owner identifies the second registered test-account email, allowing its
already-signed-in browser session to be selected against a fresh link. No expiry
or permission protection was bypassed. Hosted outsider isolation and real included
AI responses remain open; no additional migration is needed.


## October 15 — current repair roadmap Step 1 baseline

Owner authorized inventory/documentation only and requested all personal actions
be saved for the final handoff. Saved docs/release-baseline-2026-10-15.md and JSON
with every current product issue, nine connectors and all 14 meeting categories.
Source controls and historical tests are distinguished from live acceptance.
Included staging AI, foreign-account private Bud acceptance, social/public provider
lifecycle gates and reported video failure remain open. Existing dashboard accept
and message-copy code are not falsely reported as missing or fixed.

No runtime/account/credential/schema/deployment/billing/signing changes performed.
No owner action required for Step 1; later conditional actions are consolidated in
the baseline. Next batch is Step 2 AI routing and capped provider availability,
pending owner approval. Historical Beta phases retain their separate numbering.

## October 15 — repair roadmap Step 2 implementation and provider evidence

Owner approved AI responsiveness and availability, with personal actions collected
at the end. Implemented the no-Buds main greeting routing fix; source-free answers
skip evidence/tool discovery and use lightweight fresh membership checks. Included
read-only inference uses the existing metered gateway directly, with no coding CLI,
tools, silent retries or personal fallback. General responses stream as one message;
source-backed results remain withheld until access/citation rechecks. Bud identity,
personality, private-history opt-in, existing build execution and plan caps remain.

Existing OpenAI and Anthropic model/key lookup passed. Real loopback OpenAI inference
and actual desktop main/Bud QueryJobs passed (0.84s/1.85s completion in the observed
integration test); zero reservations remain. Synthetic auth and isolated SQLite
were used: this is not hosted Supabase/production acceptance. Anthropic real
inference was rejected for insufficient provider credit balance. Staging live health
confirms gateway disabled; Render still deploys e375bdc on its sleeping free host.
Do not label hosted AI restored or Step 2 fully accepted yet.

Validation: full desktop suite 824 passed before the final lightweight inventory
change; final focused routing/identity/context/Bud/managed suites 131 passed after
that change. Backend gateway/budget/provider/shared-space suites 64 passed; final
Ruff/diff checks passed. No SQL migration required. Server config overlay validated
privately without upload/deployment; production, checkout and release mode unchanged.

Consolidated owner actions and exact staging secret/settings destination are at the
end of docs/ai-responsiveness-step-2.md. Specific inference key-transfer/deployment
approval remains required; use existing Free allowance/owner activation and valid
staging login for hosted tests. Claude funding is separate and optional for OpenAI.
Step 3 remains unstarted. Website configuration proposal:
deploy/staging-ai.env.example in the Aedrova-website repository.

Step 2 hosted follow-through: owner approved the exact OpenAI key/settings/deploy
handoff. Render staging deployment dep-db8o043l550s73ej2i90 is Live on e375bdc;
verified gateway=true, OpenAI-only model file, $1/month company/Free-pool accounting
ceilings and closed checkout. Fresh native Google PKCE owner authentication,
existing Free allowance, actual hosted main/Bud replies, private Bud reply
save/reopen and zero outstanding reservations passed. Observed completion totals
12.96s/13.95s include fresh access checks and closure; loopback timings are not
hosted latency. Incremental hosted usage $0.002339. No paid hosting/production/
packaging/Stripe or migration change. Step 3 remains unstarted.

Final owner actions are consolidated in docs/ai-responsiveness-step-2.md: rotate
OpenAI credential before broader testing because a masked Render field still
exposed it in an automation DOM snapshot, update the staging AI/speech settings and
private local file, deploy and revoke old key; fund Claude only if enabling it.
No secret value is stored in tracked documents. Current source workers passed;
older installed binaries are not silently upgraded or certified as release builds.

## October 15 — repair roadmap Step 3 and retained-key decision

Owner approved Step 3 and requested mitigation of the Render snapshot mistake
without generating new keys. Existing key remains unchanged; automation runtime
reset and exact-byte desktop tracked-file/Step 2 artifact scans completed. No copy
found in those files. Prior tool output cannot be erased; exposure is not reversed.
No Render settings, credentials, deployment or purchases changed in this batch.
Owner elected to retain the key; original rotation advice is not an outstanding
action for this source batch. Full record: docs/workspace-ai-setup-step-3.md.

Desktop creation now requires provider/model-policy and execution review with
acknowledgement. Account/computer-scoped workflow settings are persisted; main/Bud
manual build requests open review without automatic execution. Subspace partial
failure retries preferences without duplicate creation. Go to Dashboard closes
before activation triggers a refresh, and the introductory profile retains its
authorized workspace. Compact/light/dark review inspected. Existing workspaces,
website and backend creation APIs are not newly migrated or server-gated.

Final desktop suite 835 passed; Ruff/diff passed. No new live workspace creation
or signed installer certification claimed. No owner action required now. Step 4
requires owner approval; production promotion and release gates remain separate.

## October 15 — repair roadmap Step 4 messaging

Owner approved Step 4, personal interventions at the end. Implemented selectable
conversation text, rounded line highlights, native keyboard copy for agent/Bud
labels, token/revision-aware composer clearing and distinct main/thread drafts.
Receipts preserve newly typed text; retries clear only untouched restored drafts.
Private Bud sends clear immediately with existing saved-message retry IDs.
DM + now offers searchable People/Buds, configured avatars, stable identities,
workspace/session guards and non-interrupting same-Bud dialog reopening.

Full desktop suite 846 passed, Ruff/diff passed; embedded PostgreSQL migration/RLS
suite passed including coworker DM and private Bud isolation. Real staging fresh
native sessions verified actual streamed Bud reply/save/reopen, repeated-ID
idempotency, foreign-account table/RPC read/write/spoofed-reply denial and zero
reserved usage. Incremental test usage $0.001992. No new keys, schema, workspace
memberships, connector scopes, Render deployment or production/installer changes. The first cold-host
attempt was incomplete; subsequent health-verified attempt passed. Live two-human
messaging/notifications and all membership lifecycles remain release acceptance
items, not claimed by this narrower test. Details: docs/messaging-step-4.md.

No owner action required now. Step 5 single-action connector UX needs approval;
Step 6 live provider certification and Step 10 production promotion remain gated.

## October 15 — repair roadmap Step 5 connector UX

Owner approved Step 5. Disconnected detail has one Connect your account action,
with app icon and scoped permission/policy copy; no normal token/ID fields,
advanced toggle or duration menu. Managed Search uses an honest enable/topic flow.
Provider-required named resource/Figma-link selection appears after OAuth only.
Connected accounts use a separate Manage access/Disconnect view, including when
new OAuth setup is unavailable. Default grant lifetime stays 24 hours; no broad
or permanent account-access claim was added.

Duplicate pending actions check status; stale start responses are invalidated on
navigation/Bud changes. Empty discovery shows only reconnect. Success requires
refreshed matching Connected grant data. Light/dark/compact states inspected;
dark content surface fixed. Existing compatibility token handlers/backend APIs
retained outside the normal customer flow. Full desktop suite 857 passed before
final visual/management refinements; final focused results recorded below.

No provider grants, credentials, backend/schema/API changes, external deployment,
production or installer changes. Real catalog/lifecycle certification remains
Step 6. No personal action required now. Approval required before Step 6; exact
future provider interventions will be collected at the final handoff. Evidence
and known boundaries: docs/connector-ux-step-5.md.

Final Step 5 follow-through: connector/Bud/loading suite 77 passed after visual,
unavailable-provider management and disconnect-status refinements; Ruff/diff pass.

## October 15 — repair roadmap Step 6 in progress

Owner approved live connector certification, with interventions saved for the end.
Authenticated staging catalog/grant check passed after cold-host wake-up; only
Instagram/TikTok OAuth enabled, no active grants in the named test workspace.
Existing local pairs present for GitHub/Supabase/Figma/Notion; absent for Stripe/
Vercel and managed Search key. No provider app secrets printed or transferred, no provider
scopes, registrations, access grants, hosting charges or production changes made.

One social OAuth start each passed. TikTok web handoff stalled in Google's loading
account chooser before reaching provider; Instagram provider screen not opened.
No renewed grant/read certification claimed; temporary sessions/URL files cleaned.
Historical TikTok maximum-attempt and public social-review gates remain unresolved.

Source fixes preserve intentional token-exchange denials, distinguish 429/5xx
from access loss, normalize TikTok comma/space scopes without broadening them and
remove stale token-workaround setup copy. Added all-nine grant lifecycle/isolation
regression cases with synthetic providers. Backend 528 tests passed before final
copy cleanup; final run recorded below. Live Render still e375bdc; patches are
not yet deployed. Full status and references: docs/connector-certification-step-6.md.

Required final approval: add staging callbacks and transfer the four EXISTING
client ID/secret pairs privately to aedrova-beta-staging, then deploy reviewed
staging source. Exact environment/checklist in website deploy/staging-connector-
certification.env.example. Specific destination approval is required by browser
safety. No new keys or scope expansion. Stripe bank setup stays deferred until
release. Step 6 remains open; Step 7 has not started.

Final Step 6 source validation: 528 backend tests passed after setup-copy cleanup;
Ruff/diff pass. This does not certify undeployed patches or missing live grants.


## October 15 — Step 6 approved staging setup delivered

Registered and re-read exact staging callbacks for existing GitHub/Supabase/Figma/
Notion apps, retaining prior callbacks/scopes. Copied only their eight existing
client ID/secret values privately into Render aedrova-beta-staging; retained all
34 prior variables (42 total). No new keys, purchases, production changes or
permission expansion. Saved environment then deployed specific tested da30ebf.
Render dep-db8s0huq1p3s7396bdfg Live. Health 200, AI enabled, checkout disabled.
Fresh native Google PKCE/authenticated catalog passed: all four plus Instagram/
TikTok OAuth available; Stripe/Vercel/Search remain unavailable. No active grants
in named staging workspace. Backend rerun 528 passed, Ruff/diff pass.

No owner action required for this completed setup. Step 6 remains open for fresh
provider consent/resource reads and lifecycle acceptance; those actions must be
prepared sequentially before an exact personal handoff. GitHub's initial identity
prompt resolved without owner intervention. Stripe business/bank setup remains
deferred; Step 7 and production/installers not started. Evidence and boundaries:
docs/connector-certification-step-6.md.


## October 15–16 — Step 6 live read/disconnect acceptance

GitHub/Supabase/Figma/Notion passed real staging OAuth callbacks, named-resource
selection and provider reads, local disconnect and denial afterward. GitHub also
passed fresh reconnect. Only disposable staging grants used; all four removed.
Found web Google handoff missing OpenID scopes; a55cf9d fixed it and deployed Live.
Found Notion app user/email access enabled; reduced to No user information, kept
Read content, reloaded real consent shows page-only access. Cancellation recovery
fix 6a3cc90 replaces misleading generic permission error with branded cancellation
copy while retaining failed-state/cookie handling. Backend 528 passed, Ruff/diff pass.

Instagram/TikTok reach real login but need owner test-account sessions. Exact
actions are in connector-certification-step-6.md and final handoff. Stripe/Vercel/
Search correctly reject setup-incomplete requests; no purchase or provider setup
fabricated. Live renewal/provider-global revocation and fresh cross-account tests
remain unaccepted. Step 6 is not all-nine launch certification. Step 7 needs next
owner approval with these external gates explicitly outstanding.

Final staging build 6a3cc90 is Live (Render reports deploy succeeded, 1m03s).
Cancellation recovery is verified by controlled browser-route regressions; reusing
the earlier live cancellation URL still returned 403 and is not acceptance of a
fresh successful cancellation. No claim that stale/replayed proofs are accepted.


## October 16 — repair roadmap Step 7 core meeting repair

Owner approved Step 7 and resupplied full 14-category call feature list; saved verbatim
in meeting-features-owner-source-2026-10-16.txt and mapped in meeting-step-7-status.json.
Advanced capabilities remain Steps 8–9; no feature requirement deleted or advertised
as implemented merely because it is on the list. See docs/meeting-step-7.md.

Repaired video stalls caused by awaiting access heartbeats inside the frame pump.
Independent bounded heartbeat retains fail-closed termination/guard rules. Added native
SDK microphone/speaker selection, muted-by-default video meetings, noise reduction,
optional hold-Space-to-talk with release/focus-loss cancellation and hot-plug refresh.
Curated setup-unavailable errors no longer tell valid users to sign in again.

Live generated RTC worker camera/screen exchange, forced removal and stale-token denial
passed. Forced TURN relay audio/camera/screen passed both directions; real native
audio enumeration/selection passed without capture. Full desktop 864 passed before
final recovery test; final focused result recorded below. Local meeting health 200,
staging 503. Paid API/guard upgrade remains deferred; physical/two-account hosted
acceptance is still blocked. No hosting/key transfer/payment/migration/production
or installer change. Exact owner actions consolidated in Step 7 docs/final handoff.
Step 8 is not started and requires next owner approval.

Final Step 7 verification: 865 desktop tests passed; 82 final focused meeting
checks passed after the final UI status-copy adjustment. Ruff/diff checks passed.
Light/dark wide/compact previews inspected. Forced TURN relay received generated
audio/camera/screen in both directions. No physical capture or hosted-user call
was performed. Public launch and Step 7 hardware acceptance remain gated.

## October 16 — repair roadmap Step 8 foundation (partial)

Owner approved Step 8. Added authenticated persistent channel chat inside calls,
explicit permitted captions with adjustable text size, bounded latest transcript
API query using caller RLS, server-acknowledged privacy choices with request IDs,
and transcript draft preservation/current-page search. No recording, RTC data
publishing, implicit AI reuse or new device capture. Exact source/evidence and
remaining work: docs/meeting-step-8.md; every original requirement retained in
meeting-step-8-status.json. Step 8 remains open for additional engineering and
hosted/physical acceptance; Step 9 has not started. Paid staging API/independent
guard are still deferred. No migration, provider key/allowance change, production
deployment or installer build. Owner actions consolidated in Step 8 handoff.

Step 8 validation: full desktop suite 872 passed, then 73 final focused meeting/
speech/call-bar tests passed after final request-correlation and lifecycle changes.
Backend context/wrapup API suite: 8 passed. Ruff and diff checks passed. Qt fixture
previews rendered in light/dark; these are controlled checks, not hosted RLS or
physical speech/meeting certification.

## October 16 — meeting launch gates saved

Owner requested deferral of the remaining meeting work and acceptance requirements
to launch gates. Saved docs/meeting-launch-gates.md and linked the final Beta plan.
Four open gates cover feature/scope completion, deferred paid staging API plus
independent guard, two-account physical/accessibility/security acceptance, and
production/installer parity. No gate closed, feature removed, hosting purchased,
code changed or environment deployed. No owner action required now; exact deferred
Render/device actions, costs and blockers remain explicit in the gate register.

## October 16 — repair roadmap Step 9, first advanced presentation batch

Owner approved Step 9 after saving outstanding Step 8 work as launch gates.
Implemented native application-window share targets, permission/watchdog retention,
stop/unpublish-based share pause with acknowledged resume, sharer freehand drawings
in outgoing screen pixels, pin/unpin video, video-only receive unsubscription,
self-view/preview-only mirror and basic outgoing monochrome/soft-light treatment.
Presentation and device settings scroll; fixed compact clipping during visual QA.
No background segmentation, remote-control permission or pretend advanced controls.
No new schema/backend/provider/model call or paid infrastructure. Source only;
production, installed binaries and hosted feature gates remain unchanged.

Validation: full desktop suite 884 passed; 89 final focused native meeting tests
passed after final optimizations/race checks. Ruff/diff checks passed. Existing
synthetic native RTC probe passed two-way camera/screen exchange, incoming-video
pause/resume while outgoing continued (109 resumed frames), forced removal and
cached-token rejection. No physical capture, hosted Supabase-user acceptance,
recording or transcription. Rendered light/dark wide and compact previews;
inspected compact share and Presentation; fixed clipped copy.

Full original requirements retained in docs/meeting-step-9-status.json; details,
limits and consolidated owner actions in docs/meeting-step-9.md. Step 9 remains
partial: backgrounds, advanced collaboration/moderation, breakouts/polls, translation,
telephony and streaming still open. No owner action now. Existing deferred Render
always-on API/independent guard and two-device OS-permission/listening tests remain
launch blockers in docs/meeting-launch-gates.md. Step 10 has not started.

## October 16 — remaining Step 9 work retained as launch gates

Owner requested remaining Step 9 work be added to launch gates before discussing
Step 10. Added explicit OPEN LG-MTG-05 in docs/meeting-launch-gates.md covering
all advanced capability families and physical acceptance of delivered presentation
controls. Updated status links. No feature removed, gate closed, payment submitted
or environment changed. No immediate owner action. Step 10 is staging promotion
and release preparation per the original 10-step repair roadmap; starting it still
requires owner approval, and production/download/billing activation remains gated.

## October 16 — owner requires gate closure and staging acceptance before Step 10

Owner corrected sequencing: complete all pre-production launch gates, apply the
changes to staging and test the integrated candidate before Step 10. Step 10 has
not started and requires approval after verified gate closure. Updated the main
launch plan and meeting gate register; no deferred item is treated as complete.
Release-candidate packaging/clean-machine checks precede promotion; production-only
smoke is run in Step 10 and still gates public activation. No setup/payment,
implementation, deployment or acceptance is claimed by this documentation change.

## October 16 — all-gate closure authorized; payments excluded

Owner authorizes access to necessary materials, implementation and staging testing
for ALL launch gates, with an explicit exception: no payments/purchases on owner's
behalf. This supersedes earlier implementation deferrals, not acceptance evidence,
account ownership, human hardware tests or security-specific confirmation rules.
Step 10 remains blocked. Current all-gate closure work is ongoing, not complete.

Latest GitHub candidate 006b695 failed Windows/Linux while macOS and PostgreSQL
passed. Traced Windows Bud-history failure to the fixture replacing its shared
transport before initial sync settled; Linux reply test waited for server-side
fixture mutation before GUI completion. Corrected both waits. Fixed actual Linux
AI review disclosure compression with a non-compressible minimum text height.
Focused Bud/setup/connected checks: 26 passed. Backend 530 passed; public RLS and
private PostgreSQL schema/atomic-lease checks passed locally. No claim that these
replace hosted two-account, restore or multi-worker acceptance. Developer ID signing
identity is absent locally (only Apple Development present); signing gate open.

## October 17 — candidate CI and live staging isolation checkpoint

Desktop source 3a9b698 passed GitHub CI 38998004293 on macOS, Windows, Ubuntu
and PostgreSQL/RLS. Local desktop suite: 886 passed before the final focused
fixture/layout corrections; 26 focused checks passed afterward. Backend suite:
530 passed. Public and private embedded PostgreSQL checks, lint and tracked-secret
checks passed. These results do not certify installers, physical capture or a
hosted recovery/multi-worker drill.

Deployed existing backend source 96d18562aea773ad2e312aa4074815c3581c8b3e to the
existing free aedrova-beta-staging service (Render deploy
dep-db9efldg1s2s738dg480, observed Live). No environment credentials, hosting plan,
production service, public downloads or billing activation changed. Readiness
returned 200 after initial request timeouts; meeting health remains 503 unavailable.
Always-on reliability and meeting activation are still OPEN.

Live ordinary-user staging acceptance passed private file/thread publication and
verified download, upload cancellation at two points, foreign-workspace denial,
same-workspace private-channel denial, removed-member denial and signed-out media
denial. Separate live Bud acceptance passed idempotent private history, outsider
read/write denial, same-workspace private-history/reply isolation, reverse member
isolation, no shared-channel publication and removed-member denial. Both used two
distinct Google accounts; synthetic Bud/workspace fixtures were soft-removed or
archived and probe sessions signed out. No inference or connector grant was used.
Repeatable Bud probe: scripts/check_staging_bud_privacy.py. Private local evidence:
work/staging/gate-closure-media.json and gate-closure-bud.json; never commit sessions.

Fresh native workspace creation verified mandatory AI execution consent and that
Go to dashboard dismisses its account popup and opens the welcome flow. Remaining
required-Bud/Finish later/highlight walkthrough is NOT accepted: macOS automation
failed to acquire the staging application's capture stream (-3811). No product
crash was found in the launcher log; this does not establish full native acceptance.

ALL-gate closure remains INCOMPLETE. Outstanding engineering remains explicitly
listed in meeting-launch-gates.md and original requirement/status inventories.
Other open gates include provider lifecycle/public approval, real model accounting,
hosted alerts/recovery/multi-worker and independent security review, Stripe account
and lifecycle acceptance, legal operator confirmation, Apple OAuth/Developer ID,
Windows signing and clean-machine/update/uninstall tests. Step 10 has not started.
Consolidated owner dependencies and exact next actions are in
docs/launch-gate-checkpoint-2026-10-17.md. No purchase performed.

## October 17 — native macOS adaptive app icon

Owner requested Aedrova respond to macOS Default/Dark/Clear/Tinted icon styles.
Added branding/Aedrova.icon using the existing mark, light and charcoal backgrounds
and native system mono material. Apple controls tint, Always/Auto and light/dark
renditions; no app theme override or new in-app option. Owner accepted Icon Composer's
first-use license personally. No new generated logo, payment or account grant.

Packaging and staging now compile Assets.car/compatible ICNS with Xcode actool,
merge its icon metadata and install before signing. Qt skips its fixed runtime icon
when the native macOS bundle catalog is present. Non-macOS/unbundled sources retain
the static fallback. Updated local staging bundle and verified ad-hoc signature.
Native Default, Dark, ClearLight, ClearDark, TintedLight and TintedDark exports all
passed; preview inspected. Four focused brand/native-icon tests and lint passed.
This is not signed distribution/installer or live Dock-style acceptance. Required
owner action: relaunch the updated staging build, then choose each macOS Appearance
icon style to confirm the Dock result; an already-running/older installed app will
not receive source changes automatically. Public release gates remain unchanged.

## October 18 — Mac DMG focus and requested launch hardening

Owner prioritizes Mac DMG launch; no niche pivot or 34-change roadmap authorized.
Built source 4e67d8e as an internal staging arm64/macOS 14+ preview DMG. Integrity,
manifest SHA-256, mounted app deep/strict signature, Applications link, adaptive
icon, frozen endpoint isolation, baseline secret scan and light chat/dark account
startup smoke passed. Full desktop suite: 889 passed. No Developer ID identity found;
no notarization/public download or production change. Exact signing actions and
artifact evidence: docs/mac-dmg-launch-2026-10-18.md.

Owner additionally requires caching, optimistic rendering, icon tooltips, endpoint/
login rate limits, credential scanning/private configuration and bounded malformed
input rejection before launch. Implemented 30-second session-scoped catalog-only
cache and shared icon tooltip defaults; retained existing optimistic send/retry
and access-change invalidation. Added database-backed website/connector ingress
limits and bounded metadata/JSON/mutating bodies; main DTOs reject extra fields.
Login starts 10/5 minutes per IP, callbacks 30/5 minutes separately; these are
initial policies requiring traffic/proxy/provider acceptance, not universal optimum.
Liveness uses bounded local limiting to survive DB outages. Provider/Supabase-hosted
endpoints and custom transient buttons still require explicit acceptance coverage.

Current tracked scans passed in both repositories; historical source patterns
scanned 1,029 app and 2,925 website objects. The sole historical match was confirmed
as encoded WebAssembly in vendored Prettier, not a credential. First-party literal
assignment audit found none. No credential migration/rotation was indicated by
these limited scans. Existing server secret environment, encrypted per-user grant
storage and OS Keychain remain; no shared secrets in frontend. Backend suite after
changes: 533 passed. Desktop focused cache/tooltip checks: 2 passed; connected/Bud
checks: 18 passed before the final tooltip assertion. Full revised suite: 890
passed; final cache/tooltip/voice checks: 10 passed after the final small fixes.
Shell audit found missing meeting-options, voice-discard and native menu-overflow
tooltips; corrected them. Full source/script/test Ruff passes in both repositories.
Source/local checks do not certify deployed rate limits. Public gates
stay OPEN. See website docs/launch-hardening-2026-10-18.md for exact coverage/limits.

Final packaging follow-up: rebuilt staging preview from 9dfb7c0 with desktop
catalog caching/tooltips; repeated integrity/digest, mounted signature, Applications
link, adaptive icon, staging endpoint and frozen account startup checks passed.
Current artifact/hash in docs/mac-dmg-launch-2026-10-18.md supersedes the earlier
preview. Server hardening still needs hosted acceptance, including Supabase Auth
limits/trusted ingress. No public release, hosting payment or website activation.

## October 19 — onboarding / pre-checkout preparation screen

Owner requested a short, branded spinner screen after onboarding and before payment.
Website source now shows a Bud-led, three-step preparation dialog after the optional
introduction (including Skip), and during the actual confirmed checkout request.
Plan-page preload, direct Continue escape, error/timeout recovery, safe Stripe URL
validation, reduced motion, focus handling, mobile layout and charcoal styling are
implemented. Existing app Settings → Team plan & billing uses this shared website
flow; no native payment gate, new pricing, hosted billing activation or packaged-app
change. Source details: ../Aedrova_site/docs/onboarding-preparation.md.

Local validation: 68 focused website checks passed, including eight isolated browser
cases for onboarding/skip, mobile/reduced motion, preload failure, monthly/annual
checkout, server error, unsafe redirect and timeout. No live payment or provider
call. No owner credential/SQL/payment setup needed. Normal authorized push and
website deployment remain necessary to make this visible live; neither was performed
in this task. Existing launch gates remain open as documented.

## October 19 — endpoint security audit and Google discovery

Reviewed all 84 website/backend routes plus desktop OAuth/preview boundaries.
Fixed JSON media-type validation gaps, early-error security/cache headers,
sanitized unexpected API failures, vulnerable aiohttp resolution (now 3.14.5),
preview connection bounds and standalone credential-scanner imports. Website 562
and desktop 893 full tests passed; RLS/private PostgreSQL checks, dependency and
credential audits passed. Full details: ../Aedrova_site/docs/security-audit-2026-10-19.md.

Confirmed existing Google Search Console verified domain ownership, homepage indexed,
seven indexed pages and successful sitemap with 13 discovered pages. Product-page
indexing currently fails Google's cached robots check; canonical recrawl requested.
Prepared and tested an exact-path robots edge route to avoid Render Free sleeping
robots behavior. No push/deploy/edge route activation occurred. Owner deployment
approval remains required under website instructions. Hosted proxy/multi-worker,
provider acceptance, independent review and other release gates remain open.

## October 19 — consumer trust checklist and commercial launch roadmap

Owner approved audit publication/backend deployment and requested the 20-item public
trust checklist plus SQL-injection protection. Website now implements dedicated
refund information, equal optional preference-storage choices, strict waitlist
marketing/age eligibility confirmation, purpose-bound email opt-out confirmation,
suppression-aware exports, focusable skip target and contrast corrections. Existing
Privacy/Terms/data-request/service-provider disclosures retained and updated.
SQLAlchemy value binding reviewed; adversarial OR/UNION/DROP regressions passed.
Business operator/address placeholders remain unresolved per owner's instruction;
no commercial gate or payment activated. Full checklist and evidence are in website
docs/consumer-launch-checklist-2026-10-19.md.

Owner requested latest staging file opened: local Aedrova-preview.dmg was opened;
it remains the documented internal staging artifact, not a new commercial installer.
Saved complete phased commercial B2C plan in docs/commercial-b2c-deployment-plan.md,
including C-corp/ownership/EIN/bank/market scope, consumer disclosures, live product
and security acceptance, operations, Stripe verification/prices/webhooks/lifecycle,
Mac signing/notarization, Windows signing/testing, and final go/no-go. No entity
formation, bank submission, purchase, paid hosting or commercial release performed.

Publication follow-up: website PR #16 passed both required verify checks and merged
as db2bbc8. Its tree matches the 571-test local candidate. Render staging 33fc716 and
production db2bbc8 are Live. Real hosted readiness, refund UI, branded 404, private
403, security/cache headers and crawl files passed; checkout/managed AI stayed closed.
No payments, new migrations, secret changes or public installers. Cloudflare robots
activation remains a technical manual handoff: embedded code editor rejects automation
input and active Safari switching prevents reliable native edits. Single-file bundle
and exact two path routes are documented in website deploy/search-discovery/README.md.
Owner approval already exists; no new permission is needed. Policy-date correction
and hosted acceptance record are being published separately after normal checks.

Final publication: PR #17 passed both required verify checks, merged as a445578 and
Render production is Live at that commit. Updated October 19 policy dates were
verified on /refunds, /privacy, /terms, /support and /cookies. The 57 focused follow-up
checks passed. Final website/staging backend security and consumer controls are
published; optional preference controls also honor withdrawal in already-open pages.
App source and complete commercial plan are pushed; the opened staging DMG remains
an internal preview rather than a newly rebuilt/signed commercial release.

Required owner handoff now for stable search crawling: Cloudflare → Workers & Pages →
aedrovaerrorfallback → Edit code, replace worker.js with website
`deploy/search-discovery/worker-bundled.js`, Deploy on the existing free plan, then
Domains & Routes → Add → Route (zone aedrova.com) for `aedrova.com/robots.txt` and
`www.aedrova.com/robots.txt` separately. Do not add a whole-site wildcard, DNS change
or paid upgrade. This is a tooling/editor blocker, not missing approval; Google
ownership and the successful sitemap/homepage index are already verified. Reply when
the routes are saved so hosted robots and Google inspection can be rechecked.
Commercial operator/address, asset-rights evidence, final legal/security/accessibility
reviews, Stripe/hosting/signing and live product acceptance remain launch gates in the
commercial plan; none is represented as completed by this security publication.

## October 19 — GitHub, Bud loading, connector recovery and component highlights

GitHub helper setup now checks existing authorization asynchronously and switches
verified login to a compact branded confirmation with one Continue action. A helper
installation alone no longer marks authorization complete. Publishing approval is
unchanged. Bud read-only loads leave the configuration usable immediately, allow
local setup navigation during wake-up, preserve a new local draft, and retain a
100-second bounded background read window instead of discarding a cold-host response
at 30 seconds. Writes remain blocked until current server state is loaded.
Connector poll failures restore a fresh Connect your account action instead of
stranding Check connection. Onboarding now colors the real target component; the
only overlay/input mask is the guide card, with effects cleared on step/finish.

Website fix in companion repo: generic browser-error middleware had swallowed the
specific OAuth account-recovery template. An explicit server-only response marker
preserves that page and is removed before delivery. Expired state links get a
fresh-link recovery screen. Standalone error pages embed the actual brand asset,
including the exported edge fallback; identity/state/CSRF/permissions checks remain.
Full local suites: desktop 896 passed; website 571 passed. Follow-up visual changes
receive focused checks. Error fallback Node suite: 13 passed. Screenshots in ignored
work/ui-recovery-oct19 are UI fixtures, not new live provider consent evidence.
Free-host wake latency and third-party provider approval gates remain real limits;
no payment, broadened scopes, public installer or commercial activation performed.

Delivery confirmed: website PR #18 passed both required verify checks and merged as
`db8bca9`; Render production reports Live at that commit. Staging source `404105f`
contains the same tested recovery implementation and Render staging reports Live.
Real hosted checks passed on both origins: readiness 200, actual embedded logo on
404, no-store, and private provider endpoint retaining JSON 403. Staging expired
OAuth links preserve the specific fresh-connection recovery page without leaking
the internal marker. No live OAuth grants were added for this UI regression check.
App source `3a1cfc2` is packaged in the refreshed internal DMG; acceptance and exact
hash are in docs/mac-dmg-launch-2026-10-18.md. Owner action to use desktop fixes:
quit the currently running old Aedrova, then open `/Volumes/Aedrova 1/Aedrova.app`
from the newly mounted image. Old volume was busy and was not forcefully unmounted.
No further configuration, keys or payment is required for these fixes. Free hosting
can still take 50+ seconds to wake for an actual connector request; the local wizard
now remains visible and usable while that happens. Whole-site Cloudflare outage
routing and provider publication/live acceptance remain the previously recorded gates.

## October 20 — complete connector request, active provider gates

Owner requested all connectors completed now; no payments remain authorized.
Fresh native staging sign-in and authenticated nine-provider catalog passed; six
existing OAuth configurations enabled, no saved grants in the synthetic test Bud.
117 backend connector tests passed. Created the specifically approved unlisted
Vercel Aedrova Buds integration and saved only Configuration/Projects/Deployments
Read scopes (all others None), staging callback and brand/product media. Copied
its generated credentials to ignored 0600 local config and Render staging with
specific approval; existing free service deployment succeeded at 404105f.
Owner approved project-scoped install on ayansh2 / amicus-website-mq. Real consent,
callback token exchange and authorized-project discovery passed. Late resource
selection correctly rejected the expired ten-minute state; no reader/disconnect
acceptance yet. Fixed duplicate Vercel project selection when exactly one project
was authorized; provider readers still verify before Connected. Backend suite 573
passed; website PR #19 created and staged source f06e0bd pushed for deployment.

Owner approved Stripe v0.1.0 external testing and it is now enabled, unpublished,
0/25 tested accounts. Prepared v0.1.1 adds staging callback with the same two read
permissions. Owner subsequently approved callback/upload/test-key-to-Render activation; see final
acceptance below for the credential that is still unavailable.
Fresh Instagram/TikTok starts reached their real login screens once each; owner
sign-in needed, no new social grant/read claimed. Meta admin access now requires
owner email-code identity confirmation. Brave Search is unconfigured and reaches
Login; no new account, plan, card or purchase submitted. TikTok production remains
Draft with no production products/scopes or genuine end-to-end review video.
Public approvals, renewals/revocation and remaining live tests are still launch gates.

Also fixed Bud timeout copy that incorrectly described a slow connector as an AI
service failure. 35 focused desktop transport/catalog/gallery/recovery tests passed.
No permissions, grant duration, paid hosting, public launch or checkout expanded.
Exact status/owner actions are in website docs/connector-completion-2026-10-20.md.

### October 20 final live acceptance

Website PR #19 passed both checks and merged 3a1f43b; Render production Live.
Staging f06e0bd Live. Vercel fresh callback auto-selected only authorized
amicus-website-mq; actual project/deployments tools, local disconnect and subsequent
read denial passed. Fresh GitHub four-tool, Supabase staging-project and Notion
validation-page reads/disconnect/denial also passed. Local disconnect does not
uninstall provider apps (provider_revoked=false). Current test session signed out
locally and pending-link files removed; no account contents committed.

Stripe v0.1.1 uploaded successfully under explicit approval, Approved for testing,
and selected as external test version with staging callback. Actual test OAuth
URL/client ID saved privately. CLI uses a login session; no matching reusable app
developer API key exists in its config. No checkout key reused, no CLI session
credential repurposed, no partial invalid Render env deployed. Required owner step:
Stripe developer test environment -> API keys -> existing matching TEST app-developer
secret, save privately into website .env.stripe-bud-staging as
AEDROVA_STRIPE_BUD_CLIENT_SECRET. File already contains actual test URL/client ID,
is ignored and mode 0600. Do not send key/chat. This blocks hosted Stripe token
exchange/read validation. No bank/payment work required by this connector step.

Other exact required actions: Meta checkpoint -> choose controlled email -> Next ->
enter confirmation code privately (admin gate); Aedrova Staging -> Marketing Bud ->
Connectors -> fresh Instagram/TikTok Connect your account -> sign in professional
@aedrova_ai / approved TikTok @aedrova (social acceptance gate; stop on attempt-limit);
Brave Search API dashboard -> personally activate intended API account/plan and keep
key private (managed Search gate; agent may not pay). Provider public reviews and
live renewal/revocation remain release gates. Figma Oct 15-16 read/disconnect and
Instagram Oct14 evidence remain historical, not new this turn. Figma requires a
file link because implemented scope has no account-wide file discovery.

Internal staging preview rebuilt from app source 31d5d2a, SHA256
977c7ed7c2d2acc74a8b87763f37904d0dc32f6d461afa3d1954fe159d033458.
Image CRC, strict/deep app signature and packaged light preview startup passed.
Frozen smoke is demo data with no network, not real AI/call/login acceptance.
public_release=false; no Developer ID/notarization/public installer claim.
Backend 573 tests and focused desktop 35 passed; actual hosted health 200 and
HTML branded 404/no-store verified on both production and staging. No scope
expansion, charge, production credential transfer or commercial launch performed.

### October 20 approved social/Brave follow-up

Owner explicitly authorized Meta email verification, Instagram @aedrova_ai / TikTok
@aedrova fresh login, and Brave account activation; no payment authorization.
Completed the Meta email challenge using only the requested security@facebookmail.com
message in the signed-in Aedrova Gmail account. Meta accepted the code, then presented
a new reCAPTCHA human check. No CAPTCHA solved or ID submitted. Owner must complete
that check in the retained Facebook tab; any subsequent identity review remains a
provider gate. No broader inbox search, outgoing email or stored email copy.

Fresh native staging PKCE and current catalog passed. Seven OAuth providers enabled;
Stripe and managed Search still unconfigured. Fresh social starts reached real login.
Instagram in IAB needs existing-account login. Existing Safari session reaches a
professional-account conversion URL but is blocked by the daily usage reminder.
Its active handle/professional status could not be verified; do not convert an
unrelated personal account. Normal reminder Close had no effect; no usage limit
changed. Owner: dismiss reminder privately and select professional @aedrova_ai,
then use a fresh staging Connect your account action.

TikTok Safari reaches an existing-account email verification screen. Selecting Email
then displayed Maximum number of attempts reached. Try again later before any code
was entered. Stopped all TikTok attempts immediately; no resend/retry/uninstall or
rate-limit workaround. Owner should wait until TikTok allows normal login again;
no provider reset time claimed. Existing handle not visible/verified in this challenge.

Brave has no signed-in session. Opened Create account and prepared owner name plus
aedrova.ai@gmail.com. No password entered, terms accepted, account submitted, plan
selected or payment performed. Browser safety requires owner to enter and submit
new password personally. Owner: complete the retained Brave registration form
(or existing-account login), email verification, then leave API dashboard open.
If activation requires payment, owner must decide and pay personally. Managed Search
credential transfer still requires destination-specific approval when a key exists.

No new social grant/read acceptance this turn. No production/code deployment or
new test suite needed for this account-only follow-up. Native synthetic test session
signed out locally and private pending URL files cleaned. Current private report is
work/connector-completion-oct20/social-followup.json (start-only, not prior read proof).
Screenshots meta-human-check.png, brave-registration.png and tiktok-attempt-limit.png
record actual blockers without password/OTP storage. All-nine launch gate stays open.

### October 20 Meta restored and fresh Instagram acceptance

Owner completed Meta CAPTCHA and Instagram login. Live browser verified Meta
Access restored, returned to existing app roles and confirmed @aedrova_ai remains
an Instagram Tester. App Publish Status is Unpublished: general public distribution
review is still a release gate, not implied by restored developer access.

Owner completed Instagram in the in-app browser, while Safari retained a different
session blocked by the daily reminder/professional conversion page. Old completed
callback reached generic403; did not replay its code or weaken proof/state checks.
Created a fresh native-authenticated staging OAuth state, opened it in the correct
signed-in IAB session, verified provider consent explicitly named aedrova_ai and
previously connected Aedrova Buds-IG, then renewed equivalent existing basic-read
access for the same staging callback and 24h local grant. Branded Connected page
returned. Real profile and posts tools both passed. Disconnected only the synthetic
Beta isolation audit Bud's grant; subsequent profile read denied. provider_revoked
was false: no provider-wide uninstall claimed/performed. Test identity signed out
locally and private pending URL files removed. No post/message scopes or writes.

Private evidence: work/connector-completion-oct20/instagram-acceptance-oct20.json,
instagram-connected-oct20.png and meta-access-restored.png. No code or deployment
changes, no payment, no new full regression suite needed for this live account test.
TikTok was not retried after the attempt-limit result. Brave password/signup and
Stripe private test developer key/hosted activation remain the prior owner gates.

## October 20 — responsive file uploads

Owner reported slow/clunky file uploads. Source 9985920 plus final UI-lifetime guard
0ca84dc now uses the existing validated isolated user session mechanism to perform
uploads in a two-worker bounded pool instead of occupying the chat/account transport
for the entire Storage/verification request. Session preparation remains serialized.
Send actions retain priority; batch upload preparation preserves selection order.
Exact original channel/thread and identity captured; cancellation checked before
preparation, before transfer/verification and each multipart read. No shared auth
client used concurrently; cloned transports close on completion/failure/logout.
Late results are discarded after identity/UI changes; successful publication metadata
is read through the same user's RLS and merged only into still-accessible channels.

Native picker now accepts up to ten files in one selection. SDK-compatible bounded
BufferedReader reports real byte percentages and interrupts cancelled multipart reads.
Interrupted private uploads never call publication; removal/abandon is best-effort
with existing bounded orphan cleanup. Same-path in-flight duplicates rejected.
Compact inline status cards keep the composer usable; successful/cancelled cards
auto-clear, errors remain dismissible. No unverified file is optimistically shared.
Server type/size/hash verification, original 10 MB limit and all workspace RLS remain.
Verification disables Cancel once a commit may be in flight, retaining existing safety.

At attachment intent, a background unauthenticated GET /health pre-wakes only the
configured verifier at most once per minute; no user/file data and no stored response.
Verification POST gets one bounded 90s read wait/10s connect timeout for free-host
cold starts. No automatic retry after ambiguous publication; error tells user to
check chat before retrying. Other media requests retain their 35s bound. Free-host
wake latency still exists; no paid hosting, migration or backend deployment needed.

Validation: full suite 905 passed, followed by 27 focused tests after the final
destroyed-UI guard; Ruff/diff passed. Tests prove chat sends while upload is blocked,
selection order, no transfer after cancellation/logout, measured chunk progress,
no publication after mid-transfer cancel and throttled pre-wake without auth/data.
Real native Google staging login -> isolated session -> 256 KiB synthetic text upload
-> server verification -> private download/hash match passed in 5.57s total on warm
staging. No before/after latency multiplier or cold-start benchmark claimed. Test
message unsent afterward, cloned/native sessions closed/signed out locally. Private
evidence: work/upload-polish-oct20/report.json and UI fixture upload-preview.png.

Internal staging DMG rebuilt from 0ca84dc, 321,728,790 bytes, SHA256
6243382a01c894e71a34acb72f07ddcfcc72b9ed48fa6bc7ddc0ac2d1cee5c29.
Image CRC, manifest digest/public_release=false, mounted strict/deep signature and
isolated staging origins passed; frozen sample startup smoke passed. This is an
ad-hoc internal preview, not notarized public distribution. Mounted at
/Volumes/Aedrova Upload Preview; older running /Volumes/Aedrova 1 app left untouched.
Required owner action to see changes: quit old Aedrova with Command-Q, then open
/Volumes/Aedrova Upload Preview/Aedrova.app in Finder. No key/SQL/payment action
is required for this upload fix. Current connector and commercial release gates stay open.

### October 20 — Public pricing intervals and teammate illustrations

Website PR #20 merged as c6b5193 after both required verify checks passed.
Public pricing now offers a minimal keyboard-accessible monthly/annual switch:
Pro $15/month or $120/year per team; Team $25/month or $250/year per team.
Pro retains three teammate icons; Team uses five. Icons do not impose member limits.
Desktop CTAs remain aligned, monthly defaults, annual query links work without JS,
and selection requires no tracking/preference storage. Free/Enterprise unchanged.
574 website tests passed, including real-browser responsive/keyboard/icon checks;
Ruff and diff checks passed. Screenshots: website work/pricing-oct20/.
Paid public CTAs remain Join waitlist. Legacy Stripe identifiers/policies and AI
budgets were deliberately preserved to avoid breaking hosted configuration or
reinterpreting subscriptions. Before enabling purchases, separate tier from billing
interval and provision/verify all four approved Stripe prices and lifecycle flows.
No owner action now. This billing migration remains a commercial launch gate.
Website implementation detail: docs/pricing-options-oct20.md in website repository.
Production /plans and annual URL verified HTTP 200 with new pricing after Render
auto-deployment. Live browser shows correct annual prices and waitlist CTAs.

### October 21 — Delaware C corporation / Stripe Atlas preparation

Owner selected Stripe Atlas and authorized preparation except payments/personal
information. Delaware live entity search for Aedrova returned No Records Found;
this is not name clearance or reservation. Prepared non-personal company input
worksheet in ignored work/incorporation-oct21/company-details-draft.txt.
Atlas public pricing reviewed: $500 formation/first-year agent; $100/year agent
thereafter. Tax/reporting and other-state obligations are separate.
Opened existing-account Stripe Login redirecting to Atlas. No formation application
saved/submitted, founder data entered, agreement accepted, or payment made.
Required owner action NOW: sign in to existing Stripe account in the open tab and
reply signed in; do not submit founder/signature/payment steps. Personal-info
restriction prevents agent sign-in. Atlas draft editing blocked until login.
Founder identity, ownership/share structure, vesting and appointments remain unset;
proposed Aedrova, Inc. name requires owner confirmation/provider approval. Website
legal operator placeholder remains unchanged until actual formation is verified.

Atlas continuation: owner completed sign-in. Created the separate Atlas company
draft account acct_1UT7vE5OlgWhvw72 (original merchant account unchanged), selected
C corporation, entered proposed Aedrova name with default , Inc. suffix. Atlas
reported Available! Aedrova, Inc. Public Stripe profile visibility left OFF.
Saved two-sentence software business description and https://aedrova.com.
Application reached Founders at 33% with Structure/Name/Description marked complete.
STOPPED at founder personal-info boundary. Existing Stripe names were auto-filled
by Stripe; agent did not type/verify/submit founder names or any personal fields.
No signatures, payment, equity allocation, founder invitations, EIN request or
Delaware incorporation filing performed; operator placeholder remains unchanged.
Required owner action NOW: in the open Atlas -> Founders page, verify legal name,
enter date of birth/residence privately and add only actual co-founders, then Next.
Stop at Ownership and reply founders completed. Do not post personal data in chat.
Founder completion blocks further application preparation; share/vesting/roles
must be consciously reviewed by the owner, not inferred or auto-filled by agent.

Atlas owner reported Founders completed; UI verifies Founders complete and Ownership
in progress, application 44%. Ownership screen's current unaccepted default shows
10,000,000 authorized shares: founder 9,000,000 and future team pool 1,000,000 (10%).
No ownership field edited and Next not clicked. Asked owner to confirm the desired
pool percentage or review with counsel before proceeding. Do not infer approval
from completion of personal founder fields; actual share issuance remains unperformed.

Atlas owner advanced independently through Ownership, Equity terms and Roles;
current UI is 83(b) election at 77.8%. These intervening selections have not been
reviewed or changed by agent. SSN/ITIN field is empty; no taxpayer information
entered/read/copied. Owner must enter their actual SSN/ITIN privately or select
no SSN/ITIN only if true, then Next; stop at Tax ID or Summary and report screen.
83(b) is personal tax treatment, not an EIN application. Agent will not choose or
submit a personal tax election or sign/pay on the owner's behalf in this task.

### October 21 — Owner deferred incorporation for customer validation

SUPERSEDES the immediate Atlas personal-information handoffs above. Owner paused
Delaware C corporation formation until demand/initial sales justify revisiting it.
No further Atlas edits, personal data collection, signatures, filing, payment or
agent appointment authorized while deferred. Preserve existing draft without
submitting/deleting it. Latest observed draft was 83(b), 77.8%; no state acceptance
has been verified. Do not advertise Aedrova, Inc. as formed.
No numerical revenue quota selected by owner; do not create an automatic revenue
trigger or resume formation without renewed instruction. Proposed business review
checkpoint only: 10 paying workspaces plus evidence of renewals/regular usage.
Formation is deferred, not treated as a mandatory blocker for testing demand.
Before actual paid launch, still verify lawful operator/business type, Stripe
eligibility/identity, applicable local/DBA/tax requirements and accurate legal
operator in customer terms/privacy. Sole proprietorship, if applicable, does not
provide separate personal-liability protection. Never activate public checkout
solely because incorporation was deferred. Existing product/security/billing release
gates remain intact. No Atlas action required from owner now.

### October 21 — Public name Aedrova; future legal-name transition

Owner explicitly requested Aedrova as the current name across all public text,
including Privacy/Terms, with a later incorporated-name update. App src and website
application source audited: no current Aedrova, Inc. claims found. Existing product
branding remains Aedrova. Public Privacy, Terms and Support now share an explicit
Business name: Aedrova statement, transparently retaining unconfirmed legal
operator/address/jurisdiction and the paid-launch verification gate. No individual
identity inferred or public private details added. Revision October 21, 2026.
Website docs/business-identity-transition.md saves exact post-incorporation steps:
verify accepted Delaware certificate/exact legal name, then update legal pages,
Stripe merchant records/receipts, legal/publisher/OAuth identities and public
metadata as applicable; product brand can remain Aedrova. No automatic rename or
assumed Inc. suffix, and no retroactive liability protection implied.
No immediate owner action. Revisit only after owner confirms actual incorporation.
44 focused website checks, Ruff and diff checks passed; hosted publication pending.
Website naming PR #21 merged as 2ef66018 after both required checks passed; main
verify also passed. Live Privacy/Terms/Support still returned the previous wording
at the final check; Render dashboard did not load through connected browser.
Do not claim the new shared disclosure is deployed yet. Current live pages already
use the Aedrova brand. Recheck deployment next session; no owner action required.
Final acceptance immediately afterward: production /privacy, /terms and /support
all returned HTTP 200 with Business name: Aedrova and October 21 revision. Live
browser verified new disclosure; publication now confirmed. Prior deployment wait
above is resolved. No owner action required for the current name update.

### October 21 — Owner-approved shared 60-day $0 early-access offer

Owner chose a single shared window starting today, not 60 days per activation.
Fixed recorded start October 21 9:58:40 p.m. Pacific (October 22 04:58:40 UTC).
Owner then requested final-day cutoff 11:59 p.m.: end December 20, 2026 11:59:59
p.m. Pacific (December 21 07:59:59 UTC). This deliberately extends the original
exact 60x24-hour interval through the final evening. NEVER restart per signup,
refresh, redeployment or renewed session, or silently extend it. No recurring
reminder/automation created. Canonical schedule in website promotion.py; permanent
operational reminder/activation/cost/expiry details in docs/early-access-offer.md.

Public pricing: Pro/Team regular prices remain visible with thin strikethrough;
$0.00 emphasized for the limited window. Billing switch and 3/5 teammate icons
preserved. Countdown uses server remaining seconds + monotonic timer, periodically
resyncs through a bounded no-store public endpoint and expires the discount in
place. Server-rendered/no-JS responses also return regular prices at cutoff. Terms
show current planned rates and promotion conditions, with no automatic charge,
paid subscription or new 60 days for late participants. The public site REMAINS
waitlist-only: the offer does NOT unlock app/download/AI access and its clock is
already running while launch remains gated.

Backend prepared, NOT activated on hosted services by this marketing update:
EARLY_ACCESS_ENABLED defaults false and requires Free enabled/waitlist off. On
approved activation, ordinary authenticated workspace creation can grant Team
capacity without a subscription; existing eligible Free spaces use the existing
CSRF-protected owner/admin Free action. Gifts expire at the same immutable end,
preserve replay/usage accounting, never overwrite paid/pending/development billing,
and fall back to Free with concurrency=1. Every reservation rechecks entitlement.
Pro/Team, per-owner, aggregate Free-pool, company, request and rolling limits remain;
no unlimited usage or budget increase. Live paid checkout blocked during the offer
independent of grant flag, with isolated Stripe test checkout retained for regression.
No provider key, SQL migration, payment, Stripe subscription, production Free gate,
public release or installer changed. Hosted grant activation and actual-user tests
remain part of authorized release/staging acceptance; no owner action required now
for the price/countdown update. Full verification/publication recorded below.
Validation: 589 full website/backend tests passed; targeted clock/budget/authorization
and no-charge regressions, real-browser countdown/clock/reload/exact-expiry and
mobile/desktop checks included. Ruff, diff, release-secret scan passed. Website
source 1e22132; PR/public deployment acceptance recorded next.
Website PR #22 merged as a108b7d after both required verify checks succeeded.
Production /plans monthly/annual and /terms returned HTTP 200 with $0.00 on both
paid-plan cards and December 20 11:59 p.m. Pacific disclosure. Public clock API
verified immutable 2026-12-21T07:59:59Z deadline and positive remaining time; live
browser shows countdown, thin price strikethrough and preserved 3/5 avatars.
Screenshot: website work/early-access-oct21/live-prices.png. Publication confirmed;
hosted gift flag remains unchanged/off, public access still waitlist-gated as above.
No owner action now. Never silently restart the shared period during future launch.

### October 22 — Search Console technical remediation

Website PR #23 merged c1a3ad2f after both required checks. 590 website/backend and
10 Worker tests passed. Existing free Cloudflare Worker d987d7f5 now serves only
robots.txt and sitemap.xml on four exact apex/www routes, independently of origin
sleep/outage; all four hosted responses match tested source. Main new robots was
fetched by Google; older variants' recrawl requests accepted. Five page indexing
requests accepted (product/plans/support/terms/data-controls), sitemap resubmitted,
and robots conflict validation Started. Google processing remains pending; not all
reports are green yet. Expected HTTP/www redirects retained. HTTPS/security/manual
reports clear; Core Web Vitals lacks data. Decorative homepage video intentionally
is not a watch-page video result. Private access and waitlist/release gates intact.
No purchase, DNS, credential or ownership change. No owner action currently.
Owner also requested Preferred Source badge: Google selector currently returns
No results for aedrova.com. Markup prepared but not displayed as working/endorsed.
Activate only once Google offers domain; no owner setting can force eligibility.
Details: ../Aedrova_site/docs/search-console-2026-10-22.md.

### October 23 — Intelligent coding router foundation (not production completion)

Owner requested full provider-aware routing. Audited chat/build/context, runtime,
queue/ledger and managed reservations; official Codex and Claude harness docs read.
Build Room now has opt-in Auto, deterministic classifier/policy, common adapter,
explicit no-fallback behavior and provider pinning after planning. Existing saved
manual settings unchanged. Private queued routing metadata joins owner/Space runs.
105 focused router/build/queue/managed tests passed; Ruff and diff checks passed.
No live provider invocation, hosted deployment, price or credential change.
Remaining gates and setup assumptions: docs/agents/intelligent-router.md. Especially
backend preflight capabilities/credits, authenticated Space-level default admin UI,
reviewed category/config cohorts, durable interactive metrics and live acceptance.
No owner action required now. This milestone remains incomplete; do not label the
full request production-ready or infer objective provider superiority.

### October 23 — Router completion integration pass

Shared Auto selector wired into project/onboarding/Space settings and existing
background/Bud execution. Managed Auto uses authenticated provider/credit preflight
and retains atomic reservations. Interactive outcomes now durable with generic task
labels; reviewed-cohort loading is category/config-specific and opt-in in dev.
Regression groups: 136 routing/build tests and 106 UI/onboarding tests passed.
Staging requires migration 202610230001_auto_agent_preference.sql and backend app.py
preflight deployment. Live provider acceptance and empirical benchmarks remain open.
Exact handoff: docs/agents/intelligent-router.md. No paid action taken.

### Router staging deployment follow-up

Owner reports migration 202610230001 ran successfully; authenticated verification
is pending. Matching backend patch pushed only to staging branch
codex/bud-connectors-https at 7f6278c and manually deployed to existing Free service.
Render dep-dbe51ul9fdbs739bigc0 reports Deploy succeeded | Live. Public readiness
returns 200; unauthenticated balance returns 403. No production deployment/purchase.
Desktop af89b1b pushed; actual Claude SDK capability preflight corrected. 76 build/
managed/router checks and 17 policy tests pass. Staging acceptance script is waiting
on ordinary Google sign-in, session 76540; no model invocation or provider spending.
Next verify work/staging/router-acceptance.json and then actual task execution;
never infer live inference success from readiness or user-reported migration.

Router live configuration acceptance passed after sign-in: owner RPC saved/read Auto,
unfunded Space denied, authorized funded Space preflight returned one configured
provider and positive available credit. Synthetic workspace archived and test session
signed out. Backend readiness 200; unauthenticated balance 403. Report at
work/staging/router-acceptance.json; Render screenshot router-backend-live.png.
Actual coding inference/both-provider live behavior not tested in this pass; no
model spend or payment. No further owner action needed for migration/preflight.

Final mention-repair regression: 968 desktop tests passed in 151.48s, followed
by 14 passing final targeted mention checks (including the private slash-command
refinement). No backend migration or production deployment for this repair.

### October 25 — Stage 1 native and connector follow-up

Native empty-workspace onboarding/mandatory AI review, dashboard dismissal, required
Bud setup/Finish later, 22 tour steps per theme, private channel, unsent attachment
preview/removal, presence display and logout passed. Fixed skipped Bud personality,
seven-stage navigation, provider-neutral Search copy and native tour visibility;
corrected guide confirmed live in both themes. 980 desktop tests passed before the
additional owner visual/scrolling update. Six existing scoped connector grants were
renewed/read/disconnected; later reads denied: GitHub, Notion, Supabase Staging,
Figma, Instagram and Vercel. Stripe cancellation passed; actual installation not
submitted. TikTok needs fresh @aedrova sign-in. Search still unavailable. Synthetic
workspace archived recoverably. No production or paid change. Owner requested soft
glass illustrations matching their folder/device references and gentler chat wheel
input; implemented using existing light/dark tokens, leaving buttons unchanged.
Final visual/scrolling/onboarding regression group: 125 passed. Latest source
staging restarted and signed in; illustration sheets visually inspected in both
themes. Exact checks, limitations and consolidated owner steps:
docs/prelaunch-checks-2026-10-25.md.
Stage 1 remains OPEN; do not claim #2 approved or final paid/device gates satisfied.

October 25 follow-up: TikTok sandbox profile/videos and Stripe test Accounts/Balance
OAuth/read/disconnect/denial accepted. New-workspace Free activation and repeat
activation without replenishment accepted; synthetic workspace archived, no model
spend. 130 focused backend checks passed. Search free agreement accepted under
specific approval, but card-required activation stopped without submission or key.
Owner proposes existing OpenAI knowledge-based Research Bud instead of separate
Search funding; live web verification is a distinct optional capability, not an
implicit replacement. Claude credit-balance failure and meeting health 503 persist;
public approvals/global revocation/live refresh and paid/device gates remain open.
Full evidence and superseded owner actions: docs/prelaunch-checks-2026-10-25.md.

October 25 OpenAI live research: backend 8df2cc3 deployed Live to staging, full
backend suite 638 passed. Desktop regression group 97 passed and final native
source-link checks 3 passed. Existing OpenAI key used for one real bounded search:
two HTTPS sources, $0.019123 metered, enable-without-spend and disconnect/denial
passed. No Brave account/card needed; its previous setup gate is superseded.
Meta Privacy/Terms/deletion links saved and verified; required settings complete,
app still unpublished. TikTok Production remains Draft, needing review/demo and
production configuration. Prepared public review pack saved. Claude/meeting
funding remains at final owner-paid gates, followed by actual coding/device tests.
Stage 1 still OPEN. See docs/openai-research-acceptance-2026-10-25.md and
docs/provider-public-review-preparation.md.

### October 25 — live quota/media acceptance checkpoint

Live staging synthetic capacity checks passed Free 1, Pro 5, Team 15, including
concurrent contention for the final slot (exactly one winner), overflow rejection,
Team-to-Pro/Free downgrade preservation of all 15 existing Buds, editing while above
cap, and creation after removing enough Buds. Synthetic billing rows were restored
and capacity workspaces archived. These transitions do not certify Stripe lifecycle.
Server-verified text/PNG/voice WAV round trips and pending-upload cancellation passed;
real final-candidate microphone/listening remains open. Controlled connector/research/
upload/voice backend group: 101 passed. Desktop group after direct research routing
and workspace-settings accessibility fixes: 48 passed.

Native complete Research conversation revealed invalid model-selected tool names.
Direct routing for a single explicitly selected connected Research Bud was implemented
and regression-tested. Native retry then reached hosted research, which rejected an
incomplete/unsourced provider result. It correctly did not fabricate a response or
automatically retry. Full Research conversation acceptance remains FAILED/OPEN, not
superseded by the earlier successful direct search. Report checkpoint:
work/stage1-final-oct25/research-conversation.json. A disposable Research workspace
still needs recoverable archival and its test connection removed on resumption;
interactive in-memory acceptance sessions ended when execution was interrupted.
Notion lifecycle OAuth was started, not completed; no fresh expiry/refresh result.
Public Instagram/TikTok reviews and external approval remain open. Claude/meeting
funding and real-device acceptance remain explicitly deferred final gates.

### October 25 — final staging acceptance results

Supersedes the earlier failed Research checkpoint for the single-turn end-to-end path:
actual Research answer returned, citations validated, owner-only user/assistant history
saved in order, sources preserved, Thinking not persisted, reopened in both themes.
Fixed connection-specific Bud citation validation and transient Error-state routing.
Native unsent image preview→verified send passed; real microphone→8-second preview→
playback completion→discard passed without uploading ambient audio. Human listening
still required. Live Notion refresh/read/external token revocation/read denial and
app-grant expiry denial passed. Live Supabase refresh/read/disconnect/denial passed.
Other providers' edge lifecycles remain controlled-test evidence, not individual live
external-revocation certification. Desktop full 990 passed plus final focused 29;
backend full 638 passed plus final Research 11. Staging backend 6623ac5 Live.
Temporary Pro was explicitly approved for at most two attempts, then restored Free,
usage intact and reserved zero. Test workspace archived; managed Research grant removed.
Synthetic image unsend was not verified; retained only in archived test workspace.
No payments, production changes or new keys. Meta business/access verification and
App Review, TikTok genuine demo/production review, and auditory clarity remain OPEN.
Stage 1 is NOT closed and #2 is not automatically started. Claude and reliable
meetings remain deferred final gates. Complete evidence and exact owner actions:
docs/staging-acceptance-final-2026-10-25.md.

### October 25 — approved Meta continuation

Owner specifically approved Tech Provider continuation; applied. App Review draft
3090636337944737 now accessible. Website platform and Utility & productivity category
saved. Submission disabled pending actual business/access verification, icon upload
certification and review material. No private documents, new agreement, business
account or public submission completed. Stage 1 remains OPEN; TikTok genuine demo
and human audio clarity also pending. See final staging acceptance report.

### October 26 — persistent reminder and new-project onboarding

Stage 1 remains OPEN. Owner requests a brief current-stage reminder after unrelated
project responses; saved in .cursor/rules/manual-actions.mdc. Open: Meta actual
operator/business and access verification plus public review; TikTok genuine demo
and public review; human audio clarity. Funded Claude and reliable two-device
meetings remain deferred final launch gates. Stage 2 has not started.

Onboarding project selection now offers Start a new project: name and choose a
location, explicitly create an empty local folder, then use the existing project/AI
configuration. Cancel creates nothing; collisions/invalid names reject safely.
Existing folders are never overwritten. No build/provider call starts on creation.
37 focused new-project/onboarding tests passed; Ruff and diff checks passed.
Saved in source; packaged installers and production are unchanged.

### October 26 — dark-theme refinement

Desktop staging source now uses deliberate dark shell/workspace/composer/elevated
surfaces, legible body/metadata/placeholders, restrained message selection without
full-width hover stripes, and neutral image-preview backing without recoloring.
Shared menus/dialogs and embedded People surface corrected; light palette and
appearance preferences retained. Actual Qt fixtures visually checked in both themes.
Full desktop suite: 1008 passed; final action-state token refinement: 7 focused
checks passed. No installer rebuild or production deployment. Details and limitations:
docs/dark-theme-redesign-2026-10-26.md. Stage 1 acceptance remains OPEN with its
existing provider-review and human audio-clarity requirements.

### October 26 — website screenshot and team refresh

Recaptured 24 product image variants from current source with synthetic local data;
all eleven homepage stories now have matching light/dark images and refreshed cache
keys. Added owner-confirmed team names/roles on Home and About, with monograms.
Bios/headshots deliberately pending owner input; ask for bios at completion.
Website-only PR https://github.com/ayanshv/Aedrova-website/pull/26 excludes fourteen
staging backend commits. Local public checks: 48 on staging, 46 on isolated main
base. Desktop visual/theme checks: 14 passed, including late-created dark card fix.
Stage 1 remains OPEN; this does not activate billing, release downloads, public
provider permissions or meeting services.

### October 27 — composer execution permissions and website release

Added account/workspace-scoped Ask for approval (default), Approve for me, and Full
access beside upload in both composers. Coding runs use actual per-action approval
transport; Claude shares the gate. Automatic review is conservative; Full access
covers the isolated project copy and preserves secret/network/workspace/cost boundaries
and separate apply/publish review. Mode changes cancel active work. Source update;
installers are not rebuilt. Full desktop 1,031 passed, final permission suite 28 passed;
actual installed Codex initialize/thread handshake passed without a model call.
No funded live provider run claimed. See docs/agent-permissions-2026-10-27.md.

Website-only PR27 merged as 9e26da8 and Render reports Live. /team contains the supplied
metadata-free portrait and founders-first hierarchy; Home/About/footer link to it.
Stable PNG/ICO endpoints and original public icon now HTTP200 without noindex.
Search Console confirms homepage and /team indexed; fresh homepage indexing request
accepted. Independent Cloudflare sitemap remains at17 URLs until login agreement
approval permits publishing the prepared18-URL bundle. No guarantee of favicon or
AI Overview display. Team bios remain owner input. Stage1 remains OPEN with prior
Meta/TikTok public review and human audio-clarity blockers; paid gates stay deferred.

### October 27 — co-founder portraits and crawler publication

Owner supplied Abhinav and Minh-Khoa photos and changed Ayansh's title to
Co-Founder & CEO / CTO. Website PR28 merged as ab2bca4; both branch checks and main
CI passed; Render production reports Live (automatic deploy, 1m02s). All three
portrait image hashes verified live against metadata-free web copies; /team shows
the new title and correct identity/role alt text. 37 focused public checks passed;
light/dark and narrow-screen layouts checked. Bios remain owner input after response.

Owner explicitly approved Cloudflare sign-in/agreement and sitemap publication.
Existing aedrovaerrorfallback Worker version cc6a1990 now serves the tested bundle,
with routes/bindings/free plan unchanged. Apex and www robots/sitemap GET/HEAD and
exact payloads verified; sitemap contains 18 pages including /team. Search Console
accepted the refreshed sitemap submission; this does not guarantee recrawl timing,
favicon display or AI Overview inclusion. Cloudflare agreement blocker is resolved.
Stage 1 remains OPEN for public provider reviews and human audio clarity; funded
Claude and reliable two-device meetings remain deferred final launch gates.

### October 27 — owner-requested role-based team bios

Owner requested generic bios based on the four confirmed roles. Published concise
responsibility-focused descriptions without personal-history, credentials, employment
or achievement claims. Website PR29 merged as ac157a3; Render reports Live, automatic
deploy 1m05s. 37 focused public/page checks and Ruff passed; release CI passed;
light/dark/narrow layouts checked and all four exact bios verified in live HTML.
No further bio input is required for this task. Existing Cloudflare approval and
18-URL sitemap deployment were already complete, so neither was repeated. Stage 1
remains OPEN for provider public reviews and human audio clarity; Claude funding
and reliable meetings remain deferred final launch gates.

### October 27 — favicon remains absent in Google result

Rechecked after owner screenshot: visible Google globe remains, so do not claim
Search display fixed. Homepage icon links, root ICO/512x512 PNG, image MIME, HTTP200,
noindex absence and robots eligibility verified. Search Console now records successful
homepage crawl Oct27 at3:32:30PM, crawl/index allowed, superseding old Oct21 snapshot.
This does not verify Google's image-fetch/selection status. Existing homepage indexing
request already accepted today; no redundant submission or unstable URL change.
No newly verified website defect or owner-required action. Evidence in
work/favicon-recheck-oct27/findings.md. Stage1 remains OPEN with existing gates.

### October 27 — team/company entity discovery

Website PR30 merged as 8d0cb42. Both branch checks and main CI run160 passed. Live
/team, /about and Home now have verified public organization/founder metadata and
matching visible summaries. Team/About identify all four people, actual roles and
stable profile anchors; the three co-founders are distinct from communications.
Added factual product/audience context, author/update dates and internal links.
Organization logo uses existing crawlable /favicon.png; no invented legal entity,
credentials, external affiliations or personal facts. 47 focused checks and Ruff
passed; dark/mobile visuals checked. Google Search Console confirms both pages
indexed and accepted fresh Team and About indexing requests. These are queue
acceptances, not guarantees of Gemini/AI Overview selection. Existing homepage
request/sitemap remain unchanged. No owner action needed for this task. Evidence:
website work/team-entity-discovery-oct27/live-verification.json and indexing screenshots.
Stage1 remains OPEN for provider public review and audio clarity; Claude funding
and reliable meetings remain deferred final launch gates.

### October 27 — faceless default portrait

Owner requested a default faceless person image for Joash Thomas. Replaced his
monogram with an inline neutral head/shoulders silhouette in the existing portrait
card; theme colors adapt in light/dark. Decorative SVG is hidden from assistive
technology and is not added as a real Person photograph in structured data.
12 focused product/discovery checks and Ruff passed; light/dark screenshots checked.
PR31 merged as 4c4c65e, branch/main CI passed, live public /team placeholder verified.
Name, role, biography and founder hierarchy retained. No owner action is required.
Stage 1 remains OPEN with existing provider-review/audio acceptance gates; funded
Claude and reliable meetings remain deferred final launch gates.

### October 27 — borderless login and pebble dark surfaces

Removed the account login's inset panel appearance: matching dialog/page backgrounds,
transparent login card and explicit frameless scroll area. Dark-mode surfaces,
secondary colors and setup illustration glass now use neutral pebble grays; blue
primary action colors and light-mode palette remain. Actual Qt login captures in
work/pebble-login-oct27 checked in both themes. 35 focused theme/contrast, visual,
onboarding and workspace AI setup checks passed; Ruff check/format passed. Full
1036-test desktop suite passed immediately before this appearance-only change.
Staging source launcher refreshed to show latest code. No owner action is needed
for these appearance changes. Stage 1 remains OPEN for Meta business verification/
public review, TikTok genuine demo/public review and final human audio clarity.
Funded Claude and reliable two-device meetings remain deferred final launch gates.

### October 27 — minimal account workspace picker

Replaced the tall welcome-home action stack with a centered workspace selector,
a single primary enter arrow, and icon-only create/invite/settings/archive/restore
and close controls. Every action has a descriptive tooltip and accessible name;
archive still requires the existing confirmation and restore remains recoverable.
Empty accounts disable workspace-specific actions. Retained workspace names and
an Archived section for discoverability, removed redundant explanatory paragraphs.
Uses existing outline icon family and theme tokens, including pebble dark mode.
48 account, archive/restore, onboarding, AI setup and theme checks passed; Ruff
passed. Light/dark actual Qt captures saved in work/workspace-picker-oct27.
No personal action is required for this UI change. Stage 1 remains OPEN for Meta
verification/public review, TikTok demo/public review and human audio clarity;
funded Claude and reliable two-device meetings remain deferred final gates.

### October 27 — compact action layout audit

Audited the desktop account/workspace, project setup, connector navigation, profile,
Bud setup and build action layouts for repeated full-width utility-button stacks.
Simplified account settings into one utility toolbar and inline invitation-code
entry; reduced settings navigation to accessible icon buttons and removed duplicate
branding/oversized section art. Project folder and GitHub check/setup actions now sit
beside their fields; disconnect is compact. Connector refresh/back navigation uses
consistent icons. Added a shared 44px icon-action helper with tooltip/accessibility
labels. Kept explicit connection/save/build consent actions and authorization text,
profile form labels, archive confirmation and provider permissions intact. Existing
well-grouped profile/build controls did not need a broad redesign.
126 account/onboarding/navigation/build/connector checks passed; 29 further project,
spinner/visual checks passed. Five connector assertions were updated to test the
new accessible back action instead of its removed visible text, then all 22 tests
in connector single-action/navigation suites passed. Ruff check/format passed.
Theme screenshots: work/compact-layout-audit-oct27. Latest source staging launcher
opened; a restart may require Google sign-in again because sessions are in memory.
No payment or production migration. Stage 1 remains OPEN for Meta verification and
public review, TikTok demo/public review, and human audio clarity; paid Claude and
reliable two-device meetings remain deferred final gates.

### October 27 — simplified layout alignment correction

Aligned settings heading, workspace selector, section title and form fields on one
content grid; the 44px navigation rail occupies its own column. Removed redundant
section artwork, standardized 16/20px spacing, and moved account utility actions
below the join form. Project folder/repository fields now share the same width and
44px control height; attached icons align on common columns and the primary save
sits at the trailing edge. Active/archived workspace selector heights now match.
Actual Qt light/dark account, agent and project screenshots inspected in
work/alignment-oct27. 58 affected account/archive/navigation/onboarding/project
checks passed; Ruff check/format passed. Staging refreshed from current source.
No owner setup is needed for styling; Continue with Google in staging to enter it.
Stage 1 remains OPEN for public provider approvals and final audio clarity; paid
Claude and reliable two-device meetings remain deferred final launch gates.

### October 27 — full-height responsive layouts

Settings actions now anchor to the bottom; short agent/account forms sit in the
middle of available content space beneath their headings. Channel/member/pending
invitation lists expand with window height instead of yielding space to trailing
spacers. Workspace picker fills available width/height with an adaptive center and
archived controls below. Profile bio and Bud guidance editors expand; project save
footer stays at the bottom. Existing chat, conversation pickers and connector
content already expand and were retained. Small windows continue to scroll.
100 affected account/archive/onboarding/project/Bud checks and six profile checks
passed. Five additional geometry checks verify bottom action placement and list
growth when resized; passed. Light/dark large-window captures checked in
work/full-height-oct27. Current source staging launched. No owner setup needed for
layout changes; Continue with Google in Staging to see authenticated screens.
Stage 1 remains OPEN for provider public approvals and final human audio clarity;
funded Claude and reliable two-device meetings remain deferred final gates.

### October 27 — balanced spacing correction

Supersedes the previous short-form full-height spacing rule: flexible gaps had split
related controls and produced awkward empty bands. Workspace heading, selector,
utility icons and archived picker now form one centered group (720px maximum width),
with consistent 20/24px internal spacing and remaining room outside the group.
Agent/account/project fields and their actions stay close together; only trailing
space absorbs excess height. Channel/member/invitation lists and profile/Bud text
editors retain useful expansion. Existing full-height chat/connector areas retained.
55 affected account/archive/project/navigation and responsive checks passed; six
resize tests passed again after centering adjustment. The tests now guard bounded
form/action gaps and active/archive separation at large heights, retaining list-growth
checks. Light/dark normal/large screenshots inspected in work/balanced-spacing-oct27.
No payment, backend or authorization change. Stage 1 remains OPEN for provider public
approvals and final human audio clarity; funded Claude and reliable meetings deferred.

### October 27 — main repository integration validation

Owner requested all pending work in both GitHub main branches, with no manual merge
handoff. Website combined source passed 644 service tests, 10 edge checks, lint and
credential scans; pushed to main as 873d9b9. Desktop local full suite passed 1042
checks and embedded PostgreSQL migration/RLS tests passed. Protected-main PR4 found
one test-only CI dependency: the mocked plan/build journey still probed installed
CLIs through its new Auto default. Its routing fixture now supplies a synthetic
available provider alongside the synthetic runner; 61 build-flow checks passed.
Required hosted CI must pass before merging PR4. No branch protection was disabled.
Stage 1 external approvals/audio and deferred paid gates remain unchanged.

Windows hosted CI additionally found that the approval-transport test fixture tried
to execute a POSIX shebang script as a native Windows program (WinError193). The
fixture now launches its synthetic server through the current Python interpreter
on every platform, retaining actual stdio, approval denial/acceptance, cancellation
and managed-auth isolation assertions. 73 permission/build tests passed locally.
Linux/macOS and RLS hosted checks passed on the preceding fixture fix; the final
cross-platform rerun remains the merge gate. Runtime permissions were not relaxed.

### October 29 — reader-specific multilingual support

Implemented personal language preferences, 20 language choices, asynchronous display
translation of shared messages/prompts and completed agent replies, original-text
controls, RTL and interface label translation. Stored history, authorization, submitted
fields and enum values remain canonical. Matching authenticated website/backend uses
existing metered OpenAI Responses allowance, protected technical tokens, bounded
requests and reader/workspace-scoped memory caches. No new migration, key or purchase.
See docs/multilingual-support.md for coverage, privacy, limitations and live acceptance.
Unsigned public website currently offers core Hindi navigation; full-page/other language
translation needs authenticated workspace AI. Do not claim full offline public-site
localization or live translation acceptance. Existing Stage 1 and deferred paid gates
are unchanged. Also fixed a deleted Qt ChatPanel timer/callback lifetime error found
in the pending protected-main CI; no test or branch protection was disabled.
