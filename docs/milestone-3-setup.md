# Milestone 3 — identity setup and validation

Status: local implementation; hosted end-to-end validation is still required. Milestone 4
must not begin until the milestone 3 gate passes and the owner approves it.

## Connect a development Supabase project

1. Create or select a dedicated development project. Use a fresh project for this initial
   migration; it intentionally does not silently replace existing policies or tables.
2. Apply `supabase/migrations/202609260001_identity.sql` in the project's SQL Editor or
   your Supabase migration workflow. Do NOT apply `supabase/tests/bootstrap.sql`; it is
   only a facsimile of Supabase schemas for embedded PostgreSQL testing.
3. Enable email/password Auth and email confirmation. Configure the Auth site/redirect
   URL to a page you control. Users confirm via the emailed link and then sign in to the
   desktop. To use the optional code entry, include `{{ .Token }}` in the signup email
   template. Configure SMTP for reliable delivery; signup may hit provider rate limits.
4. In Realtime settings, disable public channel access. Future subscriptions must use
   private channels and `channel:<channel UUID>` topics. Only authorized server broadcasts
   are readable; client broadcasts and presence are denied in this milestone.
5. Launch the app and choose **Account → Account & workspaces…**. Enter the project URL
   and public publishable key (legacy anon JWTs also work). Service-role and secret keys
   are rejected. Optional environment values are documented in `.env.example`; the app
   does not automatically read `.env` files.
6. Create and confirm accounts. Sign in, create a workspace, create invitation codes and
   share those codes manually with their named recipients. No invitation email is sent
   by Aedrova. Invitees sign in with a matching confirmed email and enter the code.

Public connection configuration is saved in QSettings. Passwords, session/refresh tokens
and invitation codes are never written there. Sessions are memory-only: restarting the
app requires sign-in. SDK session refresh and user verification precede each operation.
Requests run in a Qt thread-pool job; all UI updates return through a Qt signal.

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
`supabase/tests/identity.sql` through psql with `ON_ERROR_STOP=1`. Its fixtures roll back.
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
