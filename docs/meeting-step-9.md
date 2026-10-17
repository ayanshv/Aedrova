# Step 9 — advanced meeting presentation, first batch

October 16, 2026. Owner approved Step 9 after saving previous outstanding work as
launch gates. **Partial delivery, not completion of the full advanced feature list.**
No launch gate is closed by this batch; no paid service or account setup is started.

## Implemented in existing native architecture

- **Application-window sharing:** refresh the Devices share-target list and choose
  a display or application window. Actual Qt QWindowCapture/session path for a
  selected valid QCapturableWindow, retaining explicit OS permission and capture
  watchdogs. Vanished windows fail safely. Existing display sharing remains.
  Native window capture availability varies by OS/backend; physical Mac/Windows
  acceptance remains required. No browser-tab-only capture or system audio claim.
- **Pause/resume sharing:** pause stops the capture device, clears pending/local
  frames and drawings, and unpublishes the shared video track. Resume stays disabled
  until the off acknowledgement, then requests capture again. A late publish
  acknowledgement cannot undo pause. Camera/microphone call state is unaffected.
  Changing targets stops sharing. It is not a frozen continuing capture session.
- **Sharer's freehand annotations:** enabled explicitly in Presentation. Draw on
  the large preview of your own active shared screen. Blue/coral/gold strokes are
  composited into outgoing pixels and the local preview; recipients see them in
  the shared video. Clear drawings updates the outgoing view. Points respect
  letterboxing; maximum 64 strokes, 2,048 points per stroke; stop/close clears
  drawings and the base image. No remote participant drawing, text/highlighter
  tools, remote desktop access or whiteboard sync is inferred.
- **Video view controls:** pin/unpin individual video or screen tiles, independent
  of active speaker updates; show/hide the self camera tile; mirror only the local
  camera preview (outgoing video remains unmirrored).
- **Receive participant video:** unsubscribes from remote video publications,
  cancels video streams, clears the mailbox/UI and ignores late video frames.
  Remote audio playback and outgoing camera/share remain independent. Newly
  published video respects the setting; enabling it resubscribes. No meeting-wide
  moderation or participant camera control is claimed.
- **Camera treatment:** natural/monochrome and bounded 0–25% soft-light adjustment
  applied to actual outgoing camera frames. Off by default. These are basic color
  and light adjustments, not face retouching, portrait relighting or backgrounds.
- **Compact UI:** separate scrollable Presentation settings with fixed Done action;
  device options scroll independently. Footer wraps; drawing uses a crosshair only
  on the sharer's own active preview. Sharing target text explicitly says audio
  is not included. Audio-call UI keeps video presentation controls hidden.

No database migration, backend route, model/speech invocation, RTC data publishing
permission, recording grant or architecture replacement was added. Source changes
are separate from deployed services and installed app binaries.

## Verification

- Focused native/Qt tests cover outgoing vs preview mirroring, image treatment,
  annotation pixels/clear/limits, letterbox mapping, pause acknowledgement races,
  pinning, hide/self view, video-only unsubscribe, queued-frame rejection, and
  window-capture session wiring/invalid windows. Native capture wiring uses spies;
  it does not establish physical screen capture on either OS.
- Extended the existing generated-media RTC probe and ran it against the existing
  configured test project: 107/106 camera frames and 20/20 screen frames received;
  incoming video disabled while outgoing continued; 109 frames received after
  resubscription. Forced removal and cached-token rejection still passed. Synthetic
  identities/local fixture database, not hosted Supabase RLS or physical devices.
  No hardware, recording, transcription or AI request was started. Temporary room
  removed. Evidence: ignored work/meeting-call-check.json.
- Light/dark wide/680px sharing and Presentation previews rendered. Inspected light
  compact sharing and dark Presentation. Fixed clipped copy by scrolling settings
  content with a fixed Done action. Ignored work/meeting-step-9/*.png.
- Final regression counts and Ruff/diff results are recorded in milestones.md.

## Retained advanced work — not implemented here

Virtual backgrounds/segmentation, portrait/appearance effects beyond basic treatment,
second-camera capture, shared computer audio/video optimization, browser-tab capture,
participant annotation permissions, remote control, collaborative whiteboards/docs,
breakout rooms, polls/quizzes/Q&A, advanced host moderation, translated captions/
language interpretation, telephony, external apps, RTMP/live broadcast, immersive/
dual-monitor support and vendor-specific Zoom Apps/Docs/Rooms integrations remain
open. Some require platform/provider support, explicit permissions and cost review.
All original requirements remain in meeting-features-owner-source-2026-10-16.txt and
release-baseline-2026-10-15.json. Current overlay: meeting-step-9-status.json.
No nonfunctional controls were added for these features.

## Owner actions / launch gates

**No new action is required now.** The owner's paid-hosting deferral remains in
force. Existing gates in meeting-launch-gates.md still block live acceptance/launch:
when ready, personally review/submit the always-on staging API and independent
meeting guard in Render (prepared approximately $7/month each, verify current
prices first), then deploy the matching staging backend/desktop candidate. Never
bypass the guard. Finally, use two devices/accounts and personally grant OS
camera/mic/screen permissions to test audio/video, app-window capture, pause/resume,
annotations, incoming-video controls, permission revocation, consent and review.
Mac/Windows clean-machine acceptance, signing/notarization and production promotion
remain separate. Do not claim this source push is a downloadable release.
