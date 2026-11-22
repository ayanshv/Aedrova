begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('a1400000-0000-0000-0000-000000000001','thread-author@test.local',now()),
 ('a1400000-0000-0000-0000-000000000002','thread-reader@test.local',now());

do $$
declare author uuid := 'a1400000-0000-0000-0000-000000000001';
 reader uuid := 'a1400000-0000-0000-0000-000000000002';
 w uuid; c uuid; private_channel uuid;
 prompt uuid := gen_random_uuid(); answer uuid := gen_random_uuid(); secret_answer uuid := gen_random_uuid();
 wakes integer;
begin
 perform set_config('request.jwt.claim.sub', author::text, true);
 set local role authenticated;
 w := public.onboard_workspace('Shared chat activity fixture', 'Aedrova', 'codex');
 select id into c from public.channels where workspace_id=w and name='general';
 perform public.send_message(prompt,c,'@Aedrova what did we decide?');
 reset role;
 insert into public.workspace_members values (w,reader,'member');
 insert into public.channels(workspace_id,name,private) values (w,'private-source',true) returning id into private_channel;
 insert into public.channel_members values (w,private_channel,author);
 select count(*) into wakes from realtime.test_events where topic='user:'||reader::text;
 set local role authenticated;
 perform public.chat_action('typing',jsonb_build_object('channel',c,'active',true));
 perform public.report_chat_agent_progress(prompt,'context');
 perform public.save_agent_reply(answer,w,c,null,prompt,'Aedrova','Shared answer','{}','{}');
 perform public.save_agent_reply(secret_answer,w,c,null,prompt,'Aedrova','Private-source answer','{}',array[private_channel]);
 perform set_config('request.jwt.claim.sub', reader::text, true);
 assert exists(select 1 from public.chat_agent_progress where prompt_id=prompt and phase='context');
 assert not exists(select 1 from public.my_agent_replies where id in (answer,secret_answer));
 begin
  perform public.publish_chat_agent_reply(answer);
  raise exception 'Peer was allowed to publish another account’s reply';
 exception when insufficient_privilege then null;
 end;
 perform set_config('request.jwt.claim.sub', author::text, true);
 perform public.publish_chat_agent_reply(answer);
 perform public.publish_chat_agent_reply(secret_answer);
 perform set_config('request.jwt.claim.sub', reader::text, true);
 assert exists(select 1 from public.my_agent_replies where id=answer);
 assert not exists(select 1 from public.my_agent_replies where id=secret_answer);
 assert not exists(select 1 from public.chat_agent_progress where prompt_id=prompt);
 reset role;
 assert (select count(*) from realtime.test_events where topic='user:'||reader::text)>=wakes+3;
end $$;
rollback;
