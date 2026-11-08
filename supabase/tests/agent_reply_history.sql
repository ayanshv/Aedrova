begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('f7100000-0000-0000-0000-000000000001','reply-owner@test.local',now()),
 ('f7100000-0000-0000-0000-000000000002','reply-member@test.local',now());

do $$
declare w uuid; c uuid; private_channel uuid; owner_id uuid := 'f7100000-0000-0000-0000-000000000001';
 member_id uuid := 'f7100000-0000-0000-0000-000000000002';
 reply_id uuid := 'f7200000-0000-0000-0000-000000000001';
 test_prompt uuid := 'f7200000-0000-0000-0000-000000000002';
begin
 perform set_config('request.jwt.claim.sub',owner_id::text,true);
 set local role authenticated;
 w := public.onboard_workspace('Reply history fixture','Aedrova','codex');
 select id into c from public.channels where workspace_id=w and name='general';
 perform public.send_message(test_prompt,c,'What were we building?');
 reset role;
 insert into public.workspace_members(workspace_id,user_id,role) values(w,member_id,'member');
 insert into public.channels(workspace_id,name,private) values(w,'private-evidence',true)
  returning id into private_channel;
 insert into public.channel_members(workspace_id,channel_id,user_id) values(w,private_channel,owner_id);
 set local role authenticated;
 perform public.save_agent_reply(reply_id,w,c,null,test_prompt,'Aedrova','Saved answer','{}',array[private_channel]);
 perform public.save_agent_reply(reply_id,w,c,null,test_prompt,'Aedrova','Saved answer','{}',array[private_channel]);
 if (select count(*) from public.my_agent_replies where id=reply_id and my_agent_replies.prompt_id=test_prompt)<>1 then
  raise exception 'Reply did not survive read or retry';
 end if;
 perform set_config('request.jwt.claim.sub',member_id::text,true);
 if exists(select 1 from public.my_agent_replies where id=reply_id) then
  raise exception 'Another member saw private reply history';
 end if;
 reset role;
 delete from public.channel_members where channel_id=private_channel and user_id=owner_id;
 perform set_config('request.jwt.claim.sub',owner_id::text,true);
 set local role authenticated;
 if exists(select 1 from public.my_agent_replies where id=reply_id) then
  raise exception 'Reply remained after source revocation';
 end if;
end $$;
rollback;
