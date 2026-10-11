# Phase 1 owner handoff

Owner requested that interventions be collected and presented only after independent
engineering work finishes. No later milestone or public launch is authorized by this
handoff. Do not ask for passwords, keys or session tokens in chat.

## Verified staging checks

- Google provider enabled in `scvmvqlzcqhwrrsiahpj`; two distinct real Google accounts
  completed native PKCE loopback login.
- Both users read their own probe message. Foreign workspace, channel, message and
  membership reads returned no rows. Foreign message writes were denied (42501).
- Restricted staging backend cannot read public workspace rows.
- Staging Render service is separate and free; production stays unchanged.

These checks do not certify all AI context, connectors, meeting media or desktop UI.

## Deferred owner interventions, in order

1. **Clean up staging test fixtures.** In Supabase → **Aedrova Staging**
   (`scvmvqlzcqhwrrsiahpj`) → Table Editor → workspaces, identify the two workspaces
   whose names start `Beta isolation 1` and `Beta isolation 2`. Review that they
   contain only the disposable test content before deleting those exact fixtures.
   Do not select production or bulk-delete unrelated rows. The test's cleanup helper
   used an incorrect RPC parameter; it has been corrected, but the sessions ended.
   Cleanup is housekeeping; it does not invalidate the passing isolation checks.
2. **Desktop UI acceptance.** Open the source staging app using
   `uv run python -m scripts.run_staging --config work/staging/public-config.json`
   from the Aedrova repository. Verify this is the staging source app, not the
   existing packaged production app. Complete account/workspace onboarding and
   confirm Google returns focus to the app. Stop if the window/environment cannot
   be distinguished. This remains a Phase 1 acceptance gate.
3. **Approve concrete merge protections when prepared.** Repository owner must
   approve default-branch protection/ruleset changes for both repositories after
   the required checks are green. Proposed requirements: no deletion/force push,
   PRs with passing release checks, and no impossible second-reviewer requirement
   for a solo owner. Do not change these security settings without that approval.

## Later-phase requirements, not required now

Live customer connector grants/revocation, model access, billing lifecycle, meeting
media/transcription, independent security review, business verification, macOS
Developer ID/notarization and signed Windows installation tests retain their existing
release gates. See `docs/final-beta-launch-plan.md` and `docs/milestones.md`.
Never switch waitlist to billing/downloads based on Phase 1 checks alone.

## Engineering gates — not tasks for the owner

- Full Windows CI must pass; passing lease tests alone does not certify a Windows
  app. Remaining categories: provider process/pipe portability and synthetic
  executable fixtures, permissions/ACL expectations, safe retention behavior and
  responsive layouts with Windows fonts. Keep the Windows CI job failing visibly
  until corrected; do not skip unsupported tests to claim release readiness.
- Confirm final Linux CI after fixing agent-feed visibility, and final macOS/RLS CI.
- Record final native/service revisions and complete Phase 1 before requesting
  authorization for the next phase.
