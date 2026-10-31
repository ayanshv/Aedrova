# Current desktop translation — October 30, 2026

The desktop catalog offers 50 language and regional choices. Each non-English choice has a pinned English↔language pair; non-English conversations pivot through English. English and Hindi remain the default first choices. The catalog includes European, South Asian, East Asian, Middle Eastern and African languages, with Brazilian Portuguese and Traditional Chinese variants. Arabic, Urdu, Persian and Hebrew use right-to-left layouts.

Translation runs on the device through CTranslate2 with SentencePiece or Moses/BPE tokenizers. It makes no translation inference API request and has no paid cloud fallback. Normal account sync and saving preferences still use the authenticated backend. Agent generation retains normal AI usage policies.

Open View → Language & translation, choose a display language, and download its language pack. Download size is shown before installation. English readers can separately choose source-language packs to read teammates’ foreign messages. Only selected pairs download; packs are not bundled into every installer. Existing English/Hindi packs stay usable. Each device needs its own packs and disk space; installation needs internet once. Missing packs keep original text visible.

Official Argos package data is pinned by compressed length and SHA-256 and extracted as bounded data only. Model metadata and tokenizer variants are respected. CPU inference runs off the UI thread, with at most two loaded model engines and reader-scoped caches. Code, mentions, URLs, Aedrova/Buds brand names and canonical source text are protected. Show original remains available. Language detection and translation quality are probabilistic; native-speaker review of all languages has not been performed. Short or ambiguous text can be misidentified. Unreliable output falls back to originals.

Public website navigation has static locale catalogs and no inference charge. This is navigation coverage, not human-verified translation of every public/legal page. Signed-in full-page website translation remains the separate metered backend feature. No claim of free unlimited AI inference or legally authoritative translated text is made.

## Verification of the expanded catalog

Every advertised non-English desktop choice must have both verified data packages in models.json. All 98 official model archives were verified locally and pinned. The expanded desktop suite passed 1,082 checks; the separate full-catalog coverage check passed afterward. Five real models (Spanish, French, Danish/BPE, Japanese and Korean) translated a synthetic sentence with socket connections blocked and zero network attempts. Local checks cover selected-pair-only downloads, checksum failure, bounded extraction/path traversal, BPE installation, pivoting through English, original preservation and simultaneous reader isolation. The publisher rejected GitHub runner downloads with HTTP 403, so package verification ran locally; the standalone verification script is retained. Existing required desktop/RLS CI is unchanged. Clean-machine Windows/macOS installer and native-speaker review remain release work.

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
