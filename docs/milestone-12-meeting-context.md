# M12C — local consented meeting-text foundation

Owner approved local consent, transcript storage and scoped agent context on October 3.
This implementation does not record audio/video or call a speech provider. Text submitted
by a participant is explicitly `participant_text`, not a verified provider transcript.
Automatic speech ingestion remains a following, separately approved task. Public features
stay disabled; owner hosting, credentials, migration and hardware actions are deferred to M14.

## Implementation

The incremental `202610030001_meeting_context.sql` migration adds channel-scoped segments,
RLS, user-JWT RPCs, revision/roster barriers, immutable idempotent IDs, speaker attribution,
60 writes/minute/user, 2,000 characters/segment, 10,000 segments/meeting and 30-day expiry.
The caller is the speaker; no client may attribute supplied text to another participant.
Saving requires every currently present participant's transcription/text consent. AI use
requires unanimous additional AI consent at write time. A fresh join resets choices.
Crossing a roster/consent revision or expired presence rejects the pending segment.

Explicit withdrawal can disable AI use of all stored text in the meeting, or permanently
delete all its shared text. Any meeting participant can withdraw, including after a call
ends or their workspace membership is removed; this permits privacy withdrawal without
restoring read access. Leaving/ending stops future capture and preserves previously saved
consented text until withdrawal/expiry. Restoring consent never resurrects withdrawn AI
sources. Expired rows are hidden immediately; physical deletion needs scheduled maintenance.
Deletion removes database rows, not immutable provider requests, exported local snapshots
or existing backup copies. Already-running provider work cannot be retroactively recalled.
No unqualified instant erasure promise is made.

The server has explicit `AEDROVA_MEETING_CONTEXT_ENABLED=false` by default; turning it on
requires an enabled meeting service and the migration. Capability discovery, consent,
participant-text writes and withdrawal use existing user tokens and SQL authorization.
The independent guard remains required for joining. The public waitlist configuration is
unchanged and refuses meeting activation.

Desktop Meeting privacy is shown only when the server advertises this capability. It has
separate unchecked storage/AI choices, dependency handling, explicit withdrawal and a
confirmation before deleting everyone's saved text. The footer reports consent readiness
without implying audio recording. The dialog is asynchronous through the call worker;
failed writes appear in the call status. Ordinary calls continue on older servers.
There is not yet a desktop transcript editor/browser or an automatic speech ingestion UI.
The text-submission API is currently foundation work for controlled local testing.

Agent context has a separate bundled `meeting_context_enabled` switch, false by default.
When enabled it reads at most 50 eligible segments per selected permitted channel, checks
scope/AI consent/provenance, and re-reads before returning to catch withdrawal or expiry.
Segments enter FTS retrieval with `meeting:` citations, speaker ID, offset and fingerprint.
They cannot use the chat decision confirmation button or impersonate agreed decisions.
Existing context revision triggers detect text inserts, updates and deletions.

## Owner actions — M14 only, none now

1. After existing migrations, run `supabase/migrations/202610030001_meeting_context.sql` in
   the existing project's SQL Editor. Never run test/bootstrap SQL on the hosted project.
2. Configure approved always-on meeting API/guard and shared secrets using the website
   repository's `docs/render-meetings.md`. Keep waitlist meeting flags false.
3. Once physical/media/consent acceptance is ready, enable `AEDROVA_MEETING_CONTEXT_ENABLED`
   only on the staging meeting services. Rebuild the internal app with the same build-time
   flag to include permitted text in agent context. No secret is placed in the app.
4. Set up privileged daily expiry maintenance. With pg_cron explicitly enabled in Supabase,
   the operator can schedule `select aedrova_private.expire_meeting_text()` daily. This
   requires owner review/setup at M14; no scheduler or live migration has run now.
5. Run real user-JWT consent, private-channel, withdrawal, expiry and build-context checks
   against staging. Check durable snapshots/queued builds after withdrawal and stop any
   running build whose supplied context must no longer be used. Provider calls already
   sent cannot be recalled. A second Mac remains needed for physical meeting acceptance.

## Verification and next scope

Embedded PostgreSQL tests exercise actual migration/RLS/RPC behavior and conservative
withdrawal. Python tests cover server gating, bounded payloads, forwarding user JWTs,
capability fallback, UI choices, source attribution/citations and retrieval revalidation.
Light/dark dialog screenshots were inspected and initial paragraph clipping corrected.
These are local results, not hosted speech/provider or two-device acceptance.

Final local verification: 431 desktop tests, 194 website/backend tests and all 19
embedded PostgreSQL scripts passed. Scoped Ruff, Python compilation and whitespace
checks passed. Deployment flags remain false; no hosted migration or paid resource
was activated. The website suite reports an existing Starlette/httpx deprecation warning.

Next separately approved task: automatic speech-provider adapter with bounded ephemeral
audio, revision/roster barriers, speaker mapping, visible capture state, failure handling
and a transcript review surface. Test with fixtures until owner setup in M14. Provider
transcripts need a trusted ingest/provenance design; the participant-text RPC cannot
silently be relabeled as a verified speech result. Summaries/decisions require explicit
human review and should cite the stored source instead of inferring agreement.
