# Pre-Apple launch gate checkpoint — October 13, 2026

Owner explicitly authorized resuming launch-gate work before Apple enrollment.
No live charges, membership purchase, public access activation, legal identity
inference, production data deletion or provider-wide revocation is authorized here.
Apple OAuth remains queued for active membership, alongside Google with an Apple icon.

## Completed autonomous verification

- Desktop: 782 tests passed; full source/test/script Ruff and tracked-secret scan pass.
- Backend: 487 tests passed, including nine new signed-event billing lifecycle tests,
  seven operations-probe checks and one disposable recovery drill. Full Ruff and
  tracked-secret scan pass after fixing the existing voice-format line-length failure.
- PostgreSQL app migrations/RLS: complete embedded-engine run passes. The voice SQL
  migration was missing from the runner; added it and a dedicated test for verified
  WAV publication, idempotency, wrong uploader/type and private Storage/message denial.
- Private PostgreSQL backend schema/role and atomic lease SQL checks pass. This is
  embedded PostgreSQL, not real multi-worker networked deployment acceptance.
- Billing fixtures exercise failed/unpaid/incomplete/paused/canceled subscriptions,
  end-of-period cancellation, stale paid events, both plan changes, preserved spending,
  renewed period reset exactly once, full refunds and canonical-state races. Other
  existing tests cover owner/member authorization, shared pools, topups and signatures.
  No real Stripe checkout, bank setup, refund or charged inference was performed.
- Read-only operations command and incident/restore runbook prepared. Recovery drill
  preserves spent/reserved balances, request/event replay and encrypted sessions;
  wrong-key access fails closed. Hosted backup/restore is not certified by SQLite.

Implementation/runbook: website repository docs/prelaunch-operations.md and
scripts/check_operations.py. Source pushed to the existing development branches;
public marketing, waitlist, downloads, permissions and payment gates remain intact.
No new SQL is needed on staging for this update: voice migration was already installed
by owner; the new SQL file is a disposable test, NEVER run it in hosted SQL Editor.

## Gates that cannot be marked complete yet

- Connectors: provider registrations/reviews, external Stripe test eligibility, managed
  Search funding and actual consent/refresh/revoke/reconnect on representative accounts.
  Missing registrations cannot be replaced by a fake successful connection.
- Live providers: bounded paid inference, accounting and sandbox acceptance; configured
  OpenAI model lifecycle needs review before release. No silent model/rate change.
- Media/onboarding: distinct second staging account isolation, expired sessions, final
  voice playback/listening and new-user required-Bud/Finish later/tour journey. Existing
  native source had an unsaved Bud draft; do not silently discard it to restart.
- Meetings: approved always-on API/guard hosting and actual two-device consent,
  transcription, final-leave/edit/Confirm/withdrawal acceptance. Free sleeping hosting
  remains a reliability blocker; October 12 hosting purchase deferral is respected.
- Operations/security: deployed alert delivery, database/Storage restore to an isolated
  target, deletion/retention recovery, real PostgreSQL multi-worker accounting and
  independent highest-risk review. A monitoring script is not an installed alert service.
- Business: operator placeholder as requested, registration/ownership/qualified legal
  review, privacy/support mailbox acceptance. Do not repeat legal-name question now.
- Billing: owner Stripe verification/bank details, actual test/live lifecycle, approved
  production configuration and no-seat-charge fresh-customer acceptance.
- Distribution: Developer ID, notarization, Sign in with Apple, Windows installer/signing
  and clean-machine/update/uninstall acceptance. Earlier Windows CI is not a signed build.

## Grouped owner handoffs, saved for the end

Immediate live-test handoff: save the current Bud draft (or deliberately Finish later),
close Aedrova Staging and reply “ready for live checks.” We can then open a fresh
staging OAuth flow. In its Google chooser select the SECOND staging test account and
complete sign-in privately; do not reuse an expired callback or send credentials.
This blocks real cross-account/media/onboarding acceptance, not the automated checks.

When Apple enrollment is confirmed, reply “Apple membership active.” Then configure
Developer ID Application via Apple Developer Certificates/Keychain and Apple OAuth
with scoped identifiers/callbacks and private key custody. No Apple setup is complete yet.

Deferred purchases/account steps: Render always-on API and meeting guard (previously
quoted $7/month each; recheck current terms before purchase), Stripe account/bank
verification, provider registrations/reviews and Windows signing. Walk through one
owner requirement per response at that checkpoint; never ask for keys in chat or
perform a purchase based only on this general launch-gate authorization.

Public go/no-go remains separate. Do not call all launch gates closed, promise a
launch date, publish preview installers or remove waitlist mode based on these results.
