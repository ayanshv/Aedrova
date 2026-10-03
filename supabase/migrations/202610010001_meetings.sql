begin;
-- Meetings share channel visibility; joining never consents to transcription or AI reuse.
create table public.meetings (
 id uuid primary key default gen_random_uuid(),
 channel_id uuid not null references public.channels(id) on delete cascade,
 started_by uuid not null references auth.users(id),
 title text not null check(char_length(title) between 1 and 120),
 started_at timestamptz not null default clock_timestamp(),
 ended_at timestamptz,
 revision bigint not null default 1
);
create unique index one_open_meeting_per_channel on public.meetings(channel_id)
 where ended_at is null;
create table public.meeting_participants (
 meeting_id uuid not null references public.meetings(id) on delete cascade,
 user_id uuid not null references auth.users(id) on delete cascade,
 present_until timestamptz not null,
 transcription boolean not null default false,
 ai_context boolean not null default false,
 primary key(meeting_id,user_id),
 check(not ai_context or transcription)
);
alter table public.meetings enable row level security;
alter table public.meeting_participants enable row level security;
revoke all on public.meetings,public.meeting_participants from public,anon,authenticated;
grant select on public.meetings,public.meeting_participants to authenticated;
create policy meetings_read on public.meetings for select to authenticated
 using(aedrova_private.can_read_channel(channel_id));
create policy meeting_participants_read on public.meeting_participants for select to authenticated
 using(exists(select 1 from public.meetings m where m.id=meeting_id
 and aedrova_private.can_read_channel(m.channel_id)));

create function aedrova_private.lock_meeting(p_meeting uuid) returns public.meetings
language plpgsql security definer set search_path='' as $$
declare m public.meetings;
begin
 perform aedrova_private.require_user();
 select * into m from public.meetings where id=p_meeting for update;
 if m.id is null or not aedrova_private.can_read_channel(m.channel_id) then
 raise exception 'Meeting access is unavailable' using errcode='42501'; end if;
 return m;
end $$;
revoke all on function aedrova_private.lock_meeting(uuid) from public,anon,authenticated;

create function public.start_meeting(p_channel uuid,p_title text) returns uuid
language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); w uuid; result uuid;
begin
 select workspace_id into w from public.channels where id=p_channel;
 perform 1 from public.channels where id=p_channel for update;
 if not aedrova_private.can_read_channel(p_channel)
 or coalesce(aedrova_private.member_role(w),'') not in ('owner','admin','member') then
 raise exception 'Not allowed' using errcode='42501'; end if;
 if char_length(trim(p_title)) not between 1 and 120 then
 raise exception 'Meeting title must contain 1–120 characters'; end if;
 select id into result from public.meetings where channel_id=p_channel and ended_at is null;
 if result is null then
 insert into public.meetings(channel_id,started_by,title) values(p_channel,u,trim(p_title))
 returning id into result;
 end if;
 return result;
end $$;

create function public.join_meeting(p_meeting uuid) returns jsonb
language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); m public.meetings; w uuid;
begin
 m:=aedrova_private.lock_meeting(p_meeting);
 if m.ended_at is not null then raise exception 'Meeting has ended'; end if;
 select workspace_id into w from public.channels where id=m.channel_id;
 -- A fresh join resets the joining participant's choices. It is never implicit consent.
 insert into public.meeting_participants(meeting_id,user_id,present_until)
 values(m.id,u,clock_timestamp()+interval '60 seconds')
 on conflict(meeting_id,user_id) do update
 set present_until=excluded.present_until,transcription=false,ai_context=false;
 update public.meetings set revision=revision+1 where id=m.id;
 return jsonb_build_object('meeting_id',m.id,'channel_id',m.channel_id,'workspace_id',w,
 'user_id',u,'room_name','aedrova-'||w||'-'||m.channel_id||'-'||m.id);
end $$;

create function public.meeting_presence(p_meeting uuid) returns void
language plpgsql security definer set search_path='' as $$
declare m public.meetings;
begin
 m:=aedrova_private.lock_meeting(p_meeting);
 if m.ended_at is not null then raise exception 'Meeting has ended'; end if;
 -- Expired presence needs a new join and new consent; heartbeats cannot resurrect it.
 update public.meeting_participants set present_until=clock_timestamp()+interval '60 seconds'
 where meeting_id=m.id and user_id=auth.uid() and present_until>clock_timestamp();
 if not found then raise exception 'Rejoin the meeting' using errcode='42501'; end if;
end $$;

create function public.set_meeting_consent(p_meeting uuid,p_transcription boolean,p_ai boolean)
returns void language plpgsql security definer set search_path='' as $$
declare m public.meetings;
begin
 m:=aedrova_private.lock_meeting(p_meeting);
 if m.ended_at is not null then raise exception 'Meeting has ended'; end if;
 if p_transcription is null or p_ai is null or (p_ai and not p_transcription) then
 raise exception 'AI reuse requires transcription consent'; end if;
 update public.meeting_participants set transcription=p_transcription,ai_context=p_ai
 where meeting_id=m.id and user_id=auth.uid() and present_until>clock_timestamp();
 if not found then raise exception 'Join before choosing consent' using errcode='42501'; end if;
 update public.meetings set revision=revision+1 where id=m.id;
end $$;

create function public.leave_meeting(p_meeting uuid) returns void
language plpgsql security definer set search_path='' as $$
declare m public.meetings;
begin
 m:=aedrova_private.lock_meeting(p_meeting);
 update public.meeting_participants set present_until=clock_timestamp(),
 transcription=false,ai_context=false where meeting_id=m.id and user_id=auth.uid();
 update public.meetings set revision=revision+1 where id=m.id;
end $$;

create function public.end_meeting(p_meeting uuid) returns void
language plpgsql security definer set search_path='' as $$
declare m public.meetings; w uuid;
begin
 m:=aedrova_private.lock_meeting(p_meeting);
 select workspace_id into w from public.channels where id=m.channel_id;
 if m.started_by<>auth.uid() and coalesce(aedrova_private.member_role(w),'')
 not in ('owner','admin') then raise exception 'Host access required' using errcode='42501'; end if;
 update public.meetings set ended_at=coalesce(ended_at,clock_timestamp()),revision=revision+1
 where id=m.id;
 update public.meeting_participants set present_until=clock_timestamp(),
 transcription=false,ai_context=false where meeting_id=m.id;
end $$;

create function public.meeting_consent_snapshot(p_meeting uuid) returns jsonb
language plpgsql security definer set search_path='' as $$
declare m public.meetings; participants jsonb;
begin
 m:=aedrova_private.lock_meeting(p_meeting);
 select coalesce(jsonb_agg(jsonb_build_object('user_id',p.user_id,
 'transcription',p.transcription,'ai_context',p.ai_context) order by p.user_id),'[]'::jsonb)
 into participants from public.meeting_participants p
 where p.meeting_id=m.id and p.present_until>clock_timestamp();
 return jsonb_build_object('id',m.id,'revision',m.revision,'ended',m.ended_at is not null,
 'participants',participants);
end $$;

revoke all on function public.start_meeting(uuid,text),public.join_meeting(uuid),
 public.meeting_presence(uuid),public.set_meeting_consent(uuid,boolean,boolean),
 public.leave_meeting(uuid),public.end_meeting(uuid),public.meeting_consent_snapshot(uuid)
 from public,anon;
grant execute on function public.start_meeting(uuid,text),public.join_meeting(uuid),
 public.meeting_presence(uuid),public.set_meeting_consent(uuid,boolean,boolean),
 public.leave_meeting(uuid),public.end_meeting(uuid),public.meeting_consent_snapshot(uuid)
 to authenticated;
commit;
