begin;
create table public.workspace_agent_preferences (
 workspace_id uuid primary key references public.workspaces on delete cascade,
 nickname text not null check(length(nickname) between 1 and 32
   and nickname=btrim(nickname) and nickname ~ '^[[:alnum:]][[:alnum:] _-]*$'),
 provider text not null check(provider in ('codex','claude_code')),
 updated_at timestamptz not null default now()
);
alter table public.workspace_agent_preferences enable row level security;
revoke all on public.workspace_agent_preferences from public,anon,authenticated;
grant select on public.workspace_agent_preferences to authenticated;
create policy agent_preferences_read on public.workspace_agent_preferences for select to authenticated
 using (aedrova_private.member_role(workspace_id) is not null);

create function public.set_agent_preferences(p_workspace uuid,p_nickname text,p_provider text)
returns void language plpgsql security definer set search_path='' as $$
begin
 perform aedrova_private.require_user();
 perform 1 from public.workspaces where id=p_workspace for update;
 if coalesce(aedrova_private.member_role(p_workspace),'') not in ('owner','admin')
 then raise exception 'Not allowed' using errcode='42501'; end if;
 insert into public.workspace_agent_preferences(workspace_id,nickname,provider)
 values(p_workspace,btrim(p_nickname),p_provider)
 on conflict(workspace_id) do update set nickname=excluded.nickname,provider=excluded.provider,
 updated_at=now();
end $$;

create function public.onboard_workspace(p_name text,p_nickname text,p_provider text)
returns uuid language plpgsql security definer set search_path='' as $$
declare w uuid;
begin
 w := public.create_workspace(p_name);
 perform public.set_agent_preferences(w,p_nickname,p_provider);
 return w;
end $$;
revoke all on function public.set_agent_preferences(uuid,text,text),
 public.onboard_workspace(text,text,text) from public,anon;
grant execute on function public.set_agent_preferences(uuid,text,text),
 public.onboard_workspace(text,text,text) to authenticated;
commit;
