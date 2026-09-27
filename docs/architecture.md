# Architecture decisions — milestone 1

Status: provisional architecture validated through local probes, not production certification.

## Product constraints

Mac desktop first; direct website download as a DMG. Python owns first-party desktop,
API, workers and integration logic. SQL migrations, platform configuration, website markup
and third-party native binaries are necessary supporting assets. Main repository:
`/Users/ayanshvarma/Documents/Aedrova`. Chat is primary; AI is silent until invoked.

## Desktop and packaging

Use PySide6 Qt Widgets with model/view message rendering rather than a widget per message.
Milestone 1 measures a uniform-row synthetic 50k history; it does not establish rich-message,
attachment or variable-height performance. Milestone 2 must validate those separately.
Keep I/O and long-running work off Qt's UI thread. Use an explicit worker-to-UI event bridge.
Accessibility, keyboard control, platform menus, responsive layouts and light/dark tokens
are milestone 2 responsibilities.

Use PyInstaller for the initial packaging feasibility spike; a completed .app launch is
stronger evidence than a packaging plan. It is simpler to iterate than compilation for this
probe. Re-evaluate pyside6-deploy/Nuitka if release size or startup measurements warrant it.
Public release needs Developer ID signing, hardened runtime, notarization, a DMG and an
update mechanism. Validate minimum supported macOS and Apple Silicon/Intel separately.
Current local results only apply to this Apple Silicon host.

Sources:
- https://doc.qt.io/qtforpython-6/deployment/deployment-pyside6-deploy.html
- https://pyinstaller.org/en/stable/usage.html
- https://developer.apple.com/help/account/certificates/create-developer-id-certificates

## Backend and Supabase

Start with a modular Python FastAPI service and separate execution/indexing workers.
Supabase provides Auth, Postgres, Storage and authorized realtime events. The API owns
privileged actions. Desktop clients get user-scoped tokens only. Database RLS, storage
policies and realtime policies all need independent negative tests in milestone 3.
No Supabase deployment or schema exists in milestone 1.

Every persisted object carries workspace ownership. Projects bind repositories and
context; channels are conversations, tabs are views, meetings belong to channels.
Roles: owner/admin/member/guest. Reading, invoking and external-action approval are separate
capabilities. Initial approval policy is owner/admin only; per-project approvers can follow.
Server-authoritative membership/ACL lookup is mandatory: the pure domain functions cannot
make untrusted client claims safe. Do not treat an admin role as automatic private-channel access.

Source: https://supabase.com/docs/guides/realtime/authorization

## Context

Store original sources and revision history. Confirmed decisions are distinguishable from
suggestions and generated summaries. Retrieve by project plus lexical/semantic relevance.
Apply ACLs before model submission and again before delivery. Milestone 1 selection is an
eligibility filter, not a relevance/search engine.

A source must be permitted for AI, current, not deleted, in the same workspace/project,
and visible to all readers of the destination. This conservative audience intersection
avoids private facts appearing in a wider thread. Sources carry immutable identity and revision.
ContextPackage stores the request, acceptance criteria, sources and retrieval time.
Authorization remains a service responsibility even after a package is constructed.
Re-check policies before reuse; revoke cached retrieval on membership/source changes.
New readers joining a channel also require historical output visibility rules, not merely
future retrieval filtering. Derived outputs need provenance and ACL/retention handling.

Retrieved text is untrusted data, never authority to change tool permissions. No blanket
claim of end-to-end encryption: authorized servers and selected model providers need to
process permitted content. Define provider disclosure, retention and deletion before beta.

## Agent provider

First candidate: Claude Agent SDK's Python interface. The local probe starts its actual
bundled runtime and performs initialization without a prompt. It does not prove model
access, coding quality, commercial account readiness or sandbox enforcement.
Use explicit settings sources and tool configuration, not a user's ambient personal setup.
Production adapter must run in an isolated worker with workspace-scoped credentials,
restricted network, checkout boundaries, cancellation and budget enforcement.

Provider interface: a typed request with build ID, context, checkout, cost/time budgets;
an ordered stream of typed events; cancellation by build ID. Events carry no integration
secrets. Provider-specific details stay behind adapters. No simulated build is presented
as successful real execution.

Codex remains a later adapter candidate. Validate its supported integration and auth route
at implementation time; the currently reviewed app-server documentation contains experimental
transport/production caveats. Do not depend on an unsupported remote endpoint for launch.

Sources:
- https://code.claude.com/docs/en/agent-sdk/overview
- https://code.claude.com/docs/en/agent-sdk/python
- https://learn.chatgpt.com/docs/app-server

## Build state and external actions

Requested -> planning -> awaiting plan -> queued -> running -> awaiting review -> succeeded.
Planning/execution can fail; nonterminal work can be cancelled. Review can return to running.
A completed build means its implementation result is accepted, not implicitly merged/deployed.
Retries create explicit attempts; do not mutate terminal history.
The transition helper checks the graph only. Services must enforce plan authorization and
persist transitions atomically with optimistic concurrency. Restart recovery is milestone 8.

Push, merge and deploy require separate immutable action scopes: workspace, build, repository,
target, revision and artifact digest. A change in any field invalidates the old approval.
Approver membership is checked at execution, and expired/revoked grants fail closed.
Production needs one-time consumption/idempotency and transactional execution records;
the milestone 1 grant predicate is deliberately not an external-action executor.

A coding worker holds no push/merge/deploy credential. A separate broker verifies the
approval, injects narrowly scoped credentials and performs the action. Shell execution
cannot be secured by asking the model to obey a rule. A checkout or worktree is not isolation.

## Meetings

Candidate: LiveKit RTC Python SDK plus Qt media capture/rendering. Milestone 1 tests native
library loading and synthetic audio/video buffer interoperability. Do not mistake server
room administration APIs for a desktop media client. Select the final client integration
only after a two-participant end-to-end spike confirms device capture, rendering, audio
playback, echo handling, TURN, reconnection and macOS screen-share permissions.

Prefer managed media infrastructure initially; do not build a conferencing server from scratch.
Python remains the orchestration language while native libraries handle codecs/media.
Audio transcription is the first meeting context source. Screen-share interpretation is a
separate feature. Consent state must be explicit, visible and revocable, with late joiners
handled before capture continues. Recording, transcription and AI reuse are distinct grants.
No device access or recordings occur in the milestone 1 probe.

Source: https://docs.livekit.io/reference/python/livekit/rtc/index.html

## Stripe and costs

Stripe Checkout/Billing Portal plus verified server webhooks drive workspace subscriptions.
Internal append-only usage ledger: reserve budget, execute, settle actual usage, release
unused reservation. Make webhook processing and settlement idempotent. Enforce concurrent
reservations atomically. Plan prices remain assumptions until measured costs are available.
Stripe secret keys and privileged Supabase keys never ship in the app. No billing service
or paid model call is configured in milestone 1.

Source: https://docs.stripe.com/billing/subscriptions/webhooks
