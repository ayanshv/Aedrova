# Repair roadmap Step 6 — connector certification

October 15, 2026. **In progress; not certified for launch.** Owner approved this
batch and requested personal interventions only at the final handoff. No new key,
paid plan, production change or provider permission expansion was performed.

## Current live environment

Fresh native Google PKCE sign-in and authenticated staging catalog/grant queries
passed against aedrova-beta-staging.onrender.com. Public health returned HTTP 200,
managed AI enabled and checkout disabled. The earlier cold-host query was
incomplete, not a provider authorization failure. The separate existing connector
host also returned health HTTP 200. Tokens were not sent between environments.

Render Deploys still shows e375bdc / dep-db8o043l550s73ej2i90 Live. Source fixes
below are not yet deployed. Readiness evidence is in ignored
work/connector-step-6/readiness.json; no provider secrets or account content are
in that report. The named synthetic staging workspace currently has no active
connector grants. Historical connections do not certify fresh lifecycle behavior.

## All nine connectors

- **GitHub:** adapter and lifecycle tests pass; existing local client ID/secret
  present. Staging reports OAuth unavailable. Add its staging callback and deploy
  the existing credentials privately after the exact transfer approval. Fresh
  installation/resource discovery, real reads, renewal and revocation remain open.
- **Supabase:** same staging configuration blocker; existing local pair present.
  Keep projects:read only; no SQL, database rows or project keys. Historical health
  reads on the separate connector service do not certify this staging environment.
- **Figma:** same staging configuration blocker; local pair present. Keep
  file_content:read. A file link remains required after provider consent because
  current discovery cannot enumerate arbitrary accessible files. Do not invent IDs
  or silently grant all files. Fresh file read/renewal/revoke checks remain open.
- **Notion:** same staging configuration blocker; local pair present. Keep Read
  content only and the existing dedicated validation page. Do not select a personal
  parent page or broaden installation access. Fresh named-page discovery, read,
  refresh, disconnect/reconnect and provider revocation remain open.
- **Instagram:** staging OAuth available; prior October 14 @aedrova_ai tester grant
  and profile/media reads passed. A fresh OAuth start passed today, but its provider
  page was not opened after the shared web sign-in handoff stalled. No fresh grant,
  renewal/revocation or public App Review acceptance is claimed. Preserve the
  professional tester and instagram_business_basic scope only.
- **TikTok:** staging OAuth available; one fresh start passed. The web handoff
  stalled at Google's loading account chooser before reaching TikTok. No repeated
  TikTok authorization, new tester or quota bypass was attempted. The historical
  @aedrova sandbox/account-attempt restriction remains unresolved by this check.
  Fresh callback/profile/video/renewal/revocation still need acceptance.
- **Stripe:** staging unavailable; connector client pair absent locally. Developer
  external-test readiness/install link was previously blocked. Owner explicitly
  deferred business/bank setup until packaging/release; no request to complete it
  now, no fabricated credentials, and no transaction. A verified customer account
  alone does not establish the developer app's readiness.
- **Vercel:** staging unavailable; client pair absent locally. Prior integration
  registration was prepared but not submitted. Owner/legal identity, provider
  agreement and actual integration/slug remain gates. No new terms accepted.
- **Managed Search:** staging unavailable and Brave key absent locally. The normal
  customer flow is Enable web search, not an OAuth login. Provider subscription/key
  and funded usage need owner setup before real acceptance. No subscription or
  charge was started; existing global/workspace daily caps remain intact.

## Source fixes and regression evidence

Backend token-exchange errors now preserve intentional authorization denials:
Denied inherits ValueError and was being caught and relabeled as a generic outage
in the account-exchange helper. HTTP 429 now reports provider rate limiting;
server failures report temporary unavailability rather than suggesting a lost
grant. Provider response/error payloads remain withheld. These changes do not add
automatic exchange retries, which could consume one-use codes or rotating tokens.

TikTok accepts equivalent comma/space-delimited read-only scopes while still
rejecting broader or missing scopes. Server setup hints no longer suggest hidden
manual token controls removed from the customer UI in Step 5.

Added catalog-wide grant tests for all nine adapters: encrypted storage, owner
reads, foreign-account denial, version change, reconnect replacing old grants,
disconnect and expiry. Provider responses are synthetic in these tests. Existing
OAuth tests cover fixed hosts, CSRF/browser proof, PKCE where supported, encrypted
state, scope checks, discovery, actual adapter read requirements and token renewal
boundaries. They are not evidence of real provider grants or publication.

Full website/backend suite: **528 passed** after the final setup-copy cleanup.
Ruff/diff checks pass. Desktop source
unchanged in this batch; Step 5's 857/77 desktop results remain its evidence.

Temporary native test sessions were signed out and private login/authorization
URL files removed. Pending server authorization state expires under its existing
ten-minute policy. No new connector grant was completed during this pass.

## Verified provider references

Reviewed official documentation, rather than inferring capabilities from UI:
[GitHub token refresh](https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/refreshing-user-access-tokens),
[Supabase integration](https://supabase.com/docs/guides/integrations/build-a-supabase-oauth-integration),
[Figma authentication](https://developers.figma.com/docs/rest-api/authentication/),
[Notion authorization](https://developers.notion.com/guides/get-started/authorization),
[TikTok tokens and revocation](https://developers.tiktok.com/docs/en/oauth-user-access-token-management),
[Stripe Apps OAuth](https://docs.stripe.com/stripe-apps/api-authentication/oauth),
[Vercel integration creation](https://vercel.com/docs/integrations/create-integration),
[Brave Search](https://api-dashboard.search.brave.com/app/documentation/web-search/get-started).
Meta's business-login documentation required sign-in; do not claim a fresh public
documentation read for its gated page. Existing official Meta app/tester UI and
previous live evidence remain documented in the website's social-connectors.md.

## Consolidated owner handoff — required next

Approve **adding the exact staging callbacks and privately copying the existing
GitHub, Supabase, Figma and Notion client IDs/secrets from ignored website .env.dots
to Render → aedrova-beta-staging → Environment**, then deploying the tested staging
backend revision. No new keys, scope expansion, production changes or purchases.
This is a different credential destination from the prior separate connector host;
browser safety requires this specific approval before transfer/registration.

The agent will perform the approved work; do not paste secrets here. The prepared
non-secret checklist is website deploy/staging-connector-certification.env.example.
Do not import its blank values as a complete environment or replace database,
encryption, AI, speech or social settings. Keep existing callbacks and grants.
This approval blocks live certification of those four providers.

After configuration, fresh provider login/consent may need the owner personally.
Exact, newly generated pages will be supplied when ready; do not reuse expired
links or repeat the historical setup. Social consent/reconnect, Vercel registration
agreement and Search subscription are separate handoffs when actually prepared.
Stripe business/bank work stays deferred as instructed. Step 6 stays open; do not
start Step 7 or label all connectors complete.
