# Post-launch plans

## Optimal model routing

Status is deferred until after launch.

Launch uses a single Aedrova agent backed by the server-managed OpenAI (Codex) API.
Claude funding and Claude builds are post-launch work (decided November 21, 2026).
The app presents Aedrova consistently in onboarding, workspace settings, project
settings and builds. Older saved Auto or Claude preferences use OpenAI for new work.
Model routing is removed from launch advertising.

After launch, evaluate routing across providers using representative coding tasks.
Measure successful implementation, test outcomes, response time and actual cost.
Only add a provider after funding, model access and production protocol acceptance
are verified. Keep permission checks, context access controls, cancellation,
usage reservations and shared reply persistence consistent across providers.

Before enabling routing, test workspace and local project preference precedence,
retry behavior and behavior when a provider has no credits. Evaluate whether a
single Aedrova identity with internal routing gives users a clearer experience.
Update user disclosures and marketing only after the feature passes live acceptance.

## Agent-to-Bud collaboration

Status is deferred until after launch (owner direction, November 22, 2026).

The main Aedrova agent should be able to ask other Buds for input while it works, for
example consulting the Design Bud on a UI fix or the Product Bud for requirements. The
exchange runs in the background and the user sees one Aedrova answer with the Bud input
attributed. Before building it, decide how Bud tool permissions are scoped (a Bud never
lends its connectors to the agent), how consulted Bud output is cited as untrusted
evidence, and how usage is reserved and shown. Launch keeps the single-agent
mention-to-build flow.
