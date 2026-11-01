# First-use rebuild

Owner request: owner-brief.txt. Reference inspected: https://shotbase.com/.

Implement in the existing PySide6 desktop, using the current tokens, brand mark,
Bud atlas, connector gallery, Google handoff and authenticated IdentityService.
No new frontend stack, provider chooser, invented grants or marketing-only app.

## Delivery

1. Native six-stage FirstUseJourney, replacing the default account-first entry.
   Keep account/workspace administration and optional Help tour available.
2. Durable authenticated onboarding progress with compare-and-swap versions,
   idempotent Space creation and first conversation, reuse existing Space/Bud/
   invitation RPCs and their role/cap enforcement. Local pre-login drafts contain
   no credentials. Completed/legacy users go to existing workspaces.
3. Cinematic finite opening, purpose/identity form, real embedded connector gallery,
   actual Bud lineup and capped activation, invitations with honest shareable-code
   delivery, project objective and explicit handoff into the actual workspace.
4. Unified Auto model. Explicit local workflow permission review; original-folder
   apply and external publishing remain separately approved. No implicit AI run.
5. Native responsive layouts at 1440x900 and 390x844, warm light / charcoal dark,
   keyboard focus, reduced motion, bounded timers and account-safe cleanup.
6. Database/RLS, timeout/retry, new/existing/returning users and visual acceptance.
   Save per-stage desktop/mobile light/dark screenshots. Record real hosted
   acceptance separately; no payment or fabricated provider success.

## Important actual constraints

Invitations create one-use codes, not email delivery. Bud integrations belong to
Buds; creating a context Bud consumes actual server-enforced plan capacity.
Expose that before connecting. Only runtime-available OAuth/managed integrations
appear in first-use. Keep OAuth polling alive while the same journey is open,
resume the stage after a browser return and report expired grants honestly.
Meeting funding / reliable two-device tests remain separate launch gates.

## Current unrelated source change

Preserve the uncommitted native-language Original text fix in conversation.py,
its existing bilingual regression assertions and docs/milestones.md entry.

## Implemented November 1, 2026

Default app launch and the source staging launcher now open FirstUseJourney.
Explicit --account remains the account-administration entry. Returning members
are routed to their existing workspaces after authentication; interrupted first
use resumes its versioned stage. The original optional Help tour is retained.

Native components: first_use.py (six screens and responsive navigation),
first_use_visuals.py (finite context convergence and selectable actual Bud art),
first_use_actions.py (authenticated orchestration and recovery). Existing
AccountDialog, IdentityService, connector gallery, project chooser, code-based
invitations, budget enforcement and dashboard remain the implementation paths.
The main agent uses the real brand mark, separately from six specialized Buds.

The context step loads only runtime-enabled OAuth/managed providers and their
existing logos/groups. Browsing creates nothing. Explicitly connecting creates
or reuses the purpose-appropriate Bud within server-enforced plan capacity,
then continues the existing authorization, resource selection and verification.
The service context is isolated and original-session transport is serialized.
Closing setup stops authorization polling. No grants are invented.

The new migration 202611010001_first_use_journey.sql adds owner-private progress
and member-private workspace identity. Protected RPCs reuse existing Space,
Subspace, Bud, invitation and message operations. Compare-and-swap revisions
reject stale devices; row locks make writes retry-safe. AI authority is reviewed
at creation and cannot be increased through draft edits. Local folder bindings
and invitation secrets are never saved in remote progress; invitation codes are
available only in the creating session. The final objective is an actual plain
team message, without an implicit AI/build/publish operation.

Validation: full native regression run 1,104 passed before final visual/controller
refinements; focused follow-up suites cover those refinements. Actual embedded
PostgreSQL migration/RLS tests passed, including malformed drafts, stale writes,
AI review, Space/Bud/invitation/completion retries, real Bud cap and account
isolation. Lint, compilation and diff checks passed. Detailed final counts and
screenshots are in work/onboarding-rebuild/.

24 local visual-fixture captures cover all six stages at 1440x900 and 390x844 in
both themes. They are layout evidence, not a claim of new live provider consent.
Native Qt desktop narrow-width support does not create an iOS/Android binary.

## Required staging rollout

In Supabase > Aedrova Staging (scvmvqlzcqhwrrsiahpj) > SQL Editor > New query,
run supabase/migrations/202611010001_first_use_journey.sql once. Do not run it in
production during this UI iteration. This is required before a new staging user
can create/resume the new flow. Existing members retain account administration
access on older hosts. Then reopen work/staging/Aedrova Staging.app and sign in
with a staging test account for hosted acceptance. No new key, provider charge,
hosting upgrade or payment is required by this migration.

Unchanged limitations: invitations are codes, not automatically emailed; local
project folders cannot migrate between devices; provider public approvals and
meeting/Claude funding remain separate launch gates. New real browser grants
and cross-device hosted acceptance are not claimed by local transport tests.
