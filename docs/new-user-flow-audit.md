# New-user flow audit — October 13, 2026

## Release verdict

The available application flow was exercised and defects were corrected. This is
NOT a public-launch approval or a claim that every provider works end to end.
Live staging exposes two release blockers: included managed AI is not configured,
and Instagram/TikTok account sign-in is unavailable in its deployed connector inventory.
Other providers still need fresh grant/read/refresh/revocation acceptance. Apple
membership/account setup was not touched. No production data, billing, download,
waitlist, account-wide permission or real meeting activation was changed.

## Audit isolation and actual journey

Used the real macOS source app with a separate local preference file,
work/user-flow-audit/fresh.ini, explicit staging endpoints and a new synthetic
workspace, “User flow audit Oct 13.” Existing production preview and normal
staging settings/drafts were left alone. The synthetic project contains only
README.md. No account profile values were deliberately changed.

Observed through native/browser UI:

- Google sign-in using an existing staging test account returned to the app.
  The browser callback used the branded success screen. This is repeat sign-in,
  not acceptance with a brand-new Google account or new consent grant.
- Workspace name and agent/provider setup created the workspace successfully.
  Go to dashboard entered the first-run onboarding automatically.
- Landing, demo mention, simulated processing and physical Command-K hook worked.
  The demo did not invoke a real build.
- Theme-photo choices were available; found and corrected selection/apply mismatch.
- Required profile setup progressed through identity, optional details and status,
  saved existing values, then returned to the next app-onboarding step.
- Synthetic project folder and Codex selection saved, followed by execution settings,
  optional GitHub setup, device setup and summary. Device setup opened/closed;
  no new microphone/camera/screen permission or call was started in this audit.
- Required Bud onboarding opened automatically. Initial hosted load timed out with
  an actionable Retry state; Retry then loaded successfully, not an endless skeleton.
- Marketing star selection mapped to Marketing. Name, color controls, custom-color
  entry and continuous personality sliders appeared. Entered a synthetic name,
  purpose and custom personality. No external access was granted to that draft.
- The connector stage filtered to Marketing tools and displayed app icons.
  Instagram and TikTok details both reported account sign-in unavailable.
- Finish later returned to the controls tour. Next and Pause worked; focus returned
  to the composer. Command-K opened the conversation switcher; Escape closed it.
- A synthetic chat message appeared immediately and was subsequently acknowledged.
- Work navigation and Start a build opened the builder with the saved synthetic
  folder. A bounded greeting-function request reached the durable queue and failed
  with “Included AI access is not configured yet.” No hosted model inference began.
  Failure was also surfaced in conversation under Nova. The original folder stayed
  intact. Queue history showed Failed, recovery and saved-file controls.

Account → Log out was finally verified live through the native menu: the session
was removed and the real Google sign-in screen returned. The isolated audit app
was then closed. Synthetic staging workspace remains available as labeled test
data; no permanent deletion was performed.

Native accessibility snapshots intermittently lost virtual list rows between syncs;
not every message context-menu or profile-popup action could be verified through
that tool. Those interactions have automated coverage, but are not claimed as a
fresh live native acceptance. No physical second-device/media test was substituted
with a synthetic fixture.

## Corrected defects

1. Theme photo selection now applies the checked theme, including native accessibility
   selection, rather than only responding to a mouse-click signal.
2. Main navigation checkbox selection now changes the actual page and keeps a single
   active tab. Programmatic synchronization blocks signals to avoid reentrant changes.
3. Profile Continue / Save & continue accessible names track the displayed action.
4. Bud Continue / Start chatting accessible names track the current setup stage.
5. Real onboarding settings have their real heading/description exposed to assistive
   technology; they are no longer labeled as a simulated product preview.
6. Embedded required profile pages use the existing outer scroll area, eliminating
   nested page scrollbars. Standalone profile editing retains its own scrolling.
7. Connector cards use View setup when account sign-in/managed access is unavailable,
   and expose Service setup required. Connected grants remain Manage; ready account
   sign-in remains Connect. Advanced token capability does not imply login readiness.
8. Codex sandboxed shells ignore global/system Git config, avoiding denied reads of
   personal ~/.gitconfig without widening filesystem/network access. Windows shells
   receive the scrubbed Windows PATH rather than Unix-only paths.
9. Build history shows the current session’s stopped-run status/output for the exact
   same run, user and workspace. After restart it gives explicit inspect-before-retry
   guidance. Provider output is not newly persisted in the queue database, and logout
   clears the panel. No other workspace’s output is shown.
11. Reopening Account & workspaces now immediately leaves the old workspace-creation
    confirmation and presents existing workspace navigation before refreshing. A
    timed-out refresh no longer strands the user on the earlier All set screen.
10. The staging launcher accepts a separate --settings-file so future first-run audits
    do not overwrite the owner’s normal preferences.

## Builder and Bud evidence

Real installed Codex, using its existing local login, generated a greeting function
and Alice/Bob tests in a disposable build copy; independent unit tests passed and
the original was unchanged. This does NOT prove the hosted managed gateway works.
The initial run exposed the private Git-config warning fixed above.

Both installed Codex and Claude Code also authenticated to a controlled loopback
model fixture, performed real filesystem/tool operations and returned tool results.
The rerun includes actual sandboxed Git rev-parse and succeeds. This validates
CLI protocol/tool execution; model responses in this probe are fixtures, not paid
Claude inference. Hosted Claude generation/accounting remains unverified.

Bud routing, configured avatar/name, personality prompt, queued identity/version
checks, role filtering and stale/unauthorized-grant denial have automated tests.
A new source-backed Bud answer was NOT accepted live in this audit: provider
configuration/grant acceptance and hosted managed AI remain prerequisites.

## Connector acceptance and login-only limits

Normal configured flows use OAuth, not customer API keys or manual authorization
codes. A resource selection is still deliberate access scoping, not developer setup:

- GitHub: login/consent and named installed-repository picker.
- Supabase: login/consent and named project picker.
- Notion: login/consent and named shared-page picker.
- Figma: login/consent and file LINK. Current narrow file-content scope does not
  enumerate all account files; literal login-only is not supported by that scope.
- TikTok: authorized account selected automatically; unavailable in current staging.
- Instagram: professional Business/Creator account selected automatically after
  consent. Personal Instagram accounts are not supported. Staging is unconfigured.
- Stripe: provider-owned account/install selection; external-testing/public-app
  eligibility remains a separate gate from Aedrova’s subscription billing.
- Vercel: integration installation plus named authorized-project picker;
  integration registration/agreement remains open.
- Web search: Enable web search plus research topic; Aedrova’s provider funding/key
  remains open. Customers should not need a paid personal search API account.

Backend tests exercise OAuth state expiry/binding, callback exchange, resource
verification, discovery, encrypted token storage, expiry/refresh, disconnect and
cross-account/workspace denial with controlled provider HTTP responses. No blanket
claim of public provider approval, live revocation or all-account compatibility.
Existing authorized resources were not revoked or widened for the audit.

## Broader regression coverage and limits

Desktop regression suites cover chat send/retry/duplicate prevention, reactions,
threads, edit/unsend, quote/save/pin/share, rich text, grouped mentions, presence,
notifications, channels/DMs/profiles/roles, file/voice previews, upload policy,
private file/context denial, build cancellation/recovery/review/delivery,
meetings/consent/transcript confirmation/withdrawal, onboarding/defer/resume,
light/dark/reduced-motion and compact layouts. These are automated UI/service
checks, not fresh real-device acceptance for every listed feature.

Backend suite: 487 passed on this audit. Covers connector lifecycle, billing,
server usage/rate/spending limits, context isolation, upload/voice acceptance,
meetings, provider gateway, signed webhooks and trust-site functionality.
Final full desktop regression before the last account-reopen correction: 785 passed.
After that correction, all 49 account/identity/connected/launch-baseline tests passed. Full source/test/script Ruff, tracked-secret
scan and diff whitespace checks pass. The real loopback Git/tool rerun passed for
both installed CLIs. CI is triggered by the development-branch push; a new signed
Mac/Windows release was not created.
No database schema changed. Earlier passing PostgreSQL/RLS checks remain relevant;
no test SQL was run in hosted Supabase. Existing Apple/Windows installer,
live-billing, hosting, physical-media, independent-security-review and operational
restore/alerts gates are not closed by this audit.

## Required next setup and owner interventions

No new SQL, purchase, secret-in-chat or Apple action is required for these code fixes.

To unblock the actual staging builder: Render → aedrova-beta-staging → Environment,
review the private model configuration and managed-gateway activation against
Aedrova_site/docs/final-beta-phase-2.md and docs/anthropic-setup.md. The live
/api/runs endpoint rejects when gateway_enabled is false or the selected provider
has no configured model. Deploy only the approved staging configuration with its
server spending limits, then repeat the bounded workspace build and reconciliation
checks for both providers. Do not enable production/public AI or bypass billing.
Provider-key transmission to Render requires specific action-time approval when
that step is reached; no key should be pasted into this chat.

For login-only connectors: finish the provider-owned registrations/reviews in
Aedrova_site/docs/account-connector-setup.md and docs/bud-oauth.md, using the
STAGING callback https://aedrova-beta-staging.onrender.com/buds/oauth/<provider>/callback
for staging validation. Instagram needs its developer app/professional tester;
TikTok needs its actual client pair/approved test configuration deployed there.
Vercel needs the prepared integration agreement/creation; Stripe testing remains
deferred to pre-packaging verification; managed Search needs the deferred funded
provider plan. Agreements, identity checks and purchases are owner actions, not
something to fake in the app. Then approve only intended scopes and run each
provider’s fresh login → selected-resource read → refresh → disconnect/reconnect
and wrong-account checks. These block complete connector/launch acceptance.

Physical final checks remain: another tester/device for calls and transcription,
actual voice playback/listening, narrow-width/native accessibility inspection,
Windows clean-machine install/update/uninstall and final second-account re-login.
The code tests are useful evidence, not a replacement for those checks.

Apple activation remains a separate requirement. Reply “Apple membership active”
when the actual Developer account confirms activation; the completed purchase
screen alone does not verify the current developer-account state.
