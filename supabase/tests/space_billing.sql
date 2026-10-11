-- Disposable PostgreSQL fixture. Never run test fixtures on hosted Supabase.
begin;
insert into auth.users(id,email,email_confirmed_at) values
('a1000000-0000-0000-0000-000000000001','owner@spaces.test',now()),
('a1000000-0000-0000-0000-000000000002','member@spaces.test',now()),
('a1000000-0000-0000-0000-000000000003','outside@spaces.test',now());
create or replace function pg_temp.check_true(ok boolean,description text) returns void
language plpgsql as $$begin if ok is distinct from true then raise exception 'FAIL: %',description; end if; end$$;
create or replace function pg_temp.reject(statement text) returns void language plpgsql as $$
begin begin execute statement; exception when insufficient_privilege or invalid_parameter_value or serialization_failure or program_limit_exceeded then return; end;
raise exception 'FAIL: forbidden operation succeeded'; end$$;
set local role authenticated;
set local request.jwt.claim.sub='a1000000-0000-0000-0000-000000000001';
select set_config('test.root',public.onboard_workspace('Independent','Aedrova','codex')::text,true);
select set_config('test.other',public.onboard_workspace('Other','Aedrova','codex')::text,true);
select set_config('test.child',public.create_subspace(current_setting('test.root')::uuid,'Child')::text,true);
select set_config('test.deep',public.create_subspace(current_setting('test.child')::uuid,'Nested')::text,true);
select pg_temp.check_true(public.space_billing_context(current_setting('test.deep')::uuid)->>'billing_workspace'=current_setting('test.root'),'nested root');
select pg_temp.check_true(public.space_billing_context(current_setting('test.other')::uuid)->>'billing_workspace'=current_setting('test.other'),'independent root');
select pg_temp.reject($q$select public.move_subspace(current_setting('test.child')::uuid,current_setting('test.deep')::uuid,current_setting('test.root')::uuid)$q$);
select pg_temp.reject($q$update public.workspace_parents set parent_id=current_setting('test.other')::uuid$q$);
select pg_temp.reject($q$select public.resolve_billing_space_for_backend(current_setting('test.root')::uuid,auth.uid())$q$);
select public.move_subspace(current_setting('test.child')::uuid,current_setting('test.other')::uuid,current_setting('test.root')::uuid);
select pg_temp.check_true(public.space_billing_context(current_setting('test.deep')::uuid)->>'billing_workspace'=current_setting('test.other'),'moves update nested root');
select pg_temp.reject($q$select public.move_subspace(current_setting('test.child')::uuid,current_setting('test.root')::uuid,current_setting('test.root')::uuid)$q$);
select set_config('test.invite',public.create_invitation(current_setting('test.child')::uuid,'member@spaces.test')::text,true);
set local request.jwt.claim.sub='a1000000-0000-0000-0000-000000000002';
select public.accept_invitation(current_setting('test.invite'));
select pg_temp.reject($q$select public.space_billing_context(current_setting('test.child')::uuid)$q$);
select pg_temp.reject($q$select public.create_subspace(current_setting('test.other')::uuid,'Unauthorized')$q$);
set local request.jwt.claim.sub='a1000000-0000-0000-0000-000000000001';
select set_config('test.invite',public.create_invitation(current_setting('test.other')::uuid,'member@spaces.test')::text,true);
set local request.jwt.claim.sub='a1000000-0000-0000-0000-000000000002';
select public.accept_invitation(current_setting('test.invite'));
select pg_temp.check_true((public.space_billing_context(current_setting('test.child')::uuid)->>'can_manage_billing')::boolean=false,'member read only');
select pg_temp.reject($q$select public.move_subspace(current_setting('test.child')::uuid,current_setting('test.root')::uuid,current_setting('test.other')::uuid)$q$);
set local request.jwt.claim.sub='a1000000-0000-0000-0000-000000000003';
select pg_temp.reject($q$select public.space_billing_context(current_setting('test.root')::uuid)$q$);
select pg_temp.check_true((select count(*)=0 from public.workspace_parents),'RLS hides all foreign links');
reset role;
select pg_temp.check_true(public.resolve_billing_space_for_backend(current_setting('test.deep')::uuid,'a1000000-0000-0000-0000-000000000001')::text=current_setting('test.other'),'server resolver shares source of truth');
update aedrova_private.space_limits set max_depth=2;
set local role authenticated;
set local request.jwt.claim.sub='a1000000-0000-0000-0000-000000000001';
select pg_temp.reject($q$select public.create_subspace(current_setting('test.deep')::uuid,'Too deep')$q$);
set local role anon;
select pg_temp.reject($q$select public.space_billing_context(current_setting('test.root')::uuid)$q$);
rollback;
