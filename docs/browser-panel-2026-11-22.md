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

## Update: the browser is its own process (November 22, 2026)

Clicking the Browser button crashed the app. Qt WebEngine's internal objects and the app's
application-wide Python event filters (tooltips, localization, search, links) cannot share one
process: the first focus event on the page sent one of those objects through a filter and
PySide recursed until it crashed. It reproduces with any such filter and a bare web view.

The panel, its rules and the agent bridge therefore run in `aedrova/browser/host.py`, started
on first use by `window_browser.py` and told over standard input to show, hide or change access
mode. It appears as a companion window beside the main window rather than inside it.
Packaged builds start it with `--browser-host`, like `--browser-mcp`.

Follow-up if you want it inside the main window again: replace the application-wide filters with
filters on specific windows, then the panel can be embedded without a second process.
