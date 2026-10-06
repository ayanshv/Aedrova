# User profiles and onboarding

Profiles add an editable display name, unique username, photo or initials, short bio,
job title, custom status and emoji, and Online / Away / Do not disturb availability.
The account menu and Settings → Edit full profile reopen the same three-step editor.
First sign-in prompts incomplete profiles once per app session. Optional details and
first-run setup may be skipped; existing workspace and project onboarding follows.

Photos are cropped centrally and converted locally to 256×256 PNGs, discarding source
metadata. Avatars use the private `aedrova-avatars` bucket and authenticated downloads.
Only the owner and active workspace teammates can read a published avatar. Local
photo caches are cleared on sign-out. Job titles do not grant workspace permissions.
User mentions accept display names and usernames and send stable user IDs.

## Owner action required

In Supabase → SQL Editor, run the full contents of
`supabase/migrations/202610040002_chat_collaboration.sql` if not already applied.
Then run `supabase/migrations/202610050001_user_profiles.sql` once. The latter extends
profiles, creates the private avatar bucket/policies, adds profile RPCs and updates
presence RPCs to preserve new fields. Restart the rebuilt app afterward.

Hosted profile saving is pending this migration and a live account check. No secrets
or new provider configuration are required. Do not repeat migrations already applied.

## Validation

Qt tests exercise the guided flow, photo processing, validation, taken-username errors,
mentions, one-time prompting and sign-out cleanup. Embedded PostgreSQL checks profile
ownership, unique usernames, immutable workspace roles, presence preservation, name
search and avatar isolation. Six light/dark profile screens were rendered and reviewed.
A full hosted Storage upload/download cannot be verified before owner applies SQL.

A timed-out save can leave an unpublished private upload. It is deliberately retained
because the server might have committed the profile despite the timeout; deleting it
blindly could break a successfully published photo. Unpublished objects are inaccessible
to teammates and should be included in future avatar storage retention maintenance.

Shotbase's installed app was inspected without resetting preferences. Its first-run
onboarding could not be replayed; matching that exact flow needs an owner screen recording.

Latest verification: 526 Python/Qt tests passed; all migration/RLS suites passed.
The rebuilt `dist/Aedrova.app` passed deep signature verification and packaged launch
smoke checks. Targeted profile, shell and collaboration tests cover the final styling
and PNG decoder restriction after the full suite.
