# Milestone 3 — local implementation results

Status: IN PROGRESS. Local implementation and verification complete; hosted Supabase
integration has not been run. Milestone 4 remains gated.

Implemented:
- Official Supabase Python SDK, email/password login/signup and optional signup-code verification.
- Memory-only sessions; automatic expiry refresh through the SDK before authenticated actions.
- Background account operations, sanitized errors, cleared stale rosters and invitation codes.
- Account menu with connected workspace/channel creation, invitation acceptance/revocation,
  membership roles/removal and explicit private/guest channel grants.
- PostgreSQL migration with RLS, grants, narrow RPCs, protected invitation hashes, confirmed-email
  redemption and serialized membership mutations.
- Private Storage read policies and private server-broadcast subscription policies.

Evidence:
- 79 Python tests passed in 15.24 seconds, including SDK mocked-HTTP token refresh and UI tests.
- 47 PostgreSQL authorization assertions passed using PGlite 0.5.8, including cross-tenant
  denies, role escalation, private admin access, invitation replay/expiry/revocation, inviter
  demotion, storage paths and membership revocation. This is an embedded real PostgreSQL
  engine with test facsimiles of Supabase's auth/storage/realtime schemas.
- Ruff lint/format and git whitespace checks passed.
- Account screenshots inspected in light and dark; a scroll-area theme bug was corrected.
- Rebuilt Mac app passed deep/strict signature verification and launched its account screen
  from /tmp with no logged errors. Package remains locally ad-hoc signed.

Required before completion:
- Provision/connect a development Supabase project and apply the migration.
- Test actual email confirmation, login/refresh/logout and workspace operations.
- Execute negative REST and Storage HTTP checks, plus real private Realtime subscription checks.
- Keep public Realtime disabled. Existing socket authorization caching/revocation must be
  validated before shared communication ships; a SQL policy test does not prove disconnects.

Public configuration may be saved; passwords and session tokens are not. No hosted resources
were changed. Main chat remains explicit local sample data. See milestone-3-setup.md.

## Google-only login and agent onboarding revision

Customer login contains no connection, email or password fields. Backend configuration is
embedded by the build; frozen apps ignore backend overrides from environment or QSettings.
Normal launch opens login; `--demo` is explicitly local sample data only.

Google OAuth uses the system browser and PKCE, a random loopback path, strict Host checks,
query limits, timeout/cancellation (including partial HTTP requests) and sanitized output.
Onboarding atomically saves the workspace, team-wide agent nickname and preferred provider.
RLS allows workspace members to read that preference; only owners/admins can change it.
Nicknames do not alter app branding, grant capabilities, or become executable instructions.

Both SQL suites passed in embedded PostgreSQL, including invalid-onboarding rollback,
unauthorized preference edits, cross-tenant reads and revocation. Python test totals and
packaged launch evidence are recorded below after final verification.

Dependency audit: 69 installed packages assessed, no known advisories returned. The local
Aedrova package was skipped by the advisory database and is covered by first-party tests.
A baseline release check detects common embedded credential formats (including service-role
JWTs) and environment-file inclusion. Packaged first-party assets are explicitly allowlisted.
This is not proof that all vulnerabilities or hidden privileged paths have been excluded.

A dedicated milestone 4A now gates the first executable agent milestone. See the explicit
owner checklist in `owner-actions-google-onboarding.md`. Live Google/Supabase validation
has not been performed; milestone 3 remains in progress.

Final local verification: **96 Python tests passed in 15.38 seconds**. Both embedded
PostgreSQL suites passed. Ruff lint/format, packaged-resource secret checks and deep/strict
app-signature verification passed. The rebuilt app opened its Google-only account screen
from /tmp with no logged errors. Light-theme onboarding and login screenshots were reviewed.
