# Aedrova

A private Python-first desktop workspace where team conversation becomes context for
explicitly requested software builds.

## Current scope

Milestones 1–4 now include the Python desktop shell, Google-only sign-in, team onboarding,
real workspaces/channels, persistent chat and threads, private DMs, attachments, unread state,
keyset history, private realtime invalidations and reconnect/retry handling.

The desktop layout and styling are unchanged by milestone 4's completion. Functional shortcuts
use native dialogs: **⌘⇧M** starts a DM, **⌘⇧U** attaches a file, **⌘⇧S** saves a selected
message's attachment, and **⌘⇧H** loads older channel messages (scroll upward for older replies).
The browser-only OAuth callback now has branded light/dark styling.

Apply the migrations through `202609280001_communication.sql` before running this build.
See [milestone 4 setup and verification](docs/milestone-4-shared-chat.md).
Hosted multi-account validation remains pending; local tests do not certify the hosted setup.
Sessions, unsent drafts, and queued retries stay in memory; committed messages/files live in Supabase.
`--demo` explicitly opens sample data that resets at exit. Calls and billing are later milestones.

Milestone 5 adds real local builds from **Builds → Start a build**, `/build`, or an explicit
`@AgentName build ...` command. Codex live file editing/testing is verified. Claude Agent SDK
support requires Anthropic API setup for its paid live check. See the [local builds guide](docs/milestone-5-local-builds.md)
for owner steps, permission/context limits and next gates.

Milestone 6 adds **Workspace context & decisions** in the build window: local full-text search,
explicit decision recording, source citations and revision-aware retrieval. **Apply the new
Supabase migration before using context/builds:** [Milestone 6 setup](docs/milestone-6-context.md).

## Run

Requires macOS and uv. Python 3.12 is pinned; uv.lock records exact dependency versions.

```sh
uv sync --frozen
uv run aedrova
# Local sample chat only:
uv run aedrova --demo
```

Optional: `uv run aedrova --theme light` or `--theme dark`. The View menu also offers
System appearance, Reduce motion and Reduce transparency. `--settings-file work/preview.ini` isolates preview preferences.

Keyboard: Command+K to jump, Command+1–5 for tabs, Command+Shift+L for appearance.
Return sends; Shift+Return inserts a line break. Escape closes a thread or dialog.

## Verify and package

```sh
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run python scripts/capture_desktop.py
uv run python scripts/package_desktop.py
open dist/Aedrova.app
```

The package is locally ad-hoc signed, not Developer ID signed or notarized. Public DMG
distribution and updates remain milestone 11. Current packaging targets Apple Silicon.

## Milestone 1 probes

```sh
uv sync --frozen --extra spikes
uv run --extra spikes python scripts/check_integrations.py
uv run aedrova-probe
uv run python scripts/package_probe.py
```

The integration probe initializes the actual Claude SDK runtime without submitting a model
request, then checks synthetic LiveKit video/audio buffers and Qt compatibility. It does
not access a camera, microphone, repository, or cloud meeting. No API keys are required.

## Structure

- `src/aedrova/desktop`: shell, semantic themes, dialogs, virtualized messages and local fixtures.
- `src/aedrova/domain`: immutable context, permission, approval and lifecycle contracts.
- `src/aedrova/agents`: provider-independent requests and streaming event interface.
- `scripts`: repeatable feasibility, screenshots and packaging checks.
- `tests`: permission boundaries, approval scope, desktop interaction and rendering checks.
- `docs/architecture.md`: decisions and unresolved production validation.
- `docs/milestones.md`: implementation gates.
- `docs/milestone-1-results.md`: first milestone evidence.
- `docs/milestone-2-design.md`: UI behavior, keyboard controls and scope.
- `docs/milestone-2-results.md`: second milestone evidence.
- `docs/owner-actions-google-onboarding.md`: required owner setup and next gates.
- `docs/google-sign-in.md`: Google-first login and one-time owner setup.
- `docs/milestone-3-setup.md`: Supabase configuration and live validation gates.
- `docs/milestone-3-results.md`: local identity implementation evidence.
- `docs/brand-integration.md`: logo, Dock icon, brand motion and packaging.
- `docs/design-revision-results.md`: Apple-inspired visual revision and verification.

Generated builds and probe reports stay in ignored `build/`, `dist/`, and `work/`.

Current internal-alpha delivery and setup: [Milestone 7](docs/milestone-7-delivery.md).
The app now includes guided GitHub CLI installation and browser authorization; no new
Supabase migration is needed for M7. See [the roadmap](docs/milestones.md) for the
paid-beta website and complete desktop onboarding tour.
