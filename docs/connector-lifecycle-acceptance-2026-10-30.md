# Connector lifecycle acceptance — October 30, 2026

Status: **connector lifecycle acceptance PASSED** for the cases below. The final
backend candidate f9219b880ca3fba5354d6fc1a508d51373ab925f is merged to main and live
in staging. Its revoked Supabase read now returns Needs authorization. Stage 1 stays
OPEN for public provider approvals and required release CI before source promotion.
This is staging acceptance, not production or public approval.

## What was exercised

Fresh OAuth grants used a disposable staging workspace and Bud, with the existing
operator test accounts, existing read-only scopes and a 24-hour Aedrova grant. No
model generation, payment, purchase, hosting upgrade or new secret was required.
Access expiry was induced only in the exact test grant's encrypted expiry metadata.
The subsequent refresh was a real request to the provider, followed by a real read.
This does not claim that a provider's wall-clock token lifetime elapsed. Successful
refresh retained the original local grant deadline and selected resource.

- **GitHub:** repository, changes, issues and deployment reads passed. Induced access
  expiry caused actual refresh and successful reads with a future token expiry.
  GitHub's single-token revocation endpoint returned 204 for a fresh test token;
  the subsequent Aedrova read was denied. Global app authorization, app installation,
  repositories and GitHub CLI credentials were not removed. Local disconnect and
  another attempted read also passed.
- **Figma:** read the existing Figma Basics tutorial file, refreshed and read again.
  The provider now uses its documented refresh endpoint with Basic authentication
  and preserves the original refresh token when no replacement is returned. Removing
  Aedrova Buds in Figma's own Connected apps settings left no connected apps there;
  the staging read was denied. Induced local grant expiry was also denied and the
  expired encrypted credential was purged. A later disconnect correctly reported that
  the already-purged connection was unavailable; that is not counted as a new successful
  disconnect request.
- **Stripe:** renewed the existing Aedrova test-mode installation with Accounts/Balance
  read permissions. Balance read, actual refresh and another balance read passed.
  Uninstalling Aedrova Buds in test mode left the installed-app list empty; subsequent
  Aedrova access was denied. Local disconnect and denial passed. No live installation,
  billing transaction, checkout, refund or subscription was changed by this test.
- **TikTok:** sandbox profile/public-video reads and actual refresh passed. The
  documented revoke endpoint returned 200; the next Aedrova read was denied, including
  the failed renewal attempt. Local disconnect and denial passed. No attempt-limit
  bypass, publishing scope or public approval was used.
- **Instagram:** renewed the existing aedrova_ai read-only authorization; profile/media
  reads and actual long-lived-token renewal passed, with future expiry and unchanged
  local grant deadline. Removing Aedrova Buds-IG in Instagram's Apps and websites left
  no active applications; subsequent Aedrova access was denied. Local disconnect and
  denial passed. No posting or messaging access was requested.
- **Supabase:** only the selected Aedrova Staging project's metadata was read through
  Aedrova, using the existing organization Projects Read permission. Actual refresh
  and a subsequent read passed. The provider's revoke endpoint returned 204. An
  independent direct request using that revoked access token returned 401; refreshing
  its revoked renewal token returned 404. Thus an outage was not counted as successful
  revocation. Local disconnect and denial passed. Production database credentials,
  schemas, project configuration and billing were not changed.
- **Vercel:** confirmed Installation, Projects and Deployments Read access to one
  project, then read project/deployment context. Its legacy installation token has no
  refresh token. Induced expiry correctly requested reconnection; restoring only the
  test expiry metadata did not bypass its Needs authorization state. Fresh OAuth
  through the existing installation restored successful reads. After the owner's
  explicit approval of Vercel's termination acknowledgment, removing Aedrova Buds
  displayed Integration Removed, and the next staging read was denied. Local
  disconnect and denial passed. No project, deployment, environment variable or
  subscription was removed or changed.
- **Notion:** retained the October 25 live evidence: selected-page read, actual refresh,
  future token expiry, external token revocation returning 200, subsequent denial and
  induced local grant expiry denial. This was not needlessly rerun.
- **Managed Search:** no customer OAuth grant exists at the search provider. All local
  grant expiry/disconnect boundaries are covered by the catalog-wide controlled tests;
  actual Research conversation, saved history and disconnected-grant cleanup passed
  separately on October 30. Revoking the company's shared OpenAI credential would
  affect the platform and was not used as a Bud revocation test.

## Fixes found by live acceptance

1. Figma refresh previously used its code-exchange endpoint. Corrected to
   `https://api.figma.com/v1/oauth/refresh`, with only refresh_token in the form body.
   Real staging refresh/read passed after deployment.
2. GitHub/TikTok can return OAuth error bodies with HTTP 200. Explicit errors now ask
   for reauthorization before token parsing, without exposing provider response details.
3. Supabase returns 404 for the revoked refresh token observed here. That provider's
   refresh-only 404 now asks for reauthorization instead of labeling it an outage.
   The final live candidate returned Needs authorization for this revoked grant,
   then passed local disconnect and another denied read. Other providers' 404 and Supabase's authorization-code 404 handling are unchanged.

**115 targeted controlled checks passed**, covering every catalog grant, identity and
resource binding, encrypted credentials, local expiry, reconnect/version invalidation,
disconnect during reads, rotating-token concurrency, refusal to resurrect disconnected
grants, provider errors and the three fixes. Ruff and diff checks passed. Controlled
responses are not presented as live provider evidence. Transient transport failures
and expired acceptance-session handoffs were retried and recorded, not counted as
provider acceptance passes. Figma and Stripe fixture-order errors in the raw harness
report were resolved before successful selected reads; they were harness errors.

## Evidence and cleanup

Private local evidence: `work/connector-lifecycle-oct30/live.json`, `live-second.json`,
`metadata.jsonl` and screenshots. Provider content and tokens were not printed or
committed. Final database inspection confirmed zero remaining grants in both exact
disposable workspaces, both workspaces archived, seven exact test handoff records
removed and test sessions signed out. The earlier expired harness session had left
one GitHub credential: its exact test token was revoked with HTTP 204 and the local
row removed before zero-grant verification. See cleanup-confirmed.json and
old-fixture-cleanup.json. Staging readiness and the public homepage returned HTTP 200. Notion's retained evidence is documented in
[October 25 acceptance](staging-acceptance-final-2026-10-25.md).

Provider-side revocation deliberately removed the tested app authorizations. Existing
Buds using those authorizations may therefore need **Connect your account** again.
This is an expected consequence of testing revocation, not a need to generate keys.
No owner action is required to repeat these completed lifecycle checks.

## Remaining Stage 1 steps

- Meta/Instagram: actual operator business/access verification and App Review.
- TikTok: genuine end-to-end demo, Production submission and public approval.

These external approvals are not implied by successful sandbox tests. Do not start
Stage 2 UI fixes without approval. Funded Claude builds and reliable two-device
meetings remain deferred final owner-paid launch gates; no payments were made.

Primary provider references: [Figma OAuth](https://developers.figma.com/docs/rest-api/oauth-apps/),
[GitHub token revocation](https://docs.github.com/en/rest/apps/oauth-applications),
[TikTok token management](https://developers.tiktok.com/docs/en/oauth-user-access-token-management),
[Supabase revocation](https://supabase.com/docs/reference/api/v1-revoke-token),
[Stripe OAuth](https://docs.stripe.com/stripe-apps/api-authentication/oauth),
[Vercel integration permissions](https://vercel.com/docs/integrations/install-an-integration/manage-integrations-reference).
