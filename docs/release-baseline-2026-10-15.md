# Release baseline — October 15, 2026

Step 1 of the newly requested repair roadmap. This is an inventory and acceptance plan, not a claim that the implementation or launch gates are complete. Earlier Beta phases retain their historical names; this Step 1 does not reopen or certify the old Phase 1. Owner actions are consolidated at the end. No runtime, hosted configuration, credentials or database changes were made.

## Version and evidence boundary

- App inspected: `fbdc0efc5697569fff6ea6dce04a4ed03e6a3815` on `milestone-3-identity`.
- Website source snapshot: `863cd2665aa85e60a120bb9ee717d42777fe6c29`. Source commits do not prove deployed version.
- Historical latest desktop suite: 795 passed, recorded October 14; not rerun for this documentation-only task.
- Historical staging backend deployment reused e375bdc; exact currently running build must be checked before implementation acceptance.
- Source inspection today: agent routing, creation/dashboard handlers, message copy/selection hooks, connector controls and call controls. Hosted accounts and real calls were not tested today.
- Machine-readable full inventory: [release-baseline-2026-10-15.json](release-baseline-2026-10-15.json). Every requirement has a stable ID, independent source/live status, acceptance requirement and roadmap batch.

## Findings that determine the order

1. Restore bounded AI and conversational routing first. Staging explicitly denied included AI configuration in prior live testing. A greeting currently reaches analysis/build machinery; configured provider health and tool selection need separate tests.
2. Creation only submits a subset of required AI preferences. Dashboard acceptance code already exists; reproduce the actual remaining dialog before changing it.
3. Copy/selection and composer clearing have implementations, but the owner reports failures. Exact mention tokens, both composers, async send revisions and native selection behavior must be exercised.
4. Connector detail currently exposes OAuth, duration, token and resource controls. This conflicts with the requested single-action experience. Instagram staging read-only access passed historically; that does not certify the whole catalog or public customer availability.
5. Call controls exist, but the owner reports video failure. In-call audio uses system defaults and sharing covers the entire selected screen; these are not full device switching/window/tab sharing.
6. Private Bud saving/reopening passed for the first staging account. Foreign-account live isolation and real inference are still open. Existing RLS/local tests must not be reported as a completed two-account live test.

## Sequential roadmap and exit gates

1. **Establish baseline.** This document and complete requirement register; no fixes authorized.
2. **AI routing and availability.** Fast greetings/questions, correctly selected Bud identity, actual capped main/Bud replies, truthful progress; provider errors/limits/cancel.
3. **Mandatory AI setup.** All creation paths persist full AI settings and close the correct dashboard popup; no forced silent provider consent.
4. **Messaging and direct messages.** Copy/selection polish, revision-safe composer clearing, People/Buds picker, private access and live replies.
5. **Single-action connector UX.** Connect your account is the one normal action; remove duration/token setup from customer flow; truthful permissions and branded verified confirmation.
6. **Live connector certification.** Every advertised provider passes real lifecycle/isolation checks; provider review, permissions and unsupported discovery recorded explicitly.
7. **Core meeting repair.** Two devices: audio/video, joining/leaving, media permissions/recovery, host access checks and basic layouts/sharing; prioritize current failure.
8. **Meeting communication, intelligence and accessibility.** In-call communication, captions/transcript consent/review/context, history and permission-aware recording; test retention and revocation.
9. **Advanced meeting capability batches.** Presentation/effects, collaborative sharing/docs, breakouts/polls, language, telephony/apps/broadcast; feasibility, costs, permission model and delivery stages decided before promises.
10. **Staging promotion and release.** Exact reviewed revisions/config/schema; migration rehearsal and rollback; core live gates; production smoke; then separate signing, installers, billing and download activation.

Advanced Zoom-scale parity is retained in the register rather than silently deleted. It is not a credible single launch patch: choose a supported first-release subset explicitly before promotion. Zoom Docs/Apps/Rooms are vendor-specific names requiring an integration or an Aedrova equivalent decision. E2EE may conflict with server-side recording/transcription; settle supported configurations before claiming both.

## Product defects and connector requirements

- **AI-01 — Fast greetings and ordinary questions without Git/project/build work.** Source: Routing can invoke analysis/build paths; no isolated greeting path established. Live: Owner reports unnecessary work. Acceptance: Main-agent and Bud greetings use no Git/build tools; stream actual response; progress reflects actual work. Evidence: `src/aedrova/desktop/window.py:944`.
- **AI-02 — Restore included AI for main agent and Buds without bypassing limits.** Source: Provider paths exist. Live: Staging explicitly denied: included AI not configured. Acceptance: Capped real replies for main agent and Bud; provider failure, quota, timeout and cancellation tests; no unauthorized local fallback. Evidence: `docs/private-bud-conversations.md`.
- **SET-01 — Require complete AI configuration for every new chatspace.** Source: Creation currently passes provider/name/nickname; subspace uses separate path. Live: Not verified. Acceptance: Every creation entry requires model/provider/background builds/auto execution/approval preferences; durable reopening and failed-save recovery. Evidence: `src/aedrova/desktop/account.py:705`.
- **SET-02 — Go to Dashboard dismisses creation popup.** Source: open_dashboard already calls accept(); reproduce which dialog remains. Live: Owner reports persistent popup. Acceptance: All create/join/onboarding dashboard paths dismiss correct dialog, retain chosen workspace and avoid focus theft. Evidence: `src/aedrova/desktop/account.py:684`.
- **CHAT-01 — Copy messages and comfortably select text.** Source: Copy/context-menu/selection code exists. Live: Owner reports not copyable. Acceptance: Mouse, keyboard and context copy work on human/main-agent/Bud messages; selection supports multiline, links and code. Evidence: `src/aedrova/desktop/conversation.py`.
- **CHAT-02 — Softer, readable text-selection highlight.** Source: Needs visual audit. Live: Owner reports boxy/tight highlight. Acceptance: Light/dark/system, multiline and code selections are legible with comfortable line spacing; native copy preserved. Evidence: `src/aedrova/desktop/conversation.py`.
- **CHAT-03 — Clear composer after accepted agent or Bud send.** Source: Clear uses exact text comparison; root cause not proven. Live: Owner reports draft remains. Acceptance: Plain/mention-token/thread/private sends clear submitted revision; typing during send is preserved; rejected send retains recoverable draft. Evidence: `src/aedrova/desktop/window.py:944`.
- **DM-01 — DM + includes coworkers and all configured Buds.** Source: Coworker picker and separate private Bud dialog exist; combined picker pending. Live: Own private save/reopen passed historically; outsider test incomplete. Acceptance: People/Buds sections; every configured Bud discoverable; stable reopen; no duplicate DM; outsider read/write denied; actual Bud reply. Evidence: `docs/private-bud-conversations.md`.
- **CON-01 — Remove connection-duration menu from normal flow.** Source: Lifetime control exists. Live: Current source differs from requested UX. Acceptance: No duration menu; secure expiry/refresh/revoke policy remains enforced server-side. Evidence: `src/aedrova/desktop/bud_connectors.py:265`.
- **CON-02 — Exactly one connector action: Connect your account.** Source: OAuth, advanced token/resource inputs and selection actions exist. Live: Current source differs from requested UX. Acceptance: Normal disconnected detail has exactly one action; no token/code inputs; accessible pending/retry states; provider-required resource consent handled honestly. Evidence: `src/aedrova/desktop/bud_connectors.py`.
- **CON-03 — Provider login to branded connected confirmation and configured Bud.** Source: OAuth/callback/reader source exists. Live: Instagram read-only staging passed; catalog not fully accepted. Acceptance: Login/consent to callback preserves Bud/role/workspace; account/resource discovery where supported; verified access before success; cancel/denial safely recover. Evidence: `docs/social-connectors.md in website repository`.
- **CON-04 — Disclose necessary account access without claiming unlimited permission.** Source: Terms/privacy must match provider scopes. Live: Requested full-account wording not approved as a technical fact. Acceptance: Remove duration UX without replacing provider consent; accurate data/scopes/retention/disconnect disclosures; no claim Bud creation grants unrestricted access. Evidence: `docs/final-beta-launch-plan.md`.
- **REL-01 — Promote tested staging changes to main build.** Source: Repositories and historical deployed staging image differ. Live: Promotion not performed. Acceptance: Review exact app/backend/schema/config versions; migration compatibility, backup and rollback; core gates pass; production smoke before release. Evidence: `docs/pre-apple-launch-gates.md`.
- **CALL-01 — Repair video-call joining and media.** Source: LiveKit worker, controls and layouts exist. Live: Owner reports video calling broken; fresh reproduction pending. Acceptance: Two real devices/accounts: join, audible audio, visible video, toggle devices, network recovery, leave/end; permission-denied and revoked-membership tests. Evidence: `src/aedrova/desktop/meeting_call.py`.

## Connector certification status

Normal customers should not enter developer keys/codes. Provider login and provider-required account/resource consent are unavoidable where applicable. Use supported discovery to avoid manual resource IDs, but do not pretend providers can enumerate inaccessible resources. Managed Search is an enablement flow, not a third-party login. Linear remains excluded; inspect any legacy PostHog exposure before deciding whether to remove or include it.

- **PROV-01 — GitHub:** Historical connection and adapters; fresh-customer lifecycle pending.
- **PROV-02 — Supabase:** Source/setup exists; complete customer OAuth/resource lifecycle unverified.
- **PROV-03 — Figma:** Source/setup exists; historical file-link limitation requires current provider review.
- **PROV-04 — Notion:** Source/setup exists; current live lifecycle not certified.
- **PROV-05 — Stripe:** Bud app testing prepared; developer business verification blocks external testing; separate from subscription billing.
- **PROV-06 — Instagram:** Oct 14 staging callback/native Connected and profile/media endpoint reads passed; read-only instagram_business_basic; public review and lifecycle pending.
- **PROV-07 — TikTok:** Sandbox setup complete; new staging grant blocked by account mismatch/maximum-attempt restriction; older service reads do not prove new grant.
- **PROV-08 — Vercel:** Source adapter; provider registration/live lifecycle pending.
- **PROV-09 — Managed Search:** Managed service, not customer OAuth; source bounded usage; funding/key/live acceptance pending.

Each provider must verify real permitted reads/actions, identity and resource scope, callback state, token protection, expiry/refresh, refusal/cancel, pagination, quota/timeouts, disconnect/reconnect, external revocation and cross-workspace isolation. A successful callback alone is insufficient. Never claim posting/message/full-account rights from read-only social grants.

## Complete meeting request register

Every item below is retained independently in the JSON register. Unless specifically recorded otherwise, it is not live-certified. “Not established” means the focused audit did not establish an implementation; it is not proof that no relevant code exists elsewhere. Source controls are evidence to investigate, not completed acceptance.

### 1. Audio and video

- **MTG-01-01** Mute/unmute microphone. Batch 7; Related source path exists; completeness unproven; Core candidate / scope to confirm.
- **MTG-01-02** Toggle camera. Batch 7; Related source path exists; completeness unproven; Core candidate / scope to confirm.
- **MTG-01-03** Select microphone. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-01-04** Select speaker. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-01-05** Select camera. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-01-06** Audio settings and microphone modes. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-01-07** Join computer audio. Batch 7; Related source path exists; completeness unproven; Core candidate / scope to confirm.
- **MTG-01-08** Telephone dial-in. Batch 7; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-01-09** Speaker view. Batch 7; Related source path exists; completeness unproven; Core candidate / scope to confirm.
- **MTG-01-10** Gallery view. Batch 7; Related source path exists; completeness unproven; Core candidate / scope to confirm.
- **MTG-01-11** Hide/stop incoming participant videos. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-01-12** Virtual backgrounds. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-01-13** Video filters and appearance effects. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-01-14** Portrait lighting and supported enhancements. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-01-15** Share a second camera. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-01-16** Optimize shared video playback and audio. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-01-17** Push-to-talk. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-01-18** Automatically mute on join. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-01-19** Display names and profile pictures. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-01-20** Show/hide pronouns. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-01-21** Immersive view. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-01-22** Dual-monitor support. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.

### 2. Participant communication

- **MTG-02-01** In-meeting group chat. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-02-02** Private participant chat where permitted. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-02-03** Send to everyone or selected recipients. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-02-04** Share files where enabled. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-02-05** Share links. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-02-06** Save meeting chat. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-02-07** Emoji reactions. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-02-08** Raise hand. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-02-09** Nonverbal feedback. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-02-10** Respond to polls/quizzes. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-02-11** Change own display name. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-02-12** Add/edit own profile picture. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-02-13** Participant list. Batch 8; Related source path exists; completeness unproven; Core candidate / scope to confirm.
- **MTG-02-14** Invite participants. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-02-15** View meeting information and joining details. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.

### 3. Screen sharing and collaboration

- **MTG-03-01** Share entire desktop. Batch 9; Related source path exists; completeness unproven; Advanced / feasibility review.
- **MTG-03-02** Share application window. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-03-03** Share browser tab/supported content. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-03-04** Share computer audio. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-03-05** Share video content. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-03-06** Slides as virtual background. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-03-07** Share second camera. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-03-08** Pause/resume screen sharing. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-03-09** Annotate shared content. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-03-10** Draw/highlight/add text. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-03-11** Permission for participant annotation. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-03-12** Grant remote control. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-03-13** Request remote control. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-03-14** Multiple simultaneous screen shares. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-03-15** Side-by-side sharing layout. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-03-16** Share whiteboard. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-03-17** Create/edit collaborative whiteboards. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-03-18** Open/create Zoom Docs. Batch 9; Not established in focused call-module audit; Vendor-specific integration or Aedrova equivalent decision.
- **MTG-03-19** Co-edit documents. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.

### 4. AI and meeting intelligence

- **MTG-04-01** Meeting assistant/questions during call. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-04-02** Meeting summaries. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-04-03** Extract action items. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-04-04** Key points/highlights. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-04-05** Live transcription. Batch 8; Related source path exists; completeness unproven; Core candidate / scope to confirm.
- **MTG-04-06** Searchable transcripts. Batch 8; Related source path exists; completeness unproven; Core candidate / scope to confirm.
- **MTG-04-07** Automated captions. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-04-08** Translated captions. Batch 8; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-04-09** Meeting language translation. Batch 8; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-04-10** Ask questions about meeting content. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-04-11** Smart recording/recording highlights. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-04-12** Personalized AI notes. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.

### 5. Recording and history

- **MTG-05-01** Start/stop local recording. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-05-02** Start/stop cloud recording. Batch 8; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-05-03** Request host cloud recording. Batch 8; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-05-04** Grant selected participants local recording. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-05-05** Pause/resume recording. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-05-06** Record audio/video. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-05-07** Record shared screens. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-05-08** Generate recording transcripts. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-05-09** Save/review recordings. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-05-10** Recording highlights/summaries. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-05-11** View/search meeting transcripts. Batch 8; Related source path exists; completeness unproven; Core candidate / scope to confirm.

### 6. Breakout rooms

- **MTG-06-01** Create breakout rooms. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-06-02** Automatically assign participants. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-06-03** Manually assign participants. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-06-04** Participant self-selection. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-06-05** Rename rooms. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-06-06** Move participants between rooms. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-06-07** Open/close rooms. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-06-08** Broadcast messages. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-06-09** Broadcast voice messages. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-06-10** Return to main session. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-06-11** Host visits rooms. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-06-12** Share screens into rooms. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-06-13** Timers/countdowns. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-06-14** Preassign participants. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.

### 7. Polls and engagement

- **MTG-07-01** Launch live polls. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-07-02** Create multiple-choice polls. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-07-03** Create advanced polls. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-07-04** Run quizzes. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-07-05** Collect responses. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-07-06** Display results. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-07-07** Download reports. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-07-08** Reactions for instant feedback. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-07-09** Raised hands. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-07-10** Nonverbal feedback. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-07-11** Structured Q&A. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.

### 8. Host and co-host controls

- **MTG-08-01** Mute individual participant. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-08-02** Mute all participants. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-08-03** Request unmute. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-08-04** Stop participant video. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-08-05** Control screen-sharing permission. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-08-06** Control chat permission. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-08-07** Control unmute permission. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-08-08** Control renaming permission. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-08-09** Assign co-hosts. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-08-10** Transfer host privileges. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-08-11** Rename participants. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-08-12** Put participant on hold. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-08-13** Remove participants. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-08-14** Lock meeting. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-08-15** Enable/manage waiting room. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-08-16** Admit waiting participants. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-08-17** Join/leave sounds. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-08-18** Recording permissions. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-08-19** Whiteboard permissions. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-08-20** Manage captions/transcription. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-08-21** Report inappropriate behavior. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.

### 9. Security and access

- **MTG-09-01** Meeting passcodes. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-09-02** Waiting rooms. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-09-03** Lock meeting. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-09-04** Restrict joining. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-09-05** Remove unwanted participants. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-09-06** Participant permissions. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-09-07** Screen-sharing restrictions. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-09-08** Chat/file-sharing restrictions. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-09-09** Recording access control. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-09-10** Meeting encryption. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-09-11** End-to-end encryption for supported configurations. Batch 7; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-09-12** Report participants. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-09-13** Entry/exit management. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.

### 10. Accessibility and language

- **MTG-10-01** Automated captions. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-10-02** Manual captions. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-10-03** Live transcription. Batch 8; Related source path exists; completeness unproven; Core candidate / scope to confirm.
- **MTG-10-04** Translated captions. Batch 8; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-10-05** Language interpretation. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-10-06** Caption font/type/size customization. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-10-07** Caption position settings. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-10-08** Keyboard navigation/shortcuts. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-10-09** Screen-reader support. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-10-10** Accessible meeting controls. Batch 8; Not established in focused call-module audit; Core candidate / scope to confirm.

### 11. Meeting apps and integrations

- **MTG-11-01** Open Zoom Apps inside meeting. Batch 9; Not established in focused call-module audit; Vendor-specific integration or Aedrova equivalent decision.
- **MTG-11-02** Supported third-party apps. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-11-03** Collaborate through integrated tools. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-11-04** Open collaborative documents. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-11-05** Whiteboards. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-11-06** Scheduling/productivity integrations. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-11-07** Share supported app content. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-11-08** Notice when apps are active. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.

### 12. Streaming and broadcast

- **MTG-12-01** Stream to supported platforms. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-12-02** Custom RTMP. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-12-03** Broadcast presentations externally. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-12-04** Broadcast audio. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-12-05** Webinar Q&A. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.

### 13. Layout and personal settings

- **MTG-13-01** Gallery/speaker switching. Batch 9; Related source path exists; completeness unproven; Advanced / feasibility review.
- **MTG-13-02** Change display names. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-13-03** Backgrounds/effects. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-13-04** Toolbar placement. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-13-05** Meeting theme. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-13-06** Chat previews. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-13-07** Keep controls visible. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-13-08** Accessibility settings. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-13-09** Screen-sharing behavior. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-13-10** Audio/video preferences. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-13-11** Supported display layouts. Batch 9; Not established in focused call-module audit; Advanced / feasibility review.

### 14. Joining/leaving/call management

- **MTG-14-01** Invite participants. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-14-02** Copy invitation. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-14-03** Meeting ID/join information. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-14-04** Computer audio. Batch 7; Related source path exists; completeness unproven; Core candidate / scope to confirm.
- **MTG-14-05** Telephone audio. Batch 7; Not established in focused call-module audit; Advanced / feasibility review.
- **MTG-14-06** Leave meeting. Batch 7; Related source path exists; completeness unproven; Core candidate / scope to confirm.
- **MTG-14-07** Host end for everyone. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-14-08** Transfer to Zoom Room. Batch 7; Not established in focused call-module audit; Vendor-specific integration or Aedrova equivalent decision.
- **MTG-14-09** Invited participants not yet joined. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.
- **MTG-14-10** Reclaim host privileges. Batch 7; Not established in focused call-module audit; Core candidate / scope to confirm.

## Staging-to-main decision

Promote core fixes only after Steps 2–8 relevant release gates pass, all advertised connectors are certified or explicitly withheld from release, and the first-release meeting scope is agreed. Step 9 advanced capabilities can ship in later reviewed increments; no unsupported capability should appear as available. Record exact app/backend revisions, migrations, OAuth callback/environment differences, provider grants, feature flags, limits and rollback. Do not copy staging credentials to production. Production smoke and backend entitlements must pass before download or billing activation. Apple membership alone does not close these gates.

## Consolidated owner actions — all deferred to the handoff

**Required now for Step 1: none.** The inventory can be completed without signing in, entering keys, running SQL, paying or authorizing accounts. No new request is pending during baseline work.

Later actions are conditional, not instructions to perform them now:

- **Step 2 approval:** authorize the next implementation batch. If real staging inference needs credential deployment, present the prepared exact service/key purpose and capped spending configuration for approval at that point; never paste secrets in chat. Without it, capped hosted inference acceptance remains blocked.
- **Live account checks, Steps 4/6:** when prepared, use the named staging test account on the exact fresh login screen; complete password/2FA/consent personally if required. The expired prior second-account handoff is not a successful isolation check. TikTok attempts must be allowed to recover; do not repeatedly retry or guess a reset interval.
- **Provider launch gates, Step 6:** complete provider-required verification/review or consent when automation cannot. Stripe developer verification, social public approval and unverified catalog lifecycle tests remain open. Customer account verification alone cannot clear developer-app review.
- **Reliable meeting hosting, Step 7:** approve an exact hosting/provider option only after current requirements/costs are rechecked. Prior paid staging/guard upgrade was deferred; no new charge is authorized by this inventory.
- **Promotion/release:** confirm actual legal operator when determined (placeholder remains), finish deferred Stripe bank/billing launch setup, confirm active Apple membership and required signing access, and perform unavoidable physical-device/clean-machine tests. Exact steps and blocked gate will be supplied together when the release candidate is ready; nothing is requested now.

The independent Cloudflare outage Worker was already created by the owner but remains starter/unrouted in the last evidence. Complete it in its own authorized delivery batch; do not ask the owner to create it again. Public waitlist/billing/download mode stays unchanged.

## Documentation validation

- 205 unique requirement IDs, including 182 meeting items across all 14 requested categories.
- All nine advertised connector entries retained; Linear excluded.
- Source versus live status separate; historical tests are labeled and no fresh runtime test is claimed.
- This snapshot supersedes stale setup handoffs for current planning; historical milestone evidence is preserved.
