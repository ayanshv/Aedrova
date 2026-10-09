-- Actual resource-scoped Bud adapters; tokens remain in the private service store.
begin;
alter table public.workspace_dots drop constraint if exists workspace_dots_provider_check;
alter table public.workspace_dots add constraint workspace_dots_provider_check
 check(provider in ('github','stripe','supabase','vercel','posthog','figma','notion','instagram','tiktok','search','linear'));
create or replace function public.save_workspace_dot(p_id uuid,p_workspace uuid,p_version integer,p_provider text,p_resource text,p_name text,p_color text default '#4388F5',p_shape text default 'round')
returns public.workspace_dots language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); r public.workspace_dots;
begin
 perform aedrova_private.check_user_budget('dots',30,60);
 perform 1 from public.workspaces where id=p_workspace for update;
 if coalesce(aedrova_private.member_role(p_workspace),'') not in ('owner','admin') then raise exception 'Only workspace owners and admins can manage Dots'; end if;
 if p_version is null or p_provider not in ('github','stripe','supabase','vercel','posthog','figma','notion','instagram','tiktok','search','linear') or p_name !~ '^[A-Za-z0-9][A-Za-z0-9 _-]{0,31}$' or lower(p_name) in ('aedrova','channel','everyone') or p_color !~ '^#[A-Fa-f0-9]{6}$' or p_shape not in ('round','squircle','cloud') then raise exception 'Invalid Dot identity'; end if;
 if exists(select 1 from public.workspace_agent_preferences where workspace_id=p_workspace and lower(nickname)=lower(p_name)) then raise exception 'Use a name different from the central agent'; end if;
 if length(p_resource) not between 1 and 200 or p_resource ~ '(://|\.\.)' or (p_provider<>'search' and p_resource ~ '[[:space:]]') then raise exception 'Use a provider resource identifier, without credentials'; end if;
 if p_provider='github' and p_resource !~ '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$' then raise exception 'Use owner/repository'; end if;
 if p_id is null then
  if p_version<>0 or (select count(*) from public.workspace_dots where workspace_id=p_workspace and deleted_at is null)>=12 then raise exception 'Workspace supports up to 12 Dots'; end if;
  insert into public.workspace_dots(workspace_id,provider,resource,name,color,shape,created_by) values(p_workspace,p_provider,p_resource,p_name,p_color,p_shape,u) returning * into r;
 else
  update public.workspace_dots set name=p_name,color=p_color,shape=p_shape,version=version+1,updated_at=now()
  where id=p_id and workspace_id=p_workspace and version=p_version and provider=p_provider and resource=p_resource and deleted_at is null returning * into r;
  if not found then raise sqlstate 'PT409' using message='Dot changed. Refresh before saving.'; end if;
 end if;
 return r;
end $$;
revoke all on function public.save_workspace_dot(uuid,uuid,integer,text,text,text,text,text)
 from public,anon;
grant execute on function public.save_workspace_dot(uuid,uuid,integer,text,text,text,text,text)
 to authenticated;
commit;
