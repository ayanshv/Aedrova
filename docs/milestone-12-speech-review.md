# M12D — speech capture and reviewed meeting evidence

Implemented locally on October 3, 2026. M13 has not started. No hosted migration,
provider request, public deployment, paid resource or secret configuration was performed.
Owner setup and live acceptance remain in M14 as requested.

## What changed

When the staging server advertises speech capability, each participant can explicitly
start transcription of their own unmuted microphone. Meeting privacy separately controls
30-day shared text storage and agent reuse. Every present participant must approve
storage; everyone must separately approve AI reuse. Join/rejoin requires fresh choices.
The call displays capture, processing, paused and stopped states. Capture never starts
from consent alone. Muting, leaving, reconnecting or local privacy actions stop capture.

The native LiveKit local microphone stream is resampled to mono 16 kHz PCM. In-memory
buffers hold at most ten seconds and are discarded across consent/roster changes.
Incomplete final chunks are discarded. One request at a time is sent, with no backlog
or automatic retry. Capture pauses during provider processing, so transcripts can have
gaps and are not a complete recording. Only each participant's microphone is processed;
there is no camera, shared-screen, remote-party or system-audio transcription. Account
attribution identifies the sender, not a verified voice or biometric speaker.

The server validates and cleans WAV data, reserves authorization and allowance before
provider access, then checks consent/roster/presence again before saving results. Speech
uses the documented OpenAI multipart transcription endpoint with `whisper-1` and JSON
responses: [official speech guide](https://developers.openai.com/api/docs/guides/speech-to-text).
Keys remain server-only. Raw audio is not written to Aedrova disk or database; bytes live
in process memory and provider handling applies. No memory zeroization or instant recall
of already-sent provider requests is promised.

Provider text is saved with server-only `provider_speech` provenance. Authenticated users
cannot forge speech writes through the text RPC or direct table writes. Durable UUID/digest
reservations prevent duplicate provider calls after a completed save; failed/pending IDs
cannot be reused. Bounds: 1–10 seconds/request, 2,000 transcript characters, 16 KiB provider
response, one active request/account, four requests/API process, 12 attempts/minute/account,
10,000 segments/meeting, and one combined audio hour/workspace in a rolling 24-hour window.
Reserved failed attempts count toward allowance. These are conservative staging limits,
not approved paid-plan pricing or measured speech cost. Provider account spend limits
and cost approval are still required before launch.

Review transcript is available during a call and through Meetings history after calls
in a context-enabled internal build. It includes paging, source citations/original text,
corrections, explicit confirmed decisions, refresh, withdrawal and deletion confirmation.
Only the speaker or a workspace owner/admin may save a review. Expected-version checks
prevent stale overwrites. Reads retain channel RLS, expiry and current account scope.
Errors/session closure clear stale displayed text. Review changes keep the original text.

Unreviewed speech never enters agent context. Reviewed corrections, reviewer attribution,
confirmed-decision status and meeting citations enter existing permission-scoped retrieval.
AI consent is also required; editing cannot resurrect withdrawn permission. Withdrawal
invalidates meeting-wide AI evidence; deletion removes shared segments. Context is
revalidated before gathering completes and revision triggers detect subsequent edits.
Already-exported snapshots, provider work and backup copies cannot be instantly recalled.
Leaving/ending stops new speech; earlier eligible text remains until withdrawal/expiry.

## Required owner actions — none now; M14 only

1. In Supabase SQL Editor, after existing migrations, apply
   `supabase/migrations/202610030001_meeting_context.sql`, then
   `supabase/migrations/202610030002_meeting_speech_review.sql`. Never apply test/bootstrap
   SQL. The second migration grants execute on the two speech functions to the existing
   restricted `aedrova_website` role if present. If the role is created afterward, explicitly
   grant execute on `public.reserve_meeting_speech(uuid,uuid,uuid,bigint,uuid[],text,integer,integer)`
   and `public.finish_meeting_speech(uuid,uuid,text)` to that role; no table privileges or
   privileged Supabase service-role key are needed for speech.
2. Finish the approved always-on meeting API/guard setup from website
   `docs/render-meetings.md`; use its restricted private Supabase database connection.
   Keep public waitlist capabilities disabled. Existing meeting credentials remain server-only.
3. Review OpenAI speech data handling, obtain an API key, approve costs and configure
   provider spend limits. Set `AEDROVA_SPEECH_KEY` privately in the meeting API secret store,
   not the desktop, repository or chat. A Codex or Claude subscription is not this API key.
4. On staging only, enable `AEDROVA_MEETING_CONTEXT_ENABLED=true` and then
   `AEDROVA_SPEECH_ENABLED=true`. Rebuild the internal desktop with the bundled
   `meeting_context_enabled` flag for historical review/agent reuse. The guard needs
   neither the speech flag nor the speech key. Example: website `deploy/meetings.env.example`.
5. Set privileged daily maintenance for `select aedrova_private.expire_meeting_text()`
   using approved Supabase scheduling. Expired segments are immediately hidden; this job
   physically removes them and removes speech reservation metadata older than 30 days.
6. Validate real two-account consent, private-channel isolation, microphone attribution,
   correction/citations, quota/failures, withdrawal/deletion and queued/running build behavior
   against staging. Confirm physical capture on two Macs when available. No live transcription
   or hosted billing/cost acceptance is claimed by local tests. Public activation requires
   successful release/safety checks and owner authorization.

## Local verification

All 438 desktop and 213 website/backend tests pass. Scoped Ruff, compilation and
whitespace checks pass. The website suite retains its existing Starlette/httpx deprecation
warning. All 21 embedded PostgreSQL migration/test scripts pass, including actual SQL
reservation, replay, provenance grants, review versions, consent changes during processing,
post-call review/deletion, allowance exhaustion and expiry. Native LiveKit local-track
capture was exercised with synthetic PCM without hardware or cloud access. Capture-buffer
and loop tests prove incomplete/revision-crossing chunks are discarded. Provider fixtures
cover malformed audio, bounded responses, denial, timeout, empty speech and retry behavior.
Qt renders of call/privacy/review controls were inspected in both themes at narrower widths.
This is local acceptance, not a hosted end-to-end provider or two-Mac physical test.

Next: ask permission for M13's final safety/security audit. M13B explains the entire
codebase; M14 contains deferred owner setup, live acceptance and release activation.
