begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('f1000000-0000-0000-0000-000000000001','ai-owner@test.local',now()),
 ('f1000000-0000-0000-0000-000000000002','ai-member@test.local',now());
create or replace function pg_temp.check_true(ok boolean,description text) returns void language plpgsql as $$
begin if ok is distinct from true then raise exception 'FAIL: %',description; end if; end $$;
create or replace function pg_temp.denied(statement text,code text default '42501') returns void language plpgsql as $$
declare actual text;
begin begin execute statement; exception when others then get stacked diagnostics actual=returned_sqlstate;
 if actual=code then return; end if; raise; end; raise exception 'FAIL: unauthorized action succeeded'; end $$;
set local role authenticated;
set local request.jwt.claim.sub='f1000000-0000-0000-0000-000000000001';
select set_config('test.w',public.onboard_workspace('AI teammate acceptance','Aedrova','codex')::text,true);
select set_config('test.config','{"name":"Pixel","role":"engineering","shape":"round","color":"#4388F5","personality":"concise","reporting":"quiet","effort":"quick","importance":"normal","responsibilities":"Implement scoped changes"}',true);
select pg_temp.check_true(public.save_ai_teammate('f1100000-0000-0000-0000-000000000001',current_setting('test.w')::uuid,0,current_setting('test.config')::jsonb)=1,'create persistent identity');
select pg_temp.check_true(public.save_ai_teammate('f1100000-0000-0000-0000-000000000001',current_setting('test.w')::uuid,0,current_setting('test.config')::jsonb)=1,'same create retry returns existing version');
select pg_temp.denied($q$select public.set_agent_preferences(current_setting('test.w')::uuid,'pixel','codex')$q$,'22023');
select pg_temp.denied($q$select public.save_ai_teammate('f1100000-0000-0000-0000-000000000002',current_setting('test.w')::uuid,0,current_setting('test.config')::jsonb)$q$,'23505');
select pg_temp.denied($q$select public.save_ai_teammate('f1100000-0000-0000-0000-000000000002',current_setting('test.w')::uuid,0,jsonb_set(current_setting('test.config')::jsonb,'{name}','"Aedrova"'))$q$,'22023');
select pg_temp.check_true(public.save_ai_teammate('f1100000-0000-0000-0000-000000000001',current_setting('test.w')::uuid,1,current_setting('test.config')::jsonb,true)=2,'pause version');
select pg_temp.denied($q$select public.save_ai_teammate('f1100000-0000-0000-0000-000000000001',current_setting('test.w')::uuid,1,current_setting('test.config')::jsonb)$q$,'PT409');
select set_config('test.invite',public.create_invitation(current_setting('test.w')::uuid,'ai-member@test.local','member'),true);
set local request.jwt.claim.sub='f1000000-0000-0000-0000-000000000002';
select pg_temp.check_true((select count(*)=0 from public.ai_teammates),'outsider identities hidden');
select public.accept_invitation(current_setting('test.invite'));
select pg_temp.check_true((select count(*)=1 from public.ai_teammates),'member shared identities');
select pg_temp.denied($q$select public.save_ai_teammate('f1100000-0000-0000-0000-000000000001',current_setting('test.w')::uuid,2,current_setting('test.config')::jsonb)$q$);
select pg_temp.denied('update public.ai_teammates set paused=false');
select pg_temp.denied($q$select public.remove_ai_teammate('f1100000-0000-0000-0000-000000000001',2)$q$);
set local request.jwt.claim.sub='f1000000-0000-0000-0000-000000000001';
select public.remove_member(current_setting('test.w')::uuid,'f1000000-0000-0000-0000-000000000002');
set local request.jwt.claim.sub='f1000000-0000-0000-0000-000000000002';
select pg_temp.check_true((select count(*)=0 from public.ai_teammates),'revoked membership hides identity');
set local request.jwt.claim.sub='f1000000-0000-0000-0000-000000000001';
select public.remove_ai_teammate('f1100000-0000-0000-0000-000000000001',2);
select pg_temp.check_true((select count(*)=0 from public.ai_teammates),'removed identity no longer assignable');
select pg_temp.denied($q$select public.save_ai_teammate('f1100000-0000-0000-0000-000000000001',current_setting('test.w')::uuid,0,current_setting('test.config')::jsonb)$q$);
rollback;
