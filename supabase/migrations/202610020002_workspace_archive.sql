begin;
-- Personal organization only. Archive never changes membership, billing or shared data.
create table public.workspace_preferences (
 workspace_id uuid not null,
 user_id uuid not null,
 archived boolean not null default false,
 primary key(workspace_id,user_id),
 foreign key(workspace_id,user_id) references public.workspace_members(workspace_id,user_id)
 on delete cascade
);
create index workspace_preferences_by_user on public.workspace_preferences(user_id,archived,workspace_id);
alter table public.workspace_preferences enable row level security;
revoke all on public.workspace_preferences from public,anon,authenticated;
grant select on public.workspace_preferences to authenticated;
create policy workspace_preferences_read on public.workspace_preferences for select to authenticated
 using(user_id=auth.uid() and aedrova_private.member_role(workspace_id) is not null);

create function public.list_my_workspaces(p_archived boolean default false)
returns table(id uuid,name text) language plpgsql stable security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user();
begin
 if p_archived is null then raise exception 'Choose an archive state' using errcode='22023'; end if;
 return query select w.id,w.name from public.workspaces w
 join public.workspace_members m on m.workspace_id=w.id and m.user_id=u
 left join public.workspace_preferences p on p.workspace_id=w.id and p.user_id=u
 where coalesce(p.archived,false)=p_archived order by w.name,w.id;
end $$;

create function public.set_workspace_archived(p_workspace uuid,p_archived boolean)
returns uuid language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user();
begin
 -- Serialize with membership changes; a removed user cannot recreate a preference.
 perform 1 from public.workspaces where id=p_workspace for update;
 if p_archived is null then raise exception 'Choose an archive state' using errcode='22023'; end if;
 if not exists(select 1 from public.workspace_members where workspace_id=p_workspace and user_id=u)
 then raise exception 'Workspace unavailable' using errcode='42501'; end if;
 if coalesce((select archived from public.workspace_preferences
 where workspace_id=p_workspace and user_id=u),false)=p_archived then return p_workspace; end if;
 perform aedrova_private.check_user_budget('workspace_archive',20,60);
 insert into public.workspace_preferences(workspace_id,user_id,archived)
 values(p_workspace,u,p_archived)
 on conflict(workspace_id,user_id) do update set archived=excluded.archived;
 return p_workspace;
end $$;
revoke all on function public.list_my_workspaces(boolean),public.set_workspace_archived(uuid,boolean)
 from public,anon;
grant execute on function public.list_my_workspaces(boolean),public.set_workspace_archived(uuid,boolean)
 to authenticated;
commit;
