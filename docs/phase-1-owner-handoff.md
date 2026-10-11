# Phase 1 owner handoff

Independent Phase 1 engineering is complete: 732 tests pass on Windows, macOS
and Ubuntu, with database and website/backend CI green. Tested native code: 8a98c27.
Phase 2, M14, production merges/deployment and public billing/downloads remain gated.
Do not send passwords, provider keys or session tokens in chat.

## Verified staging checks

- Separate Supabase project: Aedrova Staging (`scvmvqlzcqhwrrsiahpj`). Its 23 app
  migrations and restricted private backend schema are installed.
- Google provider is enabled; two distinct real Google accounts completed native
  PKCE loopback login. Both directions passed own-message reads, foreign workspace,
  channel, message and membership read denial, and foreign-message write denial.
- Restricted staging backend cannot read public workspace rows (42501).
- Separate free Render service is live at https://aedrova-beta-staging.onrender.com,
  deployed from service e3da1d7. Auto-deploy, checkout, releases and funded AI are off.
- Final source and CI evidence are recorded in final-beta-phase-1.md.

These checks do not certify all AI context, connectors, meeting media or desktop UI.

## Required owner actions to close Phase 1

### 1. Accept the staging desktop account journey

Quit the existing packaged Aedrova app yourself first, to avoid confusing it with
source staging. In Terminal, run:

```sh
cd /Users/ayanshvarma/Documents/Aedrova
uv run python -m scripts.run_staging --config work/staging/public-config.json --check-only
uv run python -m scripts.run_staging --config work/staging/public-config.json
```

The first command must pass. The second opens source with separate staging
preferences, database and service origins. Use a registered Google staging test
account. Confirm browser sign-in returns to the app, you can select/create a
staging workspace and reach its conversation, then sign out and confirm the session
is gone. Do not connect a production project or try paid AI/billing in this check.
If you cannot distinguish the source app or the return fails, stop and report the
screen/error. This verifies the real desktop handoff beyond the passing PKCE probe
and remains a Phase 1 acceptance gate.

### 2. Enable main-branch merge protections in both repositories

Open each repository's **Settings → Rules → Rulesets → New ruleset → New branch
ruleset**:

- https://github.com/ayanshv/Aedrova/settings/rules
- https://github.com/ayanshv/Aedrova-website/settings/rules

Name it `Release baseline`, set enforcement to **Active**, and target the default
branch `main`. Require a pull request before merging, block force pushes, and
restrict deletions. Require status checks to pass. Use these exact check names:

- Aedrova: `Desktop checks (ubuntu-latest)`, `Desktop checks (macos-latest)`,
  `Desktop checks (windows-latest)`, and `PostgreSQL RLS checks`.
- Aedrova-website: `verify` (the Website checks workflow).

Do not require a second person's approval while you are the only repository owner.
Keep the approval count at zero; the PR and CI checks are still required. Save and
confirm both rulesets show **Active** targeting `main`. Do not merge the release
branches or deploy production as part of this action. This establishes the merge
gate and remains required for Phase 1 sign-off. Security settings require the
owner's specific approval; this handoff does not silently change them.

## Optional staging housekeeping

In Supabase → **Aedrova Staging** → Table Editor → `workspaces`, review the two
workspaces whose names start `Beta isolation 1` and `Beta isolation 2`. Delete only
those disposable probe fixtures if they contain only the synthetic test content.
Never select production or bulk-delete unrelated rows. The test cleanup initially
used the wrong RPC parameter; it is corrected, but those sessions were signed out.
This housekeeping does not invalidate the passing isolation checks or block Phase 1.

## Later-phase gates

Live customer connector grants/revocation, model access, billing lifecycle, meeting
media/transcription, independent security review, business verification, macOS
Developer ID/notarization, Windows ACL/runtime/installer and update acceptance retain
their release gates. CI on Windows does not certify a signed Windows installer or
live Codex/Claude sandbox behavior. See final-beta-launch-plan.md and milestones.md.
Never switch waitlist to billing/downloads based on Phase 1 checks alone.

## Permission boundary

Phase 1 closes after both required owner actions are confirmed. Request approval
before Phase 2 (complete connectors and AI providers). Approval for Phase 2 does not
waive missing Phase 1 acceptance or authorize production launch.

## Owner confirmation and Phase 2 authorization

October 10, 2026: owner reports both required actions completed (staging desktop
acceptance and GitHub main-branch rulesets) and explicitly approves starting Phase 2.
Phase 1 is closed on that owner acceptance; this is not a separate automated
re-inspection of the desktop journey or hosted rulesets. Phase 2 connector/provider
validation is now authorized. Public launch, production merges, billing/downloads
and later phases remain gated. The subsequent Finish later fix passed 55 focused
Bud/onboarding tests and is included in the source handoff.
