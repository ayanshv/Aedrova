# Repair roadmap Step 6 — live connector acceptance

October 15–16, 2026. **Core four accepted for scoped reads and local disconnect;
all-nine launch certification remains open.** Production and installers unchanged.

## Live results

Tested the real staging service using native Google PKCE and the named synthetic
workspace Beta isolation 1 eb8958 / TikTok staging audit Bud. Tokens stayed in
memory or encrypted on the server; reports contain no returned account contents.

- GitHub: real OAuth callback; discovery returned only installed ayanshv/Aedrova.
  Selection verified repository, commits, issues and deployments through actual
  provider reads. Local disconnect passed; subsequent repository read denied.
  Fresh OAuth/reselection then returned Connected; final cleanup disconnected it.
- Supabase: real OAuth callback with existing Aedrova organization Projects READ.
  Discovery listed projects, selected only Aedrova Staging. Actual project health/
  region read passed. Local disconnect passed; subsequent project read denied.
- Notion: real OAuth callback, discovery returned only Aedrova connector validation.
  Actual page/immediate-block read passed. Local disconnect passed; later read denied.
  Found shared OAuth app unnecessarily enabled user profiles/emails. Selected No
  user information, preserving Read content and disabled writes/comments. Reloaded
  provider consent now offers only View pages you select. Existing page selection
  retained; no personal parent page selected or content read. This is a reduction
  to the existing provider app's capabilities; no production server deployment.
- Figma: real OAuth callback and scoped design read passed for the existing Bud
  configuration prototype (Untitled). Local disconnect passed; later design read
  denied. A file link is still required after login because file discovery is not
  offered by this implementation. Attempt to create a disposable file hit Figma's
  free file limit; no upgrade, payment, creation or deletion performed.
- Instagram: fresh staging start and actual Instagram login page reached with
  instagram_business_basic. No signed-in session in the connected browser, so no
  fresh callback/profile/media read claimed. Historical Oct 14 reads remain prior
  evidence only; public review, renewal and revocation remain open.
- TikTok: fresh staging start and actual TikTok login page reached with
  user.info.basic/video.list and PKCE. No current signed-in sandbox test session;
  no fresh callback/profile/video read claimed. Did not retry the historical
  attempt-limit error or bypass it. Public review/lifecycle acceptance remains open.
- Stripe/Vercel/managed Search: authenticated live connection attempts rejected
  with accurate owner setup hints. Missing credentials/provider registration or
  Brave Search setup remain blockers. Stripe bank/business work stays deferred
  until release. No false connected status, new subscription or purchase.

Local disconnect deletes Aedrova's grant and blocks its tool reads; it does NOT
uninstall the provider app or revoke every provider-side token. Returned
provider_revoked=false is accurate. Global provider uninstall was not performed,
because it could disrupt existing non-staging grants. Forced live token expiry/
refresh and a fresh cross-account test were not performed in this batch; controlled
regressions cover token rotation, expiry, foreign-account denial and races.

## Fixes and validation

1. Web Google handoff omitted OpenID scope compared with working native sign-in.
   Added standard openid/email/profile scopes, retaining PKCE, cookies and identity
   checks. The product's subsequent browser sign-in returned to staging; fresh
   connector states reached actual providers. An earlier consumed state correctly
   rejected reuse. a55cf9d deployed Live as dep-db8s578n74is73cknu6g.
2. Notion app capabilities narrowed as described above; reloaded consent verified.
3. User cancellation showed generic Forbidden/account-permission instructions.
   Added branded cancellation recovery: no new access added, return to account.
   Failed state and proof-cookie deletion remain enforced. Invalid/replayed grants
   remain denied. Regression verifies cancellation cannot become Connected.
   Source 6a3cc90 is Live (Render deploy succeeded, 1m03s). Recovery is verified
   by controlled route regressions; reloading the earlier live cancellation URL
   still returned 403. Fresh valid live cancellation needs separate acceptance;
   stale/replayed proof remains denied.

Full backend suite **528 passed** after both code changes; focused 108 passed
before cancellation change; Ruff/diff passed. The local helper mistakenly sent
four GitHub tool calls where API allows at most three; server correctly rejected
that request. This was a test-harness error, not a product bug. GitHub's successful
selection had already verified all four tools on the server. No limits relaxed.

Four successful test grants were disconnected. Native test session signed out and
private authorization URL files removed. Abandoned pending states expire under
the existing ten-minute policy. No new credential, permission expansion, hosting
charge, production promotion or installer release. Docs/source pushed to GitHub.

Private ignored evidence: work/connector-step-6/live-batch.json,
notion-page-only.jpg, staging-deployed.jpg and final deployment screenshot.
OAuth status fields in helper report reflect the latest reconnect start, not the
older successful selection; selected_read_verification/read_tools and disconnect
fields record the completed reads. Notion/Supabase/Figma repeat-reconnect consent
was not completed a second time. Only GitHub reconnect was fully accepted live.

## Owner actions and next step

To finish social live acceptance, in Aedrova Staging → Buds → Marketing Bud →
Connectors, open Instagram → Connect your account, sign in as @aedrova_ai, and
leave the read-only consent screen open. Then do TikTok with the sandbox-approved
@aedrova account. Use fresh buttons, not expired authorization tabs; do not send
credentials in chat. If TikTok reports maximum attempts, stop and report it.
These account sessions block remaining social acceptance, not the completed four
core read/disconnect tests. Browser safety may require a specific new grant approval
if its recipient, scopes or lifetime differ from the existing test grant.

All-nine certification also needs Stripe/Vercel/Search setup, live renewal and
provider-revocation checks, public social/provider approvals and remaining isolated
account checks. Keep them as release gates; do not claim every connector is ready.

Next roadmap item is Step 7: meeting reliability and an agreed first-release call
scope. It has not started. Ask owner whether to proceed with these external
connector acceptance gates explicitly outstanding; public launch remains blocked.

Official Google scope reference used for the fix:
https://supabase.com/docs/guides/auth/social-login/auth-google
