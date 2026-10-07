begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('a7000000-0000-0000-0000-000000000001','optional@memory.test',now());
create or replace function pg_temp.check_true(ok boolean,description text) returns void
language plpgsql as $$ begin if ok is distinct from true then raise exception 'FAIL: %',description; end if; end $$;
set local role authenticated;
set local request.jwt.claim.sub='a7000000-0000-0000-0000-000000000001';
select set_config('test.w',public.onboard_workspace('Optional meetings','Aedrova','codex')::text,true);
select set_config('test.c',(select id::text from public.channels where workspace_id=current_setting('test.w')::uuid limit 1),true);

select pg_temp.check_true(to_regclass('public.meeting_transcript_segments') is null,'meeting schema intentionally absent');
select public.send_message('a7100000-0000-0000-0000-000000000001',current_setting('test.c')::uuid,'Keep exports accessible');
select public.save_product_memory('a7200000-0000-0000-0000-000000000001',current_setting('test.w')::uuid,current_setting('test.c')::uuid,0,
 'requirement','Accessible exports','Keep exports accessible','approved',jsonb_build_array(public.memory_source('message','a7100000-0000-0000-0000-000000000001')));
select pg_temp.check_true((public.memory_list(current_setting('test.w')::uuid)->>'total')='1','chat-backed memory works without meetings');
select pg_temp.check_true(public.memory_source('meeting','a7300000-0000-0000-0000-000000000001') is null,'absent meetings fail closed');
do $$ begin
 begin perform public.save_product_memory('a7200000-0000-0000-0000-000000000002',current_setting('test.w')::uuid,current_setting('test.c')::uuid,0,
 'decision','Forged meeting','Must not save','approved',jsonb_build_array(jsonb_build_object('kind','meeting','id','a7300000-0000-0000-0000-000000000001','fingerprint','forged')));
 exception when insufficient_privilege then return; end;
 raise exception 'FAIL: absent meeting source accepted'; end $$;
reset role;
update public.messages set unsent_at=now() where id='a7100000-0000-0000-0000-000000000001';
select pg_temp.check_true((select count(*)=0 from public.product_memory),'chat withdrawal still purges memory');
select pg_temp.check_true((select count(*)=0 from public.product_memory_history),'chat withdrawal still purges history');
rollback;
