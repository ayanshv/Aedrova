# Apple setup and on-device meeting notes

Owner authorized Apple setup on November 5, then requested on-device notes for existing Zoom, Meet and Teams calls before publishing the DMG. Stage 4 production operations was approved and is temporarily paused for these priorities. No payment or public download activation is authorized by this document.

## Apple progress

- Active developer team verified in Apple's portal: J64LC76P77. Its account holder/signing identity is Sonal Verma. This does not establish Aedrova's legal operator or incorporation.
- Developer ID Application certificate issued and imported with its matching private key into this Mac's login Keychain. `security find-identity -v -p codesigning` recognizes it as valid. Existing development identity was retained.
- Primary App ID `com.aedrova.desktop` registered with Sign in with Apple.
- Desktop and website Apple OAuth entry points implemented behind `AEDROVA_APPLE_LOGIN_ENABLED=false` by default. Existing Google login remains. Both use the existing PKCE, callback, session and workspace-authorization paths. No Apple private key is packaged in the app or frontend.
- Website `scripts/apple_client_secret.py` generates a P-256/ES256 secret valid for 179 days into an exclusive mode-0600 file; never stdout. Rotation deadline is 30 days before expiry. The private signing key stays outside Git and frontend assets.

## Apple completion sequence

1. Register separate Services IDs for staging and production, associated with the primary App ID. Proposed IDs: `com.aedrova.login.staging` and `com.aedrova.login` (availability must be verified).
2. Register staging domain `scvmvqlzcqhwrrsiahpj.supabase.co` and return URL `https://scvmvqlzcqhwrrsiahpj.supabase.co/auth/v1/callback`. Production uses `cpelagtufyocepnqcqqd.supabase.co` and its matching `/auth/v1/callback`. Do not use a desktop loopback URL as Apple's return URL: Supabase handles Apple's callback, then redirects the PKCE code to Aedrova's existing allowlisted callback.
3. Create a Sign in with Apple key, store its one-time .p8 download privately, and generate the environment-specific client secrets locally. Register the Services ID first in each Supabase project's Apple Client IDs. Configure staging first; require actual success/cancellation/returning-user/Hide My Email acceptance before enabling production.
4. Verify name onboarding when Apple provides no name, stable identity and workspace access, and account-linking behavior. Never merge accounts just because names match. Hide My Email may result in a different account; explain this before reusing an existing workspace.
5. If sending to private-relay addresses, register the actual sending domain/source and confirm authenticated mail delivery. Do not register an invented email provider or claim mailbox acceptance from local fixtures.
6. Owner saves an app-specific password to local notarytool profile `Aedrova-Notary` using the prepared private setup command. No password belongs in chat, code or GitHub logs. Alternatively use an appropriately scoped approved App Store Connect API key; do not mix it with the Sign in with Apple key.
7. Freeze and review the source/configuration candidate, build with `AEDROVA_SIGNING_IDENTITY='Developer ID Application: Sonal Verma (J64LC76P77)'`, included AI mode and explicit intended endpoints. Compile and sign the local audio helper and all nested dependencies, verify hardened runtime and usage descriptions. No blanket signature/validation bypasses.
8. Run existing `scripts/build_dmg.py --notary-profile Aedrova-Notary`: submit app, require Accepted, staple, verify Gatekeeper; create/sign/notarize/staple/assess DMG. Preserve submission IDs, logs and SHA-256 manifest. A code-signing certificate alone is not notarization.
9. Test fresh-Mac download/quarantine, drag-to-Applications, first launch, Apple/Google login, microphone/system-audio consent, update and uninstall. Check architecture coverage. Publish only after release go/no-go; notarization alone does not certify backend or commercial readiness.

Apple references: [Developer ID](https://developer.apple.com/help/account/certificates/create-developer-id-certificates), [web sign-in](https://developer.apple.com/help/account/capabilities/configure-sign-in-with-apple-for-the-web/), [Supabase Apple setup](https://supabase.com/docs/guides/auth/social-sign-in/auth-apple), [notarization](https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution).

## Local meeting design

Users keep their calls in their existing meeting software. Aedrova never joins or hosts that external call. A tiny Apple ScreenCaptureKit/AVAudioEngine bridge captures computer audio and the microphone after explicit Start and participant-consent acknowledgement. All product orchestration, transcription, review and sharing remain Python. No screen video is stored. Other applications' sounds can be captured, so the UI discloses this and users should stop private audio first. Headphones reduce acoustic duplicates.

Core Audio microphone activity can suggest notes for supported native apps/browsers on macOS 14.2+. App-open fallback is explicitly described as an app being open, not proof of a meeting. Suggestions can be disabled in call options. Detection reads process/audio activity metadata, never captures audio, and never automatically starts recording. Muted calls and some browser/helper processes may not be detected; manual Start remains available. Automatic meeting-end inference is not certified; Finish is explicit.

Whisper base (multilingual), converted by Systran and pinned to `ebe41f70d5b6dfa9166e2c581c45c9c0cfc57b66`, runs locally through faster-whisper/CTranslate2. Explicit first-use model download is about 148 MB. File sizes and SHA-256 values are pinned and verified. Audio inference uses a local path and local-files-only mode; there is no paid speech fallback. Short speech, overlap and names can be inaccurate. Computer audio is not attributed to individual people.

Capture uses private temporary audio chunks, a bounded eight-item queue, two-hour session limit and transcript byte limit. A slow machine stops capture rather than silently dropping an unbounded queue. Normal completion deletes each processed audio chunk and the temporary directory; closing the review discards its in-memory draft and stops capture. Forced OS termination/crashes can leave temporary files, so this is not a secure-erasure guarantee. A retention/recovery cleanup review remains before release.

The visible side capsule has soft shadow, neutral theme surfaces, Aedrova mark, actual audio-level waveform and stop/open controls. Preparing/audio-permission/finishing states use the same capsule; Apple's mandatory OS permission dialogs remain system controlled. No recording indication is shown as actual listening before the helper signals Ready.

After Finish, users edit draft notes and transcript. Draft notes extract verbatim candidate lines; they are not an API-generated summary or verified decisions. Only Confirm shares the chosen reviewed text to the captured channel through the existing private, verified attachment pipeline. Membership, channel permissions, upload verification and existing withdrawal/deletion controls apply. Raw audio is never uploaded. Existing agent context retrieval reads this permitted text alongside workspace evidence and announces reviewed meeting notes during Thinking. No automatic model call or build is triggered by recording or Confirm.

This removes the need for Aedrova-hosted meeting rooms/guard and speech-provider billing for this workflow. It does not eliminate normal application/database hosting, storage or metered agent reasoning. Existing hosted calls remain separately gated; this addition does not certify them. Windows computer-audio capture needs a separate WASAPI implementation and device acceptance; do not advertise this Mac bridge as Windows meeting support.

## Verification and remaining gates

- Existing OAuth/account focused checks: 28 desktop and 91 website/auth/secret checks passed before the audio work.
- Swift helper compiled successfully on this Apple-silicon Mac; no device capture was initiated by compilation or detection-only checks.
- Pinned model installed and hash verified. A public JFK speech sample transcribed successfully with all socket connections blocked (about 10 seconds including model load for an 11-second sample). This is offline inference evidence, not a real-call capture test or universal latency guarantee.
- Focused meeting consent, path/size/symlink validation, chronological transcript, extractive notes, review-before-share, scope-change denial and existing meeting-context/device regressions passed. Latest combined test/visual evidence must be recorded after the side capsule changes.
- Still required: physical microphone plus computer-audio capture, permission denial/retry and stop cleanup, real external call/headphones/mute behavior, final light/dark capsule review, actual staged confirmed upload and agent retrieval with a second-account denial check. Do not claim the feature launch-ready until these pass.
- Apple Services IDs/signing key/Supabase setup, owner notary credential, actual notarization and clean-machine acceptance remain open.

## November 6 execution update

- Both Services IDs are registered and their exact Supabase callbacks saved: `com.aedrova.login.staging` and `com.aedrova.login`. The Apple portal session expired overnight; a fresh owner sign-in resolved the rejected saves.
- Sign in with Apple key `MTGXKB796S` is created, scoped only to primary Aedrova. Its .p8 is private outside both repositories. Generated 179-day secrets were saved in each project's provider settings. Staging Apple authentication is enabled. Production credentials are prepared but its provider stays disabled pending the actual staged biometric sign-in.
- Native Apple login reaches the real macOS account/Touch ID consent sheet for Aedrova. No biometric authentication or personal account consent was bypassed. Cancellation returns both login buttons to an enabled state. The owner must complete a fresh Apple sign-in personally to certify the callback/session/workspace path. Do not reuse the expired acceptance link.
- Google is above Apple in a vertical, equal-width hierarchy; Apple uses its logo and native system typography. Both entry points remain separated from subscriptions and charging.
- Owner completed the private notarytool credential setup and local signing-key unlock. Both validate successfully. The full staging candidate and nested helper signed successfully with Developer ID and hardened runtime.
- App notarization submission `e63248f1-1160-4919-8059-ce5ec8a90c72` is in Apple's queue. The running DMG workflow waits for Accepted before stapling, then creates, signs, submits and assesses the DMG. No installer has been published or represented as notarized yet.
- A bounded, approved 20-second physical capture passed: both computer and microphone sources produced local transcript text, including the public sample. The draft was discarded without sharing. No matching temporary audio directories remained after cleanup. On-device sample inference also passed with sockets blocked.
- Full native candidate before the final header/checkbox refinements: 1,168 passed. Focused follow-up checks cover the new header routing, consent/review/share boundary, account and OAuth paths. Swift bridge compilation, source lint and secret-pattern checks pass. Native call icons now lead with meeting notes; optional hosted calls live under meeting options.
- Checkbox styling now uses a rounded blue square and a white check in native QCheckBox and website checkbox inputs. Keyboard focus and disabled states remain explicit. The design is a UI change, not a consent-default change.
- Production Render compute is verified at 0.5 CPU / 512 MB. Its Blueprint's obsolete explicit Free plan was removed; Render preserves an existing service's selected plan when this field is omitted. No plan purchase/change was submitted.
- Production health/readiness respond successfully, but checkout and managed AI remain false. Render's environment inventory has no managed OpenAI/Anthropic key or model configuration. Actual application launch remains gated on reviewed production migrations, approved provider configuration/allowances, recovery/operations and final installation acceptance. Do not switch off waitlist protections merely because the host is paid.

### Consolidated owner actions after returning

Required for Apple acceptance: open the newest staging login, click Sign in with Apple, choose the intended email-sharing preference, and complete Touch ID or Apple's password/2FA privately. Sharing the email used by the existing workspace can avoid unintentionally creating a separate relay-email identity; do not merge accounts based on display names.

Before public application launch: approve the concrete production provider credential/configuration transfer once its reviewed package is presented; complete any required personal operator/identity disclosures; provide final real-device/clean-machine acceptance. Existing paid production hosting and notary credentials are already completed and must not be requested again. Purchases remain owner-only. Apple's pending notarization decision is external and cannot be replaced by local signature verification.
