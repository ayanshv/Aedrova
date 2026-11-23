# Beta allowlist

While the gate is on, only emails on the list can use Aedrova. The check lives in the database
(`aedrova_private.require_user()`), so it covers every action, not just sign-in. The app also asks
right after sign-in and explains plainly when an email is not on the list.

Migration: `supabase/migrations/202611230001_beta_allowlist.sql`. It creates an empty list and a
gate that is **off** by default, so applying it changes nothing until you turn the gate on.

## Run order

1. Apply the migration to the project testers will use.
2. Add yourself and every tester **before** turning the gate on (below).
3. Turn the gate on. Sign in once with a listed account and once with an unlisted one to check.

## Add or remove emails

Run in the Supabase SQL editor. Emails are stored lower case; Gmail dots and `+tags` are ignored,
so `First.Last+beta@gmail.com` matches `firstlast@gmail.com`.

```sql
insert into aedrova_private.beta_access (email, note)
values ('person@example.com', 'Name, workspace')
on conflict do nothing;

delete from aedrova_private.beta_access where email = 'person@example.com';
select email, note, added_at from aedrova_private.beta_access order by added_at;
```

## Turn the gate on or off

```sql
update aedrova_private.beta_gate set enabled = true;   -- on
update aedrova_private.beta_gate set enabled = false;  -- off, the list is kept
```

## Limits

- A removed tester loses access on their next request; no data is deleted.
- Apple "Hide My Email" gives Aedrova a relay address that cannot match a real inbox. Ask beta
  testers to sign in with Google or an email and password.
- Do not commit tester emails to the repository.
