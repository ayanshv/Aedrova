begin;
-- First-use progress is presentation state, never a source of access authority.
create table public.first_use_progress (
 user_id uuid primary key references auth.users on delete cascade,
 revision bigint not null default 0,
 stage integer not null default 1 check(stage between 1 and 5),
 draft jsonb not null default '{}' check(jsonb_typeof(draft)='object' and octet_length(draft::text)<=16000),
 workspace_id uuid references public.workspaces on delete set null,
 buds jsonb not null default '{}',
 invitations jsonb not null default '{}',
 first_message_id uuid,
 ai_reviewed_at timestamptz,
 completed_at timestamptz,
 updated_at timestamptz not null default now()
);
alter table public.first_use_progress enable row level security;
revoke all on public.first_use_progress from public,anon,authenticated;
grant select on public.first_use_progress to authenticated;
create policy first_use_read on public.first_use_progress for select to authenticated
 using(user_id=(select auth.uid()));

create table public.workspace_identity (
 workspace_id uuid primary key references public.workspaces on delete cascade,
 icon text not null check(icon in ('spaces','folder','context','work','smile','search')),
 purpose text not null,
 description text not null check(length(description)<=2000)
);
alter table public.workspace_identity enable row level security;
revoke all on public.workspace_identity from public,anon,authenticated;
grant select on public.workspace_identity to authenticated;
create policy workspace_identity_read on public.workspace_identity for select to authenticated
 using(aedrova_private.member_role(workspace_id) is not null);

create function public.get_first_use_progress() returns jsonb
language sql stable security definer set search_path='' as $$
 select coalesce((select to_jsonb(p)-'user_id' from public.first_use_progress p
 where p.user_id=aedrova_private.require_user()),'{}'::jsonb)
$$;

create function public.save_first_use_progress(p_revision bigint,p_stage integer,p_draft jsonb)
returns jsonb language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); r public.first_use_progress;
begin
 perform aedrova_private.check_user_budget('first_use',90,60);
 if p_revision is null or p_revision<0 or p_stage is null or p_stage not between 1 and 5
 or p_draft is null or jsonb_typeof(p_draft)<>'object' or octet_length(p_draft::text)>16000
 or p_draft - array['name','icon','purpose','description','goal','selected_roles','automatic'] <> '{}'::jsonb
 or exists(select 1 from jsonb_each(p_draft) f where f.key in ('name','icon','purpose','description','goal') and jsonb_typeof(f.value)<>'string')
 or length(coalesce(p_draft->>'name',''))>80
 or length(coalesce(p_draft->>'description',''))>2000
 or length(coalesce(p_draft->>'goal',''))>4000
 or coalesce(p_draft->>'icon','spaces') not in ('spaces','folder','context','work','smile','search')
 or coalesce(p_draft->>'purpose','software') not in ('software','design','research','marketing','operations','personal')
 or (p_draft ? 'automatic' and jsonb_typeof(p_draft->'automatic')<>'boolean')
 or (p_draft ? 'selected_roles' and (jsonb_typeof(p_draft->'selected_roles')<>'array'
 or jsonb_array_length(p_draft->'selected_roles')>6))
 then raise exception 'Check your setup details' using errcode='22023'; end if;
 if p_draft ? 'selected_roles' then
  if exists(select 1 from jsonb_array_elements(p_draft->'selected_roles') v where jsonb_typeof(v)<>'string' or v #>> '{}' not in ('builder','designer','marketing','finance','research','product')) then
   raise exception 'Choose supported Buds' using errcode='22023'; end if;
 end if;
 if exists(select 1 from public.first_use_progress p where p.user_id=u and
   (p.revision<>p_revision or p.completed_at is not null)) then
  raise exception 'Setup changed on another device. Reload to continue.' using errcode='40001'; end if;
 -- Workflow authority was explicitly reviewed at Space creation. Draft edits
 -- on another device cannot silently increase that recorded authority.
 if exists(select 1 from public.first_use_progress p where p.user_id=u and p.workspace_id is not null and coalesce(p.draft->'automatic','false'::jsonb) is distinct from coalesce(p_draft->'automatic','false'::jsonb)) then
  raise exception 'Change workflow permissions in workspace settings' using errcode='22023'; end if;
 if exists(select 1 from public.first_use_progress p where p.user_id=u and p.workspace_id is not null
   and (p.draft - array['goal','selected_roles']) is distinct from (p_draft - array['goal','selected_roles'])) then
  raise exception 'Change Space details in workspace settings' using errcode='22023'; end if;
 insert into public.first_use_progress(user_id,revision,stage,draft)
 values(u,1,p_stage,p_draft)
 on conflict(user_id) do update set revision=first_use_progress.revision+1,
 stage=excluded.stage,draft=excluded.draft,updated_at=now()
 where first_use_progress.revision=p_revision and first_use_progress.completed_at is null
 returning * into r;
 if not found then raise exception 'Setup changed on another device. Reload to continue.' using errcode='40001'; end if;
 if p_revision<>0 and r.revision=1 then raise exception 'Setup changed on another device' using errcode='40001'; end if;
 return to_jsonb(r)-'user_id';
end $$;

create function public.create_first_use_space(p_parent uuid default null,p_allow_ai boolean default false) returns jsonb
language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); r public.first_use_progress; w uuid;
begin
 select * into r from public.first_use_progress where user_id=u for update;
 if not found then raise exception 'Save your setup before creating a Space' using errcode='22023'; end if;
 if r.workspace_id is not null then
  if aedrova_private.member_role(r.workspace_id) is null then raise exception 'Space unavailable' using errcode='42501'; end if;
  return to_jsonb(r)-'user_id';
 end if;
 if length(btrim(coalesce(r.draft->>'name',''))) not between 1 and 80
 then raise exception 'Give your Space a name' using errcode='22023'; end if;
 if p_allow_ai is distinct from true then raise exception 'Review and allow AI setup' using errcode='22023'; end if;
 if p_parent is null then
  w:=public.onboard_workspace(r.draft->>'name','Aedrova','auto');
 else
  w:=public.create_subspace(p_parent,r.draft->>'name');
  perform public.set_agent_preferences(w,'Aedrova','auto');
 end if;
 insert into public.workspace_identity(workspace_id,icon,purpose,description)
 values(w,coalesce(r.draft->>'icon','spaces'),coalesce(r.draft->>'purpose','software'),coalesce(r.draft->>'description',''));
 update public.first_use_progress set workspace_id=w,stage=2,ai_reviewed_at=now(),revision=revision+1,updated_at=now()
 where user_id=u returning * into r;
 return to_jsonb(r)-'user_id';
end $$;

create function public.activate_first_use_buds(p_roles text[]) returns jsonb
language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); r public.first_use_progress;
 role_name text; existing uuid; b public.workspace_dots;
begin
 select * into r from public.first_use_progress where user_id=u for update;
 if not found or r.workspace_id is null then raise exception 'Create your Space first' using errcode='22023'; end if;
 if coalesce(aedrova_private.member_role(r.workspace_id),'') not in ('owner','admin')
 then raise exception 'Space unavailable' using errcode='42501'; end if;
 if p_roles is null or cardinality(p_roles)>6 or array_position(p_roles,null) is not null
 or not p_roles <@ array['builder','designer','marketing','finance','research','product']::text[]
 then raise exception 'Choose supported Buds' using errcode='22023'; end if;
 foreach role_name in array p_roles loop
  existing:=nullif(r.buds->>role_name,'')::uuid;
  if existing is not null and exists(select 1 from public.workspace_dots
    where id=existing and workspace_id=r.workspace_id and deleted_at is null) then continue; end if;
  -- A disconnected identity does not grant GitHub or any external account access.
  -- The existing save RPC retains fresh permissions, concurrency and plan caps.
  select * into b from public.save_workspace_bud_appearance(null,r.workspace_id,0,
   'github','selection/pending',initcap(role_name),'#4388F5','round',initcap(role_name),
   'Help with '||role_name||' assignments. Use only context explicitly available to you. '
   ||'No external tool is connected until its account is authorized.',role_name);
  r.buds:=r.buds||jsonb_build_object(role_name,b.id);
 end loop;
 update public.first_use_progress set buds=r.buds,revision=revision+1,updated_at=now()
 where user_id=u returning * into r;
 return to_jsonb(r)-'user_id';
end $$;

create function public.invite_first_use_teammate(p_email text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); r public.first_use_progress;
 address text:=lower(btrim(p_email)); token text; invitation uuid;
begin
 select * into r from public.first_use_progress where user_id=u for update;
 if not found or r.workspace_id is null then raise exception 'Create your Space first' using errcode='22023'; end if;
 if coalesce(aedrova_private.member_role(r.workspace_id),'') not in ('owner','admin')
 then raise exception 'Space unavailable' using errcode='42501'; end if;
 if address is null or address !~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'
 or length(address)>320 then raise exception 'Enter a teammate email' using errcode='22023'; end if;
 if r.invitations ? address then
  return jsonb_build_object('progress',to_jsonb(r)-'user_id','email',address,'created',false);
 end if;
 if (select count(*) from jsonb_object_keys(r.invitations))>=10 then raise exception 'Invite more people in workspace settings' using errcode='54000'; end if;
 token:=public.create_invitation(r.workspace_id,address,'member');
 select id into invitation from public.workspace_invitations where workspace_id=r.workspace_id
 and email=address and invited_by=u order by expires_at desc,id desc limit 1;
 update public.first_use_progress set invitations=invitations||jsonb_build_object(address,invitation),
 revision=revision+1,updated_at=now() where user_id=u returning * into r;
 -- A code is returned once and is never persisted in onboarding progress.
 return jsonb_build_object('progress',to_jsonb(r)-'user_id','email',address,'created',true,'code',token);
end $$;

create function public.complete_first_use(p_goal text) returns jsonb
language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); r public.first_use_progress; c uuid; m uuid;
begin
 select * into r from public.first_use_progress where user_id=u for update;
 if not found or r.workspace_id is null then raise exception 'Create your Space first' using errcode='22023'; end if;
 if coalesce(aedrova_private.member_role(r.workspace_id),'') not in ('owner','admin','member')
 then raise exception 'Space unavailable' using errcode='42501'; end if;
 if r.completed_at is not null then return to_jsonb(r)-'user_id'; end if;
 if p_goal is null or length(btrim(p_goal)) not between 1 and 4000
 then raise exception 'Describe your first project in 1 to 4000 characters' using errcode='22023'; end if;
 select id into c from public.channels where workspace_id=r.workspace_id and kind='channel'
 and not private order by (name='general') desc,name,id limit 1;
 if c is null then raise exception 'Your first channel is unavailable. Refresh your Space.' using errcode='42501'; end if;
 m:=gen_random_uuid();
 perform public.send_message(m,c,btrim(p_goal),null);
 update public.first_use_progress set first_message_id=m,completed_at=now(),stage=5,
 draft=draft||jsonb_build_object('goal',btrim(p_goal)),revision=revision+1,updated_at=now()
 where user_id=u returning * into r;
 return to_jsonb(r)-'user_id';
end $$;

revoke all on function public.get_first_use_progress(),public.save_first_use_progress(bigint,integer,jsonb),
 public.create_first_use_space(uuid,boolean),public.activate_first_use_buds(text[]),
 public.invite_first_use_teammate(text),public.complete_first_use(text) from public,anon;
grant execute on function public.get_first_use_progress(),public.save_first_use_progress(bigint,integer,jsonb),
 public.create_first_use_space(uuid,boolean),public.activate_first_use_buds(text[]),
 public.invite_first_use_teammate(text),public.complete_first_use(text) to authenticated;
commit;
