begin;
-- Additive: existing workspaces stay independent; no subscription or usage changes.
create table public.workspace_parents (
 workspace_id uuid primary key references public.workspaces(id),
 parent_id uuid not null references public.workspaces(id),
 check(workspace_id<>parent_id)
);
create index workspace_parent_children on public.workspace_parents(parent_id);
create table aedrova_private.space_limits (
 singleton boolean primary key default true check(singleton),
 max_depth integer not null default 4 check(max_depth between 1 and 16),
 max_subspaces integer not null default 100 check(max_subspaces between 1 and 10000)
);
insert into aedrova_private.space_limits default values;
revoke all on aedrova_private.space_limits from public,anon,authenticated;
alter table public.workspace_parents enable row level security;
revoke all on public.workspace_parents from public,anon,authenticated;
grant select on public.workspace_parents to authenticated;
create policy space_parent_read on public.workspace_parents for select to authenticated
 using(aedrova_private.member_role(workspace_id) is not null
 and aedrova_private.member_role(parent_id) is not null);
create function aedrova_private.billing_root(w uuid) returns uuid
language plpgsql stable security definer set search_path='' as $$
declare cur uuid:=w; next_id uuid; seen uuid[]:='{}';
begin
 loop
  if cur=any(seen) or cardinality(seen)>=16 then
   raise exception 'Invalid Space hierarchy' using errcode='22023'; end if;
  seen:=array_append(seen,cur);
  if not exists(select 1 from public.workspaces where id=cur) then
   raise exception 'Space unavailable' using errcode='42501'; end if;
  select parent_id into next_id from public.workspace_parents where workspace_id=cur;
  if next_id is null then return cur; end if;
  cur:=next_id;
 end loop;
end $$;
create function public.space_billing_context(p_workspace uuid) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); root uuid; r text; par uuid;
begin
 root:=aedrova_private.billing_root(p_workspace);
 if aedrova_private.member_role(p_workspace) is null or aedrova_private.member_role(root) is null
 then raise exception 'Space unavailable' using errcode='42501'; end if;
 r:=aedrova_private.member_role(root);
 select parent_id into par from public.workspace_parents where workspace_id=p_workspace;
 return jsonb_build_object('workspace',p_workspace,'billing_workspace',root,'parent_id',par,
 'billing_name',(select name from public.workspaces where id=root),
 'billing_role',r,'can_manage_billing',r in ('owner','admin'),'user_id',u);
end $$;
create function public.create_subspace(p_parent uuid,p_name text) returns uuid
language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); root uuid; w uuid; depth integer; n integer;
 lim aedrova_private.space_limits;
begin
 perform pg_advisory_xact_lock(73114013);
 root:=aedrova_private.billing_root(p_parent);
 if coalesce(aedrova_private.member_role(p_parent),'') not in ('owner','admin')
 or coalesce(aedrova_private.member_role(root),'') not in ('owner','admin')
 then raise exception 'Only authorized Space owners or admins can create subspaces' using errcode='42501'; end if;
 select * into lim from aedrova_private.space_limits;
 with recursive ancestors(id,d) as (select p_parent,1 union all
 select p.parent_id,a.d+1 from ancestors a join public.workspace_parents p on p.workspace_id=a.id)
 select max(d) into depth from ancestors;
 with recursive children(id) as (select root union all
 select p.workspace_id from children c join public.workspace_parents p on p.parent_id=c.id)
 select count(*)-1 into n from children;
 if depth>=lim.max_depth or n>=lim.max_subspaces then
 raise exception 'Space nesting or subspace limit reached' using errcode='54000'; end if;
 perform aedrova_private.check_user_budget('create_subspace',5,60);
 w:=public.create_workspace(p_name);
 insert into public.workspace_parents values(w,p_parent);
 -- Access is explicit, not inherited: inviting to a subspace never grants parent access.
 return w;
end $$;
create function public.move_subspace(p_workspace uuid,p_parent uuid,p_expected_parent uuid)
returns uuid language plpgsql security definer set search_path='' as $$
declare old_root uuid; new_root uuid; current_parent uuid; lim aedrova_private.space_limits;
 parent_depth integer; subtree_depth integer; total integer; added integer;
begin
 perform aedrova_private.require_user();
 perform pg_advisory_xact_lock(73114013);
 select parent_id into current_parent from public.workspace_parents where workspace_id=p_workspace;
 if current_parent is null or current_parent is distinct from p_expected_parent then
 raise exception 'Subspace changed. Refresh before moving.' using errcode='40001'; end if;
 perform aedrova_private.check_user_budget('move_subspace',5,60);
 old_root:=aedrova_private.billing_root(p_workspace); new_root:=aedrova_private.billing_root(p_parent);
 if aedrova_private.member_role(old_root) is distinct from 'owner'
 or aedrova_private.member_role(new_root) is distinct from 'owner'
 or aedrova_private.member_role(p_workspace) is distinct from 'owner'
 or coalesce(aedrova_private.member_role(p_parent),'') not in ('owner','admin') then
 raise exception 'Both billing Space owners must authorize the move' using errcode='42501'; end if;
 if exists(with recursive children(id) as (select p_workspace union all
 select p.workspace_id from children c join public.workspace_parents p on p.parent_id=c.id)
 select 1 from children where id=p_parent) then
 raise exception 'A subspace cannot contain its parent' using errcode='22023'; end if;
 select * into lim from aedrova_private.space_limits;
 with recursive ancestors(id,d) as (select p_parent,1 union all
 select p.parent_id,a.d+1 from ancestors a join public.workspace_parents p on p.workspace_id=a.id)
 select max(d) into parent_depth from ancestors;
 with recursive children(id,d) as (select p_workspace,1 union all
 select p.workspace_id,c.d+1 from children c join public.workspace_parents p on p.parent_id=c.id)
 select max(d),count(*) into subtree_depth,added from children;
 with recursive children(id) as (select new_root union all
 select p.workspace_id from children c join public.workspace_parents p on p.parent_id=c.id)
 select count(*)-1 into total from children;
 if parent_depth+subtree_depth>lim.max_depth
 or total+(case when new_root=old_root then 0 else added end)>lim.max_subspaces then
 raise exception 'Space nesting or subspace limit reached' using errcode='54000'; end if;
 -- Require all subtree members to already belong to the destination billing Space.
 if exists(with recursive children(id) as (select p_workspace union all
 select p.workspace_id from children c join public.workspace_parents p on p.parent_id=c.id)
 select 1 from public.workspace_members m join children c on c.id=m.workspace_id
 where not exists(select 1 from public.workspace_members r where r.workspace_id=new_root and r.user_id=m.user_id)) then
 raise exception 'Invite subspace members to the destination Space before moving' using errcode='42501'; end if;
 update public.workspace_parents set parent_id=p_parent where workspace_id=p_workspace;
 return p_workspace;
end $$;
revoke all on function aedrova_private.billing_root(uuid) from public,anon,authenticated;
revoke all on function public.space_billing_context(uuid),public.create_subspace(uuid,text),
 public.move_subspace(uuid,uuid,uuid) from public,anon;
grant execute on function public.space_billing_context(uuid),public.create_subspace(uuid,text),
 public.move_subspace(uuid,uuid,uuid) to authenticated;
create function public.resolve_billing_space_for_backend(p_workspace uuid,p_user uuid)
returns uuid language plpgsql stable security definer set search_path='' as $$
declare root uuid;
begin
 root:=aedrova_private.billing_root(p_workspace);
 if not exists(select 1 from public.workspace_members where workspace_id=p_workspace and user_id=p_user)
 or not exists(select 1 from public.workspace_members where workspace_id=root and user_id=p_user)
 then raise exception 'Space unavailable' using errcode='42501'; end if;
 return root;
end $$;
revoke all on function public.resolve_billing_space_for_backend(uuid,uuid) from public,anon,authenticated;
do $$begin
 if exists(select 1 from pg_roles where rolname='aedrova_website') then
 grant usage on schema public to aedrova_website;
 grant execute on function public.resolve_billing_space_for_backend(uuid,uuid) to aedrova_website;
 end if;
end$$;
commit;
