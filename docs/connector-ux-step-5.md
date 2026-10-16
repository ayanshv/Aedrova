# Repair roadmap Step 5 — single-action connector setup

October 15, 2026. Owner approved Step 5. Desktop source implementation; live
provider certification is the separate Step 6 gate.

## Customer workflow

Disconnected provider detail has one connection action: **Connect your account**.
The provider icon, permission description and grant-policy text explain the action.
Token inputs, manual resource IDs, the advanced-token toggle, duration controls
and the global Refresh button are absent from that screen. Back navigation remains
available. This also applies to the gallery embedded in Bud configuration.

The existing OAuth API opens the fixed Aedrova service authorization URL. Login
and provider consent remain with the provider. Where the API requires a resource
choice, it appears only after authorization: named repository/project/page choices,
or a Figma file link when discovery is not supported. No developer code, secret or
internal resource ID is requested in this customer flow. Web search is honestly
labeled **Enable web search**, not a fictional third-party login; it asks for a
research topic after enablement.

Unavailable sign-in stays disabled with a clear service-setup explanation. It does
not offer a token workaround or pretend provider registration/review is complete.
Connected detail has one **Manage access** action leading to a separate resource
and Disconnect view. Management remains reachable when new sign-in is unavailable.
Disconnect removes Aedrova's saved access; the copy also explains provider-side
revocation without falsely claiming it always happened automatically.

The existing default 24-hour grant lifetime is unchanged and stated in text.
Provider expiry, refresh and revocation protections still apply. Removing a menu
does not silently extend permissions, make grants permanent, or give a Bud full
account access. No Terms/Privacy claim was changed to suggest otherwise. Future
grant-lifecycle improvements require the separate certification review.

## State and verification

While authorization is pending, the action checks its status instead of starting
duplicate grants. Opening another provider, changing Bud, returning to the gallery
or closing invalidates the old local attempt; a late start response cannot open a
browser for the wrong target. Empty resource discovery exposes only reconnect;
valid discovery has one continuation action. Reconnect starts a fresh local flow.
This does not claim that stopping local polling revokes an already-approved grant.

Connection success requires refreshed Bud data containing a Connected grant for
the matching provider. Callback completion by itself cannot render the branded
success screen. Existing configured Bud artwork and provider-specific copy remain.
Loading retains the existing skeletons; browser-wait instructions stay beside the
action instead of becoming a bottom-left loading notice. Dark-mode content surfaces
were corrected and light/dark/compact entry, unavailable and management states
visually inspected in ignored work/connector-step-5.

Legacy scoped-token verification handlers and backend endpoints are retained for
compatibility/internal diagnostics, with state holders outside the customer page.
No normal customer control exposes them. Backend logic, scopes, schema, API
contracts, routing, authentication and account credentials were not changed.

## Tests and limits

Desktop suite: 857 passed before the last visual/management refinements. Final
focused connector/Bud/loading suite: 77 passed after those refinements.
Coverage includes one entry action/no visible inputs, unavailable providers,
matching verified grants, stale authorization replies, duplicate-click handling,
empty discovery, managed search, expiry, URL validation, embedded draft save,
recovery, disconnect and existing token-path compatibility. Ruff/diff checks pass.

Tests use controlled provider transports. This batch does not newly certify real
login, provider review, refresh, revocation or discovery across the nine advertised
connectors. Those remain Step 6; prior live Instagram/TikTok evidence and provider
blockers are not overwritten by UI tests. No external OAuth grant, new key, SQL,
Render deployment, production promotion or installer build occurred here.

## Final owner actions

None required for this source/UI batch. Do not create keys or repeat old setup
steps now. Approve Step 6 to begin the live connector certification pass; any
unavoidable provider login, verification or consent handoffs will be consolidated
with exact instructions. Production promotion remains Step 10 after release gates.
