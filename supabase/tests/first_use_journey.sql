begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('f1100000-0000-0000-0000-000000000001','first-use-owner@test.local',now()),
 ('f1100000-0000-0000-0000-000000000002','first-use-other@test.local',now());
create function pg_temp.assert_journey(ok boolean,msg text) returns void language plpgsql as $$
begin if ok is distinct from true then raise exception 'FAIL %',msg; end if; end $$;
create function pg_temp.expect_journey_error(statement text, expected text) returns void language plpgsql as $$
begin
 begin execute statement;
 exception when others then
  if sqlstate=expected then return; end if;
  raise;
 end;
 raise exception 'FAIL expected error %',expected;
end $$;
set local role anon;
select pg_temp.expect_journey_error('select public.get_first_use_progress()','42501');
set local role authenticated;
set local request.jwt.claim.sub='f1100000-0000-0000-0000-000000000001';
select pg_temp.assert_journey(public.get_first_use_progress()='{}','new user has no invented setup');
select pg_temp.expect_journey_error($q$select public.save_first_use_progress(0,1,'{"admin":true}')$q$,'22023');
select pg_temp.expect_journey_error($q$select public.save_first_use_progress(0,1,'{"name":{}}')$q$,'22023');
select pg_temp.expect_journey_error($q$select public.save_first_use_progress(0,1,'{"selected_roles":["unknown"]}')$q$,'22023');
select pg_temp.assert_journey(public.save_first_use_progress(0,1,
 '{"name":"First-use acceptance","icon":"context","purpose":"research","description":"A real team project","automatic":false}') ->>'revision'='1','initial revision');
select pg_temp.expect_journey_error($q$select public.save_first_use_progress(0,1,'{"name":"Stale device"}')$q$,'40001');
select pg_temp.expect_journey_error('select public.create_first_use_space(null,false)','22023');
select set_config('test.journey_space',public.create_first_use_space(null,true)->>'workspace_id',true);
select pg_temp.assert_journey(public.create_first_use_space(null,true)->>'workspace_id'=current_setting('test.journey_space'),'space retry does not duplicate');
select pg_temp.assert_journey((select count(*)=1 from public.workspaces where name='First-use acceptance'),'one Space');
select pg_temp.assert_journey((select icon='context' from public.workspace_identity where workspace_id=current_setting('test.journey_space')::uuid),'real Space identity');
select pg_temp.expect_journey_error($q$select public.save_first_use_progress(2,2,
 '{"name":"First-use acceptance","icon":"context","purpose":"research","description":"A real team project","automatic":true}')$q$,'22023');
select set_config('test.journey_bud',public.activate_first_use_buds(array['research'])->'buds'->>'research',true);
select pg_temp.assert_journey(public.activate_first_use_buds(array['research'])->'buds'->>'research'=current_setting('test.journey_bud'),'Bud activation retry uses existing identity');
select pg_temp.expect_journey_error($q$select public.activate_first_use_buds(array['finance'])$q$,'54000');
select pg_temp.assert_journey(not(public.get_first_use_progress()->'buds' ? 'finance'),'failed activation does not claim success');
select pg_temp.expect_journey_error($q$select public.activate_first_use_buds(array['unknown'])$q$,'22023');
select pg_temp.expect_journey_error($q$select public.invite_first_use_teammate('bad address')$q$,'22023');
select pg_temp.assert_journey(public.invite_first_use_teammate('teammate@team.test')->>'created'='true','real invitation created');
select pg_temp.assert_journey(public.invite_first_use_teammate('teammate@team.test')->>'created'='false','invitation retry is not duplicated');
select pg_temp.assert_journey((select count(*)=1 from public.workspace_invitations where workspace_id=current_setting('test.journey_space')::uuid),'one invitation');
select pg_temp.assert_journey(not(public.get_first_use_progress()->'invitations'->'teammate@team.test' ? 'code'),'invitation codes are not saved in progress');
select set_config('test.journey_message',public.complete_first_use('Let us build a useful research workspace')->>'first_message_id',true);
select pg_temp.assert_journey(public.complete_first_use('Let us build a useful research workspace')->>'first_message_id'=current_setting('test.journey_message'),'completion retry retains one first conversation');
select pg_temp.assert_journey((select count(*)=1 from public.messages where id=current_setting('test.journey_message')::uuid),'first conversation was actually saved');
select pg_temp.assert_journey(public.get_first_use_progress()->>'completed_at' is not null,'completion persists');
select pg_temp.expect_journey_error($q$select public.save_first_use_progress(99,1,'{}')$q$,'40001');
set local request.jwt.claim.sub='f1100000-0000-0000-0000-000000000002';
select pg_temp.assert_journey(public.get_first_use_progress()='{}','other account cannot load progress');
select pg_temp.assert_journey((select count(*)=0 from public.first_use_progress),'progress RLS isolates accounts');
select pg_temp.assert_journey((select count(*)=0 from public.workspace_identity where workspace_id=current_setting('test.journey_space')::uuid),'workspace identity remains private');
select pg_temp.expect_journey_error('select public.complete_first_use(''Intrusion'')','22023');
select pg_temp.expect_journey_error('update public.first_use_progress set completed_at=now()','42501');
rollback;
