# Bud connectors — current implementation and acceptance

Updated October 10, 2026. This replaces the earlier local-only setup notes.
The owner confirmed the existing connector SQL migration succeeded; no new SQL
is required for this validation pass. Linear is intentionally removed.

## What works in the implementation

The native, role-filtered gallery is available in Bud setup and Account → Connectors.
Configured providers use browser OAuth as the primary path. Paste a resource URL
where supported; the app extracts the repository, file, page or project reference.
TikTok resolves the authorized account automatically. Advanced scoped tokens remain
available; these are not an invitation to paste a secret into chat.

The isolated HTTPS service is https://aedrova-connectors.onrender.com. Public
website checkout remains in waitlist mode. AI access and meetings are separate
from this connector-only service. Its free Render instance may sleep.

Credentials are encrypted in the private service database. Each grant belongs to
one user, workspace, Bud version and resource. Reads are bounded and rechecked
before returning evidence. Disconnect and expiry withhold access; disconnect
removes Aedrova's grant, not necessarily the provider's token. Provider data is
untrusted evidence and does not grant permission to execute instructions.

Direct Bud mentions use that Bud's name, sprite and authorized tools. A leading
Bud mention or explicit Bud token also takes precedence if its name matches the
main agent's nickname. Mentioning a Bud inside a request addressed to the main
agent does not change the recipient. Builds keep the existing project permissions
and review flow. Every model run still needs configured workspace AI access.

New onboarding requires a configured Bud with a verified connection before its
completion flag is persisted. Canceling returns to setup. Drafts may still be
saved outside required onboarding without pretending they are connected.

## Provider acceptance matrix

“Previously live” below records earlier observed provider reads; it does not mean
refresh, revocation and every new account have passed live acceptance.

| Provider | Implemented access | Live acceptance / remaining gate |
| --- | --- | --- |
| GitHub | App OAuth; repository metadata, commits, issues/PRs, deployments | Previously live read passed. Fresh grant, refresh and disconnect acceptance remain. |
| Supabase | OAuth; selected project's name, region and health | Previously live read passed for Pebble. No SQL, database rows, keys or secrets. |
| Figma | OAuth; file name and bounded page/frame labels | Previously live read passed for Pebble. No renders or design edits. |
| Notion | OAuth; selected page title and up to 20 immediate blocks | Previously live read passed on a dedicated empty validation page. Live refresh pending. |
| TikTok | OAuth sandbox; profile and up to 10 public videos | Previously live read passed for Orbit. Production review and live refresh pending. |
| Instagram | Scoped professional-account token; profile and up to 10 posts | Meta app/consent setup and live acceptance pending. No publishing. |
| Stripe | Restricted key; available/pending account balance | Owner key and live acceptance pending. Balance is not revenue or profit. |
| Web search | Brave API key; up to 5 result snippets | Owner key and live acceptance pending. Search may incur provider usage. No linked-page fetching. |
| Vercel | Scoped token; project metadata and up to 10 deployments | Owner token and live acceptance pending. No environment variables or writes. |

All adapters have controlled HTTP tests. These tests do not replace live provider
consent, production app review or independent-account acceptance.

## October 10 validation evidence

Both full suites passed: 701 desktop tests and 391 website/service tests before
this pass's additional regression cases. Focused tests additionally exercise
same-name Bud routing, explicit mention tokens, required verified-tool onboarding,
changed Bud settings, disconnected/expired grants and account isolation.

Live UI: existing Google sign-in returned to the desktop, workspace navigation
worked, and the hosted Bud setup loaded successfully. A fresh Google account and
its new provider grant have not been tested. Existing grants must be located in
the owning account/workspace before claiming a new live source-backed Bud answer.
Do not reset a real grant's expiry or disconnect it solely to simulate a test.

## Owner actions and release gates

For the next live acceptance, open Aedrova with the Google account that owns the
existing Pebble/Orbit Buds, select their workspace, then open Account → Connectors.
This identifies the existing authorized resources without creating broader access.
Any fresh provider consent is a separate explicit approval step.

For Finance later: in Stripe Dashboard → Developers → API keys, create a restricted
**test** key with Account and Balance read access only. Enter it in Aedrova's masked
Stripe connector field with the matching account ID; never send it in chat.
Instagram needs a Meta developer app and professional-account consent. Brave and
Vercel need their scoped keys. These block those providers' live acceptance, not
this completed code test pass. No purchase or production Stripe checkout is needed
for read-only connector testing.

Marketing image/video generation remains planned after connector acceptance.
Publishing will require separate scopes and approval. M14, always-on hosting,
Apple signing/notarization and public DMG/Windows release remain deferred.

## Sign-in-first connector experience — October 10

Supported account connections no longer ask customers for IDs or credentials
before sign-in. GitHub, Supabase and Notion show named choices after OAuth;
TikTok uses the authorized account directly. Figma uses browser sign-in followed
by a file link because its current file-content permission does not list all files.
Token entry remains an explicitly opened advanced option, never the default.
A disconnected Bud draft uses pending metadata until authorization; this does
not grant access. Only verified resource reads create a connected grant.

Picker discovery reads names and IDs only from the consented account. Choices
are bounded: first 100 Supabase projects / Notion pages, or repositories from
first 10 GitHub installations (100 each). Figma verifies its selected file.
Intermediate tokens stay encrypted on the connector service for the existing
10-minute authorization window and are removed when selection completes/fails.
No new OAuth scopes, SQL migration, developer app or customer-entered code is
required for this improvement. No provider publishing/review gates are bypassed.

Owner required now: quit the desktop preview (⌘Q), reopen
`/Users/ayanshvarma/Documents/Aedrova/dist/Aedrova.app`, open a Bud's Connectors,
choose the service and click Connect account. Authorize only intended resources.
Fresh live consent and selected-resource reads remain acceptance checks; local
HTTP tests do not substitute for those. Instagram, Stripe, Vercel and Search
still need their outstanding provider support/setup before they can offer the
same account-login experience. M14 and public Beta remain deferred.
