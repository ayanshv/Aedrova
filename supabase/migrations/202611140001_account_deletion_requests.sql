begin;

create table aedrova_private.account_deletion_requests (
    user_id uuid primary key,
    id uuid not null unique default gen_random_uuid(),
    requested_at timestamptz not null default now(),
    completed_at timestamptz check (completed_at >= requested_at)
);

alter table aedrova_private.account_deletion_requests enable row level security;
revoke all on aedrova_private.account_deletion_requests from public, anon, authenticated;

create function public.get_account_deletion_request()
returns jsonb language plpgsql stable security definer set search_path = '' as $$
declare
    requester uuid := aedrova_private.require_user();
begin
    return (
        select jsonb_build_object('id', request.id, 'requested_at', request.requested_at,
                                  'completed', request.completed_at is not null)
        from aedrova_private.account_deletion_requests as request
        where request.user_id = requester
    );
end;
$$;

create function public.request_account_deletion()
returns jsonb language plpgsql volatile security definer set search_path = '' as $$
declare
    requester uuid := aedrova_private.require_user();
begin
    insert into aedrova_private.account_deletion_requests (user_id) values (requester)
    on conflict (user_id) do nothing;
    return public.get_account_deletion_request();
end;
$$;

revoke all on function public.get_account_deletion_request(), public.request_account_deletion()
    from public, anon, authenticated;
grant execute on function public.get_account_deletion_request(), public.request_account_deletion()
    to authenticated;

notify pgrst, 'reload schema';
commit;
