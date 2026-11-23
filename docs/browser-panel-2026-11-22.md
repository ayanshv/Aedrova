# Built-in browser panel: decisions and plan (November 22, 2026)

Owner decisions
- **Scope:** full agent control (open, read, screenshot, scroll, click, type), with a visible
  cursor and a Stop button.
- **Placement:** a panel docked beside the conversation.
- **Safety follows the composer's access mode.** Full access: public sites open without prompts.
  Approve for me: ask once per new site; clicks that look like purchases, deletes or submissions
  ask. Ask for approval: ask per new site and for each click or typed entry.
- **Always, in every mode:** never type passwords, card numbers or one-time codes; no
  downloads or uploads; no local-network, loopback or file addresses; no camera, microphone,
  location or notification prompts; page text is untrusted data, never instructions.
- **Engine:** embedded Qt WebEngine (Chromium 140 in the current PySide6). Adds roughly 150 to
  200 MB to installers.
- **Policies:** privacy policy and terms on the website must describe it (drafted locally in the
  site repository; the owner reviews with counsel and deploys).

Architecture
- `aedrova/browser/policy.py`: pure rules (URL checks, address checks, sensitive fields,
  decision per access mode).
- `aedrova/browser/panel.py`: the panel, an isolated profile, approvals, cursor, Stop.
- `aedrova/browser/controller.py`: runs agent actions on the page, one at a time.
- `aedrova/browser/bridge.py`: a loopback socket with a per-session token.
- `aedrova/browser/mcp_server.py`: the stdio tool server the Codex agent talks to.

Not verified yet: a real Codex run calling these tools, and packaged-build behaviour.

## Status (November 22, 2026)

Built and tested
- Policy rules (33 tests), panel with isolated profile, approvals, visible cursor and Stop,
  controller, loopback bridge with a session token, and an MCP tool server that completes a
  real MCP handshake and lists its seven tools.
- Codex accepts the generated settings (`codex mcp get aedrova_browser` shows the stdio server
  with approvals handled by the app).
- Docked beside the conversation: Browser button, View menu, and Ctrl+Shift+B. It stays unloaded
  until used; agents that use it open it automatically.
- Website drafts: privacy section 25 and terms section 27 in the site worktree
  `Aedrova_site_browser` (branch `codex/browser-policy`), not pushed or deployed.

Not verified
- A real Codex run calling the tools (needs a signed-in agent run).
- Packaged builds: Qt WebEngine adds its own helper process and resources. Re-check
  PyInstaller output, macOS signing and notarization, and the Windows build, and expect a much
  larger installer.
- Behaviour on real websites: logins, consent banners, CAPTCHAs (the agent cannot and must not
  pass them), and heavy pages.

Owner actions
1. Have counsel review the drafted privacy and terms sections, then merge and deploy the site.
2. Decide whether the browser is on for the first public launch (`browser/enabled` setting).
3. Approve a packaging pass for the larger installer.

## Update: a large side panel inside the workspace (November 22, 2026)

Opening the browser crashed the app. Qt WebEngine's internal objects and the app's
application-wide Python event filters cannot both be alive: the first focus event on a page
sends one of those objects through a filter and PySide recurses until it dies. A bare web view
plus a do-nothing filter reproduces it.

The panel now docks inside the workspace, beside the conversation, and stays out of the way of
that bug: `aedrova/desktop/appfilters.py` is the one place application-wide filters register.
While a page exists they are lifted (tooltips use the system's, translation rescans on a timer,
idle time is read from the pointer); closing the panel closes the page and puts them back. The
web page is only created when someone opens an address or an agent acts, and the empty panel
shows "Browse with Aedrova".

Known limit: with the browser open, custom tooltips and instant translation of new widgets are
replaced by simpler stand-ins until it is closed.
