# Slack and Microsoft Teams migration

Planned October 5, 2026 at the owner's request. No importer is implemented or activated
by this document. Add M17A–M17E after M17 and before M18 launch acceptance; retain
existing milestone numbers. Test and report each stage, then obtain approval for the next.
The final codebase walkthrough follows deployment of this work as well.

Goal: a team arrives with its accessible history, familiar organization and identities
intact, verifies the result, then switches without losing newly created work. “Seamless”
means guided and recoverable, not a promise to bypass source-platform restrictions.

## M17A — migration foundation and guided preview

Build one Python migration pipeline with source adapters and a stable intermediate model
for users, memberships, channels, chats, messages, threads, attachments and reactions.
Keep source IDs, original timestamps, provenance and import batch IDs. Validate archives,
reject unsafe paths/oversized payloads and sanitize rich text and URLs. Stream large
imports through durable jobs with resumable checkpoints, cancellation and bounded retries.

Add a native migration wizard: choose source → connect/upload → select history/channels →
map people and destinations → preview → approve import. Show counts, sizes, unavailable
content, estimated workload and permission conflicts before writing anything. Default
private conversations to excluded unless explicitly selected and safely mapped. Imports
must not send historical notifications, invite people or launch AI builds.

Acceptance: preview writes no live chat data; malformed archives are rejected; interruption
and retry produce no duplicates; unauthorized users cannot initiate or inspect imports.
Test large synthetic datasets and accessible progress/error states on Mac and Windows.

## M17B — Slack importer and familiar first day

Support official Slack JSON ZIP exports first. Preserve available channel names/topics,
authors, timestamps, threads, edits/deletion markers, supported formatting and reactions.
Import pins/bookmarks and other metadata only where supplied by the source and supported
by Aedrova. Report unsupported custom emoji, apps, workflows and missing data explicitly.

Exports include file links, not a guarantee of file bytes. Download only authorized
accessible assets through controlled fetching, preserve source references, deduplicate
by content and show missing/expired attachments. Do not treat source retention gaps as
an importer bug or recover data Slack no longer exposes.

Map source identities to verified Aedrova accounts; unmatched/deactivated people become
historical attribution only, never impersonated accounts. Never grant roles by display
name or unverified email. Preserve private channel/DM membership; unresolved identities
keep restricted history inaccessible until safely resolved. Retain source membership
limits even when merging into an existing channel; block merges that broaden access.

Acceptance: representative export reconciles counts and ordering; threads/reactions/files
open correctly; duplicate imports are idempotent; two-account isolation passes; invitations
are previewed and sent only after a separate explicit admin action.

## M17C — Teams importer and account compatibility

Implement a read-only Microsoft Graph adapter with tenant-admin authorization and narrow
required permissions. Discover teams, public/private/shared channels, 1:1/group chats and
available history; preview supported and unavailable sources before fetching at scale.
Preserve available message/reply authorship, times, edits, reactions, HTML formatting and
channel structure. Handle pagination, throttling, token expiry/revocation and checkpointed
retries. Files may require separately authorized SharePoint/OneDrive access; request it
only for selected attachments. Report missing meeting recordings/transcripts, cards,
applications, tenant/retention restrictions and external/shared-channel limitations.

Add Microsoft sign-in/account linking for Teams users before inviting them. Linking
requires proof of both accounts, prevents duplicate identities and never automatically
merges accounts based only on matching email. Do not require a Teams user to adopt Google.

Acceptance: tenant-authorized real test import, no cross-tenant/private leaks, revoked
access halts fetching, duplicates/retries reconcile and attachment failures remain visible.
Admin restrictions are explained with exact owner actions instead of silent partial success.

## M17D — staged rollout, catch-up and migration verification

Start in a staged destination that ordinary members cannot see until approved. Let admins
inspect representative channels, identity mappings, files and a reconciliation report.
Promote only verified data while preserving source history/provenance. Offer a pilot with
one team/channel before full migration and a final catch-up window at cutover. Slack ZIP
catch-up uses a newer export; Teams uses supported date filters/change mechanisms after
verifying their limits. Explain what needs a temporary posting freeze for accurate cutover.

Provide import-scoped rollback that removes only imported objects and index entries,
never new Aedrova messages or shared files used by other data. Separate preexisting user
changes from imported revisions. Keep a migration log with counts, omissions and errors.
No bidirectional chat bridge or silent writes/deletions on Slack/Teams in this scope.

Acceptance: pilot → catch-up → final promotion preserves new destination work; new source
messages and supported edits reconcile; rollback and retry are safe; completeness warnings
are acknowledged before cutover. Do not recommend cancelling the source service until
admins approve reconciliation and retention requirements.

## M17E — context continuity and migration launch acceptance

After explicit approval, index imported accessible conversations/files for cited retrieval.
Treat historical suggestions as unapproved candidates, never automatically confirmed
product decisions. Keep imported DM/private-channel restrictions, deletion and revocation
in sync with retrieval. Do not interpret an imported meeting transcript as consent for AI
reuse; require the existing consent/review process. Historical @mentions never execute.

Add concise source-specific onboarding, familiar shortcut guidance and admin/team checklists.
Verify search, original dates/authorship, notification quietness, source citations and
permission-scoped agent context on realistic datasets. Test archive safety, hostile text,
SSRF/file fetching, quotas, retention/deletion, job access, account linking and recovery.
Run a real authorized Slack pilot and Teams pilot, plus Mac/Windows UI/accessibility tests.
Publish measured migration results and exact supported coverage; never promise lossless
imports for unavailable source data. Update website migration copy and real screenshots
only when features pass acceptance, respecting push/deployment approval gates.

## Owner actions and platform constraints

No credentials, SQL or purchases are required for this planning task. At implementation:
provide an authorized Slack export/test workspace and a Microsoft test tenant/admin who
can approve the necessary Graph permissions; review source data handling and choose pilot
channels. Explain every action one requirement per response when ready. Never request
secrets or real private exports in chat; use the approved local/server upload workflow.

Slack export coverage depends on plan, role and export approval; standard export access
does not guarantee private-channel or DM history. Teams export requires the applicable
Graph permissions and tenant authorization, and retention limits affect availability.
Recheck current requirements, licensing and any costs before enabling a connector.

Primary sources checked for planning:
- [Slack export options](https://slack.com/help/articles/201658943-Export-your-workspace-data)
- [Slack import/export guide](https://slack.com/help/articles/204897248-Guide-to-Slack-import-and-export-tools)
- [Teams Export APIs](https://learn.microsoft.com/en-us/microsoftteams/export-teams-content)

M18 security/production launch acceptance includes all import/account-linking surfaces.
Remaining M14 owner/release actions follow all planned feature implementation, per the
October 5 authoritative order in milestones.md. Apple enrollment is deferred until then.
