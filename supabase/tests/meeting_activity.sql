begin;
insert into auth.users(id,email,email_confirmed_at,raw_user_meta_data) values
 ('74000000-0000-0000-0000-000000000001','activity-host@test.invalid',now(),
 '{"full_name":"Host","avatar_url":"https://lh3.googleusercontent.com/photo"}'),
 ('74000000-0000-0000-0000-000000000002','activity-other@test.invalid',now(),'{}');
create or replace function pg_temp.check_true(ok boolean,description text) returns void
language plpgsql as $$ begin if ok is distinct from true then
 raise exception 'FAIL: %',description; end if; end $$;
create or replace function pg_temp.denied(statement text) returns void language plpgsql as $$
begin begin execute statement; exception when insufficient_privilege then return; end;
 raise exception 'FAIL: unauthorized operation succeeded'; end $$;
set local role authenticated;
set local request.jwt.claim.sub='74000000-0000-0000-0000-000000000001';
select set_config('test.w',public.onboard_workspace('Activity test','Aedrova','codex')::text,true);
select set_config('test.c',(select id::text from public.channels where workspace_id=current_setting('test.w')::uuid limit 1),true);
select set_config('test.m',public.start_meeting(current_setting('test.c')::uuid,'Live meeting')::text,true);
select public.join_meeting(current_setting('test.m')::uuid);
select public.set_meeting_announcement_channel(current_setting('test.w')::uuid,current_setting('test.c')::uuid);
select pg_temp.check_true(public.meeting_activity()->'meetings'->0->'participants'->0->>'avatar_url'='https://lh3.googleusercontent.com/photo','safe profile is visible');
select pg_temp.check_true(public.meeting_activity()->'preferences'->0->>'announcement_channel'=current_setting('test.c'),'shared destination');
set local request.jwt.claim.sub='74000000-0000-0000-0000-000000000002';
select pg_temp.check_true(jsonb_array_length(public.meeting_activity()->'meetings')=0,'outsider cannot see active meetings');
select pg_temp.denied('select public.set_meeting_announcement_channel(current_setting(''test.w'')::uuid,current_setting(''test.c'')::uuid)');
set local request.jwt.claim.sub='74000000-0000-0000-0000-000000000001';
select set_config('test.private',public.create_channel(current_setting('test.w')::uuid,'private-call',true)::text,true);
select pg_temp.denied('select public.set_meeting_announcement_channel(current_setting(''test.w'')::uuid,current_setting(''test.private'')::uuid)');
reset role;
update auth.users set raw_user_meta_data='{"avatar_url":"https://unknown.invalid/photo"}'
 where id='74000000-0000-0000-0000-000000000001';
set local role authenticated;
select pg_temp.check_true(public.meeting_activity()->'meetings'->0->'participants'->0->>'avatar_url' is null,'unsafe photo URL excluded');
select public.leave_meeting(current_setting('test.m')::uuid);
select pg_temp.check_true(jsonb_array_length(public.meeting_activity()->'meetings'->0->'participants')=0,'left participants disappear');
select public.end_meeting(current_setting('test.m')::uuid);
select pg_temp.check_true(jsonb_array_length(public.meeting_activity()->'meetings')=0,'ended meetings disappear');
set local request.jwt.claim.sub='74000000-0000-0000-0000-000000000002';
select pg_temp.check_true(jsonb_array_length(public.meeting_activity()->'meetings')=0,'outsider sees no activity');
select pg_temp.check_true(jsonb_array_length(public.meeting_activity()->'preferences')=0,'outsider sees no settings');
set local role anon;
select pg_temp.denied('select public.meeting_activity()');
rollback;
