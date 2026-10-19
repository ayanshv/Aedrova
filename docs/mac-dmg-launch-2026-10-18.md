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
