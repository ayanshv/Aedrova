# Meetings audit, November 23, 2026

Scope: can a tester start and stay in a hosted meeting, and does Aedrova know a person is in one.
Code-level review plus tests. Hosted meetings are still switched off on the websites (see
"Turning meetings on").

## Fixed in source

1. **One missed beat ended a live call.** The call pinged the server every 8 seconds and any
   single failure (a slow or waking server, a brief network drop, a rate limit) ended the call.
   Presence lasts 60 seconds, so the call now rides out up to two missed beats and ends on the
   third. Refused access (401, 403, 404, 405) still ends the call at once.
2. **Long calls were dropped when the sign-in token ran out.** The call kept the one token it
   started with, so every request after it expired (about an hour, less if it was nearly spent)
   was refused. The call now refreshes the account token about three minutes before expiry and
   never adopts a token for a different account.

Tests: `tests/test_meeting_resilience.py`.

## Findings that are not code defects

- **Detection is Mac only.** Local meeting suggestions use the native audio helper. Windows and
  Linux never suggest notes, and macOS before 14.2 cannot see which app is using the microphone.
- **Detected apps:** Zoom, Teams, Webex, Google Meet in the front browser, and any browser using
  the microphone. FaceTime, Slack huddles, Discord and WhatsApp are not recognized.
- **Hosted presence:** a person counts as in a meeting while their last beat is under 60 seconds
  old. If the app crashes, they disappear after at most a minute; rejoining can be refused for up
  to 30 seconds while the old connection expires.
- **The helper must ship signed.** `aedrova-meeting-audio` is built by `scripts/package_desktop.py`
  into `Contents/Helpers`. Signing and notarization must cover it with the microphone and
  audio-capture entitlements, or detection and local notes fail silently.
- **Transcript context is still off by default.** It needs the meeting migration, the server flag
  and an app built with `AEDROVA_MEETING_CONTEXT_ENABLED=true`.

## Turning meetings on (owner actions)

Hosted meetings need all of these; none can be done from source alone.

1. **Always-on hosting and the independent guard** (`docs/meeting-launch-gates.md`, LG-MTG-02):
   two Render upgrades of about $7 a month each, submitted by you.
2. **LiveKit project values** set privately on the service: URL, API key, API secret of at least
   32 characters. Never paste them into chat.
3. **Service flags:** `AEDROVA_MEETINGS_ENABLED=true` on the service, and
   `AEDROVA_MEETING_CONTEXT_ENABLED=true` only after consent testing.
4. **Database:** the meeting migrations on the project testers use, including
   `202610030001_meeting_context.sql`.
5. **Check:** `/health/meetings` returns 200, then a two-device meeting with two accounts.
