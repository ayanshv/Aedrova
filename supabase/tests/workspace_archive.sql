-- Disposable fixture only. Never apply tests to hosted Supabase.
begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('92000000-0000-0000-0000-000000000001','owner@archive.test',now()),
 ('92000000-0000-0000-0000-000000000002','member@archive.test',now()),
 ('92000000-0000-0000-0000-000000000003','outsider@archive.test',now());
create or replace function pg_temp.check_true(ok boolean, description text) returns void
language plpgsql as $$ begin if ok is distinct from true then raise exception 'FAIL: %',description; end if; end $$;
create or replace function pg_temp.denied(statement text) returns void language plpgsql as $$
begin begin execute statement; exception when insufficient_privilege then return; end;
 raise exception 'FAIL: unauthorized operation succeeded'; end $$;
set local role authenticated;
set local request.jwt.claim.sub='92000000-0000-0000-0000-000000000001';
select set_config('test.w',public.onboard_workspace('Archive fixture','Aedrova','codex')::text,true);
select set_config('test.c',(select id::text from public.channels where workspace_id=current_setting('test.w')::uuid limit 1),true);
select public.send_message('93000000-0000-0000-0000-000000000001',current_setting('test.c')::uuid,'Preserve this discussion');
select set_config('test.invite',public.create_invitation(current_setting('test.w')::uuid,'member@archive.test')::text,true);
select pg_temp.check_true((select count(*)=1 from public.list_my_workspaces()),'new workspace visible');
select public.set_workspace_archived(current_setting('test.w')::uuid,true);
select public.set_workspace_archived(current_setting('test.w')::uuid,true);
select pg_temp.check_true((select count(*)=0 from public.list_my_workspaces()),'archive hides workspace');
select pg_temp.check_true((select count(*)=1 from public.list_my_workspaces(true)),'archive is discoverable');
select pg_temp.check_true((select count(*)=1 from public.workspace_preferences),'idempotent preference');
select pg_temp.check_true((select count(*)=1 from public.messages where channel_id=current_setting('test.c')::uuid),'archive preserves messages');
select pg_temp.check_true(aedrova_private.member_role(current_setting('test.w')::uuid)='owner','archive preserves membership');
select pg_temp.denied($q$update public.workspace_preferences set user_id='92000000-0000-0000-0000-000000000002'$q$);
set local request.jwt.claim.sub='92000000-0000-0000-0000-000000000002';
select public.accept_invitation(current_setting('test.invite'));
select pg_temp.check_true((select count(*)=1 from public.list_my_workspaces()),'teammate unaffected');
select pg_temp.check_true((select count(*)=0 from public.list_my_workspaces(true)),'teammate archive isolated');
select pg_temp.check_true((select count(*)=0 from public.workspace_preferences),'other preferences private');
select public.set_workspace_archived(current_setting('test.w')::uuid,true);
select public.set_workspace_archived(current_setting('test.w')::uuid,false);
select pg_temp.check_true((select count(*)=1 from public.list_my_workspaces()),'member restores workspace');
set local request.jwt.claim.sub='92000000-0000-0000-0000-000000000003';
select pg_temp.check_true((select count(*)=0 from public.list_my_workspaces(true)),'foreign archive hidden');
select pg_temp.denied($q$select public.set_workspace_archived(current_setting('test.w')::uuid,true)$q$);
select pg_temp.denied($q$select public.set_workspace_archived(current_setting('test.w')::uuid,false)$q$);
set local request.jwt.claim.sub='92000000-0000-0000-0000-000000000001';
select public.remove_member(current_setting('test.w')::uuid,'92000000-0000-0000-0000-000000000002');
set local request.jwt.claim.sub='92000000-0000-0000-0000-000000000002';
select pg_temp.denied($q$select public.set_workspace_archived(current_setting('test.w')::uuid,false)$q$);
select pg_temp.check_true((select count(*)=0 from public.list_my_workspaces()),'removed member cannot restore');
reset role;
select pg_temp.check_true((select count(*)=0 from public.workspace_preferences where user_id='92000000-0000-0000-0000-000000000002'),'membership removal clears preference');
set local role anon;
select pg_temp.denied('select public.list_my_workspaces(true)');
select pg_temp.denied($q$select public.set_workspace_archived(current_setting('test.w')::uuid,false)$q$);
rollback;
