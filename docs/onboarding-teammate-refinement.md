# October 6 — reference-led onboarding and living teammate sidebar

Authorized UI/teammate refinement before M17F.2. The two owner-provided ZIP archives
were inspected as visual references, not product instructions. Dub supplies the compact
forms, soft ambient canvas and restrained edges; Linear supplies progressive setup.
Aedrova's branding, blue accent, Python/PySide implementation and actual setup data remain.

## Implemented

- Centered 12-screen introduction/setup, compact type/buttons/inputs, restrained borders,
  white/blue ambient background and equivalent dark/system appearance.
- Google sign-in, profile details, workspace/agent identity, project/provider, workflow,
  GitHub and device controls are retained. Existing controls spotlight tour follows setup,
  now including the AI teammate shelf. No fake permissions or automatic provider activation.
- Chat shell uses tighter radii, quieter blue material and a compact channel heading.
- AI teammates have a dedicated sidebar section with + creation, every active profile,
  independent blinking/breathing, pointer-aware eyes and click-to-mention. New identities
  fall with bounded gravity, collision response, rebound and rotation. Polling or rename
  retains the same object/position. Workspace switches remove previous actors.
- Reduced motion uses still open-eyed characters and deterministic placement. Timers stop
  when hidden; idle animation never runs a model or creates a task.
- Free-text custom role is stored as `role_label` alongside the compatible execution-mode
  field. Existing Research/Product/Engineering profiles load without migration. Name remains
  an input; mode, shape, color, personality, reporting, work window and importance use
  styled discrete sliders with keyboard control and semantic values.
- Explicit Suggest tools with AI uses the selected local Codex/Claude provider login,
  read-only mode and a disposable synthetic repository. Only the role description is sent,
  never team/project context. Output is bounded and allowlisted; arbitrary tool IDs are
  discarded. Suggestions cannot grant access or connect apps. Failed/stale suggestions
  have a clear recovery and do not prevent manual role setup. Closing cancels the run.
- Current tool suggestions identify existing context/project/review capabilities; Figma,
  Google Drive, Marketing and Finance connectors remain labelled coming later. Existing
  project/GitHub permissions still govern execution; custom role text never expands them.

## Validation and owner actions

Real Codex role analysis passed on synthetic input (`work/onboarding-refinement/live-role-advice.json`).
The response suggested workspace search, Product memory, project files, meeting context
and Google Drive; the latter remains explicitly unavailable. Local model use can consume
provider allowance. Managed included-provider role advice is a later integration, not claimed here.

Tests cover allowlisting/no workspace transmission, role authority, keyboard sliders,
12-marble physical settling, stable rename, hidden/reduced-motion timers, paused clicks,
persistent mention tokens and the retained onboarding/account workflow. Full suite,
scoped lint, actual PostgreSQL/RLS suites, final packaged checks and light/dark/compact
captures are recorded in the handoff. Validation completed: 602 desktop tests passed;
42 focused account/onboarding/teammate tests passed after the final sign-in styling;
32 website checks passed. Scoped Ruff, PostgreSQL/RLS checks, final app signature
verification and packaged smoke checks also passed. Frame delivery targets ~60Hz; macOS scheduling
and device performance determine actual frame rate.

**Owner action now: no SQL, keys or purchases are required.** Existing local provider login
and allowance are required only when requesting AI tool suggestions or running assignments.
No accounts connected, GitHub pushes, deployment or release activation performed.
M17F.2 shared chat results/team management still requires permission.
