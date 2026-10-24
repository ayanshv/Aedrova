# Meeting Step 8 — communication and transcript foundation

October 16, 2026. Owner approved starting Step 8. **Partial implementation; not
full Step 8 completion or live meeting acceptance.** The entire requested feature
list remains in meeting-features-owner-source-2026-10-16.txt and the immutable
release-baseline-2026-10-15.json. Nothing has been dropped from that list.

## Delivered source changes

- Native **Channel chat** available from audio/video meetings. Uses the existing
  signed-in identity, fixed originating channel, message_page and send_message RPCs;
  existing channel RLS, posting rules and server write budgets remain authoritative.
  Clearly says channel members outside the call can read it and messages persist.
  Latest 50 root messages; selectable plain text (including links), no HTML execution.
  A failed send retains its draft and retries with the same message ID. Account
  changes, authorization errors and call closure clear displayed private text.
  This is channel chat, not a new meeting-only or private-recipient chat system.
- **Captions** is an explicit, read-only window with three text sizes and selectable
  text. Reads latest 20 existing permitted transcript segments every three seconds,
  one request at a time. Opens no device, starts no transcription/provider call.
  Current exact participant consent and a snapshot no older than ten seconds are
  required before fetching and displaying. A consent change during a request
  discards its result. A 500ms local guard clears text on stale/disallowed consent.
  Participants still individually consent, start transcription and unmute. Delayed
  provider chunks may leave gaps; sender account is not verified voice attribution.
- Backend transcript GET accepts `latest=true`, bounded to 20 rows ordered by
  insertion time/id. It uses the caller's existing Supabase RLS token and feature
  gate. No new table, migration, service-role privilege, RTC data permission,
  recording grant, provider key, allowance or paid hosting change.
- Meeting privacy waits for server acknowledgement before closing; failures and
  timeouts remain retryable. Request IDs prevent an old acknowledgement from
  closing a later operation. Fixed failures emitting unknown media control kinds.
- Transcript edits/decision choices survive switching segments. Saving one segment
  keeps others' drafts. Page/meeting changes, refresh and closing require explicit
  discard when unsaved. Search filters the current page. Session closure and
  authorization errors purge private drafts without a confirmation prompt.
- Existing post-call “Share with Aedrova?” review/atomic confirmation, source
  citations, explicit decisions, separate AI reuse permission, expiry and withdrawal
  remain intact. Recording is still OFF: transcription consent does not grant
  audio/video recording rights.
- Wrapped footer controls, bounded text windows, accessible control names,
  keyboard-selectable text, initial skeletons and light/dark styling.

## Verification and limits

- Desktop full regression and final focused checks recorded in milestones.md.
- Backend: 8 meeting context/wrapup API tests passed, including bounded latest
  query, caller token forwarding, missing authentication and disabled feature gate.
- New controlled Qt tests cover ambiguous-send retry, channel mismatch/revocation,
  account switch, consent change in flight, stale captions, font size, privacy
  failure/retry/success and stale acknowledgement, draft preservation and call-end
  cleanup. They use fixtures, not live cross-workspace Supabase acceptance.
- Light/dark 680px meeting and 640px chat/caption previews rendered; inspected light
  meeting and dark captions. Ignored evidence: work/meeting-step-8/*.png.
- No hosted call, actual speech capture, second account live RLS check or physical
  accessibility/device acceptance was performed in this batch. No production
  deployment, hosted flag change, signing or installer rebuild.

## Remaining Step 8 engineering

Private/selected-recipient meeting chat; meeting-only chat policy; in-call file
attachments/export; reactions, raise hand and nonverbal feedback; profile editing
and invite/join details; summaries/action extraction and meeting Q&A beyond existing
retrieval; local/cloud recording and host recording permissions; manual captions,
caption positioning and physical screen-reader validation. Polls, translated
captions, advanced moderation and other advanced requests remain explicitly in the
Step 9 scope rather than exposed as fake controls. See meeting-step-8-status.json.

## Owner actions — consolidated, no new requirement now

The owner deferred paid hosting; do not start charges or bypass the access guard.
These existing gates block hosted meeting acceptance and launch:

1. When ready, personally select/submit the $7/month always-on API plan in
   Render → aedrova-beta-staging → Compute. Deploy the separate staging meeting
   guard from Aedrova_site/deploy/render-beta-meeting-guard.yaml (another $7/month
   base service). Confirm charges before submitting; neither was enabled here.
   Transfer any missing private LiveKit values only through the approved private
   settings workflow, never chat. Keep staging Supabase/credentials separate.
2. After the guard is healthy, deploy this backend branch and use the updated
   desktop source with work/staging/public-config.json. Verify
   /health/meetings returns 200 before enabling hosted acceptance. No SQL migration
   is added by Step 8. Do not promote to production or distribute installers yet.
3. On two physical devices with two staging accounts, grant mic/camera permission
   yourself and test channel chat, refusal for a user outside the private channel,
   transcription only after both consent, captions stopping on consent withdrawal,
   editable review/decision/version conflict, post-call Confirm, saved-text expiry
   and deletion. Confirm real listening/captions and keyboard/screen-reader access.

Continue Step 8 engineering within existing approval. Do not mark Step 8 complete
or move into Step 9 merely because the foundation's controlled tests pass.
