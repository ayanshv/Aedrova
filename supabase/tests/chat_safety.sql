begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('a1500000-0000-0000-0000-000000000001','mod-a@example.invalid',now()),
 ('a1500000-0000-0000-0000-000000000002','mod-b@example.invalid',now()),
 ('a1500000-0000-0000-0000-000000000003','mod-c@example.invalid',now());
do $$
declare a uuid:='a1500000-0000-0000-0000-000000000001'; b uuid:='a1500000-0000-0000-0000-000000000002';
 outsider uuid:='a1500000-0000-0000-0000-000000000003';
 w uuid; c uuid; dm uuid; m uuid:=gen_random_uuid(); r uuid;
begin
 perform set_config('request.jwt.claim.sub',a::text,true); set local role authenticated;
 w:=public.onboard_workspace('Rolled back moderation','Aedrova','codex');
 select id into c from public.channels where workspace_id=w and name='general';
 perform public.send_message(m,c,'A normal message');
 reset role;
 insert into public.workspace_members(workspace_id,user_id,role) values (w,b,'member');
 set local role authenticated;
 begin
  perform public.send_message(gen_random_uuid(),c,'I will kill you.');
  raise exception 'Direct threat was accepted';
 exception when invalid_parameter_value then null;
 end;
 perform set_config('request.jwt.claim.sub',outsider::text,true);
 begin
  perform public.report_chat_message(m,'harassment');
  raise exception 'Outsider could report inaccessible message';
 exception when insufficient_privilege then null;
 end;
 perform set_config('request.jwt.claim.sub',b::text,true);
 r:=public.report_chat_message(m,'harassment');
 assert r is not null;
 assert r=public.report_chat_message(m,'harassment');
 dm:=public.start_direct_message(w,a);
 assert public.set_chat_block(w,a,true);
 assert (select count(*) from public.my_chat_blocks() where user_id=a)=1;
 perform set_config('request.jwt.claim.sub',a::text,true);
 assert not exists(select 1 from public.my_chat_blocks());
 begin
  perform public.start_direct_message(w,b);
  raise exception 'Blocked user could open DM';
 exception when insufficient_privilege then null;
 end;
 begin
  perform public.send_message(gen_random_uuid(),dm,'Blocked message');
  raise exception 'Blocked user could send DM';
 exception when insufficient_privilege then null;
 end;
 perform set_config('request.jwt.claim.sub',b::text,true);
 assert not public.set_chat_block(null,a,false);
 perform public.send_message(gen_random_uuid(),dm,'Allowed after unblocking');
 reset role;
 assert (select count(*) from aedrova_private.chat_reports where id=r and reporter_id=b and sender_id=a)=1;
 assert not has_table_privilege('authenticated','aedrova_private.chat_reports','select');
end $$;
rollback;
