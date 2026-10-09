# Buds — setup and current capabilities

Buds are workspace-owned connections to useful sources. Their names, planet styles,
colors, roles and instructions personalize how Aedrova finds context. Buds use the
central AI's existing model access; a name or instructions never expand permissions.

## What changed

- Six native setup screens: introduction, appearance, name/color, purpose, tool connection, ready.
- Editable name, role, instructions, planet/moon/ringed planet and eight colors,
  plus a custom color picker. Live previews, blinking and gentle motion respect
  reduced-motion preferences. No blush or ornamental robot parts.
- Bud drafts can be saved while provider OAuth setup is pending. The final ready
  screen requires a real connection; unsupported providers remain unavailable.
- Ten read-only adapters and multiple private resource connections per Bud are implemented; see `docs/bud-connectors.md` for scopes, setup and live-validation gates.
- Bud mentions preserve existing identifiers, so earlier conversations and grants
  continue to work. The internal table/API names remain workspace_dots and /api/dots.
- Neutral charcoal dark surfaces across the app; blue remains an accent.
- Empty meetings no longer display a join notification or active header indicator.

## Required owner action

Run the complete file `supabase/migrations/202610070002_bud_profiles.sql` in the
existing Supabase project's SQL Editor. The prior workspace_dots migration must
already be installed. This update adds role/instructions, retaining all existing
identities and permission checks. It can safely be rerun.

Without the update, profiles with empty notes can still use the earlier RPC.
Profiles with a role/instructions show a clear migration-required error rather
than silently discarding input. New fields cannot be fully validated against
hosted Supabase until you apply the migration.

## Real GitHub connection

Follow the GitHub App instructions in `docs/dots.md`. Use callback
`http://127.0.0.1:8090/dots/github/callback` for the current local service.
Server credentials belong in `/Users/ayanshvarma/Documents/Aedrova_site/.env.dots`,
using that repository's `deploy/dots.env.example`; never paste secrets in chat.
The local launcher now loads this file when present and enables Buds by default,
while keeping checkout, public release and downloads disabled.

Restart the local server after adding credentials. Sign in to its website using
the same Google account as the desktop. In Buds, save your repository profile,
connect GitHub, finish consent, and refresh. Each teammate authorizes their own
access. Existing provider tokens never enter the model or shared profile table.

Next acceptance task: connect a chosen provider and verify source-backed answers,
revocation and independent account boundaries. Stripe currently supplies account
balance only; revenue reporting is separate future work.

## Sculpted reference artwork — October 7

The Buds now use six reference-derived, local 3D sprites: cap, brush, star, glasses,
magnifying glass and sprout. Their paired vertical eyes have no mouths or blush.
The shared renderer displays these assets in both the habitat and configuration.
Existing reduced-motion and bounded local physics behavior remains intact. Body
color variants are cached rather than regenerated each animation frame. No model
or network request is needed to display or animate a Bud.

Appearance can match a role automatically, or be explicitly selected independently
of that role. Earlier round/squircle/cloud values retain automatic fallback mapping.
Run `202610070003_bud_appearance.sql` AFTER `202610070002_bud_profiles.sql` in Supabase
SQL Editor to persist explicitly selected appearances across team devices. Existing
profiles work with automatic appearance before this additive update. Tool OAuth
configuration and permissions are unchanged; visual customization grants no access.

## Reference-led Bud setup refinement

The centered warm-white/charcoal panel follows the supplied onboarding composition,
with sculpted character previews, image-led choices, compact color swatches,
short copy, step indicators and restrained native fades. Reduced motion disables
fades. Appearance, name/color and role/instructions each have their own page;
real provider authorization remains the final gate before chatting. No additional
database update is required for this layout. Refreshing connection status preserves
the current setup step, and Back preserves draft fields. Unimplemented provider
adapters are still marked unavailable rather than shown as connected toggles.

### macOS color-control rendering fix

The page-level opacity effect conflicted with child SpringButton graphics effects
on Cocoa. Fades now apply only to the character artwork. Swatches and Custom color
render directly in the page; native Cocoa regression tests verify their rendered
colors and selection in both light and dark themes. No database changes required.

## Role-specific connector sets

Bud setup now separates **specialty** from **appearance**. Choose Builder, Designer,
Marketing, Finance, Research or Product, then add optional purpose and instructions.
The specialty and purpose persist in the existing role metadata; no new SQL is needed.
Existing freeform purposes are preserved when unchanged. A character's look never grants access.

| Specialty | Primary tools | Additional recommendations |
| --- | --- | --- |
| Builder | GitHub, Supabase | Vercel, Linear, Sentry |
| Designer | Figma, Notion | Google Drive, Linear |
| Marketing | Instagram, TikTok | Meta Ads, Google Analytics, PostHog, Notion |
| Finance | Stripe | QuickBooks, Google Sheets, Notion |
| Research | Workspace AI model, Web search, Notion | Google Drive, PostHog |
| Product | Notion, Linear, PostHog | GitHub, Supabase, Figma, Stripe, Search, AI model, Instagram, TikTok, Google Drive |

The gallery now implements GitHub, Supabase, Figma, Notion, Stripe, Instagram,
TikTok, Brave Search, Vercel and Linear. Other recommendations remain future adapters.
Each Bud supports up to twelve independently authorized resource connections per
user. Role suggestions never grant access. The workspace AI model uses existing
provider configuration; no additional model subscription is provisioned by a role.

Run `202610070004_bud_connectors.sql` after the earlier Bud migrations. Follow
[connector setup](bud-connectors.md) for credentials, exact read boundaries and
remaining live acceptance. Existing GitHub OAuth remains compatible; token-based
GitHub connections do not require the owner's GitHub OAuth app configuration.
Social publishing, finance mutations and deployments remain separate future work.
