begin;

create or replace function aedrova_private.check_user_budget(p_bucket text,p_limit integer,p_seconds integer)
returns void language plpgsql security definer set search_path='' as $$
declare u uuid:=auth.uid(); w bigint; n integer;
begin
 if u is null then return; end if;
 w:=floor(extract(epoch from clock_timestamp())/p_seconds)::bigint*p_seconds;
 insert into aedrova_private.write_budgets values(u,p_bucket,w,1)
 on conflict(user_id,bucket,window_start) do update set count=write_budgets.count+1
 returning count into n;
 if n=1 then
  delete from aedrova_private.write_budgets
  where user_id=u and bucket=p_bucket and window_start<w-p_seconds;
 end if;
 if n>p_limit then raise exception 'Too many requests. Wait before retrying.' using errcode='P0001'; end if;
end $$;

alter function public.start_direct_message(uuid, uuid) set schema aedrova_private;
alter function public.message_page(uuid, bigint, bigint, uuid, boolean, integer) set schema aedrova_private;
alter function public.chat_inventory(uuid, text, text, uuid) set schema aedrova_private;

revoke all on function aedrova_private.start_direct_message(uuid, uuid),
 aedrova_private.message_page(uuid, bigint, bigint, uuid, boolean, integer),
 aedrova_private.chat_inventory(uuid, text, text, uuid)
 from public, anon, authenticated;

create function public.start_direct_message(p_workspace uuid, p_user uuid)
returns uuid language plpgsql volatile security definer set search_path='' as $$
begin
 perform aedrova_private.require_user();
 perform aedrova_private.check_user_budget('direct-message-open', 30, 60);
 return aedrova_private.start_direct_message(p_workspace, p_user);
end $$;

create function public.message_page(
 p_channel uuid, p_before bigint default null, p_after bigint default null,
 p_parent uuid default null, p_threads boolean default false, p_limit integer default 100
)
returns setof public.messages language plpgsql volatile security definer set search_path='' as $$
begin
 perform aedrova_private.require_user();
 perform aedrova_private.check_user_budget('message-page', 180, 60);
 return query select * from aedrova_private.message_page(
  p_channel, p_before, p_after, p_parent, p_threads, p_limit
 );
end $$;

create function public.chat_inventory(
 p_workspace uuid, p_query text default '', p_section text default 'search', p_channel uuid default null
)
returns jsonb language plpgsql volatile security definer set search_path='' as $$
begin
 perform aedrova_private.require_user();
 perform aedrova_private.check_user_budget('chat-inventory', 90, 60);
 return aedrova_private.chat_inventory(p_workspace, p_query, p_section, p_channel);
end $$;

revoke all on function public.start_direct_message(uuid, uuid),
 public.message_page(uuid, bigint, bigint, uuid, boolean, integer),
 public.chat_inventory(uuid, text, text, uuid) from public, anon;
grant execute on function public.start_direct_message(uuid, uuid),
 public.message_page(uuid, bigint, bigint, uuid, boolean, integer),
 public.chat_inventory(uuid, text, text, uuid) to authenticated;

notify pgrst, 'reload schema';
commit;
