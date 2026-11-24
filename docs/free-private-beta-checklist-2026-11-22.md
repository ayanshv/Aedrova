# Before the free, private beta

**This is the final gate before the beta launches.** Every ★ item must be Done before anyone
is invited (owner decision, November 23, 2026).

Scope: invited testers only, access behind a password or invite, no payments. Billing, tax,
refunds and Stripe live mode are out of scope. Written November 22, 2026. Status key: **Done**,
**Partial**, **Open**, **Owner** (only you can do it). Items marked ★ block the beta.

November 23 owner update: after the Mac VM test, track three remaining gates. Gate 9 covers
the OpenAI spending cap, Render alert and backups for the selected beta database. Gate 10
covers counsel review and deployment of the policies. Gate 12 covers the monitored feedback
address, invite message and known issues. The live Slack export test is waived for this beta.

## 1. Getting people in

| Item | Status | Notes |
|---|---|---|
| ★ Decide the gate: a shared password on the download page, per-person invite codes, or an email allowlist in the database | Owner | Recommended: password on the download page plus an allowlist so a leaked link or password is not enough to sign in. |
| ★ Enforce the allowlist at sign-in | Open | Today anyone can sign in with Google. Needs a database check on first sign-in and a clear "you are not on the list yet" screen. |
| ★ A way to give a workspace AI capacity without Stripe | Partial | Done and verified on staging November 23: Pro-sized gift, $100 shared pool, Free workspace upgraded by the app; the same web summary used 3% of the five-hour window instead of 81%. Production still needs the same settings and deploy, and the gift should be checked once the invite gate exists. |
| Invite email and a one-page install guide | Partial | Draft below. Add the verified private download link and access instructions before sending. |
| Tester list with name, email, OS and version | Owner | A simple sheet is enough. |

## 2. A build testers can install

| Item | Status | Notes |
|---|---|---|
| ★ Mac: Developer ID signing, notarization, a clean-machine install test | Partial | November 23 staging DMG and app passed signature, stapling and Gatekeeper checks. The exact DMG also passed checksum and Gatekeeper in the cloned Mac VM. A separate installation reached the account screen with fresh app settings and showed both sign-in options. Complete the authenticated walkthrough and verify the gated website download before release. |
| ★ Packaging check with the new browser engine | Partial | The bundled Qt WebEngine helper passed deep signature validation. Launch the browser panel from the installed signed app in the VM to verify it runs. |
| Windows build | Partial | A preview installer exists. For a private beta an unsigned build with SmartScreen instructions is workable; say so in the guide, or limit the first cohort to Mac. |
| ★ One environment for the beta | Owner | Pick the Supabase and Render projects testers will use and point the build at them. Do not mix staging and beta data. |
| Update path | Partial | The app checks for updates but does not install them. Plan on "download the new build" and tell testers. |

## 3. The database and services

| Item | Status | Notes |
|---|---|---|
| ★ Apply every migration to the beta project, in order | Owner | Includes join codes, shared chat activity, chat safety, shared pins, Slack history and Slack channels. Run the embedded test script first (`scripts/test_database.py`). |
| ★ Backups you control | Partial | Supabase showed seven scheduled backups for Aedrova Staging, most recent November 23, 2026 at 08:15 UTC. An isolated restore and coverage of Storage files still need verification. Confirm the selected project before release. |
| ★ Render capacity and a spend limit | Owner | In the selected beta service, check Metrics for memory and enable failure emails under Settings → Notifications. Verify who receives them. [Render notifications](https://render.com/docs/notifications) |
| ★ AI spending cap at the provider | Owner | In Settings → Projects → the project billed for the beta gateway → Limits, set the approved monthly amount, turn on Enforce a hard limit and add a 50% alert. [OpenAI project limits](https://help.openai.com/en/articles/9186755-managing-projects-in-the-api-platform) |
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
| ★ Run the real flows once on a signed build | Partial | The November 23 VM installation signed in to a staging workspace and displayed the active AI allowance. Verify automatic Zen onboarding on the replacement installer, then workspace creation, mention to build, delivery review and apply, and a real pull request. |
| Real Slack export | Waived for beta | Owner waived this launch gate on November 23 because no real export is available. Live import remains unverified. |
| ★ Agent run through the browser | Open | Needs a working model account (the Codex login hit its usage limit today). |
| Two accounts | Open | Second-account isolation for chat, Slack archive and files. |
| Meetings | Partial | The meeting health check returned 503 earlier. Either fix it or turn meetings off for the first cohort. |
| First-run permission prompts on a clean Mac | Open | Microphone, camera and screen, and the setup step that explains them. |

## 6. Support and learning

| Item | Status | Notes |
|---|---|---|
| ★ A feedback and bug channel | Partial | The live support page lists contact@aedrova.com. Confirm the mailbox is monitored and that the signed app links to it. Ask for version and OS and keep private message content out of reports. |
| Crash and error reports | Open | Optional for a dozen testers if you can ask them to send the log. |
| A short list of known issues | Partial | Draft below. Confirm against the final beta installer before sending. |

### Draft Mac beta invitation

**Subject:** Your Aedrova Mac beta invitation

Hi [first name],

We’d like you to try Aedrova with your team. Download the Mac beta from [private download
link] and follow the access instructions in this invite. Open the DMG, drag Aedrova to
Applications, then open Aedrova and click **Get started**. You can create a workspace or
join your team with a workspace code.

This is a free private beta. If something gets in your way, email contact@aedrova.com.
Tell us what you tried, what happened, and your Aedrova and macOS versions. Leave out
private messages and files.

**Known issues**

- To update Aedrova, download the new installer from the same private link.
- Slack import has yet to be verified with a live export. Keep the original archive and retain access to Slack while trying it.

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
4. A pull request and an agent browser run.
5. Terms, privacy and the install guide, then invite five people first.
