begin;

-- Android phones register a Firebase token, which is not hexadecimal and is case sensitive.
alter table aedrova_private.push_devices
 add column if not exists platform text not null default 'ios'
 check (platform in ('ios','android'));
alter table aedrova_private.push_devices drop constraint if exists push_devices_token_check;
alter table aedrova_private.push_devices add constraint push_devices_token_check check (
 (platform='ios' and token ~ '^[0-9a-fA-F]{32,200}$')
 or (platform='android' and token ~ '^[A-Za-z0-9:_-]{60,4096}$'));

create function public.register_android_push_device(p_token text,p_environment text,p_package text)
returns void
language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user();
begin
 perform aedrova_private.check_user_budget('push-register',30,3600);
 if p_token is null or p_token !~ '^[A-Za-z0-9:_-]{60,4096}$'
  or p_environment not in ('development','production')
  or p_package is null or length(p_package) not between 3 and 200
 then raise exception 'Device unavailable' using errcode='22023'; end if;
 insert into aedrova_private.push_devices(token,user_id,environment,bundle_id,platform)
 values(p_token,u,p_environment,p_package,'android')
 on conflict(token) do update set user_id=excluded.user_id,environment=excluded.environment,
  bundle_id=excluded.bundle_id,platform='android',last_seen_at=now();
 -- A person keeps their ten most recently used devices, across phones.
 delete from aedrova_private.push_devices d where d.user_id=u and d.token in (
  select token from aedrova_private.push_devices where user_id=u
  order by last_seen_at desc offset 10);
end $$;

create function public.unregister_android_push_device(p_token text) returns void
language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user();
begin
 delete from aedrova_private.push_devices where token=p_token and user_id=u;
end $$;

revoke all on function public.register_android_push_device(text,text,text),
 public.unregister_android_push_device(text) from public,anon;
grant execute on function public.register_android_push_device(text,text,text),
 public.unregister_android_push_device(text) to authenticated;

-- The sender now also learns each device's platform, and can forget either kind of token.
create or replace function public.push_delivery(p_id bigint) returns jsonb
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
 select coalesce(jsonb_agg(jsonb_build_object('token',d.token,'environment',d.environment,
   'platform',d.platform)),'[]'::jsonb)
  into devs from aedrova_private.push_devices d where d.user_id=r.user_id;
 select count(*) into pending from public.chat_notifications x
  where x.user_id=r.user_id and x.seen_at is null;
 return jsonb_build_object('user_id',r.user_id,'kind',r.kind,'channel',r.channel_id,
  'message',r.message_id,'parent',r.parent_id,'workspace',r.workspace_id,
  'channel_name',r.channel_name,'channel_kind',r.channel_kind,'sender',r.sender,
  'devices',devs,'unseen',pending);
end $$;

create or replace function public.push_forget_device(p_token text) returns void
language sql security definer set search_path='' as $$
 delete from aedrova_private.push_devices where token=p_token or token=lower(p_token);
$$;

commit;
