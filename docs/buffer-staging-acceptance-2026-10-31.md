# Buffer Marketing Bud staging acceptance — October 31, 2026

Scope: the new primary social publishing path, staging only. No payment,
production publishing enablement, customer personal token or public delivery.

## Passed against real services

- Created the confidential Aedrova Staging OAuth App Client with owner approval;
  only account read and post read/write permissions. Credentials are private,
  encrypted/server-side at runtime and stored in Render staging only.
- Owner connected Instagram @aedrova_ai through Buffer's normal Free-plan flow.
- A fresh authenticated staging workspace/Bud completed Google identity binding,
  Buffer PKCE consent, callback, organization selection and actual channel read.
  The account reported one writable, unpaused Instagram channel.
- Saved its selected channel. Draft save retry returned the same draft ID.
- An unapproved dispatch was rejected. Approved, then edited the draft;
  approval became invalid and dispatch was rejected again.
- Actual Buffer refresh-token rotation succeeded through the durable single-use
  claim implementation, followed by authorized reads using renewed credentials.
- With explicit owner approval, scheduled the exact reviewed test caption and
  existing public Aedrova logo for November 30, 2026 at 16:11:54 Asia/Bangkok.
  The first provider attempt rejected missing Instagram metadata without a post
  ID. Added explicit post/reel format and feed policy, passed CI, deployed and
  repeated the approved operation successfully.
- A repeated dispatch returned the same provider post ID. Buffer showed exactly
  one queue entry; its read API reported `scheduled` with the exact UTC due time.
- Local disconnect removed the channel from Aedrova. A fresh draft using that
  disconnected grant was rejected. Removing the disposable Bud also purged its
  private social records, and the test workspace was archived.
- Owner-approved removal deleted only that scheduled test. Buffer queue returned
  to zero. It was never publicly delivered. No other social posts were changed.

## Fixes discovered by real acceptance

1. Instagram requires explicit post type and feed policy. The provider adapter
   derives image feed-post / video-reel metadata from reviewed content.
2. Current Buffer status includes `scheduled`; older examples use `buffer`.
   Preserve current scheduled/published/failed states and older equivalents.
3. The Social review must keep rejection details visible after refresh, and
   distinguish last-confirmed scheduled state from confirmed public delivery.

## Automated and hosted checks

Initial full backend/site suite: 691 passed. Full desktop run: 1,090 passed with
one obsolete role-tool expectation corrected; affected suite then 86 passed.
Required hosted desktop checks passed on Ubuntu, macOS and Windows, together
with PostgreSQL RLS. Backend CI passed image build/startup, private PostgreSQL
schema access, lint, secret scan and website checks.

Latest targeted regressions: 31 social backend cases and eight desktop social
review cases pass locally. New format/status commits undergo their own required
hosted checks before merge/deployment. Fixture tests are explicitly separate
from the real scheduling evidence above; no simulated result is called a live pass.

Coverage includes OAuth callback/resource replay, other-user rejection, encrypted
storage, channel reselection, exact approval, concurrent dispatch, uncertain
writes, malformed/oversized input and unsafe media URLs, consumed-refresh timeout,
refresh/disconnect races, feature-flag shutdown and authenticated endpoint inventory.

## Boundaries and outstanding rollout work

The tested external operation was Instagram scheduling, followed by cancellation.
No actual public delivery or every-platform/media-format certification is claimed.
Analytics are unavailable through Buffer OAuth apps. Private workspace attachments
are not exposed publicly; the first interface uses stable public image/video URLs.
Already queued provider posts survive local disconnect and need management in Buffer.

Production client/callback configuration and deliberate publishing enablement
remain a later rollout gate. Direct Meta/TikTok public approvals remain unverified
for preserved legacy read integrations; they no longer gate the new primary
Buffer path. Other social networks need their own authorized-channel acceptance
before being advertised as tested. Remaining account-deletion/retention operations,
security/recovery, Apple login/installers and commercial setup retain their own gates.

Private receipts/screenshots: work/buffer-social-oct31/. Never commit credentials,
OAuth state, unredacted tokens or private operator files from that directory.
