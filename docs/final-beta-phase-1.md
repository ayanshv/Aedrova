# Final-Beta Phase 1 — release baseline

October 10, 2026. Phase 1 authorized by the owner. Later phases remain gated.
Status: hosted staging installation, Google PKCE and two-account isolation verified.
Final cross-platform CI is being completed; desktop acceptance and main-branch
protections remain owner gates. M14/public paid downloads remain deferred.

## Frozen first-release scope and evidence

| Area | Implemented source | Current acceptance boundary |
| --- | --- | --- |
| Account/workspace | Google browser return, profiles, organizations, invitations, roles, channel membership, workspace archive | Two real staging Google PKCE logins and bidirectional isolation passed; desktop UI acceptance pending |
| Chat | Channels/private channels, DMs/groups, threads, edit/delete, mentions, rich text, reactions, optimistic sends, search, attachments, saved/pinned items, presence/activity | Local regression coverage; fresh-user delivery, network recovery and upload limits need later acceptance |
| Builder | Codex/Claude adapters, project binding, context selection, isolated build/review, delivery evidence and approvals | Provider/runtime and original-folder/publish approval tests; clean-machine/provider acceptance pending |
| Buds | Six role looks, names/colors, configuration, named mentions, evidence/context, scoped connector grants | Native/service regression coverage; real refresh/revocation/customer grants still pending |
| Connectors | GitHub, Supabase, Figma, Notion, TikTok, Instagram, Stripe, Vercel, managed Search | Implementation is not universal live readiness; see matrix below |
| Meetings/context | Audio/video calls, call bar, participant state, meeting leases, consent, transcript/context and speech paths | Local tests and migration/RLS checks; multi-user media, transcription quality and consent journeys remain Phase 3 gates |
| Shared work | Product memory, decisions, review/evidence, Work/Project/Files | Source and SQL checks; live cross-workspace acceptance pending |
| Website/billing | Waitlist, Free/Pro/Team/Enterprise presentation, encrypted signup export, verified subscription/budget ledger, gated checkout/downloads | aedrova.com root/readiness returned 200 and remains waitlist; full Stripe lifecycle not certified |
| Distribution | Local macOS preview packaging, signature and release-safety checks | Developer ID/notarization and clean-machine DMG/Windows installer/update acceptance deferred to Phase 8 |

Pulse removed from desktop navigation, View menu, source module and service routes.
Its historical documentation remains marked deferred. Meeting heartbeat endpoints
and stored customer data are preserved. Linear remains excluded. Marketing media
generation is planned, not an advertised implemented release feature.
No new feature scope may silently enter this baseline.

## Connector acceptance inventory

| Connector | Baseline status | Remaining gate |
| --- | --- | --- |
| GitHub | OAuth/app and automatic account/resource discovery implemented; previous owner connection reported | Fresh customer grant, expiry, refresh/revocation/reconnect and least-privilege acceptance |
| Supabase | OAuth connection/readers implemented; previous setup recorded | Separate staging grants and customer/resource isolation acceptance |
| Figma / Notion | OAuth flows/readers implemented; previous setup recorded | Fresh customer authorization, refresh/revoke and resource selection acceptance |
| TikTok | OAuth implementation and owner account-linking work recorded | Provider eligibility/review/scopes and customer lifecycle acceptance |
| Instagram | Login implementation exists | Meta registration/review and real eligible-account validation |
| Stripe Bud | Stripe App approved for testing; account selection/binding and read-verification regression tests | Developer business verification, external testing, server credentials and public review; customer verification cannot bypass these |
| Vercel | Integration OAuth, team/resource selection and scoped reads implemented | App registration/terms and live lifecycle acceptance |
| Search | Authenticated managed enablement, daily budgets; no invented OAuth | Funded provider key and acceptance; customers should not supply a shared server key |

OpenAI implementation/local configuration exists; no new production credential or
model-access certification in Phase 1. Anthropic/runtime code and tests exist;
provider credentials/model requests/cost behavior remain Phase 2 verification.
No real connector is called complete based on mocked HTTP tests.

## Environment separation

| Environment | Database/data | App/service configuration |
| --- | --- | --- |
| Development | Disposable test SQLite/PGlite; fixtures only | Source/local HTTP; no implicit production acceptance |
| Staging | Owner-created `scvmvqlzcqhwrrsiahpj` (Aedrova Staging, healthy, Canada Central, free/NANO); 23 app migrations now installed; tables verified in the hosted Table Editor | Explicit public profile + separate `work/staging/app.ini`; Separate staging HTTPS server live; Google provider enabled and two-account native OAuth verified |
| Production | Existing `cpelagtufyocepnqcqqd`; customer/waitlist data not copied or migrated | Existing aedrova.com and connector origin; checkout/download gates unchanged |

`scripts/run_staging.py` rejects known production endpoints and secret keys in
public profiles. Backend explicit staging requires secure HTTPS and a separate
Supabase database, rejects production origin/project, live Stripe secrets and
checkout/download/development-AI bypass. The restricted database username is
validated against the chosen Supabase project rather than hardcoded to production.
Local secret files remain ignored; inspected files have mode 0600. No values are
recorded here. Staging backend credentials and Google provider are configured separately; values are never recorded here.
Do not point a profile at production merely to make a staging screen load.

## GitHub review

Both repositories are public, owner-only (0 collaborators). GitHub Secret Protection
and push protection enabled on both, verified in their hosted settings. No classic
branch protection or rulesets on either. Dependabot/security updates and CodeQL
not configured. Review completed; stronger merge enforcement remains a release gate.
After the new CI checks run, protect the default branches against deletion/force push
and require passing checks through PRs. Do not require an impossible second-person
approval for the solo owner. Changes to security-sensitive access/protections require
concrete owner approval at the applicable setup gate.

Release CI added for native Linux/macOS/Windows pytest, source/secret checks and real
embedded-PostgreSQL migration/RLS tests. Service CI covers pytest, secret/source
checks, private ledger access/atomic lease SQL and container startup/readiness.
No hosted credentials are required by CI. This is regression infrastructure, not
an independent security audit or clean-machine installer certification.
3,937 tracked vendor files under the motion project's node_modules were removed
from Git tracking; installed files remain on disk, with manifests/lockfile retained.
Recognizable-secret scans pass on first-party tracked source. Such scans cannot
prove the absence of arbitrary secrets or clean prior Git history.

## Validation log

Before change: native 734 tests, service 414 tests passed.
After Pulse removal/staging safeguards: service 409 tests passed. Native focused
baseline/call/account/release checks: 16 passed after fixing a test-module import.
Native full-suite result: **725 tests passed** (102 seconds).
Ruff passed for both repos. All ordered Supabase migration/RLS SQL tests passed in
PGlite; optional meeting migration ordering passed. The fresh staging bundle installs
atomically and refuses an existing application schema. Private ledger access and
atomic meeting lease checks passed; networked concurrency is still a live gate.
Offscreen source UI proof: `work/phase1-no-pulse.png` (synthetic workspace, no live
customer acceptance). Production website root/readiness 200; connector /api/pulse
404; one connector readiness request timed out, so production connector availability
must not be inferred from source checks. No server deploy was performed in this phase.

## Required staging setup, one owner action at a time

1. In the **Aedrova Staging** SQL Editor, run the prepared fresh-project app schema
   from `work/staging/schema.sql`. Verify the project name/ref before running. It
   contains 23 current migrations and RLS/functions, no customer rows/passwords;
   guarded against existing app schemas. Never run on the production project.
2. Configure a separate restricted staging backend role/private schema using the
   service repository's `sql/supabase-website.sql`; set its private password yourself,
   never send it in chat. Keep the private schema outside the Data API exposed schemas.
3. Configure staging public URL/key, separate HTTPS service origin and encryption
   key in ignored local/server environment; use `deploy/staging.env.example`.
4. Configure staging Google OAuth and redirect allowlist separately, then run
   `scripts/run_staging.py --config work/staging/public-config.json --check-only`
   before launching and validating two disposable users/workspaces.
5. Record remote Linux/macOS/Windows/service CI results and protect merge gates;
   record the exact deployed revisions before testing against any hosted service.

Phase 1 cannot pass until real staging setup/isolation and remote CI are verified.
Phase 2 needs a new owner approval after this phase's report. No payment or upgrade
is currently required by this setup handoff.

## Pushed revisions and remote CI — October 10

Desktop baseline pushed as a7efded on milestone-3-identity; service baseline a2b1423
on codex/bud-connectors-https. These are branch pushes, not default-branch merges or
production deployments. Service CI run 38078223509 passed all steps, including image
startup and private PostgreSQL checks. Desktop run 38078225013 PostgreSQL job passed;
Windows failed test collection because ledger.py and retention.py import Unix-only
fcntl. Keep the Windows job failing visibly; do not skip it or certify an installer.
This existing portability defect is a release blocker for Phase 8; macOS/Linux job
results are pending at this entry. No Windows runtime port performed in Phase 1.
Local macOS preview rebuilt, deep/strict signature and bundled-secret scan passed;
packaged offscreen smoke confirms four navigation pages and screenshot success.
Quit/reopen the app to load the new preview. This is not a notarized public DMG.
Owner reported staging SQL Success; hosted Table Editor confirms chat, meeting
transcript, product-memory and AI-teammate tables now exist. Separate private backend role/server/Google auth setup still pending.

Owner reported restricted private role/schema SQL Success. Next private handoff:
work/staging/enable-backend-role.private.sql (ignored, mode 0600) enables only the
staging restricted role with a unique generated password. Matching password and
separate encryption key stored in ignored mode-0600 work/staging/secrets.json.
Owner must personally run credential-changing SQL; no password appears in chat/Git.
No role password has been submitted by the agent. Staging service is not configured.
Linux CI finished with 724 passing tests and one failure: provider mismatch validation
ran after looking up an installed Codex executable. Fixed the ordering and tightened
the test to forbid runtime lookup. Focused managed tests: 16 passed. Rerun pending.

Staging backend credential handoff completed by owner; actual restricted database
login verified, public workspace read denied. Server environment validated locally.
Next gate: free Render staging service with staging-only credentials, then separate
Google OAuth setup and end-to-end isolation validation. Phase 1 remains in progress.

## Staging HTTPS service — October 10

Owner explicitly approved uploading staging-only database/encryption credentials to
Render and deploying the free service. Created aedrova-beta-staging,
service srv-db58sn8473hc73a9n3qg, deploy dep-db58sn8473hc73a9n580, commit e3da1d7.
Render reports Deploy succeeded | Live. Origin:
https://aedrova-beta-staging.onrender.com. Auto-deploy off; free $0/month compute.
Fresh external GET / and /health/ready return 200 (readiness reports ready).
/auth/google returns 303 to scvmvqlzcqhwrrsiahpj.supabase.co with redirect_to
https://aedrova-beta-staging.onrender.com/auth/callback. /api/pulse remains 404.
Credentials are stored only in Render environment and ignored restricted local files.
Public staging desktop profile saved in work/staging/public-config.json; check-only
validation passed. Production origin/database credentials were not used.

Google provider is disabled in Aedrova Staging. Exact provider callback verified:
https://scvmvqlzcqhwrrsiahpj.supabase.co/auth/v1/callback.
Next owner requirement: create a separate Google Cloud project named Aedrova Staging
(Google Cloud project selector > New project > name > Create); do not enable billing.
Then configure a testing consent screen/client, test users and staging redirect URLs.
This blocks staging end-to-end login; Phase 1 remains in progress.
No Phase 2/M14/public billing/download activation. Windows fcntl remains a release gate.

Owner reports creating the separate Aedrova Staging Google Cloud project. Current
agent browser project selector (amillum account context) returns no Aedrova matches.
Requested public Google Project ID to select the correct project/account before OAuth
configuration. Do not infer that creation failed or configure amillum as staging.
Staging Render service is live; Google sign-in acceptance remains blocked.

Owner supplied Google staging Project ID aedrova-staging, number 7280065225.
Direct in-app browser project URL opens only a partially loaded Google welcome page;
API navigation aborts, so project access/consent setup not yet independently verified.
Next owner requirement: in the owner's working browser, select aedrova-staging >
APIs & Services > OAuth consent screen (Google Auth Platform) > Get started.
Set app name Aedrova Staging, a support email available in dropdown, External audience
in Testing, contact aedrovaai@gmail.com. Owner must personally review/accept any policy
agreement on creation. OAuth client/secret/allowlist and sign-in validation follow.
Do not reuse amillum/production OAuth credentials. Phase 1 remains in progress.

Owner reports staging Google consent-screen initialization completed. Next owner
requirement in project aedrova-staging: Google Auth Platform > Clients > Create client,
Web application, name Aedrova Staging Web, authorized redirect URI exactly
https://scvmvqlzcqhwrrsiahpj.supabase.co/auth/v1/callback. Keep client secret/private
JSON outside Git/chat; install directly into staging Supabase provider in a later step.
OAuth client creation, test-user enrollment, Supabase provider/URL configuration and
end-to-end login still pending; Phase 1 remains in progress.

Owner reports Aedrova Staging Web OAuth client created and staging Supabase Google
provider credentials saved. Secrets supplied directly by owner, not received in chat.
Next requirement: in Google Cloud project aedrova-staging > Google Auth Platform >
Audience > Test users > Add users, add the Google account used to test desktop login
and Save. Keep publishing status Testing. A second independently controlled tester
account will be needed for multi-user isolation acceptance. Redirect allowlist and
end-to-end login remain subsequent gates; Phase 1 is not complete.

Owner reports Google staging test user added. Next requirement: Supabase project
Aedrova Staging > Authentication > URL Configuration: Site URL
https://aedrova-beta-staging.onrender.com; redirect URLs exactly
https://aedrova-beta-staging.onrender.com/auth/callback and
http://127.0.0.1:43827/auth/**. Native code uses random PKCE callback paths under
/auth/ on the fixed loopback port; narrow path wildcard is required. Do not add
production URLs or broad domain wildcards. Owner saves this configuration.
Staging login/end-to-end isolation acceptance still pending; Phase 1 remains open.

Owner reports staging Site URL and exact web/native redirect allowlist saved.
Started isolated source staging launcher successfully (separate public-config.json and
app.ini). Existing production app shares a display name; source process was stopped
without closing the user's packaged app, avoiding accidental production sign-in.
Opened web staging /auth/google for initial OAuth return validation. Free Render
instance cold-start pending; next owner action is Google account selection/consent
in staging web login. Browser/native session and multi-user isolation not yet verified.
Phase 1 remains in progress.

Fresh staging readiness HTTP 200 confirmed after cold start. /auth/google returns
303 to staging Supabase with correct staging /auth/callback. In-app browser remains
on Render interstitial; fresh login tab redirect blocked by client. Owner handoff:
open https://aedrova-beta-staging.onrender.com/auth/google in Safari/normal browser,
select registered Google test user and complete consent; report signed in or error.
No authenticated login acceptance claimed. Native and multi-user tests still pending.

Owner login returned validation_failed / Unsupported provider: provider is not enabled.
Independent staging Supabase /auth/v1/settings check confirms external.google=false
for scvmvqlzcqhwrrsiahpj. Provider credentials were owner-reported saved, but enabling
Google was not persisted. Required now: staging Authentication > Sign In / Providers >
Google > Enable Sign in with Google > Save. Do not modify production. Staging login
and Phase 1 acceptance remain blocked until provider enablement and login validation.

## Staging Google login — owner confirmation

Owner enabled the staging Google provider and reports successfully signing in with
the registered test user. Independent /auth/v1/settings verification confirms
external.google=true for scvmvqlzcqhwrrsiahpj. Browser session/desktop handoff has
not been independently inspected; multi-user workspace isolation remains pending.
Next owner requirement: Google Cloud project aedrova-staging > Google Auth Platform
> Audience > Test users > Add users: add a second Google account under the owner's
control and Save. This enables two-user staging isolation validation. Do not send
credentials or use a production workspace. Phase 1 remains in progress; later phases
and public billing/download activation remain gated.

Owner reports second Google staging test user added. Started a staging-only hosted
isolation probe using existing native PKCE/loopback OAuth code (no production
endpoints, session tokens kept in memory). First browser login is awaiting owner
account selection. Subsequent second distinct login is explicitly paused. Probe
will create two disposable staging workspaces/messages, verify own reads and
bidirectional foreign workspace/channel/message/member reads and message writes
are denied, then unsend probe messages and archive workspaces. This does not
certify meeting media, AI context isolation or desktop UI handoff. Phase 1 remains
in progress until actual results and other release gates are recorded.

First real staging native OAuth callback succeeded (ACCOUNT_1_SIGNED_IN). The
probe then exited with EOFError because the background command has no interactive
stdin; local test session was signed out by cleanup. Replaced stdin pause with a
bounded local signal-file wait and restarted first login. Owner must sign in again
with the original test account before the second distinct account handoff. No
isolation tests have run yet; do not treat this runner issue as a Google failure.

Restarted first staging OAuth session verified successful and retained in memory.
Released bounded signal-file pause; second staging Google sign-in opened. Owner
must choose the second distinct registered test account (Use another account if
Google selects the original). Two-user isolation probes run after that callback;
results are not yet available. Phase 1 remains in progress.

## Hosted two-account isolation result

Both real staging Google OAuth sessions succeeded and authenticated distinct users.
Created two disposable staging workspaces with one probe message each. In both
directions, each account could read its own message, and reads of the other
workspace, channel, message and membership rows returned no data. Sending a message
into the other account's channel was rejected with PostgreSQL 42501. These
specific hosted isolation checks PASSED; this is not full AI-context/security
certification or desktop UI acceptance.

Cleanup failed because the local probe sent p_id rather than p_message to
unsend_message. Helper corrected; sessions were signed out. Two disposable staging
workspaces/messages remain (no production mutations); cleanup is outstanding.
Evidence: ignored work/staging/isolation-report.json, status
isolation_passed_cleanup_failed. Do not require repeated sign-ins solely to hide
this test-runner issue.

Remote CI run 38078880708 independently verified: PostgreSQL RLS, macOS desktop
and Ubuntu desktop passed; Windows desktop failed. Existing Unix-only fcntl
imports in agents/ledger.py and agents/retention.py remain the next baseline
engineering blocker. Phase 1 is still in progress; hosted merge protections,
Windows CI and desktop UI acceptance remain gates. No owner setup action is
required immediately while engineering addresses the Windows blocker.

## October 10 — portability fixes and deferred handoff

Owner requested independent completion without setup interruptions, with owner
actions saved for the end. Added `docs/phase-1-owner-handoff.md`.

Implemented native nonblocking Windows CRT byte-range leases alongside POSIX
flock; secure final-component opening rejects Windows reparse points and POSIX
symlinks before truncation. Locks are released when streams close and descriptors
are not inherited implicitly. Execution and retention no longer import fcntl on
Windows. Build-check receipts use the same safe file opener. Added real second-
process exclusion/reacquisition, symlink target-preservation, and error-classification
tests; all six new lease tests passed in the first actual Windows runner (the full
Windows job reached 675 passing tests rather than failing collection).

Remote run 38109927599 at e5d1499: PostgreSQL and macOS passed; Linux reported
one existing agent-feed visibility bug (730 passed); Windows reported 53 failures,
675 passed and six teardown errors. These are not silently skipped. Fixed the
agent-event stack switch so the transcript is visible when it contains rows, and
strengthened its existing layout regression to assert visibility. Also fixed Windows
agent timestamps (unsupported %- modifiers), explicit UTF-8 emoji catalog loading,
and GitHub login's synchronous FailedToStart race. The updated focused suites
passed 77 tests locally; full local baseline passed 731 tests before these follow-ups.
Source/secret checks and ordered SQL/RLS/optional-meeting checks passed.

Remaining Windows failures include Unix-only synthetic executable fixtures/runtime
pipe/process handling, POSIX permission assertions versus Windows ACL semantics,
conservative retention behavior on platforms without safe rmtree, and font/layout
differences. Windows distribution and full Phase 1 sign-off remain blocked; no
Windows installer or universal cross-platform readiness is claimed. Follow-up remote
CI is required for the final revision. Owner interventions stay deferred as requested.
No production merge/deployment, Phase 2, M14 or paid download activation performed.


## October 10 — final Phase 1 baseline verification

Hosted staging setup, separate Google OAuth and bidirectional two-account row
isolation are verified. Staging readiness returned 200, Google provider enabled,
and the removed Pulse route returned 404 during this final pass. Production and
public release/billing gates remain unchanged.

Native revision 2d93e52 fixes Windows bounded provider pipe reads, process-tree
lifetime containment with a kill-on-close job, portable synthetic subprocess helpers,
filesystem-specific permission preservation assertions, conservative retention
expectations and responsive connector/account/project layouts. No tests are skipped
to claim Windows readiness. Follow-up wraps the connector gallery banner and adds a
real spawned-command cancellation regression. Full updated local suite: 732 passed;
Ruff, tracked secret-pattern and compile checks passed. Ordered migration/RLS and
optional-meeting-order checks passed. Final remote evidence is recorded below when
complete; independent code completion does not waive the owner acceptance gates.

Owner handoff: docs/phase-1-owner-handoff.md. Required to close Phase 1: source
staging desktop login/workspace/sign-out acceptance and active main-branch PR/check
protections in both repositories. Two disposable isolation workspaces remain as
optional cleanup, not a failing isolation check. Windows CI is regression evidence,
not certification of installer signing, Windows ACL privacy or live provider sandbox
behavior; those remain later-phase gates. Obtain new approval for Phase 2 only after
reporting these results and outstanding owner actions.
