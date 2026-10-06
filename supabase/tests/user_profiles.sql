begin;
insert into auth.users(id,email,email_confirmed_at,raw_user_meta_data) values
 ('96000000-0000-0000-0000-000000000001','profile1@test.local',now(),'{"full_name":"Original"}'),
 ('96000000-0000-0000-0000-000000000002','profile2@test.local',now(),'{}'),
 ('96000000-0000-0000-0000-000000000003','profile3@test.local',now(),'{}');
create or replace function pg_temp.check_true(ok boolean,description text) returns void language plpgsql as $$
begin if ok is distinct from true then raise exception 'FAIL: %',description; end if; end $$;
create or replace function pg_temp.denied(statement text) returns void language plpgsql as $$
begin begin execute statement; exception when insufficient_privilege or invalid_parameter_value or check_violation then return; end; raise exception 'FAIL: accepted invalid operation'; end $$;
insert into storage.objects(bucket_id,name,metadata) values('aedrova-avatars','96000000-0000-0000-0000-000000000001/96000000-0000-0000-0000-000000000011.png','{"size":100}');
set local role authenticated;
set local request.jwt.claim.sub='96000000-0000-0000-0000-000000000001';
select pg_temp.check_true(not (public.my_chat_profile()->>'profile_completed')::boolean,'new profile incomplete');
select public.save_chat_profile('{"display_name":"Maya Chen","username":"maya_chen","bio":"Building together","title":"Founder","status":"Focus","status_emoji":"🚀","availability":"busy","profile_completed":true,"avatar_path":"96000000-0000-0000-0000-000000000001/96000000-0000-0000-0000-000000000011.png","user_id":"96000000-0000-0000-0000-000000000003","role":"admin"}');
select pg_temp.check_true(public.my_chat_profile()->>'user_id'='96000000-0000-0000-0000-000000000001','cannot change another profile');
select set_config('test.pw',public.onboard_workspace('Profiles','Aedrova','codex')::text,true);
select set_config('test.pi',public.create_invitation(current_setting('test.pw')::uuid,'profile2@test.local','member'),true);
select public.chat_action('profile','{"status":"Available","availability":"online"}');
select public.chat_action('heartbeat');
select pg_temp.check_true(public.my_chat_profile()->>'username'='maya_chen' and public.my_chat_profile()->>'status_emoji'='🚀','presence preserves profile');
select pg_temp.check_true(jsonb_array_length(public.chat_inventory(current_setting('test.pw')::uuid,'maya_chen','people')->'people')=1,'search custom username');
select pg_temp.check_true((select display_name='Maya Chen' from public.team_directory() limit 1),'custom display name in chat');
select pg_temp.denied('select public.save_chat_profile(''{"username":"bad space"}'')');
select pg_temp.denied('select public.save_chat_profile(''{"availability":"invalid"}'')');
select pg_temp.check_true(aedrova_private.can_read_avatar('96000000-0000-0000-0000-000000000001/96000000-0000-0000-0000-000000000011.png'),'own avatar');
set local request.jwt.claim.sub='96000000-0000-0000-0000-000000000002';
select public.accept_invitation(current_setting('test.pi'));
select pg_temp.check_true(aedrova_private.can_read_avatar('96000000-0000-0000-0000-000000000001/96000000-0000-0000-0000-000000000011.png'),'teammate avatar');
select pg_temp.denied('select public.save_chat_profile(''{"display_name":"Other","username":"maya_chen","profile_completed":true}'')');
select pg_temp.denied('select public.save_chat_profile(''{"avatar_path":"96000000-0000-0000-0000-000000000001/96000000-0000-0000-0000-000000000011.png"}'')');
set local request.jwt.claim.sub='96000000-0000-0000-0000-000000000003';
select pg_temp.check_true(not aedrova_private.can_read_avatar('96000000-0000-0000-0000-000000000001/96000000-0000-0000-0000-000000000011.png'),'outsider avatar denied');
select pg_temp.denied(format('select public.chat_inventory(%L)',current_setting('test.pw')));
select pg_temp.check_true(not exists(select 1 from storage.objects where bucket_id='aedrova-avatars'),'storage RLS hides outsider photos');
set local role anon;
select pg_temp.denied('select public.my_chat_profile()');
rollback;
