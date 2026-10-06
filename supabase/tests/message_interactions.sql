begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('94000000-0000-0000-0000-000000000001','sender@reactions.test',now()),
 ('94000000-0000-0000-0000-000000000002','member@reactions.test',now()),
 ('94000000-0000-0000-0000-000000000003','outsider@reactions.test',now());
create or replace function pg_temp.check_true(ok boolean, description text) returns void
language plpgsql as $$ begin if ok is distinct from true then raise exception 'FAIL: %',description; end if; end $$;
create or replace function pg_temp.denied(statement text) returns void language plpgsql as $$
begin begin execute statement; exception when insufficient_privilege then return; end;
 raise exception 'FAIL: unauthorized operation succeeded'; end $$;
set local role authenticated;
set local request.jwt.claim.sub='94000000-0000-0000-0000-000000000001';
select set_config('test.w',public.onboard_workspace('Reactions','Aedrova','codex')::text,true);
select set_config('test.c',(select id::text from public.channels limit 1),true);
select public.send_message('94000000-0000-0000-0000-000000000011',current_setting('test.c')::uuid,'Erase this original');
select public.send_message('94000000-0000-0000-0000-000000000012',current_setting('test.c')::uuid,'Keep this reply','94000000-0000-0000-0000-000000000011');
select public.set_context_decision('94000000-0000-0000-0000-000000000011','Erase this original',true);
select public.set_message_reaction('94000000-0000-0000-0000-000000000011','👍',true);
select public.set_message_reaction('94000000-0000-0000-0000-000000000011','👍',true);
select pg_temp.check_true((select count(*)=1 from public.message_reactions),'reaction retry is idempotent');
-- Unsend also revokes attachment metadata and Storage access.
select set_config('test.path',public.reserve_attachment('94000000-0000-0000-0000-000000000014',current_setting('test.c')::uuid,'notes.txt',3,repeat('a',64)),true);
insert into storage.objects(bucket_id,name,metadata) values('aedrova-files',current_setting('test.path'),'{"size":3}');
select public.finish_attachment('94000000-0000-0000-0000-000000000014');
select public.unsend_message('94000000-0000-0000-0000-000000000014');
select pg_temp.check_true((select count(*)=0 from public.attachments),'attachment metadata removed');
select pg_temp.check_true((select count(*)=0 from storage.objects where name=current_setting('test.path')),'attachment Storage access revoked');
select set_config('test.private',public.create_channel(current_setting('test.w')::uuid,'private',true)::text,true);
select public.send_message('94000000-0000-0000-0000-000000000013',current_setting('test.private')::uuid,'Private');
select set_config('test.invite',public.create_invitation(current_setting('test.w')::uuid,'member@reactions.test','member'),true);
set local request.jwt.claim.sub='94000000-0000-0000-0000-000000000002';
select public.accept_invitation(current_setting('test.invite'));
select pg_temp.denied($q$select public.set_message_reaction('94000000-0000-0000-0000-000000000013','👍',true)$q$);
select pg_temp.check_true(public.message_interactions(array['94000000-0000-0000-0000-000000000013'::uuid])='[]'::jsonb,'private channel metadata isolated');
select public.set_message_reaction('94000000-0000-0000-0000-000000000011','👍',true);
select pg_temp.check_true((public.message_interactions(array['94000000-0000-0000-0000-000000000011'::uuid])->0->'reactions'->0->>'count')::int=2,'both accounts aggregate');
select pg_temp.denied($q$select public.unsend_message('94000000-0000-0000-0000-000000000011')$q$);
select public.set_message_reaction('94000000-0000-0000-0000-000000000011','👍',false);
select pg_temp.check_true((select count(*)=1 from public.message_reactions),'remove only own reaction');
select public.set_message_reaction('94000000-0000-0000-0000-000000000011','👩🏽‍💻',true);
set local request.jwt.claim.sub='94000000-0000-0000-0000-000000000003';
select pg_temp.check_true(public.message_interactions(array['94000000-0000-0000-0000-000000000011'::uuid])='[]'::jsonb,'outsider metadata isolated');
select pg_temp.denied($q$select public.set_message_reaction('94000000-0000-0000-0000-000000000011','❤️',true)$q$);
select pg_temp.denied($q$select public.unsend_message('94000000-0000-0000-0000-000000000011')$q$);
set local request.jwt.claim.sub='94000000-0000-0000-0000-000000000001';
select set_config('test.revision',public.context_revision(current_setting('test.c')::uuid)::text,true);
select public.unsend_message('94000000-0000-0000-0000-000000000011');
select public.unsend_message('94000000-0000-0000-0000-000000000011');
select pg_temp.check_true((select body='Message unsent.' and unsent_at is not null from public.messages where id='94000000-0000-0000-0000-000000000011'),'original body erased');
select pg_temp.check_true((select body='Keep this reply' from public.messages where id='94000000-0000-0000-0000-000000000012'),'thread intact');
select pg_temp.check_true((select count(*)=0 from public.context_decisions),'decision body erased');
select pg_temp.check_true((select count(*)=0 from public.message_reactions),'unsend clears reactions');
select pg_temp.check_true(public.context_revision(current_setting('test.c')::uuid)>current_setting('test.revision')::bigint,'build context invalidated');
select pg_temp.denied($q$select public.set_message_reaction('94000000-0000-0000-0000-000000000011','👍',true)$q$);
select pg_temp.denied('insert into public.message_reactions values(''94000000-0000-0000-0000-000000000012'',''94000000-0000-0000-0000-000000000002'',''👍'')');
select public.remove_member(current_setting('test.w')::uuid,'94000000-0000-0000-0000-000000000002');
set local request.jwt.claim.sub='94000000-0000-0000-0000-000000000002';
select pg_temp.denied($q$select public.set_message_reaction('94000000-0000-0000-0000-000000000012','👍',true)$q$);
select pg_temp.check_true(public.message_interactions(array['94000000-0000-0000-0000-000000000012'::uuid])='[]'::jsonb,'revoked member metadata denied');
reset role;
select pg_temp.check_true(not exists(select 1 from realtime.test_events where payload<>'{}'::jsonb),'notifications contain no message content');
set local role anon;
select pg_temp.denied($q$select public.message_interactions(array['94000000-0000-0000-0000-000000000012'::uuid])$q$);
rollback;
