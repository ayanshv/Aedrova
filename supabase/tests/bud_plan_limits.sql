begin;
create schema if not exists aedrova_billing;
-- Disposable test ledger matching the private backend's verified subscription fields.
create table if not exists aedrova_billing.billing (
 workspace text primary key, plan text, status text, period_start bigint, period_end bigint
);
insert into auth.users(id,email,email_confirmed_at) values
 ('a2400000-0000-0000-0000-000000000001','bud-cap-owner@test.local',now()),
 ('a2400000-0000-0000-0000-000000000002','bud-cap-other@test.local',now());
create function pg_temp.assert_cap(ok boolean, msg text) returns void language plpgsql as $$
begin if ok is distinct from true then raise exception 'FAIL %',msg; end if; end $$;
create function pg_temp.at_limit(w uuid) returns void language plpgsql as $$
begin
 begin
  perform public.save_workspace_bud(null,w,0,'github','cap/overflow','Overflow');
 exception when sqlstate '54000' then return;
 end;
 raise exception 'FAIL quota not enforced';
end $$;
set local role authenticated;
set local request.jwt.claim.sub='a2400000-0000-0000-0000-000000000001';
select set_config('test.capw',public.onboard_workspace('Bud caps','Aedrova','codex')::text,true);
select pg_temp.assert_cap(public.workspace_bud_capacity(current_setting('test.capw')::uuid)->>'limit'='1','unactivated workspace uses Free cap');
select set_config('test.capdot',(public.save_workspace_bud(null,current_setting('test.capw')::uuid,0,'github','cap/one','One')).id::text,true);
select pg_temp.at_limit(current_setting('test.capw')::uuid);
select pg_temp.assert_cap((public.save_workspace_bud(current_setting('test.capdot')::uuid,current_setting('test.capw')::uuid,1,'github','cap/one','One edited')).version=2,'editing at cap remains allowed');
select public.remove_workspace_dot(current_setting('test.capdot')::uuid,current_setting('test.capw')::uuid,2);
select pg_temp.assert_cap(public.workspace_bud_capacity(current_setting('test.capw')::uuid)->>'remaining'='1','deleting frees a slot');
reset role;
insert into aedrova_billing.billing values(current_setting('test.capw'),'monthly','active',0,extract(epoch from now())::bigint+3600);
set local role authenticated;
select pg_temp.assert_cap(public.workspace_bud_capacity(current_setting('test.capw')::uuid)->>'limit'='5','Pro cap');
do $$begin for i in 1..5 loop perform public.save_workspace_bud(null,current_setting('test.capw')::uuid,0,'github','cap/pro'||i,'Pro '||i); end loop; end$$;
select pg_temp.at_limit(current_setting('test.capw')::uuid);
reset role;
update aedrova_billing.billing set plan='annual' where workspace=current_setting('test.capw');
set local role authenticated;
select pg_temp.assert_cap(public.workspace_bud_capacity(current_setting('test.capw')::uuid)->>'limit'='15','Team cap');
do $$begin for i in 6..15 loop perform public.save_workspace_bud(null,current_setting('test.capw')::uuid,0,'github','cap/team'||i,'Team '||i); end loop; end$$;
select pg_temp.at_limit(current_setting('test.capw')::uuid);
-- A subspace shares its subscription capacity, rather than multiplying it.
select set_config('test.capchild',public.create_subspace(current_setting('test.capw')::uuid,'Child')::text,true);
select pg_temp.assert_cap(public.workspace_bud_capacity(current_setting('test.capchild')::uuid)->>'used'='15','subspaces share capacity');
select pg_temp.at_limit(current_setting('test.capchild')::uuid);
reset role;
update aedrova_billing.billing set period_end=0 where workspace=current_setting('test.capw');
set local role authenticated;
select pg_temp.assert_cap(public.workspace_bud_capacity(current_setting('test.capw')::uuid)->>'limit'='1','expired paid plan falls back to Free');
select pg_temp.assert_cap((select count(*)=15 from public.workspace_dots where deleted_at is null),'downgrade preserves saved Buds');
select pg_temp.at_limit(current_setting('test.capw')::uuid);
reset role;
update aedrova_billing.billing set plan='enterprise',period_end=extract(epoch from now())::bigint+3600 where workspace=current_setting('test.capw');
set local role authenticated;
select pg_temp.assert_cap(public.workspace_bud_capacity(current_setting('test.capw')::uuid)->>'limit'='0','Enterprise needs explicit capacity');
reset role;
insert into aedrova_private.enterprise_bud_limits values(current_setting('test.capw')::uuid,30);
set local role authenticated;
select pg_temp.assert_cap(public.workspace_bud_capacity(current_setting('test.capw')::uuid)->>'limit'='30','Enterprise agreed cap');
set local request.jwt.claim.sub='a2400000-0000-0000-0000-000000000002';
do $$begin
 begin perform public.workspace_bud_capacity(current_setting('test.capw')::uuid);
 exception when insufficient_privilege then return; end;
 raise exception 'FAIL outsider reads capacity';
end $$;
do $$begin
 begin update aedrova_private.enterprise_bud_limits set capacity=1000;
 exception when insufficient_privilege then return; end;
 raise exception 'FAIL client changes quota';
end $$;
set local role anon;
do $$begin
 begin perform public.workspace_bud_capacity(current_setting('test.capw')::uuid);
 exception when insufficient_privilege then return; end;
 raise exception 'FAIL anonymous reads quota';
end $$;
rollback;
