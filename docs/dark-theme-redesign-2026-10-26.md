# Dark theme refinement — October 26, 2026

Implemented in the desktop source checkout; no production deployment or installer rebuild.

## Verified causes

Aedrova uses native PySide6, QPalette, QSS and custom QPainter surfaces, not Tailwind
or browser theme inversion. The old dark palette assigned the same #141415 to the
sidebar and workspace and the same #0C0C0D to shell/rail, while custom GlassFrame
painting and transparent child widgets inherited those limited layers. Composer
background reused the workspace background. Popup/menu backgrounds also reused it.

MessageDelegate.paint filled the entire row with theme.surface for either MouseOver
or Selected. That is the broad gray conversation stripe. It also rendered message
bodies with secondary text. Attachment previews were drawn as original QPixmaps with
no inversion, brightness filter or persistent opacity. Transparent dark marks blended
into the dark card. Send animations temporarily fade whole messages as designed;
that behavior is preserved. Connector marks independently use white tiles to keep
black provider glyphs legible; avatars retain their own colors.

## Implementation

Central Theme semantic colors now distinguish canvas #141519, workspace #191B20,
rail #121419, sidebar #171A20, secondary surface/composer #1F2229, header #17191E,
and elevated overlays #252832. Text #F1F3F7, secondary #B0B6C2, muted #A1AAB9,
borders #353C49 and brand-blue action #79A7FF form one shared palette. Added
header/elevated/composer/preview and accent hover/pressed tokens; Qt Midlight/Mid/Dark/Light roles also consume
these semantic values rather than platform default grays in loading states.

Dark-mode message selection uses a narrow accent marker, with a bounded focus outline;
hover no longer fills the row. Existing reaction controls and grouped timestamps
still respond to hovering. Dark message bodies use primary text; metadata remains
secondary. Explicit dark placeholder colors avoid Qt deriving a faint half-opacity
placeholder after stylesheet polishing. Image previews use a neutral matte beneath the original pixels, including
draft thumbnails. There is no recoloring or image mutation. Menus, tooltips, choices,
dialogs, active navigation and composer consume the shared tokens. Light palette,
layout, typography, existing controls and appearance persistence are retained.

## Verification

Pixel-rendering regressions cover dark hovered/selected/focused rows and unchanged
source image pixels plus transparent backing in both themes. Contrast assertions
check primary/secondary/muted text at >=4.5:1 on all five key dark surfaces and action
text >=4.5:1; blue focus/action contrast >=3:1 on controls. Theme initialization,
switching, persisted system preference and reduced-motion preservation are tested.

Actual Qt widgets were rendered offscreen with synthetic local-only data in both
light and dark: workspace, composer active/inactive, menus, dialog, preferences,
connector gallery/loading, Project, Work, Files and People. Screenshots and repeatable
renderer: work/dark-theme-review/. No real account or uploaded private media was used.
This verifies application content rendering, not OS-native titlebar behavior, real
OAuth, provider responses, physical-device display color or packaged-installer parity.
Those were not needed to change styling and are not claimed as re-certified.

Four old visual assertions required updating: dark selected workspace is now the
semantic accent background, and dialogs/confirmation boxes/profile menus use the
new elevated surface instead of sharing the workspace color. Their pixel/palette,
clickability and theme-switch coverage remains intact. An embedded People panel
is explicitly marked as workspace content so it does not inherit dialog elevation.

76 focused shell/theme/visual/connector tests passed after those assertions changed;
7 focused theme checks passed after final placeholder refinement. Ruff and diff
checks passed. Full desktop rerun: **1008 passed**, one existing audioop deprecation warning.
Final semantic hover/pressed color refinement: **7 focused theme checks passed**;
normal, hover and pressed action text all meet the asserted contrast threshold.

Existing Stage 1 acceptance blockers remain independent of this visual change.
