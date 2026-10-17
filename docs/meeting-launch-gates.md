# Meeting launch gates

Saved October 16, 2026 at the owner's request. **All gates below are OPEN.**
Deferred to the pre-launch review; no hosting purchase, deployment or live testing
is requested now. Deferral does not mean acceptance, deletion of scope or permission
to advertise unfinished features. Step 8 remains partial and Step 9 has not started.

## LG-MTG-01 — Finish meeting functionality and freeze release scope

Owner: engineering; owner approves any release-scope reduction.

- Finish the outstanding Step 8 communication work: private/selected-recipient and
  meeting-only chat policy, in-call attachments/export, reactions, raise hands,
  nonverbal feedback, profile controls and invite/join details.
- Complete the promised meeting intelligence and recording work: summaries/action
  extraction, meeting questions, recording permissions and local/cloud recording.
  Do not interpret transcription consent as recording consent.
- Complete accessibility acceptance: manual captions/position controls as scoped,
  keyboard operation, focus order, text scaling and physical screen-reader checks.
- Resolve each retained Step 9 requirement against the approved release scope.
  All original requested features remain in meeting-features-owner-source-2026-10-16.txt
  and release-baseline-2026-10-15.json; current implementation status is in
  meeting-step-8-status.json. No blanket Zoom-parity claim.

Close only with working implementation and evidence for every advertised feature,
or an explicit owner-approved scope adjustment reflected in website/product copy.

## LG-MTG-02 — Reliable staging hosting and independent access guard

Owner action, deferred until ready:

1. In Render → aedrova-beta-staging → Compute, review and personally submit the
   prepared $7/month always-on API upgrade. Confirm the current displayed price
   before submitting; do not start a charge automatically.
2. Review/deploy the separate staging guard using
   Aedrova_site/deploy/render-beta-meeting-guard.yaml. Its prepared base plan is
   another $7/month: approximately $14/month combined, excluding provider usage
   and taxes; verify current prices at submission.
3. Configure missing private staging LiveKit values through the approved private
   settings workflow. Never paste secrets into chat or reuse production settings.

Engineering then deploys the matching backend/desktop candidate to staging and
verifies /health/meetings returns 200 with the independent guard healthy. Do not
bypass the guard or merely flip meeting feature flags. Step 8 adds no SQL migration.
These actions unlock hosted acceptance and block meeting launch until completed.

## LG-MTG-03 — Two-account physical meeting and access acceptance

Owner action, after LG-MTG-02:

Use two physical devices and two staging accounts. Personally grant operating-system
microphone/camera/screen permissions and participate in the listening checks.
Engineering records results for:

- Audio/video, mute, device selection, screen sharing, reconnection, host end,
  join/leave behavior and focus/fullscreen stability.
- Channel chat delivery/history/retry and denial for accounts outside the private
  channel/workspace; no cross-workspace leakage.
- Transcription only after current unanimous consent, explicit per-speaker start,
  captions/text sizing, and capture/display stopping on withdrawal or stale consent.
- Editable post-call review, Confirm, citation/attribution, separate AI reuse,
  version conflicts, withdrawal, deletion and retention behavior.
- Keyboard/screen-reader usability, readable light/dark layouts and no stale
  private content after sign-out or call closure.

Generated RTC/TURN traffic, fixture UI checks and unit tests do not close this gate.

## LG-MTG-04 — Production promotion and installer parity

After the prior gates pass, approve the exact candidate for production promotion.
Deploy the corresponding backend, rebuild and sign/notarize the Mac release and
produce/sign the Windows release as required by the release plan. Test clean
install/update/sign-in and the advertised meeting flows on both platforms before
publishing download links. Current source pushes are not installer acceptance.

## Evidence retained

Step 8 foundation: 872 desktop regression tests, followed by 73 final focused
meeting tests; 8 backend API tests passed. Light/dark Qt fixture previews inspected.
Chat/captions/privacy/review source delivered; no production deployment, installer
rebuild, paid upgrade or physical hosted meeting acceptance performed in that batch.
Detailed boundaries: meeting-step-7.md and meeting-step-8.md.

At the final go/no-go review, record candidate commits, environment, test evidence,
owner approval and closure date for each gate. No gate is closed by this document.
