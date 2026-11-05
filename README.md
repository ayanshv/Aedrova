# Aedrova

Your team, plus Agents

Aedrova is a Python desktop workspace for team conversations, configurable AI teammates called Buds, and software builds grounded in the context a team has permission to use.

The project is in pre-launch development. Feature implementation, staging acceptance, provider approval, and public release are tracked separately in [the milestones](docs/milestones.md) and [pre-launch timeline](docs/pre-launch-timeline.md).

## What the app does

- Team workspaces, channels, threads, private conversations, file previews, and voice messages.
- Buds with configurable roles, appearance, personality, reporting preferences, and authorized tool connections.
- Coding workflows through Codex and Claude Code, with Auto routing, workspace defaults, and manual provider selection.
- Workspace context and product memory backed by source references, confirmed decisions, and permission checks.
- Builds in a separate project copy, observed check results, reviewable changes, and approval gates for applying or publishing work.
- Per-reader language preferences, multilingual prompts, and supported offline translation models.
- Meeting controls, local device checks, and consent-based transcript review where the required services are configured.

Staging checks have covered core collaboration, bounded OpenAI builds, Research follow-up, connector lifecycle behavior, and offline English/Hindi reader flows. Funded Claude builds, reliable two-device meeting acceptance, and final installer validation remain release gates. Provider availability depends on configuration and approval.

## Run locally

Use Python 3.12 and [uv](https://docs.astral.sh/uv/).

```sh
uv sync --frozen
uv run aedrova --demo
```

The demo uses sample data. To connect the application to configured services, run without `--demo` and follow the [identity setup](docs/google-sign-in.md) and [service setup](docs/milestone-3-setup.md) guides.

```sh
uv run aedrova
uv run aedrova --theme dark
uv run aedrova --settings-file work/preview.ini
```

The settings-file option isolates preview preferences. Configure credentials privately using the documented environment and operating-system credential storage. Keep secrets out of source control.

macOS and Windows distribution are planned. Packaging and operating-system acceptance must pass before public downloads are enabled.

## Development checks

```sh
uv run ruff check src scripts tests
QT_QPA_PLATFORM=offscreen uv run pytest -q
uv run python -m compileall -q src scripts
uv run python scripts/check_release_secrets.py --tracked
```

On Windows, set `QT_QPA_PLATFORM=offscreen` in the shell before running pytest. CI runs desktop checks on Linux, macOS, and Windows, plus PostgreSQL access-control checks.

Database setup lives in `supabase/migrations/`. Apply reviewed migrations in order to the intended environment. Use [the release timeline](docs/pre-launch-timeline.md) for staging and production gates.

## Packaging

```sh
uv run python scripts/package_desktop.py
```

Packaging requires the protocol-tested coding runtime and platform dependencies checked by the script. Public Mac distribution requires Developer ID signing and notarization. Windows signing, clean-machine installation, and release acceptance are also required. See [the Mac release checklist](docs/mac-dmg-launch-2026-10-18.md) and [final paid launch gates](docs/final-paid-launch-gates.md).

## Repository layout

- `src/aedrova/desktop/` contains the Qt interface, themes, onboarding, and interaction controls.
- `src/aedrova/agents/` contains routing, context gathering, provider adapters, and execution.
- `src/aedrova/dots/` contains Bud service clients and connector contracts.
- `src/aedrova/identity/` and `src/aedrova/meetings/` contain account and meeting behavior.
- `supabase/` contains migrations and database boundary tests.
- `scripts/` contains release checks, database validation, and packaging tools.
- `tests/` contains automated regression checks.
- `docs/` contains architecture, setup instructions, acceptance evidence, and remaining gates.

Generated builds and local evidence belong in ignored `build/`, `dist/`, and `work/` directories.

## Related project

The [Aedrova website repository](https://github.com/ayanshv/Aedrova-website) hosts the public site, onboarding, workspace billing, and managed backend services.

Product information and support are available at [aedrova.com](https://aedrova.com/) and contact@aedrova.com.
