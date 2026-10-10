# Final-Beta Phase 1 — release baseline

October 10, 2026. Phase 1 authorized by the owner. Later phases remain gated.
Status: source baseline prepared; hosted staging installation and remote CI evidence
remain required before passing the phase. M14/public paid downloads remain deferred.

## Frozen first-release scope and evidence

| Area | Implemented source | Current acceptance boundary |
| --- | --- | --- |
| Account/workspace | Google browser return, profiles, organizations, invitations, roles, channel membership, workspace archive | New isolated staging Google login and multi-user acceptance pending |
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
| Staging | Owner-created `scvmvqlzcqhwrrsiahpj` (Aedrova Staging, healthy, Canada Central, free/NANO); 23 app migrations now installed; tables verified in the hosted Table Editor | Explicit public profile + separate `work/staging/app.ini`; separate HTTPS server/OAuth/provider credentials still needed |
| Production | Existing `cpelagtufyocepnqcqqd`; customer/waitlist data not copied or migrated | Existing aedrova.com and connector origin; checkout/download gates unchanged |

`scripts/run_staging.py` rejects known production endpoints and secret keys in
public profiles. Backend explicit staging requires secure HTTPS and a separate
Supabase database, rejects production origin/project, live Stripe secrets and
checkout/download/development-AI bypass. The restricted database username is
validated against the chosen Supabase project rather than hardcoded to production.
Local secret files remain ignored; inspected files have mode 0600. No values are
recorded here. No staging secret or provider credential has been configured yet.
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
