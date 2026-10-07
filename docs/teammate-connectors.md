# AI teammate connectors — scoped local release

October 6: owner authorized real connectors, automatic tool suggestions and a required tool
connection, bringing the first connector slice forward before shared results (M17F.2).

## What exists

- GitHub: selected repository metadata, first 10 open issues/PRs and bounded README.
  Reuses the user's explicit existing GitHub helper login when no token is entered.
- Figma: selected file structure at depth 2. This does not render design images or fetch
  every nested layer.
- Notion: first 100 direct blocks of a selected page. Nested blocks and pagination are
  explicitly excluded in evidence coverage.
- All requests are read-only, fixed-host, timeout/size bounded. Redirects are rejected.
  A failed required connection stops the assignment; no synthetic results or stale fallback.
- Explicit Verify & connect fetches the resource before storing a token. Save verifies
  every configured tool again. An assignment gathers fresh evidence and checks account
  membership/profile version again. Every work phase rechecks tool access, so disconnecting
  after planning prevents the next phase from using an earlier connector snapshot.
- Tokens are in the native macOS Keychain only, keyed by account/workspace/teammate/tool/
  resource. Shared teammate config contains only tool IDs and resource IDs. Tokens never
  enter model prompts, chat, shared SQL config or subprocess arguments.
- Members connect their own credentials to owner-approved resources on their own Mac;
  only owners/admins can change the teammate's resource selection. Changing accounts or
  workspace cannot reuse another account's connection. Disconnect removes the local token.
- At least one connected tool is required to save a teammate and run a new assignment.
  Existing profiles remain readable, but must be connected before new work. Already saved
  results remain reviewable. No SQL migration is needed: existing config JSON stores the
  resource selection, with existing owner/admin RLS/version controls.
- Typing a role immediately produces clearly labelled local role-based suggestions.
  After a 1.6-second pause, the existing local Codex/Claude provider refines them with AI.
  This uses the provider's login/allowance and sends only the role, not team context.
  Missing provider access retains transparent local suggestions. Suggestions never grant
  permission, choose Engineering authority or overwrite a resource being configured.
- External evidence has source citations, bounded coverage and an untrusted-evidence
  label in the task's existing source index. Recognizable secrets in sources fail closed.

## What the owner/user needs to do

No SQL, server secrets, purchases or public OAuth app registration are required for this
local connector slice. The user must explicitly connect at least one resource:

1. Aedrova → AI TEAMMATES → + (or select a teammate) → describe a role.
2. Choose a tool in Connect their tools; enter the selected resource URL.
3. GitHub: if already signed in through Aedrova's GitHub setup, leave the token blank and
   select Verify & connect. Otherwise finish GitHub setup or supply a fine-grained token
   restricted to the selected repository with read-only metadata, contents and issues access.
4. Figma: Settings → Security → Personal access tokens; generate a token with
   `file_content:read` for a file your account can access. Enter it only in the masked
   Aedrova connector field. Paste the file/design URL and Verify & connect.
5. Notion: create an internal connection with Read content capability, copy its token
   locally, and add the connection to the chosen page using page ••• → Add connections.
   Enter the token only in Aedrova, paste that page's URL and Verify & connect.
6. If macOS asks, authorize Aedrova to use Keychain. Save teammate, then @mention them.

Only one tool is required. Figma/Notion live acceptance needs the owner's actual granted
resource and credentials; these have not been connected silently or claimed validated.
Do not paste tokens into this chat. Provider token expiry/revocation requires reconnecting.

## Verification

All 612 desktop tests and 32 website public-page checks passed. Database/RLS suites,
scoped lint, final app signature verification and packaged smoke checks passed.
Actual GitHub API retrieval
using the owner's existing helper login passed. A real macOS Keychain synthetic save/read/
account-isolation/delete test passed and removed its test entry; no owner token was saved
by the validation script. Report: `work/teammate-connectors/live-check.json`.

## Scope limits and next gates

This is a local, read-only connector release, not general action execution or shared
credential hosting. Public multi-user OAuth installs, Windows credential storage, deeper
retrieval, marketing publishing, generation tools and financial tools are later connector
stages. M17F.2 shared results/task history/team management still requires approval.
Website preview describes implemented scope; no GitHub push or live deployment performed.

## Provider references

- [GitHub fine-grained token permissions](https://docs.github.com/en/rest/authentication/permissions-required-for-fine-grained-personal-access-tokens)
- [Figma personal access tokens](https://developers.figma.com/docs/rest-api/personal-access-tokens/)
- [Figma authentication/scopes](https://developers.figma.com/docs/rest-api/authentication/)
- [Notion connection authorization](https://developers.notion.com/guides/get-started/authorization)
