# Owner checklist — Google login and team onboarding

These are one-time Aedrova infrastructure tasks. Customers only use Google login and
create/join a workspace; they never need Supabase accounts, database URLs or API keys.
Milestone 3's live validation is blocked until these actions are complete.

1. **Supabase project:** create/select Aedrova's dedicated development project. The one
   managed database stores all teams with workspace-based RLS separation.
2. **SQL Editor:** apply `202609260001_identity.sql`, then
   `202609270001_agent_onboarding.sql` from `supabase/migrations/`. If you already applied
   the first migration successfully, apply only the second. Both are transactional.
   Do not apply test bootstrap SQL to Supabase.
3. **Google Cloud / Google Auth Platform:** configure Aedrova's branding and OAuth consent
   audience. Create a **Web application** OAuth client because Google returns to Supabase.
   Add the exact callback from Supabase's Google provider screen, normally
   `https://<project-ref>.supabase.co/auth/v1/callback`, to Authorized redirect URIs.
   Add two Google test accounts while the consent app is in testing.
4. **Supabase Authentication → Providers → Google:** enable Google and enter the Google
   client ID and client secret directly there. Disable the Email provider for this
   Google-only product. Never paste client secrets or service-role keys into chat or source.
5. **Supabase Authentication → URL Configuration:** add the desktop redirect allowlist entry
   `http://127.0.0.1:43827/auth/**`. This is separate from Google's Supabase callback above.
6. **Supabase Realtime settings:** disable Allow public access. Keep Supabase Auth's
   rate-limit/abuse protections enabled. Custom workspace/RPC limits are milestone 4A work.
7. **Build configuration:** provide the Supabase project URL and public publishable key
   to the build process (these two public values can be shared with Codex). We will embed
   them in Aedrova. Google client secrets stay in Supabase. The current preview is
   unconfigured until these public values are supplied and the app is rebuilt.
8. **Live validation:** sign in with the two test Google accounts, create separate teams,
   name an agent, and test an invitation. We still need hosted negative REST, Storage and
   Realtime checks before declaring milestone 3 complete. Report any setup errors verbatim
   after removing secrets; successful local tests are not a substitute for this stage.

No SMTP setup is needed for Google-only sign-in. Invitations currently use manually shared,
single-use codes. No Stripe setup or GitHub OAuth configuration is needed for this milestone.
Before public release, publish the Google consent app and complete any branding/domain
verification Google requests. Signing/notarization remains the Mac release milestone.

## What the customer experiences

Google login → create or join a team → choose an agent nickname and preferred provider.
The nickname defaults to Nova, is shared across the workspace, and can be changed by an
owner/admin. Joining teammates inherit it. Product branding always remains Aedrova.
Provider choice is saved now; actual Codex/Claude Code execution arrives in milestone 5.
The connected chat surface arrives in milestone 4; `--demo` is explicitly sample chat only.
Sessions are memory-only in this preview; Keychain persistence is not yet implemented.

## Next delivery gates

Milestone 4: shared messages, threads, DMs, attachments, unread indicators, reconnect/retry,
and replacing sample conversations with authorized connected workspace data. It requires
milestone 3 live validation and owner permission.

Milestone 4A: app safety before real code execution. Audit secrets/environment-file leakage,
privileged keys, auth/tenant boundaries, hidden privileged paths/backdoors, dependencies,
server-enforced rate limits and quotas, file limits, logging/redaction, incident handling,
and agent sandbox/tool/network permissions. Repeat relevant checks before beta and release.

References:
- https://supabase.com/docs/guides/auth/social-login/auth-google
- https://supabase.com/docs/guides/auth/redirect-urls
- https://supabase.com/docs/guides/realtime/settings
