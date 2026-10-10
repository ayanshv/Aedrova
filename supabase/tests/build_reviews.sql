begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('b6000000-0000-0000-0000-000000000001','build-owner@test.local',now()),
 ('b6000000-0000-0000-0000-000000000002','build-member@test.local',now());
create or replace function pg_temp.check_true(ok boolean,description text) returns void
language plpgsql as $$ begin if ok is distinct from true then raise exception 'FAIL: %',description; end if; end $$;
create or replace function pg_temp.denied(statement text,code text default '42501') returns void
language plpgsql as $$ declare actual text;
begin begin execute statement; exception when others then get stacked diagnostics actual=returned_sqlstate;
 if actual=code then return; end if; raise; end;
 raise exception 'FAIL: unauthorized action succeeded'; end $$;
set local role authenticated;
set local request.jwt.claim.sub='b6000000-0000-0000-0000-000000000001';
select set_config('test.w',public.onboard_workspace('Build review acceptance','Aedrova','codex')::text,true);
select set_config('test.c',(select id::text from public.channels where workspace_id=current_setting('test.w')::uuid limit 1),true);
select set_config('test.private',public.create_channel(current_setting('test.w')::uuid,'private-evidence',true)::text,true);
select public.send_message('b6100000-0000-0000-0000-000000000001',current_setting('test.c')::uuid,'Preserve UTC dates');
select public.save_product_memory('b6200000-0000-0000-0000-000000000001',current_setting('test.w')::uuid,current_setting('test.c')::uuid,0,
 'constraint','UTC dates','Preserve UTC dates','approved',jsonb_build_array(public.memory_source('message','b6100000-0000-0000-0000-000000000001')));
select set_config('test.e',jsonb_build_object('task','Test build','memory_revision',repeat('a',64),
 'review_digest',repeat('b',64),'project_fingerprint',repeat('c',64),
 'acceptance_criteria',jsonb_build_array('Export dates in UTC'),
 'requirements',(select jsonb_build_array(jsonb_build_object('id',id,'version',version,'kind',kind,'title',title,'body',body,
 'sources',sources,'channel_id',channel_id,'assessment','reviewer_verified','files',jsonb_build_array('dates.py'),
 'checks',jsonb_build_array(repeat('d',64)))) from public.product_memory where id='b6200000-0000-0000-0000-000000000001'),
 'files',jsonb_build_array(jsonb_build_object('path','dates.py','diff','+ UTC')),
 'checks',jsonb_build_array(jsonb_build_object('id',repeat('d',64),'command','pytest','exit_code',0,'state','passed',
 'project_fingerprint',repeat('c',64),'output','1 passed')))::text,true);
select pg_temp.check_true(public.save_build_review('b6300000-0000-0000-0000-000000000001',current_setting('test.w')::uuid,current_setting('test.c')::uuid,
 array[current_setting('test.c')::uuid],0,current_setting('test.e')::jsonb)=1,'initial evidence version');
select pg_temp.check_true(public.save_build_review('b6300000-0000-0000-0000-000000000001',current_setting('test.w')::uuid,current_setting('test.c')::uuid,
 array[current_setting('test.c')::uuid],0,current_setting('test.e')::jsonb)=1,'lost-response retry idempotent');
select pg_temp.check_true((select count(*)=1 from public.messages where id='b6300000-0000-0000-0000-000000000001'),'share notification sent once');
select pg_temp.denied($q$select public.save_build_review('b6300000-0000-0000-0000-000000000001',current_setting('test.w')::uuid,current_setting('test.c')::uuid,
 array[current_setting('test.c')::uuid],0,jsonb_set(current_setting('test.e')::jsonb,'{task}','"changed"'))$q$,'PT409');
select pg_temp.denied('update public.build_reviews set version=99');
select pg_temp.denied($q$select public.save_build_review('b6300000-0000-0000-0000-000000000003',current_setting('test.w')::uuid,current_setting('test.c')::uuid,
 array[current_setting('test.c')::uuid],0,jsonb_set(current_setting('test.e')::jsonb,'{checks,0,exit_code}','1'))$q$,'22023');
select pg_temp.denied($q$select public.save_build_review('b6300000-0000-0000-0000-000000000003',current_setting('test.w')::uuid,current_setting('test.c')::uuid,
 array[current_setting('test.c')::uuid],0,jsonb_set(current_setting('test.e')::jsonb,'{checks,0,project_fingerprint}','"outdated"'))$q$,'22023');
select pg_temp.denied($q$select public.save_build_review('b6300000-0000-0000-0000-000000000003',current_setting('test.w')::uuid,current_setting('test.c')::uuid,
 array[current_setting('test.c')::uuid],0,jsonb_set(current_setting('test.e')::jsonb,'{files,0,path}','"../escape"'))$q$,'22023');
select public.record_build_delivery('b6500000-0000-0000-0000-000000000001','b6300000-0000-0000-0000-000000000001',repeat('b',64),'draft_pr','https://github.com/owner/test/pull/1');
select public.record_build_delivery('b6500000-0000-0000-0000-000000000002','b6300000-0000-0000-0000-000000000001',repeat('b',64),'draft_pr','https://github.com/owner/test/pull/1');
select pg_temp.check_true((select count(*)=1 from public.build_delivery_receipts),'delivery retry idempotent');
select pg_temp.denied($q$select public.record_build_delivery('b6500000-0000-0000-0000-000000000003','b6300000-0000-0000-0000-000000000001',repeat('b',64),'draft_pr','https://attacker.test/pull/1')$q$,'22023');
select public.save_build_review('b6300000-0000-0000-0000-000000000002',current_setting('test.w')::uuid,current_setting('test.c')::uuid,
 array[current_setting('test.c')::uuid,current_setting('test.private')::uuid],0,current_setting('test.e')::jsonb);
select set_config('test.invite',public.create_invitation(current_setting('test.w')::uuid,'build-member@test.local','member'),true);
set local request.jwt.claim.sub='b6000000-0000-0000-0000-000000000002';
select pg_temp.check_true((select count(*)=0 from public.build_reviews),'outsider evidence isolation');
select public.accept_invitation(current_setting('test.invite'));
select pg_temp.check_true((select count(*)=1 from public.build_reviews),'intersection of source channels enforced');
select public.decide_build_review('b6400000-0000-0000-0000-000000000001','b6300000-0000-0000-0000-000000000001',1,'approved','Reviewed local command evidence');
select public.decide_build_review('b6400000-0000-0000-0000-000000000001','b6300000-0000-0000-0000-000000000001',1,'approved','Reviewed local command evidence');
select pg_temp.check_true((select count(*)=1 from public.build_review_decisions),'duplicate review action idempotent');
select pg_temp.denied($q$select public.decide_build_review('b6400000-0000-0000-0000-000000000002','b6300000-0000-0000-0000-000000000002',1,'approved','steal')$q$);
select pg_temp.denied($q$select public.save_build_review('b6300000-0000-0000-0000-000000000001',current_setting('test.w')::uuid,current_setting('test.c')::uuid,
 array[current_setting('test.c')::uuid],1,current_setting('test.e')::jsonb)$q$);
set local request.jwt.claim.sub='b6000000-0000-0000-0000-000000000001';
select public.chat_action('edit',jsonb_build_object('message','b6100000-0000-0000-0000-000000000001','body','Export with offsets now'));
select pg_temp.denied($q$select public.decide_build_review('b6400000-0000-0000-0000-000000000003','b6300000-0000-0000-0000-000000000001',1,'approved','stale evidence')$q$,'PT409');
select public.unsend_message('b6100000-0000-0000-0000-000000000001');
select pg_temp.check_true((select count(*)=0 from public.build_reviews),'source withdrawal purges shared evidence');
select pg_temp.check_true((select count(*)=0 from public.build_review_decisions),'source withdrawal purges derived review notes');
select pg_temp.check_true((select count(*)=0 from public.build_delivery_receipts),'withdrawal purges delivery receipts');
rollback;
