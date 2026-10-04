# Agent replies in the conversation — October 3, 2026

Agent public updates now render inside the existing conversation timeline instead of
occupying a separate, 230px-high panel over the composer. Message rows use the team’s
configured agent nickname (Aedrova fallback), the brand avatar, system typography matching
teammate messages, sender hierarchy, paragraph spacing and local sent time/date. Full
sent timestamp is available as a tooltip. Tool disclosures remain expandable and align
with the message body; build status, Stop and history controls remain available.

The transcript scrolls with teammate messages. Its anchored timeline row survives incoming
chat/model refreshes without deleting the live Qt widget, and long transcripts can reach
their final update even when a row exceeds the viewport height. Existing private/local
build visibility and clearing on logout/new build are preserved. This is presentation,
not new Supabase chat persistence or broadcasting agent output to other participants.
Activity is displayed only in its originating channel, avoiding accidental appearance
in another channel of the same workspace. No user message data is modified.

Verification: 477 desktop tests and Ruff/whitespace checks pass. New checks cover nickname,
time/date, readable multiline text, realtime widget lifetime/order, channel isolation and
long-response scrolling. Light/dark wide and compact captures inspected in
work/agent-chat-polish. Rebuilt internal preview with the existing Apple Development
identity, local AI mode and meeting origin http://127.0.0.1:8090; packaged launch, signature
and resource-secret checks pass. No SQL, hosting, Stripe or public deployment changed.

Owner action: quit and reopen dist/Aedrova.app when ready to load the rebuilt UI.
The currently open setup form was left intact. Continue M14 local release rehearsal only
with the owner's permission after this requested UI task.

## Working messages and build onboarding follow-up

Working status, elapsed time and Stop now live inside a named agent message in the
conversation, rather than beside the composer. Streamed public updates/tools remain
visible during the run. At completion, transient status/tools/updates are removed from
chat and replaced by the final provider result. Errors and cancelled context-only runs
also retain a clear final response. Build details/history retain their existing review
and diagnostic paths. Automatic planning can transition into execution without showing
a completed plan as a final chat result. No private reasoning is exposed.

Getting started → Bring your tools now includes an inline project folder picker, coding
provider, preferred editor and explicit “Let the agent plan and execute automatically”
checkbox. Continue validates and saves the existing per-account/per-workspace project
binding, preserves other connection settings and does not start a build. Back preserves
unsaved choices; skipping without a folder leaves build permission unchanged. Invalid
folders and changed account/workspace are refused. Automatic work remains opt-in;
original-file application and publishing keep their approval gates. Compact setup screens
scroll their content while keeping navigation accessible.

All project/build folder selectors now use Qt's native folder dialog on macOS, with its
Finder-style navigation and OS theme. No custom Finder recreation or OS permissions
changes were added.

Verification: 482 desktop tests, Ruff, signature/resource scanning and packaged launch
pass. Light/dark working/results/onboarding captures were inspected. Internal preview
rebuilt with the same Apple Development identity and local meeting origin. No SQL,
credentials or paid hosting actions are needed. Quit/reopen the existing dist/Aedrova.app
to load the changes; existing users can revisit Help → Getting started → Bring your tools.
M14 remains unfinished; ask permission before resuming its remaining release rehearsal.


## Workspace mentions and scroll boundary

Both main and thread composers now show/insert the workspace agent nickname on `@`,
click, Tab or Return. Names with spaces and Unicode complete without sending; changing
workspace preferences refreshes both controls. The existing `@Aedrova` command remains
an accepted alias; product branding is unchanged.

Inline transcript sizing now measures live row layouts and fixes the feed/content height
to that height. The conversation recalculates its list range on replacement, preventing
a completed short result from retaining a long transcript's blank scroll space. Native
wheel/trackpad and scrollbar boundaries clamp at the final message; long results remain
fully reachable after width changes.

Validation: 490 desktop tests, Ruff, diff whitespace, visual inspection, preview signing,
release secret scanner and packaged smoke passed. No SQL, provider call or public
deployment required. Owner: quit Aedrova and reopen `dist/Aedrova.app` to load this build.
Ask permission before resuming the remaining local M14 release rehearsal.
