begin;
create table public.messages (
 id uuid primary key,
 channel_id uuid not null references public.channels on delete cascade,
 sender_id uuid not null references auth.users,
 body text not null check(length(btrim(body)) between 1 and 10000),
 parent_id uuid,
 created_at timestamptz not null default clock_timestamp(),
 unique(channel_id,id),
 foreign key(channel_id,parent_id) references public.messages(channel_id,id),
 check(parent_id is distinct from id)
);
create index messages_channel_time on public.messages(channel_id,created_at desc,id);
alter table public.messages enable row level security;
revoke all on public.messages from public,anon,authenticated;
grant select on public.messages to authenticated;
create policy messages_read on public.messages for select to authenticated
 using(aedrova_private.can_read_channel(channel_id));
create function public.send_message(p_id uuid,p_channel uuid,p_body text,p_parent uuid default null)
returns uuid language plpgsql security definer set search_path='' as $$
declare u uuid := aedrova_private.require_user(); w uuid; old public.messages;
begin
 select workspace_id into w from public.channels where id=p_channel;
 -- Serialize against membership revocation and other writes in this workspace.
 perform 1 from public.workspaces where id=w for update;
 if not aedrova_private.can_read_channel(p_channel)
 or coalesce(aedrova_private.member_role(w),'') not in ('owner','admin','member')
 then raise exception 'Not allowed' using errcode='42501'; end if;
 if p_parent is not null and not exists(select 1 from public.messages
 where id=p_parent and channel_id=p_channel and parent_id is null)
 then raise exception 'Thread unavailable' using errcode='42501'; end if;
 insert into public.messages(id,channel_id,sender_id,body,parent_id)
 values(p_id,p_channel,u,btrim(p_body),p_parent) on conflict(id) do nothing;
 select * into old from public.messages where id=p_id;
 if old.sender_id is distinct from u or old.channel_id is distinct from p_channel
 or old.body is distinct from btrim(p_body) or old.parent_id is distinct from p_parent
 then raise exception 'Message identity conflict' using errcode='42501'; end if;
 return p_id;
end $$;
revoke all on function public.send_message(uuid,uuid,text,uuid) from public,anon;
grant execute on function public.send_message(uuid,uuid,text,uuid) to authenticated;
commit;
