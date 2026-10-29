# Launch gate 1 — staging acceptance, October 24, 2026

**Status: PARTIAL / OPEN. This is not launch approval.** Owner approved starting the
first of six prelaunch steps. Production, payment settings, provider scopes and hosting
plans were not changed. Do not proceed to step 2 as though this gate has passed.

## Candidate and environment

- Desktop checkout: `eb7cf2d9fe2596d21b6ab44f5a690436a88ea340`, plus the local test
  coverage additions described below. App PR #3 merged to main previously; the local
  checkout has that tested content, preceding GitHub's final merge-only commit.
- Backend local checkout: `4112ad192f95ed13e84b54cf74ab172166168708` on
  `codex/checkout-idempotency`. These local tests do not establish staging parity.
- Render staging dashboard reports deployed source
  `7f6278c1af09be8cf0c7c3d5dbb759553e6191c7`, deployment Live. Backend checkout
  idempotency changes are therefore not covered by this deployed-source acceptance.
- Public staging profile was validated with production endpoints rejected. Native
  source preview uses a separate fresh preferences file; hosted accounts are existing
  staging test accounts, not newly registered users.
- Hosting remains the existing free sleeping instance. No purchase was made.

## Fresh verification

1. Desktop complete suite: **924 passed**; one Python audioop deprecation warning.
2. Backend complete suite: **598 passed**; one Starlette/httpx deprecation warning.
3. Embedded PostgreSQL migration/RLS suites passed, including optional meeting-order
   cases. Discovered that the runner omitted the latest Auto preference migration;
   added it and `supabase/tests/auto_agent_preference.sql`, then reran successfully.
   The new SQL checks Auto onboarding/persistence, both explicit provider transitions,
   invalid provider rejection, direct-write denial, outsider/member authority,
   removed-member visibility and anonymous rejection. No hosted migration was changed. Added a regression guard that fails when any
   migration is omitted from the runner; that additional test passed separately.
4. **51 hosted checks: 50 passed, one failed.** Liveness/readiness return 200.
   **45 private/gateway route requests** reject anonymous schema-valid requests with
   403, including native media, Bud OAuth, meeting and model endpoints. Foreign Origin
   and invalid bearer requests reject; missing page returns 404. All sampled responses
   retain nosniff and no-store. Checkout/top-up/portal/free-plan mutation routes were
   deliberately excluded from hosted probes. This is not an authenticated tenant test
   for every route or a distributed load/rate-limit certification.
5. Fresh Google OAuth with two existing staging accounts completed. Authenticated
   checks passed: real server-verified private upload/download, cancellation after
   reservation/storage, foreign workspace denial, private-channel member denial,
   removed-member denial, Auto preference RPC/readback, Bud private-history separation
   in both directions, retry idempotency and forbidden cross-user reply linkage.
   Synthetic messages were unsent, Bud soft-removed and workspace archived; sessions
   signed out. No real customer files or speech were used.
6. Authenticated backend model preflight finds **one configured coding provider** and
   an existing funded staging workspace. One bounded synthetic Codex tool-free request
   through the actual app reply function/gateway **completed successfully**: first text
   **11.01 seconds**, total **12.10 seconds**, 25 response characters. The test capped
   output at 256 tokens, used existing staging allowance, closed the run and signed
   out. No tools, project reads, payment, automatic refill or other provider ran.
   This proves one live reply, not low-latency acceptance or full coding-build success.
7. Native fresh-preferences source app launches, Google login returns successfully,
   account/workspace loading finishes, and Go to dashboard dismisses the account
   dialog and opens the first-run welcome intro. Full intro/Bud/highlight-tour,
   composer, hardware and clean-machine workflows remain separate checks.
8. Scoped Ruff and tracked-source secret scanner passed. New acceptance script has
   no stored session/provider credentials; reports omit token values and user emails.

## Connector readiness — authenticated staging catalog

GitHub, Supabase, Figma, Notion, Instagram, TikTok and Vercel report OAuth configured.
This is readiness metadata, **not** a fresh consent/refresh/revocation/resource-read
certification for any provider. Public provider approval/tester restrictions still
need validation. Stripe reports `oauth_available=false`. Web Search reports
`managed_available=false` and has no OAuth login flow. A service API key is an operator
configuration concern, not something every customer should enter.

A disposable newly created workspace reports `no_plan` and zero available allowance.
It safely cannot spend before plan activation. The intended free/early-access activation
path and UX must be accepted before claiming new users can use included AI immediately;
this run did not create a subscription or alter allowances.

## Confirmed blocker and remaining work

- `/health/meetings` returns **503 unavailable**. Reliable meeting, media, consent,
  transcription/review and two-device acceptance cannot pass while the required
  backend/independent guard is unavailable. Do not bypass the guard or flip a flag
  solely to make readiness green. See `meeting-launch-gates.md`.
- Stripe OAuth and managed Web Search are not enabled in the inspected staging
  catalog; verify private configuration and provider account setup before retrying.
- Complete real grant/resource/refresh/revocation tests for every advertised connector.
  No new scopes, permissions or platform agreements were accepted in this run.
- Test both coding providers end to end; only Codex was advertised and exercised.
  Test the real build/review/apply path and budget exhaustion/concurrent admission.
- Complete native required-Bud/Finish later/highlight-tour and composer regression
  checks plus human microphone/camera/playback checks. A 12-second synthetic reply
  is not evidence that every user interaction is responsive.
- Align staging backend with the chosen release candidate before final acceptance.
  Keep checkout idempotency deployment and commercial billing gates explicitly separate.

## Consolidated owner actions / dependencies

1. **Meeting infrastructure, only when ready to fund it:** Render → staging service →
   Compute, personally review current charges and choose always-on hosting; configure
   the separate staging meeting guard following `meeting-launch-gates.md`. Agent must
   not submit payment. This blocks live meeting acceptance, not the passing file tests.
2. **Connector setup:** complete any Stripe developer identity/external-test setup and
   activate the intended Search API account in the providers' dashboards. Use private
   deployment settings for credentials; never paste keys in chat. No purchase is
   authorized. These block the respective connector acceptance, not all app testing.
3. **Physical acceptance after meeting readiness:** provide two devices/test accounts
   with microphones/cameras and personally handle any new OS permission prompts.
   This unlocks audio/video/focus/consent/playback verification that fixtures cannot prove.

Existing authenticated browser sessions allowed the current two-account tests without
new manual sign-in. No new SQL action is required for this checkpoint. Request any
specific new provider grant/agreement approval at the actual consent screen.

Evidence (ignored local operational files):
`work/staging-acceptance-2026-10-24/{hosted-boundaries.json,authenticated.json,ai-live.json,database.log,native.log}`.
Reproducible authenticated runner: `scripts/check_staging_acceptance.py --help`.
Do not commit private configuration, raw browser sessions or operational credentials.

## Ordered follow-up requested October 24

Owner requests the following **only after Stage 1 acceptance is complete**:

- Recognize an agent mention anywhere in a message, including `hey @aedrova wya`,
  preserving text before and after the mention as the prompt. Cover configured agent
  aliases, Bud names, case and mention boundaries without routing ordinary words.
- Preserve the sent user prompt in conversation history while the agent thinks and
  after its result. Thinking updates must replace only their transient agent row;
  refresh, optimistic acknowledgement and persistent message reconciliation must not
  remove the user's prompt or older results.
- Regression-test both behaviors together and verify the actual native conversation.

Owner subsequently authorized implementing these two fixes before Stage 1 closure.
Implementation and focused regression tests are complete; see the follow-up below.
Stage 1 itself remains open while its live gates remain.

## Follow-up candidate — October 24 evening

- Desktop full regression: 954 passed. Backend final regression: 621 passed.
  Planning/retrieval focused checks: 73 passed after instruction clarification.
- Backend 1b155eb deployed successfully to the existing free staging service only,
  on codex/stage1-acceptance. Previous 1f196d6 fixed Stripe external-test chnlink
  URL validation (fixed HTTPS marketplace host and bounded path, no redirects).
- Large harness inference previously treated serialized bytes as tokens. Conditional
  official provider counting now uses fixed provider endpoints, 12-second deadline,
  4 KiB response cap, validated integer counts and conservative token margin.
  Provider errors/malformed counts fail before generation/reservation; actual usage
  settlement, plan limits and no-fallback protections remain. 47 gateway tests pass.
- Real managed greeting was 0.962–1.407 seconds in these samples, no tools/inference.
  Real plan reached the provider after the fix but initially omitted citations;
  validator correctly rejected it. Planning instructions now distinguish permitted
  read-only inspection NOW from future implementation/tests. Live rerun is required.
- Hosted boundaries after deploy: 50/51 passed; /health/meetings remains 503.
- Native tests observed latest Auto selector, GitHub connected confirmation with
  Continue, device enumeration, intro completion and Bud Finish later resuming the
  highlight tour. The user subsequently interacted with the native app; no claim
  of complete tour, microphone listening or two-device acceptance is made.
- Latest authenticated report additionally proves true concurrent Free quota
  admission and presence sharing (Online/Away/DND) across distinct test accounts.
  No production migration or financial change was made.

Additional exact owner dependency: approve copying the existing locally validated
Anthropic API key into Render → aedrova-beta-staging → private
AEDROVA_ANTHROPIC_KEY and selecting config/models.beta.json, then deploying staging.
Do not upload the Claude-only env file wholesale: it would replace Codex eligibility.
This transfer requires specific approval under browser credential-transmission rules;
no secret should be pasted into chat. It blocks live Claude/Auto both-provider proof.
Meeting hosting/payment and physical-device actions above remain necessary. Managed
Search needs operator account activation/private key configuration before its live
reader test; any purchase remains owner-only. Public website quota copy deployment
and the new-workspace early-access/free activation path also remain acceptance gates.

New evidence: work/staging-acceptance-2026-10-24-followup/ including authenticated-final.json,
hosted-boundaries.json, backend-final.log, gateway-live.png and build/report.json.

### Live coding acceptance closed for Codex (latest run)

The final managed Auto → Codex run passed actual planning with inspected source
citations, implementation in the independent build copy, generated unittest execution,
original unchanged before review, guarded reviewed apply and unittest execution in the
synthetic original. No dependency, real project, payment, refill or fallback was used.
Its greeting took 0.826 seconds without inference. Test workspace was archived,
synthetic task unsent and session signed out. See followup/build/report.json and
followup/build/plan.txt. This closes the bounded Codex path, not all coding workloads
or the still-unconfigured hosted Claude path. Local final planning wording and Bud
capacity accessibility text require reloading the source app to take effect.

Stage 1 is still OPEN. In particular, meetings are not accepted while health is 503;
full connector fresh consent/resource/refresh/revoke, Claude end-to-end and new-workspace
included-AI activation remain unverified. The owner's two subsequent mention/history
fixes remain explicitly queued until this stage is complete.

## Mention repair follow-up (owner explicitly changed the ordering)

Implemented explicit @agent mentions anywhere in prose, preserving the text on both
sides while excluding email addresses/name prefixes. Bud mentions retain Bud identity.
Accepted conversational agent prompts are now ordinary optimistic/persisted channel or
thread messages, with the agent activity anchored after the user prompt. They survive
thinking, completion, second prompts and server refresh; no false sent message is
created when agent admission is rejected. Private /build commands remain private.

135 routing/build/messaging focused tests passed, plus 14 final targeted mention checks.
Tracked-source secret scan, Ruff and diff checks passed. Full suite log:
work/staging-acceptance-2026-10-24-followup/mentions-full-suite.log.
Source staging was restarted using the same fresh.ini preferences. Google required
a new passkey confirmation for the previous native account (Vishnu Varma); automation
canceled that prompt and canceled the pending native sign-in. Owner must use Continue
with Google and complete their own account verification. The corrected source app
is open at a usable login screen. This is not a claim of authenticated native live
acceptance for the repaired conversation; automated Qt/transport tests cover it.

Final mention-repair regression: 968 desktop tests passed in 151.48s, followed
by 14 passing final targeted mention checks (including the private slash-command
refinement). No backend migration or production deployment for this repair.


Claude staging follow-up: combined catalog/key deployed and gateway schema defect
fixed at ebb36c6. Both providers advertise correctly. Actual Claude coding remains
blocked by Anthropic API credit-balance rejection; owner billing action can wait
for final paid setup. See claude-staging-acceptance-2026-10-24.md for exact owner
actions, evidence and tests. No key regeneration or additional SQL is required.

## October 25 native/connector addendum

See [current follow-up](prelaunch-checks-2026-10-25.md). This closes the bounded
native onboarding/tour/unsent-preview/logout checks and renews real scoped reads
plus local disconnect/denial for six providers. Older catalog statements that
Stripe is unconfigured are superseded: its test install/permissions page now opens;
installation consent remains pending. Stage 1 remains OPEN for the specifically
listed provider, activation, funding-dependent and physical-device gates.
