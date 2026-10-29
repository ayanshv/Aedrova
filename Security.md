# Aedrova security policy

Last reviewed: October 24, 2026. Scope: this desktop repository and the accompanying
`Aedrova_site` backend. This is an engineering policy, not a security certification,
legal guarantee, or statement that every source change is deployed.

## Reporting a vulnerability

Email **contact@aedrova.com** with subject **Security report — Aedrova**. Include the
affected version/environment, minimum reproduction steps, expected and actual results,
and likely impact. Use synthetic accounts and redact tokens, customer data and passwords.
Do not post an exploit or sensitive evidence in a public issue. Ask for a secure transfer
method before sending sensitive material; no dedicated encrypted reporting channel is
currently documented. Response times are not guaranteed and no paid bounty is promised.

Report suspected account compromise promptly. Disconnect the affected integration and
revoke its grant at the provider when safe. Do not send credentials to support.

## Authorized testing boundaries

Test only systems/accounts you own or have explicit permission to assess. Stop after
minimal proof of unauthorized access; do not extract another user's information. No
production denial of service, credential attacks, social engineering, payment activity,
or destructive testing. This policy does not grant permission to test third-party
providers or establish a legal safe-harbor agreement.

## Security requirements

- Enforce identity and resource authorization on the server and in database policies.
  Never trust a client-supplied workspace, role, price, budget or subscription state.
- Keep provider secrets, database credentials and privileged Supabase keys outside
  desktop bundles, browser code, Git, prompts and telemetry. Public Supabase keys are
  identifiers whose safety depends on effective row-level security (RLS).
- Use HTTPS for hosted traffic. The native OAuth callback is a narrowly bound loopback
  HTTP exception, not permission for an HTTP production callback.
- Validate size, schema, type, origin and permissions before expensive work. Use
  parameterized SQL; validation and keyword filtering do not replace parameters.
- Scope external access to the provider's approved permissions and selected resources.
  Creating a Bud is not authorization to access an entire account or bypass consent.
- Treat chats, files, transcripts, connectors and generated code as untrusted evidence.
  Require review/approval before applying original-folder changes or publishing.
- Fail closed on unavailable authorization, exhausted budgets and uncertain eligibility.
  No silent fallback to an unmetered model or broader credential.
- Keep optional context, meeting processing and connector access understandable and
  revocable. Do not promise deletion from a provider after data has already been sent.

## Vulnerability response

The release owner assigns an incident lead and records detection time, affected
versions, exposure, decisions and evidence in restricted storage. Do not store incident
secrets in this repository.

1. Triage reproducibility and impact. Treat active cross-workspace disclosure,
   credential compromise and unauthorized spending as release-blocking incidents.
2. Contain: disable affected feature admission, revoke compromised grants/sessions,
   restrict access and stop further data delivery. Preserve minimal sanitized evidence.
3. Rotate exposed credentials at their issuing provider and update private deployment
   settings. Deleting a key from a commit does not revoke it; assess Git history,
   artifacts, logs and caches as separate exposure locations.
4. Repair the root cause, add a meaningful regression test and verify unauthorized
   requests fail while legitimate workflows still work.
5. Deploy the reviewed fix to staging, validate, then authorize production rollout or
   rollback. Confirm active releases and hosted configuration actually contain the fix.
6. Determine notification obligations with qualified counsel using the real facts,
   jurisdictions and contracts. Do not invent a universal notification deadline.
7. Document recovery, residual risk, owners and follow-up dates. Test restoration before
   declaring recovery; retain evidence only for the approved incident purpose.

## Release policy and evidence

There is no published security-support lifetime for older installers. Do not imply
old downloads are patched because main is fixed. The release owner must inventory
available versions, publish update instructions and remove unsafe releases when needed.

[Authentication](Auth.md), [data security](Data%20Security.md),
[threat model](Threat%20Model.md) and [release checklist](Security%20Checklist.md)
form this policy set. Existing audits in `docs/` are dated historical evidence, not
permanent attestations. The checklist controls new release decisions; existing owner
approval gates in [milestones](docs/milestones.md) still apply.
