# Bud briefs

Every Bud has a Markdown brief that tells it who it is, what it does and what it can read. It is
built from the template `src/aedrova/desktop/assets/buds/bud-brief.md`, with the choices made
during setup filled in as variables:

| Variable | Comes from |
|---|---|
| `{{name}}` | the Bud's name |
| `{{role}}`, `{{responsibilities}}` | the job role chosen in setup (Builder, Designer, Marketing, Finance, Research, Product) |
| `{{purpose}}` | the purpose written in setup |
| `{{sources}}` | the connectors actually connected, with what each can read, and its tools |
| `{{warmth}}`, `{{directness}}`, `{{detail}}`, `{{initiative}}`, `{{diligence}}`, `{{reporting}}` | the working-style sliders |
| `{{voice}}`, `{{notes}}` | the custom voice and notes |

The brief is rendered fresh each time the Bud answers and given to the model, so changing the
Bud's settings changes its behavior. The same text is saved as one file per Bud in
`~/Library/Application Support/Aedrova/Buds/<name>-<id>.md`. Open it from the last step of the Bud
setup ("Open Bud brief"). Setup text is treated as data: control characters and template syntax are
stripped, and every field is length-limited.

## How a Bud reads its connectors

- A message to a Bud always includes a read of its connected sources. Only a bare greeting skips it.
- The model picks which of the Bud's read-only tools to call. If it replies with extra words around
  the JSON the choice is still understood, and if it picks nothing for a real question the Bud reads
  its own first three tools rather than answer blind.
- What a connector can return is deliberately narrow: GitHub (repository details, recent commits,
  open issues, deployments), Notion (one shared page, first 20 blocks), Figma (top pages and
  frames), Supabase (project health), Vercel, Stripe (balance), Instagram, TikTok, search. File
  contents, nested Notion pages and images are not read.
