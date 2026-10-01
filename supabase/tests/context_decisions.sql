begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('60000000-0000-0000-0000-000000000001','owner@context.test',now()),
 ('60000000-0000-0000-0000-000000000002','member@context.test',now());
create or replace function pg_temp.check_true(ok boolean, description text) returns void
language plpgsql as $$ begin if ok is distinct from true then raise exception 'FAIL: %',description; end if; end $$;
create or replace function pg_temp.denied(statement text) returns void language plpgsql as $$
begin begin execute statement; exception when insufficient_privilege then return; end;
 raise exception 'FAIL: unauthorized operation succeeded'; end $$;
set local role authenticated;
set local request.jwt.claim.sub='60000000-0000-0000-0000-000000000001';
select set_config('test.w',public.onboard_workspace('Context','Nova','codex')::text,true);
select set_config('test.c',(select id::text from public.channels limit 1),true);
select public.send_message('61000000-0000-0000-0000-000000000001',current_setting('test.c')::uuid,'Export CSV');
select public.set_context_decision('61000000-0000-0000-0000-000000000001','Export CSV',true);
select pg_temp.check_true((select confirmed and source_body='Export CSV' and confirmed_by=auth.uid() from public.context_decisions),'confirmed with provenance');
select public.set_context_decision('61000000-0000-0000-0000-000000000001','Export CSV',false);
select pg_temp.check_true((select not confirmed from public.context_decisions),'retired');
do $$ begin
 begin perform public.set_context_decision('61000000-0000-0000-0000-000000000001','Old body',true);
 exception when serialization_failure then return; end;
 raise exception 'FAIL: stale source accepted'; end $$;
select pg_temp.denied('update public.context_decisions set confirmed=true');
select set_config('test.private',public.create_channel(current_setting('test.w')::uuid,'private',true)::text,true);
select public.send_message('61000000-0000-0000-0000-000000000002',current_setting('test.private')::uuid,'Private requirement');
select public.set_context_decision('61000000-0000-0000-0000-000000000002','Private requirement',true);
set local request.jwt.claim.sub='60000000-0000-0000-0000-000000000002';
select pg_temp.check_true((select count(*)=0 from public.context_decisions),'outsider has no evidence');
select pg_temp.denied($q$select public.set_context_decision('61000000-0000-0000-0000-000000000001','Export CSV',true)$q$);
set local request.jwt.claim.sub='60000000-0000-0000-0000-000000000001';
select set_config('test.invite',public.create_invitation(current_setting('test.w')::uuid,'member@context.test','member'),true);
set local request.jwt.claim.sub='60000000-0000-0000-0000-000000000002';
select public.accept_invitation(current_setting('test.invite'));
select pg_temp.check_true((select count(*)=1 from public.context_decisions),'private source decisions hidden');
select pg_temp.denied($q$select public.set_context_decision('61000000-0000-0000-0000-000000000002','Private requirement',true)$q$);
select public.set_context_decision('61000000-0000-0000-0000-000000000001','Export CSV',true);
set local request.jwt.claim.sub='60000000-0000-0000-0000-000000000001';
select public.remove_member(current_setting('test.w')::uuid,'60000000-0000-0000-0000-000000000002');
set local request.jwt.claim.sub='60000000-0000-0000-0000-000000000002';
select pg_temp.check_true((select count(*)=0 from public.context_decisions),'revocation removes decision access');
select pg_temp.denied($q$select public.set_context_decision('61000000-0000-0000-0000-000000000001','Export CSV',false)$q$);
reset role;
-- Service-side deletion must remove the decision, including its copied source text.
delete from public.messages where id='61000000-0000-0000-0000-000000000002';
select pg_temp.check_true((select count(*)=0 from public.context_decisions where message_id='61000000-0000-0000-0000-000000000002'),'deleted source cascades');
set local role anon;
select pg_temp.denied('select * from public.context_decisions');
select pg_temp.denied($q$select public.set_context_decision('61000000-0000-0000-0000-000000000001','Export CSV',true)$q$);
reset role;
set local role authenticated;
set local request.jwt.claim.sub='60000000-0000-0000-0000-000000000001';
select set_config('test.revision',public.context_revision(current_setting('test.c')::uuid)::text,true);
reset role;
update public.messages set body='Edited requirement' where id='61000000-0000-0000-0000-000000000001';
set local role authenticated;
select pg_temp.check_true(public.context_revision(current_setting('test.c')::uuid)>current_setting('test.revision')::bigint,'edits invalidate revision');
select set_config('test.revision',public.context_revision(current_setting('test.c')::uuid)::text,true);
reset role;
delete from public.messages where id='61000000-0000-0000-0000-000000000001';
set local role authenticated;
select pg_temp.check_true(public.context_revision(current_setting('test.c')::uuid)>current_setting('test.revision')::bigint,'deletions invalidate revision');
set local request.jwt.claim.sub='60000000-0000-0000-0000-000000000002';
select pg_temp.denied($q$select public.context_revision(current_setting('test.c')::uuid)$q$);
rollback;
