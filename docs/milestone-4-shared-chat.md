# Milestone 4 — code delivered; hosted acceptance pending

## Required owner action

Run `202609280001_communication.sql` in your existing Supabase project's SQL Editor. Apply it after the three migrations you already ran; do not rerun earlier migrations or any files under `supabase/tests`. The new migration preserves existing workspaces/messages, adds DMs, read cursors, bounded private attachments, history cursors, and content-free realtime triggers. It configures the existing private bucket for uploads up to 10 MiB using application/octet-stream.

Keep Realtime public access disabled. No Google OAuth changes, new API keys, SMTP, or new services are needed. Restart with the rebuilt Aedrova.app and sign in again (sessions remain in memory).

## Using the unchanged desktop layout

- Create workspaces using the existing onboarding and open them with Go to dashboard.
- Create channels using the existing +/Workspace controls. Select a private channel in workspace settings to manage explicit access.
- Start a DM with **⌘⇧M** and choose a teammate in the native selection dialog. The conversation appears in the existing Direct Messages list. DMs are scoped to a workspace, limited to two non-guest members, and excluded from third-party admins' access.
- Attach a file with **⌘⇧U**. Files must contain 1 byte–10 MiB. Transfers run in the background and use immutable paths. Select a file message and press **⌘⇧S** to save it with the native Save dialog. Nothing is automatically opened or executed.
- Existing message views display file names and thread replies. Click a message to open its thread. **⌘⇧H** loads older channel messages; scrolling upward at the top of the message or thread view loads that view's older history. History uses bounded 100-record keyset pages, not a fixed last-500 limit.
- Unread counts appear alongside the existing channel/DM names. Read positions are stored per user/channel and cannot move backward. They advance while the active chat is visible at its latest messages.
- Private realtime events contain no message bodies or identifiers: they only wake a permission-checked refresh. Three-second polling repairs missed events and checks current access. Transient failures use backoff up to 30 seconds and retry queued sends with stable IDs. Permission/validation failures are not automatically retried.

## Live acceptance — needs two Google accounts

1. Sign into the updated build with your account, create/open a workspace, send a message and reply, then restart and check persistence.
2. Invite a second Google account. In a second app instance/device, join with that exact account. Confirm new messages and replies appear on both sides.
3. Start a DM; confirm it is visible to its two participants and invisible to an unrelated workspace admin/member.
4. Attach a harmless test file, download from the other account, and verify the bytes. Try an empty/over-10-MiB file; confirm it cannot publish. No secrets or private production files are needed for testing.
5. Send while the recipient views another channel. Check the unread count, open/read the channel, and check it clears across sessions.
6. Temporarily disconnect networking, queue a test message, reconnect, and confirm it appears once. Unsent drafts/retry IDs are memory-only and are lost when the app exits; durable execution queues belong to milestone 8.
7. Remove the second account or revoke its private-channel access. Confirm history/files become unavailable, queued sends are denied, and refresh does not restore unauthorized content. Previously downloaded files cannot be remotely erased.
8. Test the OAuth callback page on a fresh sign-in: Aedrova logo, soft glass, automatic light/dark appearance, and a clear instruction to return to the app. The page never claims token exchange has completed before it actually has.

These actions are required to finish milestone 4's hosted acceptance. Embedded PostgreSQL and fake-transport UI tests do not validate deployed Auth, Storage upload middleware or WebSocket permissions end to end.

## Validation and boundaries

Automated coverage includes private DM denial, idempotent creation/sends, channel/thread pagination, unread cursors, immutable attachments, uploader ownership, private file access, membership revocation, content-free broadcast payloads, retry classification/queueing, bounded/hash-verified downloads, upload response-loss recovery, native action wiring, and OAuth callback security headers/content. The callback's dark and light rendering were inspected in a browser.

Desktop layout, theme, spacing, and styling were not redesigned. Existing controls receive connected data; shortcuts and native dialogs expose new actions. The OAuth browser page was styled only after milestone 4 implementation passed its initial code/database checks.

Files are opaque private downloads, not malware-scanned. Interrupted unpublished uploads can remain private in Storage; expiry prevents reuse, and orphan cleanup/quota hardening belong to the final safety audit (milestone 13). Full abuse/rate-limit controls, public release signing/notarization, and durable offline persistence are not claimed here. The owner has deferred the full audit until feature development is complete, before public launch. Essential permission and execution-isolation safeguards remain part of each implementation milestone.

## Next milestone

5: first real agent build—connect one repository and one provider, assemble permitted chat context, approve a plan, run an isolated implementation, stream progress and tests, then review the diff. Repository push remains a separate explicit approval. The full safety audit is deferred to milestone 13 at the owner's request.

Owner clarification: the two-account observation was successful isolation between separate workspaces, not a chat-delivery failure. That check does not establish same-workspace sharing, file/realtime delivery, or every other hosted acceptance scenario.
