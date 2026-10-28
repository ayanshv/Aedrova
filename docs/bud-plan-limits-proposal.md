# Bud capacity by workspace plan

October 24, 2026 — approved by owner. Source implementation complete; owner reports
staging SQL installed. Authenticated hosted verification remains pending.

- Free: 1 Bud per workspace.
- Pro: 5 Buds per workspace.
- Team: 15 Buds per workspace.
- Enterprise: contracted capacity, configured explicitly by an administrator.

Capacity is shared by the workspace, not multiplied by members. Creating multiple
Buds does not multiply AI credits, concurrent-run limits, or provider budgets.
Saved configurations and disconnected Buds count toward capacity; deleting a Bud frees a
slot. Reconnecting or editing an existing Bud does not consume another slot.

The new migration enforces creation with a subscription-scoped transaction lock
and the verified private `aedrova_billing.billing` ledger. Legacy internal tier
`monthly` means Pro; `annual` means Team, independent of the public interval switch.
Subspaces share the billing root's capacity. Without a verified paid entitlement,
the cap is Free. The private Enterprise table requires explicit operator capacity.
Bud setup shows count/limit; website cards list the approved capacities.
Client-side counters are guidance, never authorization.
Early-access capacity follows the workspace's effective promotional entitlement
and expiry; no automatic paid subscription is created.

If a downgrade leaves too many Buds, retain configurations and history and block
new creation until below the new limit. Existing Buds remain editable/removable;
this change does not automatically delete or pause them. AI spending remains capped
separately. Enterprise requires finite configured capacity, never unlimited.

Owner reports staging installation of
`supabase/migrations/202610240001_bud_plan_limits.sql` completed. No repeat SQL action
is needed. Restart the app with the staging launcher to load the quota counter.
Verify the authenticated RPC and hosted boundaries before certifying enforcement.
Production migration is a separate release step. No API key, purchase or billing
change is required.
