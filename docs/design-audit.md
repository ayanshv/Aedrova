# Aedrova Workroom design pass — October 6, 2026

The attached design brief authorized a structural frontend redesign. The product model
remains workspaces, conversations, source-backed context, projects and permission-controlled
AI work. No database schema, authentication protocol, provider invocation, billing allowance
or permission boundary was changed by this pass.

## Design system

Neutral edge-to-edge workspace surfaces replace floating glass panels and background auras.
Blue identifies selection, focus and primary actions. System typography uses a 30/24/18/14/12/11
pixel hierarchy; spacing follows 4/8/12/16/24/32/48. Controls use 7px corners, panels 10px and
popup menus retain the previously requested borderless 16px corners. Outline icons share
one stroke weight. Hover changes color; press feedback is restrained and honors reduced motion.

## Product structure and changes

- Compact global search header and continuous channel sidebar; the main conversation has more space.
- Conversation / Project / Work / Files navigation. Team context and Queue are adjacent utilities.
- Work exposes the existing build studio, queue/history and shared evidence. The connected Files
  landing exposes the actual permitted file browser rather than an obsolete milestone placeholder.
- Messages retain rich text, reactions, attachments, metadata, threads and the existing final-message
  scroll boundary. Body text has a maximum reading width. AI senders have a small AI identity marker.
- Product memory and shared reviews use responsive list/detail layouts. Long lists elide titles
  rather than creating horizontal scrollbars. Existing access, source review and approval remain intact.
- Teammate configuration separates Purpose and tools from Personality. Required tool verification,
  role suggestions, sliders, character customization and sidebar behavior remain intact.
- Settings groups Account, Appearance, Workflow and Plan & AI access. Profile, onboarding, account
  setup and call/device surfaces inherit the same typography, colors and controls.
- Narrow dialog actions wrap instead of squeezing buttons. This applies to build, evidence, context,
  connectors, delivery review, queue, projects and meeting text actions.
- Literal ampersands render correctly in button labels without exposing mnemonic underscores.
- Onboarding and sign-in lose decorative background auras; theme selection uses fresh actual UI captures.
- The local website uses matching neutral/blue colors, system titles, quieter surfaces and reduced
  radii/shadows. Centered navigation, cinematic footage, forms, prices and backend behavior remain.
  Actual desktop screenshots were refreshed locally; sample data stays explicitly labelled.

## Inspection and verification matrix

| Area | Coverage |
| --- | --- |
| Main workspace | Light/dark, normal/compact, channels, DMs, drafts, thread navigation, empty channel |
| Chat controls | Send/newline, mentions, emoji/reaction menus, editing/unsend, formatting, saving, search, file actions |
| AI experience | In-chat activity/final result, stop controls, studio empty state, queue/recovery, permission checks |
| Context and review | Memory proposal/approved/source states, revision actions, build evidence, diffs and review controls |
| Teammates | Role/tools, required connection, personality, discrete sliders, shelf, compact editor |
| Identity/settings | Google sign-in, workspace creation/invites, all three profile stages, grouped preferences |
| Meetings | Audio/video layouts, devices off, roster/control state, device checks, privacy/transcript controls |
| Onboarding | Introduction and actual setup stages in both themes, compact controls, appearance photos and tour tests |
| Website | Homepage/navigation, plans, onboarding, sign-in, shared page styles; 390px light/dark browser checks |
| Package | Rebuilt native app, deep signature verification, isolated-settings packaged smoke report |

Reproducible actual-widget captures are in `work/design-audit`, `work/milestone-2`,
`work/milestone-3`, `work/onboarding-refinement`, `work/m15`, `work/m16`, `work/m17f1`
and `work/website-screenshots`. `scripts/capture_design_audit.py` captures 30 additional
native views with disposable sample data, no network calls and no device capture.

615 desktop tests and 247 website tests passed. Three added layout tests cover narrow action
wrapping, dynamic build-action insertion and list/detail selection after resize. The visual
background check tolerates one RGB channel of native macOS rounding while retaining exact
palette verification. Delivery/queue checks were rerun after their final layout change.

This is local visual acceptance, not a repeat live acceptance test for payment, OAuth, provider
credentials or physical meetings. Existing launch/integration limitations remain in their
milestone documents. There was no push, deployment, live payment or access grant in this pass.

## Owner actions

No new SQL, credentials or configuration are required for this redesign. The rebuilt app opens
at normal Google sign-in; sign in normally to inspect the connected workspace. Publishing the
website changes is a separate authorized action. M17F.2 shared teammate results/history and
team management still require permission. M14 release/signing/live billing gates remain deferred.
