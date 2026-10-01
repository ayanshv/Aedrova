# Autonomous builds and inline agent activity — 2026-09-30

This completes the requested M7 follow-up. M8 has not started.

## Owner action, once per connected project

Reopen the rebuilt `dist/Aedrova.app`. In Projects → Project settings, choose the project
folder and coding provider, enable **Let my agent plan and execute automatically**, and
Save connection. Then send `@Nova, build …` (or `@Aedrova …`) in chat. Previous auto-plan
permission did not authorize coding, so existing connections require this explicit setting
once. No new Supabase SQL or Google OAuth configuration is required.

Each mention now retrieves the permitted workspace corpus, generates its own plan, and
continues into implementation/testing without displaying a planner or asking again for routine
in-scope tool actions. The visible build details UI has Start build, Stop, source inspection,
folder access and review/delivery; there is no visible Create plan or Approve plan step.
The internal planning phase remains for requirements/citation verification.

## Activity in chat

Public agent updates and actual tool actions appear as plain text above the composer.
Running activity has a subtle left-to-right text shimmer. Stop stays next to it. Clicking the
status opens details voluntarily. Reduced motion disables shimmer; hidden/completed activity
stops its timer. The log is requester-local, bounded and cleared on logout. It shows public
updates and actions, not private reasoning events. Both appearance modes were inspected.

New appended conversation does not invalidate a plan already underway. The original evidence
must remain unchanged and accessible: edited/deleted sources or retired decisions stop the
transition into coding. The next mention gathers the latest corpus. Limits fail explicitly
rather than silently using partial context. This is a point-in-time authorized corpus, not
unlimited continuous background recording. New overlapping requests are refused, with their
text preserved, until the active run completes or is stopped.

Changing/disconnecting saved project authority stops automatic work. Claude automatic file
permissions remain within the build copy; command approvals retain the existing sandbox and
no-network configuration. Codex retains workspace-write/no-network coding. Applying reviewed
changes to the original project and publishing to GitHub are still separate explicit approvals.
Aedrova must remain running; restart recovery and durable execution are M8 work.

## Codex failure correction

The previous adapter aborted on every JSON `error` event, including recoverable reconnect
notifications, and replaced the actual failure with a generic login/quota message. It now lets
the CLI finish its own recovery and accepts success only after a completed turn and clean exit.
It does not replay an entire coding turn automatically. Terminal failures are classified into
usage limits, authentication, model access, context limits, incompatible CLI, sandbox or network
errors. stderr is drained concurrently and bounded; raw diagnostic content is never displayed.

The old failed run's specific cause cannot be recovered because it was discarded. A real
Codex run with the corrected adapter completed successfully on this Mac. Actual exhausted
quota, revoked login or provider outages still require the indicated provider/account action;
no desktop patch can grant extra usage. This Mac's CLI reported an existing ChatGPT login.
Claude paid execution and live GitHub publishing remain outside the verified live checks.

[Official non-interactive Codex documentation](https://learn.chatgpt.com/docs/non-interactive-mode)
and [authentication documentation](https://learn.chatgpt.com/docs/auth) informed the protocol check.

## Verification

The complete Python suite, database suites, lint/format, packaged launch/signature and baseline
secret checks are recorded at handoff. New regressions cover recovery followed by success,
terminal error classification without diagnostic leakage, large stderr without pipe deadlock,
automatic mention-to-build execution, changed context, cancellation, saved scope, no planner UI,
private feed cleanup and shimmer lifecycle/reduced motion.

Real Codex acceptance: a single mention read a synthetic permitted workspace requirement,
planned, implemented calculator code and tests in a build copy, and passed six unittest cases.
No studio appeared. Original files stayed untouched; nothing was pushed. Evidence:
`work/autonomous-live.log`, `work/autonomous-agent-proof/`, `work/autonomous-agent-tests.log`,
`work/autonomous-sql.log`, `work/autonomous-package.log`, `work/autonomous-smoke.json`.

Included AI usage under an Aedrova subscription remains M9, with backend provider billing and
scoped credentials. No shared provider secrets or billing bypass were added to the desktop.
For GitHub publication the previously documented owner browser authorization and disposable-repo
acceptance are still required; code-level tests do not establish a successful live push.
