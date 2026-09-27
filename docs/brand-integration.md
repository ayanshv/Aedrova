# Aedrova brand integration

The supplied transparent PNG is preserved at `src/aedrova/desktop/assets/aedrova.png`.
Display framing excludes nearly transparent export noise and keeps space for the halo.

The mark appears beside the app wordmark, in the quiet AI presence, and in About.
The macOS app bundle and application icon use a multi-resolution ICNS with a charcoal
rounded backdrop. Regenerate it with `uv run python scripts/prepare_brand_icon.py`.
PyInstaller explicitly bundles both brand resources.

Mint, blue and violet ambient light now echoes the logo while the interface retains
neutral surfaces and restrained blue action accents. Marks gently lift on hover;
Reduce motion disables the effect, including newly opened About dialogs. There is no
continuous animation or simulated agent activity.

Validation: 57 tests passed in 14.32 seconds; Ruff passed. Fourteen visual snapshots
were regenerated and representative light/dark layouts reviewed. The rebuilt app
passed deep/strict signature verification and launched from /tmp with bundled assets.
It remains an ad-hoc-signed local preview, not a public notarized release.

Milestone 3 remains paused pending approval.
