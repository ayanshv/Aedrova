# Milestone 1 — feasibility and architecture contracts

Completed 2026-09-26 on macOS / Apple Silicon with Python 3.12.14.

## Delivered

- Python project scaffold with isolated environment and locked dependencies.
- Qt desktop feasibility application with a virtualized 50,000-message history.
- Context/source, membership/channel, provider event, build-state and approval contracts.
- Repeatable SDK/media probe and Mac application packaging script.
- Architecture decisions, remaining risks and sequential milestone gates.

## Verification

- `uv run --no-sync pytest -q`: **29 passed in 1.08 seconds**.
  Tests cover cross-workspace/project filtering, private-source exclusion from broader
  conversations, deleted/superseded/disallowed sources, revoked invocation authority,
  state transitions, approval scope mutation, expiry/revocation, and Qt model/rendering.
- `uv run --no-sync ruff check .`: **passed**.
- `uv run --no-sync ruff format --check .`: **15 files already formatted**.
- `uv lock --check` and `uv build`: **passed**; source distribution and Python wheel built.
- Claude Agent SDK **0.2.160**: actual bundled runtime initialized successfully with
  tools disabled and explicit empty settings sources. **No model request submitted.**
- LiveKit **1.1.20**: synthetic RGBA -> BGRA -> Qt image conversion passed, including
  pixel verification; 48kHz mono audio buffer creation passed. Qt media imports passed.
- PyInstaller **6.22.3**: built an Apple Silicon `.app` successfully, no warnings/errors
  found in the packaging log.
- Packaged executable launched from `/tmp`, outside the checkout and without `uv`.
  It rendered 50,000 fixture rows, scrolled to the final row and saved a screenshot.
  Internal probe duration: **0.482 seconds**, including its deliberate 200ms timer.
  This is a local smoke measurement, not end-to-end cold startup or a performance SLA.
- Development executable: same probe passed in **0.390 seconds**.
- `codesign --verify --deep --strict dist/Aedrova-Probe.app`: **passed** for local
  ad-hoc signing. This does not establish Developer ID signing or notarization.
- Packaged screenshot visually inspected: list, labels and final row render correctly.

Other locked versions: PySide6 6.11.2, Pydantic 2.13.5, pytest 9.1.1.

## Boundaries

This milestone proves local desktop/package feasibility, agent protocol initialization,
media buffer compatibility and executable domain rules. It does not prove a production
chat platform, an isolated coding worker or working video conferencing.

Still to verify at their planned milestones:

- Paid model access and actual repository editing/testing (milestone 5).
- Backend-enforced permissions, database RLS and authorized realtime (milestone 3).
- Rich, variable-height messages and the final UI (milestones 2 and 4).
- Live two-participant media, devices, screen sharing, echo handling and network recovery
  (milestone 10; media provider selection remains provisional until that spike passes).
- Approval persistence, one-time action execution and credential broker (milestones 7–8).
- Stripe/Supabase/GitHub live service integration and credentials at their milestones.
- Developer ID signing, notarization, DMG, clean-Mac installation and updates (milestone 11).
- Intel Mac compatibility and minimum supported macOS version.

Raw local evidence lives in ignored `work/desktop.json`, `work/packaged.json`,
`work/integrations.json`, `work/package-build.log` and the associated PNG screenshots.
The development app is `dist/Aedrova-Probe.app`.

## Next gate

Milestone 2: desktop shell and visual system — workspace/channel/tab navigation,
chat/thread layout, keyboard interactions, accessibility and light/dark themes.
**Do not begin until the owner grants permission.**
