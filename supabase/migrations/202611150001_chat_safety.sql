begin;

create table aedrova_private.chat_reports (
 id uuid primary key default gen_random_uuid(),
 reporter_id uuid not null,
 message_id uuid not null,
 workspace_id uuid not null,
 channel_id uuid not null,
 sender_id uuid not null,
 excerpt text not null,
 reason text not null check (reason in ('harassment','threat','spam','sexual_content','other')),
 created_at timestamptz not null default now(),
 reviewed_at timestamptz,
 unique (reporter_id,message_id)
);
create table aedrova_private.chat_blocks (
 blocker_id uuid not null references auth.users(id) on delete cascade,
 blocked_id uuid not null references auth.users(id) on delete cascade,
 primary key (blocker_id,blocked_id),
 check (blocker_id <> blocked_id)
);
alter table aedrova_private.chat_reports enable row level security;
alter table aedrova_private.chat_blocks enable row level security;
revoke all on aedrova_private.chat_reports, aedrova_private.chat_blocks from public,anon,authenticated;

create function public.report_chat_message(p_message uuid,p_reason text) returns uuid
language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); report_id uuid;
begin
 perform aedrova_private.check_user_budget('chat-report',15,3600);
 insert into aedrova_private.chat_reports(reporter_id,message_id,workspace_id,channel_id,sender_id,excerpt,reason)
 select u,m.id,c.workspace_id,c.id,m.sender_id,left(m.body,2000),p_reason
 from public.messages m join public.channels c on c.id=m.channel_id
 where m.id=p_message and m.sender_id<>u and m.unsent_at is null
 and aedrova_private.can_read_channel(c.id)
 on conflict(reporter_id,message_id) do nothing returning id into report_id;
 if report_id is null then
  select id into report_id from aedrova_private.chat_reports where reporter_id=u and message_id=p_message;
 end if;
 if report_id is null then raise exception 'Message unavailable' using errcode='42501'; end if;
 return report_id;
end $$;

create function public.set_chat_block(p_workspace uuid,p_user uuid,p_blocked boolean) returns boolean
language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user();
begin
 perform aedrova_private.check_user_budget('chat-block',30,60);
 if p_blocked is true then
  if p_user is null or p_user=u or aedrova_private.member_role(p_workspace) is null or not exists(
   select 1 from public.workspace_members m where m.workspace_id=p_workspace and m.user_id=p_user
  ) then raise exception 'Teammate unavailable' using errcode='42501'; end if;
  insert into aedrova_private.chat_blocks values(u,p_user) on conflict do nothing;
 elsif p_blocked is false then
  delete from aedrova_private.chat_blocks where blocker_id=u and blocked_id=p_user;
 else
  raise exception 'Block status required' using errcode='22023';
 end if;
 return p_blocked;
end $$;

create function public.my_chat_blocks() returns table(user_id uuid,display_name text)
language sql stable security definer set search_path='' as $$
 select b.blocked_id,
 case when exists (
  select 1 from public.workspace_members a join public.workspace_members peer using (workspace_id)
  where a.user_id=b.blocker_id and peer.user_id=b.blocked_id
 ) then coalesce(p.display_name,'Teammate') else 'Former teammate' end
 from aedrova_private.chat_blocks b left join public.chat_profiles p on p.user_id=b.blocked_id
 where b.blocker_id=(select auth.uid())
$$;

create function aedrova_private.chat_pair_blocked(a uuid,b uuid) returns boolean
language sql stable security definer set search_path='' as $$
 select exists(select 1 from aedrova_private.chat_blocks where
 (blocker_id,blocked_id) in ((a,b),(b,a)))
$$;
revoke all on function aedrova_private.chat_pair_blocked(uuid,uuid) from public,anon,authenticated;

create or replace function public.start_direct_message(p_workspace uuid,p_user uuid) returns uuid
language plpgsql volatile security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); c uuid;
begin
 perform aedrova_private.check_user_budget('direct-message-open',30,60);
 perform 1 from public.workspaces where id=p_workspace for update;
 if u=p_user or coalesce(aedrova_private.member_role(p_workspace),'') not in ('owner','admin','member')
 or not exists(select 1 from public.workspace_members where workspace_id=p_workspace
 and user_id=p_user and role in ('owner','admin','member'))
 then raise exception 'Recipient unavailable' using errcode='42501'; end if;
 if aedrova_private.chat_pair_blocked(u,p_user) then
  raise exception 'Direct message unavailable' using errcode='42501';
 end if;
 select id into c from public.channels where workspace_id=p_workspace
 and kind='dm' and dm_low=least(u,p_user) and dm_high=greatest(u,p_user);
 if c is null then
 c:=gen_random_uuid();
 insert into public.channels(id,workspace_id,name,private,kind,dm_low,dm_high)
 values(c,p_workspace,'dm-'||c::text,true,'dm',least(u,p_user),greatest(u,p_user));
 end if;
 insert into public.channel_members values(p_workspace,c,u),(p_workspace,c,p_user)
 on conflict do nothing;
 return c;
end $$;

create function aedrova_private.enforce_chat_safety() returns trigger
language plpgsql security definer set search_path='' as $$
begin
 if tg_op='INSERT' and exists(select 1 from public.channels c where c.id=new.channel_id and c.kind='dm'
 and aedrova_private.chat_pair_blocked(c.dm_low,c.dm_high)) then
  raise exception 'Direct message unavailable' using errcode='42501';
 end if;
 if new.unsent_at is null and new.body ~* $threat$^\s*(i will|i['’]ll|i am going to) (kill|shoot|stab) you( right now)?[.!]*\s*(?:$)$threat$ then
  raise exception 'Chat safety: direct threat' using errcode='22023';
 end if;
 return new;
end $$;
revoke all on function aedrova_private.enforce_chat_safety() from public,anon,authenticated;
create trigger enforce_chat_safety before insert or update of body on public.messages
for each row execute function aedrova_private.enforce_chat_safety();

revoke all on function public.report_chat_message(uuid,text),public.set_chat_block(uuid,uuid,boolean),public.my_chat_blocks()
 from public,anon,authenticated;
grant execute on function public.report_chat_message(uuid,text),public.set_chat_block(uuid,uuid,boolean),public.my_chat_blocks()
 to authenticated;
notify pgrst,'reload schema';
commit;
