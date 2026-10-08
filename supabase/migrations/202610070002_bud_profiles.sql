-- Buds presentation reuses existing Dot identities, grants and mention tokens.
begin;
alter table public.workspace_dots add column if not exists role text not null default '';
alter table public.workspace_dots add column if not exists instructions text not null default '';
alter table public.workspace_dots drop constraint if exists bud_role_length;
alter table public.workspace_dots add constraint bud_role_length check(length(role)<=240);
alter table public.workspace_dots drop constraint if exists bud_instructions_length;
alter table public.workspace_dots add constraint bud_instructions_length check(length(instructions)<=2000);
create or replace function public.save_workspace_bud(
 p_id uuid,p_workspace uuid,p_version integer,p_provider text,p_resource text,p_name text,
 p_color text default '#4388F5',p_shape text default 'round',
 p_role text default '',p_instructions text default ''
) returns public.workspace_dots language plpgsql security definer set search_path='' as $$
declare r public.workspace_dots;
begin
 if p_role is null or p_instructions is null or length(p_role)>240 or length(p_instructions)>2000 then
  raise exception 'Keep the Bud purpose under 240 characters and instructions under 2000';
 end if;
 -- Existing RPC enforces fresh owner/admin, rate limit, immutable resource,
 -- optimistic version, maximum Bud count and validated identity values.
 select * into r from public.save_workspace_dot(p_id,p_workspace,p_version,p_provider,p_resource,p_name,p_color,p_shape);
 update public.workspace_dots set role=p_role,instructions=p_instructions where id=r.id returning * into r;
 return r;
end $$;
revoke all on function public.save_workspace_bud(uuid,uuid,integer,text,text,text,text,text,text,text) from public,anon;
grant execute on function public.save_workspace_bud(uuid,uuid,integer,text,text,text,text,text,text,text) to authenticated;
commit;
