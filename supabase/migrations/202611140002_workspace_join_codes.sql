begin;

create table aedrova_private.workspace_join_codes (
    workspace_id uuid primary key references public.workspaces on delete cascade,
    code_hash bytea not null unique,
    issued_by uuid not null,
    expires_at timestamptz not null,
    uses integer not null default 0 check (uses between 0 and 20)
);
alter table aedrova_private.workspace_join_codes enable row level security;
revoke all on aedrova_private.workspace_join_codes from public, anon, authenticated;

create function public.create_workspace_join_code(p_workspace uuid)
returns text language plpgsql volatile security definer set search_path = '' as $$
declare
    requester uuid := aedrova_private.require_user();
    secret text;
begin
    perform 1 from public.workspaces where id = p_workspace for update;
    if coalesce(aedrova_private.member_role(p_workspace), '') not in ('owner', 'admin') then
        raise exception 'Only workspace owners or admins can create a join code' using errcode = '42501';
    end if;
    perform aedrova_private.check_user_budget('workspace-join-code', 10, 60);
    secret := upper(substr(replace(gen_random_uuid()::text, '-', ''), 17, 16));
    insert into aedrova_private.workspace_join_codes (workspace_id, code_hash, issued_by, expires_at)
    values (p_workspace, sha256(convert_to(secret, 'UTF8')), requester, now() + interval '7 days')
    on conflict (workspace_id) do update set code_hash = excluded.code_hash, issued_by = excluded.issued_by,
        expires_at = excluded.expires_at, uses = 0;
    return 'A2-' || substr(secret, 1, 4) || '-' || substr(secret, 5, 4) || '-' ||
        substr(secret, 9, 4) || '-' || substr(secret, 13, 4);
end $$;

alter function public.accept_invitation(text) set schema aedrova_private;
revoke all on function aedrova_private.accept_invitation(text) from public, anon, authenticated;

create function public.accept_invitation(p_token text)
returns uuid language plpgsql volatile security definer set search_path = '' as $$
declare
    requester uuid := aedrova_private.require_user();
    normalized text;
    digest bytea;
    target uuid;
    invitation aedrova_private.workspace_join_codes;
begin
    if p_token is null or length(p_token) > 128 then
        raise exception 'Invitation unavailable' using errcode = '42501';
    end if;
    normalized := upper(btrim(p_token));
    if normalized !~ '^A2(-[0-9A-F]{4}){4}$' then
        return aedrova_private.accept_invitation(btrim(p_token));
    end if;
    digest := sha256(convert_to(replace(substr(normalized, 4), '-', ''), 'UTF8'));
    select workspace_id into target from aedrova_private.workspace_join_codes where code_hash = digest;
    perform 1 from public.workspaces where id = target for update;
    select * into invitation from aedrova_private.workspace_join_codes where workspace_id = target and code_hash = digest;
    if invitation.workspace_id is null or invitation.expires_at <= now() or not exists (
        select 1 from public.workspace_members where workspace_id = target and user_id = invitation.issued_by
            and role in ('owner', 'admin')
    ) then
        raise exception 'Invitation unavailable' using errcode = '42501';
    end if;
    if exists (select 1 from public.workspace_members where workspace_id = target and user_id = requester) then
        return target;
    end if;
    if invitation.uses >= 20 then
        raise exception 'Invitation unavailable' using errcode = '42501';
    end if;
    insert into public.workspace_members (workspace_id, user_id, role) values (target, requester, 'member');
    update aedrova_private.workspace_join_codes set uses = uses + 1 where workspace_id = target;
    return target;
end $$;

revoke all on function public.create_workspace_join_code(uuid), public.accept_invitation(text) from public, anon;
grant execute on function public.create_workspace_join_code(uuid), public.accept_invitation(text) to authenticated;
notify pgrst, 'reload schema';
commit;
