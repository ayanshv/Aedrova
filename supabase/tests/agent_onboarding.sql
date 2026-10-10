begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('10000000-0000-0000-0000-000000000001','owner@team.test',now()),
 ('10000000-0000-0000-0000-000000000002','outsider@team.test',now()),
 ('10000000-0000-0000-0000-000000000003','member@team.test',now());
create or replace function pg_temp.check_true(ok boolean, description text) returns void
language plpgsql as $$ begin if ok is distinct from true then raise exception 'FAIL: %',description; end if; end $$;
create or replace function pg_temp.denied(statement text) returns void language plpgsql as $$
begin
 begin execute statement;
 exception when insufficient_privilege then return; end;
 raise exception 'FAIL: unauthorized operation succeeded: %',statement;
end $$;
set local role authenticated;
set local request.jwt.claim.sub='10000000-0000-0000-0000-000000000001';
select set_config('test.team',public.onboard_workspace('Team','Nova','codex')::text,true);
select pg_temp.check_true((select nickname='Nova' and provider='codex' from public.workspace_agent_preferences),'onboarding saves nickname and provider');
select public.set_agent_preferences(current_setting('test.team')::uuid,'Atlas','claude_code');
select pg_temp.check_true((select nickname='Atlas' and provider='claude_code' from public.workspace_agent_preferences),'owner can rename');
select pg_temp.denied('update public.workspace_agent_preferences set nickname=''Bypass''');
do $$ begin
 begin perform public.onboard_workspace('Must roll back','<script>','codex');
 raise exception 'Unsafe nickname accepted'; exception when check_violation then null; end;
 begin perform public.onboard_workspace('Must roll back','Nova','backdoor');
 raise exception 'Unknown provider accepted'; exception when check_violation then null; end;
 begin perform public.set_agent_preferences(current_setting('test.team')::uuid,repeat('x',33),'codex');
 raise exception 'Oversized nickname accepted'; exception when check_violation then null; end;
end $$;
select pg_temp.check_true((select count(*)=1 from public.workspaces),'onboarding failures leave no partial workspace');
select set_config('test.member_invite',public.create_invitation(current_setting('test.team')::uuid,'member@team.test','member'),true);
set local request.jwt.claim.sub='10000000-0000-0000-0000-000000000002';
select pg_temp.check_true((select count(*)=0 from public.workspace_agent_preferences),'outsider cannot read nickname');
select pg_temp.denied($q$select public.set_agent_preferences(current_setting('test.team')::uuid,'Malicious','codex')$q$);
set local request.jwt.claim.sub='10000000-0000-0000-0000-000000000003';
select public.accept_invitation(current_setting('test.member_invite'));
select pg_temp.check_true((select nickname='Atlas' from public.workspace_agent_preferences),'joining members inherit shared name');
select pg_temp.denied($q$select public.set_agent_preferences(current_setting('test.team')::uuid,'Unauthorized','codex')$q$);
set local request.jwt.claim.sub='10000000-0000-0000-0000-000000000001';
select public.remove_member(current_setting('test.team')::uuid,'10000000-0000-0000-0000-000000000003');
set local request.jwt.claim.sub='10000000-0000-0000-0000-000000000003';
select pg_temp.check_true((select count(*)=0 from public.workspace_agent_preferences),'revoked members lose nickname access');
reset role;
set local role anon;
select pg_temp.denied('select * from public.workspace_agent_preferences');
select pg_temp.denied($q$select public.onboard_workspace('Team','Nova','codex')$q$);
rollback;
