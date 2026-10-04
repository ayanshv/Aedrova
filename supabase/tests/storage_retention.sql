begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('a3000000-0000-0000-0000-000000000001','storage@test.local',now()),
 ('a3000000-0000-0000-0000-000000000002','outsider@test.local',now());
create or replace function pg_temp.check_true(ok boolean, description text) returns void
language plpgsql as $$ begin if ok is distinct from true then raise exception 'FAIL: %',description; end if; end $$;
create or replace function pg_temp.denied(statement text) returns void language plpgsql as $$
begin begin execute statement; exception when insufficient_privilege then return; end;
 raise exception 'FAIL: unauthorized operation succeeded: %',statement; end $$;
set local role authenticated;
set local request.jwt.claim.sub='a3000000-0000-0000-0000-000000000001';
select set_config('test.w',public.onboard_workspace('Storage','Aedrova','codex')::text,true);
select set_config('test.c',(select id::text from public.channels where workspace_id=current_setting('test.w')::uuid limit 1),true);
select set_config('test.path',public.reserve_attachment('a4000000-0000-0000-0000-000000000001',current_setting('test.c')::uuid,'live.txt',3,repeat('a',64)),true);
insert into storage.objects(bucket_id,name,metadata) values('aedrova-files',current_setting('test.path'),'{"size":3}');
select public.finish_attachment('a4000000-0000-0000-0000-000000000001');
select pg_temp.denied('select * from aedrova_private.storage_usage');
select pg_temp.denied('select * from public.claim_storage_cleanup()');
reset role;
update aedrova_private.storage_usage set limit_bytes=10485763 where workspace_id=current_setting('test.w')::uuid;
set local role authenticated;
select set_config('test.pending',public.reserve_attachment('a4000000-0000-0000-0000-000000000002',current_setting('test.c')::uuid,'pending.txt',3,repeat('a',64)),true);
-- A retry does not charge twice.
select public.reserve_attachment('a4000000-0000-0000-0000-000000000002',current_setting('test.c')::uuid,'pending.txt',3,repeat('a',64));
do $$ begin
 begin perform public.reserve_attachment('a4000000-0000-0000-0000-000000000003',current_setting('test.c')::uuid,'over.txt',1,repeat('a',64));
 exception when program_limit_exceeded then return; end;
 raise exception 'FAIL quota overflow accepted'; end $$;
set local request.jwt.claim.sub='a3000000-0000-0000-0000-000000000002';
select pg_temp.denied($q$select public.reserve_attachment('a4000000-0000-0000-0000-000000000004',current_setting('test.c')::uuid,'outside.txt',1,repeat('a',64))$q$);
reset role;
select pg_temp.check_true((select used_bytes=10485763 from aedrova_private.storage_usage where workspace_id=current_setting('test.w')::uuid),'reserved bytes counted once');
update public.attachments set expires_at=now()-interval '48 hours' where object_path=current_setting('test.pending');
select * from public.claim_storage_cleanup();
select pg_temp.check_true((select count(*)=1 from public.attachments where object_path=current_setting('test.path')),'finalized object preserved');
select pg_temp.check_true((select used_bytes=10485763 from aedrova_private.storage_usage where workspace_id=current_setting('test.w')::uuid),'expired bytes held until API deletion');
select pg_temp.check_true(not public.finish_storage_cleanup(current_setting('test.pending'),null),'unclaimed/null lease cannot release bytes');
update aedrova_private.storage_cleanup set ready_at=now()-interval '1 hour';
set local role service_role;
select set_config('test.lease',(select lease::text from public.claim_storage_cleanup()),true);
select pg_temp.check_true((select count(*)=0 from public.claim_storage_cleanup()),'active lease not double claimed');
select pg_temp.check_true(not public.finish_storage_cleanup(current_setting('test.pending'),gen_random_uuid()),'stale token rejected');
select pg_temp.check_true(public.finish_storage_cleanup(current_setting('test.pending'),current_setting('test.lease')::uuid),'missing upload safely acknowledged');
select pg_temp.check_true(not public.finish_storage_cleanup(current_setting('test.pending'),current_setting('test.lease')::uuid),'finish idempotent without double decrement');
reset role;
select pg_temp.check_true((select used_bytes=3 from aedrova_private.storage_usage where workspace_id=current_setting('test.w')::uuid),'bytes released once');
set local role authenticated;
set local request.jwt.claim.sub='a3000000-0000-0000-0000-000000000001';
select pg_temp.denied($q$select public.reserve_attachment('a4000000-0000-0000-0000-000000000002',current_setting('test.c')::uuid,'pending.txt',3,repeat('a',64))$q$);
reset role;
-- Cascade deletion preserves a cleanup tombstone, and existing Storage metadata prevents ack.
delete from public.attachments where object_path=current_setting('test.path');
update aedrova_private.storage_cleanup set ready_at=now()-interval '1 hour';
select set_config('test.lease',(select lease::text from public.claim_storage_cleanup()),true);
do $$ begin
 begin perform public.finish_storage_cleanup(current_setting('test.path'),current_setting('test.lease')::uuid);
 exception when raise_exception then return; end;
 raise exception 'FAIL existing object released'; end $$;
-- Fixture simulates Storage API deletion; production worker never deletes metadata in SQL.
delete from storage.objects where name=current_setting('test.path');
select pg_temp.check_true(public.finish_storage_cleanup(current_setting('test.path'),current_setting('test.lease')::uuid),'API deletion ack releases bytes');
select pg_temp.check_true((select used_bytes=0 from aedrova_private.storage_usage where workspace_id=current_setting('test.w')::uuid),'all retired bytes released');
set local role authenticated;
select set_config('test.cascade',public.reserve_attachment('a4000000-0000-0000-0000-000000000005',current_setting('test.c')::uuid,'cascade.txt',2,repeat('a',64)),true);
reset role;
delete from public.workspaces where id=current_setting('test.w')::uuid;
select pg_temp.check_true((select count(*)=1 from aedrova_private.storage_cleanup where object_path=current_setting('test.cascade')),'workspace cascade retains orphan work');
select pg_temp.check_true((select used_bytes=10485760 from aedrova_private.storage_usage where workspace_id=current_setting('test.w')::uuid),'workspace cascade does not release undeleted bytes');
update aedrova_private.storage_cleanup set ready_at=now()-interval '1 hour';
select set_config('test.oldlease',(select lease::text from public.claim_storage_cleanup()),true);
update aedrova_private.storage_cleanup set lease_until=now()-interval '1 hour';
select set_config('test.newlease',(select lease::text from public.claim_storage_cleanup()),true);
select pg_temp.check_true(current_setting('test.oldlease')<>current_setting('test.newlease'),'expired worker lease rotates');
select pg_temp.check_true(not public.finish_storage_cleanup(current_setting('test.cascade'),current_setting('test.oldlease')::uuid),'old worker cannot finish renewed lease');
select pg_temp.check_true(public.finish_storage_cleanup(current_setting('test.cascade'),current_setting('test.newlease')::uuid),'new worker can finish');
rollback;
