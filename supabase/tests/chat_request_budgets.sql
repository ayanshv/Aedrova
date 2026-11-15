begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('95000000-0000-0000-0000-000000000001','owner@chat-budget.test',now()),
 ('95000000-0000-0000-0000-000000000002','member@chat-budget.test',now());

create function pg_temp.expect_denied(statement text) returns void language plpgsql as $$
begin
 execute statement;
 raise exception 'Expected access denial';
exception when insufficient_privilege then return;
end $$;

create function pg_temp.expect_limited(statement text) returns void language plpgsql as $$
begin
 execute statement;
 raise exception 'Expected rate limit';
exception when raise_exception then
 if sqlerrm <> 'Too many requests. Wait before retrying.' then raise; end if;
end $$;

set local role authenticated;
set local request.jwt.claim.sub='95000000-0000-0000-0000-000000000001';
select set_config('test.w',public.onboard_workspace('Chat budget','Aedrova','codex')::text,true);
select set_config('test.c',(select id::text from public.channels where workspace_id=current_setting('test.w')::uuid limit 1),true);
select set_config('test.i',public.create_invitation(current_setting('test.w')::uuid,'member@chat-budget.test')::text,true);
set local request.jwt.claim.sub='95000000-0000-0000-0000-000000000002';
select pg_temp.expect_denied($q$select public.message_page(current_setting('test.c')::uuid)$q$);
select public.accept_invitation(current_setting('test.i'));
set local request.jwt.claim.sub='95000000-0000-0000-0000-000000000001';
select public.start_direct_message(current_setting('test.w')::uuid,'95000000-0000-0000-0000-000000000002');
select public.message_page(current_setting('test.c')::uuid);
select public.chat_inventory(current_setting('test.w')::uuid);
select pg_temp.expect_denied($q$select aedrova_private.message_page(current_setting('test.c')::uuid)$q$);
reset role;

insert into aedrova_private.write_budgets(user_id,bucket,window_start,count)
select '95000000-0000-0000-0000-000000000001'::uuid, bucket,
 floor(extract(epoch from clock_timestamp())/60)::bigint*60 + offset_seconds, allowance
from (values ('direct-message-open',30), ('message-page',180), ('chat-inventory',90)) as limits(bucket,allowance)
cross join (values (0),(60)) as windows(offset_seconds)
on conflict(user_id,bucket,window_start) do update set count=excluded.count;

set local role authenticated;
select pg_temp.expect_limited($q$select public.start_direct_message(
 current_setting('test.w')::uuid,'95000000-0000-0000-0000-000000000002')$q$);
select pg_temp.expect_limited($q$select public.message_page(current_setting('test.c')::uuid)$q$);
select pg_temp.expect_limited($q$select public.chat_inventory(current_setting('test.w')::uuid)$q$);
set local request.jwt.claim.sub='95000000-0000-0000-0000-000000000002';
select public.message_page(current_setting('test.c')::uuid);
set local role anon;
select pg_temp.expect_denied($q$select public.chat_inventory(current_setting('test.w')::uuid)$q$);
rollback;
