begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('20000000-0000-0000-0000-000000000001','owner@chat.test',now()),
 ('20000000-0000-0000-0000-000000000002','outsider@chat.test',now());
create or replace function pg_temp.check_true(ok boolean, description text) returns void
language plpgsql as $$ begin if ok is distinct from true then raise exception 'FAIL: %',description; end if; end $$;
create or replace function pg_temp.denied(statement text) returns void language plpgsql as $$
begin begin execute statement; exception when insufficient_privilege then return; end;
 raise exception 'FAIL: unauthorized operation succeeded'; end $$;
set local role authenticated;
set local request.jwt.claim.sub='20000000-0000-0000-0000-000000000001';
select set_config('test.w',public.onboard_workspace('Chat','Nova','codex')::text,true);
select set_config('test.c',(select id::text from public.channels limit 1),true);
select public.send_message('30000000-0000-0000-0000-000000000001',current_setting('test.c')::uuid,'Hello');
select public.send_message('30000000-0000-0000-0000-000000000001',current_setting('test.c')::uuid,'Hello');
select pg_temp.check_true((select count(*)=1 from public.messages),'idempotent retry');
select pg_temp.denied($q$select public.send_message('30000000-0000-0000-0000-000000000001',current_setting('test.c')::uuid,'Changed')$q$);
select public.send_message('30000000-0000-0000-0000-000000000002',current_setting('test.c')::uuid,'Reply','30000000-0000-0000-0000-000000000001');
select pg_temp.check_true((select count(*)=2 from public.messages),'thread saved');
select pg_temp.denied($q$select public.send_message('30000000-0000-0000-0000-000000000003',current_setting('test.c')::uuid,'Nested','30000000-0000-0000-0000-000000000002')$q$);
select pg_temp.denied('delete from public.messages');
select pg_temp.denied('update public.messages set body=''tampered''');
select set_config('test.other',public.create_channel(current_setting('test.w')::uuid,'other')::text,true);
select pg_temp.denied($q$select public.send_message('30000000-0000-0000-0000-000000000003',current_setting('test.other')::uuid,'Wrong channel','30000000-0000-0000-0000-000000000001')$q$);
set local request.jwt.claim.sub='20000000-0000-0000-0000-000000000002';
select pg_temp.check_true((select count(*)=0 from public.messages),'outsider read denied');
select pg_temp.denied($q$select public.send_message('30000000-0000-0000-0000-000000000003',current_setting('test.c')::uuid,'Intruder')$q$);
set local request.jwt.claim.sub='20000000-0000-0000-0000-000000000001';
select set_config('test.private',public.create_channel(current_setting('test.w')::uuid,'private',true)::text,true);
select public.send_message('30000000-0000-0000-0000-000000000004',current_setting('test.private')::uuid,'Private');
select set_config('test.invite',public.create_invitation(current_setting('test.w')::uuid,'outsider@chat.test','member'),true);
set local request.jwt.claim.sub='20000000-0000-0000-0000-000000000002';
select public.accept_invitation(current_setting('test.invite'));
select pg_temp.check_true((select count(*)=2 from public.messages),'member sees public messages but not private');
select pg_temp.denied($q$select public.send_message('30000000-0000-0000-0000-000000000005',current_setting('test.private')::uuid,'Private intruder')$q$);
set local request.jwt.claim.sub='20000000-0000-0000-0000-000000000001';
select public.remove_member(current_setting('test.w')::uuid,'20000000-0000-0000-0000-000000000002');
set local request.jwt.claim.sub='20000000-0000-0000-0000-000000000002';
select pg_temp.check_true((select count(*)=0 from public.messages),'revoked member loses history');
select pg_temp.denied($q$select public.send_message('30000000-0000-0000-0000-000000000005',current_setting('test.c')::uuid,'Revoked')$q$);
reset role;
set local role anon;
select pg_temp.denied('select * from public.messages');
select pg_temp.denied($q$select public.send_message('30000000-0000-0000-0000-000000000003',current_setting('test.c')::uuid,'Anon')$q$);
rollback;
