-- Dots are shared capability identities. Secrets live in the private server store.
begin;
create table if not exists public.workspace_dots (
 id uuid primary key default gen_random_uuid(),
 workspace_id uuid not null references public.workspaces(id) on delete cascade,
 provider text not null check(provider in ('github','stripe','supabase','vercel','posthog','figma','notion')),
 resource text not null check(length(resource) between 1 and 200),
 name text not null check(name ~ '^[A-Za-z0-9][A-Za-z0-9 _-]{0,31}$'),
 color text not null default '#4388F5' check(color ~ '^#[A-Fa-f0-9]{6}$'),
 shape text not null default 'round' check(shape in ('round','squircle','cloud')),
 version integer not null default 1,
 created_by uuid references auth.users(id) on delete set null,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 deleted_at timestamptz
);
create unique index if not exists workspace_dots_resource on public.workspace_dots(workspace_id,provider,lower(resource)) where deleted_at is null;
create unique index if not exists workspace_dots_name on public.workspace_dots(workspace_id,lower(name)) where deleted_at is null;
alter table public.workspace_dots enable row level security;
revoke all on public.workspace_dots from anon,authenticated;
grant select on public.workspace_dots to authenticated;
create policy dots_members_read on public.workspace_dots for select to authenticated using (aedrova_private.member_role(workspace_id) is not null and deleted_at is null);
create or replace function public.save_workspace_dot(p_id uuid,p_workspace uuid,p_version integer,p_provider text,p_resource text,p_name text,p_color text default '#4388F5',p_shape text default 'round')
returns public.workspace_dots language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); r public.workspace_dots;
begin
 perform aedrova_private.check_user_budget('dots',30,60);
 perform 1 from public.workspaces where id=p_workspace for update;
 if coalesce(aedrova_private.member_role(p_workspace),'') not in ('owner','admin') then raise exception 'Only workspace owners and admins can manage Dots'; end if;
 if p_version is null or p_provider not in ('github','stripe','supabase','vercel','posthog','figma','notion') or p_name !~ '^[A-Za-z0-9][A-Za-z0-9 _-]{0,31}$' or lower(p_name) in ('aedrova','channel','everyone') or p_color !~ '^#[A-Fa-f0-9]{6}$' or p_shape not in ('round','squircle','cloud') then raise exception 'Invalid Dot identity'; end if;
 if exists(select 1 from public.workspace_agent_preferences where workspace_id=p_workspace and lower(nickname)=lower(p_name)) then raise exception 'Use a name different from the central agent'; end if;
 if length(p_resource) not between 1 and 200 or p_resource ~ '(://|[[:space:]]|\.\.)' then raise exception 'Use a provider resource identifier, without credentials'; end if;
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
create or replace function public.remove_workspace_dot(p_id uuid,p_workspace uuid,p_version integer)
returns void language plpgsql security definer set search_path='' as $$
begin
 perform aedrova_private.require_user();
 if coalesce(aedrova_private.member_role(p_workspace),'') not in ('owner','admin') then raise exception 'Only workspace owners and admins can remove Dots'; end if;
 update public.workspace_dots set deleted_at=now(),version=version+1,updated_at=now() where id=p_id and workspace_id=p_workspace and version=p_version and deleted_at is null;
 if not found then raise sqlstate 'PT409' using message='Dot changed. Refresh before removing.'; end if;
end $$;
revoke all on function public.save_workspace_dot(uuid,uuid,integer,text,text,text,text,text),public.remove_workspace_dot(uuid,uuid,integer) from public,anon;
grant execute on function public.save_workspace_dot(uuid,uuid,integer,text,text,text,text,text),public.remove_workspace_dot(uuid,uuid,integer) to authenticated;
create or replace function aedrova_private.guard_builder_dot_name() returns trigger
language plpgsql security definer set search_path='' as $$
begin
 if exists(select 1 from public.workspace_dots where workspace_id=new.workspace_id and deleted_at is null and lower(name)=lower(new.nickname)) then raise exception 'Builder nickname is reserved by a Dot'; end if;
 return new;
end $$;
revoke all on function aedrova_private.guard_builder_dot_name() from public,anon,authenticated;
create trigger guard_builder_dot_name before insert or update of nickname on public.workspace_agent_preferences for each row execute function aedrova_private.guard_builder_dot_name();
-- Preserve connected resource identities. No local Keychain token is copied or uploaded.
insert into public.workspace_dots(workspace_id,provider,resource,name,color,shape,created_by)
select t.workspace_id,c->>'tool',c->>'resource',
 case when row_number() over(partition by t.workspace_id,c->>'tool' order by t.updated_at,t.id)=1 then case c->>'tool' when 'github' then 'GitHub' when 'figma' then 'Figma' else 'Notion' end else case c->>'tool' when 'github' then 'GitHub' when 'figma' then 'Figma' else 'Notion' end||' '||substr(t.id::text,1,6) end,
 coalesce(t.config->>'color','#4388F5'),coalesce(t.config->>'shape','round'),t.created_by
from public.ai_teammates t cross join lateral jsonb_array_elements(coalesce(t.config->'connections','[]'::jsonb)) c
where t.deleted_at is null and c->>'tool' in ('github','figma','notion')
on conflict do nothing;
-- Retain legacy records for recovery; the application no longer routes assignments to them.
comment on table public.ai_teammates is 'Deprecated prototype; connections migrated to workspace_dots. Legacy builds must be reviewed, never silently resumed.';
commit;
