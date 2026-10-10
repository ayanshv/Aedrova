# Google-first desktop sign-in

Customers see Continue with Google. There are no email/password or connection forms. Supabase
configuration is absent from the customer form. The system browser handles Google;
the desktop receives a one-time code on loopback and exchanges it with a memory-only
PKCE verifier using the official SDK. No Google client secret ships in the desktop.
Supabase creates the Auth identity on first successful Google sign-in. Workspace access
still requires creating a workspace or accepting an email-bound invitation; a matching
email domain alone never grants membership.

## Owner actions required now

These steps block live Google sign-in, not local code/UI testing. They are one-time
application infrastructure setup; customers do not create Supabase projects or enter keys.

1. Finish the development Supabase project and SQL migration described in
   `milestone-3-setup.md`. Apply both identity and agent-onboarding migrations in order.
2. In Google Cloud / Google Auth Platform, configure the app branding/consent screen.
   Create an OAuth client of type **Web application** (Supabase is Google's callback).
   Register the exact callback URL shown by Supabase's Google provider settings, normally
   `https://<project-ref>.supabase.co/auth/v1/callback`, as an authorized redirect URI.
   While the Google app is in testing, add the Google accounts you will test with.
3. In Supabase **Authentication → Sign In / Providers → Google**, enable Google and enter
   that client ID and client secret. Disable the Email provider for this Google-only release. Enter the secret directly in Supabase, not in chat,
   source code or the desktop. Save the provider configuration.
4. In Supabase **Authentication → URL Configuration → Redirect URLs**, add:
   `http://127.0.0.1:43827/auth/**`
   The fixed loopback port and unpredictable path belong to this desktop build. The
   browser returns to the same Mac, not to a public server. Do not substitute Google's
   callback URL in this field; Google and the desktop have different redirect steps.
5. Give the build process `AEDROVA_SUPABASE_URL` and
   `AEDROVA_SUPABASE_PUBLISHABLE_KEY`, then run `uv run python scripts/package_desktop.py`.
   The packager validates and embeds these PUBLIC settings as `public-config.json` in the
   app bundle. Installed customers have no connection setup or override UI. Packaged builds
   ignore environment and old QSettings backend overrides. Source development runs can use
   environment values. A build without public configuration is explicitly unconfigured.
6. Click Continue with Google, complete consent, return to the app and create or join a
   workspace. Report the result so hosted tenant-isolation checks can be completed.

For public release, move the Google consent app out of testing and complete any branding
or domain verification requested by Google. Google-only sign-in does not need Supabase SMTP. Aedrova currently uses manually shared
workspace invitation codes; automated invitation email would require a mail integration. The database migration and Realtime configuration remain required.

## Implementation and current limits

- Loopback listener binds only 127.0.0.1, lives for at most three minutes, accepts only the
  per-attempt unpredictable path, rejects ambiguous codes, suppresses callback logging and
  sends no-store responses without reflecting tokens or user input.
- Supabase's PKCE verifier stays in memory. Wrong callbacks cannot establish a session
  without the matching verifier. Cancellation closes the listener; a late completed
  exchange is signed out if cancellation was requested.
- Browser launch failure, provider rejection, timeout and listener conflicts return to
  a retryable state. One login attempt can use the fixed port at a time.
- Tokens are memory-only; this change does not add Keychain session persistence.
- Local callback tests and mocked SDK exchanges are not a live Google integration test.
  Provider configuration and a successful packaged end-to-end login are still required.

Official references:
- https://supabase.com/docs/guides/auth/social-login/auth-google
- https://supabase.com/docs/guides/auth/redirect-urls
- https://supabase.com/docs/reference/python/auth-signinwithoauth

## Team onboarding

After Google login, users with no workspace see workspace creation or Join my team.
Creating a workspace includes a shared agent nickname (default Nova) and a preferred
provider (Codex or Claude Code). Both are stored atomically with the workspace. Owners
and admins may rename the agent later. Members and guests inherit the team name; they
cannot change it. A nickname is presentation data, never an authorization identity or
executable instruction. Aedrova's product/window/logo branding remains unchanged.
Provider selection stores a preference; actual agent execution remains milestone 5.

Default launch now opens the account screen. `--demo` explicitly opens sample chat for
development; that path contains no connected workspace data and does not bypass RLS.
