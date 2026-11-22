begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('a2000000-0000-0000-0000-000000000001','pin-owner@test.local',now()),
 ('a2000000-0000-0000-0000-000000000002','pin-reader@test.local',now());

do $$
declare
 owner_id uuid := 'a2000000-0000-0000-0000-000000000001';
 reader_id uuid := 'a2000000-0000-0000-0000-000000000002';
 w uuid;
 c uuid;
 private_channel uuid;
 msg uuid := gen_random_uuid();
 secret uuid := gen_random_uuid();
 reader_topic text := 'user:' || reader_id::text;
 wakes integer;
begin
 perform set_config('request.jwt.claim.sub',owner_id::text,true);
 set local role authenticated;
 w := public.onboard_workspace('Pin sync fixture','Aedrova','codex');
 select id into c from public.channels where workspace_id=w and name='general';
 reset role;
 insert into public.workspace_members values (w,reader_id,'member');
 insert into public.channels(workspace_id,name,private) values(w,'private-pins',true)
 returning id into private_channel;
 insert into public.channel_members values(w,private_channel,owner_id);
 set local role authenticated;
 perform public.send_message(msg,c,'Share this pin');
 perform public.send_message(secret,private_channel,'Private pin');
 reset role;
 select count(*) into wakes from realtime.test_events where topic=reader_topic;
 set local role authenticated;
 perform public.chat_action('saved',jsonb_build_object('message',msg,'present',true));
 perform public.chat_action('pinned',jsonb_build_object('message',secret,'present',true));
 perform public.chat_action('pinned',jsonb_build_object('message',msg,'present',true));
 perform public.chat_action('pinned',jsonb_build_object('message',msg,'present',true));
 perform set_config('request.jwt.claim.sub',reader_id::text,true);
 assert jsonb_array_length(public.chat_inventory(w,'','pinned',c)->'messages')=1;
 assert jsonb_array_length(public.message_interactions(array[secret]))=0;
 reset role;
 assert (select count(*) from realtime.test_events where topic=reader_topic)=wakes+1;
 perform set_config('request.jwt.claim.sub',owner_id::text,true);
 set local role authenticated;
 perform public.chat_action('pinned',jsonb_build_object('message',msg,'present',false));
 perform set_config('request.jwt.claim.sub',reader_id::text,true);
 assert jsonb_array_length(public.chat_inventory(w,'','pinned',c)->'messages')=0;
 reset role;
 assert (select count(*) from realtime.test_events where topic=reader_topic)=wakes+2;
 set local role authenticated;
 perform set_config('request.jwt.claim.sub',owner_id::text,true);
 perform public.set_message_reaction(msg,'👍',true);
 perform set_config('request.jwt.claim.sub',reader_id::text,true);
 assert public.message_interactions(array[msg]) @>
  '[{"reactions":[{"emoji":"👍","count":1,"mine":false}],"saved":false}]'::jsonb;
 perform public.set_message_reaction(msg,'👍',true);
 assert public.message_interactions(array[msg]) @>
  '[{"reactions":[{"emoji":"👍","count":2,"mine":true}]}]'::jsonb;
 perform public.set_message_reaction(msg,'👍',false);
 assert public.message_interactions(array[msg]) @>
  '[{"reactions":[{"emoji":"👍","count":1,"mine":false}]}]'::jsonb;
 reset role;
end $$;
rollback;
