# Bud connectors — implementation and owner setup

## Delivered locally

A reference-led native gallery is available from Account → Connectors, Settings →
Manage connectors, and directly in step 5 of Bud setup. The setup panel widens
into a categorized, searchable three-column gallery with role suggestions.
Selecting a card opens a scrollable resource/permission screen within the same
flow in light or charcoal dark themes. Connecting a new Bud saves its profile
first; edited profiles are saved before granting access to the current version.
No extra window opens or steals fullscreen focus. Navigation and Bud switching
are disabled while verification is pending; closing clears the masked token.

Ten real read adapters are implemented. They contact provider APIs to verify every
advertised capability before showing Connected. No simulated connection is stored.
Each Bud supports up to 12 resources per user; teammates authorize their own access.
Tokens are encrypted in the private service database, excluded from shared Supabase
profiles and AI prompts. Resource IDs and names can enter the AI's tool catalog.
Membership, Bud version, resource ownership, expiration and revocation are checked
before and after reads. Evidence is bounded and treated as untrusted input.

This release supports scoped tokens plus browser OAuth and automatic refresh for
GitHub Apps, Figma, Notion, Supabase Management API and Linear. Existing GitHub App
OAuth remains compatible. Social OAuth/publishing and external write actions are
not implemented by this change. See the server checkout’s `docs/bud-oauth.md` for
exact app registrations, callbacks and encrypted credential setup. Adapters have HTTP contract tests;
successful live account reads still require your credentials and acceptance checks.
Nothing has been pushed or deployed by this task.

## Required now: database update

In your existing Supabase project's SQL Editor, paste and run the entire file:
`/Users/ayanshvarma/Documents/Aedrova/supabase/migrations/202610070004_bud_connectors.sql`.
Earlier Bud profiles and appearance migrations must already be installed. This
idempotent migration adds permitted provider/resource types while preserving
owner/admin checks, version conflicts and resource immutability. It does not store
provider tokens. New primary-provider Buds cannot save until this migration runs.
The private connector table is created automatically by the shared service.

Quit and reopen the rebuilt `dist/Aedrova.app`. Sign into the local shared service
using the same Google account as the desktop, then open Connectors and choose a
saved Bud. Select a tool, enter its resource ID and paste its token into the masked
field. Choose an expiration and click Verify & connect. Never paste tokens in chat
or commit them to Git. Aedrova expiration removes local access; it does not revoke
the token at the provider. Disconnect removes your selected grant immediately;
revoke its token in the provider dashboard too when it is no longer needed.

## Provider setup and implemented scope

Start with one provider. Use the least privilege available and a development
resource. Where a provider only offers broad personal tokens, Aedrova's adapter
still restricts which resource and operations can be used; the token itself may
have broader privileges outside Aedrova.

| Tool | Token and resource | What the Bud can currently read |
| --- | --- | --- |
| GitHub | Settings → Developer settings → Fine-grained personal access tokens. Select a repository and read permissions for Metadata, Contents, Issues, Pull requests and Deployments. Resource: `owner/repository`. | Repository metadata, recent commits, open issues and deployments. No pushes or writes. |
| Supabase | Account → Access tokens: Management API token. Resource: your 20-character project reference. Do not use publishable or service-role database keys. | Selected project name, region and status. No database rows, SQL, secrets or API keys. |
| Figma | Settings → Security → Personal access tokens, with `file_content:read`. Resource: the file key from its URL. | File name and bounded page/frame labels. No screenshots, renders or image interpretation. |
| Notion | Create an internal integration with Read content, then share the selected page with that integration. Resource: page UUID; token: integration secret. | Page title and up to 20 immediate blocks. No nested-page traversal or writes. |
| Stripe | Dashboard → Developers → API keys → restricted key (`rk_test_` first), read permissions for Account and Balance. Resource: matching `acct_` account ID. | Available/pending account balance in minor currency units. This is not revenue or profit. No customer personal data or payment writes. |
| Instagram | Meta developer app with Instagram API using Instagram Login; authorize a professional Business/Creator account with `instagram_business_basic`. Resource: authorized Instagram user ID; token: its user access token. | Profile and up to ten posts. No publishing, messaging or personal-account support. |
| TikTok | Developer app with Login Kit and Display API, scopes `user.info.basic` and `video.list`. Resource: authorized `open_id`; token: user access token. | Profile and up to ten public videos. No publishing or messages. |
| Web search | Brave Search API subscription token. Resource: a saved research topic of 3–200 characters. | Up to five result snippets. Linked pages are not fetched. Searches may consume paid provider usage. |
| Vercel | Account settings → Tokens, scoped to the relevant account/team. Resource: `prj_` project ID. | Project metadata and up to ten deployments. No environment variables or deployment writes. |
| Linear | Settings → Security & access → personal API key with read access. Resource: team UUID. | Team metadata and up to ten issues. No issue writes. |

Instagram and TikTok require your provider developer applications and valid consent
tokens; app review/approval is required before offering access to other users. Their
OAuth acquisition flows are not built into Aedrova yet. Existing GitHub OAuth needs
the ignored server `.env.dots` configured as described in `docs/dots.md`; GitHub
personal-token access works independently of those OAuth credentials.

Official setup references: [Figma](https://developers.figma.com/docs/rest-api/personal-access-tokens/),
[Notion](https://developers.notion.com/guides/get-started/quick-start),
[Stripe](https://docs.stripe.com/keys),
[Supabase Management API](https://supabase.com/docs/reference/api/introduction),
[Instagram](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login),
[TikTok Display API](https://developers.tiktok.com/doc/display-api-overview/),
[Brave Search](https://brave.com/search/api/),
[Linear](https://linear.app/developers/graphql),
[Vercel](https://vercel.com/docs/rest-api).

## Acceptance and next tasks

After SQL and a token are configured, validate a real provider read, a source-backed
Bud answer, immediate disconnect, token expiration and another user's independent
access. Automated tests cover these boundaries with controlled provider responses;
they do not replace successful live acceptance. Public deployment remains separate.

Next work, after owner approval: guided OAuth connections/refresh and live provider
acceptance; then remaining role tools (Drive, Sheets, analytics, accounting), and
explicitly approved write capabilities. M14 remains deferred until feature work is
complete. Marketing claims should reflect each validated capability and its limits.


### Addressed Bud identity — October 8, 2026

Direct Bud mentions now preserve the selected Bud name and configured sprite through
working messages and the final response. Read-only questions restrict retrieval to that
Bud’s grants; action-word build requests preserve the Bud profile in the existing durable
queue and retain project permissions, version checks and review behavior. The central
agent remains available through its own mention. Choosing a look in Bud setup selects
the matching specialty and connector recommendations automatically.

The owner’s newly connected local GitHub workspace has a private $2 development
allowance for 24 hours, with the existing concurrency and spend caps. This is not a paid
subscription, is not auto-renewed, and does not enable public checkout. Live repository
reading and run authorization passed; the owner must reopen the rebuilt app and retry
the chat request to verify the complete interactive response.

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

Resource inputs now include provider-specific lookup instructions. Supabase
uses Project Settings → General → Reference ID, also visible after /project/
in the dashboard URL. Its account sign-in requires an HTTPS service callback;
HTTP loopback is rejected by the provider. Credentials alone do not unblock it.


### Hosted connector preview — October 8

The signed preview bundles https://aedrova-connectors.onrender.com as its separate
connector_origin. AI and meetings retain their local managed_origin. Hosted
GitHub and Supabase callbacks are saved; GitHub retains its local callback too.
Readiness, restricted routes, 45 focused native tests and deep signature checks
pass. Hosted provider reads require sign-in and per-Bud reauthorization; local
SQLite grants are not migrated. Figma/Notion need sign-in, and the Linear account
has no workspace yet. Remaining providers need credentials and live acceptance.

Native Google sign-in and hosted Bud catalog/profile reads passed live. Supabase
OAuth now reaches its actual Projects Read consent page for the Aedrova organization
with the correct HTTPS callback; approval and project-read verification remain.
Bud-only requests allow 90 seconds for Render free-host wake-up; AI timeouts retain
their existing defaults. Network failures identify the connector service accurately.
48 focused desktop tests and 12 service-boundary tests pass. Figma registration is
prepared but submitting Create app accepts Developer Terms, requiring action-time
approval. No provider credentials were generated during this follow-up.
