begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('a6000000-0000-0000-0000-000000000001','owner@memory.test',now()),
 ('a6000000-0000-0000-0000-000000000002','member@memory.test',now());
create or replace function pg_temp.check_true(ok boolean,description text) returns void
language plpgsql as $$ begin if ok is distinct from true then raise exception 'FAIL: %',description; end if; end $$;
create or replace function pg_temp.denied(statement text) returns void language plpgsql as $$
begin begin execute statement; exception when insufficient_privilege then return; end;
 raise exception 'FAIL: unauthorized operation succeeded'; end $$;
set local role authenticated;
set local request.jwt.claim.sub='a6000000-0000-0000-0000-000000000001';
select set_config('test.w',public.onboard_workspace('Memory','Aedrova','codex')::text,true);
select set_config('test.c',(select id::text from public.channels where workspace_id=current_setting('test.w')::uuid limit 1),true);
select public.send_message('a6100000-0000-0000-0000-000000000001',current_setting('test.c')::uuid,'Use UTC for exported dates');
select set_config('test.sources',jsonb_build_array(public.memory_source('message','a6100000-0000-0000-0000-000000000001'))::text,true);
select public.save_product_memory('a6200000-0000-0000-0000-000000000001',current_setting('test.w')::uuid,current_setting('test.c')::uuid,0,
 'constraint','Date handling','Use UTC for exports','proposal',current_setting('test.sources')::jsonb);
select pg_temp.check_true((public.memory_list(current_setting('test.w')::uuid)->'items'->0->>'state')='proposal','proposals not automatically approved');
select public.save_product_memory('a6200000-0000-0000-0000-000000000001',current_setting('test.w')::uuid,current_setting('test.c')::uuid,1,
 'constraint','Date handling','Use UTC for exports','approved',current_setting('test.sources')::jsonb);
select pg_temp.check_true((select count(*)=2 from public.product_memory_history),'revision history retained');
do $$ begin
 begin perform public.save_product_memory('a6200000-0000-0000-0000-000000000001',current_setting('test.w')::uuid,current_setting('test.c')::uuid,1,
 'constraint','Date handling','Old client edit','approved',current_setting('test.sources')::jsonb);
 exception when sqlstate 'PT409' then return; end;
 raise exception 'FAIL stale version accepted'; end $$;
select pg_temp.denied('update public.product_memory set body=''tampered''');
select set_config('test.private',public.create_channel(current_setting('test.w')::uuid,'private',true)::text,true);
select public.send_message('a6100000-0000-0000-0000-000000000002',current_setting('test.private')::uuid,'Private design constraint');
select public.save_product_memory('a6200000-0000-0000-0000-000000000002',current_setting('test.w')::uuid,current_setting('test.private')::uuid,0,
 'constraint','Private','Private design constraint','approved',jsonb_build_array(public.memory_source('message','a6100000-0000-0000-0000-000000000002')));
select set_config('test.invite',public.create_invitation(current_setting('test.w')::uuid,'member@memory.test','member'),true);
set local request.jwt.claim.sub='a6000000-0000-0000-0000-000000000002';
select pg_temp.check_true((select count(*)=0 from public.product_memory),'outsider memory isolation');
select public.accept_invitation(current_setting('test.invite'));
select pg_temp.check_true((public.memory_list(current_setting('test.w')::uuid)->>'total')='1','private memory hidden');
select pg_temp.check_true((select count(*)=2 from public.product_memory_history),'private revision history hidden');
select pg_temp.denied($q$select public.save_product_memory('a6200000-0000-0000-0000-000000000002',current_setting('test.w')::uuid,current_setting('test.private')::uuid,1,'constraint','Private','steal','approved',current_setting('test.sources')::jsonb)$q$);
set local request.jwt.claim.sub='a6000000-0000-0000-0000-000000000001';
reset role;
update public.messages set body='Use local dates now' where id='a6100000-0000-0000-0000-000000000001';
set local role authenticated;
select pg_temp.check_true((public.memory_list(current_setting('test.w')::uuid)->'items'->1->>'fresh')='false','edited source invalidates approval');
do $$ begin
 begin perform public.save_product_memory('a6200000-0000-0000-0000-000000000001',current_setting('test.w')::uuid,current_setting('test.c')::uuid,2,
 'constraint','Date handling','Use UTC','approved',current_setting('test.sources')::jsonb);
 exception when sqlstate 'PT409' then return; end;
 raise exception 'FAIL stale source accepted'; end $$;
select set_config('test.sources',jsonb_build_array(public.memory_source('message','a6100000-0000-0000-0000-000000000001'))::text,true);
select public.save_product_memory('a6200000-0000-0000-0000-000000000003',current_setting('test.w')::uuid,current_setting('test.c')::uuid,0,
 'constraint','Replacement','Use local dates','approved',current_setting('test.sources')::jsonb,null,'a6200000-0000-0000-0000-000000000001',2);
select pg_temp.check_true((select state='superseded' and version=3 from public.product_memory where id='a6200000-0000-0000-0000-000000000001'),'atomic supersession');
select public.save_product_memory('a6200000-0000-0000-0000-000000000004',current_setting('test.w')::uuid,current_setting('test.c')::uuid,0,
 'question','Timezone conflict','Which timezone?','conflict',current_setting('test.sources')::jsonb,'a6200000-0000-0000-0000-000000000003');
select pg_temp.check_true((public.memory_list(current_setting('test.w')::uuid,'conflict')->>'total')='1','indexed memory search');
select pg_temp.check_true((public.memory_list(current_setting('test.w')::uuid,'',1)->>'truncated')='true','coverage limits disclosed');
reset role;
update public.messages set unsent_at=now() where id='a6100000-0000-0000-0000-000000000001';
set local role authenticated;
select pg_temp.check_true((public.memory_list(current_setting('test.w')::uuid)->>'total')='1','unsent sources and derived entries unavailable');
select pg_temp.check_true((select count(*)=1 from public.product_memory_history),'history follows source deletion');
set local request.jwt.claim.sub='a6000000-0000-0000-0000-000000000002';
select pg_temp.check_true((select count(*)=0 from public.product_memory),'member cannot read deleted source memory');
set local request.jwt.claim.sub='a6000000-0000-0000-0000-000000000001';
select public.remove_member(current_setting('test.w')::uuid,'a6000000-0000-0000-0000-000000000002');
set local request.jwt.claim.sub='a6000000-0000-0000-0000-000000000002';
select pg_temp.denied($q$select public.memory_list(current_setting('test.w')::uuid)$q$);
set local request.jwt.claim.sub='a6000000-0000-0000-0000-000000000001';
select public.send_message('a6100000-0000-0000-0000-000000000005',current_setting('test.c')::uuid,'Specification attached');
reset role;
insert into public.attachments(id,channel_id,uploader_id,filename,byte_size,sha256,object_path,message_id)
values('a6300000-0000-0000-0000-000000000001',current_setting('test.c')::uuid,
'a6000000-0000-0000-0000-000000000001','spec.md',100,repeat('a',64),'memory-test/spec.md','a6100000-0000-0000-0000-000000000005');
set local role authenticated;
select public.save_product_memory('a6200000-0000-0000-0000-000000000005',current_setting('test.w')::uuid,current_setting('test.c')::uuid,0,
 'requirement','Specification','Follow the specification','approved',jsonb_build_array(public.memory_source('attachment','a6300000-0000-0000-0000-000000000001')));
select pg_temp.check_true(public.memory_source('attachment','a6300000-0000-0000-0000-000000000001')->>'filename'='spec.md','file citation resolves original');
reset role;
update public.attachments set sha256=repeat('b',64) where id='a6300000-0000-0000-0000-000000000001';
set local role authenticated;
select pg_temp.check_true((select not (item->>'fresh')::boolean from jsonb_array_elements(public.memory_list(current_setting('test.w')::uuid)->'items') item where item->>'id'='a6200000-0000-0000-0000-000000000005'),'changed file hash marks memory stale');
reset role;
delete from public.attachments where id='a6300000-0000-0000-0000-000000000001';
select pg_temp.check_true((select count(*)=0 from public.product_memory where id='a6200000-0000-0000-0000-000000000005'),'deleted file removes derived copies');
set local role authenticated;
select set_config('test.meeting',public.start_meeting(current_setting('test.c')::uuid,'Memory meeting')::text,true);
select public.join_meeting(current_setting('test.meeting')::uuid);
select public.set_meeting_consent(current_setting('test.meeting')::uuid,true,true);
select public.append_meeting_text(current_setting('test.meeting')::uuid,'a6400000-0000-0000-0000-000000000001',
 (select revision from public.meetings where id=current_setting('test.meeting')::uuid),
 array['a6000000-0000-0000-0000-000000000001'::uuid],'Keep the export accessible',100);
select public.save_product_memory('a6200000-0000-0000-0000-000000000006',current_setting('test.w')::uuid,current_setting('test.c')::uuid,0,
 'requirement','Meeting decision','Accessible exports','approved',jsonb_build_array(public.memory_source('meeting','a6400000-0000-0000-0000-000000000001')));
select public.review_meeting_segment('a6400000-0000-0000-0000-000000000001',0,'Accessible export with labels',true);
select pg_temp.check_true((select not (item->>'fresh')::boolean from jsonb_array_elements(public.memory_list(current_setting('test.w')::uuid)->'items') item where item->>'id'='a6200000-0000-0000-0000-000000000006'),'reviewed transcript correction invalidates memory');
select public.withdraw_meeting_text(current_setting('test.meeting')::uuid,false);
select pg_temp.check_true((select count(*)=0 from public.product_memory where id='a6200000-0000-0000-0000-000000000006'),'AI withdrawal purges derived memory');
reset role;
insert into aedrova_private.write_budgets(user_id,bucket,window_start,count)
values('a6000000-0000-0000-0000-000000000001','memory-save',
 floor(extract(epoch from clock_timestamp())/60)::bigint*60,60)
on conflict(user_id,bucket,window_start) do update set count=60;
set local role authenticated;
do $$ begin
 begin perform public.save_product_memory('a6200000-0000-0000-0000-000000000007',current_setting('test.w')::uuid,current_setting('test.c')::uuid,0,
 'goal','Budget','Budget exceeded','proposal',current_setting('test.sources')::jsonb);
 exception when raise_exception then
 if sqlerrm='Too many requests. Wait before retrying.' then return; end if;
 raise;
 end;
 raise exception 'FAIL rate limit bypassed'; end $$;
set local role anon;
select pg_temp.denied('select * from public.product_memory');
select pg_temp.denied($q$select public.memory_source('message','a6100000-0000-0000-0000-000000000001')$q$);
reset role;
rollback;
