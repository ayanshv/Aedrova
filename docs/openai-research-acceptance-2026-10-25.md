# OpenAI Research Bud — staging acceptance

Implemented and deployed to **staging only**, backend commit `8df2cc3`, Render
deployment `dep-dbf3ifjrjlhs739eept0` (Live). Existing OpenAI credential reused;
no new key, Brave account, card, funding, hosting upgrade or production change.

## Behavior

- Research Bud / Web search uses OpenAI Responses with a pinned search-capable
  `gpt-5.4-mini-2026-03-17`. Its backend key never reaches desktop or grant records.
- Saving a topic is free. Actual live research requires an active plan and budget.
- Existing service/workspace daily caps remain 100/10. Before every request,
  reserve the full 128k search input ceiling, 2048 output tokens and one $0.01
  search fee ($0.115216 maximum reservation at the pinned model rates).
  Settle reported usage plus search fee; uncertain outcomes keep the reservation.
  No overage, silent fallback, automatic retries or budget increase.
- Agent retrieval passes its scoped run token, avoiding a second workflow that
  would conflict with Free concurrency. Server checks user, workspace, current
  membership and billing root. Direct tool reads create/end their own metered run.
- One hosted search call; low reasoning; 60-second processing checks and bounded
  provider response. Incomplete/uncited results fail visibly. `store:false`.
- Search request contains the saved topic, not workspace files, messages or private
  history. Final agent synthesis still uses the existing permission/context rules.
- Actual returned source URLs are appended after permission recheck. Native reply
  links support mouse and keyboard and reject local-file/credential-bearing URLs.
- Greetings continue to skip retrieval. Research/current/sources questions enter
  the existing controlled selection flow. This is bounded live research, not a
  claim that an unlimited background deep-research product has shipped.

## Acceptance

- Full backend suite: **638 passed** (one existing dependency warning).
- Combined desktop chat/mentions/Bud tools/connectors regression group: **97 passed**;
  final native source-link group: **3 passed**. Scoped Ruff/diff checks passed.
- Real authenticated staging read passed using the existing disposable audit Bud
  and a public official-documentation topic. Two HTTPS sources returned. Creating
  the capability changed no spend; actual search recorded **19123 micro-USD
  ($0.019123)**. Borrowed-run path passed with existing credit, no funding.
- Local disconnect succeeded; later tool read denied. Test run closed and local
  test session signed out. Transient authorization URLs/result file removed.
- Native citation UI preview rendered in both themes; this preview is distinct
  from the actual hosted tool acceptance above. Final whole-agent synthesis uses
  the separately tested existing pipeline; no additional live synthesis was run.

Ignored evidence: `work/acceptance-final-oct25/research-live.json`,
`research-staging-live.png`, `research-light.png`, `research-dark.png`.

## Remaining gates

TikTok sandbox reads, Stripe test reads, new-workspace Free activation and now live
OpenAI Search are accepted. Brave activation is superseded and its card page closed.
Claude credit balance remains unfunded, and hosted meeting health remains 503;
keep their payment steps at the final owner-paid launch gate, then run actual
Claude coding and two-device call/consent/transcript acceptance.

Public social availability remains separate from tester acceptance. The inspected
TikTok Production app is a draft with no production products/scopes and requires
review details plus a real end-to-end demo. Meta app 3077883259220045 is unpublished;
its missing Privacy/Terms/deletion URLs were saved and verified after reload.
Meta now confirms all required app settings complete; use-case/App Review/access
verification and final publishing are not accepted by that message alone.

See `docs/provider-public-review-preparation.md` for prepared submission text and
exact remaining provider work. Stage 1 is not globally complete; no public launch
or Step 10 production promotion is authorized by this acceptance.

Official model/tool/rate references checked October 25, 2026:
https://developers.openai.com/api/docs/guides/tools-web-search
https://developers.openai.com/api/docs/models/gpt-5.4-mini
https://developers.openai.com/api/docs/pricing
