# M11 — local onboarding and Mac distribution preparation

October 2, 2026. Owner approved M11 after Stripe sandbox checkout branding.

## Delivered locally

- Four optional setup screens: team/agent settings, appearance/accessibility, IDE/project/workflow/GitHub, and an invitation to explore.
- Seventeen guided-tour steps in five selectable chapters. Back/Next, keyboard navigation, Pause/Resume, Skip and replay from Help; progress is private to each account and tour version.
- Spotlights only visible, enabled controls. Navigation does not send messages, start builds, invite people, capture devices or make purchases. Existing project/provider permission settings remain authoritative.
- Light/dark layouts and compact/large windows verified. Reduced motion disables transitions; existing accessibility preferences persist.
- Help → Check for updates performs an explicit, read-only release check. Preview manifests, mismatched processors, unsupported macOS versions and malformed metadata are rejected. It opens the configured website for an available update; it never silently replaces the app.
- Internal preview DMG with drag-to-Applications link, version/processor/minimum-macOS metadata and SHA-256 manifest. Public packaging remains gated by Developer ID signing and notarization.
- Website installation/recovery guidance and gated release metadata/download endpoints. Files disappearing after startup produce an unavailable response.

## Verification

404 desktop tests and 135 website tests pass. Scoped Ruff and whitespace checks pass.
Both themes and tour chapter layouts were rendered and inspected. The graphics-effect
regression that hid tour controls was fixed with a restrained position transition.
Packaging, mounted app signature, disk-image integrity, drag-to-Applications link,
manifest checksum and packaged light/dark launch checks passed and are recorded in
`work/m11`; these are local checks, not fresh-Mac/public-distribution acceptance.
No additional Supabase SQL is required for M11.

## Owner actions needed before public release

Owner scheduling update, October 2: defer Apple Developer enrollment/certificate and
notarization credential setup until M13's final public installer gate. No Apple setup
is required to continue M12 locally. A purchased domain can be deferred until launch
or omitted; a stable hosting-provider HTTPS URL is sufficient for hosted integration
tests. Do not defer signing/notarization beyond publishing the public Mac installer.

1. As the Apple Developer Program team Account Holder, in Apple Developer → Certificates, Identifiers & Profiles, create a **Developer ID Application** certificate for the Mac that builds Aedrova, using a Certificate Signing Request from Keychain Access. Install the certificate with its private key in the login Keychain. An Apple Development certificate is insufficient for public distribution. This blocks the public installer, not the local preview.
2. In your local Terminal, run `xcrun notarytool store-credentials aedrova-notary` and follow its prompts for your Apple ID, team ID and app-specific password. Credentials stay in Keychain; never paste them in chat. This enables Apple's notarization service.
3. Choose a stable HTTPS hosting URL for the Python website/backend. A purchased domain is optional. Configure private Stripe/provider/database/session credentials on the server, Supabase Google OAuth redirect allowlists and the Stripe webhook URL for that environment. Complete the deferred commercial-provider and subscription acceptance before enabling paid AI. Localhost meeting credentials cannot support other people's Macs.
4. Configure the desktop's existing `AEDROVA_MANAGED_ORIGIN` to that HTTPS origin and the Developer ID signing identity via `AEDROVA_SIGNING_IDENTITY`. Do not include server credentials in desktop configuration. Run `uv run python scripts/package_desktop.py`, then `uv run python scripts/build_dmg.py --notary-profile aedrova-notary` from the desktop repository. The public script notarizes/staples/verifies both app and DMG; failure prevents public release.
5. On the website server, set `AEDROVA_DOWNLOAD_PATH` to the notarized DMG with its adjacent `.manifest.json`, and `AEDROVA_DOWNLOAD_SHA256` to its manifest digest. Enable `AEDROVA_RELEASE_READY=true` only after release acceptance. Keep checkout/provider gates separate; a downloadable app alone does not mean paid access is accepted.
6. Before launch, test the signed installer on a fresh Mac: install/open without bypassing Gatekeeper, Google sign-in, setup/tour, project/IDE/GitHub, local build, device permissions and updating while retaining user projects. The current build targets this Mac's processor and macOS 14+. Intel distribution needs its own build and acceptance; no universal build is claimed.

The owner previously reported no second Mac or hosting account. Fresh-Mac acceptance,
public hosting, Developer ID/notarization and live commercial access remain explicit
release gates. Nothing was pushed, deployed or published during this task.

## Next proposed work (permission required)

M12 reconciles the PRD and advertised features with implementation, then finishes
confirmed integration gaps. It includes deferred meetings: shared HTTPS service,
two-device physical-call validation, explicit transcription consent and scoped meeting
context for the agent. Other candidates are richer file/design/decision context and
end-to-end GitHub/provider acceptance. M13 remains the final safety/launch audit.

Reference: [Apple Developer ID distribution guidance](https://developer.apple.com/developer-id/).
Visual artifacts: `work/m11/tour-dark-0.png`, `work/m11/tour-light-12.png`,
`work/m11/setup-light.png`; website `work/stripe-check/m11-download.png`.
