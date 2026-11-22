# AI allowances: weekly and five-hour windows

Decision (November 22, 2026): included AI is limited by a rolling five-hour window and a
rolling weekly window, with a monthly backstop. Chat, files and meetings never use these.
Limits are measured in provider cost, so they stay honest if model prices change.

## Limits by plan

| Plan | Weekly cap | Five-hour cap | Monthly backstop | Weekly tokens* | Five-hour tokens* |
|---|---|---|---|---|---|
| Free | $0.15 | $0.10 | $0.50 | about 91k | about 61k |
| Pro | $2.00 | $0.80 | $8.70 | about 1.2M | about 487k |
| Teams | $4.00 | $1.60 | $17.40 | about 2.4M | about 974k |

\* Blended tokens at the configured `gpt-5.3-codex` rates ($1.75 input, $0.175 cached input,
$14 output per million) and a typical coding mix of 92% input (75% of it cached) and 8%
output, about $1.64 per million tokens. A run that writes more code uses fewer tokens per
dollar; a run that mostly reads uses more.

## Why these numbers still make a profit

Prices are the live aedrova.com prices: Pro $15/month or $144/year, Teams $30/month or
$288/year. The table uses the annual price per month ($12 and $24), the worst case for
revenue. Payment fees are Stripe's 2.9% plus $0.30.

| | Pro | Teams |
|---|---|---|
| Net revenue per month, annual billing | $11.63 | $23.28 |
| Worst case: every week used to the cap (4.33 weeks) | $8.67 | $17.33 |
| Worst-case gross margin, annual billing | 25% | 25% |
| Worst-case gross margin, monthly billing | 39% | 40% |
| Expected at 35% use, annual billing | 74% | 74% |

Hosting, database and meeting costs are fixed and not included. The test
`tests/test_allowance_windows.py` fails if a future edit pushes the worst case below 24%.

## Where it lives

- Site: `aedrova_site/policy.py` (numbers and the basis in comments), `budgets.py`
  (windows), `store.py` (balance fields `weekly_*` and `five_hour_*`).
- Desktop: the usage meter shows the tighter window and lists both with reset times.

## Status and owner actions

Price reconciliation: the three conflicting tables were an artifact of a stale local checkout.
The published main branch already prices per person and derives every allowance from one
table (Pro $15 / $144, Teams $30 / $288). The allowance work was rebuilt on that base in the
worktree `Aedrova_site_allowances`, branch `codex/weekly-five-hour-allowances`, staged and
not committed, with all 733 site tests and 14 browser tests passing.

1. **Review and merge** that branch (ask me to commit it and open the pull request). Your older
   `Aedrova_site` checkout is 16 commits behind `origin/main`; pull it before editing there.
2. **Before deploying, check the `plans` setting on Render.** If it holds allowances from the
   old limits, the service refuses to start and says why. Use 8,700,000 / 104,400,000 /
   17,400,000 / 208,800,000 for `pro_monthly` / `pro_annual` / `power_monthly` /
   `power_annual`, or leave `plans` unset while checkout is off. This blocks the deploy.
3. **Deploy to Render** only after the merge. It also ships the web search gateway change.
   Deploying is yours to approve; I have not deployed anything.
4. **Recheck the margin** if a model rate or plan price changes. The test and the comment in
   `policy.py` show the formula.
