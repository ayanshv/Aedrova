# Aedrova introduction and guided configuration

`zen_onboarding.py` supplies the animation and flow; `zen_setup.py` supplies real
configuration pages. `onboarding.SetupDialog` remains the integration entry point.
The native app's `--onboarding` argument opens the introduction directly.

The 12 screens are: boot, demo mention, 2.5-second simulated context map, shortcut
playground, appearance/editor/accessibility, profile/workspace personalization,
project/provider, agent authority, GitHub, devices, final review, and handoff.

Light or dark neutral surfaces use Aedrova blue accents. The original transparent
brand mark has a text fallback. Critically damped springs, orbiting sparks, mention
particles, animated page lifts, a 12-step trail and fading integration dialogs share
one visual language. A precise 16 ms timer targets 60 fps; OS timing is not guaranteed.
Reduced motion suppresses decorative motion and shortens transitions.

The first four screens are simulations and say so. Real setup screens explicitly
identify real choices. Appearance/editor/project drafts save only at final review.
Profile changes in the embedded three-page form and GitHub authorization are real;
they apply only through their explicit Save/Authorize controls. Device checks start
only on explicit device controls and may prompt for macOS permissions. Nothing
automatically starts a build, call, upload, installation, recording, transcript or push.

Automatic planning/execution is an explicit checkbox, initially off for an unbound
project. It grants the existing local-project behavior: after a mention, share
accessible workspace context with the chosen provider, plan, edit a build copy and
run sandboxed commands. Applying to the original folder and publishing require
separate approval. A valid specific folder and the same signed-in account/workspace
are required before saving that grant. Existing project fields are preserved.

Provider login, AI allowance, repository authorization and meeting deployment are
not silently configured or falsely marked ready. Review distinguishes chosen values
from verified integration access. Account/profile confirmation is required; advanced
configuration is revisitable in Settings. The simulated intro can be skipped directly
to settings. Set up later is available only after profile completion and closes the
remaining flow without applying draft preferences. Account changes invalidate the
flow; signing in explicitly from an unauthenticated preview binds the subsequent
setup to that account. Completion remains account-scoped in QSettings v2.

Owner steps: no SQL or new deployment credentials. Sign in through the profile step
if needed, choose the project you actually want the agent to work on, and select the
automatic-build checkbox only if you want that authority. Use GitHub and device
setup controls when desired. Provider access remains a separate requirement before
real builds; the onboarding's simulation never proves a provider is configured.

## Visual refinement

Titles use the macOS system font at semibold weight with tighter display tracking.
Blue is the primary accent; neutral surfaces follow the selected Light, Dark or System appearance.
Appearance choices show captures of the real desktop app using local sample content,
with System combining the light and dark captures. No private workspace content is
included. The screenshots ship inside the application, with immediate neutral
fallbacks if unavailable. Setup illustrations cover identity, the local folder,
planning and execution, repository review, meeting devices and final choices.
The Google entry uses the existing multicolor Google icon. All real actions retain
explicit controls and the existing permission rules. This visual change requires
no new Supabase migration or external configuration.

Appearance selection immediately previews the entire introduction in Light or Dark.
System resolves the current macOS appearance and follows live changes while the
introduction is open. Painted illustrations, theme-photo labels, integration
dialogs and control states share the same appearance. The choice remains a draft
until the existing final Save action applies it to the dashboard.

## Sign-in → required profile → controls tour

Google authentication now hands the user back automatically after the authenticated
profile/workspace snapshot loads successfully. Ordinary refreshes do not advance
onboarding. Cancelled or failed sign-in keeps the same step available for retry.
The three-page profile form is embedded in setup: confirm a display name and unique
username, then optional photo, bio/title and status. Save must succeed before the
project step opens. Incomplete profiles cannot use “Set up later” to bypass it.
An account without a workspace gets an explicit create/join control before project
setup; sample workspace IDs never receive a real account's project binding.
The existing provider, permission and repository rules are preserved.

After completing setup, Explore Aedrova starts automatically with twenty concise
spotlights grouped into chapters. Each explanation is at most forty words. The
highlights ease in, respect reduced motion, and point to real visible controls;
the guide never sends a message, starts a build/call or publishes code. Users can
move backward, jump chapters, pause or skip and resume from Help. Finishing the tour
restores focus to the composer. No new SQL migration is needed. The owner should
sign in once in the rebuilt app to confirm the live Google callback; automated
journey tests use a fake transport and do not access personal credentials.
