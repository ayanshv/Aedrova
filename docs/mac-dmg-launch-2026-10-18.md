# Mac DMG launch focus — October 18, 2026

Owner prioritizes the existing product's Mac DMG launch. The proposed agency
pivot and 34-change product roadmap are not authorized implementation scope.
Windows is outside this immediate packaging checkpoint. Existing launch gates
remain authoritative; this focus is not permission to mark them passed.

## Current artifact

- Source: `9dfb7c0`; adaptive macOS icon and desktop hardening included.
- Local installer: `work/Aedrova-preview.dmg`, **internal staging preview only**.
- Version 0.1.0, Apple silicon/arm64, macOS 14+, 322,330,142 bytes.
- SHA-256: `40270266eafc7f9998523873b221560e659fd0cc939b904fe9ac4565a040a4fa`.
- Adjacent manifest explicitly declares `public_release: false`.
- Explicit staging Supabase/managed AI/connector origins verified inside the
  frozen bundle. Included-AI mode selected; no local fallback configured.
- Baseline tracked/runtime/resource secret scan passed. This is a pattern check,
  not a complete security audit.
- Disk-image CRC/integrity and SHA-256 manifest checks passed.
- Read-only mounted app deep/strict signature verification, Applications symlink
  and native icon catalog checks passed. Image detached after verification.
- Frozen app light-mode chat and dark-mode account startup smoke passed and
  screenshots inspected. These use local sample/unsigned-in state; they do not
  certify real login, AI replies, connector grants, calls or fresh-Mac installation.

Local detailed evidence: `work/staging/dmg-acceptance.json`, smoke JSON/PNGs,
test XML and private packaging logs. Artifacts and credentials are not committed.

Initial desktop validation passed 889 tests; revised source passed 890, followed by
10 focused cache/tooltip/voice tests after the last small fixes. Rebuilt this DMG
with desktop caching/tooltips. Repeated integrity, digest, mounted signature,
Applications link, native icon, staging endpoint and frozen account startup checks
passed (`work/staging/hardening-dmg-acceptance.json`). The separate server hardening
still requires hosted staging acceptance; bundling a client does not deploy a server.
See the website repository's docs/launch-hardening-2026-10-18.md.

## Immediate signing dependency

Only Apple Development identity found locally. No Developer ID Application
identity is installed, and public notarization was not attempted. No payment,
production change, public download or checkout activation performed.

Owner steps:

1. Apple Developer → Account: verify membership is **Active**. If still pending,
   resolve activation with Apple; do not buy another membership automatically.
2. With the active team selected, Xcode → Settings → Accounts → Apple Account →
   team → Manage Certificates → + → **Developer ID Application**. If unavailable,
   use Apple Developer → Certificates, Identifiers & Profiles → Certificates and
   Apple's CSR workflow on this Mac. Keep the private key in the login Keychain.
   An Apple Development or Developer ID Installer certificate is not a substitute.
3. Locally run `xcrun notarytool store-credentials aedrova-notary` and complete
   Apple ID, team ID and app-specific-password prompts privately. Never paste
   credentials in chat. This stores the notary profile in Keychain.

After signing access exists: build the approved production-configured candidate,
notarize/staple/assess both app and DMG, then perform clean-Mac install, login,
core workflow, permissions and update/uninstall acceptance. Do not relabel the
staging preview as the production installer. The website download gate stays off
until the applicable product, business and release acceptance gates are passed.

References: [Developer ID certificates](https://developer.apple.com/help/account/certificates/create-developer-id-certificates/),
[notarization workflow](https://developer.apple.com/documentation/security/customizing-the-notarization-workflow).

## October 19 internal preview refresh

Rebuilt from source `3a1cfc2` with the GitHub confirmation, immediate local Bud
setup, connector poll recovery and component-only tour highlight fixes. This replaces
the earlier internal preview; it is **ad-hoc signed for internal staging**, not a
Developer ID/notarized production release. Staging public endpoints and included-AI
configuration matched the isolated public profile inside the frozen bundle.

- `work/Aedrova-preview.dmg`: 322,331,591 bytes.
- SHA-256 `8b8a350280740745fe89812709c537e5b3a884ff4a40cf7acbb8bb4fc5b9a762`.
- Manifest `public_release: false`; checksum, image CRC, deep/strict app signature,
  frozen account startup and screenshot capture passed.
- Full desktop suite: 896 passed; 22 follow-up GitHub/tour checks passed after final
  confirmation spacing/tint adjustments. Release secret-pattern scan and Ruff passed.
- Evidence: ignored `work/ui-recovery-oct19/acceptance.json`, screenshots and private
  build logs. UI confirmation/tour captures use preview fixtures, not provider consent.
- Mounted new image at `/Volumes/Aedrova 1`; mounted app strict verification passed.
  Older `/Volumes/Aedrova` could not unmount because it is busy. No forced unmount or
  user-app termination performed. Owner should quit the old app, then open the app
  from `/Volumes/Aedrova 1/Aedrova.app` to see these changes. Existing installed apps
  do not update merely because source or a DMG was rebuilt.

## October 20 internal connector-copy refresh

Rebuilt source 31d5d2a after Bud-specific timeout recovery copy fix (35 focused tests).
Internal staging DMG is 322,333,062 bytes, SHA256
977c7ed7c2d2acc74a8b87763f37904d0dc32f6d461afa3d1954fe159d033458.
public_release=false; image CRC and deep/strict app signature passed. Frozen light
preview startup smoke passed with 4 tabs and 5 sample messages; no network services
connected in this fixture. New image was not mounted over the owner's running app;
existing older mounted volumes were not forcefully detached. Signing/clean-machine
release gates above remain open. This is not a commercial download.

## October 20 upload responsiveness refresh

Latest internal staging preview replaces earlier images: source 0ca84dc,
321,728,790 bytes, SHA256
6243382a01c894e71a34acb72f07ddcfcc72b9ed48fa6bc7ddc0ac2d1cee5c29.
Includes isolated bounded upload workers, multi-file picker, real byte progress,
responsive cancellation and compact/auto-clearing completion feedback. Full suite
905 passed; final UI-destruction guard followed by 27 focused passing tests. Real
warm staging 256 KiB upload/verification/private-download integrity passed, 5.57s
including session preparation and download. Synthetic message cleaned by unsend.

CRC/digest, mounted deep/strict signature, staging-origin equality and packaged
preview startup passed. public_release=false; ad-hoc internal only. Mounted as
/Volumes/Aedrova Upload Preview. Owner must quit the old running Aedrova, then
open that volume's Aedrova.app to use the new client. Old running volume was not
force-unmounted, and no automatic production update/public download was enabled.
