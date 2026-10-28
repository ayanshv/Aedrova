# Composer agent permissions — October 27, 2026

The main and thread composers now expose a theme-aware dropdown immediately beside
file upload. Saved independently for the signed-in account and workspace on this
computer; missing or invalid preferences fail to **Ask for approval**. Guests
cannot grant execution authority. This preference does not enable background builds,
change provider selection, add connector scopes, or bypass workspace authorization.

## Behavior

- **Ask for approval:** trusted read-only inspection remains available; proposed
  file changes and commands needing runtime approval pause for an actual Allow/No
  decision with exact action details. No is the default. Planning cannot edit.
- **Approve for me:** automatically approves edits inside the isolated build copy
  excluding protected paths, and plain bounded pytest commands. Shell composition,
  custom scripts, external paths, plugin/config overrides and other commands go to
  the human gate. This is a deterministic local review, not another paid model call.
- **Full access:** project edits and commands run without per-action prompts inside
  the isolated build copy. It does **not** remove the sandbox, network restrictions,
  secret exclusions, workspace membership, billing limits, or the separate original-
  folder apply/publish review. The UI states this scope and requires explicit
  confirmation when a user chooses Full access; existing accounts are not upgraded.

Switching modes cancels an active build, dismisses outstanding approval and requires
starting a fresh task. The requested mode is captured for each phase; runtime and
background authorization are rechecked rather than inheriting stale approval.

## Execution implementation

The coding runtime now uses private stdio app-server sessions for composer-governed
runs, because noninteractive `codex exec` cannot return individual approval requests.
The adapter initializes an ephemeral thread, handles command/file approval requests,
returns per-action accept/decline (never session-wide acceptance), rejects scope
mismatches and unknown permission expansion, preserves command/test evidence, and
bounds events, time, tool count and process lifetime. Cancellation kills the process
group and pending approval cannot revive it. Managed sessions retain only their
scoped gateway token and never copy personal auth. Local sessions copy authentication
alone to a temporary private home; personal config, hooks and MCP servers are absent.
Temporary credentials are removed on normal cleanup. Child shell environment remains
scrubbed. Claude continues through its existing sandboxed PreToolUse gate, now using
the same selected permission policy and human prompt.

## Verification and limits

Full desktop suite passed: **1,031 tests** before the last cancellation/managed-auth
regressions were added. Final permission-focused suite: **28 passed**;
build/provider/background regression set also passed. Tests exercise actual fake
stdio subprocess request/response, approve/decline, scope mismatch, cancellation,
managed gateway isolation, conservative auto review, per-account/workspace persistence,
thread synchronization, Full-access confirmation, stale authority rejection and
project-change revocation. Changing the connected project resets authority to Ask.
The installed real Codex runtime accepted initialize + ephemeral untrusted/read-only
thread setup with network disabled; no model turn was submitted in that check.

Light/dark composer captures are in `work/agent-permissions-oct27/`. No new billable
provider build was used to certify this change. Funded Claude and real-device acceptance
remain existing launch gates. Source is updated; signed distributable installers have
not been rebuilt. Stage 1 is OPEN, not automatically promoted by this feature.
