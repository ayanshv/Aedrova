begin;

create function aedrova_private.wake_channel_peers(p_channel uuid, p_actor uuid)
returns void language sql security definer set search_path='' as $$
 select realtime.send('{}'::jsonb, 'refresh', 'user:' || m.user_id::text, true)
 from public.channels c join public.workspace_members m on m.workspace_id=c.workspace_id
 where c.id=p_channel and m.user_id<>p_actor and (
    (not c.private and m.role<>'guest') or exists (
      select 1 from public.channel_members cm where cm.channel_id=c.id and cm.user_id=m.user_id
    )
 );
$$;
revoke all on function aedrova_private.wake_channel_peers(uuid,uuid) from public,anon,authenticated;

create function aedrova_private.wake_typing_peers() returns trigger
language plpgsql security definer set search_path='' as $$
begin
 if tg_op='DELETE' then
   perform aedrova_private.wake_channel_peers(old.channel_id,old.user_id);
 elsif tg_op='INSERT' or old.expires_at<=now() then
   perform aedrova_private.wake_channel_peers(new.channel_id,new.user_id);
 end if;
 return null;
end $$;
revoke all on function aedrova_private.wake_typing_peers() from public,anon,authenticated;
create trigger wake_typing_peers after insert or update or delete on public.chat_typing
for each row execute function aedrova_private.wake_typing_peers();

alter table public.agent_reply_history add column shared boolean not null default false;
alter policy agent_reply_history_read on public.agent_reply_history using (
 (author_id=(select auth.uid()) or (shared and exists (
   select 1 from public.messages p where p.id=agent_reply_history.prompt_id and p.unsent_at is null
 ))) and aedrova_private.member_role(workspace_id) in ('owner','admin','member')
 and aedrova_private.can_read_channel(channel_id)
 and not exists(select 1 from unnest(source_channels) s(id) where not aedrova_private.can_read_channel(s.id))
 and (parent_id is null or exists(select 1 from public.messages m
    where m.id=agent_reply_history.parent_id and m.unsent_at is null))
);
create index agent_reply_shared_recent on public.agent_reply_history
 (workspace_id,channel_id,parent_id,created_at desc,id) where shared;

create table public.chat_agent_progress (
 prompt_id uuid primary key references public.messages(id) on delete cascade,
 channel_id uuid not null references public.channels(id) on delete cascade,
 author_id uuid not null references auth.users(id) on delete cascade,
 parent_id uuid references public.messages(id) on delete cascade,
 phase text not null check (phase in ('thinking','context','responding')),
 expires_at timestamptz not null
);
alter table public.chat_agent_progress enable row level security;
revoke all on public.chat_agent_progress from public,anon,authenticated;
grant select on public.chat_agent_progress to authenticated;
create policy chat_agent_progress_read on public.chat_agent_progress for select to authenticated using (
 expires_at>now() and aedrova_private.can_read_channel(channel_id)
 and exists(select 1 from public.messages m where m.id=prompt_id and m.unsent_at is null)
 and (parent_id is null or exists(select 1 from public.messages m
   where m.id=chat_agent_progress.parent_id and m.unsent_at is null))
);
create index chat_agent_progress_channel on public.chat_agent_progress(channel_id,expires_at);

create function public.report_chat_agent_progress(p_prompt uuid, p_phase text) returns void
language plpgsql security definer set search_path='' as $$
declare requester uuid := aedrova_private.require_user(); prompt public.messages; previous text;
begin
 select * into prompt from public.messages m where m.id=p_prompt and m.sender_id=requester and m.unsent_at is null;
 if not found or not aedrova_private.can_read_channel(prompt.channel_id) then
   raise exception 'Prompt unavailable' using errcode='42501';
 end if;
 perform aedrova_private.check_user_budget('chat-agent-progress',60,60);
 select phase into previous from public.chat_agent_progress where prompt_id=p_prompt and expires_at>now();
 if p_phase='finished' then
   delete from public.chat_agent_progress where prompt_id=p_prompt;
 elsif p_phase in ('thinking','context','responding') then
   delete from public.chat_agent_progress where author_id=requester and expires_at<=now();
   insert into public.chat_agent_progress values(p_prompt,prompt.channel_id,requester,prompt.parent_id,p_phase,now()+interval '35 seconds')
   on conflict(prompt_id) do update set phase=excluded.phase,expires_at=excluded.expires_at;
 else
   raise exception 'Unknown activity phase' using errcode='22023';
 end if;
 if previous is distinct from p_phase then
   perform aedrova_private.wake_channel_peers(prompt.channel_id,requester);
 end if;
end $$;

create function public.publish_chat_agent_reply(p_reply uuid) returns void
language plpgsql security definer set search_path='' as $$
declare requester uuid := aedrova_private.require_user(); reply public.agent_reply_history;
begin
 update public.agent_reply_history r set shared=true
 where r.id=p_reply and r.author_id=requester and aedrova_private.can_read_channel(r.channel_id)
 and aedrova_private.member_role(r.workspace_id) in ('owner','admin','member')
 and not exists(select 1 from unnest(r.source_channels) s(id) where not aedrova_private.can_read_channel(s.id))
 and exists(select 1 from public.messages p where p.id=r.prompt_id and p.sender_id=requester and p.unsent_at is null)
 returning r.* into reply;
 if not found then raise exception 'Reply or prompt unavailable' using errcode='42501'; end if;
 delete from public.chat_agent_progress where prompt_id=reply.prompt_id;
 perform aedrova_private.wake_channel_peers(reply.channel_id,requester);
end $$;

revoke all on function public.report_chat_agent_progress(uuid,text),public.publish_chat_agent_reply(uuid) from public,anon;
grant execute on function public.report_chat_agent_progress(uuid,text),public.publish_chat_agent_reply(uuid) to authenticated;
notify pgrst, 'reload schema';
commit;
