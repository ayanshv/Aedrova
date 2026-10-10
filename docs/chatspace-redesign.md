# Conversation-first chatspace — October 6, 2026

This pass redesigns native Qt presentation and interaction hierarchy. It does not change
service calls, routing, authentication, database schemas, AI execution, permissions or billing.

## Navigation

The left rail shows the current workspace, an all-workspaces switcher, creation and account.
All workspace identities remain available through the existing named workspace menu and search.
The sidebar groups workspace identity/invitation, living AI teammates, workspace tools,
channels and direct conversations. Selected channels use an edge marker rather than a pill.

Conversation, Project, Work and Files remain the primary views. Activity, Saved, Team context
and Queue move into a keyboard-accessible Workspace tools accordion. Unseen activity counts
remain visible on its collapsed heading. The existing chat-tools menu remains beside the views.
The guided tour expands this accordion when spotlighting its controls.

## Conversation and composer

Nearby messages by the same sender group visually, with one avatar and sender header. Actual
messages are not combined: reactions, replies, links, attachments, editing and deletion retain
individual targets. Group boundaries respect sender IDs, date/time, delivery state, confirmed
decisions and visible edited/saved/pinned metadata. Grouped timestamps appear in the gutter on
hover; full author/time remain in accessibility text. Following rows relayout after edits.

The composer is a single command surface: recipient/build cue, multiline editor and restrained
controls for uploads, named-agent invocation, people mentions, formatting, emoji and sending.
Thread composers identify the thread. All original shortcuts, completion and draft behavior remain.
The repeated exterior explanatory footer is replaced by the integrated cue. The global shortcut
footer and timestamps retain the previous accessible light/dark contrast.

AI output continues to live in the conversation with the existing named sender, compact character,
AI identity marker, activity disclosure, stop control and final result. No separate chatbot or
oversized message cards were introduced. Idle character animation and reduced-motion support remain.

## Validation

618 desktop tests pass, including three added redesign regression journeys. Tests cover grouping
boundaries and per-message actions, keyboard expansion and the single visible rail identity.
Existing navigation, drafts, thread, mention, reaction, upload, tour, call, AI, identity and safety
suites pass. Lint passes. Normal/compact light/dark screenshots and 30 additional real-widget
screens cover secondary views, settings, profiles, project connection, build studio, queue and calls.
Sample captures use disposable fixtures and do not perform device capture or live provider work.

This does not re-certify live OAuth, payments, external APIs or physical meetings. Their existing
setup and rollout gates remain unchanged. No commit, push or deployment was performed.

## Owner action

Quit Aedrova and reopen `dist/Aedrova.app` to load the rebuilt design; sign in normally if prompted.
No new SQL, credentials or permissions are required. The website was not changed by this task.
M17F.2 remains approval-gated.
