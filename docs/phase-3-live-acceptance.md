# Phase 3 live acceptance — October 12, 2026

Environment: Aedrova Staging only, disposable `Beta isolation 1 eb8958` workspace.
No production changes, paid hosting, billing activation or meeting activation.

## Verified on the actual signed-in native client

- HTTPS staging `/health/ready` returns ready.
- Synthetic 90-byte text fixture uploads to private Storage, passes hosted verification,
  and appears as an attachment message. Composer confirms “Shared · verified securely.”
- The published attachment is still present after a new native session signs in.
- A text file falsely named PNG is rejected with a content/type mismatch explanation;
  no additional message appears.
- A 10 MiB + 1 byte text fixture is rejected with the 1 byte–10 MB explanation;
  no additional message appears.
- Actual default microphone exists and supports mono 16 kHz Int16. This checks device
  compatibility, not capture or speech accuracy.
- Initial plain-Python preview reached the enabled dictation service, but Qt rejected
  microphone permission: missing NSMicrophoneUsageDescription in the main bundle.

## Fix discovered during live testing

`run_staging.py` now uses a local, ad-hoc signed source app bundle on macOS, with a
stable staging-only identifier and camera/microphone usage descriptions. It imports
this checkout and virtualenv; it is not a distributable installer. No credentials
are copied into it. Windows/Linux keep the original launcher. The corrected preview
starts, is accessible to native automation, and signs in through the existing Google
session. Owner completed microphone consent and a real spoken test reached the editable draft.
Public packaging's microphone explanation also includes chat dictation. Native QAudio
enum callback and background Qt shutdown errors found in logs were fixed afterward.

## Still awaiting acceptance

Real speech-to-editable-draft succeeded: owner said “Aedrova, test test test”; provider
returned “I drove a... test, test, test...”. Editing was verified without sending.
A later unattended recording failed provider transcription; no success claimed for it.
Owner then requested voice recordings instead. Composer now uses local record/preview/send
with no transcription. Real voice publication/playback acceptance is still pending;
see voice-messages.md. Staging voice SQL has been run by owner.

Live private-channel/thread publication, in-flight upload cancellation, second-account
attachment isolation, allowance denial and expired-session cases still require live
acceptance. Automated regressions do not replace those checks. Bud configuration,
Finish later → highlight tour and real model style behavior need live acceptance too.
Meeting hosting/two-device transcription remains deferred separately; Phase 3 is open.

Evidence: ignored `work/live-chat-media/` screenshots (upload-result, malformed-result,
oversized-result, dictation-start). Temporary root fixture copies removed; one benign
published staging attachment remains for persistence verification. No personal files
were uploaded.

Checks this turn: 50 focused Bud/dictation tests; 14 file-policy/dictation tests; 22
identity tests (overlapping suites, not summed). Scoped lint, source-bundle launch,
staging configuration validation, secret scan and diff whitespace checks pass.

Full native pre-voice suite passed: 762 tests. Post-change suites recorded below.

Voice messages: owner captured/previewed a real 10-second recording; native publication
passed hosted verification and persisted after restart. Owner reported distortion: quality
acceptance failed. Native-format conversion/continuous resampling and five-minute limit are
implemented and under listening recheck. Safe image/text previews also implemented. No
production activation. Earlier 767-native/463-backend pass predates this final quality pass.

Recheck: owner sent the native-format eight-second clip and reports distortion mostly
gone. Publication/persistence passed after restarting the staging source app. Residual
sound quality remains open. Text snippet visibly rendered after adding preview scheduling
on server snapshots; synthetic PNG upload passed hosted verification. Earlier “pending”
voice references above describe the original test state, superseded by these results.

Image thumbnail visibly rendered after a fresh Google-authenticated source launch.
Evidence: `work/live-chat-media/voice-and-image-preview.png` (synthetic blue PNG,
no personal information). Actual revised voice card and original voice card are
also present. Owner listening describes local preview; automated inspection does
not establish remaining acoustic quality or clean-machine playback acceptance.

## October 12 — continued hosted media acceptance

Live normal Google OAuth against staging now verifies synthetic text publication in a
private channel's thread, correct parent ID, authenticated download byte integrity,
cancellation after reservation and cancellation after Storage upload, and denial
through the native media boundary after sign-out. Test messages were unsent and
probe workspaces archived. No personal files, AI calls or production changes.

The cancellation run found a real missing client allowlist entry for
`abandon_attachment`; the SQL existed but the client rejected the operation before
calling it. Added the allowed authenticated operation and a regression through the
actual client RPC wrapper. Both cancellation boundaries then passed live.

Native Bud setup loaded, appearance/name/back navigation, personality text input,
connector gallery and Finish later returning to chat were inspected. Accessibility
selection changed the artwork but left the specialty at Builder because macOS toggles
checkable buttons without their click signal. Changed the handler to the checked-state
signal; tests cover all six appearances and resulting real specialties. This source
fix requires the next staging source launch for its live recheck. Full native suite:
779 passed. Scoped Ruff, secret scan and whitespace checks pass. One existing
system-theme fallback test was corrected for Retina pixel scaling.

Remaining required-now owner action: Safari's Google account chooser → sign in with
SECOND staging test account, distinct from ayanshvarma0603@gmail.com. The prepared
`scripts/check_staging_media.py` uses memory-only OAuth sessions, synthetic files and
an explicit account chooser. Its live two-account run waits there; foreign-workspace
and same-workspace/private-channel file denial must not be claimed until it passes.
If the OAuth callback expires, rerun with the public staging profile and report path.
No credentials should be pasted in chat. Report: ignored
`work/staging/media-acceptance.json`.

Residual voice sound quality, revised inline playback acceptance, real model
personality behavior, full required-Bud → deferred highlight-tour handoff and meeting
hosting/two-device transcription remain open. A signed-out media check does not
substitute for hosted expired-token testing. Phase 3 is not complete.

### Follow-up — second-account sign-in did not complete the probe

Owner reported signed in. Inspection showed Supabase `bad_oauth_state` because the
previous authorization state expired; the runner then timed out. Fresh attempts used
normal OAuth again. One attempt hit a hosted ReadTimeout and cleaned up its probe
workspace. After the staging readiness endpoint returned 200, another fresh run
passed private-thread publication/download and both cancellation boundaries again.
The second account chooser opened correctly but that account is signed out in Safari;
Google requests its password and Safari did not supply an existing autofill value.
No password was read, entered, changed or saved. The two-account tests remain blocked
by completion of that fresh Google login, not by a passing isolation result.

Owner action at handoff: in Safari → current Google “Hi Ayansh” sign-in, enter the
second staging account password privately and complete Google sign-in. If that link
expires, reply ready so a fresh runner authorization can be opened; do not use an old
callback link. No SQL, provider key, payment or production change is required for this
check. Remaining Phase 3 gates recorded above still apply. Phase 4 UX may be proposed
with explicit permission while these release gates remain open; do not silently mark
Phase 3 complete to advance the checklist.
