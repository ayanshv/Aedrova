-- Disposable PostgreSQL proof of voice finalization and private-file boundaries.
begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('b3000000-0000-0000-0000-000000000001','voice@test.local',now()),
 ('b3000000-0000-0000-0000-000000000002','outside-voice@test.local',now());
create or replace function pg_temp.check_true(ok boolean, description text) returns void
language plpgsql as $$ begin if ok is distinct from true then raise exception 'FAIL: %',description; end if; end $$;
create or replace function pg_temp.denied(statement text) returns void language plpgsql as $$
begin begin execute statement; exception when insufficient_privilege then return; end;
 raise exception 'FAIL: unauthorized voice operation succeeded'; end $$;
set local role authenticated;
set local request.jwt.claim.sub='b3000000-0000-0000-0000-000000000001';
select set_config('test.w',public.onboard_workspace('Voice','Nova','codex')::text,true);
select set_config('test.c',public.create_channel(current_setting('test.w')::uuid,'private-voice',true)::text,true);
select set_config('test.path',public.reserve_attachment('b4000000-0000-0000-0000-000000000001',current_setting('test.c')::uuid,'voice.wav',32044,repeat('c',64)),true);
insert into storage.objects(bucket_id,name,metadata) values('aedrova-files',current_setting('test.path'),'{"size":32044}');
select pg_temp.denied($q$select public.finish_verified_attachment('b3000000-0000-0000-0000-000000000001','b4000000-0000-0000-0000-000000000001',repeat('c',64),'audio/wav')$q$);
reset role;
set local role aedrova_website;
select pg_temp.denied($q$select public.finish_verified_attachment('b3000000-0000-0000-0000-000000000002','b4000000-0000-0000-0000-000000000001',repeat('c',64),'audio/wav')$q$);
select pg_temp.denied($q$select public.finish_verified_attachment('b3000000-0000-0000-0000-000000000001','b4000000-0000-0000-0000-000000000001',repeat('c',64),'audio/mpeg')$q$);
select public.finish_verified_attachment('b3000000-0000-0000-0000-000000000001','b4000000-0000-0000-0000-000000000001',repeat('c',64),'audio/wav');
select public.finish_verified_attachment('b3000000-0000-0000-0000-000000000001','b4000000-0000-0000-0000-000000000001',repeat('c',64),'audio/wav');
reset role;
select pg_temp.check_true((select count(*)=1 from public.messages where id='b4000000-0000-0000-0000-000000000001'),'voice published once');
select pg_temp.check_true((select verified_type='audio/wav' from public.attachments where id='b4000000-0000-0000-0000-000000000001'),'verified voice type retained');
set local role authenticated;
set local request.jwt.claim.sub='b3000000-0000-0000-0000-000000000002';
select pg_temp.check_true((select count(*)=0 from public.messages where id='b4000000-0000-0000-0000-000000000001'),'foreign account cannot read voice message');
select pg_temp.check_true((select count(*)=0 from public.attachments where id='b4000000-0000-0000-0000-000000000001'),'foreign account cannot read voice attachment');
select pg_temp.check_true((select count(*)=0 from storage.objects where bucket_id='aedrova-files' and name=current_setting('test.path')),'foreign account cannot read voice storage object');
rollback;
