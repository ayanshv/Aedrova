begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('f5000000-0000-0000-0000-000000000001','connector-owner@test.local',now()),
 ('f5000000-0000-0000-0000-000000000002','connector-member@test.local',now());
create or replace function pg_temp.check_true(ok boolean,description text) returns void language plpgsql as $$
begin if ok is distinct from true then raise exception 'FAIL: %',description; end if; end $$;
create or replace function pg_temp.denied(statement text,code text default 'P0001') returns void language plpgsql as $$
declare actual text;
begin begin execute statement; exception when others then get stacked diagnostics actual=returned_sqlstate;
 if actual=code then return; end if; raise; end; raise exception 'FAIL: unauthorized action succeeded'; end $$;
set local role authenticated;
set local request.jwt.claim.sub='f5000000-0000-0000-0000-000000000001';
select set_config('test.w',public.onboard_workspace('Connector acceptance','Aedrova','codex')::text,true);
select set_config('test.dot',(public.save_workspace_bud_appearance(null,current_setting('test.w')::uuid,0,'search','AI team workspaces','Scout','#4388F5','round','Research','Use evidence','research')).id::text,true);
select pg_temp.check_true((select provider='search' and resource='AI team workspaces' from public.workspace_dots),'Search topics allow spaces');
select public.save_workspace_bud_appearance(null,current_setting('test.w')::uuid,0,'instagram','123456789','Social','#4388F5','round','Marketing','','marketing');
select public.save_workspace_bud_appearance(null,current_setting('test.w')::uuid,0,'tiktok','openid123','Videos');
select public.save_workspace_bud_appearance(null,current_setting('test.w')::uuid,0,'linear','00000000-0000-0000-0000-000000000001','Roadmap');
select pg_temp.denied($q$select public.save_workspace_bud_appearance(null,current_setting('test.w')::uuid,0,'unknown','x','Invalid')$q$);
select pg_temp.denied($q$select public.save_workspace_bud_appearance(null,current_setting('test.w')::uuid,0,'notion','with spaces','Invalid')$q$);
select pg_temp.denied($q$select public.save_workspace_bud_appearance(null,current_setting('test.w')::uuid,0,'search','https://evil.test','Invalid')$q$);
select pg_temp.denied($q$select public.save_workspace_bud_appearance(current_setting('test.dot')::uuid,current_setting('test.w')::uuid,1,'figma','fileKey','Scout')$q$,'PT409');
select set_config('test.invite',public.create_invitation(current_setting('test.w')::uuid,'connector-member@test.local','member'),true);
set local request.jwt.claim.sub='f5000000-0000-0000-0000-000000000002';
select pg_temp.check_true((select count(*)=0 from public.workspace_dots),'outsider isolation');
select public.accept_invitation(current_setting('test.invite'));
select pg_temp.denied($q$select public.save_workspace_bud_appearance(null,current_setting('test.w')::uuid,0,'search','AI products','Member')$q$);
select pg_temp.denied('delete from public.workspace_dots','42501');
rollback;
