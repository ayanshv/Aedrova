# Prompt-injection check (November 25, 2026)

Question: can text on a web page, or in other untrusted content, steer an agent into leaking
files, opening hostile addresses or acting for itself?

## What was tested

`tests/test_prompt_injection.py` runs 110 attack-style checks against the rules the app enforces
in code. `scripts/live_injection_check.py` is a live version against a real model.

- Addresses: loopback, private, link-local, metadata, IPv6 forms, numeric spellings, look-alike
  dots, user-info tricks, non-web schemes, over-long and control-character addresses, and names
  that resolve to private addresses (including mixed answers).
- Page text: hostile text always sits below the "untrusted web page content" marker.
- Fields: password, card, one-time-code, token and similar fields are never filled.
- Access modes: what each mode asks before acting on an injected instruction.
- The coding agent: injected shell commands, network clients, and edits to secrets or paths
  outside the project.

## Gaps found and fixed

1. Octal and hex spellings of loopback (`0177.0.0.1`) passed the address check. Non-canonical
   numeric hosts are now refused.
2. A name with a look-alike dot (`example.com。localhost`) hid a `.localhost` name. Look-alike
   dots are normalised before the checks.
3. The request guard missed bracketed IPv6 addresses.
4. The request guard blocked ordinary sites that start with a digit (`1password.com`, `3m.com`).
5. In Ask for approval and Approve for me, an address with a long query or fragment on an
   already-approved site opened without asking, so page text could carry data out. Addresses
   carrying more than 48 characters after the path now ask.
6. In Approve for me, any text typed into a search box went through without asking. Text longer
   than 48 characters now asks.

## What is not covered

- **A live model.** This Mac's Codex login cannot use the model set in `~/.codex/config.toml`
  (`gpt-6.1-sol`), and the other models tried were refused too, so no live run happened. The
  checks above prove what the app does regardless of what a model decides, not what a model
  chooses to do with hostile text. Run `scripts/live_injection_check.py` once a model works.
- **Full access.** By design it acts without asking, so an injected instruction can open an
  attacker address with data in it. Do not make it the default for testers.
- **Short leaks.** Under the 48-character limit, small pieces of text can still leave one
  navigation at a time in Approve for me. Ask for approval stops this.
- **Name rebinding.** A name can resolve to a public address when checked and a private one
  later. The request guard checks hosts by name and address form, not by a fresh lookup.
- **Other content.** Search results, Slack imports and workspace chat reach the agent as
  labelled untrusted evidence. Their wording was checked for the label, not attacked with a model.
- **Codex's own sandbox.** File and network limits inside a build are Codex's, not tested here.

## Recommendation for testers

Default the first cohort to Approve for me, or Ask for approval for anyone who gives the agent
project files. Tell them Full access trusts every page the agent reads.
