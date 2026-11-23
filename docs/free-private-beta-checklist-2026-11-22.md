# Before the free, private beta

**This is the final gate before the beta launches.** Every ★ item must be Done before anyone
is invited (owner decision, November 23, 2026).

Scope: invited testers only, access behind a password or invite, no payments. Billing, tax,
refunds and Stripe live mode are out of scope. Written November 22, 2026. Status key: **Done**,
**Partial**, **Open**, **Owner** (only you can do it). Items marked ★ block the beta.

## 1. Getting people in

| Item | Status | Notes |
|---|---|---|
| ★ Decide the gate: a shared password on the download page, per-person invite codes, or an email allowlist in the database | Owner | Recommended: password on the download page plus an allowlist so a leaked link or password is not enough to sign in. |
| ★ Enforce the allowlist at sign-in | Open | Today anyone can sign in with Google. Needs a database check on first sign-in and a clear "you are not on the list yet" screen. |
| ★ A way to give a workspace AI capacity without Stripe | Partial | Built on the early-access gift: Pro-sized allowance per workspace, $100 shared cap, Free workspaces upgraded once by the app. Needs the staging push, four Render settings and a retest (see `early-access-offer.md`). Production unchanged. |
| Invite email and a one-page install guide | Open | Download link, password, first-run steps, known issues, who to contact. |
| Tester list with name, email, OS and version | Owner | A simple sheet is enough. |

## 2. A build testers can install

| Item | Status | Notes |
|---|---|---|
| ★ Mac: Developer ID signing, notarization, a clean-machine install test | Owner | In progress. Unsigned Mac builds are blocked by Gatekeeper for most people. |
| ★ Packaging check with the new browser engine | Open | Qt WebEngine adds a helper process and roughly 150 to 200 MB. Re-run signing, notarization and the frozen-startup check. |
| Windows build | Partial | A preview installer exists. For a private beta an unsigned build with SmartScreen instructions is workable; say so in the guide, or limit the first cohort to Mac. |
| ★ One environment for the beta | Owner | Pick the Supabase and Render projects testers will use and point the build at them. Do not mix staging and beta data. |
| Update path | Partial | The app checks for updates but does not install them. Plan on "download the new build" and tell testers. |

## 3. The database and services

| Item | Status | Notes |
|---|---|---|
| ★ Apply every migration to the beta project, in order | Owner | Includes join codes, shared chat activity, chat safety, shared pins, Slack history and Slack channels. Run the embedded test script first (`scripts/test_database.py`). |
| ★ Backups you control | Owner | The free Supabase plan has no backups. Either upgrade the beta project or schedule a manual export and test one restore. |
| ★ Render capacity and a spend limit | Owner | Production is small. Check memory for a dozen testers and set an alert. |
| ★ AI spending cap at the provider | Owner | Set a hard monthly limit on the OpenAI account the gateway uses, and an alert at half. |
| Kill switches | Partial | The browser has `browser/enabled`. Make sure you can also switch off AI, web search and Slack import quickly. |
| Monitoring that reaches a person | Partial | Render emails exist. Send them somewhere you will see them. |

## 4. Safety and privacy

| Item | Status | Notes |
|---|---|---|
| ★ Beta terms and a privacy notice that match the product | Owner | The pages exist. Have counsel review the new browser sections, then deploy. Say plainly: beta, data can be lost, AI sends content to providers. |
| ★ Test web content steering an agent | Open | The browser and web search read untrusted pages while the agent can read files. Try instruction-injection pages, and consider defaulting testers to "Ask for approval". |
| Account deletion and data export | Partial | The privacy page promises both. A documented manual process is enough for a beta. |
| Confirm the browser, Slack import and web search defaults for testers | Owner | Decide what is on for the first cohort. |

## 5. Does it work for a stranger

| Item | Status | Notes |
|---|---|---|
| ★ Run the real flows once on a signed build | Open | Sign in, create a workspace, onboarding, mention to build, delivery card, and a real pull request. |
| ★ Real Slack export | Owner | Import into a test workspace, check the From Slack channels and a cited answer, then remove it. Do not paste exports into chat. |
| ★ Agent run through the browser | Open | Needs a working model account (the Codex login hit its usage limit today). |
| Two accounts | Open | Second-account isolation for chat, Slack archive and files. |
| Meetings | Partial | The meeting health check returned 503 earlier. Either fix it or turn meetings off for the first cohort. |
| First-run permission prompts on a clean Mac | Open | Microphone, camera and screen, and the setup step that explains them. |

## 6. Support and learning

| Item | Status | Notes |
|---|---|---|
| ★ A feedback and bug channel | Open | A monitored email and a link in the app. Include version and OS, never message content. |
| Crash and error reports | Open | Optional for a dozen testers if you can ask them to send the log. |
| A short list of known issues | Open | Saves a lot of repeated questions. |

## Not needed for this beta

Stripe live mode, tax, refunds, dunning, plan upgrade and cancellation flows, a public download
page, SOC 2, a third-party penetration test, a status page, load testing at scale, Windows
code-signing certificates (optional), localization beyond English and Hindi, an iPhone or
Android app, trademark filing, and incorporation (decide this before any paid launch, not
before an invited beta).

## Suggested order

1. Choose the gate and the environment, and write the beta plan grant.
2. Apply migrations, set backups and the provider spending cap.
3. Signed Mac build with the browser engine, and a clean-machine run.
4. Real Slack export, a pull request and an agent browser run.
5. Terms, privacy and the install guide, then invite five people first.
