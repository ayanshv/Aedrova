# Bud personality, blinking and onboarding handoff — October 12, 2026

Implemented in the existing native application and public website:

- Eye-only blinks retain original sculpted sprites, accessories and custom tint.
  App shelf, previews, look picker, lineup, in-chat Bud avatars and intro use the
  same art. Website decorative and confirmation Buds use the same eye coordinates.
  Web animation pauses in hidden tabs, excludes offscreen rendering and respects
  reduced motion. Failed assets leave CSS artwork intact. Screenshot images of
  the product are intentionally static.
- Explicit **Finish later** resumes the controls tour and records `budsDeferred`
  for the current account. Ordinary dialog close still returns to unfinished
  onboarding. Deferring never pretends a connector was authorized or a Bud ready.
- A seventh setup step provides continuous warmth, directness, response detail,
  initiative, diligence and active-work progress interval controls plus up to
  480 characters describing a custom personality. Workspace owners/admins edit;
  members can inspect existing configuration.
- Preferences use a versioned JSON block in the existing 2,000-character private
  instruction field. Legacy instructions survive unchanged; profile versions and
  existing stale-configuration protections remain. No new migration is required.
- Both read-only Bud answers and Builder prompts explicitly apply working style,
  bounded by permissions, evidence, plan budgets and existing approval gates.
  Optional progress prose is throttled; technical tool events remain visible.
  Intervals are minimum spacing when the provider emits progress, not a promise
  of scheduled updates. There are no idle tasks or extra AI calls for animation.
  Diligence influences model instructions; it does not raise execution budgets.

Verification: 762 native tests passed, including persistence, input validation,
permission/version guards, explicit-defer tour handoff and eye rendering. Follow-up
reduced-motion changes have focused regression checks. Light/dark screenshots and
open/closed comparison are in `work/bud-personality/`. Website preview verified
17 animated placements and no console errors; public-page/deployment checks passed.

Owner action: reopen the current source build to load changed Python modules. From
`/Users/ayanshvarma/Documents/Aedrova`, run `.venv/bin/python scripts/run_staging.py
--config work/staging/public-config.json` after closing the previous staging preview.
No SQL, credentials or provider setup are required for this change. Native staging
Google sign-in and physical dictation/upload acceptance from Phase 3 remain pending;
paid meeting hosting and Stripe launch setup remain deferred. This change does not
mark Phase 3 or final Beta acceptance complete.
