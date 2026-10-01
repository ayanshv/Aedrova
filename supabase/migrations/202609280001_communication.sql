begin;
-- Direct conversations use the existing channel access boundary, with immutable participants.
alter table public.channels add column kind text not null default 'channel'
 check(kind in ('channel','dm'));
alter table public.channels add column dm_low uuid references auth.users;
alter table public.channels add column dm_high uuid references auth.users;
alter table public.channels add constraint dm_participants check(
 (kind='channel' and dm_low is null and dm_high is null) or
 (kind='dm' and private and dm_low is not null and dm_high is not null and dm_low<dm_high));
create unique index direct_pair on public.channels(workspace_id,dm_low,dm_high) where kind='dm';
create function public.start_direct_message(p_workspace uuid,p_user uuid) returns uuid
language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); c uuid;
begin
 perform 1 from public.workspaces where id=p_workspace for update;
 if u=p_user or coalesce(aedrova_private.member_role(p_workspace),'') not in ('owner','admin','member')
 or not exists(select 1 from public.workspace_members where workspace_id=p_workspace
 and user_id=p_user and role in ('owner','admin','member'))
 then raise exception 'Recipient unavailable' using errcode='42501'; end if;
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
create or replace function public.set_channel_member(p_channel uuid,p_user uuid,p_allowed boolean)
returns void language plpgsql security definer set search_path='' as $$
declare w uuid;
begin
 perform aedrova_private.require_user();
 select workspace_id into w from public.channels where id=p_channel and kind='channel';
 perform 1 from public.workspaces where id=w for update;
 if coalesce(aedrova_private.member_role(w),'') not in ('owner','admin')
 or not aedrova_private.can_read_channel(p_channel)
 then raise exception 'Not allowed' using errcode='42501'; end if;
 if p_allowed then
 insert into public.channel_members values(w,p_channel,p_user) on conflict do nothing;
 else delete from public.channel_members where channel_id=p_channel and user_id=p_user; end if;
end $$;
create function public.team_directory()
returns table(workspace_id uuid,user_id uuid,display_name text)
language sql stable security definer set search_path='' as $$
 select m.workspace_id,m.user_id,
 coalesce(nullif(left(u.raw_user_meta_data->>'full_name',80),''),'Teammate '||left(m.user_id::text,6))
 from public.workspace_members m join auth.users u on u.id=m.user_id
 where aedrova_private.member_role(m.workspace_id) in ('owner','admin','member')
 and m.role in ('owner','admin','member')
$$;
-- Monotonic per-channel cursor. All message writes acquire the workspace lock first.
alter table public.messages add column sequence bigint;
with numbered as (select id,row_number() over(order by created_at,id) as n from public.messages)
update public.messages m set sequence=numbered.n from numbered where m.id=numbered.id;
alter table public.messages alter column sequence set not null;
alter table public.messages alter column sequence add generated always as identity;
select setval(pg_get_serial_sequence('public.messages','sequence'),
 greatest(coalesce((select max(sequence) from public.messages),0),1),
 exists(select 1 from public.messages));
create unique index message_sequence on public.messages(sequence);
create index message_channel_sequence on public.messages(channel_id,sequence desc);
create table public.channel_reads (
 channel_id uuid not null references public.channels on delete cascade,
 user_id uuid not null references auth.users on delete cascade,
 last_sequence bigint not null default 0 check(last_sequence>=0),
 primary key(channel_id,user_id)
);
alter table public.channel_reads enable row level security;
revoke all on public.channel_reads from public,anon,authenticated;
grant select on public.channel_reads to authenticated;
create policy read_own_cursor on public.channel_reads for select to authenticated
 using(user_id=auth.uid() and aedrova_private.can_read_channel(channel_id));
create function public.mark_channel_read(p_channel uuid,p_sequence bigint) returns void
language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); top bigint;
begin
 if not aedrova_private.can_read_channel(p_channel)
 then raise exception 'Not allowed' using errcode='42501'; end if;
 select coalesce(max(sequence),0) into top from public.messages where channel_id=p_channel;
 if p_sequence is null or p_sequence<0 or p_sequence>top
 then raise exception 'Invalid cursor' using errcode='22023'; end if;
 insert into public.channel_reads values(p_channel,u,p_sequence)
 on conflict(channel_id,user_id) do update set last_sequence=greatest(channel_reads.last_sequence,excluded.last_sequence);
end $$;
create function public.unread_counts() returns table(channel_id uuid,unread bigint)
language sql stable security definer set search_path='' as $$
 select c.id,count(m.id) from public.channels c
 left join public.channel_reads r on r.channel_id=c.id and r.user_id=auth.uid()
 left join public.messages m on m.channel_id=c.id and m.sequence>coalesce(r.last_sequence,0)
 and m.sender_id<>auth.uid()
 where aedrova_private.can_read_channel(c.id) group by c.id
$$;
-- Keyset history; callers can separately page replies for a root outside the current window.
create function public.message_page(p_channel uuid,p_before bigint default null,p_after bigint default null,
 p_parent uuid default null,p_threads boolean default false,p_limit integer default 100)
returns setof public.messages language plpgsql stable security definer set search_path='' as $$
begin
 perform aedrova_private.require_user();
 if not aedrova_private.can_read_channel(p_channel)
 then raise exception 'Not allowed' using errcode='42501'; end if;
 if p_after is not null then
 return query select * from public.messages where channel_id=p_channel
 and sequence>p_after and (p_threads or parent_id is not distinct from p_parent)
 order by sequence asc limit greatest(1,least(coalesce(p_limit,100),200));
 else
 return query select * from public.messages where channel_id=p_channel
 and (p_before is null or sequence<p_before) and (p_threads or parent_id is not distinct from p_parent)
 order by sequence desc limit greatest(1,least(coalesce(p_limit,100),200));
 end if;
end $$;
-- Attachments: reserve a unique object path, upload immutable bytes, then atomically publish.
create table public.attachments (
 id uuid primary key,
 channel_id uuid not null references public.channels on delete cascade,
 uploader_id uuid not null references auth.users,
 filename text not null check(length(filename) between 1 and 180 and filename !~ '[/\\\\[:cntrl:]]'),
 byte_size bigint not null check(byte_size between 1 and 10485760),
 sha256 text not null check(sha256 ~ '^[a-f0-9]{64}$'),
 object_path text not null unique,
 message_id uuid unique,
 expires_at timestamptz not null default now()+interval '1 hour',
 foreign key(channel_id,message_id) references public.messages(channel_id,id)
);
alter table public.attachments enable row level security;
revoke all on public.attachments from public,anon,authenticated;
grant select on public.attachments to authenticated;
create policy attachment_read on public.attachments for select to authenticated using(
 aedrova_private.can_read_channel(channel_id) and (message_id is not null or uploader_id=auth.uid()));
create function public.reserve_attachment(p_id uuid,p_channel uuid,p_filename text,p_size bigint,p_sha256 text)
returns text language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); w uuid; a public.attachments;
begin
 select workspace_id into w from public.channels where id=p_channel;
 perform 1 from public.workspaces where id=w for update;
 if not aedrova_private.can_read_channel(p_channel) or
 coalesce(aedrova_private.member_role(w),'') not in ('owner','admin','member')
 then raise exception 'Not allowed' using errcode='42501'; end if;
 select * into a from public.attachments where id=p_id;
 if a.id is not null then
 if a.uploader_id<>u or a.channel_id<>p_channel or a.filename<>p_filename
 or a.byte_size<>p_size or a.sha256<>p_sha256 then
 raise exception 'Attachment identity conflict' using errcode='42501'; end if;
 return a.object_path;
 end if;
 if (select count(*) from public.attachments where uploader_id=u and message_id is null
 and expires_at>now())>=20 then raise exception 'Too many pending uploads' using errcode='54000'; end if;
 insert into public.attachments(id,channel_id,uploader_id,filename,byte_size,sha256,object_path)
 values(p_id,p_channel,u,p_filename,p_size,p_sha256,w::text||'/'||p_channel::text||'/'||p_id::text)
 returning * into a;
 return a.object_path;
end $$;
create function aedrova_private.can_upload_object(path text) returns boolean
language sql stable security definer set search_path='' as $$
 select exists(select 1 from public.attachments a join public.channels c on c.id=a.channel_id
 where a.object_path=path and a.uploader_id=auth.uid() and a.message_id is null and a.expires_at>now()
 and aedrova_private.can_read_channel(c.id)
 and aedrova_private.member_role(c.workspace_id) in ('owner','admin','member'))
$$;
create or replace function aedrova_private.can_read_object(path text) returns boolean
language sql stable security definer set search_path='' as $$
 select exists(select 1 from public.attachments a where a.object_path=path
 and aedrova_private.can_read_channel(a.channel_id)
 and (a.message_id is not null or (a.uploader_id=auth.uid() and a.expires_at>now())))
$$;
update storage.buckets set public=false,file_size_limit=10485760,
 allowed_mime_types=array['application/octet-stream'] where id='aedrova-files';
create policy aedrova_files_upload on storage.objects for insert to authenticated
 with check(bucket_id='aedrova-files' and aedrova_private.can_upload_object(name));
create policy aedrova_files_cancel on storage.objects for delete to authenticated
 using(bucket_id='aedrova-files' and aedrova_private.can_upload_object(name));
create function public.finish_attachment(p_id uuid,p_parent uuid default null) returns uuid
language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); a public.attachments; actual bigint; m uuid;
begin
 select * into a from public.attachments where id=p_id;
 if a.uploader_id is distinct from u or not aedrova_private.can_read_channel(a.channel_id)
 then raise exception 'Attachment unavailable' using errcode='42501'; end if;
 if a.message_id is not null then
 if not exists(select 1 from public.messages where id=a.message_id and parent_id is not distinct from p_parent)
 then raise exception 'Attachment identity conflict' using errcode='42501'; end if;
 return a.message_id; end if;
 if a.expires_at<=now() then raise exception 'Upload expired' using errcode='42501'; end if;
 select (metadata->>'size')::bigint into actual from storage.objects
 where bucket_id='aedrova-files' and name=a.object_path;
 if actual is distinct from a.byte_size then raise exception 'Upload incomplete' using errcode='22023'; end if;
 m:=public.send_message(p_id,a.channel_id,'Shared a file: '||a.filename,p_parent);
 update public.attachments set message_id=m where id=p_id;
 return m;
end $$;
-- Content-free invalidations on personal topics: cached socket authorization cannot leak chat bodies.
create policy aedrova_user_events on realtime.messages for select to authenticated
 using(extension='broadcast' and realtime.topic()='user:'||auth.uid()::text);
create function aedrova_private.notify_message() returns trigger language plpgsql security definer
set search_path='' as $$
declare recipient uuid;
begin
 for recipient in select m.user_id from public.channels c join public.workspace_members m
 on m.workspace_id=c.workspace_id where c.id=new.channel_id
 and ((not c.private and m.role<>'guest') or exists(select 1 from public.channel_members cm
 where cm.channel_id=c.id and cm.user_id=m.user_id)) loop
 perform realtime.send('{}'::jsonb,'refresh','user:'||recipient::text,true);
 end loop;
 return new;
end $$;
create trigger message_notification after insert on public.messages for each row
execute function aedrova_private.notify_message();
-- Also notify on attachment finalization, after its metadata is visible.
create function aedrova_private.notify_attachment() returns trigger language plpgsql security definer
set search_path='' as $$
begin
 perform realtime.send('{}'::jsonb,'refresh','user:'||new.uploader_id::text,true);
 return new;
end $$;
create trigger attachment_notification after update on public.attachments for each row
execute function aedrova_private.notify_attachment();
revoke all on function public.start_direct_message(uuid,uuid),public.team_directory(),
 public.mark_channel_read(uuid,bigint),public.unread_counts(),
 public.message_page(uuid,bigint,bigint,uuid,boolean,integer),
 public.reserve_attachment(uuid,uuid,text,bigint,text),public.finish_attachment(uuid,uuid)
 from public,anon;
grant execute on function public.start_direct_message(uuid,uuid),public.team_directory(),
 public.mark_channel_read(uuid,bigint),public.unread_counts(),
 public.message_page(uuid,bigint,bigint,uuid,boolean,integer),
 public.reserve_attachment(uuid,uuid,text,bigint,text),public.finish_attachment(uuid,uuid)
 to authenticated;
revoke all on function aedrova_private.can_upload_object(text),aedrova_private.notify_message(),
 aedrova_private.notify_attachment() from public,anon;
grant execute on function aedrova_private.can_upload_object(text) to authenticated;
commit;
