# Chat collaboration — October 5

## Owner action required now

You already applied `202610040001_message_interactions.sql`; **do not rerun it**.

1. In the existing Aedrova Supabase project, open **SQL Editor → New query**.
2. Copy the **entire** `supabase/migrations/202610040002_chat_collaboration.sql` file into the editor and **Run once**. This versioned migration is not designed for repeated application.
3. Quit Aedrova and reopen `dist/Aedrova.app`. Sign in again if prompted. Restart resets the client's missing-migration fallback.

This unlocks group DMs, shared edits/topics/posting policies, saved/pinned messages, statuses/presence, typing, notifications and workspace search. Existing chat and previously enabled reactions remain usable before applying it. No new keys, paid services or external accounts are required.

Shared hosted acceptance remains pending until this migration is applied and two accounts exercise these features in the same workspace. Local SQL tests use actual PostgreSQL and actual migrations, but are not a hosted Supabase acceptance test.

## Feature inventory and entry points

| Requirement | Implementation / entry point |
|---|---|
| Workspaces / organizations | Existing workspace creation, switching, archive/restore and invitation onboarding reviewed |
| Public/private channels | Existing channel creation and channel-member grants reviewed; private channels remain filtered by RLS |
| Topics and descriptions | Chat **••• → Channel details & members**; owners/admins edit |
| Direct messages | Existing ⌘⇧M picker, or **People & presence → profile → Message** |
| Group DMs | **••• → Start group DM**; choose 2–20 teammates; private participant-only conversation |
| Threads / replies | Existing message click / context menu / Return; quoted messages additionally available |
| Reactions / multiple reactions | Five quick emoji, full Unicode picker, per-user toggle and shared counts |
| Editing and deletion | Own delivered message context menu **Edit message** or **Delete / unsend message** |
| Reply / quote | **Reply in thread** or **Quote message**; quotation inserts editable Markdown in the composer |
| @user / @channel / @everyone | Type @ and part of a name + Tab/Return, or use the composer’s mention dropdown. Teammate IDs are encoded on send; readable names stay in the editor and message UI |
| Rich text and code blocks | Markdown rendered safely; **Aa** offers bold, italic, inline code, code blocks, lists and links. Raw HTML stays literal |
| Files/images | **＋** in either composer; protected uploads; click attachment to preview or save; images retain aspect ratio |
| Drag/drop | Drop files into chat or composer; maximum 10 files per drop, existing 10 MB/file upload boundary |
| Timestamps | Existing sender/time/date retained; edited/pinned/saved markers added |
| Unread / read state | Existing per-account cursors/counts plus message **Mark unread**; automatic cursor advancement pauses until leaving that channel |
| Typing | Short-lived per-channel indicators; expiry 8 seconds; scopes checked server-side |
| Online / away presence | People/profile views; 30-second heartbeat, offline after 90 seconds without heartbeat, automatic idle away after 5 minutes |
| Notifications | Persisted mention, direct/group DM, thread participation and optional all-channel notifications; activity badge and in-app notification banner. No email/push notification delivery is claimed |
| Notification preferences | **••• → Notification preferences**; all, mentions/DMs/replies, or muted for the current channel |
| Search messages/people/channels/files | Top search or ⌘F, scoped to accessible content in current workspace; ⌘K retains conversation switching; bounded to 100 message results per query |
| Pinned/saved/bookmarks | Message context menu; **Saved** is account-private; pins are team-visible and administered by owners/admins |
| Link previews | Click link / **Preview link**. Destination preview appears immediately; optional **Load page preview** reads bounded public HTTPS metadata only on request. No automatic remote image fetch |
| Channel members | Channel details shows actual accessible membership; **Manage members and permissions** opens existing administration UI |
| Invitations/profiles/roles | Existing invitations and owner/admin/member management reviewed; profiles show name, role, presence/status and Message action; existing account settings edit display name |
| Channel-specific permissions | Existing private channel grants/revocation plus new owners/admins-only posting policy enforced across sends/replies/uploads |
| Forwarding/sharing | **Forward / share** copies text to a chosen accessible conversation; attachment files stay in the original conversation, clearly disclosed |
| Copy message link | **Copy link to message** creates an `aedrova://chat/...` link. Packaged Mac app registers the scheme. Recipient must sign in and have channel access |
| Activity center / recent activity | **Activity** and **••• → Recent activity**; click notification to open its message/thread and mark it seen |
| Custom status | **••• → Set your status**; online, away, do not disturb plus status text |
| File browser | **Files** in the chat tools searches all visible uploaded files across current workspace; select to preview/save |

## Access and lifecycle

All shared operations run with the user's Supabase JWT. SQL security-definer functions use an empty search path, explicit identity/membership checks and bounded requests. Tables have select-only authenticated grants with RLS; mutations are RPC-only. Workspace locks serialize edits and group creation against membership revocation. Group creation and reaction/write retries retain idempotent IDs/state. Requests have per-user rate budgets.

Edits invalidate confirmed decisions tied to the old text and bump existing AI context revisions. Unsend preserves reply relationships, erases original message content and revokes attachment access. Saved/pinned/search/activity reads exclude unsent content. Already downloaded/copied/forwarded text and previously completed builds cannot be retroactively erased.

Link metadata uses HTTPS, verified TLS, a public IP pinned for the connection, no redirects, no cookies or credentials, a four-second socket timeout and a 100 KB read bound. Markdown resource loading cannot read local files or automatically fetch remote images.

Presence is approximate and expires if a Mac sleeps/quits. Typing and reads are per channel, notifications honor channel preferences; do not disturb suppresses transient banners while retaining activity history. Notification delivery here is in-app, not email or OS push. Search results are capped; narrow the query for older matches.

On logout, dialogs, name completions, status/typing data and collaboration views are cleared immediately. Requests/results also check workspace/session context before rendering.

## Verification

- Full Python/Qt regression suite plus new collaboration journeys.
- Actual migration/SQL assertions: sender-only edit, stale decision invalidation, private/group DM isolation, private-channel search protection, account-private saves, admin-only pins/posting, mention/DM notifications, mute/seen/unread state, typing, status, revocation and anonymous denial.
- Qt journeys cover readable Markdown, literal HTML, mention ID encoding, edit/reply preservation, save/quote, file-drop destinations, logout cleanup, stale results and inaccessible message links.
- Link-preview checks reject private IPs, credentials, non-HTTPS pages and nonstandard ports.
- Rendered widget checks in light and dark themes; rounded result lists, wrapped snippets and compact controls.
- Rebuilt signed preview app and bundled protocol registration.

## Hosted acceptance after migration

Use two signed-in accounts joined to the same test workspace. Check one-to-one/group DMs, mentions, activity badges, typing/presence, edits/reactions, saved privacy and pin sharing. Create a private channel excluding account two and confirm search/links/notifications never expose it. Set an admin-only posting policy and verify account two cannot post. Revoke a member and confirm access disappears. This is separate from M14 release/provider activation.
