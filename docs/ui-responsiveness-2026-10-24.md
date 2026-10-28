# UI delay audit and workspace settings refresh

October 24, 2026. Desktop source changes only; no hosted deployment, migration,
price/allowance change, payment, new provider grant or production activation.

## Changes delivered

- **DM +:** previously queued a full account snapshot before even constructing the
  recipient picker. It now opens directly from the current session/workspace snapshot,
  including configured Buds and local search. Opening requires no backend request or
  transport-queue completion. Actual DM creation and private Bud history still require
  server authorization. Normal dashboard sync refreshes the recipient directory.
- **Profile image:** a CSS radius on the button did not clip its QIcon. Photo rendering
  now center-crops and clips the actual image to a rounded square with transparent
  corners, preserving a 2x pixel density. The button is square rather than rectangular.
- **Channels +:** opens a dedicated name/privacy form immediately. It queues creation
  once, shows a pending state, and selects the real channel only after confirmation.
  Unknown outcomes offer Close and refresh, preserving the name and avoiding automatic
  duplicate creation. Logout invalidates the form; stale workspace callbacks cannot
  navigate a different account/workspace. Private creation is enabled in the UI only
  for cached owner/admin roles; current server authority remains decisive.
- **Workspace settings:** replaced the single long administration form with five
  sections: Your agent, Channels, People, Invitations and Account. Added native section
  visuals, clear headings and one primary action for the selected task. Secondary
  access controls are collapsed. Channel permission changes have their own channel
  selector. Invitation code/copy details appear only after an actual code exists;
  pending invitations appear only when present. Auto retains the Aedrova logo.
- **Settings open:** uses already authorized snapshot data while the active dashboard
  performs normal sync, rather than starting a full-page loader every time it opens.
- **Background sync:** no longer disables/covers every account page for dashboard jobs.
  Initial authentication and explicit account operations retain their loading/lock
  behavior. A settings save during a background job is deferred once, then rechecked
  against the same session/workspace; logout intent cancels it rather than silently
  issuing a stale write.
- **Search/files/saved panels:** display matching local authorized results immediately
  when available, then reconcile server inventory. An access/transport failure clears
  cached results; no prior private results remain presented as successfully refreshed.

## Other interaction paths inspected

Reviewed desktop window navigation/account opening, connected transport queue, message
outbox/reaction overlays, conversation picker, collaboration inventory/mentions, profile
avatar retrieval, staged uploads/previews, Bud connector loading and project settings.

Existing messages and reactions already have local pending/optimistic representations
and reconciliation. Existing local attachments stage before explicit Send; remote media
still requires verification before publication. Channel navigation uses permitted cached
messages when available. Mentions/formatting/navigation menus are local. Avatar and Bud
art caches already avoid repeated image work. No artificial delay or extra network
operation was added to these paths.

This is a targeted source/interaction audit, not a claim that every possible screen,
network condition, supported OS or external provider was benchmarked. First authentication,
empty caches and genuinely remote content may still load. Free hosted cold starts,
provider generation latency and unavailable meeting infrastructure cannot be fixed by
pretending a request succeeded.

## Safe use of optimistic UI

Local feedback is distinct from confirmed state. Do not fabricate a connected grant,
accepted permission, verified upload, completed build, successful payment or funded
allowance. Permission changes, publishing, deletions, billing and external authorization
keep their existing backend checks and approval gates. Cached views do not authorize
mutations. Keep session/workspace guards, failure clearing, stable message identifiers
and no duplicate retry after an uncertain non-idempotent operation.

## Verification and evidence

- Full desktop regression run: **933 passed** with the existing audioop deprecation
  warning. Final layout/cleanup adjustments have a separate focused verification below.
- Added ten focused regressions: picker while transport busy; settings while sync
  busy; focused channel form/no opening request; one creation until confirmation;
  uncertain creation/no duplicate retry; photo corner transparency; immediate cached
  inventory and clearing on failure; deferred settings save; cleared channel form on logout; cancelled queued save after
  logout intent.
- Existing DM tests now explicitly populate the session cache; they still verify the
  real server RPC for creating/reopening a conversation rather than accepting a fake DM.
- Light/dark settings previews inspected with synthetic workspace/account fixtures.
  Local previews: `work/ui-responsiveness-2026-10-24/`. These are rendered widgets,
  not a fresh live OAuth/provider acceptance record.
- Ruff, whitespace and secret-pattern validation accompany the source changes.

No personal setup is needed for these UI changes. A running source process must be
restarted to load edited modules. Existing step-1 blockers remain in
[staging acceptance](staging-acceptance-2026-10-24.md): meeting readiness 503, Stripe
OAuth/managed Search unavailable, remaining connector lifecycle, full build and physical
meeting acceptance. This UI work does not close those gates or approve public launch.

Final native recheck: blocked because macOS is locked. Owner must unlock the Mac
and leave Aedrova Staging available; the running source process must be restarted
to load the changed modules. No new credentials, migration, provider consent or
payment is required for that UI recheck. Do not treat offscreen previews as this check.
