# Message reactions, emoji and unsend

Channels, direct conversations and threads share the same interactions. Hover a sent message for 👍 ❤️ 😂 🎉 👀 and a plus button. Plus opens an offline searchable picker with 3,944 Unicode Emoji 17 entries, including modifiers, flags and joined sequences. Existing reaction chips show totals and highlight the current user's reactions; clicking toggles only that user's reaction. The same picker opens from the composer smile button and inserts at the current cursor.

Right-click a message you sent and choose **Unsend message**. The original body, attachment metadata and recorded decision are removed; reactions clear. A small timestamped “Message unsent.” marker preserves thread references and replies. Unsend cannot retract copies someone already saw/downloaded or outputs of earlier builds. Context revision counters invalidate context collected before the change. Reactions and unsends synchronize through private content-free wakeups and polling, including edits to messages with old sequence IDs.

## Required owner action now

1. In the Aedrova Supabase project, open **SQL Editor → New query**.
2. Paste the entire file `supabase/migrations/202610040001_message_interactions.sql` and click **Run** once. The earlier migrations must already be installed, as in the current project.
3. Quit Aedrova and open `/Users/ayanshvarma/Documents/Aedrova/dist/Aedrova.app`; sign in again. Existing chat stays usable if the migration is absent, but shared reactions and unsend cannot work until it is applied.

No new account, key, provider or paid service is required. Do not execute this migration twice: the table/function creation is intentionally a versioned one-time migration.

## Verification

The embedded PostgreSQL suite applies the actual migration and covers two-account totals, idempotent retries, Unicode combined emoji, owner-only unsend, retained replies, erased decisions, revoked file access, outsider/private-channel/revoked-member isolation, blocked direct writes and anonymous access, and content-free notifications. Python/Qt journeys cover picker search and selection, cursor insertion/cancel, chip toggling, local ownership checks and reconciliation of reactions/unsends on already cached old-sequence messages. Native captures were reviewed in light and dark themes. Hosted two-account acceptance remains pending the owner applying the migration.

Catalog provenance: https://unicode.org/Public/17.0.0/emoji/emoji-test.txt; Unicode license is bundled under desktop/assets/licenses/Unicode-LICENSE.txt.

## Reaction responsiveness refinement

Shared reactions now update on click, before the network request completes. Pending
intent overlays incoming polling data so slow reads cannot undo the visible choice.
Rapid toggles for the same message/emoji coalesce to the latest intent, with one job
at a time. Reaction writes run ahead of background work and read back only the affected
message's interaction state rather than waiting for an entire workspace refresh.
Failed confirmations revert the pending reaction and keep chat visible; the failure
notice remains visible through background refreshes. Sign-out clears pending state.
No new SQL or configuration is required. Server access checks and rate limits remain.
