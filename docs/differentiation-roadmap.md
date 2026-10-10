# From connected tools to a team delivery system

Added October 3, 2026. This is planned work, not implemented functionality or permission
to start it. Complete and test each milestone, report owner actions and limitations,
then ask permission before starting the next. Reuse existing context retrieval,
confirmed decisions, isolated builds and review controls rather than duplicate them.

Product promise: **Your team's decisions, turned into working software—with the context intact.**
The differentiator must be visible and verifiable in the product, not just marketing copy.

Owner direction: advertise each differentiation feature on the website as part of that
feature's implementation milestone, not in advance and not only at M17. After validating
the implementation, update relevant feature copy, actual product screenshots, onboarding
and availability disclosures; verify responsive layouts and links. Distinguish preview or
gated functionality from public availability. Website updates are a completion criterion
for each applicable milestone. No website changes are requested by this reminder; follow
the existing push/deployment authorization gates when delivering those future updates.

## Current delivery order — owner revision October 5

Build M15 → M16 → M17 → migration M17A–M17E → AI Teammates M17F first.
Then complete remaining M14 (owner production setup, hosted meeting acceptance,
Windows support/distribution and updated release rehearsals), followed by M18 acceptance
and authorized launch. The codebase walkthrough follows the completed deployment.
Earlier instructions to finish M14 before feature implementation are superseded.
External acceptance that cannot yet run must be recorded, not claimed complete; finish
it before launch. Ask permission to start M15, then again between subsequent milestones.

## M14 — deferred production prerequisites and meeting completion

The completed M14A local rehearsal remains recorded. Repeat release checks with the final
feature set after implementation. M14B remains
the deferred guided owner setup for Apple Developer ID, Render and live Stripe. Prepare
independent implementation while owner account/payment actions are unavailable; do not
activate paid checkout, public installers or unvalidated capabilities.

### M14C — full meeting acceptance

**Meetings are completely finished at M14C, only when all these checks pass:**

- Deploy the authenticated HTTPS meeting API and independent supervision/maintenance
  jobs, apply the required hosted migrations and validate health, recovery and access
  revocation. Keep service secrets server-side.
- Verify Start/Join, shared public announcement destination, private-channel isolation,
  participant photos/counts, host end, leaving and expired presence with two real accounts.
- Validate camera, microphone, speakers and screen sharing on two physical Macs with
  the released signing identity; check permission denial/recovery, echo, reconnect,
  network loss and device changes. Synthetic media and two accounts on one Mac do not
  satisfy this gate. A second physical Mac/tester is currently unavailable.
- Validate real speech ingestion, transcript corrections/review, confirmed decisions
  and cited agent context in a hosted call. Verify recording consent, separate AI reuse
  consent, withdrawal/deletion and unauthorized access. Screen sharing does not imply
  visual interpretation of shared content.
- Exercise quota exhaustion, provider failure, interrupted uploads, cleanup and retention;
  confirm readable recovery states and no capture or AI reuse without consent.
- Run relevant automated regressions and retain a live acceptance report. Resolve failures
  before enabling public meeting/transcription/context capabilities.

M10 delivered the native call implementation; M12 delivered local meeting context and
speech/review implementation. Neither replaces final hosted/hardware acceptance. No
calendar date is promised while hosting, provider setup and a second Mac remain unavailable.

Owner actions are deferred to M14B/C: approve hosting costs in Render, configure private
server/provider credentials there, run supplied migrations in Supabase, complete Apple
signing setup and arrange a second Mac/tester. Provide exact dashboard/file instructions
when each step is ready; never request secrets in chat. For the existing announcement
feature, run `supabase/migrations/202610030004_meeting_activity.sql` in the Supabase SQL
Editor and reopen Aedrova if this migration has not already been applied.

## M15 — persistent product memory

Make what the team has agreed visible in a native Product memory view: goals, approved
requirements, constraints, decisions, unresolved questions and source references.
Treat extracted candidates as proposals until an authorized teammate confirms them.
Support editing, retiring and superseding decisions with revision history. Surface
conflicting statements for review rather than silently selecting one as truth.

Build a permission-scoped, incrementally refreshed index of available chats, files and
reviewed consented transcripts. Record freshness and missing sources. Link designs as
sources when available; do not claim an unimplemented design integration or visual
understanding. Pin the memory revision used by a build and flag changes during execution.

Acceptance: approved versus brainstorm content remains distinct; a changed decision
supersedes the old one; citations open the correct accessible source; stale/deleted/revoked
sources are excluded; private channels and workspaces remain isolated; retrieval succeeds
over a representative multi-channel dataset. The team can inspect and correct what the
agent believes before it builds.

## M16 — traceable builds and shared review

Turn an agent request into a shared build record with approved requirements, acceptance
criteria, cited sources and the memory revision. Preserve seamless automatic planning
when enabled; request clarification only for material unresolved conflicts or missing
requirements. Show which requirements a change and its tests address.

Attach real diffs, executed check results and their logs, remaining gaps and a reviewable
PR when GitHub is connected. Preserve explicit publish/push approval. Distinguish untested
claims from verified results; never invent successful tests or delivery links. Reflect
build/review status and final results in the originating conversation.

Acceptance: a real local project change leads to an owner-approved test PR; every claimed
completed requirement has source/change/check evidence; failing checks remain visible;
concurrent runs, retries and cancellation do not duplicate writes or PRs; inaccessible
sources and secrets do not leak into records. Existing manual provider setup remains
truthfully disclosed until managed access is accepted.

## M17 — continuous team delivery

Connect discuss → confirm → build → review → deliver in one persistent team workflow.
Add shared work items with ownership, blockers and review status; teammates can resume
the same work with its context intact. Reconcile delivered changes and approved review
decisions back into product memory; propose updates for human confirmation rather than
silently rewriting intent. Show new decisions that affect an unfinished build.

Demonstrate the workflow in onboarding and on the website with actual captures. Replace
generic integration claims with the concrete memory, citations and delivery controls
users can operate. Do not advertise planned or gated features as publicly available.

Acceptance: two teammates hand off a real work item from confirmed decision to reviewed
delivery without restating its context; a later requirement change is visible and linked;
partial/offline/provider failure recovery preserves history; workspace permissions apply
to every record and notification. Measure time to accepted PR, repeated clarification
and correction cycles on matched tasks; report observed results rather than promise
superiority over Slack plus integrations without evidence.

## M17A–M17E — migration from Slack and Microsoft Teams

Complete the [migration roadmap](migration-roadmap.md): preview and durable import jobs,
Slack exports, Teams Graph import/Microsoft identity linking, pilot/catch-up/rollback and
permission-scoped context continuity. Validate authorized real imports before advertising
availability. These additions precede M18 and are included in final launch/security checks.

## M17F — AI Teammates

Deliver the [AI Teammates roadmap](ai-teammates-roadmap.md) as a headline pillar beside
the central builder: persistent configurable specialists with native chat, scoped tools
and meeting-aware context using existing execution/usage infrastructure. Include its
acceptance and marketing deliverables before M18; no passive model spending or gamification.

## M18 — expanded release acceptance and launch

Repeat security/privacy checks for the new memory/index/delivery surfaces: prompt injection,
source permissions, secret filtering, local file boundaries, rate/usage limits, audit
records, deletion/retention and billing failures. Validate end-to-end onboarding, managed
AI, meeting acceptance, subscription lifecycle, signed installer and update/rollback on
the actual production configuration. Polish light/dark, accessibility and compact layouts
for the added views and update public documentation.

The existing public waitlist website can remain live throughout. Public product launch
requires M14 prerequisites and M15–M18 acceptance; it is not triggered by this roadmap edit.
Record evidence and unresolved limitations, then obtain explicit release authorization.

## After the entire app is complete and deployed

Deliver the requested entire-codebase walkthrough (historical label M13B) using the final
implementation, including these additions and real deployment/update procedures. Its
historical number does not place it before M14–M18. Ask permission before starting it.
