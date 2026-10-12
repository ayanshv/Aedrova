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
