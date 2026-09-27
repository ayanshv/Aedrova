# Aedrova — design revision

Completed September 26, 2026 in the Python/PySide6 desktop app.

## Design

- System typography with large, tightly tracked headings and medium/semibold hierarchy.
- Spacious floating workspace panels, 24-pixel corners, capsule tabs and subtle borders.
- White/#F5F5F7 light appearance and black/#1C1C1E dark appearance.
- Neutral surfaces dominate; blue is reserved for actions and small accents. The 60/30/10 rule is a visual hierarchy, not an exact allocation of screen pixels.
- Cached blurred aura, translucent materials, specular edges and soft ambient shadows.
- Responsive Projects and Files bento layouts.
- Hover scale, press compression and spring release with stable hit targets.
- Persistent Reduce motion and Reduce transparency controls in the View menu.

Glass is rendered in Python/Qt using an in-app blurred backdrop. It does not use Apple's native Liquid Glass API or refract other desktop windows.

## Verification

- Full suite: **56 passed in 12.17 seconds**.
- Ruff lint and formatting checks passed.
- Tests cover existing navigation, messages, threads, drafts and creation, plus motion, reduced effects, responsive grids and restrained accent coverage in both themes.
- 14 visual snapshots generated, including compact layouts, light/dark chat, threads, Projects, Files and dialogs; representative layouts visually inspected.
- Rebuilt `dist/Aedrova.app`; deep/strict ad-hoc signature verification passed.
- Packaged app launched from `/tmp`, rendered dark appearance with an open thread and saved its smoke screenshot; process exited successfully without logged errors.

## Scope

This remains a local preview. Messages and created spaces reset on exit. Supabase, live chat, AI execution, calls and Stripe are not connected. The package is ad-hoc signed, not notarized for public distribution. Full VoiceOver user testing remains outstanding.

Milestone 3 (identity and tenant isolation) has not started and requires owner approval.
