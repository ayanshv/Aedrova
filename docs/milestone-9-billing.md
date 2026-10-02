# Milestone 9 desktop connection

The separate Python service is in `/Users/ayanshvarma/Documents/Aedrova_site`.
Its implementation/test record is `docs/milestone-9.md`; exact required owner actions are
`docs/owner-setup.md`. Live activation is pending those steps, not implied by local tests.

For development, `AEDROVA_MANAGED_ORIGIN=http://127.0.0.1:8090` selects a local managed service.
Public app builds bundle its HTTPS origin, the public Supabase connection, Codex CLI 0.155.1
with license/notices and the pinned Claude runtime. Packaged apps ignore ambient origin overrides.
Stripe keys, provider keys and billing database credentials are not packaged or requested from
customers. Context collection binds the signed-in account/workspace to an opaque two-hour run
credential; every inference rechecks live membership and budgets. Credentials are in memory,
provider subprocess environments and encrypted short-lived backend sessions, not command arguments.

Managed Codex uses a private temporary CODEX_HOME and explicit custom-provider overrides after
`exec`, preserving sandbox/file-review boundaries. Claude uses the existing SDK tool hooks with
its base URL and scoped key replaced. No provider-login fallback runs when managed access fails.
Settings adds workspace balances and website billing access, with stale-account checks.
Tab mention completion is handled before Qt focus traversal. Existing custom agent names remain.

294 Python tests, existing embedded PostgreSQL/RLS suites, both installed runtime loopback
file-write probes, package/signature/baseline secret checks and preview smoke tests pass.
The preview installer is ad-hoc signed and unavailable for public checkout/download. Developer ID
signing/notarization, staged live Stripe/OAuth/provider acceptance, real PostgreSQL concurrency,
cost measurement and clean-Mac testing require owner setup. Milestone 10 remains unstarted.
