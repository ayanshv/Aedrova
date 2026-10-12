# Voice messages — staging acceptance

The composer microphone now records voice attachments, replacing the default speech-to-text flow.
Record up to 5 minutes, finish, preview with Play/Pause, then explicitly Send voice.
Cancel, logout, hiding/closing the app, or changing conversation discards local unsent audio.
Typed text stays unchanged. Audio is mono 16 kHz 16-bit PCM WAV (1 second–5 minutes), under 10 MB.
No speech-provider request or AI allowance is used. Uploaded audio consumes existing workspace
storage and is available only to authorized members through the existing attachment RLS.

The native and server content inspectors validate container size, format, frame count and actual
PCM bytes. Existing server upload rate/concurrency limits and hash verification remain in place.
The additive 202610120002_voice_messages.sql migration permits audio/wav only through privileged
verified finalization. Owner reports successful installation in Staging on October 12, 2026.
Do not run in production yet. Deploy matching staging backend before testing Send voice.

Voice attachment cards play/pause in the conversation, display playback progress, and support
existing attachment save actions. Playback uses a private temporary WAV, removed when stopped
by a scope change or app closure. No automatic playback and no automatic AI ingestion/transcription.
Treat playback on clean Windows/macOS machines as a remaining release gate.

Tests cover malformed/truncated/trailing WAV, duration/format limits, preview without upload,
rejected queue retention, accepted queue cleanup, channel-change discard and no model calls.
Real microphone capture/provider dictation was observed before the change; this does not count
as real voice upload/playback acceptance. Phase 3 remains open until those live cases pass.

## October 12 live follow-up

Owner recorded and previewed a real 10-second clip. Native Send voice published it with
“Shared · verified securely”; it survived source-app restart. Owner reported severe distortion,
so sound-quality acceptance failed. Changed recorder to device preferred sample format/rate,
explicit float/integer conversion, channel downmix, partial-frame preservation and continuous
resampling. Raised duration to five minutes (9.6 MB PCM), within the existing 10 MiB cap.
No new SQL is needed for the duration change; deploy the matching server policy.
Human listening recheck is required before claiming the distortion resolved.
Image and UTF-8 text attachments now get bounded private thumbnails/snippets in chat;
PDF/Office stay click-to-open/save and are not executed or fetched from external URLs.
Failed sends retain local previews for retry. Discard/context changes cancel pending upload.

## Revised recorder acceptance

Owner sent the revised eight-second clip and reports “distortion is mostly gone.”
The clip is present in the server-backed feed after a fresh source-app launch. This
is an improvement, not a clean sound-quality pass: residual distortion remains an
open Beta issue. A live text snippet rendered after fixing preview scheduling in
server snapshot updates. A synthetic PNG also passed hosted upload verification.
The five-minute policy is live on the existing free staging backend (e375bdc);
no further migration, key, payment or hosting upgrade is required for voice messages.
Image thumbnail also visibly rendered after restarting and signing in again. Live
text and image preview rendering passed; PDF/Office preview remains limited to
existing click-to-open/save behavior. All preview downloads use authenticated
attachment access and bounded local caches cleared on scope changes.

Final native regression suite: 772 passed; scoped lint, secret scan and diff checks pass.
Backend suite: 463 passed before the final native preview-only patch.
