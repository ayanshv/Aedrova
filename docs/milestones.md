# Delivery gates

Current status: milestones 1 and 2 complete, including the requested Apple-inspired design revision. Milestone 3 is approved and in progress; hosted Supabase validation remains required.

The owner requested sequential milestones. At the end of each: run necessary checks,
report evidence and limitations, then ask permission before beginning the next.
Never interpret a passed unit test as a passed live integration.

1. **Feasibility and contracts** — Python desktop/history probe, package launch, SDK handshake,
   synthetic media interoperability, permissions/context/build/approval contracts and documented limits.
2. **Desktop shell and visual system** — workspace/channel/tab navigation, chat and thread layout,
   keyboard behavior, accessibility and light/dark themes with realistic fixtures.
3. **Identity and tenant isolation** — Supabase login, invitations, roles, private channels,
   data/storage/realtime policies; negative cross-tenant tests.
4. **Reliable communication** — messages, threads, DMs, attachments, unread state, reconnect and retries.
5. **First real build** — one repo/provider, scoped context, plan approval, isolated implementation,
   tests, cancellation and streamed results. Internal alpha.
6. **Project context** — indexed retrieval, confirmed decisions, source citations, stale/deleted and
   revoked context handling; relevance/security evaluations.
7. **Review and delivery** — diffs, exact approvals, GitHub push/PR, IDE handoff and one preview provider.
8. **Execution durability** — queue/recovery, resource limits, concurrency, idempotency and usage ledger.
9. **Stripe paid beta** — subscriptions, entitlements, credits, verified/replayed webhooks and billing
   lifecycle checks. Requires a distributable beta installer from an early slice of milestone 11.
10. **Meetings** — room calls, devices, sharing, consent/transcription and meeting-to-build retrieval.
11. **Public Mac release** — website/DMG/signing/notarization, updates, fresh-Mac installation,
    backups/recovery, crash reporting and operations.
12. **Expansion** — second provider, more integrations/environments/platforms and multi-repo agents.

Live model execution, connected Supabase/GitHub/Stripe, conferencing and release signing require
appropriate service accounts at their milestones. Local protocol probes do not replace those gates.
