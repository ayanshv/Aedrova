# Aedrova

A private Python-first desktop workspace where team conversation becomes context for
explicitly requested software builds.

## Current scope

Milestones 1–2: architecture contracts and an interactive Mac desktop preview. Navigate
workspaces, channels and tabs; write local messages; open threads; create local spaces;
read sample documents; switch light/dark/system appearance.

**Local preview:** messages, drafts and created spaces reset when the app closes. Only
appearance, reduced-effects preferences and public Supabase configuration are saved. Account and workspace administration is available through **Account → Account & workspaces…**
when configured with Supabase. See [identity setup](docs/milestone-3-setup.md). Hosted validation
is still pending. Realtime chat, AI execution, calls and billing are not connected.

## Run

Requires macOS and uv. Python 3.12 is pinned; uv.lock records exact dependency versions.

```sh
uv sync --frozen
uv run aedrova
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
- `docs/milestone-3-setup.md`: Supabase configuration and live validation gates.
- `docs/milestone-3-results.md`: local identity implementation evidence.
- `docs/brand-integration.md`: logo, Dock icon, brand motion and packaging.
- `docs/design-revision-results.md`: Apple-inspired visual revision and verification.

Generated builds and probe reports stay in ignored `build/`, `dist/`, and `work/`.
