# Security release checklist

Created: October 24, 2026. Duplicate this checklist into a dated release record for each
candidate. An unchecked item is unverified, not necessarily missing implementation.
A source control marked below does not assert production configuration or live acceptance.
No payments, new permissions or production activation are authorized by this document.

## Release record — complete before approval

- [ ] Record app SHA, backend SHA, migration head, runtime/dependency versions, deployed
      services, feature flags, release owner, test date and evidence location.
- [ ] Inventory every advertised connector/feature as public-ready, restricted beta,
      disabled or unsupported. Remove unsupported launch claims and buttons.
- [ ] Track remaining findings with owner and due date; disable affected high-risk features.

## Source controls inspected for this policy set

- [x] Desktop sessions are in memory; native Google login uses PKCE and bounded loopback
      callbacks (`src/aedrova/identity/{service,oauth}.py`).
- [x] Database migrations and local RLS test infrastructure exist (`supabase/migrations/`,
      `scripts/test_database.py`). Deployment and tenant acceptance are separate gates.
- [x] Agent isolation, secret-pattern checks, local ledger and conservative retention
      mechanisms exist (`src/aedrova/agents/`, `src/aedrova/security/credentials.py`).
- [x] Backend code includes request limits, DB-backed traffic admission, CSRF/session
      checks, encrypted private payloads, signed Stripe webhook validation and private
      upload verification. Inspection does not prove hosted settings or active versions.
- [x] Reporting, incident response, auth boundaries, lifecycle and threat requirements
      are documented in the five root security documents.

## Authentication, access and connectors — engineering + release owner

- [ ] Run current OAuth, permission and RLS regression suites; apply reviewed migrations
      to staging and verify the actual database policy/function definitions.
- [ ] Complete real two-account workspace/private-channel/Bud DM/file isolation checks.
      Test removed users and expired/stolen-session replay without exposing real data.
- [ ] Verify logout, CSRF, origin/cookie settings, private no-store and sanitized errors
      on enabled hosted endpoints, including early middleware errors.
- [ ] For EACH advertised provider: fresh login → consent → bound callback → real scoped
      read → success UI; then denial, expiry, refresh failure, disconnect and revocation.
- [ ] Confirm callback allowlists and production/public provider approval. Tester/sandbox
      success does not authorize all customers. No token entry required for advertised
      login-only flows; clearly disable providers whose setup is incomplete.
- [ ] Verify supported OS vault behavior and ensure no plaintext fallback on Windows.

## API, files and agent execution — engineering

- [ ] Inventory routes with the backend endpoint audit; test schema-valid unauthenticated
      requests, wrong-resource authority and every mutating permission boundary.
- [ ] Verify bound SQL values and allowlisted dynamic identifiers in changed query paths.
- [ ] Test body/metadata limits, nested JSON, invalid formats, spoofed MIME, oversized
      files, unauthorized preview/download, cancellation and orphan cleanup.
- [ ] Verify DB-backed admission across multiple hosted workers and trusted ingress IPs.
      Current coarse login-start policy is 10 requests/300 seconds per IP/category;
      callback is 30/300. Tune with shared-NAT measurements, not arbitrary bypasses.
- [ ] Test agent filesystem/network/environment canaries and prompt injection in files,
      chats and transcripts for every bundled runtime version. Verify apply/publish gates.
- [ ] Verify concurrent allowance reservations, uncertain charges, deadlines/cancellation,
      retries and no silent provider fallback; check global spending alerts/kill switch.
- [ ] Verify meeting participant controls, consent, transcript review/withdrawal and
      media privacy using two devices. Disabled infrastructure must explain next steps.

## Data and operations — release owner + engineering

- [ ] Inventory production secrets and access; rotate any exposed value at its issuer.
      Scan tracked source, relevant Git history, logs and packaged artifacts separately.
- [ ] Confirm stable recoverable encryption keys, restricted backend DB role and least
      privilege for dashboards/CI; enable available operator MFA and review access.
- [ ] Assign approved retention durations and schedule/observe hosted cleanup workers.
- [ ] Test verified deletion/export/disconnect requests and cache invalidation; reconcile
      backup/provider limits with published disclosures.
- [ ] Configure alerts for errors, auth abuse, webhook/queue failures and AI expenditure;
      trigger a safe synthetic alert and verify delivery to the responsible person.
- [ ] Complete isolated backup restore and key-recovery drill; record measured recovery
      times, revocation/deletion reconciliation and rollback steps.
- [ ] Obtain independent security review of auth/RLS, tokens, agents and billing. Resolve
      critical/high release findings; retain a dated review record without customer data.

## Billing, legal and release — required before commercial activation

- [ ] Owner completes Stripe identity/bank/tax configuration directly in Stripe and
      personally approves any payment. Do not paste credentials or bank details in chat.
- [ ] Test monthly/annual prices, workspace coverage, checkout response-loss retries,
      Stripe idempotency keys, webhook duplication/order, failed payment, cancellation,
      refund and entitlement transitions in test mode. Confirm deployed backend SHA.
- [ ] Finalize actual operator/business disclosures and qualified legal review of
      Privacy/Terms/refunds/cookies/consent. Do not claim Aedrova Inc. before registration;
      incorporation is a separate business decision, not a security-test substitute.
- [ ] Owner confirms Apple membership/signing access and Windows signing arrangements
      in their respective accounts. Never transmit signing secrets through chat.
- [ ] Produce verified installers; test clean Mac/Windows machines, first-run onboarding,
      permissions, connector return flow, updates, uninstall and account recovery.
- [ ] Match website screenshots, pricing, support, download URLs and release notes to
      the actual candidate. Obtain explicit final production/download activation approval.

## Reproducible local checks

Run from the app repository (Node must be installed for the PostgreSQL harness):

```sh
uv run ruff check .
uv run pytest
uv run python scripts/check_release_secrets.py --tracked
uv run python scripts/test_database.py --node /absolute/path/to/node
```

From the sibling `Aedrova_site` repository:

```sh
uv run ruff check .
uv run pytest
uv run python -m scripts.audit_endpoints
```

Use the dependency-audit procedure in each repository's CI/lockfile tooling. Preserve
sanitized test outputs with candidate SHA/environment; do not publish private auth
sessions or raw provider output. The prior app main merge had 924 passing tests; that
is historical evidence, not a fresh test result for every future release.

## Go/no-go

Launch requires passing applicable gates with evidence. If a gate cannot be completed,
keep the corresponding feature unavailable and make the remaining scope explicit.
Record approver, exact artifact/deployment versions, rollback target and outstanding
nonblocking issues. Documents and attractive error screens cannot replace live testing.
