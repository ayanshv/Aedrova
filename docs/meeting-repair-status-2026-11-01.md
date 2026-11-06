# Meeting repair status, November 1, 2026

Live meetings remain blocked; do not mark acceptance complete.

## Local repairs

- Prepare fresh authenticated meeting access in the interactive request worker,
  rather than running potentially refreshing authentication on the UI thread.
  Duplicate clicks coalesce. Changed user, service, workspace or channel discards
  the result; disconnect clears pending preparation.
- Connect RTC before optional transcript capability discovery. That discovery
  fails closed and has a bounded HTTP timeout; it cannot stall the media pump.
  Mandatory room authorization and access-monitoring heartbeat remain enforced.
- Failed joins expose Try again. Retry waits for the old worker to finish, closes
  its device controller, and creates a fresh authenticated call/worker. Devices
  are not reused after closure. Leaving during connection is ordinary cancellation
  and still runs cleanup.

Changes are local source, not a hosted deployment. Command-Q and reopen
`work/staging/Open Latest Aedrova Staging.command` to load them.

## Hosted evidence

Read-only inspection confirmed aedrova-beta-staging is still a Free Render service:
https://dashboard.render.com/web/srv-db58sn8473hc73a9n3qg/compute

Initial health probes timed out; after waking, /health returned 200 and
/health/meetings returned 503 with {"status":"unavailable"}. The latter is the
live blocker. The saved private staging environment has meetings disabled; this
saved copy alone does not establish current live environment values. No settings,
secrets, plans, payments or security guards were changed.

## Deferred owner actions and engineering follow-up

Payments remain the final launch gates, per the owner's instruction. When ready:

1. Render > aedrova-beta-staging > Compute: personally choose/save an always-on
   plan after reviewing its current price. No purchase has been made.
2. Create/deploy the independent staging meeting guard from
   `/Users/ayanshvarma/Documents/Aedrova_site/deploy/render-beta-meeting-guard.yaml`.
   Any billable deployment must be submitted by the owner.
3. Complete the missing private staging LiveKit configuration in Render's private
   Environment settings, using the approved private credential workflow, never
   secrets in chat. Verify guard connectivity and matching database/provider scope.
4. Engineering deploys the matching candidate, enables meetings only with a healthy
   independent guard, and verifies /health/meetings returns 200. Flipping the flag
   alone or bypassing monitoring is not a fix.
5. Run a real two-account, two-physical-device audio/video/screenshare and leave/
   reconnect check. Participants must grant OS device permissions and assess actual
   audio/video quality. Automated tests cannot establish this acceptance.

See docs/meeting-launch-gates.md for the full safety and advertised-feature gates.
Stage 2 remains open for the remaining owner-directed fixes and combined live
light/dark review; reliable meetings cannot be called complete before these steps.

## Validation

135 meeting/access/device/communication/transcription/wrap-up/presentation checks
passed headlessly, including new blocked-capability/nonblocking-media,
failed-join retry, and stale session-preparation coverage. Ruff and whitespace
checks passed. Evidence: work/meeting-repair-nov1/acceptance.log. Real network media
and physical devices have not passed while hosted meeting health is unavailable.
