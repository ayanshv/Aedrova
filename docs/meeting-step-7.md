# Step 7 — core meeting repair

October 16, 2026. Owner approved this step with the complete attached feature list.
Core implementation delivered; physical two-device/hosted acceptance remains open.
No paid infrastructure, production promotion, installer or Apple-account changes.

## Requirements retained

The complete owner-supplied list is preserved verbatim in
[meeting-features-owner-source-2026-10-16.txt](meeting-features-owner-source-2026-10-16.txt).
All 14 categories and stable MTG requirement IDs remain in
[the full register](release-baseline-2026-10-15.json). Nothing was deleted from scope.
The status overlay meeting-step-7-status.json records this step without rewriting
that immutable baseline. This is core Step 7, not delivery of every advanced feature.

Step 8 covers communication, intelligence, consented transcription/review/history,
recording permissions and accessibility. Step 9 retains effects/backgrounds,
collaborative annotation/remote control/whiteboards/docs, second-camera/video-audio
sharing, breakout rooms, polls/quizzes/Q&A, advanced moderation, translation,
telephony, integrations, streaming/RTMP, immersive/dual-monitor experiences and
vendor-specific Zoom Apps/Docs/Rooms decisions. Availability, consent/security,
provider capabilities and costs must be checked before claiming those features.
Do not add nonfunctional buttons or describe all Zoom capabilities as implemented.

## Root causes and changes

- The native worker awaited each access-heartbeat HTTP call in its video pump.
  A slow response could freeze camera/screen publication for up to 20 seconds.
  Heartbeats now run independently. Failure/timeout still ends the call; cleanup
  cancels/gathers the task and clears queued images. Existing external access
  guard/lease checks remain required; no authorization bypass or extended lease.
- Added microphone/speaker choices using actual LiveKit ADM stable device IDs,
  not mismatched Qt device IDs or names. Selection is validated against current
  native inventory. Microphone changes stop/unpublish capture and require explicit
  unmute. Failed device selection reverts the UI; no silent capture restart.
- Added background-noise reduction while retaining echo cancellation and automatic
  gain control. Changing it mutes the microphone; failure restores the prior choice.
- Video meetings default to joining muted. The explicit audio-call flow retains its
  established behavior. Camera capture still requires the explicit video action
  and OS permission; manual meeting opening starts no capture/network.
- Added optional hold-Space-to-talk in Devices. Releasing Space, disabling the
  preference or deactivating the call window mutes/cancels pending microphone
  activation. Device pickers/text fields retain normal keyboard behavior.
- Device hot-plugging stops capture and refreshes camera/screen/audio choices.
- Curated setup/guard-unavailable responses no longer misdiagnose the user as
  signed out. Actual account denials still fail closed, arbitrary provider error
  bodies stay hidden, and rate-limit messages ask users to wait.
- Existing gallery/speaker layouts, participant list, camera selection, full-screen
  sharing, leave/end server checks, transcript consent and wrap-up are retained.

## Verification and boundaries

- Full desktop suite: **865 passed**. Final focused meeting suite: **82 passed**
  after the last connection-status copy adjustment. Ruff/diff checks pass.
- Live native worker: two generated camera/screen peers passed, with 108 camera
  frames per peer and 23/21 screen frames. Forced removal and rejection of the
  removed participant's cached token passed. Synthetic identities, not hosted RLS.
- Forced TURN relay: both peers received 20 generated audio, 20 camera and 5 screen
  frames; decoded frames rendered correctly in Qt. No camera/microphone/screen
  hardware was captured or recorded. No speech/model call or transcription started.
- Actual local ADM enumeration found two microphones and two speaker devices;
  recording/playout selection setters passed without starting capture/playback.
  This does not prove audible output, mic quality, echo cancellation or live
  Bluetooth switching during a call. These remain human hardware acceptance.
- Tests cover slow heartbeat without video stalls, access-loss cleanup, pending
  permission cancellation, device IDs/disappearance, noise setting recovery,
  default mute, push-to-talk release/focus loss, existing call controls and privacy.
- Light/dark and 1120/680-width UI previews rendered and visually inspected with
  fixture participants. Previews are not evidence of a real physical meeting.
- Local /health/meetings: 200. Hosted beta staging /health/meetings: 503 unavailable.
  Hosted meetings are deliberately disabled; they are not repaired by UI changes.
- No fresh two-account hosted RLS, two-device physical video/audio, echo, physical
  screen capture, network recovery, host-end or membership-revocation test performed
  in this batch. Controlled regressions and synthetic transport are separate proof.

Ignored evidence: work/meeting-step-7/*.png, device-selection.json,
work/meeting-call-check.json, work/meeting-transport-relay.json. Secrets stay in
existing ignored configuration; test JWTs are short-lived. Synthetic rooms removed.
No new provider account, permanent key, database migration or architecture rebuild.

## Owner actions — deferred hosting and final acceptance

No account action is needed to use the completed source/unit-test changes.
The prior paid-hosting deferral is preserved. When ready to unblock hosted calls:

1. In Render → aedrova-beta-staging → Compute, review an always-on plan and its
   current recurring charge. The owner must personally submit any paid upgrade.
   No upgrade was submitted here.
2. Prepare the existing staging API's LiveKit URL/key/paired secret privately and
   the independent guard using website deploy/render-beta-meeting-guard.yaml
   (Render → New → Blueprint → repository Aedrova-website → that Blueprint path).
   That file references only staging database/encryption/auth values. Keep
   production credentials out; do not substitute the older main/production setup.
   Private credential transfer to Render needs exact destination approval first;
   no secret should be pasted into chat. Review/submit the worker charge personally.
3. After the worker is healthy and exact staging setup is reviewed, enable staged
   meetings and verify /health/meetings returns 200. Preserve billing/release gates.
   The agent must verify this before issuing test-call access; never disable the
   guard to make a call appear healthy.
4. On two devices, use two approved staging accounts in the same disposable
   channel. Grant only requested camera/mic/screen permissions. Verify both-way
   speech/video, mute/camera toggles, selected devices, speaker echo/headphones,
   sharing/stop, leave/rejoin, host end, membership removal and network recovery.
   Report sound/image quality; generated peers cannot establish these results.

These gates block hosted/physical acceptance and public launch, not the completed
core source repair. Existing connector gates remain separately tracked in Step 6.
Ask before starting Step 8. Do not mark the entire 14-category list complete.
