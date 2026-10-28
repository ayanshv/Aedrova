# Authentication and authorization

Last reviewed: October 24, 2026. Read with [Security.md](Security.md).

## Identity is not authority

Supabase Auth establishes the signed-in identity. Workspace membership, channel
visibility, ownership, billing authority, private Bud conversations and meeting
permissions are separate server/database checks. Knowledge of a UUID or possession of
the public Supabase key grants no resource access. Never accept a role from UI state.

Desktop evidence: `src/aedrova/identity/service.py`. It uses user tokens, in-memory
sessions and `persist_session=False`; tokens must not be written to QSettings or
project files. Context workers clone the authenticated session and check identity.
This is not a guarantee against malware running as the same OS user.

## Native sign-in

`src/aedrova/identity/oauth.py` opens the system browser and exchanges an authorization
code through the Supabase PKCE flow. The callback binds to `127.0.0.1`, has a random
per-attempt path, validates Host/path and bounded query/code fields, accepts one result,
and has cancellation/deadline handling. Responses use no-store and a restrictive CSP;
callback data is not logged. Do not replace PKCE with tokens in a URL or accept an
arbitrary redirect supplied by the browser. Test cancellation, duplicate callbacks,
wrong path/Host, stale codes and an already-occupied local port.

Hosted provider enablement and exact callback allowlists are deployment requirements.
An implemented login button does not prove the provider or redirect is configured.

## Website sessions and CSRF

The sibling backend's `aedrova_site/app.py` sets HttpOnly, SameSite=Lax cookies and
Secure cookies for production/HTTPS. Mutating cookie-authenticated requests require
the session's CSRF token, compared with `secrets.compare_digest`. Authenticated access
uses the private server session and validated identity; a bearer route must enforce
its own token scope rather than relying on cookie CSRF protection.

Verify allowed origins, HTTPS settings, session expiry and logout in the deployed
release. Logout must clear local/UI state and the applicable server session; test
that replaying the old session cannot access protected data. Do not describe logout
as revocation of every independent provider grant.

## Resource authorization

Use the SQL migrations under `supabase/migrations/` as the executable RLS/RPC contract.
New tables, functions and storage paths require explicit authorization review. Elevated
server credentials must never enter a desktop request or bypass user checks casually.
Check membership and private-channel visibility at retrieval time, including AI context,
file previews/downloads, meeting transcripts, DM history and realtime subscriptions.

Billing changes require authorized ownership/administration checked on the backend.
Entitlements derive from verified workspace billing state. Inviting a member is not
permission to create another charge. Parent/subspace inheritance must preserve access
boundaries; a shared allowance does not make private content shared.

## Connector authorization

Backend evidence: `../Aedrova_site/aedrova_site/bud_oauth.py`, `bud_account_oauth.py`
and `bud_connections.py`. Validate state, account/workspace binding, registered callback,
expiry and replay handling before saving a grant. Provider consent determines actual
scopes; never substitute “full access” language for granular authorization.

Connection success requires a completed callback AND a successful authorized resource
read. Test wrong account, denied consent, expired grant, refresh failure, disconnect,
revocation at the provider and resource removal. An unpublished/tester-only app is not
public-ready. Never widen scopes to make a test pass without review.

The legacy local connector vault in `src/aedrova/connectors/service.py` explicitly uses
macOS Keychain and refuses unsupported platforms; it does not fall back to plaintext.
This does not establish equivalent Windows credential storage. Hosted OAuth credentials
are a separate backend storage path. Both paths need release-platform acceptance.

## Agent and meeting tokens

Managed AI uses scoped short-lived run credentials and backend admission; the desktop
must not receive the provider's permanent secret. Provider selection does not authorize
new tools, filesystem access or spending. Confirm scope and expiry on every gateway
request. Meeting join tokens/leases require participant authorization independently of
being signed in, and context consent independently of joining a call.

## Required negative tests

Use synthetic accounts A and B in different workspaces and a private channel inaccessible
to B. Attempt reads, writes, context retrieval, download URLs, private Bud DM access,
billing operations and meeting admission as B. Also test removed members, expired
sessions, forged IDs, stale role caches and token replay. Denial must not reveal private
contents through errors, logs or optimistic UI. Record current release SHA and environment.

Local entry points: `tests/test_oauth.py`, `scripts/test_database.py` and the sibling
backend's `tests/test_endpoint_boundaries.py`, `tests/test_bud_oauth.py` and
`tests/test_bud_account_oauth.py`. Local tests do not replace hosted isolation tests.
