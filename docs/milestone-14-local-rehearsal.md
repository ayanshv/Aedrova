# M14A — local installation and update rehearsal

October 3, 2026. Owner authorized finishing the remaining local rehearsal. Production
account/payment setup remains deferred. This report does not declare all of M14 complete.

## Delivered

`scripts/rehearse_installation.py` verifies the actual preview DMG digest/size, disk image
integrity, Applications link, bundle version and code signature. It mounts read-only and
uses a disposable Applications directory to install, replace and roll back the packaged
app. Each launch uses demo data and an explicit isolated settings file. Both themes launch;
preferences and a synthetic user-owned project are checked after every replacement.
The mounted image is detached and disposable installation files are removed on exit.
Evidence is saved under `work/m14-installation/`.

The current updater rejects preview installers and remains an explicit download handoff.
Loopback HTTP acceptance checks cover a compatible newer release fixture, unavailable
service, malformed JSON, oversized metadata, preview/unsupported releases and redirects
to another origin. Invalid metadata field types now produce readable validation errors
instead of uncaught type errors. No real public release metadata is fabricated or enabled.

## Scope and limitations

This uses two copies of the same 0.1.0 preview, so it validates replacement/rollback
mechanics and retained isolated preferences/files, not a released old-to-new migration.
HTTP newer-version checks use labeled fixtures. Real Supabase account persistence and
fresh-Mac installation are not claimed by a demo launch.

The signature is Apple Development, not Developer ID. Public notarization, Gatekeeper
acceptance on a fresh Mac, live Stripe/provider access, hosted concurrency/backup restore,
and physical two-Mac meeting/transcription/consent acceptance remain M14B/C gates.
No live capability flags, hosted migrations, credentials, purchases, push or public
deployment are changed by this task. The website remains a waitlist.

## Verification

- 503 desktop tests, including actual loopback HTTP update acceptance/failure checks.
- 247 website/backend tests; one existing Starlette/httpx deprecation warning.
- All 25 desktop migration/RLS SQL files in embedded PostgreSQL, plus the private
  website ledger/meeting schema and atomic lease checks. These are local database checks.
- Scoped Ruff and whitespace checks; packaged source/resource credential scan.
- Signed preview packaging, DMG creation, and isolated installed/replacement/rollback
  launches. Light/dark launch captures inspected. No public signing acceptance claimed.

Logs: desktop `work/m14-desktop-tests-final.log`, `work/m14-database.log`,
`work/m14-package.log`, `work/m14-dmg-final.log`, `work/m14-installation-final.log`;
website `work/m14-website-tests.log` and `work/m14-ledger.log`.

## Repeat the local rehearsal

From the desktop repository, after packaging the signed preview:

```sh
uv run python scripts/build_dmg.py --preview
uv run python scripts/rehearse_installation.py
```

Do not use this preview DMG as the public download. Follow `app-updates.md` for real
version bumps, Developer ID/notarization, versioned release hosting and explicit user updates.

## Owner actions

No owner action is required for the local rehearsal. Reopen the rebuilt preview to use
the update-validation fix. When owner setup becomes available, M14B provides the guided
Apple Developer ID, Render paid hosting and live Stripe walkthrough. Configure server-only
provider credentials privately; complete Supabase migrations and arrange a second Mac/tester
for M14C. Each dashboard/file step must be supplied when ready; never paste secrets in chat.

If the announcement migration is still unapplied, run the contents of
`supabase/migrations/202610030004_meeting_activity.sql` in Supabase → SQL Editor, then
reopen Aedrova. This unlocks shared meeting announcement settings and participant activity;
it does not complete hosted meeting acceptance.

Obtain permission before M14B/C or another implementation milestone. Independent M15
product-memory work can be proposed while production prerequisites remain unavailable,
but doing so does not waive M14 acceptance or enable public release.
