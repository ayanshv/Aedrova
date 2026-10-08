-- Run after 202610070002_bud_profiles.sql. No change to access or provider authority.
begin;
alter table public.workspace_dots add column if not exists appearance text not null default 'auto';
alter table public.workspace_dots drop constraint if exists bud_appearance_valid;
alter table public.workspace_dots add constraint bud_appearance_valid
 check(appearance in ('auto','builder','designer','marketing','finance','research','product'));
create or replace function public.save_workspace_bud_appearance(
 p_id uuid,p_workspace uuid,p_version integer,p_provider text,p_resource text,p_name text,
 p_color text default '#4388F5',p_shape text default 'round',
 p_role text default '',p_instructions text default '',p_appearance text default 'auto'
) returns public.workspace_dots language plpgsql security definer set search_path='' as $$
declare r public.workspace_dots;
begin
 if p_appearance is null or p_appearance not in ('auto','builder','designer','marketing','finance','research','product') then
  raise exception 'Choose a supported Bud appearance';
 end if;
 select * into r from public.save_workspace_bud(p_id,p_workspace,p_version,p_provider,p_resource,p_name,p_color,p_shape,p_role,p_instructions);
 update public.workspace_dots set appearance=p_appearance where id=r.id returning * into r;
 return r;
end $$;
revoke all on function public.save_workspace_bud_appearance(uuid,uuid,integer,text,text,text,text,text,text,text,text) from public,anon;
grant execute on function public.save_workspace_bud_appearance(uuid,uuid,integer,text,text,text,text,text,text,text,text) to authenticated;
commit;
