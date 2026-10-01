begin;
create table public.context_decisions (
 message_id uuid primary key references public.messages(id) on delete cascade,
 channel_id uuid not null,
 source_body text not null,
 confirmed boolean not null,
 confirmed_by uuid not null references auth.users(id),
 updated_at timestamptz not null default clock_timestamp(),
 foreign key(channel_id,message_id) references public.messages(channel_id,id) on delete cascade
);
create index context_decisions_channel on public.context_decisions(channel_id,message_id);
alter table public.context_decisions enable row level security;
revoke all on public.context_decisions from public,anon,authenticated;
grant select on public.context_decisions to authenticated;
create policy context_decisions_read on public.context_decisions for select to authenticated
 using(aedrova_private.can_read_channel(channel_id));
create function public.set_context_decision(p_message uuid,p_body text,p_confirmed boolean)
returns void language plpgsql security definer set search_path='' as $$
declare u uuid := aedrova_private.require_user(); w uuid; m public.messages;
begin
 select c.workspace_id into w from public.messages x join public.channels c on c.id=x.channel_id
 where x.id=p_message;
 perform 1 from public.workspaces where id=w for update;
 select * into m from public.messages where id=p_message for update;
 if m.id is null or not aedrova_private.can_read_channel(m.channel_id)
 or coalesce(aedrova_private.member_role(w),'') not in ('owner','admin','member') then
 raise exception 'Not allowed' using errcode='42501'; end if;
 if m.body is distinct from p_body then
 raise exception 'Source changed. Refresh context before recording a decision.' using errcode='40001'; end if;
 insert into public.context_decisions(message_id,channel_id,source_body,confirmed,confirmed_by)
 values(m.id,m.channel_id,m.body,p_confirmed,u)
 on conflict(message_id) do update set source_body=excluded.source_body,confirmed=excluded.confirmed,
 confirmed_by=excluded.confirmed_by,updated_at=clock_timestamp();
end $$;
revoke all on function public.set_context_decision(uuid,text,boolean) from public,anon;
grant execute on function public.set_context_decision(uuid,text,boolean) to authenticated;
-- Revision counters detect edits/deletions occurring between paged reads.
create table aedrova_private.context_revisions (
 channel_id uuid primary key references public.channels(id) on delete cascade,
 revision bigint not null default 0
);
revoke all on aedrova_private.context_revisions from public,anon,authenticated;
create function aedrova_private.bump_context_revision() returns trigger
language plpgsql security definer set search_path='' as $$
declare c uuid;
begin
 if tg_table_name='channels' then c:=new.id;
 elsif tg_op='DELETE' then c:=old.channel_id;
 else c:=new.channel_id; end if;
 if exists(select 1 from public.channels where id=c) then
 insert into aedrova_private.context_revisions(channel_id,revision) values(c,1)
 on conflict(channel_id) do update set revision=context_revisions.revision+1;
 end if;
 if tg_op='UPDATE' and tg_table_name<>'channels' then
 if old.channel_id is distinct from new.channel_id and exists(select 1 from public.channels where id=old.channel_id) then
 insert into aedrova_private.context_revisions(channel_id,revision) values(old.channel_id,1)
 on conflict(channel_id) do update set revision=context_revisions.revision+1;
 end if;
 end if;
 return null;
end $$;
revoke all on function aedrova_private.bump_context_revision() from public,anon,authenticated;
create trigger context_message_revision after insert or update or delete on public.messages
 for each row execute function aedrova_private.bump_context_revision();
create trigger context_attachment_revision after insert or update or delete on public.attachments
 for each row execute function aedrova_private.bump_context_revision();
create trigger context_decision_revision after insert or update or delete on public.context_decisions
 for each row execute function aedrova_private.bump_context_revision();
create trigger context_channel_revision after update of name,private on public.channels
 for each row execute function aedrova_private.bump_context_revision();
create function public.context_revision(p_channel uuid) returns bigint
language plpgsql stable security definer set search_path='' as $$
begin
 if not aedrova_private.can_read_channel(p_channel) then
 raise exception 'Not allowed' using errcode='42501'; end if;
 return coalesce((select revision from aedrova_private.context_revisions where channel_id=p_channel),0);
end $$;
revoke all on function public.context_revision(uuid) from public,anon;
grant execute on function public.context_revision(uuid) to authenticated;
commit;
