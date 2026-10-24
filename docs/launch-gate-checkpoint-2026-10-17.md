# Launch-gate checkpoint — October 17, 2026

Status: **OPEN; not release approval.** Complete and test all preproduction gates
before requesting Step 10. Payment remains excluded from agent authorization.

## Verified this checkpoint

- Desktop candidate `3a9b698`: macOS, Windows, Linux and PostgreSQL CI green
  ([run 38998004293](https://github.com/ayanshv/Aedrova/actions/runs/38998004293)).
- Fixed asynchronous Bud test transport/reply races and actual Linux compression
  of the required AI execution disclosure. Final focused checks passed.
- Backend `96d18562aea773ad2e312aa4074815c3581c8b3e` deployed to existing free
  staging; Render observed Live. Warm readiness 200; meetings 503 unavailable.
- Hosted two-account file/thread/private-channel isolation, canceled upload and
  signed-out media denial passed. Hosted Bud outsider/member/revoked-member
  privacy and retry idempotency passed. Synthetic fixtures archived/soft-removed.
- Native workspace creation requires explicit AI execution consent. Its dashboard
  action closed the creation popup. Remaining onboarding walkthrough unverified.

Evidence reports are local under `work/staging/`, ignored to avoid committing
authentication material. Bud privacy probe is maintained in `scripts/` and uses
ordinary staging OAuth, synthetic messages and no model/provider credentials.

## Owner actions, consolidated

1. **Native acceptance:** bring the Aedrova Staging source preview to the foreground
   and leave it visible for the remaining Bud setup → Finish later → highlight-tour
   check. The automation capture stream currently fails on macOS. If it remains
   unavailable, complete that walkthrough manually and report the exact failing
   screen. This blocks native onboarding acceptance, not the passing server checks.
2. **Meeting hosting, when affordable:** Render → aedrova-beta-staging → Compute:
   owner chooses/purchases always-on hosting; then provision the independent meeting
   guard described in meeting-launch-gates.md. Review current charges before saving;
   earlier estimate was $7/month per service, not a new price guarantee. Free sleeping
   hosting and absent guard block reliable meeting/transcription acceptance. Agent
   must not submit a payment or silently activate the meeting service.
3. **Apple:** Apple Developer → Account: confirm membership is Active. Reply
   “Apple membership active” only after activation. Developer ID Application signing
   identity is absent locally; activation, signing/notarization and Sign in with Apple
   remain unverified. Keep credentials/private keys out of chat.
4. **Physical release tests:** provide two signed-in devices/accounts with working
   microphones/cameras and a Windows clean-machine test target. Exercise consent,
   mute/video/share, listening, final-leave transcript review and withdrawal; then
   installation/update/uninstall of signed candidates. CI is not a substitute.
5. **Business and billing, before public activation:** finalize the actual legal
   operator (placeholder stays until confirmed), obtain qualified legal review and
   verify support mailbox/phone handling. Complete Stripe verification/bank setup
   privately at the agreed prelaunch checkpoint. Test real test-mode subscription
   lifecycle before enabling any paid downloads; no agent purchase is authorized.

These owner actions are dependencies, not a claim that completing them alone will
close every gate. Remaining implementation, connector certification, hosted alert/
backup/restore and concurrency evidence, provider approvals and independent
security review stay OPEN in the authoritative gate registers. Do not promote,
publish downloads, enable billing, or describe the product as launch-ready yet.
