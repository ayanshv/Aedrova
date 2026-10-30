# Current desktop translation — October 30, 2026

Desktop display translation now runs locally through CTranslate2 and SentencePiece with pinned English/Hindi Argos model data. It makes no translation inference API request and has no paid cloud fallback. Ordinary sign-in, message synchronization and language-preference saving still use the existing authenticated backend. Generating an agent response is separate and retains normal AI usage policies.

English/Hindi packs are installed on the tested Mac. On a clean installation use View → Language & translation → Download English/Hindi languages (209 MB once), then choose the display language. Downloads contain no conversation text and are size/SHA-256 checked before bounded data-only extraction. CPU inference is serialized off the UI thread, with bounded input/output and per-reader memory caches. Code, mentions, URLs and source text stay canonical; Show original remains available. Missing/unsupported packs retain originals and never trigger a paid translation fallback.

Only English↔Hindi is currently provided offline. Other language choices retain original text. Public website translation has not been converted by this desktop task and keeps its previously documented behavior. Model outputs may be imperfect; review original text for important details. Model data provenance is retained beside installed weights; release packaging must include runtime notices and verify clean-machine behavior.

## Acceptance

Two distinct staging identities read the same synthetic hosted conversation concurrently, with English/Hindi display preferences, actual local model inference, and original toggles. Multilingual prompt text and mentions remained unchanged in hosted history. Synthetic workspaces were archived for both test identities; no preference overwrites or paid entitlements were needed. Local inference was separately exercised with socket connections blocked: zero network connections were attempted. This check covers prompt delivery/display and existing multilingual intent routing; no new billable agent generation or build was run.

## Historical API implementation (superseded for desktop)

# Per-reader languages — October 29, 2026

## Behavior

View → Language & translation, also available from Your profile, chooses a personal
language and automatic conversation translation. Twenty languages are supported:
English, Hindi, Spanish, French, German, Portuguese, Italian, Japanese, Korean,
Chinese, Arabic, Urdu, Bengali, Tamil, Telugu, Indonesian, Vietnamese, Thai, Turkish
and Russian. Arabic and Urdu switch the desktop layout direction.

Messages and submitted prompts retain their canonical original body and chronological
position. Translation is presentation per reader, including teammates' prompts and
completed agent responses. Original text is immediately visible while asynchronous
translation runs. Message context menus offer Show original/translation, Copy message
and Copy original. Quoted code, inline code, mentions, email addresses, source references
and URLs are protected during translation; executable content is never translated.
Multilingual instructions enter the existing conversation/build routes. Explicit
native build requests still use current build permissions; translation itself has
no tools and cannot approve, execute or publish anything.

Interface labels, placeholders, tooltips and accessibility labels translate separately
from user-entered values. Dropdown enum values remain canonical on submission.
Preferences are stored in the reader's own Supabase Auth metadata, not workspace
roles. Existing user metadata is updated through the existing authenticated user API.
No database migration or new credential is required.

## Service and data boundaries

The matching website/backend provides authenticated /api/language and /api/translations.
Every translation checks workspace membership before caching/metering; cookie writes
require CSRF. The existing included OpenAI Responses service translates bounded batches
with a strict JSON schema and store:false. Inputs are untrusted content, not instructions.
Translation uses existing workspace AI allowance and company spending/concurrency caps;
it is not free unlimited inference. Up to 12 strings/24KB per request, 24 requests per
reader per minute, and four translation requests concurrently at service level.
Responses are bounded and validated before display. No raw translation text is logged.
Server cache is memory-only, reader/workspace/target scoped, 15 minute TTL, 256 entries.
Desktop cache is memory-only, scoped and cleared on sign-out/account change. Stale
language/account results cannot update the new reader's view. Quota/provider failures
leave originals visible; no local provider fallback or silent unbounded retry.

The website footer shares the account preference on authenticated pages. Unsigned
visitors have core Hindi navigation from a static catalog; other/full-page website
translations currently require a signed-in workspace with included AI enabled.
This is not a complete offline catalog for every public page/language. Public legal
texts/metadata remain canonical English. Automatic translations should be checked
for important decisions and legal wording; do not describe them as authoritative.

## Verification and remaining acceptance

Deterministic local tests cover reader-specific message display, original preservation,
copy behavior, language restoration, enum submission, RTL, account cache clearing,
stale in-flight results and repeated account snapshot refreshes. Backend tests cover
metering/settlement, membership revocation before cache reads, CSRF, request bounds,
protected tokens, invalid model output and private preference updates. Real Qt light
and dark Hindi captures are under ignored work/multilingual-oct29. The displayed
conversation translation in those captures is a deterministic fixture, not a live
provider-quality result. No purchase or new provider funding has occurred.

Required before declaring live acceptance:
1. Deploy the matching backend source to Render → aedrova-beta-staging using existing
   settings; do not activate paid compute or production services.
2. Sign in to the updated Staging app → View → Language & translation → Hindi → Save.
   A second reader keeps English. Send ordinary non-sensitive test text in English and
   Hindi, and ask the main agent and Research Bud a question. Verify both readers see
   their chosen language and Show original returns the exact source.
3. Verify preference survives a fresh authenticated session, and quota/provider failure
   retains original text. Native speakers must review translated wording and RTL layout.

Stage 1 remains OPEN for existing public provider approvals and final human audio
clarity. Funded Claude and reliable two-device meetings stay deferred final paid gates.

Local verification: full desktop suite 1059 passed before the final snapshot/lifetime
hardening; 44 targeted localization/collaboration checks passed afterward. Full backend
suite 657 passed. Both source trees pass Ruff, whitespace and tracked credential checks.
The browser preview verifies Hindi navigation and an explicit unavailable/original-text
fallback for unsigned visitors; source IDs/URLs and form values are unchanged.

## October 30 live follow-up

Website/backend main includes the final cache correction at 5120d55 and is Live in
staging. Translation scripts and every shipped locale catalog participate in the
asset version, and locale fetches use that version. Website tests: 658 passed.
Desktop initial final suite: 1063 passed. Live startup testing then found busy
workspace synchronization could discard or starve a language save. Saving now uses
an independent authenticated clone/worker, with one pending save per window and
account/lifetime checks before applying results. 30 targeted localization/profile
checks passed, including busy refresh, errors, and an account switch. The full/hosted
candidate suites and the native language-quality check gate final acceptance.
