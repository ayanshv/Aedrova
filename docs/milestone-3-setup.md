# Milestone 3 — identity setup and validation

Status: local implementation; hosted end-to-end validation is still required. Milestone 4
must not begin until the milestone 3 gate passes and the owner approves it.

## Required owner actions

Customers use Google OAuth against Aedrova's one managed backend. Workspace membership
and RLS isolate each team's data. Customers never enter a project URL, API key or database
password, and never need a Supabase account.

1. Create/select a fresh development Supabase project.
2. In its SQL Editor, apply these migrations in order:
   - `supabase/migrations/202609260001_identity.sql`
   - `supabase/migrations/202609270001_agent_onboarding.sql`
   If the first migration was already applied successfully, apply only the second. Do not
   apply `supabase/tests/bootstrap.sql`; that is only for the embedded test database.
3. Configure Google Cloud's OAuth consent/branding and a Web application OAuth client.
   Register the exact Supabase callback URL displayed in its Google provider settings.
   Add two Google test users while your consent app is in testing.
4. Enable Google in Supabase Authentication providers and enter the Google client ID/secret
   directly there. Disable Email for this Google-only release. No SMTP setup is required.
5. Add `http://127.0.0.1:43827/auth/**` to Supabase Authentication's redirect URL allowlist.
6. Disable **Allow public access** in Supabase Realtime settings. Keep Auth abuse/rate-limit
   protections enabled. Application RPC rate limits are a required safety milestone 4A task.
7. Provide the project URL and PUBLIC publishable key to the build process. We can package
   them into the app; there is no customer configuration form. Never send Google secrets,
   service-role keys or database passwords in chat. See `google-sign-in.md` for details.
8. Complete Google consent in the browser, then create/join a workspace. Choose a team-wide
   agent nickname and preferred provider. Test with both accounts, including separate
   workspaces and an invitation. These live checks are required before milestone 3 completes.

The generated public configuration is bundled in the app. Passwords and session/refresh
tokens are never written to QSettings or disk. Sessions currently stay in memory; restart
requires Google sign-in. Background operations keep the UI responsive. Workspace invitations
are manually shared, single-use codes; the app does not claim to send invitation emails.

## Authorization contract

- PostgreSQL is authoritative. All reads use the user's JWT and RLS. Mutations use narrow
  security-definer RPCs with an empty search path, explicit caller validation and grants.
- Workspace owner is immutable in this first version; owner transfer/deletion needs a
  separate verified workflow. Owner account deletion must not be enabled casually in Auth.
- Owners can assign admin/member/guest roles. Admins can invite/remove members and guests,
  but cannot promote users or remove owners/admins. Non-owners may leave via Remove member.
- Private channels require explicit channel membership, including for owners/admins.
  Guests need explicit access even to public channels. Channel access can be administered
  only by an owner/admin who can already read the channel.
- Members may create public channels. Only owners/admins create private channels, avoiding
  private rooms whose creator cannot manage access. The creator gets explicit membership.
- Invitations are confirmed-email-bound, single-use and expire after seven days. Only the
  SHA-256 digest is stored. Redemption checks the inviter's current authority. Joining
  cannot overwrite an existing role. Workspace locks serialize membership mutations.
- Private `aedrova-files` paths must be `<workspace UUID>/<channel UUID>/<object name>`.
  Reads require current channel access; all client writes are denied until attachment
  validation is implemented. No public bucket or signed URLs are created.
- Realtime policies authorize new private-topic subscriptions. Existing socket authorization
  can be cached by Realtime; live revocation/disconnect behavior is an explicit milestone 4
  gate. Do not treat a policy query as proof of existing socket termination.

## Tests

```sh
uv sync --frozen
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run python scripts/test_database.py --node /path/to/node
```

The last command downloads pinned PGlite 0.5.8 into ignored `work/`, verifies the registry
integrity hash, and runs the unchanged migration and SQL permission tests in disposable
PostgreSQL. The Python runner uses a tiny generated adapter for that third-party Node/WASM
engine; no JavaScript ships in the product. This exercises SQL/RLS/grants, not GoTrue Auth,
PostgREST, the Storage HTTP API or Realtime sockets. SDK HTTP tests use mocked transport.

For a disposable hosted/local Supabase database, apply the migration normally and execute
`supabase/tests/identity.sql` and `supabase/tests/agent_onboarding.sql` through psql with `ON_ERROR_STOP=1`. Its fixtures roll back.
It uses fixed test user IDs; never run it against production. Then perform live checks:

- Two confirmed accounts in separate workspaces; login, refresh, logout and relaunch.
- Invite email mismatch, expiry, replay, revocation and inviter demotion.
- Cross-tenant REST reads/writes, private-channel access, guest grants and role escalation.
- Storage list/download deny and allow checks through HTTP, not just SQL.
- Private Realtime subscription deny/allow, and public-topic configuration verification.
- Packaged app login and workspace creation with the deployed migration.

Chat remains explicitly labeled local sample data. Accounts and workspace administration
are in the Account screen; connecting the main conversation UI is milestone 4.

References: [Supabase RLS](https://supabase.com/docs/guides/database/postgres/row-level-security),
[Storage policies](https://supabase.com/docs/guides/storage/security/access-control),
[Realtime authorization](https://supabase.com/docs/guides/realtime/authorization),
[Python Auth](https://supabase.com/docs/reference/python/auth-signinwithpassword).
