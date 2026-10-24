# Coding router — initial implementation

## Architecture assessment
Chat mentions use dot_analysis and tool-free managed replies for conversation;
Build Room uses Worker, LocalRunner, private checkouts, permission-scoped evidence,
and explicit plan/review/publishing gates. Background work uses ExecutionQueue and
RunLedger with fingerprints and explicit recovery; it never automatically replays
uncertain edits. ManagedClient.begin reserves workspace AI budget on the server.
Existing provider credentials and settlement remain unchanged. The router adds no
keys, model endpoints, dependencies or billing authority.

## Delivered surface
Build Room adds opt-in Auto beside manual Codex and Claude Code. Existing saved
preferences stay manual. Auto selects once before planning; successful selection is
pinned in the Build Room selector before implementation. No dual execution,
automatic fallback or retry. Ordinary conversation classification returns no agent.
Both adapter instances delegate to the existing sandboxed coding harness, retaining
progress, cancellation, permission callbacks, context and test-output handling.

Policy is configured through the immutable Python Policy object: default Codex,
minimum 30 reviewed samples, quality/cost/latency weights .6/.2/.2. Candidate metrics
must describe comparable task categories and the same agent configuration; callers
must not mix incomparable cohorts. Reviewed evaluations use a Wilson lower bound.
Insufficient evidence selects an eligible default without claiming superiority.
Unknown cost/latency fails closed when that constraint is explicitly supplied.
Server credit reservations remain authoritative, including for manual choices.

The pure choose interface supports auto/manual/space_default, availability, tools,
reviewed metrics and constraints. runtime_candidates checks installation only;
authentication and real provider availability are checked at execution, and failure
stops the build. Current UI does not fetch preflight live balances or reviewed
metrics, so production selection currently uses the default rather than pretending
to optimize cost. No new admin Space-default setting or automatic chat/background
Auto migration is enabled. Those require integration with authenticated backend
preference/capability data before enabling broadly.

## Telemetry and evaluation
Queued Auto runs record selected provider, category, outcome, policy version and
phase in the existing private SQLite ledger. Duration and observed token counts
remain in its usage table; queries join run owner/workspace. No new prompt, model
output, exception, credential or conversation logging. Interactive routing rationale
is returned to Build Room; it is not yet durable telemetry. Costs, configuration,
repair rates and quality verdicts remain unknown unless backed by actual existing
provider/server evidence. Never infer test success from task completion.

evaluate() runs synthetic routing cases without invoking a provider or altering
policy. It measures routing expectations, not agent quality. Reviewed real-agent
benchmarks and versioned category-specific cohorts are still needed before enabling
metric-driven traffic. No unvalidated online learning.

## Setup and provider assumptions
No new environment variables. Existing AEDROVA_MANAGED_ORIGIN and included AI mode
retain backend-owned credentials and budget checks; local provider-login mode retains
its existing separate billing. Runtime CLI authentication must be valid. Missing
credentials/outages stop the run; the user explicitly selects another provider.
No new paid test, key transfer, purchase or hosted migration performed.

Official execution references reviewed October 23, 2026:
- https://developers.openai.com/codex/noninteractive
- https://code.claude.com/docs/en/headless
Both describe coding harness execution rather than ordinary text-only model calls.

## Remaining acceptance
This is an opt-in foundation, not the full production rollout requested. Remaining:
authenticated per-Space admin Auto/default UI, category/config-specific reviewed
metrics ingestion, preflight backend credit/capability data, durable interactive
telemetry and actual cost/repair/test-outcome records, broad routing across background
and Bud flows, live provider and cross-Space end-to-end acceptance. No owner action
is required for local tests; live execution requires a signed-in staging workspace
with provider access and explicitly authorized usage. Do not claim those gates passed.

## Completion pass — October 23

Shared provider selector now exposes Auto in onboarding, local project settings and
owner/admin Space settings (existing RPC authorization retained). Saved background
and Bud build requests carry that setting into the same BuildJob routing boundary.
Conversation replies resolve Auto to the default text provider and never run the
coding classifier/harness. Build Room pins the provider selected for an approved
plan. Automatic provider fallback remains disabled.

Managed Auto preflight calls the existing authenticated /api/balance/{workspace}.
That response now includes configured provider/model identifiers only, after
billing_context authorization. Auto intersects those with installed runtimes and
requires positive available credit. The existing atomic /api/runs reservation is
still mandatory, so a balance race cannot authorize unbudgeted inference. Preflight
availability means configured, not a promise that an upstream provider is online;
provider errors stop work. No second provider is tried or charged automatically.

Interactive phases get a unique private ledger run containing a generic task label
rather than prompt text, along with the same observed usage/outcome records.
Actual monetary cost remains authoritative on the server; absent actual cost/test
quality information is unknown, never fabricated. CLI completion alone does not
establish test success. Raw command results remain in the existing review evidence.

Development builds may opt into a reviewed cohort with
AEDROVA_ROUTING_EVALUATION_FILE=/private/path/cohort.json. Frozen builds ignore that
environment variable. JSON must be <=64KB with reviewed=true, exact category and
configuration="aedrova-local-harness-v1", and providers keyed by codex/claude_code.
Each metrics object must contain samples, successes, estimated_cost, latency.
Use the same currency/units across candidates. No automatic online updates. This
loader checks cohort compatibility, not the truth of reviewer-supplied measurements.
Production release must ship an explicitly reviewed configuration before enabling
measured-policy optimization; no real performance dataset is available yet.

### Required staging acceptance actions
1. Supabase → Aedrova Staging → SQL Editor → New query: run
   /Users/ayanshvarma/Documents/Aedrova/supabase/migrations/202610230001_auto_agent_preference.sql.
   This expands only the preference enum; existing RLS and owner/admin RPC remain.
   Shared Space Auto cannot be saved until this is installed. Do not run in production.
2. Deploy the website/backend source change (app.py balance provider preflight) to
   aedrova-beta-staging before testing managed Auto. Old servers fail closed with a
   curated preflight error; manual choices remain available.
3. In staging with configured provider access/credit, choose Auto in Project settings,
   request a small repository task, approve plan, verify changes/tests, cancellation,
   usage, and a second member's denied admin edit. Real inference is not yet verified
   in this pass. No keys or payments are requested.

Earlier Remaining acceptance text describes the initial snapshot; shared selector,
backend preflight and durable interactive records are now implemented as above.
Remaining deployment/acceptance and unavailable empirical benchmarks must not be
reported as completed. No source migration automatically deploys itself.

### Live staging acceptance after owner migration

Staging backend 7f6278c is Live (Render dep-dbe51ul9fdbs739bigc0).
Health readiness 200; unauthenticated balance 403. check_staging_router.py completed
with authenticated owner RPC Auto save/read passing, unfunded disposable workspace
returning no_plan/zero available, and an existing authorized workspace returning
provider preflight and positive available credit. One configured provider was
reported. Disposable workspace archived; test session signed out. No model call
or provider spend occurred. Result: work/staging/router-acceptance.json.
This verifies configuration/preflight, not actual coding inference or both-provider
end-to-end behavior. Those acceptance gates remain distinct.
