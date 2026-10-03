begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('70000000-0000-0000-0000-000000000001','host@meetings.test',now()),
 ('70000000-0000-0000-0000-000000000002','peer@meetings.test',now()),
 ('70000000-0000-0000-0000-000000000003','outsider@meetings.test',now());
create or replace function pg_temp.check_true(ok boolean,description text) returns void
language plpgsql as $$ begin if ok is distinct from true then
 raise exception 'FAIL: %',description; end if; end $$;
create or replace function pg_temp.denied(statement text) returns void language plpgsql as $$
begin begin execute statement; exception when insufficient_privilege then return; end;
 raise exception 'FAIL: unauthorized operation succeeded'; end $$;
set local role authenticated;
set local request.jwt.claim.sub='70000000-0000-0000-0000-000000000001';
select set_config('test.w',public.onboard_workspace('Meeting tests','Aedrova','codex')::text,true);
select set_config('test.c',(select id::text from public.channels where workspace_id=current_setting('test.w')::uuid limit 1),true);
select set_config('test.m',public.start_meeting(current_setting('test.c')::uuid,'Design sync')::text,true);
select pg_temp.check_true(public.start_meeting(current_setting('test.c')::uuid,'Duplicate')=current_setting('test.m')::uuid,'one active meeting');
select public.join_meeting(current_setting('test.m')::uuid);
select pg_temp.check_true((public.meeting_consent_snapshot(current_setting('test.m')::uuid)->'participants'->0->>'transcription')='false','joining does not consent');
select public.set_meeting_consent(current_setting('test.m')::uuid,true,true);
select set_config('test.rev',public.meeting_consent_snapshot(current_setting('test.m')::uuid)->>'revision',true);
select public.meeting_presence(current_setting('test.m')::uuid);
select pg_temp.check_true((public.meeting_consent_snapshot(current_setting('test.m')::uuid)->>'revision')=current_setting('test.rev'),'heartbeat keeps consent revision');
select set_config('test.code',public.create_invitation(current_setting('test.w')::uuid,'peer@meetings.test','member')::text,true);
set local request.jwt.claim.sub='70000000-0000-0000-0000-000000000002';
select public.accept_invitation(current_setting('test.code'));
select public.join_meeting(current_setting('test.m')::uuid);
select pg_temp.check_true((public.meeting_consent_snapshot(current_setting('test.m')::uuid)->>'revision')::bigint>current_setting('test.rev')::bigint,'late join invalidates capture permit');
select pg_temp.check_true((public.meeting_consent_snapshot(current_setting('test.m')::uuid)->'participants'->1->>'transcription')='false','late join starts without consent');
select public.set_meeting_consent(current_setting('test.m')::uuid,true,false);
select pg_temp.denied('update public.meeting_participants set ai_context=true');
select pg_temp.denied('delete from public.meetings');
select pg_temp.denied('select public.end_meeting(current_setting(''test.m'')::uuid)');
select public.set_meeting_consent(current_setting('test.m')::uuid,false,false);
select pg_temp.check_true((public.meeting_consent_snapshot(current_setting('test.m')::uuid)->'participants'->1->>'transcription')='false','revocation immediate');
do $$ begin
 begin perform public.set_meeting_consent(current_setting('test.m')::uuid,false,true);
 exception when raise_exception then return; end;
 raise exception 'FAIL: AI enabled without transcription'; end $$;
select public.leave_meeting(current_setting('test.m')::uuid);
select pg_temp.denied('select public.meeting_presence(current_setting(''test.m'')::uuid)');
select pg_temp.denied('select public.set_meeting_consent(current_setting(''test.m'')::uuid,true,true)');
set local request.jwt.claim.sub='70000000-0000-0000-0000-000000000003';
select pg_temp.check_true((select count(*)=0 from public.meetings),'outsider cannot see meetings');
select pg_temp.check_true((select count(*)=0 from public.meeting_participants),'outsider cannot see presence');
select pg_temp.denied('select public.join_meeting(current_setting(''test.m'')::uuid)');
select pg_temp.denied('select public.meeting_consent_snapshot(current_setting(''test.m'')::uuid)');
select pg_temp.denied('select public.start_meeting(current_setting(''test.c'')::uuid,''Intrusion'')');
set local request.jwt.claim.sub='70000000-0000-0000-0000-000000000001';
select public.end_meeting(current_setting('test.m')::uuid);
select pg_temp.check_true((public.meeting_consent_snapshot(current_setting('test.m')::uuid)->>'ended')='true','host can end');
select pg_temp.check_true(jsonb_array_length(public.meeting_consent_snapshot(current_setting('test.m')::uuid)->'participants')=0,'ending expires everyone');
select pg_temp.check_true(public.start_meeting(current_setting('test.c')::uuid,'Next sync')<>current_setting('test.m')::uuid,'new meeting after ending');
set local role anon;
select pg_temp.denied('select public.join_meeting(current_setting(''test.m'')::uuid)');
rollback;
