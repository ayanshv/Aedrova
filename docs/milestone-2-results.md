# Milestone 2 — completed

Verified on 2026-09-26 on macOS / Apple Silicon with Python 3.12.14 and PySide6 6.11.2.
Implementation: `/Users/ayanshvarma/Documents/Aedrova`.

## Delivered

- Python/Qt desktop shell with workspace rail, channel sidebar and five tabs.
- Workspace/channel/direct-conversation navigation and searchable quick switcher.
- Validated local workspace and channel creation dialogs.
- Variable-height messages, sample attachment references, pinned decision and thread panel.
- Local message/reply composition; independent workspace/channel/thread drafts.
- Light, dark and system appearance; persisted appearance preference.
- Keyboard shortcuts, focus navigation, accessible control names and message text roles.
- Compact thread layout, collapsible sidebar and scrollable workspace rail.
- Readable sample project documents; honest unconnected Builds/Meetings views.
- Reproducible screenshots and standalone `dist/Aedrova.app` packaging.

## Verification

- Full suite: **51 tests passed in 10.11 seconds**, including the 29 milestone 1 tests.
- `ruff check`: **passed**.
- `ruff format --check`: **27 files already formatted**.
- `uv lock --check`: **passed**.
- `uv build`: source distribution and Python wheel **built successfully**.
- Standalone Apple Silicon `.app`: **built successfully**, no WARNING/ERROR entries
  in the packaging log.
- `codesign --verify --deep --strict dist/Aedrova.app`: **passed** for local ad-hoc signing.
- Packaged binary launched from `/tmp` independently of uv: **passed**. Smoke report
  confirms five tabs, five initial messages, correct workspace/channel, light theme,
  and successful screenshot capture.
- Eleven visual QA snapshots generated. Light/dark conversation, thread, compact layout,
  project page, search/create dialogs and document rendering were visually inspected.

Interaction checks cover:

- Channel/workspace switching and draft isolation.
- Direct conversations and empty-channel first message.
- Return to send, Shift+Return newline, whitespace rejection and message length limit.
- Mention insertion without fabricated AI execution.
- Pinned decision, thread replies, thread drafts and closing/restoring the main conversation.
- Search results, no-match behavior, keyboard selection and dialog dismissal.
- Duplicate-name validation and local space creation.
- Appearance switching and persisted preference.
- Tab navigation and readable documents.
- Command+K, Command+1/3, Command+Shift+L, Tab focus and Escape.
- Accessible names/text roles and selected semantic text color contrast of at least 4.5:1.
- Rendering and reaching the final row in 2,000 variable-height messages, with a bounded
  512-entry text-layout cache; the original 50,000 uniform-row probe remains covered.
- Workspace rail layout with 20 additional workspaces.
- Selected workspace background remains visible after theme changes.

The long-history test found a batched-layout scrolling issue. MessageView now retries the
requested position as the layout range grows; its regression test confirms the final row
actually intersects the visible viewport. Visual QA also caught an inherited scroll-area
style hiding the active workspace background; the selector is scoped and regression-tested.

## Scope and limitations

This is an interactive **local preview**, not a connected team workspace. Messages, replies,
drafts and newly created spaces reset when the application closes. Only appearance is saved.
Sample attachment references are not uploaded files. No accounts, Supabase policies, live
chat, model calls, repository actions, payments, camera/microphone access or calls are active.

Accessibility checks establish names, text roles, keyboard behavior and selected color
contrasts; they do not constitute a full manual VoiceOver audit. Performance checks use
synthetic local data and are not production service latency measurements.

The application is locally ad-hoc signed. Public Developer ID signing, notarization, DMG,
updates, Intel support and clean-device release validation remain later distribution work.

## Run and evidence

Launch: `open /Users/ayanshvarma/Documents/Aedrova/dist/Aedrova.app`
Development: run `uv run aedrova` from the product directory.

Raw local evidence:
- `work/milestone-2-tests.xml`
- `work/milestone-2-package.log`
- `work/milestone-2-wheel.log`
- `work/m2-packaged-light.json` and `.png`
- `work/milestone-2/visual-qa.json` and eleven PNGs

## Next approval gate

Milestone 3: Supabase authentication, workspace membership/invitations, roles, private
channels, storage/realtime access policies and cross-tenant isolation tests.
**Milestone 3 has not started. Owner approval is required.**
