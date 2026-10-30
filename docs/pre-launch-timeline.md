# Aedrova pre-launch timeline

Planning baseline: October 30, 2026, Asia/Bangkok. Apple Developer membership is active, as reported by the owner. Account/team access, certificates and Apple login have not been verified by this planning task.

Target: 15–20 focused working days of execution, excluding external provider review, owner setup and funding delays. This is an estimate, not a promised launch date. Preparation may overlap; milestone completion remains gated. This timeline does not itself authorize another stage. Stage 1 acceptance was subsequently resumed by the owner; each later stage still requires approval.

Stage 1 remains OPEN. Previously passed: fresh onboarding, bounded OpenAI build/review/apply, Stripe test access, TikTok staging access and new-workspace Free activation. Offline English/Hindi desktop translation and simultaneous-reader prompt-display acceptance have now passed with two real staging accounts. Public-site localization remains partial and separate. The earlier bounded API test allowance was restored; offline acceptance needed no entitlement change.

## 1. Finish staging acceptance — Days 1–3

Passed: live Bud-cap/downgrade checks, uploads/voice transport, human audio clarity, Research three-turn conversation/follow-up/correction, and simultaneous English/Hindi reader/prompt display with offline models. Connector lifecycle acceptance also passed; see connector-lifecycle-acceptance-2026-10-30.md. Remaining: public Meta/Instagram/TikTok review.

Exit: evidence for each advertised flow; unresolved features held back from launch.

## 2. UI fixes and visual acceptance — Days 4–5 · 1–2 working days

Immediately after Stage 1, audit and fix visual and interaction issues across fresh login/onboarding, workspace selection/settings, chat/DMs/channels, files/audio, Buds/connectors, meeting setup and website/pricing/support. Keep the existing brand and working buttons. Correct spacing, hierarchy, alignment, clipping, confusing actions, loading/empty/error states and inconsistent icons. Review light/dark themes, window sizes, keyboard focus/tooltips, and representative long-label/RTL language layouts.

Exit: agreed UI issues fixed and visually reviewed on the final staging candidate; core flows remain functional, with no new product scope. Record remaining cosmetic issues explicitly. Do not begin this stage until Stage 1 exits or the owner approves an exception.

## 3. Security and recovery — Days 5–7

Independent access-boundary review, rate and spending limits, secret/input checks, and an actual isolated backup restoration.

Exit: no unresolved critical/high findings; restore and rollback evidence.

## 4. Production operations — Days 7–8

Prepare alerts, support routing, incident response, account deletion, connector revocation and production configuration inventory.

Exit: owners, runbooks and recovery actions documented; paid activation deferred.

## 5. Additional minor and sizeable features — Days 8–12 · 3–4 working days

Reserve 3–4 working days for one sizeable, contained feature or two smaller additions, including integration and acceptance. Examples: richer file previews, a focused Bud configuration improvement, or completing a bounded language experience. Select the actual scope before starting; these examples are not commitments. Keep the existing architecture and core workflows.

Exit: agreed behavior implemented, integrated and accepted, or explicitly deferred; feature freeze follows. Avoid new product pillars, major infrastructure changes or additions with unresolved external dependencies. Work exceeding the slot requires trading out another feature or revising the date.

## 6. Apple and installer preparation — Days 1–12 · parallel preparation

Use activated Apple membership for Developer ID/notarization setup and Sign in with Apple configuration. Prepare Mac DMG and Windows release pipelines and clean-machine checks.

Exit: signing identities and Apple login configured; Windows signing method selected. Any new costs wait for the final paid gate.

## 7. Final paid and commercial gates — Days 13–15 · owner controlled

Owner completes required production hosting/meeting guard, provider funding and any signing purchases. Finalize Stripe prices/entitlements; verify retries, renewals, failures, upgrades, cancellations and refunds. Complete funded Claude and real two-device meeting acceptance.

Exit: funded services operate and billing matches approved plans. No payments submitted by the agent.

## 8. Package, validate and launch — Days 16–20

Freeze candidate, sign/notarize Mac and sign Windows, validate clean installs/update/uninstall. Apply reviewed production migrations, verify backups, downloads, support, legal/operator disclosures and rollback. Invite a small cohort before wider launch.

Exit: explicit go/no-go approval, working download links and monitored production. Blockers delay release.

## Owner actions and external dependencies

No personal action is required to approve or read this plan. When execution resumes:

- Apple Developer account: sign in and provide the active team identifier/access when needed; complete any account security confirmation privately. This blocks certificates, notarization and Apple login, not general preparation.
- Meta/Instagram: complete requested business/access verification in Meta and submit accurate App Review materials. TikTok: provide the real demo and complete public review. Public connector availability remains blocked until approved; alternatively explicitly exclude those connectors from launch.
- Meetings and installers: provide access to a second device plus a clean Windows/Mac environment at acceptance time. The existing voice-message listening check has passed; repeat it only if audio changes warrant it.
- Final paid gate only: personally complete hosting/provider/signing payments and Stripe banking/activation as required. These block the corresponding production features.
- Before public commercial release: confirm the actual legal operator and required disclosures. C-Corp formation remains deferred; do not represent Aedrova as incorporated. If the 60-day offer is still advertised, reconcile its actual deadline/eligibility before launch; do not silently restart it.

Feature freeze: after step 5, only launch blockers, security fixes and release corrections. New feature requests go to a post-launch backlog unless explicitly replacing scheduled work. Security and release acceptance apply to every added feature; the feature slot does not waive launch gates.
