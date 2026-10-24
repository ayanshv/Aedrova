# Repair roadmap Step 3 — workspace AI setup

October 15, 2026. Owner approved Step 3 and requested personal actions only at
the final handoff. Desktop source implementation; no production promotion.

## Delivered

Desktop independent Space and subspace creation now includes a required third
review: selected provider, actual model policy, background versus reviewed builds,
context/execution disclosure and explicit acknowledgement. Changing provider or
workflow invalidates that acknowledgement. The included gateway chooses the
approved model under existing plan limits; the UI does not promise arbitrary
models that the backend cannot serve. Local provider mode uses its default model.

Provider/nickname use existing workspace RPCs. Execution consent is saved per
account/workspace on this computer through the existing project settings, not
silently granted to other teammates. It does not connect a project folder. Main
agent and Bud build requests honor explicit manual mode and open a review without
launching background execution. Applying original files and publishing retain
their existing approvals. Disconnecting a project preserves the AI setup while
turning automatic execution off.

A subspace preference failure retains the already-created workspace and retries
only its preferences. Pending setup disables execution and returns to the review
on dashboard entry. Refresh failure retains the workspace ID. Existing workspaces
and external creation APIs are not migrated or newly server-gated by this desktop
change. Website creation is outside this batch.

Go to Dashboard closes the account dialog before synchronous activation can start
another request. The introductory profile flow retains its selected authorized
workspace across that ordering change. Compact AI review scrolls rather than
compressing disclosures and buttons.

## Validation and limits

Regression tests exercise required acknowledgement, preference changes, scoped
persistence, subspace partial failure/retry, pending setup recovery, dismissal and
main/Bud manual routing. Light/dark and short-window offscreen previews were
inspected. Local artifacts are in ignored work/ai-step-3.
Final full desktop suite: 835 passed; Ruff and diff checks passed. The existing
audioop deprecation warning remains unrelated to this change.
Existing authenticated
hosted AI acceptance is recorded separately in ai-responsiveness-step-2.md; this
batch does not certify a new hosted workspace creation or signed installer.

## Existing key mitigation

The owner requested keeping the existing OpenAI key instead of generating a new
one. No key was generated, revoked or changed, and no Render environment settings
were changed in this batch. The browser automation runtime was reset, clearing
retained variables/handles. An exact-byte scan found no copy in tracked desktop
repository files or Step 2 artifacts. Render was left on Deploys, outside the
credential editor. Future credential operations must avoid broad DOM snapshots.

These actions cannot remove the value from the earlier tool-output transcript or
undo its exposure. They do not prove absence from every log or establish whether
the key has been misused. The original rotation recommendation remains a risk
mitigation, but the owner elected to retain the key; it is not a required action
for completing this requested source batch. Existing staging accounting limits
remain unchanged.

## Final owner actions

None required to apply or test this local source batch. No SQL, new key, paid
hosting or account intervention is requested. Production deployment, installer
replacement, public connector approval and optional Claude funding remain separate
release gates. Obtain approval before Step 4 of the current repair roadmap.
