begin;

-- The website sender has no direct table access. It reads one notification, its
-- recipient's devices and unseen count, and prunes dead devices only through these.
create function public.push_delivery(p_id bigint) returns jsonb
language plpgsql security definer set search_path='' as $$
declare r record; devs jsonb; pending integer;
begin
 select n.user_id, n.kind, m.channel_id, m.id as message_id, m.parent_id,
  c.workspace_id, c.name as channel_name, c.kind as channel_kind,
  coalesce(u.raw_user_meta_data->>'full_name','Someone') as sender
 into r
 from public.chat_notifications n
 join public.messages m on m.id=n.message_id
 join public.channels c on c.id=m.channel_id
 left join auth.users u on u.id=m.sender_id
 where n.id=p_id and m.unsent_at is null;
 if not found then return null; end if;
 select coalesce(jsonb_agg(jsonb_build_object('token',d.token,'environment',d.environment)),'[]'::jsonb)
  into devs from aedrova_private.push_devices d where d.user_id=r.user_id;
 select count(*) into pending from public.chat_notifications x
  where x.user_id=r.user_id and x.seen_at is null;
 return jsonb_build_object('user_id',r.user_id,'kind',r.kind,'channel',r.channel_id,
  'message',r.message_id,'parent',r.parent_id,'workspace',r.workspace_id,
  'channel_name',r.channel_name,'channel_kind',r.channel_kind,'sender',r.sender,
  'devices',devs,'unseen',pending);
end $$;

create function public.push_forget_device(p_token text) returns void
language sql security definer set search_path='' as $$
 delete from aedrova_private.push_devices where token=lower(p_token);
$$;

revoke all on function public.push_delivery(bigint),public.push_forget_device(text)
 from public,anon,authenticated,service_role;
grant execute on function public.push_delivery(bigint),public.push_forget_device(text)
 to aedrova_website;

commit;
