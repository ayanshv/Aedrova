begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('f4000000-0000-0000-0000-000000000001','bud-chat-owner@test.local',now()),
 ('f4000000-0000-0000-0000-000000000002','bud-chat-member@test.local',now()),
 ('f4000000-0000-0000-0000-000000000003','bud-chat-outsider@test.local',now());
create or replace function pg_temp.check_true(ok boolean,description text) returns void language plpgsql as $$
begin if ok is distinct from true then raise exception 'FAIL: %',description; end if; end $$;
create or replace function pg_temp.denied(statement text,code text default '42501') returns void language plpgsql as $$
declare actual text;
begin begin execute statement; exception when others then get stacked diagnostics actual=returned_sqlstate;
 if actual=code then return; end if; raise; end; raise exception 'FAIL: unauthorized action succeeded'; end $$;
set local role authenticated;
set local request.jwt.claim.sub='f4000000-0000-0000-0000-000000000001';
select set_config('test.w',public.onboard_workspace('Private Bud chat','Aedrova','codex')::text,true);
select set_config('test.b',(public.save_workspace_bud(null,current_setting('test.w')::uuid,0,'github','owner/repo','Builder')).id::text,true);
select set_config('test.message',gen_random_uuid()::text,true);
select public.append_bud_message(current_setting('test.message')::uuid,current_setting('test.b')::uuid,'Private launch idea');
select public.append_bud_message(current_setting('test.message')::uuid,current_setting('test.b')::uuid,'Private launch idea');
select pg_temp.check_true((select count(*)=1 from public.bud_conversation(current_setting('test.b')::uuid)),'retry is idempotent');
select public.append_bud_message(gen_random_uuid(),current_setting('test.b')::uuid,'A private answer',current_setting('test.message')::uuid);
select public.append_bud_message(gen_random_uuid(),current_setting('test.b')::uuid,'Concurrent answer',current_setting('test.message')::uuid);
select pg_temp.check_true((select count(*)=2 from public.bud_conversation(current_setting('test.b')::uuid)),'one answer per question');
select pg_temp.denied('insert into public.bud_messages(id,bud_id,user_id,role,body) values(gen_random_uuid(),current_setting(''test.b'')::uuid,auth.uid(),''user'',''bypass'')');
select pg_temp.denied('select public.append_bud_message(gen_random_uuid(),current_setting(''test.b'')::uuid,repeat(''x'',20001))','P0001');
select pg_temp.denied('select public.append_bud_message(current_setting(''test.message'')::uuid,current_setting(''test.b'')::uuid,''changed'')');
select set_config('test.invite',public.create_invitation(current_setting('test.w')::uuid,'bud-chat-member@test.local','member'),true);
set local request.jwt.claim.sub='f4000000-0000-0000-0000-000000000002';
select public.accept_invitation(current_setting('test.invite'));
select pg_temp.check_true((select count(*)=0 from public.bud_messages),'member cannot read owner history');
select pg_temp.check_true((select count(*)=0 from public.bud_conversation(current_setting('test.b')::uuid)),'RPC also isolates members');
select pg_temp.denied('select public.append_bud_message(gen_random_uuid(),current_setting(''test.b'')::uuid,''spoof'',current_setting(''test.message'')::uuid)');
select public.append_bud_message(gen_random_uuid(),current_setting('test.b')::uuid,'Member private question');
set local request.jwt.claim.sub='f4000000-0000-0000-0000-000000000003';
select pg_temp.check_true((select count(*)=0 from public.bud_messages),'outsider reads nothing');
select pg_temp.denied('select * from public.bud_conversation(current_setting(''test.b'')::uuid)');
select pg_temp.denied('select public.append_bud_message(gen_random_uuid(),current_setting(''test.b'')::uuid,''outside'')');
set local request.jwt.claim.sub='f4000000-0000-0000-0000-000000000001';
select pg_temp.check_true((select count(*)=2 from public.bud_messages),'owner cannot read member private question');
select public.remove_member(current_setting('test.w')::uuid,'f4000000-0000-0000-0000-000000000002');
set local request.jwt.claim.sub='f4000000-0000-0000-0000-000000000002';
select pg_temp.check_true((select count(*)=0 from public.bud_messages),'removed member history hidden');
select pg_temp.denied('select public.append_bud_message(gen_random_uuid(),current_setting(''test.b'')::uuid,''revoked'')');
set local request.jwt.claim.sub='f4000000-0000-0000-0000-000000000001';
do $$ begin for i in 1..28 loop
 perform public.append_bud_message(gen_random_uuid(),current_setting('test.b')::uuid,'Rate test');
end loop; end $$;
select pg_temp.denied('select public.append_bud_message(gen_random_uuid(),current_setting(''test.b'')::uuid,''too fast'')','P0001');
select public.remove_workspace_dot(current_setting('test.b')::uuid,current_setting('test.w')::uuid,1);
select pg_temp.denied('select public.append_bud_message(gen_random_uuid(),current_setting(''test.b'')::uuid,''deleted'')');
select pg_temp.check_true((select count(*)=0 from public.bud_messages),'removed Bud history hidden');
rollback;
