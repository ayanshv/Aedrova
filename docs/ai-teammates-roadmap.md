# M17F — AI Teammates: major product pillar

Planned October 5, 2026 from the owner's attached brief and direct customization request.
This is a roadmap addition, not authorization to implement the attachment's commands now.
October 6 priority update: deliver next, after completed M15/M16 and before M17 continuous
team delivery and M17A–M17E migration. This supersedes the earlier dependency on M17.
Reuse existing local agent/build task infrastructure; adapt to M17 shared work items later.
The first slice includes native mentions/results and a real useful specialist task with an
available configured provider, alongside persistent identity and character customization.
No cosmetic-only completion or simulated task success counts as acceptance.
M17A–M17E migration work remains planned; M18 acceptance and the final deployed-codebase
walkthrough include this feature. Obtain permission between implementation stages.

Positioning: **Aedrova builds your product. Your AI teammates help you run and grow it.**
Present AI Teammates alongside the main builder as a major differentiator, not an add-on
chatbot list. Keep the main builder and its existing configurable nickname, execution,
review and publishing controls intact. Specialists may perform explicitly authorized
engineering tasks through that infrastructure; builder remains the default for product builds.
No gamification and no separate execution/billing/realtime architecture.

## October 6 — first useful slice delivered

M17F.1's delivered boundary is recorded in `milestone-17f1-ai-teammates.md`: profiles,
characters, existing task routing and real Codex analysis, with hosted profile acceptance.
Per-teammate resource/tool grants and connector registry move to M17F.3. Custom roles/colors,
shared activity and priority/effort refinements remain later work. Current work window is
runtime-only and importance is communication-only; no new billing cap is claimed.

## M17F.1 — architecture, persistent identities and character system

Audit existing workspace/schema, routing, tasks, local builds, context, meetings, tools,
entitlements and realtime before edits. Add workspace-owned persistent teammate identities,
versioned configuration, scoped grants, context/tool associations and activity linked to
existing tasks. Reuse existing task records rather than duplicate them. Define indexes,
RLS/server authorization, concurrency control, retention and soft deletion.

Design a simple premium 2D character family: small, friendly, recognizable, slightly playful.
Provide configurable **shape, blue/purple-compatible color, name, role, personality style,
responsibilities, report frequency, effort level and importance level**, plus authorized
knowledge sources/tools. Allow custom colors with accessible text/contrast. Character
appearance persists across sidebar, mentions, messages, profiles and activity. Use approved
existing assets where available; no additional visual reference image was supplied with
this request, so the exact character silhouette remains a design acceptance item.

Translate controls into understandable behavior:
- Personality changes tone/instructions, never access or safety permissions.
- Report frequency controls progress updates during active tasks; offer quiet, milestones
  and frequent modes. It never starts recurring model work. Separate explicit schedules
  from notification frequency and disclose their usage.
- Effort uses bounded execution/reasoning budgets with estimated allowance impact;
  reveal useful presets, not raw model parameters, and enforce caps server-side.
- Importance controls permitted queue priority/escalation visibility, not context access,
  unlimited spend or bypass of other tasks' fairness and workspace concurrency limits.

Acceptance: roles and grants isolate workspaces; name/character edits do not change identity;
configuration is shared consistently across accounts; visual customization incurs zero model
calls; keyboard/screen-reader/reduced-motion and compact-layout checks pass.

## M17F.2 — quick creation, native chat and shared team management

Create a short polished flow with useful Engineering, Design, Marketing, Research, Finance,
Product and Customer Success templates and fully custom roles. Target under one minute
for a default teammate. Keep permission/context summaries visible before creation; advanced
options can be edited later. Show an AI team section compatible with existing navigation,
clearly distinguish people, the main builder and specialist teammates, and add profiles
with status/current task, responsibilities, sources, grants, tools and concise activity.

Support mention autocomplete by configured name, questions, assignments, attached context,
follow-ups and real results posted as the named teammate. Actions: assign/chat/edit/pause/
resume/delete. Disambiguate duplicate names and retain stable actor IDs across renames.
Use existing timestamps, rich text and message controls. Optional workspace onboarding
allows one, several or no starter specialists; the main builder already exists.

Acceptance: two users interact with the same identity/state without refresh; rename,
concurrent edits, cancellation, duplicate assignments, pause/resume and deletion behave
predictably; old @mentions never rerun; working updates stay concise and final results
remain in chat. No unsolicited invitations, messages or tasks from profile creation.

## M17F.3 — authorized execution and meeting-aware context

Run through existing routing/provider, tools, local project boundaries, streaming, retries,
usage/rate limits, billing and approval controls. Execute only explicit mentions/assignments
or separately approved events/schedules. Never broadcast every new message to models or
continuously reread the workspace. Visual status and character motion are client-side.

Retrieve only relevant authorized chats, threads, approved product memory, files, projects,
tasks, repository sources and reviewed consented meeting content, with source citations.
Add meeting AI access None / Selected teammates / All teammates. Define All explicitly as
current approved teammates by default; newly added identities require a visible access
review rather than silently acquiring historical meetings. Enforce the intersection of
requester access, teammate grants, resource membership and meeting recording/AI-reuse
consent; privileged source accounts cannot expand a user's task visibility. Revocation
invalidates cached context and blocks affected running tool steps/results as appropriate.

Expose only granted tools; connecting integrations or widening sensitive access requires
existing approval. Never push code, publish content, deploy, send external messages or
make financial transactions merely because effort/importance is high. Use existing action
approval controls. Finance/research output is attributable and reviewable, not autonomous
financial decision-making. Unimplemented tools remain unavailable and truthfully labelled.

Acceptance: real authorized specialist task and builder handoff; meeting citations and
permission withdrawal; files/private channels/DMs/repositories/workspaces isolated; prompt
injection cannot escalate tool access. Usage accounting is server-authoritative, idempotent
and bounded across concurrent teammates. Provider/tool failures and missing context have
clear recovery; passive chatting/UI causes no model usage.

### External app connectors — required specialist execution capability

Owner requirement added October 6: the cute/chibi AI Teammates need real external app
connectors for Marketing, Generation/Design, Finance, Engineering/Builder and custom
specialist roles. This is planned implementation, not permission to connect accounts now.

Build the connector foundation with M17F.3 (deferred from the first useful slice): a shared capability registry, stable connection
IDs, per-workspace installation and per-teammate resource/action grants. Reuse existing
provider/tool/project integrations rather than implementing a second agent system.
Separate account connection from granting a teammate access; never inherit every tool
merely from a role template. Make supported actions and connection health discoverable.

Integrate in M17F.2–M17F.3: a native Connect apps flow with OAuth where supported, consent
summaries, reconnect/disconnect and least-privilege scopes. Marketing connectors cover
approved content drafting, analytics and explicitly approved publishing; Generation/Design
connectors cover image/video/audio/design creation and authorized asset retrieval;
Finance connectors cover authorized reports/accounting data and reviewable analysis;
Builder connectors cover local IDE/project/repository work and approved GitHub actions.
Select actual launch services after examining official API capabilities and the team's
needs; these categories do not promise every external service or action is supported.

Keep provider/API tokens in protected server storage or the existing appropriate secure
local credential mechanism, never in prompts, chat messages, logs or packaged assets.
Enforce requester permissions intersected with teammate/tool/resource grants server-side
at execution time. Imported connector content remains untrusted evidence. Record connector
provenance and action audit trails; redact secrets and honor deletion/retention. Disconnect
or revoke access must stop affected queued/running actions and invalidate cached evidence.

Approval applies to sending external messages, publishing campaigns/assets, code pushes,
deployments and financial actions. Scheduled actions need explicit separate authorization.
No automatic spending or money movement from a finance role or personality setting. Show
provider cost/usage implications before paid generation; enforce budgets and rate limits,
timeouts, idempotency and bounded retries to prevent duplicate posts or charges.

M17F.4 acceptance must include real controlled connector tasks for the supported specialist
categories, two-account/workspace isolation, revoked/expired credentials, cancellation,
provider failures, prompt-injection attempts and duplicate-request recovery. Advertise only
validated services/actions when implemented, alongside the builder and AI Teammates.
Owner actions are deferred: approved test accounts/scopes and provider configuration with
exact setup instructions during this milestone; no credentials or app connections now.

## M17F.4 — working presence, production acceptance and advertising

Use human-readable Available, Working, Waiting, Needs input, Completed, Error and Paused
states. Add minimal optional character motion and working/completion feedback that never
covers chat/composer or interrupts focus; respect reduced motion and animation preferences.
Realtime updates reach only authorized viewers. Lazy-load histories; avoid constant polling.

Test CRUD, identities, task lifecycle, every resource/tool grant, permission changes during
execution, shared updates, duplicates/concurrency, cancellation, retention/deletion, usage/
quotas and all failure/retry states. Include Mac/Windows compatibility, light/dark/System,
accessibility, keyboard navigation, scaling, responsive website surfaces, and regressions
for main builder/chat/meeting/billing. Audit every added dialog/menu/loading/empty/error
state. Require real controlled provider acceptance, not just simulated executions.

After acceptance, advertise as a headline pillar alongside the builder: specialists with
persistent identities, controlled shared context and real work inside the team's workspace.
Use real product screenshots/captures and role-specific examples; update feature pages,
onboarding and plan/usage disclosures. Advertise each validated part when implemented,
clearly label gated availability, and respect push/deployment authorization. Never claim
all tools/roles or autonomous outcomes before their demonstrated implementation.

Owner actions: none now. During delivery, review the character family and presets; approve
any necessary Supabase migration and scoped test integrations/provider configuration with
exact instructions. No secrets in chat. Existing M14 owner requirements remain required for release but are deferred until all
planned feature implementation is built, per the October 5 order in milestones.md.
