-- Auto routing must retain the same authority and privacy as explicit providers.
begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('24000000-0000-0000-0000-000000000001','auto-owner@team.test',now()),
 ('24000000-0000-0000-0000-000000000002','auto-outsider@team.test',now()),
 ('24000000-0000-0000-0000-000000000003','auto-member@team.test',now());
create or replace function pg_temp.check_true(ok boolean, description text) returns void
language plpgsql as $$ begin if ok is distinct from true then raise exception 'FAIL: %',description; end if; end $$;
create or replace function pg_temp.denied(statement text) returns void language plpgsql as $$
begin
 begin execute statement;
 exception when insufficient_privilege then return; end;
 raise exception 'FAIL: unauthorized operation succeeded: %',statement;
end $$;
set local role authenticated;
set local request.jwt.claim.sub='24000000-0000-0000-0000-000000000001';
select set_config('test.auto_team',public.onboard_workspace('Auto acceptance','Aedrova','auto')::text,true);
select pg_temp.check_true((select provider='auto' from public.workspace_agent_preferences
 where workspace_id=current_setting('test.auto_team')::uuid),'Auto onboarding persists');
select public.set_agent_preferences(current_setting('test.auto_team')::uuid,'Aedrova','codex');
select public.set_agent_preferences(current_setting('test.auto_team')::uuid,'Aedrova','claude_code');
select public.set_agent_preferences(current_setting('test.auto_team')::uuid,'Aedrova','auto');
do $$ begin
 begin perform public.set_agent_preferences(current_setting('test.auto_team')::uuid,'Aedrova','backdoor');
 raise exception 'Unknown provider accepted'; exception when check_violation then null; end;
end $$;
select pg_temp.denied($q$update public.workspace_agent_preferences set provider='codex'
 where workspace_id=current_setting('test.auto_team')::uuid$q$);
select set_config('test.auto_invite',public.create_invitation(current_setting('test.auto_team')::uuid,'auto-member@team.test','member'),true);
set local request.jwt.claim.sub='24000000-0000-0000-0000-000000000002';
select pg_temp.check_true((select count(*)=0 from public.workspace_agent_preferences
 where workspace_id=current_setting('test.auto_team')::uuid),'Outsider cannot read Auto configuration');
select pg_temp.denied($q$select public.set_agent_preferences(current_setting('test.auto_team')::uuid,'Aedrova','auto')$q$);
set local request.jwt.claim.sub='24000000-0000-0000-0000-000000000003';
select public.accept_invitation(current_setting('test.auto_invite'));
select pg_temp.check_true((select provider='auto' from public.workspace_agent_preferences
 where workspace_id=current_setting('test.auto_team')::uuid),'Member inherits Auto preference');
select pg_temp.denied($q$select public.set_agent_preferences(current_setting('test.auto_team')::uuid,'Aedrova','codex')$q$);
select pg_temp.denied($q$select public.set_agent_preferences(current_setting('test.auto_team')::uuid,'Aedrova','auto')$q$);
set local request.jwt.claim.sub='24000000-0000-0000-0000-000000000001';
select public.remove_member(current_setting('test.auto_team')::uuid,'24000000-0000-0000-0000-000000000003');
set local request.jwt.claim.sub='24000000-0000-0000-0000-000000000003';
select pg_temp.check_true((select count(*)=0 from public.workspace_agent_preferences
 where workspace_id=current_setting('test.auto_team')::uuid),'Revocation removes Auto configuration access');
reset role;
set local role anon;
select pg_temp.denied($q$select public.onboard_workspace('Anonymous','Aedrova','auto')$q$);
rollback;
