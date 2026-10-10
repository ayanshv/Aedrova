-- Real PostgreSQL grants, RLS and definer-function checks. Entire test rolls back.
begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('00000000-0000-0000-0000-000000000001','owner@a.test',now()),
 ('00000000-0000-0000-0000-000000000002','outsider@b.test',now()),
 ('00000000-0000-0000-0000-000000000003','member@a.test',now()),
 ('00000000-0000-0000-0000-000000000004','guest@a.test',now()),
 ('00000000-0000-0000-0000-000000000005','admin@a.test',now()),
 ('00000000-0000-0000-0000-000000000006','unconfirmed@a.test',null);
create function pg_temp.check_true(ok boolean, description text) returns void
language plpgsql as $$ begin if ok is distinct from true then raise exception 'FAIL: %',description; end if; end $$;
create function pg_temp.denied(statement text) returns void language plpgsql as $$
begin
 begin execute statement;
 exception when insufficient_privilege then return; end;
 raise exception 'FAIL: unauthorized operation succeeded: %',statement;
end $$;
set local role authenticated;
set local request.jwt.claim.sub='00000000-0000-0000-0000-000000000001';
select set_config('test.workspace',public.create_workspace('Alpha')::text,true);
select set_config('test.private',public.create_channel(current_setting('test.workspace')::uuid,'Private',true)::text,true);
select set_config('test.public',(select id::text from public.channels where name='general'),true);
select set_config('test.invite',public.create_invitation(current_setting('test.workspace')::uuid,'member@a.test','member'),true);
select set_config('test.guest',public.create_invitation(current_setting('test.workspace')::uuid,'guest@a.test','guest'),true);
select set_config('test.admin',public.create_invitation(current_setting('test.workspace')::uuid,'admin@a.test','admin'),true);
select pg_temp.check_true((select count(*)=1 from public.workspaces),'owner sees workspace');
select pg_temp.check_true((select count(*)=2 from public.channels),'creator sees private');
select pg_temp.denied('select token_hash from public.workspace_invitations');
select pg_temp.denied('update public.workspace_members set role=''owner''');
select pg_temp.denied('delete from public.channels');
select pg_temp.denied('insert into public.workspaces(name) values(''Bypass'')');

set local request.jwt.claim.sub='00000000-0000-0000-0000-000000000002';
select set_config('test.other',public.create_workspace('Beta')::text,true);
select pg_temp.check_true((select count(*)=1 from public.workspaces),'outsider sees only own workspace');
select pg_temp.check_true((select count(*)=0 from public.channels where workspace_id=current_setting('test.workspace')::uuid),'no cross-tenant channels');
select pg_temp.check_true((select count(*)=0 from public.workspace_members where workspace_id=current_setting('test.workspace')::uuid),'no cross-tenant members');
select pg_temp.denied($q$select public.accept_invitation(current_setting('test.invite'))$q$);
select pg_temp.denied($q$select public.create_channel(current_setting('test.workspace')::uuid,'Attack',false)$q$);
select pg_temp.denied($q$select public.remove_member(current_setting('test.workspace')::uuid,'00000000-0000-0000-0000-000000000003')$q$);
select pg_temp.denied($q$select public.create_invitation(current_setting('test.workspace')::uuid,'x@x.test','member')$q$);

set local request.jwt.claim.sub='00000000-0000-0000-0000-000000000003';
select public.accept_invitation(current_setting('test.invite'));
select pg_temp.denied($q$select public.accept_invitation(current_setting('test.invite'))$q$);
select pg_temp.check_true((select count(*)=1 from public.channels),'member cannot see private');
select pg_temp.denied($q$select public.set_member_role(current_setting('test.workspace')::uuid,auth.uid(),'admin')$q$);
select pg_temp.denied($q$select public.set_channel_member(current_setting('test.private')::uuid,auth.uid(),true)$q$);

set local request.jwt.claim.sub='00000000-0000-0000-0000-000000000004';
select public.accept_invitation(current_setting('test.guest'));
select pg_temp.check_true((select count(*)=0 from public.channels),'guest needs explicit public-channel membership');
select pg_temp.denied($q$select public.create_channel(current_setting('test.workspace')::uuid,'Guest channel',false)$q$);

set local request.jwt.claim.sub='00000000-0000-0000-0000-000000000005';
select public.accept_invitation(current_setting('test.admin'));
select pg_temp.check_true((select count(*)=1 from public.channels),'admin has no implicit private access');
select pg_temp.denied($q$select public.set_channel_member(current_setting('test.private')::uuid,auth.uid(),true)$q$);
select pg_temp.denied($q$select public.create_invitation(current_setting('test.workspace')::uuid,'x@x.test','admin')$q$);
select pg_temp.denied($q$select public.remove_member(current_setting('test.workspace')::uuid,'00000000-0000-0000-0000-000000000001')$q$);

set local request.jwt.claim.sub='00000000-0000-0000-0000-000000000001';
select public.set_channel_member(current_setting('test.private')::uuid,'00000000-0000-0000-0000-000000000003',true);
select public.set_channel_member(current_setting('test.public')::uuid,'00000000-0000-0000-0000-000000000004',true);
select pg_temp.denied($q$select public.set_member_role(current_setting('test.workspace')::uuid,auth.uid(),'member')$q$);
select set_config('test.expired',public.create_invitation(current_setting('test.workspace')::uuid,'outsider@b.test','member'),true);
reset role;
update public.workspace_invitations set expires_at=now()-interval '1 second' where email='outsider@b.test';
insert into storage.objects(bucket_id,name) values
 ('aedrova-files',current_setting('test.workspace')||'/'||current_setting('test.private')||'/secret.txt'),
 ('aedrova-files',current_setting('test.workspace')||'/'||current_setting('test.public')||'/shared.txt'),
 ('aedrova-files','malformed');
insert into realtime.messages values(1,'broadcast'),(2,'presence');
set local role authenticated;
set local request.jwt.claim.sub='00000000-0000-0000-0000-000000000002';
select pg_temp.denied($q$select public.accept_invitation(current_setting('test.expired'))$q$);
select pg_temp.check_true((select count(*)=0 from storage.objects),'outsider cannot list objects');
select pg_temp.denied($q$select public.remove_member(current_setting('test.workspace')::uuid,'00000000-0000-0000-0000-000000000003')$q$);
set local request.jwt.claim.sub='00000000-0000-0000-0000-000000000003';
select pg_temp.check_true((select count(*)=2 from public.channels),'private grant effective');
select pg_temp.check_true((select count(*)=2 from storage.objects),'authorized objects visible');
select pg_temp.denied($q$insert into storage.objects(bucket_id,name) values('aedrova-files','malformed')$q$);
select set_config('realtime.topic','channel:'||current_setting('test.private'),true);
select pg_temp.check_true((select count(*)=1 from realtime.messages),'authorized broadcast only');
select pg_temp.denied($q$insert into realtime.messages values(3,'broadcast')$q$);
set local request.jwt.claim.sub='00000000-0000-0000-0000-000000000005';
select pg_temp.check_true((select count(*)=0 from realtime.messages),'private topic denied to admin');
select pg_temp.check_true((select count(*)=1 from storage.objects),'admin cannot read private files');
set local request.jwt.claim.sub='00000000-0000-0000-0000-000000000001';
-- Revoked invitation cannot be redeemed.
select set_config('test.revoked',public.create_invitation(current_setting('test.workspace')::uuid,'outsider@b.test','member'),true);
select public.revoke_invitation((select id from public.workspace_invitations
 where email='outsider@b.test' order by expires_at desc limit 1));
set local request.jwt.claim.sub='00000000-0000-0000-0000-000000000002';
select pg_temp.denied($q$select public.accept_invitation(current_setting('test.revoked'))$q$);
select pg_temp.check_true((select count(*)=1 from public.list_members()),'roster hides other tenants');
select pg_temp.check_true(not aedrova_private.can_read_object(current_setting('test.other')||'/'||current_setting('test.private')||'/secret.txt'),'mismatched workspace path denied');
set local request.jwt.claim.sub='00000000-0000-0000-0000-000000000004';
select pg_temp.check_true((select count(*)=1 from public.channels),'guest explicit channel grant works');
select pg_temp.check_true((select count(*)=1 from public.list_members()),'guest cannot enumerate roster');
set local request.jwt.claim.sub='00000000-0000-0000-0000-000000000005';
select set_config('test.stale',public.create_invitation(current_setting('test.workspace')::uuid,'outsider@b.test','member'),true);
set local request.jwt.claim.sub='00000000-0000-0000-0000-000000000001';
select public.set_member_role(current_setting('test.workspace')::uuid,'00000000-0000-0000-0000-000000000005','member');
set local request.jwt.claim.sub='00000000-0000-0000-0000-000000000002';
select pg_temp.denied($q$select public.accept_invitation(current_setting('test.stale'))$q$);
set local request.jwt.claim.sub='00000000-0000-0000-0000-000000000001';
select public.remove_member(current_setting('test.workspace')::uuid,'00000000-0000-0000-0000-000000000003');
set local request.jwt.claim.sub='00000000-0000-0000-0000-000000000003';
select pg_temp.check_true((select count(*)=0 from public.workspaces),'revocation hides workspace');
select pg_temp.check_true((select count(*)=0 from public.channels),'revocation hides channels');
select pg_temp.check_true((select count(*)=0 from storage.objects),'revocation hides objects');
select pg_temp.check_true((select count(*)=0 from realtime.messages),'revocation denies new subscriptions');
set local request.jwt.claim.sub='00000000-0000-0000-0000-000000000006';
select pg_temp.denied($q$select public.create_workspace('Unconfirmed')$q$);
reset role;
set local role anon;
select pg_temp.denied('select * from public.workspaces');
select pg_temp.denied($q$select public.create_workspace('Anonymous')$q$);
rollback;
