begin;
create table public.ai_teammates (
 id uuid primary key, workspace_id uuid not null references public.workspaces(id) on delete cascade,
 config jsonb not null, version integer not null default 1,
 paused boolean not null default false, deleted_at timestamptz,
 created_by uuid not null references auth.users(id), updated_at timestamptz not null default clock_timestamp(),
 check(octet_length(config::text)<=12000)
);
create unique index ai_teammate_names on public.ai_teammates(workspace_id,lower(config->>'name')) where deleted_at is null;
alter table public.ai_teammates enable row level security;
revoke all on public.ai_teammates from public,anon,authenticated;
grant select on public.ai_teammates to authenticated;
create policy ai_teammate_read on public.ai_teammates for select to authenticated
 using(aedrova_private.member_role(workspace_id) is not null and deleted_at is null);
create function public.save_ai_teammate(p_id uuid,p_workspace uuid,p_version integer,p_config jsonb,p_paused boolean default false)
returns integer language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); old public.ai_teammates; v integer;
begin
 perform aedrova_private.check_user_budget('teammate-settings',30,60);
 perform 1 from public.workspaces where id=p_workspace for update;
 if coalesce(aedrova_private.member_role(p_workspace),'') not in ('owner','admin') then
 raise exception 'Owner or admin required' using errcode='42501'; end if;
 if coalesce(jsonb_typeof(p_config),'')<>'object' or octet_length(p_config::text)>12000
 or coalesce(p_config->>'name','') !~ '^[A-Za-z][A-Za-z0-9_-]{0,23}$'
 or lower(p_config->>'name') in ('aedrova','channel','everyone')
 or exists(select 1 from public.workspace_agent_preferences where workspace_id=p_workspace and lower(nickname)=lower(p_config->>'name'))
 or coalesce(p_config->>'role','') not in ('engineering','product','research')
 or coalesce(p_config->>'shape','') not in ('round','squircle','cloud')
 or coalesce(p_config->>'color','') !~ '^#[A-Fa-f0-9]{6}$'
 or coalesce(p_config->>'personality','') not in ('concise','supportive','analytical')
 or coalesce(p_config->>'reporting','') not in ('quiet','milestones','detailed')
 or coalesce(p_config->>'effort','') not in ('quick','balanced','deep')
 or coalesce(p_config->>'importance','') not in ('normal','important','critical')
 or coalesce(char_length(trim(p_config->>'responsibilities')),0) not between 1 and 2000
 or p_config::text ~ '(sb_secret_|sk-(proj-|ant-)|[sr]k_(live|test)_|whsec_|gh[pousr]_)[A-Za-z0-9_-]{20,}|-----BEGIN .*PRIVATE KEY-----'
 then raise exception 'Invalid teammate settings or reserved name' using errcode='22023'; end if;
 select * into old from public.ai_teammates where id=p_id for update;
 if old.id is not null and (old.workspace_id<>p_workspace or old.deleted_at is not null) then
 raise exception 'Identity unavailable' using errcode='42501'; end if;
 if old.id is not null and old.version=p_version+1 and old.config=p_config and old.paused=p_paused then return old.version; end if;
 if coalesce(old.version,0) is distinct from p_version then raise exception 'Teammate changed. Refresh first.' using errcode='PT409'; end if;
 if old.id is null and (select count(*) from public.ai_teammates where workspace_id=p_workspace and deleted_at is null)>=12 then
 raise exception 'Limit of 12 teammates per workspace' using errcode='22023'; end if;
 v:=coalesce(old.version,0)+1;
 insert into public.ai_teammates(id,workspace_id,config,version,paused,created_by)
 values(p_id,p_workspace,p_config,v,p_paused,u)
 on conflict(id) do update set config=excluded.config,version=excluded.version,paused=excluded.paused,updated_at=clock_timestamp();
 return v;
end $$;
create function public.remove_ai_teammate(p_id uuid,p_version integer) returns void
language plpgsql security definer set search_path='' as $$
declare old public.ai_teammates;
begin
 perform aedrova_private.require_user();
 select * into old from public.ai_teammates where id=p_id;
 perform 1 from public.workspaces where id=old.workspace_id for update;
 select * into old from public.ai_teammates where id=p_id for update;
 if old.id is null or coalesce(aedrova_private.member_role(old.workspace_id),'') not in ('owner','admin') then
 raise exception 'Owner or admin required' using errcode='42501'; end if;
 if old.version is distinct from p_version then raise exception 'Teammate changed. Refresh first.' using errcode='PT409'; end if;
 update public.ai_teammates set deleted_at=clock_timestamp(),version=version+1 where id=p_id;
end $$;
revoke all on function public.save_ai_teammate(uuid,uuid,integer,jsonb,boolean),public.remove_ai_teammate(uuid,integer) from public,anon;
grant execute on function public.save_ai_teammate(uuid,uuid,integer,jsonb,boolean),public.remove_ai_teammate(uuid,integer) to authenticated;
-- Both settings RPCs lock the workspace, preventing concurrent name collisions.
create function aedrova_private.guard_builder_teammate_name() returns trigger
language plpgsql security definer set search_path='' as $$
begin
 if exists(select 1 from public.ai_teammates where workspace_id=new.workspace_id
  and deleted_at is null and lower(config->>'name')=lower(new.nickname)) then
  raise exception 'Name already belongs to an AI teammate' using errcode='22023';
 end if;
 return new;
end $$;
revoke all on function aedrova_private.guard_builder_teammate_name() from public,anon,authenticated;
create trigger builder_teammate_name before insert or update of nickname
on public.workspace_agent_preferences for each row execute function aedrova_private.guard_builder_teammate_name();
commit;
