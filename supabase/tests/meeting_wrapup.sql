begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('83000000-0000-0000-0000-000000000001','host@wrapup.test',now()),
 ('83000000-0000-0000-0000-000000000002','peer@wrapup.test',now()),
 ('83000000-0000-0000-0000-000000000003','outsider@wrapup.test',now());
create function pg_temp.ok(v boolean) returns void language plpgsql as $$
begin if v is distinct from true then raise exception 'Wrapup assertion failed'; end if; end $$;
create function pg_temp.denied(q text) returns void language plpgsql as $$
begin begin execute q; exception when insufficient_privilege then return; end;
raise exception 'Unauthorized wrapup succeeded'; end $$;
create function pg_temp.stale(q text) returns void language plpgsql as $$
begin begin execute q; exception when serialization_failure then return; end;
raise exception 'Stale wrapup succeeded'; end $$;
set local role authenticated;
set local request.jwt.claim.sub='83000000-0000-0000-0000-000000000001';
select set_config('test.w',public.onboard_workspace('Wrapup','Aedrova','codex')::text,true);
select set_config('test.c',(select id::text from public.channels where workspace_id=current_setting('test.w')::uuid limit 1),true);
select set_config('test.m',public.start_meeting(current_setting('test.c')::uuid,'Product sync')::text,true);
select public.join_meeting(current_setting('test.m')::uuid);
select set_config('test.invite',public.create_invitation(current_setting('test.w')::uuid,'peer@wrapup.test','member')::text,true);
set local request.jwt.claim.sub='83000000-0000-0000-0000-000000000002';
select public.accept_invitation(current_setting('test.invite'));
select public.join_meeting(current_setting('test.m')::uuid);
reset role;
insert into public.meeting_transcript_segments
 (id,meeting_id,channel_id,speaker_id,consent_revision,consent_roster,body,offset_ms,source,ai_allowed)
 select ('84000000-0000-0000-0000-00000000000'||i)::uuid,current_setting('test.m')::uuid,
 current_setting('test.c')::uuid,'83000000-0000-0000-0000-000000000001',1,
 array['83000000-0000-0000-0000-000000000001'::uuid], 'Original '||i, i*10000,'provider_speech',i=1
 from generate_series(1,2) i;
select set_config('test.edits','[{"identifier":"84000000-0000-0000-0000-000000000001","version":0,"body":"Corrected one"},{"identifier":"84000000-0000-0000-0000-000000000002","version":0,"body":"Corrected two"}]',true);
set local role authenticated;
set local request.jwt.claim.sub='83000000-0000-0000-0000-000000000001';
select pg_temp.ok((public.meeting_wrapup_status(current_setting('test.m')::uuid)->>'ready')::boolean=false);
select pg_temp.denied('select public.confirm_meeting_transcript(current_setting(''test.m'')::uuid,current_setting(''test.edits'')::jsonb)');
select public.leave_meeting(current_setting('test.m')::uuid);
select pg_temp.ok((select ended_at is null from public.meetings where id=current_setting('test.m')::uuid));
set local request.jwt.claim.sub='83000000-0000-0000-0000-000000000002';
select public.leave_meeting(current_setting('test.m')::uuid);
select pg_temp.ok((select ended_at is not null from public.meetings where id=current_setting('test.m')::uuid));
select pg_temp.denied('select public.confirm_meeting_transcript(current_setting(''test.m'')::uuid,current_setting(''test.edits'')::jsonb)');
set local request.jwt.claim.sub='83000000-0000-0000-0000-000000000003';
select pg_temp.denied('select public.meeting_wrapup_status(current_setting(''test.m'')::uuid)');
set local request.jwt.claim.sub='83000000-0000-0000-0000-000000000001';
select pg_temp.ok((public.meeting_wrapup_status(current_setting('test.m')::uuid)->>'ready')::boolean);
select pg_temp.stale('select public.confirm_meeting_transcript(current_setting(''test.m'')::uuid,jsonb_set(current_setting(''test.edits'')::jsonb,''{1,version}'',''1''))');
select pg_temp.ok((select count(*)=0 from public.meeting_transcript_segments where reviewed_at is not null));
select pg_temp.stale('select public.confirm_meeting_transcript(current_setting(''test.m'')::uuid,jsonb_build_array((current_setting(''test.edits'')::jsonb)->0))');
select pg_temp.ok(public.confirm_meeting_transcript(current_setting('test.m')::uuid,current_setting('test.edits')::jsonb)=2);
select pg_temp.ok((select count(*)=1 from public.meeting_text_context(current_setting('test.c')::uuid)));
select pg_temp.ok((select count(*)=2 from public.meeting_transcript_segments where body like 'Original %' and review_body like 'Corrected %' and review_version=1 and not confirmed_decision));
select pg_temp.stale('select public.confirm_meeting_transcript(current_setting(''test.m'')::uuid,current_setting(''test.edits'')::jsonb)');
select public.withdraw_meeting_text(current_setting('test.m')::uuid,false);
select pg_temp.ok((select count(*)=0 from public.meeting_text_context(current_setting('test.c')::uuid)));
reset role;
select pg_temp.ok(not has_function_privilege('anon','public.confirm_meeting_transcript(uuid,jsonb)','execute'));
rollback;
