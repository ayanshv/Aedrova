# Final Beta and public launch plan

Status: PLANNED ONLY — October 10, 2026. No phase below is authorized for execution
by the request to document this plan. M14 remains deferred until product completion.
The immediate approved work is connector deployment verification, the connector
confirmation layout, reliable logout, and default automatic planning. The waitlist,
prices, checkout availability, Pulse and installer distribution are unchanged here.
The owner-supplied phase proposal is preserved in release-plan-source.md.

## Phase 1 — Establish the release baseline

Inventory app, backend, Supabase schema/RLS, connectors, AI runtimes, website and
billing. Record working, partial, missing and broken states based on evidence;
visible controls alone are not proof. Freeze the first-release feature scope.
Remove Pulse UI, routes and unused code where safe (owner item 12).
Separate development/staging/production accounts, origins, credentials and data.
Review repository access, branch protection, secret scanning and environment
configuration. Introduce release-candidate CI for account, chat, AI, connectors,
billing, authorization and subscription regressions. Push approved work to GitHub
throughout all phases (item 15); keep source, release version and deployment aligned.
Gate: documented release inventory and staging isolation, reproducible checks.

## Phase 2 — Complete connectors and AI providers

Cover every currently offered connector: GitHub, Supabase, Figma, Notion, Stripe,
Instagram, TikTok, Vercel and managed Search; audit any other integration exposed
in the current app. Linear stays excluded per the owner's previous decision;
PostHog is considered only if implementation/inventory identifies it as launch scope.
For each: real login, least privilege, named resource selection, read/action support,
credential expiry, refresh, rate limiting, timeout/error recovery, disconnect,
revocation, reconnect and fresh-customer validation. No manual codes or keys in the
normal customer workflow where provider OAuth permits it. Keep unavailable apps
honest and disabled. Stripe Bud account access is separate from Aedrova billing.
Review and test OpenAI credentials/model access, accounting, caps and failure modes;
implement/verify Anthropic key storage, model requests, timeouts and accounting.
Gate: repeatable acceptance matrix passed for every advertised connector/provider;
public provider verification complete where required. Missing app registration,
provider review and live acceptance remain blockers even when local tests pass.

## Phase 3 — Meetings, voice and file context

Finish meeting capture/transcription with participant notice and consent, transcript
storage, authorized agent use, speaker attribution where supported, long sessions,
interruptions, quality checks and deletion. Implement chat voice-to-text: microphone
permission, explicit record indicator, editable preview, cancel and deliberate send.
Define server-enforced upload size, types, count, storage and parser/time limits;
validate content rather than trusting file names. Exercise oversized, malformed and
malicious uploads. Make room/files/meeting/connector context selection and provenance
clear. Do not silently expose all workspace data to every Bud.
Gate: documented limits, usable failure states and cross-workspace isolation tests.

## Phase 4 — Complete UX simplification and polish

Add separate @ sections for agents and Buds alongside the named main agent; show
purpose/status and support search, keyboard selection and configured avatars.
Audit every screen with one obvious primary action, concise context and progressive
secondary options: signup, workspace, invitations, chat, connector/Bud setup,
approvals, generated results, settings, errors, billing and deletion. Test loading,
empty, success, disabled, keyboard, focus, scroll and responsive states. Finish the
whole-product UI pass before recording updated website screenshots.
Gate: new users can complete core journeys without founder help; no dead controls.

## Phase 5 — Privacy, legal, data controls and business readiness

Map actual collection, storage, logs, retention, AI-provider transmission and
connector permissions. Provide explicit per-user/workspace/Bud access boundaries,
context-use indicators, disconnect/revoke, relevant exports and account/workspace
and transcript/file deletion with documented retention. Test that workspace context
cannot leak into another workspace or agent response.
Prepare Privacy Policy, Terms, Acceptable Use, AI/third-party disclosures,
subprocessors, cookie/analytics notices where applicable, subscription/renewal/
cancellation/refund terms and appropriate business processing agreements.
Have qualified counsel review against the real data flows and operating markets;
policies do not guarantee legal protection. Confirm company ownership, founder and
IP agreements, signing authority, registration, taxes/bookkeeping and provider account
eligibility. Gate: accurate published documents and business readiness.

## Phase 6 — Billing and trusted purchase journey

Verify server-authoritative subscription state and plan entitlements. Test checkout,
renewals, failed/delayed payments, cancellations, refunds, upgrades/downgrades,
expired subscriptions, duplicate/out-of-order webhooks and customers who pay before
installing. Match website onboarding, plans, checkout, confirmation and desktop UI.
Prepare account/workspace onboarding before payment, clear prices/renewal/cancellation
terms, purchase confirmation and correct download access. Update screenshots and
Buds messaging only for implemented features. Keep waitlist active until final go/no-go
approval; do not enable live Stripe billing during this planning task.
Gate: full lifecycle works without manual database edits and paid access cannot be
spoofed by client plan values.

## Phase 7 — Security, abuse/cost protection and operations

Audit all endpoints, sessions, RLS/membership, token encryption, secrets, dependencies,
unsafe parsing/tool execution, prompt injection through docs/transcripts and context
isolation. Test stolen/expired sessions and direct API bypass attempts. Bound user,
workspace and appropriate IP request rates, task concurrency, file parsing,
transcription, model tokens, retries, tool calls and total provider spending;
verify entitlement/cost limits server-side. Retain approval for consequential actions.
Simulate provider outages, failed databases, network loss, expired tokens, stalled
queues and webhook errors; test timeout, idempotency and recovery behavior.
Add production error/provider alerts, spending/usage alerts, database/queue/webhook
monitoring, backups and a tested restore. Remove debug paths, bypasses and test accounts.
Create credential leak, account compromise, cost spike and exposure response runbooks.
Obtain an independent review of highest-risk areas before release. Use OWASP API risks
as the audit baseline; do not describe testing as an absolute security guarantee.
Gate: no unresolved critical/high issues, verified isolation/caps/recovery and a
responsible incident contact.

## Phase 8 — Desktop distribution, support and release readiness

Produce Developer ID-signed/notarized/stapled DMG and signed Windows installer;
verify runtime compatibility, permissions and clean-machine installation on both.
Test updates, safe rollback/recovery, account recovery on a new computer and clean
uninstall. Publish premium download components, installation/troubleshooting docs,
release notes, visible support/contact, cancellation path and service status.
Maintain the Apple-quality experience across installation, messaging and connectors.
Gate: both installers independently tested, update/signing gates pass and support works.

## Phase 9 — Final go/no-go and launch

Require all advertised features to pass end-to-end; authorization/RLS/isolation and
server rate/spending limits pass; billing lifecycle and cancellation pass; privacy
matches real flows; clean-machine installers pass; support/incident path exists;
production build, screenshots, onboarding, pricing and download links agree.
Obtain explicit owner approval before changing the waitlist website to paid downloads.
Then deploy the approved artifacts and monitor production. After app completion and
deployment, deliver the previously requested entire-codebase walkthrough.

## Traceability to the owner's action list

1 connectors acceptance → 2. 2 meeting transcripts → 3. 3 chat dictation → 3.
4 upload limits → 3. 5 Stripe/every connector → 2. 6 @ agents/Buds → 4.
7 legal → 5. 8 UI polish → 4. 9 screenshots → 6. 10 Anthropic → 2.
11 OpenAI → 2. 12 Pulse removal → 1. 13 one-primary-action screens → 4.
14 complete technical/security/reliability testing → 1, 7, 9.
15 GitHub delivery → all approved phases. 16 pre-payment onboarding → 6.
17.1 DMG and 17.2 Windows → 8. 17.3 downloads → 8/9.
17.4 polished customer experience → 2/4/8. 17.5 waitlist-to-billing → 6/9.
18.A data permissions → 3/5/7; B billing lifecycle → 6; C monitoring/recovery → 7;
D independent security review → 7; E installation/update/recovery → 8;
F support/trust → 5/6/8. All six additional backlog items map to 1/5/7/8.
Founder/business readiness → 5. Final release decision → 9.

## Owner actions and approval gates

No new SQL is required for the immediate fixes. First connector setup action:
complete the open Stripe login's personal passkey/Touch ID/2FA step, then confirm
signed in. Do not share secrets here. Stripe app creation/credentials and public
review, Meta developer/Instagram registration/review, Vercel integration registration
and Brave's funded Search key remain setup gates; exact steps are in the website
repository docs/account-connector-setup.md. These prevent claiming all connectors
production-ready, but do not block saving this roadmap or the UI fixes.
Later required: reviewed legal/business arrangements, real billing/provider keys,
paid always-on hosting approval, signing/notarization and Windows signing setup,
staging/live test consent and final launch approval. Walk through one requirement
per response when its phase is approved. Obtain approval before starting Phase 1.
