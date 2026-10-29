begin;
-- Billing is private and backend verified. No client-supplied tier or editable quota.
create table aedrova_private.enterprise_bud_limits (
 workspace_id uuid primary key references public.workspaces(id),
 capacity integer not null check(capacity between 1 and 10000)
);
revoke all on aedrova_private.enterprise_bud_limits from public,anon,authenticated;

create function aedrova_private.bud_capacity(w uuid) returns jsonb
language plpgsql volatile security definer set search_path='' as $$
declare root uuid:=aedrova_private.billing_root(w); bill jsonb; tier text:='free';
 lim integer:=1; used integer; epoch bigint:=extract(epoch from now())::bigint;
begin
 if to_regclass('aedrova_billing.billing') is not null then
  execute 'select to_jsonb(b) from aedrova_billing.billing b where workspace=$1'
  into bill using root::text;
 end if;
 if bill->>'status' in ('active','trialing')
 and coalesce((bill->>'period_end')::bigint,0)>epoch
 and coalesce((bill->>'period_start')::bigint,0)<=epoch then
  case bill->>'plan'
   when 'monthly' then tier:='pro'; lim:=5;
   when 'annual' then tier:='team'; lim:=15;
   when 'enterprise' then
    tier:='enterprise';
    select capacity into lim from aedrova_private.enterprise_bud_limits where workspace_id=root;
    lim:=coalesce(lim,0);
   else null;
  end case;
 end if;
 with recursive spaces(id) as (select root union all
 select p.workspace_id from public.workspace_parents p join spaces s on p.parent_id=s.id)
 select count(*) into used from public.workspace_dots d join spaces s on d.workspace_id=s.id
 where d.deleted_at is null;
 return jsonb_build_object('plan',tier,'limit',lim,'used',used,'remaining',greatest(0,lim-used));
end $$;
revoke all on function aedrova_private.bud_capacity(uuid) from public,anon,authenticated;

create function public.workspace_bud_capacity(p_workspace uuid) returns jsonb
language plpgsql stable security definer set search_path='' as $$
begin
 perform aedrova_private.require_user();
 if aedrova_private.member_role(p_workspace) is null then
 raise exception 'Workspace unavailable' using errcode='42501'; end if;
 return aedrova_private.bud_capacity(p_workspace);
end $$;
revoke all on function public.workspace_bud_capacity(uuid) from public,anon;
grant execute on function public.workspace_bud_capacity(uuid) to authenticated;

create function aedrova_private.enforce_bud_capacity() returns trigger
language plpgsql security definer set search_path='' as $$
declare capacity jsonb; root uuid;
begin
 if new.deleted_at is not null then return new; end if;
 if tg_op='UPDATE' and old.deleted_at is null and old.workspace_id=new.workspace_id then
 return new; end if;
 root:=aedrova_private.billing_root(new.workspace_id);
 -- One lock for the subscription, including subspaces and concurrent creators.
 perform pg_advisory_xact_lock(hashtextextended(root::text,73124001));
 capacity:=aedrova_private.bud_capacity(new.workspace_id);
 if (capacity->>'used')::integer >= (capacity->>'limit')::integer then
 raise exception 'Your % plan allows % Buds. Remove a Bud or change your team plan to add another.',
 initcap(capacity->>'plan'),capacity->>'limit' using errcode='54000'; end if;
 return new;
end $$;
revoke all on function aedrova_private.enforce_bud_capacity() from public,anon,authenticated;
create trigger workspace_bud_capacity before insert or update of workspace_id,deleted_at
 on public.workspace_dots for each row execute function aedrova_private.enforce_bud_capacity();
-- Replace the old universal cap of 12; the atomic trigger applies all plan caps.
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
  if p_version<>0 then raise exception 'Invalid new Bud version'; end if;
  insert into public.workspace_dots(workspace_id,provider,resource,name,color,shape,created_by) values(p_workspace,p_provider,p_resource,p_name,p_color,p_shape,u) returning * into r;
 else
  update public.workspace_dots set name=p_name,color=p_color,shape=p_shape,version=version+1,updated_at=now()
  where id=p_id and workspace_id=p_workspace and version=p_version and provider=p_provider and resource=p_resource and deleted_at is null returning * into r;
  if not found then raise sqlstate 'PT409' using message='Dot changed. Refresh before saving.'; end if;
 end if;
 return r;
end $$;

commit;
