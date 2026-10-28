# Stage 1 follow-up — October 25, 2026

**Stage 1 remains OPEN. This does not approve #2 or production launch.**
All work used staging or synthetic local fixtures. No purchase, paid upgrade,
production deployment, new provider scopes, automatic refill or payment was made.
This addendum supersedes older connector-readiness and native-onboarding gaps in
`staging-acceptance-2026-10-24.md`; it does not waive the remaining live gates.

## Native acceptance completed

- Created the disposable `Prelaunch audit Oct24` workspace with the existing test
  identity. Mandatory Auto/model and execution-policy review prevented creation
  until reviewed; Go to dashboard dismissed its dialog.
- Replayed the complete introduction/profile/project/device/review onboarding
  using a synthetic local project. This is an empty workspace with a first-run
  experience, not a new Google identity or clean-machine installer acceptance.
- Required Bud setup opened, displayed shared Free capacity (0/1), and filtered
  Research tools correctly. Finish later resumed the component tour.
- Navigated all 22 tour steps in both appearances. Found the masked guide could
  be accessible but invisible on macOS after a theme change. Replaced the oversized
  masked overlay with a card-sized widget; confirmed the corrected running native
  guide is visible in dark and light mode, including a live theme change.
- Created and opened a private channel. Selected an image: its thumbnail appeared
  above the composer, remained unsent, and removal restored disabled Send.
- People displayed the owner's Away availability and configured status emoji.
- Log out removed the native session; ordinary Google sign-in returned to the app.
- Archived the disposable workspace for its owner using the supported RPC and
  verified it appears in the recoverable archive. Original workspace unchanged.

## Repairs made during acceptance

1. Bud wizard still remapped index 4 as a removed legacy connector form, skipping
   personality. Restored sequential seven-stage navigation and Back behavior;
   custom tone/reporting/personality survive navigation and saving. Confirmed the
   real native personality page appears. Corrected initial 1/6 progress to 1/7.
2. Removed Brave branding from customer-facing Web Search gallery/detail copy.
   Provider transparency in privacy/backend configuration remains intact.
3. Corrected native tour geometry/visibility as above. No surrounding light box
   or full-window input-intercepting overlay was introduced.

## Fresh connector checks

Used the existing `Beta isolation 1 eb8958` / `TikTok staging audit` fixture Bud.
Renewed existing scopes/accounts; did not expand organization/project/page access.
Tokens remained in memory or encrypted server storage; reports omit returned data.

- GitHub: existing installed repository discovery; selected `ayanshv/Aedrova`;
  actual repository, changes, issues and deployment reads passed.
- Notion: renewed only the already-selected `Aedrova connector validation` page;
  page discovery, selection and actual page read passed. Other pages unselected.
- Supabase: existing Aedrova organization Projects READ; selected only Aedrova
  Staging and verified its project reader. No production project was selected.
- Figma: existing file-content read scope; actual design read of the previously
  used Untitled prototype passed. API discovery still requires an explicit file
  selection/link. A helper initially supplied a URL where the server requires a
  normalized file identifier; validation correctly rejected it. Corrected helper
  input, not product security. No file creation, editing or deletion.
- Instagram: existing `@aedrova_ai` basic read grant renewed; verified branded
  Connected callback and real profile/posts readers.
- Vercel: reused the already-installed Aedrova Buds integration for ayansh2 without
  changing its project scope; verified Connected callback and project/deployment
  readers. Did not grant environment-variable or deployment writes.
- All six local staging connections then disconnected successfully; subsequent
  tool reads were denied. `provider_revoked=false` is accurate: global uninstall
  was not performed and could affect other grants. Pending states expire normally.
- Stripe: test account selector and Accounts/Balance read-only permissions render.
  Did not submit a new installation. Cancel returned branded “No new access was
  added”; authenticated state reported failed rather than connected.
- TikTok: fresh same-scope PKCE flow reached real login; no signed-in session was
  available in the controlled browser. No repeated credential/attempt-limit retries.
- Web Search remains honestly unavailable (`managed_available=false`).

These are scoped staging tests, not public provider approval, global revocation,
forced live expiry/refresh or every-account certification. Eight OAuth providers
now advertise configuration, but configuration alone does not establish readiness.

## Additional owner-requested visual and scrolling update

The supplied folder and device references share translucent cool layers, fine rims,
rounded contours, soft depth and simple outline symbols. Rebuilt the device panel
natively with microphone/camera/display symbols and adapted the older workflow,
profile, repository and final-review illustrations to that same visual language.
Light/dark colors resolve from the existing theme. Existing buttons and theme
styles were not changed. Graphics remain illustrative, not live hardware meters.

Chat wheel input now uses 40 pixels per conventional notch and 55% of native
trackpad pixel movement, retaining fractional motion and native momentum without
an added animation queue. Scrollbar dragging and keyboard navigation remain native;
manual scrolling cancels deferred jump-to-message requests and clamps at boundaries.

## Validation and evidence

- Final complete desktop suite before the additional visual/scrolling change:
  **980 passed**, one existing audioop deprecation warning.
- Final visual/scrolling and onboarding suite: **125 passed**, including actual
  wheel-event tests for large messages, fractional trackpad input and boundaries.
  Log: `work/prelaunch-checks-2026-10-25/visual-scroll.log`.
- Scoped Ruff, tracked-source secret scan and diff checks passed.
- Ignored local evidence: `work/prelaunch-checks-2026-10-25/`, including
  `connectors/live-batch.json`, `cleanup.json`, unsent attachment preview,
  corrected native tour screenshots, Instagram callback and Stripe cancellation,
  and rendered light/dark illustration sheets. Private handoff URLs are removed
  after use. No session token or account content belongs in committed evidence.

## Historical owner actions (superseded by the follow-up below)

1. **TikTok:** Staging → Buds → existing Marketing Bud → Connectors → TikTok →
   fresh Connect your account. Sign in as sandbox-approved `@aedrova`; leave the
   read-only consent open. Stop if TikTok reports an attempt limit. Required for
   live profile/video and disconnect checks; do not reuse expired browser tabs.
2. **Stripe connector:** use its fresh Connect your account button, select the
   intended Aedrova test dashboard, and approve only Accounts/Balance read access.
   The new test installation requires account-access consent, not a payment.
   Leave the confirmation/result for validation; no real checkout is involved.
3. **Web Search:** activate/configure the intended operator service account using
   private deployment settings. If payment is required, keep it at the final paid
   gate. Never ask customers to paste an operator API key.
4. Remaining acceptance includes public provider approvals and lifecycle/isolation
   coverage, new-workspace Free/early-access activation, and actual Claude coding.
   Claude's existing key validates but its credit balance is unfunded; do not
   regenerate a key or fund it now merely to clear this checklist.
5. Reliable meetings still depend on the separate guard/always-on service and
   subsequent two-device microphone/camera/consent/transcript acceptance. Keep
   required funding and owner hardware permissions at the consolidated final gate.

Paid deferral changes timing, not pass criteria. #2 cannot be represented as
unconditionally ready while these required Stage 1 checks remain open. No new SQL
migration or production action is required for the UI repairs in this report.

## October 25 follow-up — approved live checks

- TikTok: fresh sandbox login/callback passed; actual profile and public-video
  reads passed. Local disconnect succeeded and subsequent reads were denied.
  No attempt-limit retry or expanded scope.
- Stripe: approved test-mode installation passed on the intended Aedrova
  dashboard with Accounts/Balance reads only. Callback and balance read passed;
  local disconnect succeeded and subsequent reads were denied. No payment.
- Both disconnects returned `provider_revoked=false`: the provider installation
  is not globally revoked. These tests do not certify public release or forced
  token expiry/refresh. Public social approvals/non-tester acceptance remain open.
- New disposable workspace started with `no_plan`, zero allowance. Free activation
  returned active with 500000 micro-USD allowance and 366697 available after the
  existing shared caps. Repeating activation returned identical balances; no
  replenishment. No model calls, checkout or subscription. Workspace archived
  recoverably; test session signed out. This accepts Free activation, not the
  separate Pro/Team early-access promotion or live coding inference.
- Focused backend OAuth, certification, promotion/budget and meeting regressions:
  **130 passed**, one existing dependency deprecation warning.
- Existing Claude credential still returns a credit-balance error (400) on the
  count-tokens check; meeting health remains 503. Funding, infrastructure and
  actual two-device acceptance stay at the final paid/device gates.
- Search: accepted the specifically approved free agreement, then stopped before
  saving a card. Provider requires a valid card even to unlock free credits;
  no card submitted, key issued, credential copied or staging deployment made.
  Owner subsequently proposed using existing OpenAI knowledge instead. Research
  analysis can use the existing AI route, but must not claim live web verification.
  Separate web-search activation remains optional pending that product decision;
  do not represent the unavailable connector as connected.

Sanitized evidence: `work/acceptance-final-oct25/live-batch.json`,
`activation.json`, `dependencies.json`, `backend.log`, connected screenshots and
`search-card-required.png`. Private login/authorization handoff files removed.
No production changes. Stage 1 remains open for the remaining applicable gates.

## OpenAI Search replacement — supersedes Brave activation

At the owner's request, implemented and deployed OpenAI Responses live web search
using the existing server credential. Real staging research passed with two HTTPS
sources and $0.019123 recorded against existing AI allowance. Connection creation
spent nothing; disconnect and later-read denial passed. No Brave/card action remains.
Full backend suite 638 passed; desktop regression group 97 passed; final source-link
checks 3 passed. See `docs/openai-research-acceptance-2026-10-25.md`.

Meta required policy/deletion URLs were saved and verified after reload; publishing
screen confirms required settings complete. App remains unpublished; public access
review is not certified. TikTok Production is a draft requiring production setup
and real end-to-end review video. Prepared descriptions, scopes and demo steps:
`docs/provider-public-review-preparation.md`. Funding and actual Claude/meeting
acceptance stay at final owner-paid/device gates. Stage 1 remains open.
