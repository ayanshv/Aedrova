begin;

-- Devices that can receive push notifications for a signed-in person.
create table aedrova_private.push_devices (
 token text primary key check (token ~ '^[0-9a-fA-F]{32,200}$'),
 user_id uuid not null references auth.users(id) on delete cascade,
 environment text not null check (environment in ('development','production')),
 bundle_id text not null check (length(bundle_id) between 3 and 200),
 created_at timestamptz not null default now(),
 last_seen_at timestamptz not null default now()
);
create index push_devices_user on aedrova_private.push_devices(user_id);
alter table aedrova_private.push_devices enable row level security;
revoke all on aedrova_private.push_devices from public,anon,authenticated;

-- Where the notification sender lives. Empty until the owner configures it, so
-- applying this migration never sends anything by itself.
create table aedrova_private.push_config (
 key text primary key check (key in ('url','secret')),
 value text not null
);
alter table aedrova_private.push_config enable row level security;
revoke all on aedrova_private.push_config from public,anon,authenticated;

create function public.register_push_device(p_token text,p_environment text,p_bundle text) returns void
language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user();
begin
 perform aedrova_private.check_user_budget('push-register',30,3600);
 if p_token is null or p_token !~ '^[0-9a-fA-F]{32,200}$'
  or p_environment not in ('development','production')
  or p_bundle is null or length(p_bundle) not between 3 and 200
 then raise exception 'Device unavailable' using errcode='22023'; end if;
 insert into aedrova_private.push_devices(token,user_id,environment,bundle_id)
 values(lower(p_token),u,p_environment,p_bundle)
 on conflict(token) do update set user_id=excluded.user_id,environment=excluded.environment,
  bundle_id=excluded.bundle_id,last_seen_at=now();
 -- A person keeps their ten most recently used devices.
 delete from aedrova_private.push_devices d where d.user_id=u and d.token in (
  select token from aedrova_private.push_devices where user_id=u
  order by last_seen_at desc offset 10);
end $$;

create function public.unregister_push_device(p_token text) returns void
language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user();
begin
 delete from aedrova_private.push_devices where token=lower(p_token) and user_id=u;
end $$;

revoke all on function public.register_push_device(text,text,text),
 public.unregister_push_device(text) from public,anon;
grant execute on function public.register_push_device(text,text,text),
 public.unregister_push_device(text) to authenticated;

-- Tells the sender that a notification exists. It sends ids only, never message text.
create function aedrova_private.announce_notification() returns trigger
language plpgsql security definer set search_path='' as $$
declare target text; secret text;
begin
 select value into target from aedrova_private.push_config where key='url';
 select value into secret from aedrova_private.push_config where key='secret';
 if target is null or secret is null then return new; end if;
 if not exists(select 1 from aedrova_private.push_devices where user_id=new.user_id) then
  return new;
 end if;
 begin
  perform net.http_post(
   url:=target,
   body:=jsonb_build_object('notification_id',new.id),
   headers:=jsonb_build_object('Content-Type','application/json','Authorization','Bearer '||secret),
   timeout_milliseconds:=3000);
 exception when others then
  -- Delivering a push must never block or fail sending a message.
  null;
 end;
 return new;
end $$;

create trigger chat_notifications_announce after insert on public.chat_notifications
 for each row execute function aedrova_private.announce_notification();

commit;
