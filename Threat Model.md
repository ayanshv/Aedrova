# Aedrova threat model

Reviewed: October 24, 2026. Revisit when providers, permissions, endpoints, billing,
meeting infrastructure, context routing or distribution mechanisms change. This is a
source-informed model, not an independent penetration-test report.

## Scope, assets and trust boundaries

Protect account sessions; private workspace/channel/DM/Bud content; connector grants;
source repositories and original project folders; model and meeting budgets; verified
billing entitlements; uploaded media; installer/update integrity; recovery keys/backups.

Boundaries: browser → hosted app; desktop → Supabase/backend; user token → RLS/RPC;
backend → private ledger/storage; backend → OAuth/AI/payment providers; untrusted context
→ agent instructions/tools; isolated checkout → original folder/GitHub; build pipeline
→ signed installer/update; privileged operator → production configuration.

Assume malicious outsiders, authenticated tenants, compromised members, malicious files
and connected content, replayed/stolen credentials, compromised dependencies and operator
mistakes. Do not assume a logged-in teammate or provider document is trustworthy. An
attacker controlling the user's OS can defeat many desktop safeguards.

## Priority threats and acceptance evidence

### Critical: cross-tenant or private-channel disclosure

Attack: forge workspace/object IDs, reuse a signed URL, fetch AI context or Bud history
through an otherwise authorized endpoint. Controls: user-token authorization, RLS/RPC,
private resource scope and membership checks. Evidence: `identity/service.py` under
`src/aedrova/`, migrations and database tests. Release gate: two real staging accounts
cannot read/write each other's private resources, including cached/realtime paths.

### Critical: stolen credentials and OAuth account confusion

Attack: logged callback codes, malicious redirects, replayed state, exposed bundles or
wrong-user grants. Controls: PKCE/native random callback path; hosted OAuth binding;
private credential storage; sanitized errors and secret scanning. Evidence: OAuth tests,
`security/credentials.py`, backend OAuth modules. Gate: denied/expired/replayed/wrong-user
flows fail without storing a grant. Provider revocation must prevent further reads.
Residual risk: pattern scans miss unknown formats; OS/dashboard compromise remains.

### Critical: prompt injection and unsafe tool execution

Attack: repository/chat/transcript tells an agent to exfiltrate secrets, escape a checkout,
publish code or claim tests passed. Controls: permission-filtered context, untrusted-source
instructions, isolated checkout, restricted subprocess environment, tool permissions,
deadlines and review/approval for applying/publishing. Evidence: agent runtime/checkout
modules and `scripts/check_agent_boundaries.py`. Gate: canary files/secrets and network
probes stay protected in each supported runtime/version. Prompt instructions alone are
not isolation, and reviewed code can still contain vulnerabilities.

### High: unauthorized spend or forged billing state

Attack: concurrent requests overspend a shared allowance, client chooses a paid plan,
retries duplicate checkout, forged/out-of-order webhooks restore access. Controls:
backend workspace authority, atomic usage admission, scoped gateway credentials, signed
Stripe webhooks and deduplication. The sibling checkout implementation also snapshots
retry parameters and passes idempotency keys to Stripe; verify its release/deployment
before relying on it. Evidence: backend billing/gateway/store tests. Gate: retries,
concurrency, exhaustion, cancellations/refunds and failures preserve correct entitlements
and cannot create duplicate charges. No real payment is authorized by this document.

### High: injection, parser abuse and resource exhaustion

Attack: SQL input, oversized/nested JSON, hostile uploads, polling floods or forged
forwarded addresses. Controls: bound SQL parameters, bounded schema/body/metadata parsing,
server file verification, DB-backed traffic admission and task/time/cost limits.
Evidence: backend boundaries/traffic/file modules and endpoint tests. Gate: oversized,
malformed and concurrent requests reject predictably without provider spend or private
error leakage. Trusted proxy configuration and distributed limits require hosted tests.
File validation is not a comprehensive antivirus guarantee.

### High: meeting and media privacy failure

Attack: unauthorized join, recording without understood consent, stale leases, transcript
context after withdrawal, private recording links accessible to others. Controls:
authorized leases/tokens, private uploads, review/context-consent and scoped retrieval.
Gate: two-device join/leave/rejoin, revoked participant, recording indicators, transcript
review, withdrawal and download-isolation tests. Do not advertise end-to-end encryption,
translation or recording modes that have not been implemented and verified.

### High: supply-chain or release compromise

Attack: malicious dependency, leaked CI secret, substituted installer/update or unsigned
binary. Controls: dependency locks/audits, release secret scans, repository protections,
reviewed packaging and required signing verification. Gate: fresh signed/notarized Mac
and appropriately signed Windows installers pass clean-machine installation, login,
permissions, update and uninstall tests. CI green alone is not release acceptance.

### High: outage, key loss and destructive recovery

Attack/failure: backend asleep/unavailable, database failure, lost encryption key, leaked
backup or restore resurrecting revoked access. Controls: fail-closed admission, private
errors and bounded requests; maintenance/retention code. Gate: monitoring alerts reach
an operator; isolated restoration succeeds with documented recovery keys and reapplied
revocations/deletions. A branded error page is not availability or incident detection.

## Risk decisions

Release owner records each open finding with severity, reproduction, affected SHA and
environment, responsible person, remediation, test evidence and decision date. Active
critical issues block launch; high-impact authorization/spend/release risks block their
features until fixed or explicitly disabled. Do not silently relabel a failed test as
accepted risk. Independent review, provider approval, operational recovery and live
acceptance remain open unless separately evidenced in the release checklist.

For incident handling see [Security.md](Security.md); for data limitations see
[Data Security.md](Data%20Security.md). Historical audits are supporting evidence only.
