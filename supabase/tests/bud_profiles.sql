begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('f3000000-0000-0000-0000-000000000001','dot-owner@test.local',now()),
 ('f3000000-0000-0000-0000-000000000002','dot-member@test.local',now());
create or replace function pg_temp.check_true(ok boolean,description text) returns void language plpgsql as $$
begin if ok is distinct from true then raise exception 'FAIL: %',description; end if; end $$;
create or replace function pg_temp.denied(statement text,code text default 'P0001') returns void language plpgsql as $$
declare actual text;
begin begin execute statement; exception when others then get stacked diagnostics actual=returned_sqlstate;
 if actual=code then return; end if; raise; end; raise exception 'FAIL: unauthorized action succeeded'; end $$;
set local role authenticated;
set local request.jwt.claim.sub='f3000000-0000-0000-0000-000000000001';
select set_config('test.w',public.onboard_workspace('Dot acceptance','Aedrova','codex')::text,true);
select set_config('test.dot',(public.save_workspace_bud(null,current_setting('test.w')::uuid,0,'github','owner/repo','GitHub','#4388F5','cloud','Engineering updates','Focus on pull requests')).id::text,true);
select pg_temp.check_true((select role='Engineering updates' and instructions='Focus on pull requests' and shape='cloud' from public.workspace_dots),'Bud purpose and instructions persist');
select pg_temp.denied($q$select public.save_workspace_bud(null,current_setting('test.w')::uuid,0,'github','owner/other','Other','#4388F5','round',repeat('x',241),'')$q$);
select pg_temp.denied($q$select public.save_workspace_bud(null,current_setting('test.w')::uuid,0,'github','owner/other','Other','#4388F5','round','',repeat('x',2001))$q$);
select pg_temp.denied($q$select public.save_workspace_bud(null,current_setting('test.w')::uuid,0,'github','owner/repo','Another')$q$,'23505');
select pg_temp.denied($q$select public.save_workspace_bud(null,current_setting('test.w')::uuid,0,'github','https://evil.com','Other')$q$);
select pg_temp.denied($q$select public.save_workspace_bud(null,current_setting('test.w')::uuid,0,'github','owner/new','Aedrova')$q$);
select pg_temp.denied($q$select public.set_agent_preferences(current_setting('test.w')::uuid,'github','codex')$q$);
select pg_temp.check_true((public.save_workspace_bud(current_setting('test.dot')::uuid,current_setting('test.w')::uuid,1,'github','owner/repo','Code')).version=2,'versioned identity');
select pg_temp.denied($q$select public.remove_workspace_dot(current_setting('test.dot')::uuid,current_setting('test.w')::uuid,1)$q$,'PT409');
select set_config('test.invite',public.create_invitation(current_setting('test.w')::uuid,'dot-member@test.local','member'),true);
set local request.jwt.claim.sub='f3000000-0000-0000-0000-000000000002';
select pg_temp.check_true((select count(*)=0 from public.workspace_dots),'outsider cannot read Dots');
select public.accept_invitation(current_setting('test.invite'));
select pg_temp.check_true((select count(*)=1 from public.workspace_dots),'member sees shared identity');
select pg_temp.denied($q$select public.save_workspace_bud(null,current_setting('test.w')::uuid,0,'github','owner/new','Other')$q$);
select pg_temp.denied($q$select public.remove_workspace_dot(current_setting('test.dot')::uuid,current_setting('test.w')::uuid,2)$q$);
select pg_temp.denied('delete from public.workspace_dots','42501');
set local request.jwt.claim.sub='f3000000-0000-0000-0000-000000000001';
select public.remove_member(current_setting('test.w')::uuid,'f3000000-0000-0000-0000-000000000002');
set local request.jwt.claim.sub='f3000000-0000-0000-0000-000000000002';
select pg_temp.check_true((select count(*)=0 from public.workspace_dots),'revocation hides Dots');
set local request.jwt.claim.sub='f3000000-0000-0000-0000-000000000001';
select public.remove_workspace_dot(current_setting('test.dot')::uuid,current_setting('test.w')::uuid,2);
select pg_temp.check_true((select count(*)=0 from public.workspace_dots),'removed Dots are hidden');
rollback;
