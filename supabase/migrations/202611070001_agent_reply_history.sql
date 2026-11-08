begin;

create table public.agent_reply_history (
 id uuid primary key,
 workspace_id uuid not null references public.workspaces(id) on delete cascade,
 channel_id uuid not null references public.channels(id) on delete cascade,
 author_id uuid not null references auth.users(id) on delete cascade,
 parent_id uuid references public.messages(id) on delete cascade,
 prompt_id uuid references public.messages(id) on delete set null,
 agent_name text not null check (length(btrim(agent_name)) between 1 and 80),
 body text not null check (length(btrim(body)) between 1 and 20000),
 bud_avatar jsonb not null check (jsonb_typeof(bud_avatar) = 'object' and octet_length(bud_avatar::text) <= 1024),
 source_channels uuid[] not null check (cardinality(source_channels) between 1 and 500),
 created_at timestamptz not null default clock_timestamp()
);
create index agent_reply_history_recent on public.agent_reply_history
 (author_id, workspace_id, channel_id, parent_id, created_at desc, id);
alter table public.agent_reply_history enable row level security;
revoke all on public.agent_reply_history from public, anon, authenticated;
grant select on public.agent_reply_history to authenticated;
create policy agent_reply_history_read on public.agent_reply_history for select to authenticated using (
 author_id = (select auth.uid())
 and aedrova_private.member_role(workspace_id) in ('owner','admin','member')
 and aedrova_private.can_read_channel(channel_id)
 and not exists (
  select 1 from unnest(source_channels) s(id) where not aedrova_private.can_read_channel(s.id)
 )
 and (parent_id is null or exists (
  select 1 from public.messages m
  where m.id=agent_reply_history.parent_id and m.unsent_at is null
 ))
);

create function public.save_agent_reply(p_id uuid,p_workspace uuid,p_channel uuid,
 p_parent uuid,p_prompt uuid,p_agent text,p_body text,p_avatar jsonb,p_sources uuid[]) returns uuid
language plpgsql security definer set search_path='' as $$
declare existing public.agent_reply_history; sources uuid[]; prompt uuid;
begin
 perform aedrova_private.require_user();
 perform 1 from public.workspaces where id=p_workspace for update;
 if coalesce(aedrova_private.member_role(p_workspace),'') not in ('owner','admin','member')
 or not exists(select 1 from public.channels c where c.id=p_channel
 and c.workspace_id=p_workspace and aedrova_private.can_read_channel(c.id)) then
  raise exception 'Reply history requires channel access' using errcode='42501';
 end if;
 if p_id is null or p_body is null or length(btrim(p_body)) not between 1 and 20000
 or p_agent is null or length(btrim(p_agent)) not between 1 and 80
 or p_sources is null or cardinality(p_sources)>499
 or p_avatar is null or jsonb_typeof(p_avatar)<>'object'
 or octet_length(p_avatar::text)>1024 then
  raise exception 'Invalid agent reply' using errcode='22023';
 end if;
 if p_body ~ '(sb_secret_|sk-(proj-|ant-)|[sr]k_(live|test)_|whsec_|gh[pousr]_)[A-Za-z0-9_-]{20,}|-----BEGIN .*PRIVATE KEY-----' then
  raise exception 'Remove credentials before saving agent replies' using errcode='22023';
 end if;
 select array_agg(distinct x order by x) into sources from unnest(p_sources||array[p_channel]) x;
 if exists(select 1 from unnest(sources) s(id) where s.id is null or not exists(
  select 1 from public.channels c where c.id=s.id and c.workspace_id=p_workspace
  and aedrova_private.can_read_channel(c.id))) then
  raise exception 'Reply source access changed' using errcode='42501';
 end if;
 if p_parent is not null and not exists(select 1 from public.messages m where
  m.id=p_parent and m.channel_id=p_channel and m.parent_id is null and m.unsent_at is null) then
  raise exception 'Reply thread unavailable' using errcode='42501';
 end if;
 select m.id into prompt from public.messages m where m.id=p_prompt and m.channel_id=p_channel
  and m.parent_id is not distinct from p_parent and m.unsent_at is null;
 perform pg_advisory_xact_lock(hashtextextended('agent-reply-history:'||p_id::text,0));
 select * into existing from public.agent_reply_history where id=p_id;
 if found then
  if existing.author_id<>auth.uid() or existing.workspace_id<>p_workspace
  or existing.channel_id<>p_channel or existing.parent_id is distinct from p_parent
  or existing.agent_name<>p_agent or existing.body<>p_body or existing.bud_avatar<>p_avatar
  or existing.source_channels<>sources then
   raise exception 'Agent reply identity conflict' using errcode='42501';
  end if;
  return existing.id;
 end if;
 perform aedrova_private.check_user_budget('agent-reply-history',60,60);
 insert into public.agent_reply_history(id,workspace_id,channel_id,author_id,parent_id,prompt_id,
  agent_name,body,bud_avatar,source_channels)
 values(p_id,p_workspace,p_channel,auth.uid(),p_parent,prompt,p_agent,p_body,p_avatar,sources);
 return p_id;
end $$;
revoke all on function public.save_agent_reply(uuid,uuid,uuid,uuid,uuid,text,text,jsonb,uuid[]) from public,anon;
grant execute on function public.save_agent_reply(uuid,uuid,uuid,uuid,uuid,text,text,jsonb,uuid[]) to authenticated;
-- Earlier versions retained some channel replies only as shared evidence.
create view public.my_agent_replies with (security_invoker=true) as
 select id,workspace_id,channel_id,author_id,parent_id,prompt_id,agent_name,body,bud_avatar,created_at
 from public.agent_reply_history
 union all
 select w.id,w.workspace_id,w.channel_id,w.author_id,null::uuid,null::uuid,
  w.agent_name,w.body,null::jsonb,w.created_at
 from public.shared_agent_work w
 where w.author_id=(select auth.uid()) and not exists(
  select 1 from public.agent_reply_history r where r.id=w.id
 );
revoke all on public.my_agent_replies from public,anon,authenticated;
grant select on public.my_agent_replies to authenticated;
commit;
