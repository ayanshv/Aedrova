# Buds — implementation and activation

Buds replace the prototype mini-teammate interface. A Bud is a workspace source of
capabilities, not an autonomous agent. The central named Aedrova agent selects up to
three read-only tools, fetches only those sources and combines normalized evidence
with permitted conversations, decisions, meeting evidence and local development context.

## What is implemented

- Native compact shelf, original Aedrova chibi vectors, profile/picker, customization,
  source mentions, permissions, connection status and last update. Light/dark/system
  themes and reduced motion use the existing desktop system.
- Read-only cross-source answers without requiring a project folder. Build requests
  retain the existing independent checkout, queue, review and publication approvals.
- Server provider contract/registry. GitHub App OAuth with S256 PKCE, ten-minute
  encrypted single-use state, browser proof and same-Aedrova-account binding.
- Encrypted server grants scoped to individual user + workspace + Dot version. No
  integration token enters the desktop, browser, model prompt or shared public table.
- GitHub repository metadata, ten recent commits, ten open issues/PRs and ten
  deployment records. Deployment records do not assert success or production health.
- Structured citations and untrusted-source treatment. Both server and client recheck
  access; disconnects during retrieval/reasoning withhold stale results.
- Own-access disconnect/revoke; owner/admin workspace removal purges all stored grants.
  Failed provider revocation is reported, with GitHub settings as the fallback.
- Optional signed, size-limited, delivery-deduplicated GitHub events invalidate the
  last-read marker. Events do not automatically run models or expose raw payloads.
- Metadata/status is lightweight; provider data is retrieved on demand, never during
  ordinary chat. Raw API payloads are not persisted. Audit stores action/tool IDs,
  user/workspace/Bud IDs and time, with 90-day cleanup. Expired grants are purged.

Stripe, Supabase, Vercel and PostHog are registered **Coming next**, with no executable
production tools. Figma/Notion identities survive migration but their server adapters
also need implementation. Do not advertise these as working integrations. Local
results remain private to the initiating user, matching the existing agent feed.
Shared result publishing remains a separate permission-gated milestone.

## Owner actions required before live use

1. In Supabase → SQL Editor, run the complete contents of
   `supabase/migrations/202610070001_workspace_dots.sql` once. This adds shared Dot
   identities/RLS and migrates existing GitHub/Figma/Notion resource identities.
   The prior AI-teammates migration must already be applied. Legacy records remain
   for recovery. Local Keychain tokens are intentionally not copied or uploaded.
2. Create a **GitHub App** (not an OAuth App) at GitHub → Settings → Developer
   settings → GitHub Apps → New GitHub App. Use your Aedrova homepage. For a local
   test shared service on port 8090, set the callback to
   `http://127.0.0.1:8090/dots/github/callback`. For hosted activation, use the exact
   service origin plus `/dots/github/callback`. Enable expiring user access tokens.
   Repository permissions: **Contents, Issues, Pull requests, Deployments: Read-only**;
   Metadata is read-only. No account/organization/write permissions are needed.
   Install the App on **Only select repositories**, selecting the intended test repo.
   Generate an App client secret and retain the client ID in your secret manager.
3. On the Python shared service, configure `AEDROVA_DOTS_ENABLED=true`,
   `AEDROVA_GITHUB_DOT_CLIENT_ID` and `AEDROVA_GITHUB_DOT_CLIENT_SECRET`. Reuse the
   existing persistent `AEDROVA_ENCRYPTION_KEY` and database; do not rotate the key
   casually because existing encrypted sessions/records also depend on it.
   Use the example in the website repo at `deploy/dots.env.example`; save real values
   in an ignored local file or hosting secret store. Never paste them in chat.
   Restart that service. The desktop preview points to localhost:8090 and personal
   local Codex/Claude authentication; no paid provider access is activated here.
4. Sign in to the Aedrova website on that same service using the **same Google account**
   as the desktop. In the app: Buds → New Bud → name/appearance → GitHub → owner/repository → Save changes →
   Connect GitHub. Complete provider consent, return and click Refresh. Ask
   `@GitHub what changed recently?` or `@Aedrova explain our recent deployments`.
   Each user authorizes their own access; an admin's connection does not grant all
   members their credentials. Ensure the selected local AI provider is signed in.

The public waitlist deployment remains unchanged and disables account sign-in.
Do not enable public checkout/downloads or change the waitlist gate just to test Buds.
Use the existing local shared service for acceptance; a hosted private API deployment
and matching OAuth/Supabase redirect configuration require a separate approved release.

Optional events: configure a server-only `AEDROVA_GITHUB_DOT_WEBHOOK_SECRET`, then
GitHub App → Webhook URL `<shared HTTPS origin>/dots/github/events`, content type
JSON, matching secret, push/issues/pull-request/deployment events. Keep events disabled
on localhost unless a separately approved HTTPS ingress is provided.

If disconnect reports unsuccessful revocation, open GitHub → Settings → Applications →
Authorized GitHub Apps → Aedrova and revoke access. Workspace removal may require each
affected user to do that if GitHub is unavailable. Removed local grants are unusable
immediately even when provider-side revocation must be finished manually.

## Migration and extension boundaries

Old resource identities deduplicate by workspace/provider/resource. Legacy specialist
queue entries pause for review rather than silently running under the new model.
The durable queue, sandboxed coding runtimes, evidence/review/delivery and local
character physics are retained. Names do not confer permissions or change the central
agent identity. Changing Bud identity increments its version and requires renewed
user authorization; provider/resource changes require a new Bud.

To add a provider: implement the server `DotProvider` contract, bounded typed tools,
provider-supported auth/revocation and fixed allowed hosts; register capabilities,
normalize results/citations, add provider-specific signed event handling if needed,
then add tests before exposing availability. Never give the model arbitrary URLs,
queries, database service-role credentials or unrestricted actions.

The project uses OpenAI Responses through its existing managed gateway and Codex
runtime. It has no licensed avatar/identity API integration; Dots use the existing
original vector artwork and do not depend on scraped OpenAI interface assets.

## Validation

Final local checks: 632 desktop tests and 263 server tests passed. The embedded
PostgreSQL migration/RLS checks, packaged-app smoke check and strict bundle signature
verification also passed.

Automated provider/auth tests use fixture transport, never production credentials.
Desktop tests exercise targeted multiple-source selection, empty/unrelated selections,
malformed selections, persistent mentions, central build/query routing, source citations,
legacy migration and the real native profile/picker in both themes. Embedded PostgreSQL
runs all prior schema/RLS tests plus Dot creation, duplicate resources, restricted RPCs,
outsider isolation, revocation, optimistic versions, nickname conflicts and removal.
Live owner-provider authorization is still required; automated success is not hosted
acceptance. UI captures in `work/dots/` show actual Qt components with test fixtures.

For local browser sign-in, Supabase → Authentication → URL Configuration must allow
`http://127.0.0.1:8090/auth/callback` (or the exact local service port you chose).
Google Cloud's authorized redirect remains the Supabase provider callback, not this
Dot callback. Use a GitHub App registered for the same local callback during acceptance;
create/update the hosted callback only when the shared API deployment is approved.

After successful replacement authorization, unused prototype connector entries can be
removed from macOS Keychain Access by searching `com.aedrova.connectors`. Removing
those copies does not revoke the underlying provider/CLI login. This is optional local
cleanup, not a reason to revoke the GitHub CLI credentials used elsewhere.
