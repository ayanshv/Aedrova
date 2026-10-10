# Milestone 7 — account, chat-to-project, review and delivery

Implementation for internal Mac alpha. No new Supabase migration is required.

## What now works

- Bottom-left account menu: identity, Settings, workspace settings, invitations and logout.
- Settings: update display name, system/light/dark appearance, reduced motion/transparency,
  and preferred VS Code/Cursor/Xcode/Finder. Google owns email/sign-in security.
- Styled keyboard-accessible dropdowns and a themed project folder chooser; paths can be pasted.
- Projects connects a local folder and optional GitHub owner/repository per account/workspace
  on this Mac. Opt-in automatic planning shares permitted workspace evidence only after an
  explicit named-agent request, including `@Nova, build …`. Coding still requires plan approval.
- Private chat activity opens the plan, ongoing tool approvals or completed build. This is
  requester-local progress; shared durable build history is not implemented yet.
- Builds preserve a separate starting baseline. Review shows added/modified/deleted files,
  binary summaries and executable changes. Large text files require IDE inspection.
- Apply explicitly writes the reviewed changes into the original project, checking every
  touched file first. Unrelated local changes and the Git index are untouched. A recovery
  receipt/copy remains beside the build. Restrictive file modes are preserved.
- Open the build or original project in the configured editor. No editor extension required.
- Preview site serves a copied static site on loopback only, excluding dotfiles and backend
  source. It needs root `index.html`; it is not hosted deployment or a framework server.
- GitHub preparation is read-only. It checks write access, matching baseline blobs, default
  branch and repository visibility. Publication separately approves an exact change digest,
  new branch and draft PR; never merges or force pushes. Scope expires after ten minutes.
  Workflow edits and common credential patterns are blocked. PR text excludes retrieved chat
  evidence; its title derives from the user's request and is shown before approval.

## Limits and remaining live acceptance

Local conflict checks are optimistic, not a multi-file filesystem transaction. Close other
writers during application. On interruption, Aedrova attempts rollback without overwriting
newer external edits; inspect the recovery copy and original project before retrying.

GitHub integration is tested with a deterministic transport, including denied/expired/changed
approvals, remote conflicts and partial PR failure. No actual branch or PR has been created
as part of this milestone. Owner GitHub browser authorization and a chosen test repository
are required to validate live delivery. Two-account hosted revocation and paid Claude execution
remain unverified from earlier milestones. Baseline credential scanning is not the full M13 audit.

Codex still uses the developer's local login for alpha. Included AI is M9. A build's final
message is not proof that all its tests passed; inspect actual agent output and generated tests.

## Owner steps

1. Reopen the rebuilt app, sign in, and choose Projects → Connect a project. Select a specific
   local folder and preferred editor in Settings. Optional automatic planning is explained there.
2. On first dashboard entry, use **Install GitHub CLI** in the setup screen. Existing installs
   are detected. The same screen is available under **Projects → Project settings → Set up
   GitHub**. Click **Sign in to GitHub → Copy code & open GitHub**, paste the one-time code on
   GitHub and approve the requested access. Then enter owner/repository and **Check GitHub
   connection** in Projects. Your GitHub account needs write access. Google login is separate.
   Installation needs an internet connection but no Homebrew, terminal command or admin password.
3. In a disposable test repository with an initial commit matching the local starting files, ask the named agent for
   a small feature, approve the plan, inspect Review & deliver, and explicitly approve a new
   branch/draft PR. This is the remaining live GitHub acceptance; no production push is needed.
4. If testing Claude, configure its developer API credentials outside the app source. Do not
   paste private credentials into chat. No new database or Google OAuth setup is needed.

Next technical milestone: M8 execution durability, including queue/recovery after interruption,
resource/concurrency controls, idempotent external actions and a usage ledger. Separate approval
is required before M8 begins.


## Guided GitHub setup follow-up

Implemented after the M7 completion checks, as requested. This is the basic dependency/setup
flow, not the full animated desktop tour scheduled for M11a. GitHub sign-in can be completed
later, and cancelling setup does not delete the workspace. Installation remains an explicit
button action, never a silent background executable install.

The helper is pinned to GitHub CLI 2.102.0, with SHA-256 values checked against GitHub's
release metadata. ARM64 and Intel downloads have separate checksums. Only exact executable
and license ZIP members are written; no archive paths are extracted. Cancellation, tampering,
invalid archive members and existing installation conflicts fail without replacing user files.
The helper lives under `~/Library/Application Support/Aedrova/tools/github-cli/2.102.0/`.
It does not alter PATH or install system packages. Updates need a reviewed release/checksum
change; it does not download arbitrary latest binaries at runtime.

Real validation on this ARM Mac: official download, checksum verification, installation into
a disposable test folder, `gh --version`, and real device-code request/display/cancellation
passed. No browser authorization was performed, token obtained, repository modified or PR
created by that check. Both current and earlier CLI code-message formats have regression tests.
Intel execution and fresh-Mac distribution remain release acceptance work. GitHub owns credential
storage; Aedrova does not capture tokens. Do not promise that every OS keychain configuration
behaves identically.

References: [official CLI release](https://github.com/cli/cli/releases/tag/v2.102.0),
[GitHub browser authentication](https://cli.github.com/manual/gh_auth_login),
[Git database API](https://docs.github.com/en/rest/guides/using-the-rest-api-to-interact-with-your-git-database).


## Final verification — 2026-09-29

- 243 Python tests pass, including the account/project/review journeys, delivery conflict and
  approval protections, installer verification/cancellation and GitHub login UI regression tests.
- All embedded PostgreSQL identity, onboarding, messages, communication and context/decision
  suites pass. No M7 schema changes.
- Ruff lint/format and `git diff --check` pass.
- Real Codex read a synthetic confirmed requirement, returned a cited plan, generated calculator
  code and tests in a separate copy, and the reviewed files applied into the original disposable
  project. All three generated unittest cases passed there. No production files were changed.
- Official ARM64 CLI download/checksum/execution and actual device-code display/cancellation pass.
- Light/dark settings, project, review, menu, dropdown and GitHub setup renders inspected; fields
  and helper content remain readable. Scrollable setup accommodates the authorization step.
- Rebuilt `dist/Aedrova.app`; ad-hoc signature verification, packaged account-screen launch and
  baseline runtime/resource secret/environment-file checks pass.

Evidence remains in ignored `work/m7-final-tests.log`, `work/m7-final-package.log`,
`work/m7-final-smoke.json`, `work/m7-delivery-proof/`, `work/m7-github-device.json` and
`work/m7-visual/`. No live GitHub publication is implied by these results.


Later update (2026-09-30): the owner requested autonomous execution and inline activity.
`autonomous-agent.md` supersedes the earlier per-run planning approval UX. Users explicitly
enable automatic planning/execution in their saved project settings; local application and
GitHub publishing remain separately approved.
