begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('90000000-0000-0000-0000-000000000001','owner@scale.test',now()),
 ('90000000-0000-0000-0000-000000000002','foreign@scale.test',now());
create or replace function pg_temp.check_true(ok boolean, description text) returns void
language plpgsql as $$ begin if ok is distinct from true then raise exception 'FAIL: %',description; end if; end $$;
create or replace function pg_temp.denied(statement text) returns void language plpgsql as $$
begin begin execute statement; exception when insufficient_privilege then return; end;
 raise exception 'FAIL: unauthorized operation succeeded'; end $$;
set local role authenticated;
set local request.jwt.claim.sub='90000000-0000-0000-0000-000000000001';
select set_config('test.w',public.onboard_workspace('Scale','Aedrova','codex')::text,true);
select set_config('test.c',(select id::text from public.channels where workspace_id=current_setting('test.w')::uuid limit 1),true);
select public.send_message('91000000-0000-0000-0000-000000000001',current_setting('test.c')::uuid,'Invoice export UTC');
select pg_temp.check_true((select count(*)=1 from public.search_workspace_context(current_setting('test.w')::uuid,'invoice')),'search retrieves evidence');
select pg_temp.check_true((select count(*)=0 from public.search_workspace_context(current_setting('test.w')::uuid,'unrelated')),'no fabricated results');
select pg_temp.check_true((select count(*)=1 from public.search_workspace_context(current_setting('test.w')::uuid,'invoice',1)),'search limit');
set local request.jwt.claim.sub='90000000-0000-0000-0000-000000000002';
select set_config('test.other',public.onboard_workspace('Other','Aedrova','codex')::text,true);
select pg_temp.denied($q$select public.search_workspace_context(current_setting('test.w')::uuid,'invoice')$q$);
select pg_temp.check_true((select count(*)=0 from public.search_workspace_context(current_setting('test.other')::uuid,'invoice')),'workspace isolation');
set local request.jwt.claim.sub='90000000-0000-0000-0000-000000000001';
select set_config('test.private',public.create_channel(current_setting('test.w')::uuid,'private',true)::text,true);
select public.send_message('91000000-0000-0000-0000-000000000003',current_setting('test.private')::uuid,'Invoice private');
select set_config('test.invite',public.create_invitation(current_setting('test.w')::uuid,'foreign@scale.test')::text,true);
set local request.jwt.claim.sub='90000000-0000-0000-0000-000000000002';
select public.accept_invitation(current_setting('test.invite'));
select pg_temp.check_true((select count(*)=1 from public.search_workspace_context(current_setting('test.w')::uuid,'invoice')),'private channel excluded for ordinary member');
set local request.jwt.claim.sub='90000000-0000-0000-0000-000000000001';
reset role;
-- Force the fixture's current window to its cap, without sending 120 broadcasts.
insert into aedrova_private.write_budgets values(
 '90000000-0000-0000-0000-000000000001','message',
 floor(extract(epoch from clock_timestamp())/60)::bigint*60,120)
 on conflict(user_id,bucket,window_start) do update set count=120;
set local role authenticated;
do $$ begin
 begin perform public.send_message('91000000-0000-0000-0000-000000000002',current_setting('test.c')::uuid,'Blocked');
 exception when raise_exception then
 if sqlerrm like 'Too many requests.%' then return; end if; raise;
 end;
 raise exception 'FAIL: direct RPC bypassed rate cap';
end $$;
select public.send_message('91000000-0000-0000-0000-000000000001',current_setting('test.c')::uuid,'Invoice export UTC');
select pg_temp.check_true((select count(*)=0 from public.messages where id='91000000-0000-0000-0000-000000000002'),'blocked insert rolled back');
select pg_temp.denied('select * from aedrova_private.write_budgets');
set local role anon;
select pg_temp.denied($q$select public.search_workspace_context(current_setting('test.w')::uuid,'invoice')$q$);
rollback;
