begin;
insert into auth.users(id,email,email_confirmed_at,raw_user_meta_data) values
 ('40000000-0000-0000-0000-000000000001','owner@chat.test',now(),'{"full_name":"Owner"}'),
 ('40000000-0000-0000-0000-000000000002','member@chat.test',now(),'{"full_name":"Member"}'),
 ('40000000-0000-0000-0000-000000000003','admin@chat.test',now(),'{}'),
 ('40000000-0000-0000-0000-000000000004','outside@chat.test',now(),'{}');
create or replace function pg_temp.check_true(ok boolean, description text) returns void
language plpgsql as $$ begin if ok is distinct from true then raise exception 'FAIL: %',description; end if; end $$;
create or replace function pg_temp.denied(statement text) returns void language plpgsql as $$
begin begin execute statement; exception when insufficient_privilege then return; end;
 raise exception 'FAIL: unauthorized operation succeeded: %',statement; end $$;
set local role authenticated;
set local request.jwt.claim.sub='40000000-0000-0000-0000-000000000001';
select set_config('test.w',public.onboard_workspace('Team','Nova','codex')::text,true);
select set_config('test.c',(select id::text from public.channels limit 1),true);
select set_config('test.invite',public.create_invitation(current_setting('test.w')::uuid,'member@chat.test'),true);
select set_config('test.admin',public.create_invitation(current_setting('test.w')::uuid,'admin@chat.test','admin'),true);
set local request.jwt.claim.sub='40000000-0000-0000-0000-000000000002';
select public.accept_invitation(current_setting('test.invite'));
set local request.jwt.claim.sub='40000000-0000-0000-0000-000000000003';
select public.accept_invitation(current_setting('test.admin'));
set local request.jwt.claim.sub='40000000-0000-0000-0000-000000000001';
select pg_temp.check_true((select count(*)=3 from public.team_directory()),'directory only team');
select set_config('test.dm',public.start_direct_message(current_setting('test.w')::uuid,'40000000-0000-0000-0000-000000000002')::text,true);
select pg_temp.check_true(public.start_direct_message(current_setting('test.w')::uuid,'40000000-0000-0000-0000-000000000002')::text=current_setting('test.dm'),'DM retry reuses pair');
select pg_temp.denied($q$select public.start_direct_message(current_setting('test.w')::uuid,'40000000-0000-0000-0000-000000000004')$q$);
select public.send_message('50000000-0000-0000-0000-000000000001',current_setting('test.dm')::uuid,'Secret DM');
select public.send_message('50000000-0000-0000-0000-000000000002',current_setting('test.c')::uuid,'Public root');
select public.send_message('50000000-0000-0000-0000-000000000003',current_setting('test.c')::uuid,'Reply','50000000-0000-0000-0000-000000000002');
select pg_temp.check_true((select count(*)=1 from public.message_page(current_setting('test.c')::uuid)),'root pagination excludes replies');
select pg_temp.check_true((select count(*)=1 from public.message_page(current_setting('test.c')::uuid,p_parent=>'50000000-0000-0000-0000-000000000002')),'thread pagination independent');
select pg_temp.check_true((select count(*)=0 from public.message_page(current_setting('test.c')::uuid,p_before=>1)),'strict before boundary');
set local request.jwt.claim.sub='40000000-0000-0000-0000-000000000003';
select pg_temp.check_true((select count(*)=0 from public.channels where kind='dm'),'admin cannot see other DM');
select pg_temp.denied($q$select public.set_channel_member(current_setting('test.dm')::uuid,'40000000-0000-0000-0000-000000000003',true)$q$);
select pg_temp.denied($q$select * from public.message_page(current_setting('test.dm')::uuid)$q$);
set local request.jwt.claim.sub='40000000-0000-0000-0000-000000000002';
select pg_temp.check_true((select unread=2 from public.unread_counts() where channel_id=current_setting('test.c')::uuid),'unread includes replies');
select public.mark_channel_read(current_setting('test.c')::uuid,(select max(sequence) from public.messages where channel_id=current_setting('test.c')::uuid));
select public.mark_channel_read(current_setting('test.c')::uuid,0);
select pg_temp.check_true((select unread=0 from public.unread_counts() where channel_id=current_setting('test.c')::uuid),'read cursor cannot move backwards');
-- Reserve and upload one file. Metadata size comes from Storage, not the attachment caller.
select set_config('test.path',public.reserve_attachment('60000000-0000-0000-0000-000000000001',current_setting('test.dm')::uuid,'notes.txt',3,repeat('a',64)),true);
select pg_temp.check_true(aedrova_private.can_upload_object(current_setting('test.path')),'reserved owner can upload');
select pg_temp.check_true(not aedrova_private.can_upload_object('wrong/path'),'unreserved upload denied');
insert into storage.objects(bucket_id,name,metadata) values('aedrova-files',current_setting('test.path'),'{"size":3}');
select public.finish_attachment('60000000-0000-0000-0000-000000000001');
select public.finish_attachment('60000000-0000-0000-0000-000000000001');
select pg_temp.check_true((select count(*)=1 from public.messages where id='60000000-0000-0000-0000-000000000001'),'file finalization idempotent');
select pg_temp.check_true(not aedrova_private.can_upload_object(current_setting('test.path')),'published file immutable');
select pg_temp.denied($q$update public.attachments set filename='tampered'$q$);
set local request.jwt.claim.sub='40000000-0000-0000-0000-000000000003';
select pg_temp.check_true((select count(*)=0 from public.attachments),'admin cannot see private DM file');
select pg_temp.check_true((select count(*)=0 from storage.objects),'admin cannot download private DM file');
set local request.jwt.claim.sub='40000000-0000-0000-0000-000000000001';
select public.remove_member(current_setting('test.w')::uuid,'40000000-0000-0000-0000-000000000002');
set local request.jwt.claim.sub='40000000-0000-0000-0000-000000000002';
select pg_temp.check_true((select count(*)=0 from public.messages),'removed participant loses DM history');
select pg_temp.check_true((select count(*)=0 from storage.objects),'removed participant loses files');
select pg_temp.denied($q$select public.mark_channel_read(current_setting('test.c')::uuid,0)$q$);
reset role;
select pg_temp.check_true((select bool_and(payload='{}'::jsonb and private and topic like 'user:%') from realtime.test_events),'broadcasts contain no message data');
set local role anon;
select pg_temp.denied('select * from public.attachments');
select pg_temp.denied('select * from public.team_directory()');
rollback;
