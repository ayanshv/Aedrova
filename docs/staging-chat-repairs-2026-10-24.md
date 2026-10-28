# Staging chat repairs and payment-free release acceptance — October 24, 2026

Status: source repairs delivered; integrated launch gate 1 remains PARTIAL / OPEN.
This is not production promotion, a signed installer, or public-launch approval.
All owner-paid actions remain deferred under final-paid-launch-gates.md.

## Repairs

- Completed conversational answers are individual messages rather than accumulated
  inside one activity block. Their request/response order survives another prompt,
  ordinary refreshes and switching channels during this signed-in session.
- Sort actual sent timestamps after normalizing time-zone offsets, with sequence as
  a tie-breaker. A reply cannot precede its request even if clocks/receipt times differ.
  Main-chat and thread responses retain their originating channel/thread.
- Retain completed build answers when starting a later request instead of clearing
  them along with transient activity. Thinking/tool rows remain transient.
- Render safe Markdown in agent answers, streaming previews and private Bud chats.
  Bold, lists and code now render rather than exposing Markdown delimiters. Raw HTML
  is disabled and QLabel image tags are stripped; Markdown cannot fetch images or
  read local resources. Existing selectable/copyable text behavior is retained.
- Project questions now receive bounded read-only evidence from the connected local
  folder; simply having a project binding previously did not supply it to QueryJob.
  Pure local-project questions skip connector selection and the full workspace scan.
  General greetings do not read the project or start a coding process.
- Project evidence honors Git ignored files, secret-name exclusions, credential scans,
  generated/dependency exclusions, no linked-file reads, text/size/count limits and
  cancellation. POSIX reads use rooted directory descriptors and O_NOFOLLOW. Maximum
  inspected files 10,000; selected candidates 64; file size 32 KiB; excerpt 8,000
  characters; combined excerpts 64,000 bytes. Coverage is explicitly partial.
  Files are untrusted data, never executable instructions. Relative file citations
  are fingerprinted and validated. The original project is never edited by this path.
- A folder connection changed during a reply withholds that result and asks for a
  fresh request. Model identity questions receive the exact managed model/provider
  configuration; identity remains Aedrova without concealing the underlying provider.

## Important persistence boundary

Ordinary user prompts still use the existing durable shared-message RPC/outbox.
Central-agent answers and build summaries in this patch are private desktop-session
history, not a newly implemented hosted assistant-message store. They survive UI
refreshes during that session, but not app restart/sign-out, and are not sent to
teammates as fabricated human messages. Private Bud DMs retain their existing hosted
history. Sign-out clears reply caches, request origins and pending build-summary state.
Do not claim cross-device persistence for central-agent answers from these repairs.

Previously displayed answers are not regenerated when connecting a folder. Send a
fresh project question to use the current binding and files.

## Payment-free checks and remaining boundaries

1. Free/promotion activation, owner/workspace authorization, fixed expiry, no automatic
   subscription, budget enforcement and billing lifecycle checks passed in controlled
   backend tests. Hosted new-workspace included AI activation is still not certified:
   free/promotion flags remain disabled in the inspected staging configuration. Enabling
   a new company-funded allowance is reserved for the final budget/activation gate.
2. Native Qt onboarding/configuration/Bud Finish later/highlight, upload, composer,
   responsiveness, connector single-action and centered spinner regressions passed.
   Full fresh-account native walkthrough still needs staging sign-in and live acceptance.
3. Conversation integration test runs the actual async QueryJob/queue/composer path
   against fake transport: greeting then connected-project summary, exact order,
   no replaced prompt, no leftover draft/thinking row, and validated project citation.
   No provider usage or private project transmission was used for this test.
4. Connector OAuth/state/access/permission regressions passed. This is not fresh live
   certification of every connector's grant, resource read, renewal and revocation.
   Existing public provider review/tester restrictions and operator Search configuration
   remain gates. Resume each fresh provider flow after the app is authenticated; ask
   for any materially new account grant at its actual consent screen.
5. Prepared a source launcher and candidate fingerprint, without packaging or releasing
   an unaccepted candidate. Existing signing, installer clean-machine, live meeting,
   operational and production smoke requirements remain open.

## Verification

Initial full desktop suite: 976 passed. Follow-up selection covering the final local
project routing and release UX: 204 passed. Build/chat compatibility selection: 91
passed. The final complete suite after the build-history/logout refinements is recorded
in the final verification addendum below. Backend payment-free activation/billing/
connector/budget selection: 101 passed. Ruff, diff whitespace and tracked runtime/source
secret-pattern scan passed. Rendered actual message components were inspected in both
light and dark palettes using labeled synthetic examples, not live model responses.

Evidence (local, ignored): work/staging-chat-repairs-2026-10-24/ and
work/staging/{chat-and-release-final.log,chat-build-final.log}.
Backend evidence: Aedrova_site/work/staging-payment-free-checks.log.

## Latest staging launch and consolidated owner action

Restarted source staging using the existing isolated settings file and explicit staging
public endpoints; production endpoints remain rejected by the launcher. The native
Aedrova Staging account window is visibly open and ready for Continue with Google.
Safari changed tabs/timed out during automation, and the Google handoff did not finish.
Do not treat the resulting sign-in timeout as a passed authenticated walkthrough.

**Required now to unblock the remaining native and connector acceptance:** in the open
Aedrova Staging app, click Continue with Google, choose the existing staging test account
that owns your workspace (previous visible session: Ayansh Varma), complete any Google
security prompt yourself, and leave Aedrova visible. Reply “signed in.” No key, password,
SQL migration, payment or hosting upgrade is required for these source repairs.

To always run the newest local source, first quit the existing staging app, then open:
`work/staging/Open Latest Aedrova Staging.command`.
It uses the source checkout, explicit staging public profile and existing isolated
settings. Opening the bare source Python .app bundle does not supply these launch
arguments and must not be described as the reliable latest-build entry point.

## Final verification addendum

Final complete desktop suite after all source refinements: **978 passed** in 149.12s,
with the existing audioop deprecation warning. Backend selected checks: **101 passed**,
with the existing Starlette/httpx deprecation warning. Final Ruff, whitespace and
tracked source/resource secret-pattern scan passed. No production deployment, purchase,
allowance activation, new connector grant or public installer release was performed.
The final source process was restarted after the last code change; its native account
window is foregrounded at Continue with Google, without an expired pending login.

## Signed-in native follow-up

Owner completed Google sign-in. Native account shows Connected; Go to dashboard
successfully dismissed the account dialog. Two real @Aedrova hello requests completed
through the app's authorized deterministic greeting path (no model inference). Native
screenshot confirms prompt → answer → prompt → answer, both old/new user messages and
answers retained, empty composer, and no leftover Thinking row. DM picker opened in
one action. Existing Bud settings loaded, displayed the real 1/1 Free capacity and
original yellow swatch for the Marketing Bud; Finish later returned to chat.

This closes the pending sign-in handoff for these native checks; do not ask for that
sign-in again while its session remains valid. It does not certify a fresh-account
full tour, a metered project-summary response or every connector's OAuth lifecycle.
The existing TikTok staging audit Bud still reports Needs authorization. No fresh
provider grant was accepted and no provider-global revocation was attempted.
A current public /health probe timed out; /health/meetings still returned 503. Neither
result is a passing always-on/meeting acceptance. Paid infrastructure stays deferred.
Evidence: work/staging-chat-repairs-2026-10-24/live-chronology.png.

Readiness for prelaunch step 2: NOT YET certified. Finish the remaining payment-free
native and connector acceptance, explicitly carry paid-dependent checks into the final
paid gate, report the residual gate list and obtain owner approval before advancing.
No new payment, SQL or credential-generation action is required by this follow-up.
