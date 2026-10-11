# Final-Beta Phase 2 — connectors and AI providers

Status: authorized, in progress. Owner confirmed both Phase 1 manual gates and
approved Phase 2 on October 10, 2026. No Phase 3, production merge/deployment,
public checkout, downloads or M14 activation is authorized by this phase.

## Initial implementation and verification

- Bud Finish later/Close now cancels setup rather than accepting an incomplete
  required flow; parent onboarding remains resumable. 55 Bud/onboarding tests pass.
- 72 native connector, transport, loading and Bud tests pass (offscreen source).
- Website/backend suite: 426 tests pass, including connector lifecycle and gateway
  authorization, provider/model binding, bounded inputs, cached usage, uncertain
  reservations, concurrent refresh, disconnect during reads and cross-account grants.
- Existing private OpenAI key passed a fresh GET model metadata lookup for
  gpt-5.3-codex. No paid inference or entitlement grant was performed. Historical
  October 7 build acceptance does not substitute for fresh staging gateway acceptance.
- Added hidden-prompt Anthropic setup, exact configured model metadata verification,
  bounded responses, generic secret-safe failures and atomic 0600 private storage.
  Added Claude-only model configuration and explicit local --with-anthropic option;
  combined local opt-in selects the existing dual-provider configuration. Rates and
  model selection are unchanged from the frozen baseline, not newly certified.
  API account/model access, current rates, bounded real inference and live CLI
  acceptance still require validation before release. No shared fallback provider.
- All credential files remain Git/Docker excluded. No credentials are recorded here.

## Current acceptance matrix

All nine offered connectors have source adapters and local regression checks. This
is not proof of provider registration, public review or fresh-customer acceptance.

| Connector | Local setup evidence | Live acceptance still required |
| --- | --- | --- |
| GitHub | Client pair present; prior owner connection | New test account, named installed repo, read denial outside install, refresh, revoked access, reconnect |
| Supabase | Client pair present | Named project selection, project-only metadata, expiration, revoke, reconnect; no customer SQL/data/keys |
| Figma | Client pair present | Real consent, selected file link/read permissions, refresh, revoked access, reconnect |
| Notion | Client pair present | Shared-page discovery, denial outside share, refresh, revoked access, reconnect |
| TikTok | Client pair present; prior account setup | Scopes/eligibility/review, account profile/video reads, rotation, revoked access, reconnect |
| Stripe Bud | Pair absent locally; previous app approved for testing only | Aedrova developer verification, issued install URL/credentials, external test account, balance reads, refresh, uninstall/reconnect |
| Instagram | Pair absent locally | Meta registration, professional test account, basic-only scope, long-lived refresh, revocation, provider review/live mode |
| Vercel | Pair absent locally | Integration registration, authorized team/project discovery, scoped deployment reads, uninstall/reconnect |
| Managed Search | Key absent locally | Owner funding/billing cap, service/workspace limits, key rotation, membership/reconnect; no customer OAuth fiction |
| OpenAI | Fresh model metadata lookup passed | Staging run-token authorization, hard budget, bounded real request and reconciliation, interrupted/revoked runs |
| Anthropic | Private setup implemented; key absent locally | Private key/model lookup, verified pricing, bounded real request/cache accounting and runtime acceptance |

Local credential presence was checked without printing any value. Hosted service
configuration was not overwritten or inferred from those local files.

## Repeatable live protocol

For each login connector, use a dedicated test account/resource containing only
synthetic data. Capture source/build, environment, account (public identifier only),
scopes and timestamp. Sign in from the selected Bud, approve read-only access, choose
an authorized resource, verify its actual API snapshot and visible confirmation.
Test cancel/wrong account, denied resource, expiry/rotation, provider 429/network
failure, membership loss, disconnect, provider-side revoke/uninstall, and reconnect.
Confirm no access/refresh token or key reaches desktop, chat, evidence or logs.
Do not revoke a founder's existing grant that is used by other Buds/accounts.

Disconnect currently removes Aedrova's scoped stored grant and prevents further use;
it honestly returns provider_revoked=false. Provider-wide uninstall/revocation is a
separate action and may affect other resources/Buds. Do not label local disconnect
as successful provider-wide revocation. Each provider's revoke acceptance must be
recorded separately. Normal login does not expose codes/keys; Figma needs a file
link because the implemented read scope has no account-wide file enumeration.

## Owner setup sequence

First: install the Anthropic key privately using the companion website repository's
scripts/setup_anthropic.py. This performs only a read-only model metadata lookup;
no inference, billing activation, deployment or checkout is started. Missing
credentials block Anthropic live acceptance, not the existing connector regression work.

Subsequent requirements remain in the website docs/account-connector-setup.md:
Stripe business verification/external testing, Meta/Instagram registration/review,
Vercel integration registration and managed Search funding. Walk through one owner
requirement at a time. Do not paste secrets into chat. Do not mark Phase 2 complete
until every offered connector/provider passes its actual acceptance gates.
