# Claude staging activation — October 24, 2026

Owner explicitly approved transferring the existing Anthropic API key into the
private Render settings of aedrova-beta-staging, selecting config/models.beta.json
and deploying on the existing free instance. Production, prices, AI allowances,
checkout and hosting charges are outside this change.

## Configuration evidence

- Imported only AEDROVA_ANTHROPIC_KEY and AEDROVA_MODELS_FILE through a private,
  Git-ignored, mode-0600 dotenv file. Resolved the previous model-catalog row rather
  than retaining duplicate keys. No secret value was emitted or committed.
- Anthropic's authenticated model metadata returned 200 and lists the configured
  claude-sonnet-5-5 model.
- Authenticated staging preflight advertises both codex and claude_code; the
  authorized no-model greeting passes. This alone does not prove coding acceptance.

## Reproduced and repaired blocker

The first actual Claude CLI request returned a server TypeError before inference.
A synthetic CLI request captured only at loopback reproduced it locally: recursive
media validation tried hashing a JSON-schema dictionary under a property named type.
Such tool schemas are valid and common. The guard now checks string media tags
without interpreting schema objects as tags; malformed top-level tool type values
still reject before provider calls. Existing multimedia, authorization and spending
protections remain in place.

53 focused gateway tests and the full 627 backend tests pass. The fix is committed
as ebb36c6 on codex/stage1-acceptance and is being deployed only to staging.
The current live Claude planning/build/review/apply result must be recorded below
before claiming that acceptance is complete. The initial interrupted attempt cleaned
its synthetic fixture and signed out; it did not pass coding acceptance.

## Evidence and outstanding gates

Ignored operational evidence is under
work/staging-acceptance-2026-10-24-followup/: claude-build/report.json,
claude-backend-tests.log and claude-staging-live.png. No session token is saved in
those reports. No new owner SQL or key generation is required for this activation.
Other Stage 1 gates remain independently open: new-workspace free access, connector
live certification, native physical acceptance and final hosting/meeting readiness.

## Final result: configuration complete; live Claude acceptance blocked

Render reports ebb36c6 Deploy succeeded | Live. The current CLI also sends
inline-tools-2026-09-15, a beta capability outside the reviewed gateway allowlist.
Managed Claude now uses the official CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS setting
rather than widening that allowlist, and disables non-streaming fallback to avoid
an automatic protocol switch/replay after an interrupted stream. Personal provider
fallback, tool approval and strict sandboxing remain unchanged. Official reference:
https://code.claude.com/docs/en/env-vars.

The next attempt passed the gateway's beta-capability check but did not produce a
valid model result. A separate synthetic Anthropic count_tokens request (no generation)
returned HTTP 400 invalid_request_error with a credit-balance error. Model metadata
still returns 200. Do not describe Claude coding as verified: the API organization
must have sufficient credit before the complete planning/build/review/apply test.
The test subspaces/messages were cleaned up and sessions signed out.

Full regression: 970 desktop and 627 backend tests passed. Final managed-runtime/
routing checks after the fallback refinement: 34 passed. Secret scan/Ruff/diff pass.
The existing private source key was retained; the generated import copy was removed.
No production deployment, new credential, payment, automatic refill, hosting upgrade,
subscription or allowance change was made.

Required owner action, which can be deferred to the final paid infrastructure setup:
open https://platform.claude.com/settings/billing, sign into the organization that
owns the existing API key, review its API credit balance and personally add credits
if needed. Do not buy a chat subscription as a substitute or paste the key in chat.
The console login tab is open; no agreement or purchase was submitted. Reply when
funded so engineering can rerun the managed Claude task. This blocks live Claude
acceptance, not the already passing Codex build or the configuration deployment.
