begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('f5100000-0000-0000-0000-000000000001','shared-owner@test.local',now()),
 ('f5100000-0000-0000-0000-000000000002','shared-member@test.local',now()),
 ('f5100000-0000-0000-0000-000000000003','shared-outsider@test.local',now());
create or replace function pg_temp.check_true(ok boolean,description text) returns void language plpgsql as $$
begin if ok is distinct from true then raise exception 'FAIL: %',description; end if; end $$;
create or replace function pg_temp.denied(statement text,code text default '42501') returns void language plpgsql as $$
declare actual text;
begin begin execute statement; exception when others then get stacked diagnostics actual=returned_sqlstate;
 if actual=code then return; end if; raise; end; raise exception 'FAIL: unauthorized action succeeded'; end $$;
set local role authenticated;
set local request.jwt.claim.sub='f5100000-0000-0000-0000-000000000001';
select set_config('test.w',public.onboard_workspace('Shared work','Aedrova','codex')::text,true);
select set_config('test.c',(select id::text from public.channels where workspace_id=current_setting('test.w')::uuid limit 1),true);
select set_config('test.private',public.create_channel(current_setting('test.w')::uuid,'private-source',true)::text,true);
select public.save_shared_agent_work('f5200000-0000-0000-0000-000000000001',current_setting('test.w')::uuid,current_setting('test.c')::uuid,'Research Bud','Three market segments',array[current_setting('test.c')::uuid]);
select public.save_shared_agent_work('f5200000-0000-0000-0000-000000000001',current_setting('test.w')::uuid,current_setting('test.c')::uuid,'Research Bud','Three market segments',array[current_setting('test.c')::uuid]);
select public.save_shared_agent_work('f5200000-0000-0000-0000-000000000002',current_setting('test.w')::uuid,current_setting('test.c')::uuid,'Aedrova','Private-derived proposal',array[current_setting('test.private')::uuid]);
select pg_temp.check_true((select count(*)=2 from public.shared_agent_work),'same request id saves once');
select pg_temp.denied($q$select public.save_shared_agent_work('f5200000-0000-0000-0000-000000000001',current_setting('test.w')::uuid,current_setting('test.c')::uuid,'Research Bud','changed',array[current_setting('test.c')::uuid])$q$);
select pg_temp.denied($q$insert into public.shared_agent_work(id,workspace_id,channel_id,author_id,agent_name,body,source_channels) values(gen_random_uuid(),current_setting('test.w')::uuid,current_setting('test.c')::uuid,auth.uid(),'spoof','bypass',array[current_setting('test.c')::uuid])$q$);
select pg_temp.denied($q$select public.save_shared_agent_work(gen_random_uuid(),current_setting('test.w')::uuid,current_setting('test.c')::uuid,'Bud',repeat('x',20001),array[current_setting('test.c')::uuid])$q$,'22023');
select set_config('test.invite',public.create_invitation(current_setting('test.w')::uuid,'shared-member@test.local','member'),true);
set local request.jwt.claim.sub='f5100000-0000-0000-0000-000000000002';
select public.accept_invitation(current_setting('test.invite'));
select pg_temp.check_true((select count(*)=1 from public.shared_agent_work),'member can read shared work but not private-derived work');
select pg_temp.denied($q$select public.save_shared_agent_work(gen_random_uuid(),current_setting('test.w')::uuid,current_setting('test.c')::uuid,'Bud','private bypass',array[current_setting('test.private')::uuid])$q$);
select set_config('test.dm',public.start_direct_message(current_setting('test.w')::uuid,'f5100000-0000-0000-0000-000000000001')::text,true);
select pg_temp.denied($q$select public.save_shared_agent_work(gen_random_uuid(),current_setting('test.w')::uuid,current_setting('test.dm')::uuid,'Bud','Do not share DM',array[current_setting('test.dm')::uuid])$q$);
set local request.jwt.claim.sub='f5100000-0000-0000-0000-000000000003';
select pg_temp.check_true((select count(*)=0 from public.shared_agent_work),'outsider reads nothing');
select pg_temp.denied($q$select public.save_shared_agent_work(gen_random_uuid(),current_setting('test.w')::uuid,current_setting('test.c')::uuid,'Bud','outsider',array[current_setting('test.c')::uuid])$q$);
set local request.jwt.claim.sub='f5100000-0000-0000-0000-000000000001';
select public.remove_member(current_setting('test.w')::uuid,'f5100000-0000-0000-0000-000000000002');
set local request.jwt.claim.sub='f5100000-0000-0000-0000-000000000002';
select pg_temp.check_true((select count(*)=0 from public.shared_agent_work),'revoked member loses shared context');
rollback;
