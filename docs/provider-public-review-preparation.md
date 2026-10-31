# Public connector review preparation

October 25, 2026. These are prepared descriptions, not claims of provider approval.
No payment, new production credentials, callback grant, permission expansion or
public publishing was submitted in this pass. Stage 1 remains open for applicable
provider approvals and acceptance with an account outside the tester list.

## TikTok

Dashboard: https://developers.tiktok.com/app/7694803472533112852/pending

Observed: **Production / Draft**, description/URLs/platforms/review video empty,
no products or scopes. The separately configured sandbox passed real profile and
public-video reads. Sandbox acceptance cannot substitute for production review.

Prepared public description (under 120 characters):

> Aedrova connects team workspaces to TikTok so users can review their profile and public videos.

Prepared review explanation:

> Aedrova is a team workspace with configurable AI assistants called Buds. In Buds,
> configure a Marketing Bud, choose TikTok and select Connect your account. Login
> Kit authenticates the user. Display API user.info.basic identifies the authorized
> account; video.list retrieves its recent public videos. The Bud uses these reads
> to answer the user's questions. Aedrova does not publish videos, send messages,
> read private videos or request advertising permissions. Users can disconnect in
> the Bud's connector settings, immediately preventing further Aedrova tool reads.
> The submitted demonstration uses the existing sandbox-approved test account.

Use verified public pages: https://aedrova.com/terms,
https://aedrova.com/privacy, https://aedrova.com/data-controls.
Use the actual desktop app icon, Desktop platform, Login Kit and Display API;
request only `user.info.basic` and `video.list`. Register the intended final HTTPS
callback only after reviewing its destination, environment and production release
scope. Do not reuse the sandbox credential as a production credential.

Required real demo: launch staging app → Marketing Bud → TikTok → fresh connect →
approved test-account login/consent → branded connected screen → actual profile
and video read in Bud conversation → disconnect. Record the actual flow (MP4/MOV,
up to 50 MB); do not fabricate a successful demo or include secrets. Provider
requires all requested scopes demonstrated. Review the complete draft before final
submission; acceptance is an external provider decision, not a code change.

## Meta / Instagram

Dashboard: https://developers.facebook.com/apps/3077883259220045/go_live/

Saved and verified: Privacy `https://aedrova.com/privacy`, Terms
`https://aedrova.com/terms`, data deletion `https://aedrova.com/data-controls`.
Publishing screen now states required app settings are complete, but app remains
unpublished. Dashboard says Tech Provider access verification is required to submit
App Review for other users/business data. Do not invent a registered entity or
operator identity; Aedrova remains the brand until registration actually completes.

Prepared `instagram_business_basic` justification:

> An Instagram Business or Creator account owner explicitly connects their account
> to a Bud. Aedrova reads the authorized account's profile and recent media so that
> the user can ask questions about that account. It does not publish, delete media,
> send/read direct messages or access other accounts. Aedrova stores credentials
> privately on its backend, provides disconnect controls and published deletion
> instructions. Demonstration and test credentials must be provided privately via
> the provider's designated review process, never committed or put into chat.

Next review Manage messaging & content on Instagram → requested permissions/App
Review for exactly the read-only scope. Complete required Tech Provider/access
verification using the actual operator details; the owner personally handles any
identity or business documents and security challenges. Confirm exact scope and
destination at any final new access/terms/publish action. Do not enable messaging
or publishing merely because the broader use-case name contains those words.

## Deferred payment and hardware work

Later, at the consolidated final owner-paid gate: fund existing Anthropic API
account (do not regenerate its valid key); upgrade/configure the selected
production backend and separate meeting guard, plus any temporary isolated capacity
needed for acceptance. Owner submits all payments; auto-refill stays off.
Then run actual Claude builds and two-device microphone/camera/device-selection,
join/leave, host controls, consent, transcription and final transcript review.
These remain launch blockers until they pass. Search no longer needs a separate
paid account or owner card action; its normal OpenAI usage remains metered.


## Final staging pass addendum

Exact current acceptance evidence: docs/staging-acceptance-final-2026-10-25.md.
Research single-turn conversation/history/reopening now passed after client routing
and citation fixes; temporary test Pro access restored to Free with counters intact.
Meta Add to App Review explicitly opens an **irreversible Tech Provider status**
confirmation before business/access verification. The owner specifically approved continuation and Continue was clicked.
Submission draft 3090636337944737 is accessible, but Submit remains disabled.
Website platform https://aedrova.com/ and Utility & productivity category saved.
Actual business portfolio/access verification, app icon certification, allowed usage,
data handling and genuine reviewer instructions remain required. No private
documents, new business account, new agreement or public submission completed.
The review page is preserved. TikTok actual 1024px mark uploaded; the remaining Save validation error
is the missing genuine demo video. No false demo, production callback, public
permission grant or final agreement was submitted. Draft fields are not claimed saved.


## October 31 — portfolio created; public approval still blocked

Owner explicitly approved the prepared Meta portfolio creation. Meta confirmed
“Aedrova was created”; portfolio 4669825286497673 is linked to app
3077883259220045. This creates a Meta administrative portfolio, not a corporation.
The app remains Unpublished, the portfolio Unverified, and access verification
is disabled until business verification completes.

Verification was opened without selecting a legal business type. The owner must
privately confirm the actual country, business structure, legal operator and
any required supporting information/documents in Meta Business Suite → Settings
→ Security Center → Verification for Aedrova. Do not infer a corporation,
partnership or sole proprietorship from the brand or team roles. The previously
deferred registration and operator placeholder remain unchanged.

TikTok Production draft now contains the prepared Productivity description,
policy URLs, Desktop selection, Login Kit, user.info.basic and video.list.
The actual 1024×1024 mark was uploaded. Save still reports validation errors:
a genuine end-to-end demo video and a Desktop redirect URI are missing. These
in-browser fields are UNSAVED; they are not a submitted review. Do not use
sandbox credentials as production credentials or register an unreviewed final
callback just to satisfy validation. Both provider tabs are preserved.

An isolated real staging desktop workspace was opened for the demonstration,
without mocked connector data or model calls. Native automation currently selects
the older installed staging window instead of this Python window. Owner action:
bring “Aedrova — Provider review demo” to the front. Recording the actual connect,
consent, profile/video read and disconnect flow remains blocked until that window
can be controlled. No fabricated review video was uploaded.

Release CI exposed a queued refresh callback accessing a destroyed account dialog.
Commit 4336ca0 stops the controller/timer before touching deleted Qt objects; a
regression queues the callback after actual deferred deletion. 33 focused checks
passed. Required hosted desktop and PostgreSQL checks still gate source merge;
record the final CI/merge result before claiming release CI complete.

No payment, new production credential, legal registration, private business document
submission, public provider approval or Stage 2 work occurred.


October 31 continuation: all eight hosted checks at 4336ca0 passed, including both
Ubuntu/macOS/Windows runs and PostgreSQL RLS. PR #8 merged normally as
904f3dc6c52cbfc6cca2931e0ab1cf036b2f57a9. Release CI/source merge is CLOSED for this
candidate; main-push checks and installer/device gates remain separate.

The owner asked about avoiding personal verification data. No verification details
were submitted. The current Meta screen has no skip path for this public-access
route. Options are to retain approved-account testing or explicitly defer public
Instagram availability; neither constitutes public approval. Business verification
remains an external gate if public Instagram is included at launch.

The dedicated local source-only Aedrova Review Demo bundle is now accessible to
native automation. Existing Google session completed sign-in; welcome/setup was
skipped through real UI controls, and isolated workspace “Aedrova Review Demo 12e1”
is open at Bud setup. No model call, new grant, payment or public submission occurred
in opening the demo. Genuine TikTok recording is still pending.


The real UI configured Social Review (Marketing) in the isolated demo workspace,
then used TikTok → Connect your account. The hosted identity handoff accepted the
existing staging Google account and reached Safari’s TikTok login page. No active
TikTok session is available there. Owner must sign in as @aedrova, leave consent
open, and stop on any attempt limit. No TikTok consent, read-result demo, video
upload or public submission is claimed for this attempt. The demo app remains open.


October 31 signed-in continuation: Safari’s own Profile link identifies @aedrova5.
The matching sandbox’s public client key was compared to the real authorization
request and matched; its Target Users table contains only @aedrova. The fresh
authorization returned access_denied/non_sandbox_target, not an attempt-limit error.
No blind retry or successful demo was claimed. Add account → Connect TikTok account
is prepared; owner was asked for action-time approval to link @aedrova5, or to
switch Safari to the already registered @aedrova account. No tester was added yet.
Evidence: work/provider-reviews-oct31/tiktok-add-tester-confirmation.png.


October 31 approved tester link: owner explicitly approved linking @aedrova5.
Continue was clicked on the prepared Add account dialog. The in-app browser did
not expose its popup, so the same authenticated developer sandbox was opened in
Safari. Safari's Add account → Continue opened TikTok's deliberate logout/fresh-
login flow. Its Last login indicator was Google; Continue with Google reached an
existing-account chooser. No Google identity was guessed because the required
TikTok handle is @aedrova5 and the chooser does not establish email-to-handle
ownership. Owner was asked to select that account and leave confirmation open.
The tester link is NOT yet verified complete; no new consent/payment/public
submission is claimed. Prior specific approval remains valid for this exact link.


October 31 — tester account access unavailable: owner reported no longer having
access to the account needed by the fresh @aedrova5 tester-link login. Stop this
linking attempt; do not guess another Google identity, bypass account checks or
claim the tester was added. No completed link was verified. TikTok demo/public
review is blocked until the owner identifies an accessible TikTok account for an
explicit tester grant, recovers the intended account through the provider, or
explicitly defers public TikTok availability. No recovery request, account change,
payment or public submission was made. Meta verification remains separately open;
release CI at 4336ca0 passed and PR #8 merged as 904f3dc6.


## October 31 — Marketing Bud publishing architecture transition

Owner requested Buffer as the primary publishing provider, replacing the need
for each customer to configure Meta/TikTok developer apps. Historical direct
read-connector evidence above remains accurate; no public approval was fabricated.
The new primary workflow uses encrypted server OAuth, explicit channel selection,
editable drafts, exact-content approval and durable at-most-once dispatch.
See docs/marketing-social-buffer.md for API findings, limitations and deployment.

Buffer confidential staging app creation and staging credential storage/deployment
were explicitly approved. The app was created and generated credentials were
saved in ignored private configuration and Render staging (save-only; deployment
waits for tests/CI). No payment or public test post occurred. The operator's
Buffer account currently has zero social channels. Owner must connect an actual
profile in Buffer, then approve exact content/channel/time for real publication
acceptance. No customer personal API keys are requested. OAuth analytics are
unsupported and clearly unavailable. Production publishing defaults disabled.

Stage 1 remains OPEN pending real Buffer login/channel/publishing/status/lifecycle
acceptance and release CI for this new candidate. Direct Meta/TikTok public review
is deferred for legacy direct connectors, no longer a dependency of the new
Buffer publishing path. Research multi-turn, offline English/Hindi readers,
prior connector lifecycle, Bud caps, fresh onboarding, bounded OpenAI build and
owner-confirmed audio clarity retain their recorded passes. Funded Claude builds
and reliable two-device meetings remain deferred final paid/setup gates. Stage 2
UI polish must follow Stage 1 and requires owner approval.
