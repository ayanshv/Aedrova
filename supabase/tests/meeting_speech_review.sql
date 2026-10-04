begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('81000000-0000-0000-0000-000000000001','host@speech.test',now()),
 ('81000000-0000-0000-0000-000000000002','peer@speech.test',now()),
 ('81000000-0000-0000-0000-000000000003','outside@speech.test',now());
create function pg_temp.check_true(ok boolean,description text) returns void language plpgsql as $$
begin if ok is distinct from true then raise exception 'FAIL: %',description; end if; end $$;
create function pg_temp.denied(statement text) returns void language plpgsql as $$
begin begin execute statement; exception when insufficient_privilege then return; end;
raise exception 'FAIL: unauthorized operation succeeded: %',statement; end $$;
create function pg_temp.stale(statement text) returns void language plpgsql as $$
begin begin execute statement; exception when serialization_failure then return; end;
raise exception 'FAIL: stale edit succeeded'; end $$;
create function pg_temp.reserve(id uuid) returns text language sql as $$
 select public.reserve_meeting_speech('81000000-0000-0000-0000-000000000001',
 current_setting('test.m')::uuid,id,current_setting('test.rev')::bigint,
 array['81000000-0000-0000-0000-000000000001'::uuid],repeat('a',64),0,10000)
$$;
set local role authenticated;
set local request.jwt.claim.sub='81000000-0000-0000-0000-000000000001';
select set_config('test.w',public.onboard_workspace('Speech review','Aedrova','codex')::text,true);
select set_config('test.c',(select id::text from public.channels where workspace_id=current_setting('test.w')::uuid limit 1),true);
select set_config('test.m',public.start_meeting(current_setting('test.c')::uuid,'Speech sync')::text,true);
select public.join_meeting(current_setting('test.m')::uuid);
select set_config('test.rev',(select revision::text from public.meetings where id=current_setting('test.m')::uuid),true);
select pg_temp.denied('select pg_temp.reserve(''82000000-0000-0000-0000-000000000001'')');
select pg_temp.denied('select public.finish_meeting_speech(''81000000-0000-0000-0000-000000000001'',''82000000-0000-0000-0000-000000000001'',''Forged provider text'')');
set local role aedrova_website;
select pg_temp.denied('select pg_temp.reserve(''82000000-0000-0000-0000-000000000001'')');
select pg_temp.denied('select * from public.meeting_transcript_segments');
select pg_temp.denied('select * from aedrova_private.meeting_speech_jobs');
set local role authenticated;
select public.set_meeting_consent(current_setting('test.m')::uuid,true,true);
select set_config('test.rev',(select revision::text from public.meetings where id=current_setting('test.m')::uuid),true);
set local role aedrova_website;
select pg_temp.check_true(pg_temp.reserve('82000000-0000-0000-0000-000000000001')='pending','trusted reservation');
select pg_temp.denied('select pg_temp.reserve(''82000000-0000-0000-0000-000000000002'')');
select public.finish_meeting_speech('81000000-0000-0000-0000-000000000001','82000000-0000-0000-0000-000000000001','Use C S V export');
select pg_temp.check_true(pg_temp.reserve('82000000-0000-0000-0000-000000000001')='completed','no second provider call');
select pg_temp.denied('select public.reserve_meeting_speech(''81000000-0000-0000-0000-000000000001'',current_setting(''test.m'')::uuid,''82000000-0000-0000-0000-000000000001'',current_setting(''test.rev'')::bigint,array[''81000000-0000-0000-0000-000000000001''::uuid],repeat(''b'',64),0,10000)');
set local role authenticated;
select pg_temp.check_true((select count(*)=1 from public.meeting_transcript_segments),'text visible for review');
select pg_temp.check_true((select count(*)=0 from public.meeting_text_context(current_setting('test.c')::uuid)),'unreviewed speech excluded');
select public.review_meeting_segment('82000000-0000-0000-0000-000000000001',0,'Use CSV export',true);
select pg_temp.check_true((select review_body='Use CSV export' and body='Use C S V export' and confirmed_decision and reviewed_by=auth.uid() from public.meeting_text_context(current_setting('test.c')::uuid)),'correction preserves original and attributed decision');
select pg_temp.stale('select public.review_meeting_segment(''82000000-0000-0000-0000-000000000001'',0,''Overwrite'',false)');
select set_config('test.code',public.create_invitation(current_setting('test.w')::uuid,'peer@speech.test','member')::text,true);
set local request.jwt.claim.sub='81000000-0000-0000-0000-000000000002';
select public.accept_invitation(current_setting('test.code'));
select pg_temp.denied('select public.review_meeting_segment(''82000000-0000-0000-0000-000000000001'',1,''Someone else'',false)');
set local request.jwt.claim.sub='81000000-0000-0000-0000-000000000003';
select pg_temp.check_true((select count(*)=0 from public.meeting_transcript_segments),'outsider cannot see transcript');
select pg_temp.denied('select public.meeting_text_context(current_setting(''test.c'')::uuid)');
set local request.jwt.claim.sub='81000000-0000-0000-0000-000000000001';
set local role aedrova_website;
select pg_temp.reserve('82000000-0000-0000-0000-000000000002');
set local role authenticated;
select public.set_meeting_consent(current_setting('test.m')::uuid,true,false);
set local role aedrova_website;
select pg_temp.denied('select public.finish_meeting_speech(''81000000-0000-0000-0000-000000000001'',''82000000-0000-0000-0000-000000000002'',''Late provider result'')');
set local role authenticated;
select public.review_meeting_segment('82000000-0000-0000-0000-000000000001',1,'Reviewed again',true);
select pg_temp.check_true((select count(*)=0 from public.meeting_text_context(current_setting('test.c')::uuid)),'review cannot resurrect withdrawn AI access');
-- Expired in-flight work cannot be saved. Charged reservation attempts are not refunded.
reset role;
update aedrova_private.meeting_speech_jobs set deadline=now()-interval '1 second'
 where id='82000000-0000-0000-0000-000000000002';
set local role aedrova_website;
select pg_temp.denied('select public.finish_meeting_speech(''81000000-0000-0000-0000-000000000001'',''82000000-0000-0000-0000-000000000002'',''Expired result'')');
set local role authenticated;
select set_config('test.rev',(select revision::text from public.meetings where id=current_setting('test.m')::uuid),true);
reset role;
-- Fill the shared budget with historical reservations; no provider call or audio involved.
insert into aedrova_private.meeting_speech_jobs
 (id,meeting_id,user_id,revision,roster,digest,offset_ms,duration_ms,state)
 select gen_random_uuid(),current_setting('test.m')::uuid,
 '81000000-0000-0000-0000-000000000001',current_setting('test.rev')::bigint,
 array['81000000-0000-0000-0000-000000000001'::uuid],repeat('a',64),0,10000,'failed'
 from generate_series(1,358);
set local role aedrova_website;
select pg_temp.denied('select pg_temp.reserve(''82000000-0000-0000-0000-000000000003'')');
set local role authenticated;
select public.end_meeting(current_setting('test.m')::uuid);
select public.review_meeting_segment('82000000-0000-0000-0000-000000000001',2,'After call review',false);
select public.withdraw_meeting_text(current_setting('test.m')::uuid,true);
select pg_temp.check_true((select count(*)=0 from public.meeting_transcript_segments),'post-call shared deletion');
reset role;
select pg_temp.check_true(not has_function_privilege('authenticated','public.finish_meeting_speech(uuid,uuid,text)','execute'),'authenticated cannot forge provider provenance');
select pg_temp.check_true(not has_function_privilege('anon','public.reserve_meeting_speech(uuid,uuid,uuid,bigint,uuid[],text,integer,integer)','execute'),'anonymous cannot spend allowance');
update aedrova_private.meeting_speech_jobs set created_at=now()-interval '31 days';
select aedrova_private.expire_meeting_text();
select pg_temp.check_true((select count(*)=0 from aedrova_private.meeting_speech_jobs),'expiry clears request metadata');
rollback;
