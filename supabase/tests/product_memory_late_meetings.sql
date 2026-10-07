begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('a7000000-0000-0000-0000-000000000001','optional@memory.test',now());
create or replace function pg_temp.check_true(ok boolean,description text) returns void
language plpgsql as $$ begin if ok is distinct from true then raise exception 'FAIL: %',description; end if; end $$;
set local role authenticated;
set local request.jwt.claim.sub='a7000000-0000-0000-0000-000000000001';
select set_config('test.w',public.onboard_workspace('Optional meetings','Aedrova','codex')::text,true);
select set_config('test.c',(select id::text from public.channels where workspace_id=current_setting('test.w')::uuid limit 1),true);

select pg_temp.check_true(exists(select 1 from pg_trigger where tgname='memory_meeting_withdrawal'),'late meeting install attaches privacy trigger');
select set_config('test.m',public.start_meeting(current_setting('test.c')::uuid,'Memory evidence')::text,true);
select public.join_meeting(current_setting('test.m')::uuid);
select public.set_meeting_consent(current_setting('test.m')::uuid,true,true);
select public.append_meeting_text(current_setting('test.m')::uuid,'a7300000-0000-0000-0000-000000000001',
 (select revision from public.meetings where id=current_setting('test.m')::uuid),
 array['a7000000-0000-0000-0000-000000000001'::uuid],'Use accessible exports',120);
select pg_temp.check_true(public.memory_source('meeting','a7300000-0000-0000-0000-000000000001')->>'body'='Use accessible exports','participant text works without speech review');
select public.save_product_memory('a7200000-0000-0000-0000-000000000001',current_setting('test.w')::uuid,current_setting('test.c')::uuid,0,
 'decision','Export access','Use accessible exports','approved',jsonb_build_array(public.memory_source('meeting','a7300000-0000-0000-0000-000000000001')));
select public.withdraw_meeting_text(current_setting('test.m')::uuid,false);
select pg_temp.check_true((select count(*)=0 from public.product_memory),'late meeting AI withdrawal purges derived memory');
select pg_temp.check_true((select count(*)=0 from public.product_memory_history),'late meeting AI withdrawal purges history');
reset role;
alter table public.meeting_transcript_segments drop constraint meeting_transcript_segments_source_check;
update public.meeting_transcript_segments set source='provider_speech',ai_allowed=true;
set local role authenticated;
select pg_temp.check_true(public.memory_source('meeting','a7300000-0000-0000-0000-000000000001') is null,'unreviewed provider speech excluded without review schema');
rollback;
