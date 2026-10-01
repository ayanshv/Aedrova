# Milestone 5 — real local coding agents

Implemented for internal alpha. Codex completed a real model-driven plan through the Create plan button, wrote Python
files after the approval button, and ran five passing tests; an independent rerun also passed.
Claude's adapter, permission hooks and packaged runtime initialization are tested, but a
paid Claude build still requires the owner's Anthropic API setup. Signed-in hosted
workspace-to-build acceptance also remains an owner check. Neither is implied by unit tests.

## Use the build flow

1. Open the rebuilt `dist/Aedrova.app` in `/Users/ayanshvarma/Documents/Aedrova` and sign in.
   Quit an older app instance first if you have one open; save any unsent drafts before quitting.
2. Open **Builds → Start a build**, or type `/build your request`, `@Aedrova build your request`,
   or `@YourAgentNickname your request` in either chat composer. These commands open a
   private build window; they are not posted as public chat messages. Ordinary chats never start a provider or gather AI context. A leading agent mention opens
   the private build window; context sharing still requires consent.
3. Choose a **local project folder**, choose Codex or Claude Agent, describe the task, and
   enable context sharing. Empty folders and uncommitted changes are supported. Dependency
   folders and common secret files are excluded from the snapshot; install needed dependencies
   in the build folder where necessary. Coding commands have network restrictions.
4. Click **Create plan**. Read the generated plan and acceptance criteria. Click **Approve plan &
   build** only when ready to authorize local coding and test execution. Changed workspace
   evidence or a modified build checkout requires a fresh plan.
5. Review streamed commands, exit codes, the provider's test report and changed-file summary.
   **Open build folder** opens the independent local result. Your original repository is not
   automatically overwritten. Applying changes, GitHub push/PR approvals and previews arrive in
   milestone 7. Keep desired build folders; they persist after Aedrova closes.

Build folders live under `~/Library/Application Support/Aedrova/builds/<id>/project`.
They are independent Git snapshots of the selected files, with no origin remote and Git hooks
turned off. Successful builds become the starting folder for your next request. Snapshots exclude
common secrets and dependency folders and reject external symlinks; limits are 20,000 files,
25 MiB per file and 200 MiB total. Your original folder stays unchanged. This avoids a worktree's shared `.git` control files. Local result folders can
contain private code or agent-generated summaries. Delete folders you no longer need in Finder.

## Required owner actions now

**Milestone 5 itself needs no migration. The newer Milestone 6 context flow requires the migration
in `milestone-6-context.md`. No Google OAuth change or Supabase key entry is required.** Existing
message/table RLS and the milestone 4 migrations provide the signed-in reads used here.

**Codex:** the installed CLI on this Mac is version 0.155.1 and its ChatGPT login was verified.
No additional Codex login is currently needed here. On another Mac, install the official Codex
CLI and run `codex login` in Terminal. This alpha uses the local account's model allowance.
The CLI must support `exec --json --ignore-user-config --ignore-rules --ephemeral`.
[Official Codex non-interactive documentation](https://developers.openai.com/codex/noninteractive/).

**To use/test Claude:** create an API key in the Anthropic Console and enable API billing.
Do not paste it into Aedrova chat, this conversation, source code or a committed `.env` file.
For this internal alpha, launch the app from Terminal with a temporary environment variable:

```zsh
read -rs 'ANTHROPIC_API_KEY?Anthropic API key: '
export ANTHROPIC_API_KEY
/Users/ayanshvarma/Documents/Aedrova/dist/Aedrova.app/Contents/MacOS/Aedrova
unset ANTHROPIC_API_KEY
```

The `read` prompt hides input and does not put the secret in shell history. Leave that Terminal
open while using the app; the variable is removed after the app exits. A Finder-launched app
will not inherit this Terminal variable. This setup blocks only Claude's paid live acceptance,
not Codex. The bundled Python Claude Agent SDK supplies its runtime; a separate Claude CLI
installation is unnecessary. Anthropic requires API authentication for this third-party
integration unless separately approved; a Claude subscription login is not offered here.
[Anthropic integration/authentication guidance](https://code.claude.com/docs/en/agent-sdk/overview).

**Hosted acceptance:** in your signed-in workspace, put a harmless precise requirement into a
channel and a reply, invoke a small build, verify that the plan references those messages, then
approve and inspect its code/tests. Test with a second account that lacks the private-channel
membership: its context must exclude that channel. I did not borrow your browser session or
read private account tokens to substitute for this check.

## Scope and limits

- These are real coding runtimes, not simulated AI replies. The current surface covers repository
  inspection/search, planning, file edits, local commands/tests, cancellation and results. It is
  **not yet complete feature parity** with either standalone product: arbitrary MCP integrations,
  browser automation, unrestricted networking, durable sessions, multi-repo execution and delivery
  flows are not included in this milestone.
- Every readable channel in the selected workspace is traversed, including private channels/DMs
  accessible to the requester, all root messages, and all replies. Retrieval runs only on explicit
  invocation under the signed-in user's existing RLS. Unrelated workspaces are excluded.
- Evidence is written as a private, searchable JSONL file outside the Git checkout. It includes
  message IDs, channel names and supported UTF-8 attachments up to 256 KiB each. Large/binary
  attachments have metadata only; there is no PDF/image/video transcription in this milestone.
  An 8 MiB total context cap fails explicitly rather than silently omitting older messages.
  Milestone 6 now keyset-pages the scoped channel inventory, with a 10,000-channel limit.
- This is a point-in-time corpus, not a guarantee that the model reads every byte or understands
  every requirement. Milestone 6 adds ephemeral indexing, retrieval evaluations and source presentation. Active conversations can invalidate a plan before implementation.
- Context is rechecked before each phase and again before a gathered snapshot is accepted.
  Detected revocation/sign-out or a failed chat access refresh cancels active work and hides the
  private build UI. Detection depends on the app's existing refresh loop; it cannot retract data
  already sent to a provider. No generated result is automatically sent to teammates.
- Codex uses read-only planning, workspace-write implementation, no automatic escalation,
  network-disabled commands, ephemeral sessions, and no inherited user config/rules. Claude uses
  explicit read/edit/command tools, scoped file hooks, per-edit/per-command approval, empty settings
  sources, strict MCP configuration and its native sandbox with unsandboxed commands disabled.
  This is not a security certification or a claim that a local agent cannot read any host data.
- Runs have a 30-minute timeout. Claude additionally has a 60-turn / $5 SDK budget. Codex uses its
  account allowance; there is no equivalent precise per-run dollar cap in this adapter.
- Cancel stops the runtime but does not roll back partial edits or refund consumed provider usage.
  Temporary context files are removed after the phase; results/copies persist locally. Provider
  retention follows provider settings/terms. A crashed app can leave a temporary context file;
  crash recovery and cleanup are milestone 8 work.
- Build summaries and approval state are in memory; there is no shared durable build history yet.
- Public customer billing/credential brokerage must be completed before distributing managed
  paid builds. Never ship a shared Anthropic/OpenAI secret in the desktop app. This alpha's owner
  setup is not the final customer onboarding flow.

## Chat and build refinements

Create plan now focuses missing input with a specific message and shows context retrieval
progress. Context gathering uses a separate connection so it does not occupy the chat queue.
Messages appear immediately with a sending state, preserve send order and reconcile with
server acknowledgements. Network delivery still takes time; failures remain visible. Timestamp
headers no longer wrap into message text, and scrolling stays anchored during updates.

## Verification

- 166 Python tests pass, including build and interaction regression tests (subprocess streaming/cancellation/timeouts,
  scoped context pagination, guest/revocation rejection, attachment handling, checkout isolation,
  exact approval baseline, provider environment filtering, Claude permission hooks and Qt journeys).
- All existing database migration/SQL suites pass locally with PGlite. No database schema changes.
- Real authenticated Codex planning + implementation + independent Python test execution passed.
  The actual UI-button journey and five generated tests passed. Evidence is in the ignored
  `work/build-click-proof.log`; only synthetic workspace content was used.
- Packaged Claude runtime initializes successfully without submitting a model request.
- Ruff lint/format, lock consistency, baseline release secret scan, packaging, ad-hoc signature
  verification and packaged account-screen smoke pass. Light/dark build windows visually inspected.
  Ad-hoc signing is not notarization or production release approval.

Repeatable commands:

```sh
uv run --no-sync pytest -q
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync python scripts/check_agents.py
# Explicitly makes model calls using your signed-in Codex account:
uv run --no-sync python scripts/check_agents.py --live-codex
uv run --no-sync python scripts/package_desktop.py
```

## Next approval gate

Milestone 6 is implemented; apply its migration and complete hosted acceptance. Milestone 7
(chat-to-IDE builds, review and GitHub delivery) requires fresh owner approval. The full application safety audit remains milestone 13,
after feature development and before public release.
