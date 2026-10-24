begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('b1000000-0000-0000-0000-000000000001','upload@test.local',now()),
 ('b1000000-0000-0000-0000-000000000002','outside@test.local',now());
create or replace function pg_temp.check_true(ok boolean, description text) returns void
language plpgsql as $$ begin if ok is distinct from true then raise exception 'FAIL: %',description; end if; end $$;
create or replace function pg_temp.denied(statement text) returns void language plpgsql as $$
begin begin execute statement; exception when insufficient_privilege then return; end;
 raise exception 'FAIL: unauthorized operation succeeded: %',statement; end $$;
set local role authenticated;
set local request.jwt.claim.sub='b1000000-0000-0000-0000-000000000001';
select set_config('test.w',public.onboard_workspace('Files','Nova','codex')::text,true);
select set_config('test.c',(select id::text from public.channels where workspace_id=current_setting('test.w')::uuid limit 1),true);
select set_config('test.path',public.reserve_attachment('b2000000-0000-0000-0000-000000000001',current_setting('test.c')::uuid,'notes.txt',3,repeat('a',64)),true);
insert into storage.objects(bucket_id,name,metadata) values('aedrova-files',current_setting('test.path'),'{"size":3}');
select pg_temp.denied($q$select public.finish_attachment('b2000000-0000-0000-0000-000000000001')$q$);
select pg_temp.denied($q$select public.finish_verified_attachment('b1000000-0000-0000-0000-000000000001','b2000000-0000-0000-0000-000000000001',repeat('a',64),'text/plain')$q$);
reset role;
set local role aedrova_website;
select pg_temp.denied($q$select public.finish_verified_attachment('b1000000-0000-0000-0000-000000000002','b2000000-0000-0000-0000-000000000001',repeat('a',64),'text/plain')$q$);
select pg_temp.denied($q$select public.finish_verified_attachment('b1000000-0000-0000-0000-000000000001','b2000000-0000-0000-0000-000000000001',repeat('b',64),'text/plain')$q$);
select public.finish_verified_attachment('b1000000-0000-0000-0000-000000000001','b2000000-0000-0000-0000-000000000001',repeat('a',64),'text/plain');
select public.finish_verified_attachment('b1000000-0000-0000-0000-000000000001','b2000000-0000-0000-0000-000000000001',repeat('a',64),'text/plain');
reset role;
select pg_temp.check_true((select count(*)=1 from public.messages where id='b2000000-0000-0000-0000-000000000001'),'verified upload publishes once');
set local role authenticated;
set local request.jwt.claim.sub='b1000000-0000-0000-0000-000000000001';
select pg_temp.denied($q$select public.abandon_attachment('b2000000-0000-0000-0000-000000000001')$q$);
select public.reserve_attachment('b2000000-0000-0000-0000-000000000002',current_setting('test.c')::uuid,'cancel.txt',3,repeat('a',64));
select public.abandon_attachment('b2000000-0000-0000-0000-000000000002');
select pg_temp.check_true((select count(*)=0 from public.attachments where id='b2000000-0000-0000-0000-000000000002'),'cancelled pending upload unpublished');
rollback;
