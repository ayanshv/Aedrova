# Delivery gates

Current status (latest): M7 and its guided GitHub CLI setup follow-up are implemented and locally verified; live GitHub publication still needs owner browser authorization and acceptance in a test repository. M8 is not started. See `milestone-7-delivery.md`.

Earlier milestones: milestones 1 and 2 complete. Milestone 3 Google login and the first chat migration are confirmed by the owner; the owner has confirmed that messages do not leak between separate workspaces. Milestone 4 code is implemented and locally tested, including DMs, attachments, unread state, keyset history, private realtime invalidations and reconnect/retries. The owner confirms applying the final communication migration and clarifies that the two-account observation was a successful isolation check, not a delivery failure. Same-workspace delivery and remaining hosted acceptance scenarios are not established by that check. The owner moved the full safety audit to the end of feature development; it is now milestone 13.

The owner requested sequential milestones. At the end of each: run necessary checks,
report evidence and limitations, then ask permission before beginning the next.
Never interpret a passed unit test as a passed live integration.

1. **Feasibility and contracts** — Python desktop/history probe, package launch, SDK handshake,
   synthetic media interoperability, permissions/context/build/approval contracts and documented limits.
2. **Desktop shell and visual system** — workspace/channel/tab navigation, chat and thread layout,
   keyboard behavior, accessibility and light/dark themes with realistic fixtures.
3. **Identity and tenant isolation** — Google-only Supabase login, team agent nickname onboarding,
   invitations, roles, private channels,
   data/storage/realtime policies; negative cross-tenant tests.
4. **Reliable communication** — messages, threads, DMs, attachments, unread state, reconnect and retries.

5. **First real build** — implemented for internal alpha with actual Codex execution verified,
   a Claude Agent SDK adapter, permitted workspace context, plan approval, independent local Git
   copies, tests, cancellation and streamed results. Claude paid execution and signed-in hosted
   context-to-build acceptance still require owner setup/checks; see `milestone-5-local-builds.md`.
6. **Project context** — implemented and locally verified: ephemeral FTS5 retrieval, thread
   expansion, explicit member-confirmed/retired decisions, source browser, validated citation IDs,
   scoped channel pagination and revision checks for edits/deletions during collection.
   Owner applied `202609290001_context_decisions.sql`; hosted search, decision confirmation/retirement and cited Codex planning passed. See `milestone-6-hosted-check.md`.
7. **Account usability, chat-to-IDE builds, review and delivery** — start with an account/UI
   usability slice: make the bottom-left account control open a real menu with clear logout,
   current account/profile and meaningful available workspace/account actions. Build matching
   settings with working preferences; hide unavailable functions instead of inert placeholders.
   Audit dropdowns, menus, dialogs, focus/keyboard states and light/dark themes for consistency
   with Aedrova's Apple-inspired design. Test logout cleanup and all exposed account actions.
   Then finish the native end-to-end flow: a team
   agrees in chat, invokes its named agent, and the agent retrieves permitted workspace evidence
   without requiring the user to re-enter the discussion. Bind the workspace to a local project
   and connected GitHub repository, reuse that binding for subsequent requests, show progress and
   actionable questions in the chat flow, and open the resulting code in VS Code or the chosen IDE.
   Provide diffs, safe application of approved changes to the selected project, exact approvals,
   GitHub push/PR and one preview provider. Preserve uncommitted user work; pushes require approval.
8. **Execution durability** — queue/recovery, resource limits, concurrency, idempotency and usage ledger.
9. **Stripe paid beta and included AI** — one Aedrova subscription includes an explicitly defined
   workspace AI allowance and a choice of supported Codex/OpenAI or Claude models. Customers
   do not supply provider keys or purchase separate provider subscriptions. Aedrova pays provider
   API usage through its own commercial accounts. Implement a server-side provider gateway,
   Stripe subscriptions, signed/idempotent webhooks, entitlements, atomic usage reservation and
   reconciliation, concurrent-run limits, visible balances and opt-in top-ups. Never embed shared
   provider credentials in the desktop app; local coding runtimes authenticate to the gateway with
   scoped, short-lived Aedrova credentials. Verify each runtime's gateway compatibility before launch.
   Keep local-file execution and user tool approvals. Pricing and included amounts require measured
   costs and owner approval; no unlimited-usage promises or automatic overage charges by default.
   Requires a distributable beta installer from an early slice of milestone 11.
10. **Meetings** — room calls, devices, sharing, consent/transcription and meeting-to-build retrieval.
11. **Mac release preparation** — website/DMG/signing/notarization, updates, fresh-Mac installation,
    backups/recovery, crash reporting and operations.
12. **Expansion** — second provider, more integrations/environments/platforms and multi-repo agents.
13. **Application safety and release audit** — run the full safety review after feature development and before public launch. Audit source, history, dependencies and release artifacts for secrets; review tenant/session permissions and hidden administrative access; harden server-enforced rate limits, quotas, signup/invitation abuse controls, file cleanup, audit logs/redaction and incident recovery. Review agent prompt injection, checkout isolation, tool approvals and network access. This is the rescheduled full audit, formerly 4A.

Essential access checks, isolation, safe credential handling, and explicit code execution/push approvals remain part of implementing each feature. The rescheduled full audit does not remove existing protections. Milestone 5 was explicitly approved and implemented. Milestone 6 was approved and implemented; the owner applied its migration and the single-account hosted context-to-plan acceptance passed. Live two-account revocation remains unverified; local isolation suites pass. Milestone 7 was approved. Its account, project binding, local review/application, IDE, static preview and GitHub delivery code is implemented; see `milestone-7-delivery.md`. Live GitHub acceptance still requires owner authentication. Milestone 8 remains the next approval gate.

Live model execution, connected Supabase/GitHub/Stripe, conferencing and release signing require
appropriate service accounts at their milestones. Local protocol probes do not replace those gates.


## Included AI product decision — 2026-09-28

The owner requested one native Aedrova payment covering both the workspace and its coding AI.
This is the intended customer experience. Milestone 5's local Codex login / developer Anthropic
API key is an internal-alpha arrangement, not the intended paid-customer onboarding flow.
The roadmap requirement is recorded; the managed gateway and billing are not implemented yet.
No provider billing or Stripe accounts were created or charged by this documentation change.

Required later: owner enables billing for Aedrova's OpenAI Platform and Anthropic Console
accounts, completes Stripe business/payment onboarding, and approves plan prices/allowances.
Provider secrets are configured only in the backend deployment's secret store. These actions
block a live managed paid beta, not current local-alpha development. No action is needed now.

Provider references: https://developers.openai.com/codex/auth and
https://code.claude.com/docs/en/agent-sdk/overview . API-funded use is distinct from including
an individual ChatGPT/Claude consumer subscription; do not describe the plan as reselling those
subscriptions. Customer-facing provider packaging remains subject to applicable provider terms.


## Native build workflow confirmation — 2026-09-28

The owner confirmed the desired final journey: teammates converse and agree, then say
“@AgentNickname, build our newest feature, [feature]”. The named agent searches the entire
chatspace the requester is authorized to access, identifies the relevant requirements and
confirmed decisions, builds in the connected local project usable from their IDE, and can
push to the connected GitHub repository after approval. Do not make the customer manually
reconstruct context or supply provider keys. Do not interpret all chat as approved requirements.

Milestone 6 supplies context retrieval and citations; milestone 7 owns the integrated chat,
project/IDE and GitHub delivery journey; milestone 9 removes the alpha provider setup via
managed AI billing. This request records future scope only and does not authorize starting
milestone 6 or 7. The owner tried the alpha flow but Claude execution could not complete
without its API setup; do not record that attempt as successful live Claude validation.

No owner configuration is needed to start milestone 6 development. If it introduces a Supabase
migration or hosted service, provide the exact owner steps at handoff before claiming hosted
acceptance. Later milestone 7 requires the owner to select a local project/IDE and authorize
GitHub repository access; milestone 9 requires provider billing and backend secret setup.

Milestone 6 delivery: 190 Python tests and all embedded PostgreSQL suites pass. Real Codex
planning consumed synthetic indexed context and produced valid citations. Claude paid execution
and hosted workspace acceptance are not implied by those results. No milestone 7 work started.


The owner requested the account/settings/menu consistency slice at the Milestone 6 handoff.
It is recorded as the first part of Milestone 7; the request is not approval to start that
milestone. Account deletion, billing and other destructive or unavailable backend actions must
not be represented as working controls before their actual implementation and verification.


## Distribution and guided onboarding — owner direction, 2026-09-29

After finishing M7 and its checks, implement a guided GitHub CLI installation step: detect
existing installations, explain why the helper is needed, offer one explicit installation
button, show progress/retry, and guide the user through GitHub's own browser authorization.
The application should handle download and verification without terminal commands or an
administrator password wherever possible. Do not silently install executables. GitHub
connection should be offered during onboarding and remain available from Projects.

Integrate the separate marketing/download website into **M9's paid-beta release slice**
(dependent on the early signing/DMG work from M11). Keep its backend in Python and its visual
identity consistent with the desktop app. Explain the PRD's complete journey simply: private
channels/rooms, teammates, decisions and sources, a named Codex/Claude agent, local IDE builds,
review/testing/approved GitHub delivery, and consented meeting transcription as context.
Show unshipped capabilities as forthcoming until their milestone passes; do not advertise
video calling/transcription as available before M10. Keep integration expansion claims accurate.

Website journey: clear feature examples → short, friendly, skippable questions such as team
size and referral source → transparent payment plans → Google account/checkout as needed →
correct Mac download → short installation guidance. Preserve progress/back navigation; do
not make optional marketing answers a purchase gate. Plan pricing/allowances still need owner
approval and cost evidence; PRD illustrative prices are not approved billing configuration.
Owner later supplies domain/DNS access, Stripe business setup, provider billing, privacy/terms
copy, and Apple Developer signing/notarization credentials. These do not block M7/M8.

Add **M11a: premium desktop onboarding**, iterating its basic setup during M9 beta:
- Short form steps with Next/Back, restrained transitions and clear progress to configure
  account/workspace, agent nickname/provider entitlement, local project/IDE/GitHub and workflow.
- A first-dashboard interactive tour with dimmed backdrop, spotlight and anchored labels.
  Every actually available function must have a tour step: navigation/channels/threads/DMs,
  invitations/roles, search/decisions/sources, attachments/history, named-agent planning/builds,
  tool approvals/cancellation, review/application/IDE/preview/GitHub, settings/accessibility/
  logout, billing/usage, and (after M10) calls/devices/sharing/recording consent/transcripts.
- Complete coverage via short task-based chapters, not one forced marathon. Skip, pause,
  resume, previous/next and replay from Help; never perform a destructive or billable action
  just to advance a tour. Remember completion per account and tour version.
- Support keyboard focus, screen readers, reduced motion/transparency, both themes, resizing,
  missing integrations and different membership roles. Never spotlight unavailable controls.
- Add a feature-to-tour coverage check so future features cannot silently miss onboarding.

The PRD remains the feature reference, with the owner's Python/macOS-first direction taking
precedence over its original web-first platform ordering. The website and full animated tour
are scheduled work; this roadmap entry does not claim they are implemented.

Guided GitHub setup is now implemented and tested after the M7 checks. The M9 website and M11a animated tour remain planned, not started.


## M7 autonomous-agent follow-up — 2026-09-30

Implemented: saved automatic planning/execution permission, background mentions, inline public
activity/actions with reduced-motion-aware shimmer, Stop, and corrected Codex stream recovery
and terminal error reporting. No visible Create plan step remains. See `autonomous-agent.md`
for setup, tests, provider limitations and still-outstanding live GitHub authorization.
M8 remains unstarted; M9 retains included AI subscription billing.
