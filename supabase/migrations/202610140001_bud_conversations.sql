-- Private Bud history is deliberately excluded from shared chat/search/notifications.
begin;
create table public.bud_messages (
 id uuid primary key,
 bud_id uuid not null references public.workspace_dots(id) on delete cascade,
 user_id uuid not null references auth.users(id) on delete cascade,
 role text not null check(role in ('user','assistant')),
 body text not null check(length(btrim(body)) between 1 and 20000),
 reply_to uuid references public.bud_messages(id) on delete cascade,
 created_at timestamptz not null default clock_timestamp(),
 check((role='user' and reply_to is null) or (role='assistant' and reply_to is not null)),
 unique(reply_to)
);
create index bud_messages_owner on public.bud_messages(user_id,bud_id,created_at desc,id);
create index bud_messages_rate on public.bud_messages(user_id,created_at desc);
alter table public.bud_messages enable row level security;
revoke all on public.bud_messages from public,anon,authenticated;
grant select on public.bud_messages to authenticated;
create policy bud_history_owner on public.bud_messages for select to authenticated using(
 user_id=auth.uid() and exists(select 1 from public.workspace_dots d where d.id=bud_id
 and aedrova_private.member_role(d.workspace_id) in ('owner','admin','member'))
);
create function public.bud_conversation(p_bud uuid) returns setof public.bud_messages
language plpgsql security invoker set search_path='' as $$
begin
 if not exists(select 1 from public.workspace_dots d where d.id=p_bud
 and aedrova_private.member_role(d.workspace_id) in ('owner','admin','member')) then
  raise exception 'This Bud is no longer available in your workspace' using errcode='42501';
 end if;
 return query select * from (select m.* from public.bud_messages m
 where m.bud_id=p_bud and m.user_id=auth.uid() order by m.created_at desc,m.id desc limit 100) recent
 order by recent.created_at,recent.id;
end $$;
create function public.append_bud_message(p_id uuid,p_bud uuid,p_body text,
 p_reply_to uuid default null) returns public.bud_messages
language plpgsql security definer set search_path='' as $$
declare r public.bud_messages; existing public.bud_messages;
begin
 perform aedrova_private.require_user();
 if auth.uid() is null or not exists(select 1 from public.workspace_dots d where d.id=p_bud and d.deleted_at is null
 and aedrova_private.member_role(d.workspace_id) in ('owner','admin','member')) then
  raise exception 'This Bud is no longer available in your workspace' using errcode='42501';
 end if;
 if p_id is null or p_body is null or length(btrim(p_body)) not between 1 and 20000 then
  raise exception 'Write a message of up to 20000 characters';
 end if;
 perform pg_advisory_xact_lock(hashtextextended('bud-chat:'||auth.uid()::text,0));
 select * into existing from public.bud_messages where id=p_id;
 if found then
  if existing.user_id<>auth.uid() or existing.bud_id<>p_bud or existing.body<>p_body
   or existing.reply_to is distinct from p_reply_to then
   raise exception 'Message identity conflict' using errcode='42501';
  end if;
  return existing;
 end if;
 if p_reply_to is not null and not exists(select 1 from public.bud_messages m
 where m.id=p_reply_to and m.bud_id=p_bud and m.user_id=auth.uid() and m.role='user') then
  raise exception 'Reply does not belong to this conversation' using errcode='42501';
 end if;
 if p_reply_to is not null then
  select * into existing from public.bud_messages m where m.reply_to=p_reply_to
   and m.user_id=auth.uid() and m.bud_id=p_bud;
  if found then return existing; end if;
 end if;
 if (select count(*) from public.bud_messages m where m.user_id=auth.uid()
 and m.created_at>now()-interval '1 minute')>=30 then
  raise exception 'Please wait a moment before sending more messages' using errcode='P0001';
 end if;
 insert into public.bud_messages(id,bud_id,user_id,role,body,reply_to)
 values(p_id,p_bud,auth.uid(),case when p_reply_to is null then 'user' else 'assistant' end,
 p_body,p_reply_to) returning * into r;
 return r;
end $$;
revoke all on function public.bud_conversation(uuid),
 public.append_bud_message(uuid,uuid,text,uuid) from public,anon;
grant execute on function public.bud_conversation(uuid),
 public.append_bud_message(uuid,uuid,text,uuid) to authenticated;
comment on table public.bud_messages is
 'Per-user Bud conversation; assistant text is client-supplied AI output, never authority or shared context.';
commit;
