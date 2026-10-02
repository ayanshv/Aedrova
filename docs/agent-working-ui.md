# Agent working UI follow-up — 2026-09-30

Authorized after finishing M8. The rest of the dashboard layout and brand remain intact.

- Codex-style in-chat public updates, compact command/file activity, expandable exact command
  output, elapsed time, left-to-right status shimmer, keyboard focus and Stop.
- Running command rows update in place when they finish. Success, nonzero exit and interrupted
  commands have distinct states. No fabricated reasoning/progress or private chain-of-thought.
- Updates use plain text; command output is selectable and bounded. Transcript retains at most
  100 entries; scroll follows new activity without stealing a user scrolling back through it.
- Theme-aware surfaces, accessible expandable controls and reduced-motion-aware shimmer.
  Activity viewport stays between 70 and 230 pixels to accommodate smaller desktop windows.
- Account/workspace/message popups use a shared styled Fusion renderer. Disabled identity text,
  separators, hover/focus, borders and padding match Aedrova. Existing provider/settings choices
  use ChoiceBox. The remaining default direct-message picker is replaced by a matching dialog.
- File attachment/save choosers use the macOS system dialogs intentionally; the local project
  chooser remains the existing themed non-native dialog. No extra account/backend actions added.
- Fixed queued scroll callbacks after destruction and hover overriding a pressed spring animation.

Visual acceptance used synthetic workspace content only, captured in work/agent-ui-proof in both
light/dark themes. Regression tests cover tool disclosures, command failures, bounded plain text,
widget cleanup, actual elapsed time, menu/choice renderer, chosen teammate, and resize/layout.

Owner action: quit the previous app and reopen dist/Aedrova.app. There is no new SQL/OAuth setup.
Existing Codex provider quota must reset before another fully successful live coding acceptance;
the M8 attempt wrote the feature and passed four generated tests before its final turn was blocked.
Included AI and paid-beta billing remain M9, not this UI follow-up.

Final verification: 282 Python tests passed; all embedded PostgreSQL suites passed. Ruff lint/format,
git diff whitespace, rebuilt package, deep/strict signature, baseline release-secret checks and isolated
packaged-account launch passed. Signature is the existing internal-alpha ad-hoc signature; public
Developer ID signing/notarization remains release work. No production deployment or GitHub push done.
