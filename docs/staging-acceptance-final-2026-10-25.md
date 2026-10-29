# Staging acceptance — October 25, 2026

Status: **OPEN**. No production promotion, new hosting charge, card, provider funding,
subscription or auto-refill. Claude inference and reliable two-device meetings remain
deferred final gates. Public provider approval is not implied by sandbox success.

## Verified

- Live Free 1 / Pro 5 / Team 15 Bud limits. Two concurrent creates at the last slot
  produced exactly one winner for each plan. Overflow failed closed.
- Team→Pro and Team→Free preserved 15 saved Buds, blocked new creation, permitted
  editing existing Buds, and permitted creation after removal freed capacity.
  Synthetic entitlement transitions were restored. This does not certify Stripe events.
- Server-verified text, PNG and voice WAV byte-for-byte upload/download, cancellation
  after reservation and storage. Native final-candidate private-channel image preview
  stayed unsent until Send, then appeared in history; file verification returned 200.
- Native microphone capture: eight-second recording, Done→unsent preview, Play→Pause,
  playback position reached 0:08 / 0:08. Discard removed it. Ambient audio was never
  uploaded. Auditory distortion/clarity requires the owner's listening check.
- Notion: fresh renewal of the existing read-only Aedrova connector validation page,
  live read; induced access-token expiry→actual refresh→live read; metadata expiry
  became future. Revoking the fresh access token using Notion's official endpoint
  returned 200; subsequent Aedrova read denied. Induced Aedrova grant expiry also denied.
- Supabase: existing organization Projects Read renewal, selected staging project only;
  live project read; induced access-token expiry→actual refresh→read and future expiry;
  local disconnect→read denied. Disconnect explicitly reported provider_revoked=false.
- Prior acceptance retained: GitHub, Figma, Instagram, Vercel scoped reads/disconnects;
  TikTok sandbox profile/public videos; Stripe test Accounts/Balance; fresh onboarding;
  bounded actual OpenAI build→review→apply and non-replenishing Free activation.

Expiry was induced only on the fresh test grants' encrypted metadata. It did not
change provider credentials or pretend the provider's wall-clock expiry elapsed.
Notion external revocation is not evidence of global uninstall support for all
providers. Other providers' refresh/revocation edge cases remain covered by controlled
HTTP tests, not individually live-certified external revocation in this pass.

## Fixes and verification

1. Deterministic routing for an explicitly addressed Research Bud with a single
   authorized Search tool, including recovery from a transient Error state. Other
   ambiguous tools still use the bounded selector. Backend authorization remains fresh.
2. Strictly validate connection-specific `bud:<bud>:<connection>:<tool>` citations,
   alongside legacy `dot:` citations. Altered identities/tools and unknown citations
   remain rejected. This fixes valid account-based connector evidence being rejected.
3. Workspace-settings checkable navigation reacts to accessibility toggles, rather
   than relying only on mouse clicked signals.
4. Research requests explicitly ask for one search and a short sourced answer within
   unchanged token/tool/spending limits. Content-free server diagnostics record only
   outcome counts, booleans, failure phase and exception class, never topics, URLs,
   credentials, private content or account identifiers.
5. Corrected two acceptance test fixtures: use actual scrollable content for trackpad
   behavior, and assert all four new chat messages independently of initial-history
   loading. Neither change weakens chronological prompt/reply checks.

Backend full suite: **638 passed** after bounded-answer/structural diagnostic change;
**11 Research tests passed** after failure-phase diagnostics. Desktop full suite:
**990 passed** after citation and fixture repairs; **29 focused checks passed** after
final transient-error routing refinement. Ruff and diff checks passed on edited code.
Existing audioop/Starlette deprecations remain.

Backend staging commits: b0e4b71, then 6623ac5. Production unchanged. Desktop source
fixes are in the current checkout; open the source staging launcher, not an old DMG.

## Research live conversation

Earlier direct live search succeeded. The complete native conversation exposed
routing/citation failures and intermittent hosted result failures; it is not accepted
until a sourced answer is actually saved and reopens correctly. The disposable Free
workspace exhausted its monthly allowance. The owner explicitly approved temporary
existing Pro policy for this exact workspace, at most two further Research attempts,
then Free restoration, without resetting usage or company limits. No Stripe event or
new payment was made. A closed-run pending reservation was conservatively settled
at its reserved amount because provider usage was uncertain; no refund was invented.

Final native outcome: **PASS for one complete question→live Research→sourced reply→
saved history→reopening in light/dark appearance**. Owner-scoped RPC confirmed user
then assistant, saved HTTPS sources, and no persisted Thinking placeholder. No extra
multi-turn follow-up was started after the two-attempt permission was used. Metered
change during the resumed test was 140937 micro-USD ($0.140937), including conservative
uncertainty reconciliation, not a claimed exact OpenAI invoice amount.

Free was restored without resetting counters; reserved balance verified zero. The
Research managed connection was removed with an exact-fixture staging cleanup after
the helper's API disconnect failed to verify workspace access. Recoverable archival
succeeded. The synthetic image remains only within the archived disposable workspace;
its unsend cleanup did not verify. This is recorded rather than claimed deleted.
Original live-helper report retains its cleanup failure; final acceptance and cleanup
are separately recorded in research-live-acceptance.json and cleanup-confirmed.json.
An occasional provider/host failure was observed and manually retried, so this is not
an uninterrupted reliability certification.

## External review blockers and owner actions

Meta app 3077883259220045: instagram_business_basic has 20 calls and **Ready for
testing**, not public approval. The owner specifically approved Tech Provider
continuation; applied. Submission draft 3090636337944737 is accessible. Actual
business portfolio/access verification and App Review questions remain incomplete. The owner must provide actual operator
identity/business information privately. Do not invent a registered company or
silently replace the deferred business-registration decision.

TikTok app 7694803472533112852: Production remains **Draft**. Prepared description,
Productivity category, Desktop platform, homepage/Privacy/Terms URLs, actual 1024px
app icon and read-only use explanation. TikTok refuses Save without a genuine
end-to-end demo video. Fields remain unsaved except any uploaded temporary asset; the draft tab is preserved for review.
A real Login Kit / Display API profile-and-video demonstration, intended production
callback/scopes, final review of declarations, and provider submission/approval remain.
No production callback, permission expansion or final platform agreement was submitted.

Required listening check: latest Aedrova Staging→a real channel→microphone→record a
short non-sensitive sentence→Done→Play→Discard. Report whether clear or distorted.
This checks acoustic quality; the capture/preview/playback controls already passed.

References: [OpenAI web search](https://developers.openai.com/api/docs/guides/tools-web-search),
[Notion token revocation](https://developers.notion.com/reference/revoke-token).
Evidence: work/stage1-final-oct25 (ignored local artifacts, no committed secrets).

## Approved Meta continuation — latest checkpoint

Tech Provider continuation applied after explicit owner approval. Public Website
platform https://aedrova.com/ and Utility & productivity category saved. App Review
submission 3090636337944737 remains unsubmitted, with Submit disabled. No private
documents, new business account, new agreement or public release completed.

Required owner steps, consolidated:
1. Preserved Meta tab → Review → Verification: connect and verify the actual operator
   business portfolio; supply requested identity/business documents privately.
2. Meta → App settings → Basic → App icon: select
   branding/Aedrova.icon/Assets/Mark.png and review the upload certification. The
   selection was cancelled before certification; icon upload is not complete.
3. Meta → Review → App Review: complete accurate allowed-usage/data-handling
   answers and genuine reviewer instructions/demo access; review final declarations
   before submission. Verification/public review block public Instagram access.
4. Preserved TikTok Production draft: provide a genuine Login Kit / Display API
   profile/public-video demo (MP4/MOV ≤50 MB). Save currently rejects missing video.
   Review production callback/read-only scopes and declarations before submission.
5. Latest staging app → channel → microphone → record a non-sensitive sentence →
   Done → Play → Discard. Report clear/distorted; this completes human audio clarity.

Provider approval is external and cannot be guaranteed by preparing an application.
Screenshot: work/stage1-final-oct25/meta-review-current.png. Stage 1 remains OPEN;
independent security/recovery phase #2 has not been started. Claude funding and
reliable two-device meetings stay deferred final paid/setup gates.
