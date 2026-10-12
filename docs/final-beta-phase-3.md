# Phase 3 — meeting wrap-up review (October 11, 2026)

The owner authorized Phase 3 after non-Stripe Phase 2 acceptance, then explicitly
requested this post-meeting review feature during the Phase 2 checks. This specific
implementation is authorized now; Phase 2 is not silently marked complete, and
the remaining Phase 3 voice/file work has not started. Stripe stays deferred.

## Implemented

- A final participant leave ends an empty meeting under the existing meeting lock.
  Leaving while another participant has a live lease keeps the meeting active.
- After transport/device cleanup, the backend determines whether the meeting has
  ended, retained transcript exists, and the current participant is an owner/admin.
  Ordinary members cannot review other speakers through this new confirmation.
- If an authorized administrator leaves seconds before the rest of the group, a
  bounded background check waits up to one minute for actual room closure. It never
  shows an early review or follows the user into another account/workspace/new call.
  Longer-running meetings remain accessible through existing transcript history.
- The themed native review asks **Share with Aedrova?**, presents timestamped,
  attributed transcript parts, allows corrections, and has **Confirm** as its
  primary action. **Review later** saves nothing; existing meeting-history review
  remains available. No implicit recording or microphone capture is introduced.
- All corrections are local drafts until one atomic server confirmation. Expected
  versions and exact transcript membership prevent partial, stale, duplicated,
  deleted or cross-meeting confirmation. Original text, speaker/citation, expiry,
  existing decision classification and participant AI permissions are preserved.
- Only previously AI-consented text is eligible for the existing permission-scoped
  context retrieval. Confirmation does not grant or restore withdrawn AI access.
- Session closure clears private drafts; delayed callbacks cannot reopen a review
  for another account, workspace or a newer call. No raise/activateWindow calls.
- Maximum 10,000 segments, 2,000 characters per segment, bounded combined payload,
  five confirmation attempts/minute and bounded loading. Very large reviews fail
  with a reload/history path rather than silently confirming a partial transcript.

## Verification and limits

Focused native lifecycle/editor checks and HTTP forwarding/gating tests passed.
Actual embedded PostgreSQL migration/RLS tests cover ongoing/empty rooms, ordinary
members and outsiders, stale/partial/replayed reviews, preservation of originals,
AI consent and withdrawal. Both light/dark native renders inspected. These use
disposable local fixtures, not physical microphones or hosted production meetings.
Full suites: 739 desktop and 441 development backend tests passed. Application
lint, tracked-secret scans and whitespace checks passed; no hosted acceptance claimed.

## Required owner action before hosted acceptance

Supabase → **Aedrova Staging** (`scvmvqlzcqhwrrsiahpj`) → SQL Editor → New query:
run `supabase/migrations/202610110002_meeting_wrapup.sql` from this repository once.
It requires the existing meeting-context/speech-review migrations from the staging
baseline. Do not run the test SQL or a full schema reset, and do not install it in
the production Aedrova project yet. Reply success or the SQL error; never send keys.

Then the agent must deploy the matching staging backend and launch the matching
native source/build, retaining the existing meeting-context capability gate.
Validate actual owner/admin end-for-everyone and final-leave flows, another-member
still-present behavior, explicit confirmation/corrections and consent withdrawal.
The hosted automatic prompt is blocked until the migration and matching deployment
are installed. No claim of real speech-provider or two-Mac acceptance is made.
