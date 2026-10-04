begin;
-- Local M12 foundation. Deploy at M14; no audio recording/provider is enabled by SQL.
create table public.meeting_transcript_segments (
 id uuid primary key,
 meeting_id uuid not null references public.meetings(id) on delete cascade,
 channel_id uuid not null references public.channels(id) on delete cascade,
 speaker_id uuid not null references auth.users(id) on delete cascade,
 consent_revision bigint not null,
 consent_roster uuid[] not null,
 body text not null check(char_length(body) between 1 and 2000),
 offset_ms integer not null check(offset_ms between 0 and 86400000),
 source text not null default 'participant_text' check(source='participant_text'),
 ai_allowed boolean not null default false,
 created_at timestamptz not null default clock_timestamp(),
 expires_at timestamptz not null default clock_timestamp()+interval '30 days'
);
create index meeting_segment_channel on public.meeting_transcript_segments(channel_id,created_at desc);
create index meeting_segment_expiry on public.meeting_transcript_segments(expires_at);
alter table public.meeting_transcript_segments enable row level security;
revoke all on public.meeting_transcript_segments from public,anon,authenticated;
grant select on public.meeting_transcript_segments to authenticated;
create policy meeting_segment_read on public.meeting_transcript_segments for select to authenticated
 using(expires_at>clock_timestamp() and aedrova_private.can_read_channel(channel_id));
create trigger meeting_segment_revision after insert or update or delete
 on public.meeting_transcript_segments for each row
 execute function aedrova_private.bump_context_revision();

create function public.append_meeting_text(p_meeting uuid,p_id uuid,p_revision bigint,
 p_roster uuid[],p_body text,p_offset integer) returns uuid
language plpgsql security definer set search_path='' as $$
declare m public.meetings; u uuid:=aedrova_private.require_user(); roster uuid[];
 all_trans boolean; all_ai boolean; existing public.meeting_transcript_segments;
begin
 m:=aedrova_private.lock_meeting(p_meeting);
 select array_agg(user_id order by user_id),bool_and(transcription),bool_and(ai_context)
 into roster,all_trans,all_ai from public.meeting_participants
 where meeting_id=m.id and present_until>clock_timestamp();
 if m.ended_at is not null or p_revision is distinct from m.revision
 or all_trans is distinct from true or roster is null
 or not (u=any(roster)) or p_roster is distinct from roster then
 raise exception 'Meeting consent changed. Discard pending text.' using errcode='42501'; end if;
 if p_id is null or p_body is null or char_length(trim(p_body)) not between 1 and 2000
 or p_offset is null or p_offset not between 0 and 86400000 then
 raise exception 'Invalid meeting text'; end if;
 select * into existing from public.meeting_transcript_segments where id=p_id;
 if existing.id is not null then
 if existing.meeting_id=m.id and existing.speaker_id=u and existing.body=trim(p_body)
 and existing.offset_ms=p_offset and existing.consent_revision=p_revision
 and existing.consent_roster=p_roster and existing.expires_at>clock_timestamp() then
 return p_id; end if;
 raise exception 'Segment identifier cannot be reused' using errcode='42501'; end if;
 perform aedrova_private.check_user_budget('meeting-text',60,60);
 if (select count(*) from public.meeting_transcript_segments where meeting_id=m.id)>=10000 then
 raise exception 'Meeting text limit reached'; end if;
 insert into public.meeting_transcript_segments
 (id,meeting_id,channel_id,speaker_id,consent_revision,consent_roster,body,offset_ms,ai_allowed)
 values(p_id,m.id,m.channel_id,u,p_revision,roster,trim(p_body),p_offset,all_ai);
 return p_id;
end $$;

-- Explicitly withdrawing consent invalidates stored material, including after a call ends.
-- Any speaker/consenting participant can withdraw their meeting's shared text.
create function public.withdraw_meeting_text(p_meeting uuid,p_delete boolean) returns void
language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); m public.meetings;
begin
 select * into m from public.meetings where id=p_meeting for update;
 if m.id is null or not exists(select 1 from public.meeting_participants
 where meeting_id=m.id and user_id=u) then
 raise exception 'Participant access required' using errcode='42501'; end if;
 if p_delete is null then raise exception 'Choose a withdrawal action'; end if;
 perform aedrova_private.check_user_budget('meeting-withdraw',20,60);
 if p_delete then delete from public.meeting_transcript_segments where meeting_id=m.id;
 else update public.meeting_transcript_segments set ai_allowed=false where meeting_id=m.id; end if;
 update public.meeting_participants set ai_context=false,
 transcription=case when p_delete then false else transcription end
 where meeting_id=m.id and user_id=u;
 update public.meetings set revision=revision+1 where id=m.id;
end $$;

create or replace function public.set_meeting_consent(p_meeting uuid,p_transcription boolean,p_ai boolean)
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
 if not p_transcription then delete from public.meeting_transcript_segments where meeting_id=m.id;
 elsif not p_ai then update public.meeting_transcript_segments set ai_allowed=false where meeting_id=m.id;
 end if;
 update public.meetings set revision=revision+1 where id=m.id;
end $$;

create function public.meeting_text_context(p_channel uuid,p_limit integer default 50)
returns setof public.meeting_transcript_segments language plpgsql stable security definer
set search_path='' as $$
begin
 perform aedrova_private.require_user();
 if not aedrova_private.can_read_channel(p_channel) then
 raise exception 'Channel access required' using errcode='42501'; end if;
 return query select * from public.meeting_transcript_segments where channel_id=p_channel
 and ai_allowed and expires_at>clock_timestamp() order by created_at desc,id
 limit greatest(1,least(coalesce(p_limit,50),50));
end $$;

-- Privileged maintenance only; run as a scheduled DB task during M14 setup.
create function aedrova_private.expire_meeting_text() returns bigint
language plpgsql security definer set search_path='' as $$
declare n bigint;
begin
 delete from public.meeting_transcript_segments where expires_at<=clock_timestamp();
 get diagnostics n=row_count; return n;
end $$;
revoke all on function aedrova_private.expire_meeting_text() from public,anon,authenticated;
revoke all on function public.append_meeting_text(uuid,uuid,bigint,uuid[],text,integer),
 public.withdraw_meeting_text(uuid,boolean),public.meeting_text_context(uuid,integer)
 from public,anon;
grant execute on function public.append_meeting_text(uuid,uuid,bigint,uuid[],text,integer),
 public.withdraw_meeting_text(uuid,boolean),public.meeting_text_context(uuid,integer)
 to authenticated;
commit;
