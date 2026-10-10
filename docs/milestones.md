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
