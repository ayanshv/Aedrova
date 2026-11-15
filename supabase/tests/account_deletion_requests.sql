begin;

insert into auth.users (id, email, email_confirmed_at) values
    ('ed001000-0000-0000-0000-000000000001', 'deletion-one@example.test', now()),
    ('ed001000-0000-0000-0000-000000000002', 'deletion-two@example.test', now()),
    ('ed001000-0000-0000-0000-000000000003', 'deletion-unconfirmed@example.test', null);

set local role anon;
do $$ begin
    perform public.request_account_deletion();
    raise exception 'Anonymous request unexpectedly succeeded';
exception when insufficient_privilege then null;
end $$;

set local role authenticated;
select set_config('request.jwt.claim.sub', 'ed001000-0000-0000-0000-000000000003', true);
do $$ begin
    perform public.request_account_deletion();
    raise exception 'Unconfirmed request unexpectedly succeeded';
exception when insufficient_privilege then null;
end $$;

select set_config('request.jwt.claim.sub', 'ed001000-0000-0000-0000-000000000001', true);
do $$
declare receipt jsonb;
begin
    assert public.get_account_deletion_request() is null;
    receipt := public.request_account_deletion();
    assert receipt->>'id' is not null;
    assert receipt->>'requested_at' is not null;
    assert receipt->>'completed' = 'false';
    assert public.request_account_deletion() = receipt;
    assert public.get_account_deletion_request() = receipt;
end $$;

select set_config('request.jwt.claim.sub', 'ed001000-0000-0000-0000-000000000002', true);
do $$ begin
    assert public.get_account_deletion_request() is null;
    perform 1 from aedrova_private.account_deletion_requests;
    raise exception 'Another account could read the private queue';
exception when insufficient_privilege then null;
end $$;

reset role;
do $$ begin
    assert (select count(*) from aedrova_private.account_deletion_requests) = 1;
    assert (select count(*) from auth.users where id = 'ed001000-0000-0000-0000-000000000001') = 1;
end $$;

rollback;
