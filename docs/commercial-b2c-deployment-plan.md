# Aedrova commercial B2C launch plan

Updated October 19, 2026. Planning document; no incorporation, purchase, bank change,
commercial checkout or release activation is authorized by this document. The owner
must make payments personally. Current distribution is an internal staging preview;
public website remains a waitlist. Local source tests do not close live release gates.

## 1. Set the legal and commercial baseline — owner, counsel, tax adviser

- Confirm actual owner(s), authorized signatories, founder capacity/age and whether
  the intended operator will be a C corporation. Do not invent a company name or
  present a pending incorporation as complete. A C corp is a business decision, not
  a universal prerequisite for selling software; this plan includes the requested path.
- Select formation jurisdiction with advisers; if Delaware is chosen, arrange an
  authorized registered agent and file the certificate of incorporation. Separately
  evaluate registration/foreign qualification where the business actually operates,
  applicable local licenses, annual reports, franchise and income tax obligations.
- Complete organizational actions: bylaws, board/officers, founder stock/cap table,
  IP assignment for code/design/domain/Buds and any contributor/contractor agreements.
  Get advice on vesting/equity elections and time-sensitive filings before issuance.
- Obtain EIN after entity formation using IRS process; confirm responsible party and
  tax classification. Do not file an S election merely because it is familiar: the
  intended path here is C corp, subject to professional advice.
- Open business banking and bookkeeping under the real operator, establish authority,
  separate personal/business funds and calendar ongoing filings. Owner handles all
  banking, identity submission, contractual acceptance and payments personally.
- Determine initial supported countries/regions and age eligibility. Consumer terms,
  auto-renewal/cancellation, digital-content remedies, taxes and privacy vary by market.
  B2C does not itself change Aedrova's existing $10/month Pro or $200/year Team price
  per workspace; any new tiers or unit changes require separate owner approval.

Exit: formation/ownership evidence, EIN, bank eligibility, authorized contact/address,
market scope and business authority confirmed. Operator placeholders replaced only
with verified facts across Privacy, Terms, Support, Stripe and receipts.

## 2. Finalize consumer trust and support — owner plus implementation

- Review the 20-item checklist in ../Aedrova_site/docs/consumer-launch-checklist-2026-10-19.md.
- Counsel reviews Privacy, Terms, Refunds, Cookies, Acceptable Use, notices and consent
  against actual data flows and supported markets. Policies cannot waive mandatory
  consumer rights or substitute for real technical controls.
- Verify simple cancellation/refund contact and backend behavior; identify actual
  seller and authorized support/postal address. No unauthorized library or borrowed
  establishment address. Maintain contact@aedrova.com and (408) 634-5254 if still valid.
- Finalize retention/deletion/export procedure, provider contracts/DPAs as applicable,
  cross-border handling and child/minor policy. Do not launch child-directed collection
  or regulated-data promises without the appropriate process.
- Establish support intake, incident/status communication, escalation and real response
  ownership. Configure email-domain authentication and unsubscribe/suppression before
  launch communications; no launch email sender is currently configured.
- Verify licenses and ownership for all fonts/media/Buds/screenshots and shipped software
  notices. Finish keyboard, screen-reader, contrast, reduced-motion and mobile review.

Exit: truthful public disclosures, working rights/support process, verified asset rights,
market-specific review complete. Legal-ready flag is evidence-driven, not a shortcut.

## 3. Close product and security gates in staging — engineering and owner acceptance

- Complete new-user create/join/login/logout/account recovery flow; required workspace
  AI configuration, Bud setup/resume and one clear primary action on each screen.
- Run real main-agent and Bud replies, builder edits/tests/review/apply/publish approval,
  private Bud DMs and coworker DMs with second-account permission/isolation acceptance.
- Certify every advertised connector: user login, consent, callback, resource selection,
  verified read/tool use, expiry/refresh, disconnect/revoke, wrong account and denial.
  TikTok/Instagram development tester success is not public production approval.
  Hide or label services unavailable for ordinary customers until provider review passes.
- Validate audio/video, device selection, screen share and chat, recording/privacy,
  transcription review/consent/context and failure recovery. Scope advanced Zoom-like
  backlog honestly; unimplemented features cannot be advertised as launch capabilities.
- Verify private uploads, type/size/content limits, previews, voice recording/playback,
  cancellation and storage cleanup. Test malicious documents/prompt injection boundaries.
- Repeat endpoint auth/RLS/tenant tests, SQL binding, CSRF/PKCE/state, duplicate headers,
  token encryption/redaction and secrets/dependency scans. Independently review critical
  authorization/tool-execution paths. Fresh credential rotation if any actual exposure
  remains unresolved; don't assume pattern scanning erases earlier exposure.
- Accept trusted reverse-proxy settings and rate limits with the real ingress and multiple
  workers. Verify per-plan/concurrency/retry/upload/speech/model spending limits server-side,
  failure-closed behavior and provider usage reconciliation. No client-side plan authority.
- Keep feature flags and sandbox credentials separated. Save evidence by commit/build;
  fix, retest and rerun relevant regressions before promoting to production.

Exit: all advertised workflows pass on staged candidate, no unresolved critical/high-risk
findings, independent review and documented residual-risk decisions signed off.

## 4. Make production operable — engineering; owner purchases only if required

- Select an always-available hosting arrangement appropriate for paid service; sleeping
  free hosting is unsuitable for dependable real-time work. Owner reviews and pays for
  any hosting/provider upgrade. No automatic purchase or implicit meeting activation.
- Verify production migrations/least-privilege grants against staging first, backups,
  tested restore, secret storage, TLS/domain, log redaction and bounded maintenance jobs.
- Configure and test alerts for API/provider errors, cost thresholds, webhook failures,
  database health/storage, queue backlog and meeting service/guard health.
- Exercise provider outage, worker restart, cancellation, retry/backoff and rollback.
  Keep a versioned runbook for leaked credentials, abuse, data exposure and emergency
  AI/billing disable. Test a restoration rather than merely claiming backups exist.
- Keep robots/sitemap stable independent of sleeping origin. Search Console ownership
  and homepage indexing are verified; sitemap succeeds. Product indexing remains Google's
  decision after robots cache refresh. No ranking/LLM-recommendation guarantee.

Exit: readiness, monitoring, recovery and production capacity evidenced, owner approves cost.

## 5. Complete Stripe commercial configuration — owner identity/bank steps; assisted setup

- Finish Stripe verification for the ACTUAL legal operator: legal name/entity type,
  EIN/tax details, authorized representative/owners as requested, business activity,
  website, legitimate addresses and payout bank. Stripe may request additional identity
  documents. Submit sensitive information privately in Stripe, not chat or Git.
- Review public descriptor, business/support name, contact@aedrova.com, phone, support,
  Privacy, Terms and Refund URLs. Confirm live-account restrictions cleared and payout
  capability; don't confuse Stripe sandbox or Finance Bud connector with live billing.
- Preserve authorized price mapping: Free $0; Pro $10/month per workspace; Team $200/year
  per workspace; Enterprise Let's Talk, no invented fixed-price checkout. Confirm exact
  live Stripe product/price IDs, currency, interval and descriptions. Additional members
  are $0; no seat-quantity multiplication or automatically billed AI overages.
- Configure customer portal cancellation, payment-method management, receipts/invoices,
  renewal disclosures, failed-payment recovery and refund/support process. Owner/adviser
  determines sales-tax/VAT obligations, registration and tax settings; a tax feature is
  not proof of tax registration/compliance.
- Register production signed webhook endpoint and secret privately. Verify event signature,
  replay/idempotency/order handling and canonical subscription/customer-to-workspace mapping.
  Only owners/authorized billing administrators can modify billing. Other members inherit
  workspace entitlements; one member's return page must not create paid access.
- Test sandbox monthly/annual checkout, abandonment, 3DS/action required, failed payments,
  duplicated/delayed/out-of-order webhooks, renewals, cancellation, expiration, upgrade/
  downgrade, refunds/disputes, portal authorization, invitation and shared entitlements.
- Perform owner-controlled real-payment/payout acceptance only after explicit approval;
  agent cannot pay on owner's behalf. Reconcile Stripe events to backend state and provider
  costs. Do not open commercial checkout just to test missing business configuration.

Exit: verified seller/bank, exact live prices/portal/webhooks and lifecycle acceptance; owner
explicitly approves billing activation after all other launch gates.

## 6. Produce release candidates — Mac and Windows

- Confirm Apple membership actually active, correct developer team and Developer ID
  credentials. Owner completes identity/agreement/keychain/notarization credential steps
  privately. Configure and validate Sign in with Apple only with the required registered
  identifiers/redirects, key handling and account-linking behavior; no duplicate accounts.
- Build from pinned reviewed source with production origins and explicit version. Current
  local preview remains internal staging; do not relabel it as a production installer.
- Mac: appropriate architecture(s), hardened signing/entitlements, notarization, stapling,
  Gatekeeper checks on app and DMG, license notices and signed update/rollback strategy.
- Windows: build/test on Windows runner, sign installer/update artifacts using authorized
  publisher identity, verify runtime dependencies, Defender/SmartScreen behavior, clean
  install/upgrade/uninstall and permissions. Do not promise immediate SmartScreen reputation.
- Clean-machine tests: download/hash, install, first login, permissions, reconnect, build,
  Bud/connector use, meeting/media, billing state, update, logout/uninstall and recovery.
  Capture real release screenshots and exact supported OS/hardware requirements.
- Publish immutable versioned artifacts/checksums and accessible download UI only after
  acceptance. Both OS links must resolve to the tested signed artifacts, not placeholders.

Exit: signed/notarized Mac candidate and signed Windows candidate pass clean-machine tests,
recovery/update instructions ready, website/download manifest matches versions.

## 7. Final promotion and controlled commercial go-live

- Freeze one release commit, evidence bundle, website copy/screenshots and rollback target.
- Confirm company/policies/support, infrastructure/security, provider approvals, costs,
  Stripe lifecycle and both installers pass. Every claimed feature must work end to end.
- Apply verified production migrations/configuration with backup and rollback ready;
  rerun public/private smoke checks on actual production origins and account roles.
- Owner gives explicit final go/no-go approval. Only then enable checkout/release/legal
  gates and change waitlist calls to action to the validated download/purchase journey.
- Stage a small real-customer rollout; watch errors, support, spend and billing entitlement
  reconciliation. Expand only when measured acceptance holds; rollback/disable costly or
  failing functions promptly. No promise of “bulletproof” behavior or guaranteed revenue.

## First owner actions (consolidated)

1. Confirm proposed legal operator, formation jurisdiction, ownership/signatory and target
   consumer countries/age policy with advisers; start the C-corp path if still chosen.
2. Complete formation/EIN/business banking and legitimate support/postal details personally;
   keep sensitive information private. Send verified public business details when final.
3. Finish Stripe identity/business/bank setup when entity details are settled; no payment
   by the assistant. Approve costs for reliable hosting/providers if required.
4. Confirm Apple membership/team and complete private signing/notarization access; arrange
   Windows signing and clean Windows test machine/runner.
5. Complete human live-account consent/listening/device checks that automation cannot
   establish and schedule independent security/legal/accessibility review.

Primary references checked October 19, 2026:
- Delaware formation: https://corplaw.delaware.gov/forming-delaware-corporation/
- Registered agent: https://corp.delaware.gov/faqs-regarding-registered-agents/
- EIN: https://www.irs.gov/businesses/small-businesses-self-employed/get-an-employer-identification-number
- Stripe activation: https://docs.stripe.com/get-started/account/set-up
- Stripe subscription webhooks: https://docs.stripe.com/billing/subscriptions/webhooks
- Consumer subscription guidance: https://www.ftc.gov/news-events/news/press-releases/2021/10/ftc-ramp-enforcement-against-illegal-dark-patterns-trick-or-trap-consumers-subscriptions
- Apple notarization: https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution
