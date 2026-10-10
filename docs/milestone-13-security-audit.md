# M13 security audit — October 3, 2026

Follow-up: M13A now implements storage quota/orphan cleanup, conservative local retention
and Claude direct-network denial plus shell deadlines. See `milestone-13a-release-hardening.md`
for the current policy, verification and deferred hosted setup. The findings below record
the earlier M13 audit; they do not imply those M13A changes are already deployed.

Local audit and remediation are complete. This is not public-launch approval or a claim
that the application is immune to attack. M13B and M14 have not started. Changes remain
local: the live website and previously built app do not contain these new fixes.

## Scope and evidence

Reviewed both repositories' first-party implementation, configuration and release
boundaries: desktop Google/PKCE loopback authentication and session lifecycle; Supabase
workspace/channel/DM/file RLS and scoped context; project snapshots and both coding
runtimes; immutable local/GitHub review, recovery and static preview; installer/update
verification; website OAuth/cookies/CSRF/validation; waitlist and encrypted private ledger;
Stripe checkout/webhooks, managed model gateway, allowances/concurrency/rate limits;
meeting tokens, guarded leases, consent/transcript review, withdrawal and speech ingestion;
Docker/CI and release flags. Existing production-readiness findings were carried forward.

Checks used synthetic users, projects and credentials. Installed-agent protocol fixtures
used a loopback model server, not paid provider calls. No customer conversations or raw
audio were sent to a provider. No credential, database migration, purchase, public build,
GitHub publication or hosted environment was changed. No first-party backdoor was found
in the reviewed source; source review cannot establish their absolute absence.

## Findings fixed locally

1. **High: coding sandbox reads were broader than the selected project.** Codex now uses
   a filesystem allowlist for its checkout, selected context, required system/runtime
   files, a read-only planning profile and disabled tool networking. Shells have a fixed
   credential-free PATH, no login profile and no inherited provider environment. Personal
   hooks, plugins, apps, browser and subagents are disabled. The resolved launcher fixes
   compatibility with the restrictive profile. Claude denies personal home/volume/temp
   reads except the exact checkout/context, denies protected config/Git writes, disables
   unsandboxed execution and scrubs provider credentials from Bash subprocesses. Existing
   explicit tool approvals remain. System dependencies are permitted reads; this is not
   a VM or a promise that every operating-system path is invisible.
2. **High: hardcoded credentials in ordinary project/chat files could enter AI context.**
   A shared scanner rejects recognized private keys, provider/GitHub/Stripe/Google/AWS and
   Supabase secret/service-role formats before snapshot or context delivery. Credential
   directories and additional auth/config files are excluded. Raw task/plan text is also
   checked before execution. GitHub publication and packaged-source checks use the same
   rules. Findings report rule/path information without credential values. Detection is
   pattern-based: arbitrary passwords, encoded secrets and unknown formats are not proven
   absent; owners must still keep credentials out of project code and conversation.
3. **Medium: vulnerable website dependency.** Installed cryptography 46.0.7 had seven
   advisory entries representing four unique identifiers. Updated the requirement and
   lockfile to 50.0.2. Both installed Python environments now have no known vulnerabilities
   in pip-audit. This does not imply all old advisories were exploitable through Aedrova's
   Fernet usage. Primary advisory reference:
   [pyca cryptography GHSA-537c-gmf6-5ccf](https://github.com/pyca/cryptography/security/advisories/GHSA-537c-gmf6-5ccf).
4. **Medium: local preview lacked request-origin/Host protection.** GET and HEAD require
   the exact bound loopback Host and reject a foreign Origin. Dotfiles are refused;
   existing static-only snapshot, restrictive CSP and no directory listing remain.
5. **Medium: validation responses could reflect private invalid input.** FastAPI request
   validation now returns a generic 422 rather than including submitted audio/tokens or
   other invalid values in the response. Regression coverage verifies non-disclosure.
6. **Medium: parser/provider resource bounds.** Model-content inspection is iterative and
   rejects excessive nesting/item counts before provider spend. Speech replies request
   uncompressed encoding, check size before retaining bytes and have a monotonic deadline
   in addition to shorter network timeouts. Failed/late chunks release their reservation,
   discard transcript text and do not automatically retry.

## Verification

- **452 desktop tests and 216 website/backend tests pass.** Ruff passes in both repos.
- **All 21 embedded PostgreSQL migration/RLS scripts pass**, including meeting consent,
  review, scoped context, privacy withdrawal and speech-replay tests. A separate private
  billing/meeting-schema test passes: restricted website role cannot read public chat,
  create other schemas or expose its private tables to public/authenticated/service roles;
  lease reserve/rejoin checks pass. These are local PostgreSQL fixtures, not hosted races.
- Both installed runtimes complete normal synthetic edits. Adversarial shell commands
  cannot read/write the synthetic outside-project sentinel or recover provider tokens
  via their environment/parent-process probe. Actual Codex planning permits reads and
  refuses writes. Codex cannot reach the loopback network canary.
- Claude's forbidden-network command reaches no canary but waits in the runtime proxy
  permission path until the fixture's 30-second cancellation. This is **not** a successful
  normal-tool run or proof of an immediate denial response. Keep cancellation/deadlines;
  validate/improve this behavior before advertising uninterrupted autonomous builds.
- Credential-pattern scans find no matches across **179 desktop and 98 website working
  files** (including untracked first-party changes), or **256 desktop and 166 website
  reachable historical Git blobs**. Ignored local environment/work files are not public
  artifacts. Current source/resources and the previously built app pass the release leak
  scanner; that old bundle does not validate delivery of the new runtime code.
- Both dependency scans are clean after the cryptography update. Reports and runtime
  fixture logs are private local files under `work/m13` and `work/m13-dependency-audit*`.
- Read-only live probes: `/`, `/plans`, `/waitlist`, `/health`, `/health/ready` return 200
  after warm-up; nosniff, frame denial, CSP and HSTS are present. Checkout and managed AI
  remain disabled. Initial home/health requests timed out at 12 seconds, consistent with
  a cold/free instance; this is not a performance SLA or a write-path acceptance test.

## Remaining gates — not waived by M13

**Before any public app/paid beta:** rebuild the app from audited source; publish the
website security dependency patch; run Linux Docker/CI validation (Docker is unavailable
on this Mac); validate signed/notarized installers and real update delivery. Revalidate
runtime sandbox behavior whenever bundled Codex or Claude SDK/CLI versions change. The
installed-runtime result applies to this Mac and these versions, not all installations.

**Engineering before larger/public release:** storage still lacks team aggregate quotas
and an orphan-object cleanup worker. Local build/context snapshots are private OS files,
not application-encrypted archives, and need an explicit retention/cleanup policy. Safe
ledger archival and supervised maintenance remain necessary. High-volume metadata polling,
realtime member fan-out and workspace cursor serialization require measured workloads.
These preexisting items are tracked in the website's `docs/production-readiness-audit.md`.

**M14 owner/hosted acceptance:** verify every required migration on hosted Supabase (local
tests do not prove it ran there); approve/configure hosted API, independent meeting guard,
rate/proxy budgets, alerts, backups and a restore drill; enter server-only Stripe/provider/
LiveKit/speech secrets privately; test real checkout/webhooks, billing races, hard usage
limits, revocation/outages and representative load; perform two-Mac media/consent/privacy
validation; supply Apple Developer signing/notarization for public distribution. No new
secret, purchase, device or SQL action is requested now; these remain deferred to M14.

Untrusted team evidence can influence generated code even with scoped retrieval and OS
sandboxing. Review/test changes before applying or publishing. Withdrawing context stops
future authorization; it cannot retract data already delivered to a provider. Legal
retention/provider agreements and backup policies need owner review before activation.

## Next task — revised by owner after audit

M13A: implement the remaining storage quotas/orphan cleanup, local snapshot/context
retention and cleanup, and Claude forbidden-network wait handling. Obtain permission
before starting implementation; preserve existing UI and release gates. Follow with M14
owner setup, hosted acceptance and deployment/release activation.

The owner moved M13B, the entire-codebase walkthrough, until after the entire application
is complete and deployed. Obtain permission again at that point; do not start it now.
