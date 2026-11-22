# Onboarding rebuild (November 22, 2026)

## Reference

Shotbase (shotbase.com), a Mac app whose users praise its onboarding: the opening animation,
the permission step, sound and haptics. Its onboarding lives inside the downloaded app, which I
did not install, so this follows what its site shows publicly: very short headlines, one
sentence of support, benefit first, few steps. Sound and haptics are not copied.

## Setup (account, workspace, project)

- Same five stages and logic; the copy is cut to one idea per screen: "Your team, plus
  Agents." / "Sign in" / "You're in control" / "What first?".
- Each screen arrives piece by piece (logo, headline, support line, buttons), a 70 ms beat
  apart, on the shared motion scale. Reduce Motion shows everything at once.
- Five progress dots, the current one a short pill.

## Tour (after setup, inside the workspace)

- Nine stops, replacing twenty-two. Each stop dims the window, rings one real control and
  places a tag beside it: a title of up to four words and one line.
- Stops: workspaces, invite, Buds, channels, mention @Aedrova, access, Project/Work/Files,
  AI allowance, settings and help.
- Starts once, about a second after first-run setup. Skipping or finishing means it never
  starts on its own again; Help → Explore Aedrova replays it. Esc pauses and resumes.
- A stop is skipped, not faked, when its control is not on screen (for example, no AI
  allowance yet). The ring glides between controls. Clicks on the dimmed window do nothing.

## Second pass: the opening, device access and background setup

Source: the owner's description of Shotbase's first launch. The aim is that onboarding is the
first demonstration of quality, not a set of chores.

- **Opening.** Three soft lights drift slowly behind the first screen and fade in over about
  a second. The logo, the two headline lines ("Your team," / "plus Agents."), the support line
  and the button arrive one after another, about a quarter-second apart. Reduce Motion keeps
  the lights still and shows everything at once.
- **Device access.** A new step, "Allow what you need", asks for Microphone, Camera and Screen
  inside the app before the system does. Pressing Allow lights that row, steps the others back
  and says "Your Mac will ask next." The system prompt follows after a short beat. The answer
  lands as a check; a refusal shows "Open Settings" with the right privacy pane. "Allow all"
  asks one at a time. The step is skipped when everything is already allowed, and nothing in it
  is required. Screen access may need Aedrova reopened, which the row says.
- **Background setup.** A small chip shows what is still finishing ("Setting up your
  workspace", "Turning on AI") with "You can keep going", then "You're all set". It reads real
  state, never blocks a step, and disappears when done.
- **Progress.** Six dots cover welcome, account, access, devices, project and first goal.

Not copied: sound and haptics (nothing in the app plays audio today), and any custom
operating-system prompt. The system prompts themselves cannot be restyled.

## Third pass: rebuilt from a real recording (November 22, 2026)

The owner supplied a screen recording of the reference onboarding. Setup now follows its
structure and motion:

- **Split window.** Left: a drifting pastel colour wash with the title, one line of help, the
  step's controls, and Back / Continue. Right: a drawn scene for the step, with a soft edge.
- **Motion.** The wash leans a new way on each step. A scene blurs and rises into place
  (about 0.5 s); the left side arrives piece by piece. Everything stops for Reduce Motion.
- **Steps.** Welcome (four feature rows, the highlight moves), Account, Privacy, Choose your
  theme (System, Light, Dark; applies live), Set up permissions (Allow per row; the scene's
  toggles switch on as each is granted), Project, First task (a short confetti burst).
- **Rules kept.** Theme is first-run only; permissions are skipped if all are allowed; nothing
  in setup is required except an account and a workspace.
- **Not built.** Launch at login, background auto-update and a "learn the shortcut" practice
  step from the reference need product decisions or features that do not exist yet.

## Fourth pass: one flow, one window (November 22, 2026)

- Sign-in, creating or joining a workspace, and connecting a project all happen inside setup.
  The account window is created but kept hidden (`AccountDialog.quiet`) and driven for the work
  it already does: browser sign-in, `onboard_workspace`, `accept_invitation`.
- Setup covers the screen with a borderless window instead of macOS full screen, so folder
  pickers and the new-project window open on top of it, and setup takes focus back after them.
- The workspace guide (tag tour) uses the same type, buttons, dots, soft glow and glide.
- Not changed: "Use an existing workspace" still opens the account window; Apple/Google sign-in
  itself still happens in the browser.
