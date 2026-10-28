# Data security and lifecycle

Last reviewed: October 24, 2026. Internal engineering requirements; public Privacy and
Terms disclosures must match actual operations and the real legal operator. Use the
brand Aedrova; do not invent an incorporated entity or completed compliance certification.

## Data classes and permitted use

- **Public:** published product information and approved brand assets. No secrets or
  real private customer content in screenshots, demos or public test fixtures.
- **Account and workspace:** identity, memberships, roles, preferences and billing
  references. Access follows identity and workspace authority, not guessed identifiers.
- **Private content:** chat/DM history, files, voice recordings, transcripts, Bud memory,
  repository context and generated work. Retrieve only for authorized, disclosed use.
- **Restricted credentials:** OAuth grants, refresh tokens, provider keys, encryption
  keys, database passwords and webhook secrets. Keep server-side or in an explicitly
  supported OS vault. Never put these in prompts, frontend code or normal logs.
- **Operational evidence:** usage events, audit records and incident evidence. Minimize
  fields and access; avoid storing raw prompts or bearer tokens for debugging.

## Data flows and boundaries

The desktop accesses Supabase with user authority. Selected context can be sent to the
configured AI path after authorization/admission. Managed AI passes through the backend
for workspace budget and scope enforcement. Connector grants are exchanged/stored by
the appropriate backend path, and provider APIs supply authorized resource data.
Uploads use private storage and server verification before publication. Meeting/voice
capture and transcript approval are distinct from permission to use content as AI context.

A private channel is not made public by mentioning Aedrova. A provider receives whatever
context is actually sent: neither RLS nor later withdrawal retracts an earlier delivery.
Review provider terms, retention and subprocessors before enabling each production path.

## Encryption and key custody

Require HTTPS for hosted API/provider/storage transport. Confirm managed database and
object-storage encryption/backup settings in the host, rather than inferring them from
SDK use. The backend `store.py` uses Fernet for selected private payloads, including
credential/session-related records. This is application encryption of selected fields,
not end-to-end encryption of all messages or encryption of every database column.

Production must use a stable private encryption key with controlled recovery access.
Losing it can make encrypted data unreadable. Store keys separately from database
exports, restrict dashboard access and rehearse rotation with existing ciphertext before
changing production keys. Do not regenerate a key on every deployment. Never commit real
keys or recovery materials; use secret settings and least-privilege operator access.

Local build snapshots, SQLite ledgers and context files rely on OS permissions; do not
claim application-level encrypted storage. Require device lock, supported OS updates and
full-disk encryption for operator machines. Local malware remains outside these controls.

## Upload, query and execution protections

Backend `file_policy.py` and `uploads.py` enforce accepted formats, size and verification;
private storage publication must not precede server verification. Do not trust filenames,
extensions, client MIME, preview availability or client “verified” flags. Preserve explicit
Send intent; an instant local preview is not successful upload confirmation. Test oversized,
mismatched, truncated and unauthorized objects, as well as cancellation/orphan cleanup.
These checks are not a claim that comprehensive malware scanning is deployed.

Use SQLAlchemy bound parameters for values. Never interpolate request input into SQL;
allowlist any unavoidable dynamic identifiers. Apply authorization independently of SQL
injection prevention. Reject malformed/oversized bodies before parsing or provider calls.

Builds run in isolated copies with restricted environment/tool permissions. Secret-pattern
scanning reduces accidental leakage but cannot recognize every password or encoded key.
Review generated diffs and test evidence before applying or publishing changes.

## Retention, deletion and backups

Local policy in `src/aedrova/agents/retention.py` allows idle context cleanup after 24 hours
and conservative snapshot eligibility after 30 days. Edited work, active leases and
recovery/delivery evidence are preserved. These are eligibility rules with bounded
maintenance passes, not promises that all local data disappears at a fixed deadline.

Hosted retention depends on `storage_cleanup.py`, `maintenance.py`, SQL rules and an
actually scheduled worker. Before launch inventory each data class, location, purpose,
approved duration, deletion mechanism and exceptions. Record the real schedule and
operator; do not publish an invented universal retention period.

For deletion requests: verify identity/authority; identify workspace versus personal
scope; revoke future access; delete eligible active records and objects; record minimum
completion evidence; explain legal/accounting holds and provider/backup limitations.
Test deletion of derived context, cached previews and orphan uploads. Do not delete a
shared team's data merely because one member requests personal account deletion.

Backups require access control, documented retention and tested restoration into an
isolated environment. Prevent a restore from silently reactivating revoked credentials
or restoring deleted data to active use: reapply deletion/revocation records before
reopening access. Backup availability, RPO and RTO remain unverified until a dated drill.

## Logging, caching and external sharing

Exclude Authorization/Cookie headers, OAuth codes, secrets and raw private request
bodies from logs. Return sanitized errors; access-restricted logs are still sensitive.
Scope cached private data to account/workspace/resource and invalidate it after removal,
logout or permission change. Never use a shared CDN cache for authenticated responses.

Document external recipients, transmitted fields, location/retention settings and the
feature's disable/disconnect control. Production customer data must not be copied into
staging for convenience. Use synthetic fixtures and separate staging secrets/databases.

Evidence: [Auth.md](Auth.md), [Threat Model.md](Threat%20Model.md),
[Security Checklist.md](Security%20Checklist.md), `tests/test_retention.py` and the
backend's `tests/test_upload_verification.py` and `tests/test_checklist_security.py`.
