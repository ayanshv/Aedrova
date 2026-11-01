# Onboarding visual refresh

The owner superseded the saved full-rebuild brief on November 1: keep the original
screens, content and usage, applying only the new theme, animation and feel.

The default app and staging entry remain AccountDialog. Existing authentication,
Space creation/join, mandatory AI review, invitation codes, profile, project,
GitHub, device setup and optional Help tour remain in their original order and
retain their handlers. No new onboarding migration or provider consent is needed.
The experimental six-stage implementation and schema were removed before merge.

OnboardingStack crossfades outgoing native pages over the incoming screen while
keeping navigation and validation synchronous. It respects reduced motion and
finishes after 210ms. The existing welcome screen now uses the finite native
context-convergence scene with actual Aedrova branding and Buds. Original headings,
setup steps and actions remain. Neutral material corners follow both app themes.

Agent message avatars have transparent surroundings: no colored rounded tile is
painted behind the logo, and a user's photo cannot replace the agent mark.
Buffer's actual CC0 brand icon completes the existing connector icon collection.

The screenshot's no-plan error is an entitlement issue. Settings now exposes
Activate included AI only for an owner/admin when the server reports no_plan.
An explicit click calls the existing authenticated /api/free endpoint; server
eligibility, fresh billing permission checks, rate limits, shared usage budgets
and idempotent activation remain authoritative. It cannot buy a plan or reset
usage. Gate-closed or unauthorized responses remain visible. No local provider
fallback or allowance bypass is introduced.

Validation records: work/onboarding-rebuild/original-flow-tests.log and final
focused refresh tests. The earlier full regression baseline passed 1,104 tests;
new scope is covered separately by the original account/setup suites, motion and
explicit activation tests. Local theme screenshots are layout evidence, not live
provider or current-workspace entitlement acceptance.

Owner action for the currently affected workspace: open Settings > Your team's
plan & AI access > Activate included AI, then retry. If activation is denied by a
service launch gate, the exact response needs operator configuration; do not pay
or generate a new key. Existing paid launch gates remain deferred. No new SQL.
