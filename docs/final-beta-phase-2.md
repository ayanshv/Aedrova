# Final-Beta Phase 2 — connectors and AI providers

Status: authorized, in progress. Owner confirmed both Phase 1 manual gates and
approved Phase 2 on October 10, 2026. No Phase 3, production merge/deployment,
public checkout, downloads or M14 activation is authorized by this phase.

## Initial implementation and verification

- Bud Finish later/Close now cancels setup rather than accepting an incomplete
  required flow; parent onboarding remains resumable. 55 Bud/onboarding tests pass.
- 72 native connector, transport, loading and Bud tests pass (offscreen source).
- Website/backend suite: 426 tests pass, including connector lifecycle and gateway
  authorization, provider/model binding, bounded inputs, cached usage, uncertain
  reservations, concurrent refresh, disconnect during reads and cross-account grants.
- Existing private OpenAI key passed a fresh GET model metadata lookup for
  gpt-5.3-codex. No paid inference or entitlement grant was performed. Historical
  October 7 build acceptance does not substitute for fresh staging gateway acceptance.
- Added hidden-prompt Anthropic setup, exact configured model metadata verification,
  bounded responses, generic secret-safe failures and atomic 0600 private storage.
  Added Claude-only model configuration and explicit local --with-anthropic option;
  combined local opt-in selects the existing dual-provider configuration. Rates and
  model selection are unchanged from the frozen baseline, not newly certified.
  API account/model access, current rates, bounded real inference and live CLI
  acceptance still require validation before release. No shared fallback provider.
- All credential files remain Git/Docker excluded. No credentials are recorded here.

## Current acceptance matrix

All nine offered connectors have source adapters and local regression checks. This
is not proof of provider registration, public review or fresh-customer acceptance.

| Connector | Local setup evidence | Live acceptance still required |
| --- | --- | --- |
| GitHub | Client pair present; prior owner connection | New test account, named installed repo, read denial outside install, refresh, revoked access, reconnect |
| Supabase | Client pair present | Named project selection, project-only metadata, expiration, revoke, reconnect; no customer SQL/data/keys |
| Figma | Client pair present | Real consent, selected file link/read permissions, refresh, revoked access, reconnect |
| Notion | Client pair present | Shared-page discovery, denial outside share, refresh, revoked access, reconnect |
| TikTok | Client pair present; prior account setup | Scopes/eligibility/review, account profile/video reads, rotation, revoked access, reconnect |
| Stripe Bud | Pair absent locally; previous app approved for testing only | Aedrova developer verification, issued install URL/credentials, external test account, balance reads, refresh, uninstall/reconnect |
| Instagram | Pair absent locally | Meta registration, professional test account, basic-only scope, long-lived refresh, revocation, provider review/live mode |
| Vercel | Pair absent locally | Integration registration, authorized team/project discovery, scoped deployment reads, uninstall/reconnect |
| Managed Search | Key absent locally | Owner funding/billing cap, service/workspace limits, key rotation, membership/reconnect; no customer OAuth fiction |
| OpenAI | Fresh model metadata lookup passed | Staging run-token authorization, hard budget, bounded real request and reconciliation, interrupted/revoked runs |
| Anthropic | Private 0600 key and claude-sonnet-5-5 model lookup verified | Bounded real request/cache accounting, staging gateway and runtime acceptance |

Local credential presence was checked without printing any value. Hosted service
configuration was not overwritten or inferred from those local files.

## Repeatable live protocol

For each login connector, use a dedicated test account/resource containing only
synthetic data. Capture source/build, environment, account (public identifier only),
scopes and timestamp. Sign in from the selected Bud, approve read-only access, choose
an authorized resource, verify its actual API snapshot and visible confirmation.
Test cancel/wrong account, denied resource, expiry/rotation, provider 429/network
failure, membership loss, disconnect, provider-side revoke/uninstall, and reconnect.
Confirm no access/refresh token or key reaches desktop, chat, evidence or logs.
Do not revoke a founder's existing grant that is used by other Buds/accounts.

Disconnect currently removes Aedrova's scoped stored grant and prevents further use;
it honestly returns provider_revoked=false. Provider-wide uninstall/revocation is a
separate action and may affect other resources/Buds. Do not label local disconnect
as successful provider-wide revocation. Each provider's revoke acceptance must be
recorded separately. Normal login does not expose codes/keys; Figma needs a file
link because the implemented read scope has no account-wide file enumeration.

## Owner setup sequence

Anthropic private setup is complete and independently verified. Next owner step:
in the open Stripe Business details form, complete the actual business industry,
website and product description, then Save. No identity/financial information is
entered by the agent. Remaining representative/service-agreement verification
stays owner-only; Stripe external testing remains blocked until verification.

Subsequent requirements remain in the website docs/account-connector-setup.md:
Stripe business verification/external testing, Meta/Instagram registration/review,
Vercel integration registration and managed Search funding. Walk through one owner
requirement at a time. Do not paste secrets into chat. Do not mark Phase 2 complete
until every offered connector/provider passes its actual acceptance gates.

## Anthropic saved — verified follow-up

Owner reported saved. Independent metadata lookup verified claude-sonnet-5-5, with
a regular private file at0600; no inference. Initial Phase2 CI is green: native
7ef060e/run38114515076 and website e21a16c/run38114515669.

Rechecked official standard model prices. Sonnet5.5 cached input is now $0.10 per
million; corrected both configuration files from the older $0.20 value. Base input
$2, output$10 and cache writes$2.50/$4 unchanged. Added tests for actual configured
cache accounting and rejecting unpriced premium speed/region requests before any
reservation/upstream call. Latest service suite:430 passed; Ruff/secret checks pass.
Sources: https://platform.claude.com/docs/en/about-claude/pricing and
https://developers.openai.com/api/docs/models/gpt-5.3-codex .
The OpenAI model page marks the current configured model deprecated; metadata access
still passed. Provider lifecycle/migration review remains a release gate; no silent
model switch or new model/pricing promises.

Stripe current signed-in app page still explicitly blocks external testing with
"Verify your business to get started with external testing." Navigated to Settings
→ Business → Business details → Edit business details; owner form open, no submitted
fields or account activation. First owner action is the industry, website and
product description form. Further verification remains required. No new paid
requests, secret upload, deployment, production merge or Phase3 activation.

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

## October 11 — renewed non-Stripe checks and Vercel draft

Owner approved continuing Phase 2 and conditionally starting Phase 3 after checks.
733 desktop and 439 development backend tests passed. Both installed coding CLIs
passed the loopback managed protocol/tool-result exercise (no paid inference).
Private 0600 OpenAI and Anthropic files passed fresh model metadata checks for the
existing configured models; no model/rate change or shared key exposure occurred.
Application/backend scoped lint and tracked-secret checks passed; unrelated archived
motion-design helper scripts have existing broad-repository lint findings and were
not changed. Hosted gateway inference/accounting acceptance remains outstanding.

The signed-in ayansh Hobby Vercel account had no registered integrations. Prepared
the Aedrova Buds form, public logo/support/legal URLs, private visibility, mandatory
Integration Configuration Read plus Projects Read and Deployments Read, all other
optional scopes None. Redirect is the isolated staging callback:
https://aedrova-beta-staging.onrender.com/buds/oauth/vercel/callback .
No agreement accepted, Create submitted, credential issued or grant installed.
Browser tab19 is kept as the draft handoff. To submit, the owner must approve the
specific Vercel Integrations Marketplace Agreement and private integration creation
at action time; browser safety rules require that approval even with broad earlier
connector setup permission. Instagram registration, managed Search funding and live
consent/refresh/revoke/isolation acceptance also remain outstanding. Phase 2 is open.

The owner then specifically requested the post-meeting transcript review screen.
Its independent implementation is recorded in docs/final-beta-phase-3.md; this
explicit feature request does not certify Phase 2 or other Phase 3 features.
