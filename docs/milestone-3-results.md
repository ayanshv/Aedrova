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
