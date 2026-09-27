# Milestone 2 — desktop experience

## Scope

A functional, Python/Qt local UI using explicit sample data. No network requests or
service credentials. Messages, replies, drafts and newly created spaces stay in memory;
only appearance and reduced-effects preferences are saved through QSettings. This is intentional until the
identity and reliable communication milestones. It is not a production chat service.

## Design

A narrow workspace rail, a channel sidebar, and a conversation-first main area. Semantic
light/dark colors live in `desktop/theme.py`. System typography, generous spacing,
24-pixel rounded floating panels, capsule tabs and neutral avatars establish hierarchy.
Light uses #F5F5F7 and white; dark uses black and #1C1C1E. Blue is reserved for primary
controls and small accents, following a restrained 60/30/10 visual hierarchy.

`desktop/materials.py` renders a cached, blurred in-app aura behind translucent surfaces,
with soft ambient shadows and specular edges. This is Python/Qt frosted glass, not the
native macOS Liquid Glass API or desktop refraction. Projects and Files use responsive
bento grids that become a single column in compact layouts.

Buttons scale gently on hover, compress on press and spring back on release without
moving their layout or hit targets. View → Reduce motion disables these animations;
View → Reduce transparency makes surfaces opaque. Both preferences persist.

Chat, Projects, Builds, Files and Meetings are navigable views. Projects and Files contain
readable sample references. Builds explicitly shows that no build has run. Meetings
explains its upcoming status; no call, camera or microphone control is simulated.

Thread details sit beside the conversation when at least 940 logical pixels are available
in the chat area. At smaller widths, the thread temporarily occupies that area; closing it
restores the conversation and its draft. The minimum window is 900 × 650 logical pixels.
The channel sidebar can be collapsed. The workspace rail scrolls as more spaces are added.

## Interactions

- Switch workspaces from the rail or workspace menu.
- Switch channels/direct conversations using the sidebar or quick switcher.
- Create local workspaces and channels through validated dialogs.
- Compose messages; Return sends, Shift+Return inserts a line break.
- Click a message or select it and press Return to open its thread.
- Reply in the thread; drafts stay scoped to workspace, channel and thread.
- Copy a selected message using the context menu or the platform Copy shortcut.
- Open the pinned sample decision directly.
- Mention button inserts `@Aedrova`; sending does not invoke a model or invent an agent reply.
- Open and copy sample documents from Files or Projects.
- Toggle light/dark with the top-right control; select System in View → Appearance.

Mac shortcuts:
- Command+K: jump to a workspace, channel or person.
- Command+1–5: switch tabs.
- Command+Shift+L: toggle light/dark.
- Escape: close a thread or modal dialog.
- Tab: leave the composer and move to the next control.

## Rendering and accessibility

ConversationModel plus MessageDelegate render variable-height text and sample attachment
references without allocating a QWidget for each row. A 512-entry LRU document cache bounds
layout memory. Messages are rendered as literal text; HTML-like input cannot load remote
content or execute markup. Message content is limited to 10,000 characters in this preview.

Controls expose accessible names and descriptions. Message model roles expose authors,
content and reply counts to Qt accessibility. Standard keyboard navigation and visible
focus borders are retained. Automated checks cover names, focus and key interactions;
full VoiceOver user testing remains a separate accessibility validation requirement.

## Boundaries

No login, remote workspace creation, persisted messages, invitations, real file uploads,
search across message content, active AI, builds, meetings or billing are implemented here.
The fixture store is kept separate from presentation so services can replace it later.
Service authorization must remain server-enforced; UI visibility is not a security boundary.

No image assets, web frontend or non-Python application logic were introduced.
