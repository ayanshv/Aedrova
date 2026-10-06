# Shared meeting announcements

The chat header’s call bar offers Start audio/video call until a channel meeting exists, then Join
meeting with up to four circular participant photos and an exact presence count. Photos
use the participant Google profile where available; initials are the accessible fallback.
Joining still opens the existing prejoin call controls with devices off.

Public meetings show a join card in their own channel and #general by default. Workspace
owners/admins may select another public announcement channel in Meetings. The setting
is shared; private/DM meetings are announced only inside their originating channel.
Only meetings authorized by channel access are fetched, with expired presence omitted.
Ended meetings disappear. Updates use the existing approximately three-second refresh.
Cards are live status, not synthetic permanent chat messages or OS push notifications.

## Required owner action now

In Supabase Dashboard → SQL Editor → New query, paste and run the complete contents of
`supabase/migrations/202610030004_meeting_activity.sql`. Do not rerun the older migrations.
This adds the narrowly scoped activity/profile RPC and shared announcement preference.
Until applied, shared discovery/profile photos cannot be validated live. Then quit Aedrova
and reopen `/Users/ayanshvarma/Documents/Aedrova/dist/Aedrova.app`. No website deployment
or new credentials required. The local meeting service must remain running on port 8090.

## Validation

493 desktop tests passed; the final layout adjustment also passed 31 focused meeting/
chat tests. All 25 embedded PostgreSQL migration/test files passed, including outsider/
anonymous exclusion, unauthorized configuration rejection, private-channel destination
rejection, unsafe avatar exclusion, presence expiration via leave and ended-state removal.
Ruff, whitespace, light/dark 450/900-pixel visual inspection, Apple Development preview
signature, package secret scanner and packaged smoke passed. Real shared-account
acceptance is pending the owner applying the SQL. No hosted data changed or deployment
was performed. Ask permission before the next task or resuming M14.

Meeting devices, announcement settings and transcript history are available from the
call bar’s ⋯ menu. The former Meetings tab has been removed. Audio starts without
camera capture; video requests camera and microphone permissions after connection.
No new SQL or service configuration is required for this navigation change.
