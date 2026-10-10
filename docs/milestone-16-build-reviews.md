# M16 — Traceable builds and shared review

Implementation and hosted shared-review acceptance complete. External publication/provider
activation acceptance remains deferred to M14/M18.

## What is implemented

- Local builds retain bounded, credential-filtered receipts from completed provider tool
  events. Passed/failed means an observed integer exit code; missing exits remain unverified.
- Review → Requirements & shared evidence links pinned, approved and fresh Product memory
  entries, source citations, acceptance criteria, actual changed-file diffs and command logs.
  No requirement is marked verified automatically. Human verification requires both a
  changed file and a passed linked check for the final file fingerprint.
- Share exact evidence persists a versioned record. Builds → Shared build reviews lets
  permitted teammates inspect it, comment, request changes or approve that exact version.
  A single-source share adds one generic notification in its channel. Multi-source records
  omit that notice to avoid revealing private work in a broader channel.
- Original-author updates and version checks reject stale writes. Stable identifiers make
  identical share/review retries idempotent. Prior-version decisions remain historical.
- Review never executes/applies/publishes code. Existing explicit local-apply and GitHub
  publication approvals remain. Successful delivery can add a fingerprint-matched receipt;
  a failed receipt sync never reruns publication. GitHub receipts are client-observed URLs,
  not server-verified proof of remote repository contents.
- RLS requires membership and access to every gathered source channel and every linked
  memory source. Withdrawal deletes derived evidence, notes and delivery receipts.
  Workspace switches, sign-out and permission changes close/clear cached review content.
- Local website preview copy and genuine light/dark widget captures use labelled sample
  data. Public availability is not advertised. Nothing pushed/deployed for M16.

## Validation

Full desktop regression and focused UI/security tests, actual PostgreSQL migration/RLS
acceptance suites and scoped Ruff checks are run before handoff. The real Codex probe
completed planning, file edits and independent tests in a disposable project. Claude's
runtime handshake passed; no paid Claude build is claimed. Screens were inspected in light,
dark and compact layouts. Rebuilt app signature verification and packaged smoke are required.
Exact final counts are recorded in docs/milestones.md after completion.

The PostgreSQL acceptance uses synthetic users/data and rolls back: outsider/private-source
isolation, peer review, unauthorized direct writes, retry idempotency, stale versions/sources,
invalid file/check links, wrong exits, post-check file edits, unsafe paths, delivery receipt
validation, source withdrawal and its cascading cleanup.

## Owner setup and live acceptance

In the existing Supabase project's SQL Editor, open a new query, paste the full contents of
`supabase/migrations/202610060003_build_reviews.sql`, and Run once. This migration depends on
both already-applied M15 migrations. Do not rerun old schema creation scripts.

The owner confirmed Success and hosted two-account acceptance passed on October 6.
`scripts/check_hosted_build_reviews.py` creates clearly labelled synthetic fixtures, uses
normal Google sessions in memory, checks real local file/check evidence through the hosted
service and removes the invited school member afterward. No secrets appear in the report.
`work/m16/hosted-build-review-check.json` records passed checks, including revocation while
records still existed. No additional SQL or credentials are required now.

## Limits and remaining external acceptance

- Evidence is observed on the local client, not an attestation system. Tests substantiate
  only what they actually exercise; reviewer verification is a human claim.
- CLI versions that omit exit codes (including some Claude responses) show unverified.
  Provider text saying “passed” does not turn into a green check.
- Up to 100 command receipts, 200 changed files, 50 criteria; logs/diffs have explicit
  truncation markers. Cached logs are private local artifacts, not full chat archives.
- Recovered pre-M16 runs without a pinned memory snapshot cannot be shared as traceable
  evidence. Start a new build. No stale source snapshot is reconstructed by guessing.
- Sharing is conservative: all channels gathered for the build must be readable by a peer,
  even if the final diff seems to concern only one channel.
- Hosted two-account acceptance passed. An owner-approved real GitHub test PR,
  paid Claude/managed access and final release/provider acceptance remain external gates;
  unavailable activation tests stay at remaining M14/M18 under the approved ordering.
- M17 continuous team delivery is a separate task, pending explicit owner approval.
