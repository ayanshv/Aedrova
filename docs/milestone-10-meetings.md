# Milestone 10 — remaining acceptance deferred

Current status — October 2, 2026: implemented local calls/devices/sharing and one-Mac
two-account tests are preserved. The owner deferred shared hosting, second-Mac physical
acceptance, transcription and agent meeting context to M12. See `milestones.md`.
M10 is not fully accepted. The original foundation notes below are historical; later
sections record subsequent call implementation. No further M10 work is authorized by
the current visual-polish request.

## Original foundation report

The owner approved M10 on October 1, 2026. Custom-domain purchase remains deferred to M11.
This delivery is the access/consent foundation and the real transport acceptance harness.
It is **not a completed conferencing feature**. The dashboard still correctly describes
meetings as forthcoming. No camera/microphone/screen capture, recording, paid transcription
or public deployment was performed.

## Implemented

- Channel-scoped meetings and presence with PostgreSQL RLS; one open meeting per channel.
- A member can start a meeting; its host or workspace owner/admin can end it.
- Joining starts with transcription and AI reuse off. Participants can change only their
  own grants; AI reuse cannot be granted without transcription. Heartbeats cannot revive
  expired presence. Rejoins reset consent. Presence expires after 60 seconds.
- A revision-bound capture permit checks the live media roster against the server roster.
  Late join, departure, expiry, revocation or changed consent invalidates unfinished chunks.
  Audio transcription and AI context are separate; no recording/video grant is inferred.
- Server-only LiveKit credentials and disabled-by-default `/api/meetings/join`. User-token
  RPC enforces channel RLS before issuing five-minute, room-specific media credentials.
  Grants exclude room administration/recording and client data messages. Desktop receipt
  checks room/account/channel scope and expiry and hides credentials from repr.
- `scripts/check_meeting_transport.py`: actual two-peer SDK transport with generated
  microphone, camera and screen-share tracks, bidirectional reception and Qt image rendering.
  It cleans up its test room. No physical devices or model requests are involved.

## Acceptance and remaining work

Embedded PostgreSQL tests cover unauthorized/anonymous reads and joins, direct-write denial,
start deduplication, default consent, late joining, individual revocation, leaving, heartbeat
expiry rules and ending. Python tests cover room credential scope and capture barriers.
The transport harness exits with a sanitized setup-needed message without credentials.
Actual cloud transport acceptance remains unrun, rather than passed.

Before selecting the final desktop media integration, pass the two-participant spike required
by architecture.md: camera/microphone capture, Qt rendering, native speaker playback and echo
handling, screen-share permission/stop, real TURN connectivity and reconnect behavior.
Then implement the native themed prejoin/call UI, device selection, mute/video/share/leave,
visible participants and consent controls, account/channel switch cleanup and graceful errors.

Five-minute token expiry alone **does not disconnect an existing participant**. Active
membership/lease revocation must remove the participant through LiveKit's server API, including
backend restart/failure behavior, before enabling the endpoint. Current meeting credentials
must not be enabled in production. Set AEDROVA_MEETINGS_ENABLED=false until this is verified.

After media acceptance, implement consented transcription with bounded in-memory audio,
server-controlled provider credentials/costs, live-roster barriers and no capture when any
participant has not opted in. Persist bounded, attributed transcript segments with channel
ACLs, withdrawal/deletion behavior and revision counters. Wire eligible segments into agent
retrieval with citations and distinguish transcript discussion from confirmed team decisions.
Screen-share/video interpretation is separate from audio transcription and is not implied.

## Owner actions required next

1. Create a development project at https://cloud.livekit.io/ . LiveKit Cloud provides its own
   secure media URL; buying an Aedrova domain is unnecessary for this test.
2. In the project's settings, find its project URL and API credentials. Use a test project,
   not a production project's keys. Do not send its API secret in chat.
3. Copy `.env.meetings.example` to `.env.meetings` in this desktop repository, then fill
   `AEDROVA_LIVEKIT_URL`, `AEDROVA_LIVEKIT_API_KEY` and `AEDROVA_LIVEKIT_API_SECRET` locally.
   Leave `AEDROVA_MEETINGS_ENABLED=false`. Protect it with `chmod 600 .env.meetings`.
   `.env.meetings` is gitignored. These credentials are for the backend and development probe,
   never the customer's installed app or website frontend.
4. In Supabase → SQL Editor, run `supabase/migrations/202610010001_meetings.sql` after the
   existing migrations. This creates meeting access/consent tables; it does not record media.
5. Reply that the local test configuration and SQL are ready. We can then run:
   `uv run --env-file .env.meetings --extra spikes python scripts/check_meeting_transport.py`.
   This test uses cloud media infrastructure and may count against its quota; it makes no
   paid AI request. A real two-device hardware/network check follows the synthetic test.

The Cloud project/configuration blocks live media acceptance. The SQL blocks hosted meeting
API testing, but not the standalone synthetic transport probe. There is no new Google OAuth
redirect or custom-domain action required for this development stage. Before deployment, put
LiveKit credentials in the server's secret store and provision media usage/billing explicitly.

References: https://docs.livekit.io/reference/python/livekit/rtc/index.html and
https://docs.livekit.io/reference/python/livekit/rtc/platform_audio.html . The candidate Python
SDK is pinned at 1.1.20 and server API at 1.1.0. Local imports/buffer tests do not prove calls.

## Verification for this foundation

316 desktop Python tests and 86 website/backend tests passed. Ruff passes in both
repositories. All embedded PostgreSQL migration/RLS suites, including meetings, pass.
The website suite reports one existing Starlette/httpx deprecation warning.
The real transport harness correctly reports missing configuration and exits before
connecting; this is a blocked live check, not a passed media acceptance result.

### Configured-project check — October 1

The owner configured all three local LiveKit values. Preflight confirms they are
present, the URL uses wss and a LiveKit Cloud media hostname, and meetings remain
disabled. The .env.meetings file is gitignored and its mode was tightened to 0600.
LiveKit room setup and a separate read-only room-list check both returned HTTP 401.
The local/server clock comparison showed no skew. No room or physical device capture
was started. The owner must check the URL, API key and paired secret against one
project before the live test can continue. The SQL application remains unconfirmed.

The probe now skips deleting a room that was never created, preserving the original
authentication failure, and emits a credential-safe authentication diagnostic.
All 25 focused meeting tests and the scoped lint check pass after this refinement.

### Corrected credentials and live synthetic transport — October 1

The owner corrected the API secret and confirmed applying the meeting SQL in Supabase
(the owner named the editor snippet Meetings). The original hosted SQL acceptance
remains distinct from that confirmation; the live transport probe uses its own temporary
rooms and does not exercise Supabase authorization.

The standard two-peer cloud transport probe and a second run forcing TURN relay both
passed using LiveKit Python 1.1.20. Each peer received at least 20 nonempty audio frames,
20 camera frames and 5 static screen-share frames. The relay run also checks non-silent
audio. Received video is converted to Qt images and checked against the generated
source's RGB color with codec tolerance. The static screen-share threshold is lower
than camera video because the received static share sent fewer frames in the initial
probe; that was a probe assumption failure, not a rejected credential.

Reports: work/meeting-transport.json and work/meeting-transport-relay.json (no credentials).
The probe deletes its temporary room after disconnecting. Stale success reports are
removed at the start of each normal/relay run. Physical devices, echo cancellation,
network-loss reconnection and transcription remain untested. There are two SDK peers
on this computer, not two human-operated Macs. This passes transport and relay only;
it does not satisfy the architecture's complete physical-device gate. Keep meetings
disabled until the remaining M10 acceptance is implemented and verified.

All 25 focused meeting tests, scoped Ruff and the baseline release secret check pass.
The local credentials no longer need correction. Mac device permission prompts will
require explicit user action when the physical capture test is ready.

### Task 1 — native device setup — October 1

The Meetings page now opens a themed local setup dialog with camera and screen
previews, microphone level meter, device selectors, and a short generated speaker
tone. Opening the dialog starts no capture. Explicit checks request OS permission
as needed. Device changes, Stop all, closing the dialog, signing out, and quitting
stop active checks; late permission/frame callbacks cannot restart a closed check.
There is no recording, upload, transcription, or meeting join in this task.

The packaged app now declares camera/microphone usage descriptions. Developer ID
release entitlements include camera/audio input for hardened runtime. Editing the
bundle plist re-signs the outer app without re-signing the embedded vendor runtime.
Light/dark screenshots were checked locally using fake device inventory. These UI
and lifecycle tests do not establish physical-device or echo-cancellation acceptance.

Owner action now: open the rebuilt dist/Aedrova.app, enter Meetings → Check meeting
devices, and explicitly run camera, microphone, speaker, and screen checks. Approve
macOS prompts only for the checks you choose. If screen preview is denied, enable
Aedrova in System Settings → Privacy & Security → Screen & System Audio Recording
(the wording varies by macOS version), then restart the app. Camera/Microphone are
separate panels in Privacy & Security. Confirm the camera/screen preview appears,
the meter moves when speaking, the tone is audible, and closing setup stops capture.
Credentials and SQL do not need to be entered again. This owner hardware check
blocks physical-device acceptance, not the completed local implementation/tests.

Next task, subject to owner permission: validate the real-device media path and
connect channel calls to LiveKit with participant tiles, mute/video/share controls,
reconnection and active access revocation. Consent-based transcription/AI context
and full two-device acceptance follow in separately approved tasks. Meetings remain
disabled until the complete media/security acceptance passes.

Platform references:
https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.device.audio-input
https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.security.device.camera

Task 1 final verification: all 343 desktop tests pass (24 device-check tests),
repository Ruff passes, baseline release secret checks pass, and the rebuilt
ad-hoc Mac application passes strict codesign verification. The rebuilt app was
opened and shows Google sign-in; the owner must sign in to reach Meetings.
This development build is not a notarized public release.

Signed-in routing correction: the connected dashboard's generic placeholder branch
was masking the new Meetings page. Both connected and local workspaces now use the
meeting setup page. A regression test opens device setup from the signed-in Meetings
tab, checks tab preservation across rebuilds, verifies capture remains off, and checks
that sign-out closes setup. Focused connected/device tests: 30 passed; Ruff passes.
The app has been rebuilt and restarted; sign in again to reach the corrected page.

### Task 2 — candidate native channel calls — October 1

Implemented a Qt call window and dedicated asyncio RTC worker: joining existing
channel calls (including guests) or starting one, participant camera/screen tiles,
explicit microphone/camera/share controls, leave, host/admin end, reconnect state,
device pause on reconnect, and logout/close cleanup. Audio uses LiveKit's native
PlatformAudio ADM with AEC/NS/AGC configured; camera/screen remain Qt captures.
Default system audio devices are used. Configuring AEC is not proof that physical
speaker echo has passed. The architecture's physical acceptance gate is still open;
this remains the candidate integration, not an accepted production call client.

Frames use bounded latest-frame mailboxes, fixed 640×360 outgoing RGBA letterboxing,
and limited remote tile/stream counts. Closing cancels the call immediately, closes
the native microphone even while an HTTP heartbeat is awaiting a response, stops
Qt capture, and releases media/event-handler resources. A live probe exposed native
FFI destructor warnings from retained event/stream references; cleanup now drops
those references and the repeated probe exits cleanly.

The Python backend now lists/starts/joins/pulses/leaves/ends calls with Supabase
channel/host authorization. Durable encrypted server leases require LiveKit Cloud
and a persistent server encryption key. Every sweep rechecks accessible meeting
membership/roster with the user's token; lease expiry, membership loss, ended meetings
and failed auth checks request participant removal with an explicit Cloud token
revocation cutoff. Failed removals remain pending for retry. New joins fail closed
when the guard is unhealthy. A separate supervised guard is required for release so
HTTP-process downtime cannot leave only the embedded guard responsible for revocation.
Polling/removal are not instantaneous and infrastructure outages can delay removal.

Verification: 356 desktop tests and 96 backend tests pass. Ruff and baseline release
secret checks pass. Native call-window screenshots were inspected in dark/light themes.
`scripts/check_meeting_call.py` exercises two actual native call workers against Cloud
with generated camera/screen frames and fake authenticated identities. Both receive
video, a revoked participant is forcibly disconnected, and their cached token cannot
rejoin. Report `work/meeting-call-check.json`; no hardware is accessed, audio ADM is
stubbed, and hosted Supabase authorization is NOT tested by this probe. Prior real
synthetic audio and forced TURN probes remain separate evidence.

Owner action: sign in to the rebuilt app, open Meetings → Check meeting devices,
explicitly test each device, approve macOS prompts, and report which checks work.
The developer prepared a stable private `.env.meeting-server` in Aedrova_site; no new
keys or SQL are required from the owner now. Keep meetings disabled until device
preflight is confirmed; next continue this task's live two-account call validation.
Full two-Mac audio/echo/reconnect and hosted access-removal validation are still pending.
Transcription/AI context are not active and require the next task's permission after
call validation. M10 is not complete.

Cloud removal reference:
https://docs.livekit.io/reference/other/roomservice-api/

### Familiar call controls and screen-preview follow-up — October 1

The call window now offers gallery/speaker views, automatic screen-share focus,
participant and device panels, and an icon-and-label toolbar that wraps at small
window sizes. Calls stay open when minimized; explicit close/logout releases devices.
Both meeting dialogs explicitly inherit the workspace's semantic theme palette.

The owner confirmed physical camera, microphone meter, and speaker tone. Screen
preview still failed after a Settings toggle/restart in the ad-hoc build. Investigation
found a cdhash-only designated signing requirement. A valid local Apple Development
certificate is now used for this preview via AEDROVA_PREVIEW_SIGNING_IDENTITY; the
preview bundle identifier remains com.aedrova.desktop.preview. Its new requirement is
certificate-bound, stable across rebuilds. Public release still requires Developer ID,
HTTPS, notarization and release acceptance. No certificate or secret is bundled as data.
Permission denial and granted-but-no-frame failures now have different recovery
messages. Camera/screen activate only after a valid frame and have an 8-second
first-frame timeout. No permission checks are bypassed.

Owner action if screen access remains denied: remove the obsolete Aedrova entry in
System Settings → Privacy & Security → Screen & System Audio Recording, add
/Users/ayanshvarma/Documents/Aedrova/dist/Aedrova.app, enable it, then fully quit and
reopen. This is a one-time development signing transition, not a request to disable
macOS security. Actual preview success remains unconfirmed until retried.

The local API on port 8090 and independent guard are enabled only through process
overrides for approved acceptance testing. The packaged public configuration points
to http://127.0.0.1:8090. Private setup files and public release switches remain disabled.
Two-account physical calls, echo, reconnection and hosted access removal are pending.
No transcription or AI meeting context has been enabled. Do not declare M10 complete.

Apple confirmation of the development signing issue:
https://developer.apple.com/forums/thread/819406

Follow-up validation: 367 desktop tests and 103 backend tests pass, with Ruff and
packaged signature verification passing. The first packaged hosted call reached
LiveKit but failed during the immediate heartbeat. Supabase void RPCs return 204;
the shared backend adapter incorrectly required JSON. It now accepts successful
204 responses while still rejecting empty/malformed 200 and unsuccessful statuses.
Seven transport regression cases cover this distinction. Failure phase/status now
survives cleanup and never includes exception payloads. Local API restarted with fix.
The packaged signed-in hosted call now connects successfully after the 204 fix,
with devices off and the real participant panel visible. This is one-account evidence;
it does not substitute for two-Mac hardware acceptance or screen-preview confirmation.
The fixed packaged call stayed connected across repeated heartbeats; the host End
control transitioned to Leaving, and Leave returned to the dashboard. No physical
media was sent in this single-account test. Device setup is open with captures off
for the owner's remaining screen-permission retry. Continue using
AEDROVA_PREVIEW_SIGNING_IDENTITY with the installed Apple Development certificate
for future preview rebuilds; reverting to ad-hoc signing recreates the identity change.

### Camera framing and control clarity — October 1

Owner confirms camera, microphone, speakers and screen preview all work after the
signing transition. Camera frames now use centered aspect-preserving fill at 640×360,
and camera tiles/speaker stage fill their rounded bounds without side bars. This crops
outer edges rather than stretching the image. Screen sharing retains fit/letterboxing
so no shared content is cropped. Participant names appear over video in a subtle pill.
Toolbar labels report current state: Muted/Unmuted and Camera off/Camera on; tooltips
explain the action. Disabled-device icons are crossed out. Devices remain explicitly
enabled by the user. Regression cases verify camera fill versus full-screen preservation,
current-state labels/tooltips, tile modes, and reconnect reset. Two-device call acceptance
and consented transcription/AI context remain pending; no new SQL or keys required.
Camera/control refinement verification: 370 full desktop tests passed; 50 focused
meeting/device tests passed after the final paint changes. Ruff passes. Light/dark
call renders were inspected with a synthetic portrait-format frame (no hardware
capture); the packaged app uses the same stable Apple Development identity.


### Hosted two-account acceptance — October 1

`check_hosted_meeting.py` used two real Google PKCE sessions (owner and approved school
account), only user-scoped JWTs, the actual Supabase schema and running API/guard. Each
run created an isolated Meeting validation workspace. Neither account's existing
workspaces were changed. Calls were ended and the secondary membership removed; empty
test workspaces remain owned by the primary account for inspection (not permanently
purged). No email was sent and no physical capture, transcription or AI call was made
by this meeting check. Credentials stayed in memory and were not written to reports.

Final stronger run passed: nonmember/private-channel denial, invitation acceptance,
372/338 valid generated camera frames and 82/88 screen frames across the two peers,
heartbeats, roster update on leave, fresh authorized rejoin after revocation grace,
server-forced member removal (PARTICIPANT_REMOVED) with client heartbeats paused and
drained, new/cached token rejection and host end. Revocation measured 4.4 seconds in
this run, not a guaranteed SLA. Three nonmatching startup frames were excluded from
valid-frame counts. Report: work/hosted-meeting-check.json. Two physical devices,
bidirectional hardware audio, echo and network-loss reconnection remain untested.

Rapid consecutive Google logins exposed TCP TIME_WAIT listener reuse. Closed callback
ports can now be reused; active listeners remain exclusive. Random callback path,
Host validation and PKCE remain required. Regression tests verify both behaviors.

The meeting-service origin had inadvertently activated included AI for @agent builds.
Development packages now explicitly record ai_access_mode=local independently of the
meeting origin. Public paid packages require included mode; frozen apps ignore ambient
mode overrides, and included failures never select local provider credentials. The
existing personal Codex login passed a real isolated file-creation check. Included API
access still requires server-only commercial provider keys/models/billing configuration.
Verification: 374 desktop tests, 103 backend tests, Ruff, baseline secret checks and
packaged signature verification. No new SQL is required. See docs/milestones.md for
sequential next tasks and approval gates.

### M10C deployment preparation — October 1

Owner authorized completing M10, but confirms no hosting account or second Mac is
currently available. Implemented independent production guard readiness persisted in
the private PostgreSQL ledger. Production API processes do not start an embedded guard;
fresh external health is required to join. Failed sweeps/shutdown mark it unhealthy,
stopped guard health expires in 10 seconds, future timestamps and DB errors fail closed.
Lease reservation is a single conditional UPSERT; duplicate and grace-period joins
cannot overwrite an active connection. Health endpoints distinguish API liveness from
call readiness. Container/startup/preflight instructions are in the website repository's
docs/meeting-hosting.md; image build/deployment are unrun because Docker/hosting are absent.
No secrets were transmitted or bundled. No new Supabase SQL or desktop rebuild needed.

Pending: hosted PostgreSQL concurrent/restart acceptance, HTTPS/proxy operations and
two-Mac physical audio/echo/screen/reconnection. Then consented transcription and
meeting-to-agent retrieval. Existing consent primitives are not a working transcriber.
Do not mark M10 complete or start another milestone without the owner's approval.

Verification for M10C preparation: 374 desktop tests and 116 backend tests passed,
both repository Ruff checks and baseline release secret checks passed, every embedded
Supabase migration/RLS suite passed, and embedded PostgreSQL validated the private
ledger/meeting schemas plus conditional lease SQL (duplicate, grace, authorized rejoin).
These checks do not prove networked PostgreSQL concurrency, a built Docker image,
deployed TLS/monitor processes or physical two-Mac acceptance.
