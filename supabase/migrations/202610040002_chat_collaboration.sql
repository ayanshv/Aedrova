begin;
alter table public.channels add column topic text not null default '' check(length(topic)<=240);
alter table public.channels add column description text not null default '' check(length(description)<=2000);
alter table public.channels add column posting text not null default 'members' check(posting in ('members','admins'));
alter table public.channels drop constraint channels_kind_check;
alter table public.channels add constraint channels_kind_check check(kind in ('channel','dm','group_dm'));
alter table public.channels drop constraint dm_participants;
alter table public.channels add constraint dm_participants check(
 (kind in ('channel','group_dm') and dm_low is null and dm_high is null and (kind<>'group_dm' or private)) or
 (kind='dm' and private and dm_low is not null and dm_high is not null and dm_low<dm_high));
alter table public.messages add column edited_at timestamptz;
create table public.chat_profiles(user_id uuid primary key references auth.users on delete cascade,
 status text not null default '' check(length(status)<=120),
 availability text not null default 'online' check(availability in ('online','away','busy')),
 last_seen timestamptz not null default now());
create table public.chat_marks(message_id uuid references public.messages on delete cascade,
 user_id uuid references auth.users on delete cascade, kind text check(kind in ('saved','pinned')),
 created_at timestamptz not null default now(), primary key(message_id,user_id,kind));
create table public.chat_typing(channel_id uuid references public.channels on delete cascade,
 user_id uuid references auth.users on delete cascade, expires_at timestamptz not null,
 primary key(channel_id,user_id));
create table public.chat_preferences(channel_id uuid references public.channels on delete cascade,
 user_id uuid references auth.users on delete cascade, mode text not null check(mode in ('all','mentions','none')),
 primary key(channel_id,user_id));
create table public.chat_notifications(id bigint generated always as identity primary key,
 user_id uuid not null references auth.users on delete cascade,
 message_id uuid not null references public.messages on delete cascade,
 kind text not null check(kind in ('mention','dm','reply','channel')), created_at timestamptz not null default now(),
 seen_at timestamptz, unique(user_id,message_id));
create index chat_notifications_user on public.chat_notifications(user_id,id desc);
create index chat_marks_user on public.chat_marks(user_id,kind);
create index chat_typing_expiry on public.chat_typing(expires_at);
-- All mutations use user-JWT RPCs; read policies continue to enforce channel access.
alter table public.chat_profiles enable row level security;
alter table public.chat_marks enable row level security;
alter table public.chat_typing enable row level security;
alter table public.chat_preferences enable row level security;
alter table public.chat_notifications enable row level security;
revoke all on public.chat_profiles,public.chat_marks,public.chat_typing,public.chat_preferences,public.chat_notifications from public,anon,authenticated;
grant select on public.chat_profiles,public.chat_marks,public.chat_typing,public.chat_preferences,public.chat_notifications to authenticated;
create policy profiles_visible on public.chat_profiles for select to authenticated using(user_id=auth.uid() or exists(
 select 1 from public.workspace_members m where m.user_id=chat_profiles.user_id
 and aedrova_private.member_role(m.workspace_id) in ('owner','admin','member')));
create policy marks_visible on public.chat_marks for select to authenticated using((user_id=auth.uid() or kind='pinned')
 and exists(select 1 from public.messages m where m.id=message_id and aedrova_private.can_read_channel(m.channel_id)));
create policy typing_visible on public.chat_typing for select to authenticated using(aedrova_private.can_read_channel(channel_id));
create policy preferences_visible on public.chat_preferences for select to authenticated using(user_id=auth.uid() and aedrova_private.can_read_channel(channel_id));
create policy notifications_visible on public.chat_notifications for select to authenticated using(user_id=auth.uid() and exists(
 select 1 from public.messages m where m.id=message_id and aedrova_private.can_read_channel(m.channel_id) and m.unsent_at is null));
-- Enforce channel posting policy for EVERY existing entry point, including uploads/replies.
create function aedrova_private.check_posting() returns trigger language plpgsql security definer set search_path='' as $$
begin
 if (select posting from public.channels where id=new.channel_id)='admins'
 and coalesce(aedrova_private.member_role((select workspace_id from public.channels where id=new.channel_id)),'') not in ('owner','admin')
 then raise exception 'Only channel administrators can post here' using errcode='42501'; end if;
 return new;
end $$;
create trigger channel_posting before insert on public.messages for each row execute function aedrova_private.check_posting();
create function aedrova_private.chat_notify() returns trigger language plpgsql security definer set search_path='' as $$
declare person record; category text; mode text;
begin
 for person in select wm.user_id from public.workspace_members wm join public.channels c on c.workspace_id=wm.workspace_id
 where c.id=new.channel_id and wm.user_id<>new.sender_id and wm.role in ('owner','admin','member')
 and (not c.private or exists(select 1 from public.channel_members cm where cm.channel_id=c.id and cm.user_id=wm.user_id)) loop
 category:=null;
 select pref.mode into mode from public.chat_preferences pref where pref.channel_id=new.channel_id and pref.user_id=person.user_id;
 if coalesce(mode,'mentions')='none' then continue; end if;
 if position('<@'||person.user_id::text||'|' in new.body)>0 or new.body ~ '(^|[[:space:]])@(channel|everyone)([[:space:][:punct:]]|$)' then category:='mention';
 elsif (select kind from public.channels where id=new.channel_id) in ('dm','group_dm') then category:='dm';
 elsif new.parent_id is not null and exists(select 1 from public.messages m where (m.id=new.parent_id or m.parent_id=new.parent_id) and m.sender_id=person.user_id) then category:='reply';
 elsif mode='all' then category:='channel'; end if;
 if category is not null then insert into public.chat_notifications(user_id,message_id,kind) values(person.user_id,new.id,category) on conflict do nothing; end if;
 end loop;
 return new;
end $$;
create trigger chat_notifications_insert after insert on public.messages for each row execute function aedrova_private.chat_notify();
create function public.chat_action(p_action text,p_data jsonb default '{}'::jsonb) returns jsonb
language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); c uuid; w uuid; m public.messages; target uuid; members uuid[]; item uuid; actor_role text;
begin
 if length(p_data::text)>24000 then raise exception 'Request too large' using errcode='22023'; end if;
 perform aedrova_private.check_user_budget('chat-'||coalesce(p_action,''),case when p_action in ('typing','heartbeat') then 40 else 120 end,60);
 if p_action='profile' then
 if length(coalesce(p_data->>'status',''))>120 or coalesce(p_data->>'availability','online') not in ('online','away','busy') then raise exception 'Invalid status' using errcode='22023'; end if;
 insert into public.chat_profiles values(u,coalesce(p_data->>'status',''),coalesce(p_data->>'availability','online'),now())
 on conflict(user_id) do update set status=excluded.status,availability=excluded.availability,last_seen=now(); return '{}'::jsonb;
 elsif p_action='heartbeat' then
 insert into public.chat_profiles(user_id,last_seen) values(u,now()) on conflict(user_id) do update set last_seen=now(); return '{}'::jsonb;
 elsif p_action='group_dm' then
 w:=(p_data->>'workspace')::uuid;
 perform 1 from public.workspaces where id=w for update;
 if coalesce(aedrova_private.member_role(w),'') not in ('owner','admin','member') then raise exception 'Not allowed' using errcode='42501'; end if;
 select array_agg(distinct value::uuid) into members from jsonb_array_elements_text(p_data->'members') where value::uuid<>u;
 if coalesce(cardinality(members),0)<2 or cardinality(members)>20 then raise exception 'Choose 2–20 teammates' using errcode='22023'; end if;
 members:=array_append(members,u);
 foreach item in array members loop
 if not exists(select 1 from public.workspace_members where workspace_id=w and user_id=item and role in ('owner','admin','member')) then raise exception 'Member unavailable' using errcode='42501'; end if;
 end loop;
 c:=coalesce((p_data->>'id')::uuid,gen_random_uuid());
 if exists(select 1 from public.channels where id=c) then
 if not exists(select 1 from public.channels where id=c and workspace_id=w and kind='group_dm') or not aedrova_private.can_read_channel(c)
 or exists(select 1 from public.channel_members where channel_id=c and not(user_id=any(members)))
 or (select count(*) from public.channel_members where channel_id=c)<>(select count(distinct x) from unnest(members) x) then raise exception 'Conversation identity conflict' using errcode='42501'; end if;
 return jsonb_build_object('channel',c); end if;
 insert into public.channels(id,workspace_id,name,private,kind) values(c,w,'group-'||c::text,true,'group_dm');
 insert into public.channel_members select w,c,x from unnest(members) x on conflict do nothing;
 return jsonb_build_object('channel',c);
 end if;
 if p_data ? 'message' then
 select * into m from public.messages where id=(p_data->>'message')::uuid; c:=m.channel_id;
 else c:=(p_data->>'channel')::uuid; end if;
 select workspace_id into w from public.channels where id=c;
 perform 1 from public.workspaces where id=w for update;
 if not aedrova_private.can_read_channel(c) or coalesce(aedrova_private.member_role(w),'') not in ('owner','admin','member') then raise exception 'Not allowed' using errcode='42501'; end if;
 actor_role:=aedrova_private.member_role(w);
 if p_data ? 'message' then
 select * into m from public.messages where id=m.id for update;
 if m.unsent_at is not null then raise exception 'Message unavailable' using errcode='42501'; end if;
 end if;
 if p_action='edit' then
 if m.sender_id is distinct from u then raise exception 'Only the sender can edit' using errcode='42501'; end if;
 if length(btrim(coalesce(p_data->>'body',''))) not between 1 and 10000 then raise exception 'Invalid message' using errcode='22023'; end if;
 if m.body is distinct from btrim(p_data->>'body') then
 delete from public.context_decisions where message_id=m.id;
 update public.messages set body=btrim(p_data->>'body'),edited_at=clock_timestamp() where id=m.id;
 end if;
 elsif p_action in ('saved','pinned') then
 if p_action='pinned' and actor_role not in ('owner','admin') then raise exception 'Only administrators can pin' using errcode='42501'; end if;
 if (p_data->>'present')::boolean then insert into public.chat_marks(message_id,user_id,kind) values(m.id,u,p_action) on conflict do nothing;
 elsif p_action='pinned' then delete from public.chat_marks where message_id=m.id and kind='pinned';
 else delete from public.chat_marks where message_id=m.id and user_id=u and kind=p_action; end if;
 elsif p_action='forward' then
 target:=(p_data->>'destination')::uuid;
 if not exists(select 1 from public.channels where id=target and workspace_id=w) then raise exception 'Destination unavailable' using errcode='42501'; end if;
 perform public.send_message((p_data->>'id')::uuid,target,'Forwarded message'||E'\n\n'||m.body);
 elsif p_action='channel' then
 if actor_role not in ('owner','admin') or (select kind from public.channels where id=c)<>'channel' then raise exception 'Only channel administrators can configure' using errcode='42501'; end if;
 update public.channels set topic=coalesce(p_data->>'topic',''),description=coalesce(p_data->>'description',''),posting=coalesce(p_data->>'posting','members') where id=c;
 elsif p_action='notification_mode' then
 insert into public.chat_preferences values(c,u,p_data->>'mode') on conflict(channel_id,user_id) do update set mode=excluded.mode;
 elsif p_action='typing' then
 if (p_data->>'active')::boolean then insert into public.chat_typing values(c,u,now()+interval '8 seconds') on conflict(channel_id,user_id) do update set expires_at=excluded.expires_at;
 else delete from public.chat_typing where channel_id=c and user_id=u; end if;
 elsif p_action='unread' then
 insert into public.channel_reads values(c,u,greatest(0,m.sequence-1)) on conflict(channel_id,user_id) do update set last_sequence=excluded.last_sequence;
 elsif p_action='seen' then
 update public.chat_notifications n set seen_at=now() where n.user_id=u and n.message_id=m.id;
 else raise exception 'Unsupported action' using errcode='22023'; end if;
 return '{}'::jsonb;
end $$;
create function public.chat_inventory(p_workspace uuid,p_query text default '',p_section text default 'search',p_channel uuid default null)
returns jsonb language plpgsql stable security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); result jsonb; q text:=left(coalesce(p_query,''),200);
begin
 if coalesce(aedrova_private.member_role(p_workspace),'') not in ('owner','admin','member') then raise exception 'Not allowed' using errcode='42501'; end if;
 if p_channel is not null and not exists(select 1 from public.channels where id=p_channel and workspace_id=p_workspace and aedrova_private.can_read_channel(id)) then raise exception 'Not allowed' using errcode='42501'; end if;
 select coalesce(jsonb_agg(to_jsonb(x)),'[]') into result from (
 select m.id,m.channel_id,m.sender_id,m.parent_id,m.body,m.created_at,m.sequence,m.edited_at,c.name as channel,
 coalesce(nullif(left(a.raw_user_meta_data->>'full_name',80),''),'Teammate') as author,
 exists(select 1 from public.chat_marks b where b.message_id=m.id and b.user_id=u and b.kind='saved') as saved,
 exists(select 1 from public.chat_marks b where b.message_id=m.id and b.kind='pinned') as pinned,
 (select id from public.attachments f where f.message_id=m.id) as attachment_id,
 (select filename from public.attachments f where f.message_id=m.id) as filename,
 (select kind from public.chat_notifications n where n.message_id=m.id and n.user_id=u) as notification,
 (select seen_at from public.chat_notifications n where n.message_id=m.id and n.user_id=u) as seen_at
 from public.messages m join public.channels c on c.id=m.channel_id join auth.users a on a.id=m.sender_id
 where c.workspace_id=p_workspace and aedrova_private.can_read_channel(c.id) and m.unsent_at is null
 and (p_channel is null or c.id=p_channel)
 and case p_section
 when 'saved' then exists(select 1 from public.chat_marks b where b.message_id=m.id and b.user_id=u and b.kind='saved')
 when 'pinned' then exists(select 1 from public.chat_marks b where b.message_id=m.id and b.kind='pinned')
 when 'activity' then exists(select 1 from public.chat_notifications n where n.message_id=m.id and n.user_id=u)
 when 'files' then exists(select 1 from public.attachments f where f.message_id=m.id and position(lower(q) in lower(f.filename))>0)
 when 'recent' then true
 else position(lower(q) in lower(m.body))>0 or exists(select 1 from public.attachments f where f.message_id=m.id and position(lower(q) in lower(f.filename))>0) end
 order by m.sequence desc limit 100) x;
 return jsonb_build_object('workspace_id',p_workspace,'messages',result,
 'channels',coalesce((select jsonb_agg(to_jsonb(c)||jsonb_build_object('display_name',case when c.kind='group_dm' then (select string_agg(coalesce(nullif(left(a.raw_user_meta_data->>'full_name',40),''),'Teammate'),', ' order by cm.user_id) from public.channel_members cm join auth.users a on a.id=cm.user_id where cm.channel_id=c.id and cm.user_id<>u) else c.name end)) from public.channels c where c.workspace_id=p_workspace and aedrova_private.can_read_channel(c.id) and position(lower(q) in lower(c.name))>0),'[]'),
 'people',coalesce((select jsonb_agg(jsonb_build_object('user_id',m.user_id,'display_name',coalesce(nullif(left(a.raw_user_meta_data->>'full_name',80),''),'Teammate'),'role',m.role,
 'status',coalesce(p.status,''),'availability',case when p.last_seen>now()-interval '90 seconds' then coalesce(p.availability,'online') else 'offline' end))
 from public.workspace_members m join auth.users a on a.id=m.user_id left join public.chat_profiles p on p.user_id=m.user_id
 where m.workspace_id=p_workspace and m.role in ('owner','admin','member') and position(lower(q) in lower(coalesce(a.raw_user_meta_data->>'full_name','Teammate')))>0
 and (p_channel is null or not (select private from public.channels where id=p_channel) or exists(select 1 from public.channel_members cm where cm.channel_id=p_channel and cm.user_id=m.user_id))),'[]'),
 'typing',coalesce((select jsonb_agg(jsonb_build_object('channel_id',t.channel_id,'user_id',t.user_id)) from public.chat_typing t join public.channels c on c.id=t.channel_id where c.workspace_id=p_workspace and aedrova_private.can_read_channel(c.id) and t.expires_at>now() and t.user_id<>u),'[]'),
 'preferences',coalesce((select jsonb_agg(to_jsonb(p)) from public.chat_preferences p join public.channels c on c.id=p.channel_id where c.workspace_id=p_workspace and p.user_id=u and aedrova_private.can_read_channel(c.id)),'[]'),
 'unseen',(select count(*) from public.chat_notifications n join public.messages m on m.id=n.message_id join public.channels c on c.id=m.channel_id where n.user_id=u and c.workspace_id=p_workspace and aedrova_private.can_read_channel(c.id) and m.unsent_at is null and n.seen_at is null));
end $$;
-- Update metadata reconciliation so edits/pins/saves refresh even outside the newest sequence.
create or replace function public.message_interactions(p_ids uuid[]) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); result jsonb;
begin
 if coalesce(cardinality(p_ids),0)>100 then raise exception 'Too many messages' using errcode='22023'; end if;
 select coalesce(jsonb_agg(jsonb_build_object('id',m.id,'body',m.body,'unsent_at',m.unsent_at,'edited_at',m.edited_at,
 'saved',exists(select 1 from public.chat_marks s where s.message_id=m.id and s.user_id=u and s.kind='saved'),
 'pinned',exists(select 1 from public.chat_marks s where s.message_id=m.id and s.kind='pinned'),
 'reactions',coalesce((select jsonb_agg(to_jsonb(r)) from (select emoji,count(*) as count,bool_or(user_id=u) as mine from public.message_reactions where message_id=m.id group by emoji order by emoji) r),'[]'))) ,'[]') into result
 from public.messages m where m.id=any(p_ids) and aedrova_private.can_read_channel(m.channel_id);
 return result;
end $$;
revoke all on function public.chat_action(text,jsonb),public.chat_inventory(uuid,text,text,uuid),aedrova_private.check_posting(),aedrova_private.chat_notify() from public,anon;
grant execute on function public.chat_action(text,jsonb),public.chat_inventory(uuid,text,text,uuid) to authenticated;
commit;
