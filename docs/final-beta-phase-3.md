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


## October 11 — wrap-up staging migration and deployment verified

Owner reported success running the new wrap-up migration in Aedrova Staging.
Read-only public PostgREST probes resolve both `meeting_wrapup_status` and
`confirm_meeting_transcript`, returning 42501 permission denial to unauthenticated
callers rather than missing-function errors. This confirms function installation
and anonymous execution denial, not authenticated hosted behavior.

Manually deployed backend commit `1149e72` on existing free service
`srv-db58sn8473hc73a9n3qg`; Render deploy `dep-db65s4h42hec73b13mp0` visibly succeeded.
`/health/ready` returns 200 ready. Matching native source commit `31e2ec8` launched
through the isolated staging public profile. No production deployment or credentials
changed, no new paid service, no automatic recording or capability activation.

`/health/meetings` returns 503 unavailable and the new wrap-up endpoint returns the
configured meeting-text-disabled denial (403). Existing staging meetings, context,
and speech capability gates remain off. Hosted two-account/end-of-meeting/edit/
Confirm/withdrawal acceptance is therefore still blocked by the separately deferred
meeting API/guard/LiveKit and server speech activation requirements. Owner's SQL
step is complete; no further SQL is requested now. Paid hosting, provider costs and
physical two-Mac testing remain owner release-preparation actions as already deferred;
do not enable these gates just to make a smoke test pass. Phase 2 remains open.
Evidence: `work/meeting-wrapup/staging-deployed.png`.

## October 11 — transcription activation brought forward

Owner explicitly requested complete transcription activation. The restricted staging
backend lacked EXECUTE on the two speech functions because its role was created
after the migrations. Owner ran the narrow staging-only grants; both privileges
and the prepared configuration/database preflight now pass. No table grants added.

Backend `ebd9f25` adds a speech/database preflight and permits the existing bounded
Free plan with speech alone, retaining shared workspace/funder budgets and server
limits. An ignored, private staging activation profile is prepared. Matching native
source supports `scripts/run_staging.py --config work/staging/public-config.json
--meeting-context`; frozen public builds and production configuration remain gated.
Full suites passed: 743 native tests and 444 development backend tests. OpenAI
whisper-1 metadata returned 200; real audio/provider capture has not been tested.

Required now: Render → aedrova-beta-staging → Compute → Save the selected $7/month
plan personally. This starts a recurring charge. A separate $7/month meeting guard
is prepared in the backend's deploy/render-beta-meeting-guard.yaml, making base
hosting about $14/month before provider usage/taxes. No charge submitted by agent.
Then approve transfer of the existing LiveKit credentials and OpenAI key to that
staging API, deploy both services, explicitly activate the staging workspace's
limited Free plan, and validate consent/capture/edit/Confirm/withdrawal with two
accounts and physical devices. Hosted transcription is not complete until those
checks pass. Production stays unchanged; Stripe remains deferred until release.

Detailed handoff: ../Aedrova_site/docs/transcription-staging-activation.md.
Homepage Bud placements merged through website PR #8; publication checked separately.
