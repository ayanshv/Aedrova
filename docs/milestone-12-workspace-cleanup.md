# M12A — personal workspace cleanup

Owner approved M12 on October 2, 2026 and requested the latest possible Apple Developer
and domain setup. This task adds personal workspace archive/restore without deleting
shared data or changing the product design. M12 as a whole is not complete.

## Implementation

Account & workspaces now has Archive for me, a themed confirmation and a restore picker.
The server stores a private preference for the authenticated member, not a global archive
flag. Only that account's dashboard hides the workspace. Other members, files, messages,
permissions, project bindings and subscriptions remain intact. This is organization, not
revocation, deletion or a billing action. Complete local builds and leave calls first;
the UI checks before opening and submitting confirmation. Unsaved chat drafts can be
cleared when the dashboard closes or changes to the next visible workspace.

When every workspace is archived, the account screen still offers restoration and creation.
Restoring selects the restored workspace. Successful writes followed by failed refreshes
are identified as saved; the app does not silently repeat the mutation. Signing out clears
archived workspace names as well as the normal account state.

Database access uses explicit user-JWT RPCs, confirmed-account validation, membership
checks, row locks shared with membership mutations and an atomic idempotent preference
update. Changed archive choices are limited to 20/minute/account. RLS hides other users'
preferences; direct client writes and anonymous RPC execution are forbidden. Removing a
membership also removes its personal preference.

## Required owner action

Local validation: 418 desktop tests and 154 website/backend tests pass; all 17 embedded
PostgreSQL migration/test scripts pass, including archive isolation, preservation,
idempotent retries, membership-removal cleanup and anonymous denial. Scoped Ruff, basic
mypy (58 desktop source files, external stubs/untyped bodies excluded) and whitespace
checks pass. Account/confirmation layouts were rendered and inspected in both themes.
The development app was rebuilt; strict signature and packaged light/dark launch smokes
passed. These are local checks, not hosted archive/restore acceptance or public signing.

Before running the rebuilt app, open Supabase → SQL Editor → New query, paste the desktop
repository's `supabase/migrations/202610020002_workspace_archive.sql` and click Run once.
Apply it after the existing scalability migration. Never run `supabase/tests` on Supabase.
This new migration is required for the app's workspace inventory and personal organization
controls; it changes no existing messages or billing records. No new credentials are needed.

Then sign in, open Account & workspaces, archive a test workspace and restore it. Verify
the dashboard removes/re-adds it and the other account's workspace stays visible. Hosted
acceptance remains pending until the migration and this signed-in check.

## Next M12 task (permission required)

Consent-based meeting transcript storage and permission-scoped AI retrieval, with visible
participant choices and revocation handling. Automatic speech transcription needs a chosen
provider and server-side credentials; this must never be inferred from joining a call.
Transcription, meeting summaries/decisions/action items and agent retrieval are not yet live.
Shared HTTPS hosting and two-device physical meeting acceptance remain deferred requirements.
No commercial-provider or GitHub/IDE acceptance claim is added by workspace cleanup.

Apple Developer setup/signing/notarization stays in the M13 public installer gate. A custom
domain stays optional until launch; use a provider HTTPS URL for interim hosted testing.
The app is still a development preview, not a publicly accepted/notarized distribution.
