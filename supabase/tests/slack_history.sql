begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('a2100000-0000-0000-0000-000000000001','slack-owner@test.local',now()),
 ('a2100000-0000-0000-0000-000000000002','slack-reader@test.local',now()),
 ('a2100000-0000-0000-0000-000000000003','slack-outsider@test.local',now());

do $$
declare
 owner_id text := 'a2100000-0000-0000-0000-000000000001';
 reader_id text := 'a2100000-0000-0000-0000-000000000002';
 outsider_id text := 'a2100000-0000-0000-0000-000000000003';
 workspace uuid;
 batch uuid := gen_random_uuid();
 overlap uuid := gen_random_uuid();
 items jsonb := '[{"channel_id":"C123","channel_name":"launch","source_ts":"1700000000.000001",
   "author":"Maya","body":"Onboarding beta decision","links":[],"reactions":{}}]';
begin
 perform set_config('request.jwt.claim.sub', owner_id, true);
 set local role authenticated;
 workspace := public.onboard_workspace('Slack fixture','Aedrova','codex');
 reset role;
 insert into public.workspace_members values (workspace,reader_id::uuid,'member');
 set local role authenticated;
 assert public.write_slack_history(workspace,batch,0,items,false) = 1;
 assert public.slack_history(workspace,'onboarding') = '[]'::jsonb;
 assert public.write_slack_history(workspace,batch,1,items,true) = 1;
 assert public.write_slack_history(workspace,batch,1,items,true) = 1;
 assert public.write_slack_history(workspace,overlap,0,items,true) = 0;
 assert jsonb_array_length(public.slack_history(workspace,'onboarding')) = 1;
 assert public.slack_history(workspace,'slack:C123:1700000000.000001')->0->>'author' = 'Maya';
 assert public.slack_channels(workspace)->0->>'channel_name' = 'launch';
 assert (public.slack_channels(workspace)->0->>'message_count')::int = 1;
 assert public.slack_channel_messages(workspace,'C123')->0->>'body' = 'Onboarding beta decision';
 assert public.slack_channel_messages(workspace,'C123',1700000000.000001) = '[]'::jsonb;
 assert public.slack_channel_messages(workspace,'C999') = '[]'::jsonb;
 perform set_config('request.jwt.claim.sub', reader_id, true);
 assert jsonb_array_length(public.slack_history(workspace,'onboarding')) = 1;
 assert jsonb_array_length(public.slack_channels(workspace)) = 1;
 assert jsonb_array_length(public.slack_channel_messages(workspace,'C123')) = 1;
 begin
   perform public.write_slack_history(workspace,gen_random_uuid(),0,items,true);
   raise exception 'member could write an import';
 exception when insufficient_privilege then null;
 end;
 begin
   perform public.remove_slack_import(workspace,batch);
   raise exception 'member could remove import';
 exception when insufficient_privilege then null;
 end;
 perform set_config('request.jwt.claim.sub', outsider_id, true);
 begin
   perform public.slack_history(workspace,'onboarding');
   raise exception 'outsider could see import';
 exception when insufficient_privilege then null;
 end;
 begin
   perform public.slack_channels(workspace);
   raise exception 'outsider could list channels';
 exception when insufficient_privilege then null;
 end;
 begin
   perform public.slack_channel_messages(workspace,'C123');
   raise exception 'outsider could read a channel';
 exception when insufficient_privilege then null;
 end;
 perform set_config('request.jwt.claim.sub', owner_id, true);
 assert public.remove_slack_import(workspace,batch);
 assert public.slack_history(workspace,'onboarding') = '[]'::jsonb;
 assert public.slack_channels(workspace) = '[]'::jsonb;
 reset role;
end $$;
rollback;
