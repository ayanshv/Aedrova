begin;
alter table public.chat_profiles add column display_name text check(length(btrim(display_name)) between 1 and 80);
alter table public.chat_profiles add column username text check(username ~ '^[a-z0-9][a-z0-9_]{2,31}$');
alter table public.chat_profiles add column bio text not null default '' check(length(bio)<=280);
alter table public.chat_profiles add column title text not null default '' check(length(title)<=80);
alter table public.chat_profiles add column status_emoji text not null default '';
alter table public.chat_profiles add column avatar_path text;
alter table public.chat_profiles add column profile_completed boolean not null default false;
create unique index chat_username_unique on public.chat_profiles(username) where username is not null;
-- Avatars are private, immutable PNGs. No public or signed URL is persisted.
insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
 values('aedrova-avatars','aedrova-avatars',false,2097152,array['image/png']);
create function aedrova_private.can_read_avatar(path text) returns boolean language sql stable security definer set search_path='' as $$
 select exists(select 1 from public.chat_profiles p where p.avatar_path=path and (p.user_id=auth.uid() or exists(
 select 1 from public.workspace_members other join public.workspace_members mine on mine.workspace_id=other.workspace_id
 where other.user_id=p.user_id and mine.user_id=auth.uid() and other.role in ('owner','admin','member') and mine.role in ('owner','admin','member')
 and aedrova_private.member_role(mine.workspace_id) is not null)))
$$;
create policy avatar_read on storage.objects for select to authenticated using(bucket_id='aedrova-avatars' and aedrova_private.can_read_avatar(name));
create policy avatar_upload on storage.objects for insert to authenticated with check(bucket_id='aedrova-avatars'
 and name ~ '^[a-f0-9-]{36}/[a-f0-9-]{36}\.png$' and split_part(name,'/',1)=auth.uid()::text);
create policy avatar_remove on storage.objects for delete to authenticated using(bucket_id='aedrova-avatars' and split_part(name,'/',1)=auth.uid()::text);
create function public.my_chat_profile() returns jsonb language plpgsql stable security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); result jsonb;
begin
 select to_jsonb(p) into result from public.chat_profiles p where p.user_id=u;
 return coalesce(result,jsonb_build_object('user_id',u,'profile_completed',false));
end $$;
create function public.save_chat_profile(p_data jsonb) returns jsonb language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); old public.chat_profiles; merged jsonb; avatar text; chosen_emoji text;
begin
 perform aedrova_private.check_user_budget('profile-save',30,60);
 if length(p_data::text)>8000 then raise exception 'Profile too large' using errcode='22023'; end if;
 -- Serialize the user's avatar/profile updates without acquiring workspace locks.
 perform 1 from auth.users where id=u for update;
 select * into old from public.chat_profiles where user_id=u;
 merged:=coalesce(to_jsonb(old),'{}')||p_data;
 avatar:=nullif(merged->>'avatar_path',''); chosen_emoji:=coalesce(merged->>'status_emoji','');
 if chosen_emoji<>'' and not exists(select 1 from aedrova_private.reaction_emoji e where e.emoji=chosen_emoji)
 then raise exception 'Choose a supported status emoji' using errcode='22023'; end if;
 if avatar is not null and (avatar !~ '^[a-f0-9-]{36}/[a-f0-9-]{36}\.png$' or split_part(avatar,'/',1)<>u::text
 or not exists(select 1 from storage.objects where bucket_id='aedrova-avatars' and name=avatar and coalesce((metadata->>'size')::bigint,0) between 1 and 2097152))
 then raise exception 'Avatar unavailable' using errcode='42501'; end if;
 if (merged->>'profile_completed')::boolean is true and (nullif(merged->>'username','') is null or nullif(btrim(merged->>'display_name'),'') is null)
 then raise exception 'Choose a username' using errcode='22023'; end if;
 insert into public.chat_profiles(user_id,display_name,username,bio,title,status,status_emoji,availability,last_seen,avatar_path,profile_completed)
 values(u,btrim(merged->>'display_name'),lower(nullif(btrim(merged->>'username'),'')),coalesce(merged->>'bio',''),coalesce(merged->>'title',''),
 coalesce(merged->>'status',''),chosen_emoji,coalesce(merged->>'availability','online'),now(),avatar,coalesce((merged->>'profile_completed')::boolean,false))
 on conflict(user_id) do update set display_name=excluded.display_name,username=excluded.username,bio=excluded.bio,title=excluded.title,
 status=excluded.status,status_emoji=excluded.status_emoji,availability=excluded.availability,last_seen=now(),avatar_path=excluded.avatar_path,profile_completed=excluded.profile_completed;
 return public.my_chat_profile();
exception when unique_violation then raise exception 'That username is already taken. Choose another.' using errcode='22023';
end $$;
create or replace function public.team_directory() returns table(workspace_id uuid,user_id uuid,display_name text)
language sql stable security definer set search_path='' as $$
 select m.workspace_id,m.user_id,coalesce(p.display_name,nullif(left(a.raw_user_meta_data->>'full_name',80),''),'Teammate '||left(m.user_id::text,6))
 from public.workspace_members m join auth.users a on a.id=m.user_id left join public.chat_profiles p on p.user_id=m.user_id
 where aedrova_private.member_role(m.workspace_id) in ('owner','admin','member') and m.role in ('owner','admin','member')
$$;
-- Keep the existing inventory contract and extend the people objects only.
alter function public.chat_inventory(uuid,text,text,uuid) rename to chat_inventory_base;
revoke all on function public.chat_inventory_base(uuid,text,text,uuid) from public,anon,authenticated;
create function public.chat_inventory(p_workspace uuid,p_query text default '',p_section text default 'search',p_channel uuid default null)
returns jsonb language plpgsql stable security definer set search_path='' as $$
declare result jsonb; people jsonb; u uuid:=aedrova_private.require_user();
begin
 result:=public.chat_inventory_base(p_workspace,p_query,p_section,p_channel);
 -- Name/username matches must use custom profile data, including people omitted by the old Google-name search.
 select coalesce(jsonb_agg(jsonb_build_object('user_id',m.user_id,'display_name',coalesce(p.display_name,nullif(left(a.raw_user_meta_data->>'full_name',80),''),'Teammate'),
 'role',m.role,'username',p.username,'bio',coalesce(p.bio,''),'title',coalesce(p.title,''),'status',coalesce(p.status,''),'status_emoji',coalesce(p.status_emoji,''),'avatar_path',p.avatar_path,
 'availability',case when p.last_seen>now()-interval '90 seconds' then p.availability else 'offline' end)),'[]') into people
 from public.workspace_members m join auth.users a on a.id=m.user_id left join public.chat_profiles p on p.user_id=m.user_id
 where m.workspace_id=p_workspace and m.role in ('owner','admin','member')
 and position(lower(left(coalesce(p_query,''),200)) in lower(coalesce(p.display_name,a.raw_user_meta_data->>'full_name','Teammate')||' '||coalesce(p.username,'')))>0
 and (p_channel is null or not (select private from public.channels where id=p_channel) or exists(select 1 from public.channel_members cm where cm.channel_id=p_channel and cm.user_id=m.user_id));
 return jsonb_set(result,'{people}',people);
end $$;
revoke all on function public.my_chat_profile(),public.save_chat_profile(jsonb),public.chat_inventory(uuid,text,text,uuid),aedrova_private.can_read_avatar(text) from public,anon;
grant execute on function public.my_chat_profile(),public.save_chat_profile(jsonb),public.chat_inventory(uuid,text,text,uuid),aedrova_private.can_read_avatar(text) to authenticated;
create or replace function public.chat_action(p_action text,p_data jsonb default '{}'::jsonb) returns jsonb
language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); c uuid; w uuid; m public.messages; target uuid; members uuid[]; item uuid; actor_role text;
begin
 if length(p_data::text)>24000 then raise exception 'Request too large' using errcode='22023'; end if;
 perform aedrova_private.check_user_budget('chat-'||coalesce(p_action,''),case when p_action in ('typing','heartbeat') then 40 else 120 end,60);
 if p_action='profile' then
 if length(coalesce(p_data->>'status',''))>120 or coalesce(p_data->>'availability','online') not in ('online','away','busy') then raise exception 'Invalid status' using errcode='22023'; end if;
 insert into public.chat_profiles(user_id,status,availability,last_seen) values(u,coalesce(p_data->>'status',''),coalesce(p_data->>'availability','online'),now())
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
commit;
