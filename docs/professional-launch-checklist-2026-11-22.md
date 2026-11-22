# Everything needed before a professional company launch

Written November 22, 2026 from the repository, the live site, Render, and the gates in
`pre-launch-timeline.md`. Status key: **Done**, **Partial** (built, not proven), **Open**
(not started), **Owner** (only you can do it). Items marked ★ block a public launch.

## 1. Company and legal

| Item | Status | Notes |
|---|---|---|
| ★ Incorporate (C-Corp formation is deferred) and pick the legal operator, address and jurisdiction | Owner | The site still says it is not a registered corporation. Terms, Privacy and invoices need the real entity. |
| ★ Terms, Privacy, Refunds, Acceptable use, Cookies, Subprocessors reviewed by counsel | Owner | Pages exist and are dated Oct 21. They disclaim "not end-to-end encrypted, no SOC 2", which is honest but needs a lawyer's pass. |
| ★ Data processing agreement and a published subprocessor list that matches reality | Partial | Add OpenAI web search, Render, Supabase, Cloudflare, Stripe, Buffer, LiveKit. |
| Trademark search and filing for "Aedrova" and the mark | Owner | Do before wider marketing. |
| Business insurance (cyber, E&O) and a business bank account | Owner | Needed for Stripe payouts and enterprise buyers. |
| Children's policy and age gate enforced in the app, not only the waitlist | Partial | Site says 13+. |
| AI disclosures: what the agent can read, search and change, and that web search sends queries to OpenAI | Open | New with web search and local file reading. |

## 2. Billing and pricing

| Item | Status | Notes |
|---|---|---|
| ★ Map the four site prices (Pro $15/$144, Teams $30/$288 per person) to Stripe live products | Partial | Backend plan table and allowances are merged; live Stripe prices and webhooks are not created. |
| ★ Decide per-person billing versus per-workspace allowance | Open | Allowances are shared per workspace today. Seats are not counted. |
| Stripe live mode, Tax, receipts, customer portal, dunning, refund flow | Owner | Verify retries, renewals, upgrades, cancellations and refunds in test mode first. |
| Early-access window ends Dec 20, 2026 | Owner | Decide whether to extend, and keep the site copy true. |
| Margin guard: worst case at least 24% | Done | `tests/test_allowance_windows.py`. Recheck if model rates move. |

## 3. The desktop app

| Item | Status | Notes |
|---|---|---|
| ★ Apple Developer ID signing, notarization, Sign in with Apple | Owner | In progress; Stage 4 is paused for it. |
| ★ Windows code signing certificate and signed installer | Owner | Choose the method (EV certificate or cloud signing). A purchase. |
| ★ Clean-machine install, update, uninstall on Mac and Windows | Open | Preview packaging passed in CI; not clean-machine verified. |
| Auto-update channel (signed, with rollback) | Partial | Update check exists; there is no silent installer by design. |
| Crash reporting and diagnostics with no message content | Open | Needed to support real users. |
| First-run onboarding, empty states, keyboard shortcuts, VoiceOver and Narrator pass | Partial | Pass 1 and 2 done; accessibility audit not run. |
| Performance: cold start, 50k-message history, large attachments | Partial | Synthetic 50k measured; rich-message performance not. |
| Localization beyond English and Hindi | Open | Offline translation exists; UI strings are mostly English. |

## 4. The agent and the product promise

| Item | Status | Notes |
|---|---|---|
| ★ Mention-to-build proven on signed Mac and Windows builds with a real project | Open | Everything is tested in source; not in a signed build. |
| ★ Real GitHub pull request from the delivery card | Open | Needs a connected test repository. |
| ★ Slack public-channel import accepted with a real export, second account, removal | Open | Code and migration exist; the hosted migration is not applied. |
| Workspace scan quality on a large real history (400-message depth, files, meetings) | Open | Unit-tested; not run against hosted staging. |
| Web search live end to end | Partial | Gateway change is on production and staging; no real search has been run. |
| Prompt-injection and exfiltration testing for web search plus local file read | Open | New attack surface: a web page can try to steer an agent that can read your home folder. Review the deny list and consider approval for reads outside the project. |
| Windows sandbox for the agent's file and shell limits | Open | The macOS path is exercised more than Windows. |
| Reliable two-device meetings and consented transcripts as agent context | Open | Meeting health returned 503 earlier; packaging flag `AEDROVA_MEETING_CONTEXT_ENABLED`. |
| Claude provider and model routing | Deferred | Post-launch by your decision. |
| Agent-to-Bud collaboration | Deferred | Post-launch; see `post-launch-plans.md`. |

## 5. Native browser panel for Buds and the agent (new feature)

A panel inside Aedrova where the agent or a Bud can open a page, read it, click and fill
non-sensitive fields, and show the user what it is doing, with the user able to take over.

**Why it matters:** web research, checking a deployed site, reading docs, filling a form for
you, and verifying UI work the agent just built, without switching to another browser.

**Approach:** embed Qt WebEngine (Chromium) in a dockable panel next to the conversation.
PySide6 includes it; it adds roughly 150 to 200 MB to installers, which affects download
size and notarization time. A second option is an external automation channel into the user's
browser, which avoids the size but loses the visible, controllable panel.

**Rules it must ship with**
- Isolated profile: no shared cookies or logins with the user's browser. The user signs in
  inside the panel only when they choose, and the agent never types passwords or card details.
- Every agent action is visible: a highlighted cursor, a step in the task list, and a Stop
  button that works immediately.
- Allow and deny lists, SSRF protection (no local network or private addresses, no file URLs),
  download blocking by default, and a permission prompt (Ask mode) for each new site.
- Page content is untrusted data. It can never grant permissions or change settings.
- Consent copy: what the panel can see, and that screenshots may be sent to the AI provider.
- Bud use is scoped to the Bud's permissions, never wider than the user's.

**Work breakdown (rough):** panel shell and navigation (2 to 3 days); agent tool protocol for
open, read, click, type, screenshot (4 to 5 days); safety layer, prompts and tests (3 to 4
days); Windows and Mac packaging checks (2 days); security review (2 days). About three weeks
for a good first version. It should follow the launch gates in section 4, not precede them.

## 6. Infrastructure and operations

| Item | Status | Notes |
|---|---|---|
| ★ Production Supabase on Pro with physical backups, an isolated restore drill, key custody | Owner | The Free plan has no backups. Marked as a final paid gate. |
| ★ Render plans sized for launch traffic; staging off the free tier for acceptance | Owner | Production is 0.5 CPU and 512 MB; staging sleeps when idle. |
| Alerting that actually reaches a person, spending alerts, an on-call rota | Partial | Render emails exist; external delivery is unverified. |
| Public status page and an incident runbook | Open | |
| Account deletion rehearsal including live session revocation and storage bytes | Partial | Database rehearsal passed; Auth sessions, storage and provider cleanup are open. |
| Data export for users | Open | Privacy page says none exists yet. |
| Load and abuse testing for the gateway, search and uploads | Open | Rate limits exist; load numbers do not. |
| Multi-instance and proxy acceptance | Open | |

## 7. Security

| Item | Status | Notes |
|---|---|---|
| ★ Independent penetration test or review of auth, RLS, gateway and file handling | Open | An agent review was done in Stage 3; a human or third party is the standard buyers expect. |
| Dependency and secret scanning in CI, and a disclosure policy | Partial | Secret scan script exists. |
| Threat model refresh for web search, local file read and the browser panel | Open | |
| SOC 2 readiness (do not claim it until it is true) | Later | Common ask from teams buying Teams plans. |

## 8. Design finish

| Item | Status | Notes |
|---|---|---|
| Pass 3: one icon set, motion language, dark-theme contrast | Open | Outlined in `ui-audit-2026-11-22.md`. |
| macOS sheets instead of free windows for settings and dialogs | Open | Needs live review on a Mac to get right; not changed in Pass 2. |
| Final screenshots, app icon sizes, DMG and installer art, store screenshots | Open | |
| Brand sign-off: name, mark, wordmark, tone | Owner | Mostly settled. |

## 9. Mobile

| Item | Status | Notes |
|---|---|---|
| ★ iPhone companion through TestFlight and App Review | Open | First launch priority in the timeline. |
| Android companion | Later | Separate track. |

## 10. Website, support and go-to-market

| Item | Status | Notes |
|---|---|---|
| ★ Live download page with signed installers, release notes and system requirements | Open | Today it shows the waitlist. |
| Help center, getting-started guide, migration guide for Slack | Open | |
| Support inbox with SLAs, macros and a security contact that is watched | Partial | Pages exist; a human process does not. |
| Waitlist-to-invite emails and a small beta cohort before the public launch | Open | |
| Privacy-respecting analytics, with consent where required | Open | |
| Launch comms: announcement, demo video, pricing explainer | Owner | |

## 11. Go or no-go

1. Every ★ item above is Done or consciously waived by you in writing.
2. A signed Mac and Windows build passes a scripted acceptance run: sign in, import Slack,
   mention-to-build, approve, apply, open a pull request, remove the import, delete the account.
3. A small cohort uses it for a week with monitoring and a rollback ready.
4. You approve the launch. I never deploy production or spend money on your behalf.

## What I would do first

1. Signed builds and clean-machine tests, because they gate everything user-facing.
2. The real-data acceptance runs (Slack import, GitHub pull request, large-history scan).
3. Security review of web search plus local file read.
4. Stripe live mapping and the entity and legal pages, in parallel, since both need you.
5. The browser panel, after the above.
