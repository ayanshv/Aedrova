begin;
-- M12D: server-only provenance and human review. Activate only at M14.
alter table public.meeting_transcript_segments drop constraint meeting_transcript_segments_source_check;
alter table public.meeting_transcript_segments add constraint meeting_transcript_segments_source_check
 check(source in ('participant_text','provider_speech'));
alter table public.meeting_transcript_segments
 add column review_body text check(char_length(review_body) between 1 and 2000),
 add column reviewed_by uuid references auth.users(id),
 add column reviewed_at timestamptz,
 add column review_version integer not null default 0,
 add column confirmed_decision boolean not null default false;

-- No audio, credentials or provider response payloads are persisted.
create table aedrova_private.meeting_speech_jobs (
 id uuid primary key, meeting_id uuid not null references public.meetings(id) on delete cascade,
 user_id uuid not null references auth.users(id) on delete cascade,
 revision bigint not null, roster uuid[] not null, digest text not null,
 offset_ms integer not null, duration_ms integer not null,
 state text not null default 'pending' check(state in ('pending','completed','failed')),
 created_at timestamptz not null default clock_timestamp(),
 deadline timestamptz not null default clock_timestamp()+interval '45 seconds'
);
create index speech_budget_window on aedrova_private.meeting_speech_jobs(created_at,meeting_id);
revoke all on aedrova_private.meeting_speech_jobs from public,anon,authenticated;

create function aedrova_private.check_speech_scope(p_user uuid,p_meeting uuid,p_revision bigint,
 p_roster uuid[]) returns boolean language plpgsql security definer set search_path='' as $$
declare m public.meetings; roster uuid[]; saving boolean; ai boolean; prior text;
begin
 if p_user is null then raise exception 'Account required' using errcode='42501'; end if;
 prior:=current_setting('request.jwt.claim.sub',true);
 perform set_config('request.jwt.claim.sub',p_user::text,true);
 m:=aedrova_private.lock_meeting(p_meeting);
 select array_agg(user_id order by user_id),bool_and(transcription),bool_and(ai_context)
 into roster,saving,ai from public.meeting_participants
 where meeting_id=m.id and present_until>clock_timestamp();
 if m.ended_at is not null or m.revision is distinct from p_revision
 or saving is distinct from true or roster is null or not(p_user=any(roster))
 or p_roster is distinct from roster then
 raise exception 'Meeting consent changed. Discard audio and text.' using errcode='42501'; end if;
 perform set_config('request.jwt.claim.sub',coalesce(prior,''),true);
 return ai;
end $$;
revoke all on function aedrova_private.check_speech_scope(uuid,uuid,bigint,uuid[])
 from public,anon,authenticated;

create function public.reserve_meeting_speech(p_user uuid,p_meeting uuid,p_id uuid,
 p_revision bigint,p_roster uuid[],p_digest text,p_offset integer,p_duration integer)
 returns text language plpgsql security definer set search_path='' as $$
declare j aedrova_private.meeting_speech_jobs; w uuid; prior text;
begin
 perform aedrova_private.check_speech_scope(p_user,p_meeting,p_revision,p_roster);
 if p_id is null or p_digest !~ '^[a-f0-9]{64}$' or p_digest is null
 or p_offset is null or p_offset not between 0 and 86400000
 or p_duration is null or p_duration not between 1000 and 10000 then
 raise exception 'Invalid speech chunk'; end if;
 select * into j from aedrova_private.meeting_speech_jobs where id=p_id;
 if j.id is not null then
 if j.user_id=p_user and j.meeting_id=p_meeting and j.digest=p_digest
 and j.revision=p_revision and j.roster=p_roster and j.offset_ms=p_offset
 and j.duration_ms=p_duration and j.state='completed'
 and exists(select 1 from public.meeting_transcript_segments where id=p_id
 and expires_at>clock_timestamp()) then return 'completed'; end if;
 raise exception 'Speech identifier already used' using errcode='42501'; end if;
 -- Serialize this user across meetings before checking outstanding requests.
 perform pg_advisory_xact_lock(hashtextextended(p_user::text,7411));
 if exists(select 1 from aedrova_private.meeting_speech_jobs where user_id=p_user
 and state='pending' and deadline>clock_timestamp()) then
 raise exception 'Previous speech chunk is processing' using errcode='42501'; end if;
 prior:=current_setting('request.jwt.claim.sub',true);
 perform set_config('request.jwt.claim.sub',p_user::text,true);
 perform aedrova_private.check_user_budget('meeting-speech',12,60);
 perform set_config('request.jwt.claim.sub',coalesce(prior,''),true);
 select workspace_id into w from public.channels where id=(select channel_id
 from public.meetings where id=p_meeting);
 -- Serialize budget across concurrent meetings in this workspace.
 perform pg_advisory_xact_lock(hashtextextended(w::text,7412));
 if (select coalesce(sum(budget.duration_ms),0) from aedrova_private.meeting_speech_jobs budget
 join public.meetings m on m.id=budget.meeting_id join public.channels c on c.id=m.channel_id
 where c.workspace_id=w and budget.created_at>clock_timestamp()-interval '24 hours')
 +p_duration>3600000 then
 raise exception 'Workspace daily transcription allowance reached' using errcode='42501'; end if;
 if (select count(*) from public.meeting_transcript_segments where meeting_id=p_meeting)>=10000 then
 raise exception 'Meeting transcript limit reached'; end if;
 insert into aedrova_private.meeting_speech_jobs
 (id,meeting_id,user_id,revision,roster,digest,offset_ms,duration_ms)
 values(p_id,p_meeting,p_user,p_revision,p_roster,p_digest,p_offset,p_duration);
 return 'pending';
end $$;

create function public.finish_meeting_speech(p_user uuid,p_id uuid,p_body text)
 returns uuid language plpgsql security definer set search_path='' as $$
declare j aedrova_private.meeting_speech_jobs; ai boolean;
begin
 -- Lock meeting before job: same order as reservation and privacy withdrawal.
 perform 1 from public.meetings where id=(select meeting_id
 from aedrova_private.meeting_speech_jobs where id=p_id) for update;
 select * into j from aedrova_private.meeting_speech_jobs where id=p_id for update;
 if j.id is null or j.user_id is distinct from p_user or j.state<>'pending'
 or j.deadline<=clock_timestamp() then
 raise exception 'Speech request expired or invalid' using errcode='42501'; end if;
 ai:=aedrova_private.check_speech_scope(p_user,j.meeting_id,j.revision,j.roster);
 if p_body is null then
 update aedrova_private.meeting_speech_jobs set state='failed' where id=p_id;
 return null; end if;
 if char_length(trim(p_body)) not between 1 and 2000 then raise exception 'Invalid speech text'; end if;
 insert into public.meeting_transcript_segments
 (id,meeting_id,channel_id,speaker_id,consent_revision,consent_roster,body,offset_ms,source,ai_allowed)
 values(p_id,j.meeting_id,(select channel_id from public.meetings where id=j.meeting_id),
 p_user,j.revision,j.roster,trim(p_body),j.offset_ms,'provider_speech',ai);
 update aedrova_private.meeting_speech_jobs set state='completed' where id=p_id;
 return p_id;
end $$;
revoke all on function public.reserve_meeting_speech(uuid,uuid,uuid,bigint,uuid[],text,integer,integer),
 public.finish_meeting_speech(uuid,uuid,text) from public,anon,authenticated;
-- Restricted backend database role only; no service-role key in the desktop.
do $$ begin if exists(select 1 from pg_roles where rolname='aedrova_website') then
 grant execute on function public.reserve_meeting_speech(uuid,uuid,uuid,bigint,uuid[],text,integer,integer),
 public.finish_meeting_speech(uuid,uuid,text) to aedrova_website;
end if; end $$;

create function public.review_meeting_segment(p_id uuid,p_version integer,p_body text,
 p_decision boolean default false) returns integer language plpgsql security definer set search_path='' as $$
declare s public.meeting_transcript_segments; u uuid:=aedrova_private.require_user();
begin
 perform 1 from public.meetings where id=(select meeting_id
 from public.meeting_transcript_segments where id=p_id) for update;
 select * into s from public.meeting_transcript_segments where id=p_id for update;
 if s.id is null or s.expires_at<=clock_timestamp()
 or not aedrova_private.can_read_channel(s.channel_id)
 or not (s.speaker_id=u or exists(select 1 from public.workspace_members wm
 join public.channels c on c.workspace_id=wm.workspace_id
 where c.id=s.channel_id and wm.user_id=u and wm.role in ('owner','admin'))) then
 raise exception 'Speaker or workspace admin access required' using errcode='42501'; end if;
 if s.review_version is distinct from p_version then
 raise exception 'Transcript changed. Refresh before reviewing.' using errcode='40001'; end if;
 if p_body is null or char_length(trim(p_body)) not between 1 and 2000
 or p_decision is null then raise exception 'Invalid review'; end if;
 perform aedrova_private.check_user_budget('meeting-review',30,60);
 update public.meeting_transcript_segments set review_body=trim(p_body),reviewed_by=u,
 reviewed_at=clock_timestamp(),review_version=review_version+1,confirmed_decision=p_decision
 where id=p_id;
 return p_version+1;
end $$;
revoke all on function public.review_meeting_segment(uuid,integer,text,boolean) from public,anon;
grant execute on function public.review_meeting_segment(uuid,integer,text,boolean) to authenticated;
create or replace function public.meeting_text_context(p_channel uuid,p_limit integer default 50)
returns setof public.meeting_transcript_segments language plpgsql stable security definer set search_path='' as $$
begin
 perform aedrova_private.require_user();
 if not aedrova_private.can_read_channel(p_channel) then
 raise exception 'Channel access required' using errcode='42501'; end if;
 return query select * from public.meeting_transcript_segments where channel_id=p_channel
 and ai_allowed and expires_at>clock_timestamp()
 and (source='participant_text' or reviewed_at is not null)
 order by created_at desc,id limit greatest(1,least(coalesce(p_limit,50),50));
end $$;
-- Expiry also clears provider idempotency metadata. Does not contain raw audio.
create or replace function aedrova_private.expire_meeting_text() returns bigint
language plpgsql security definer set search_path='' as $$ declare n bigint; begin
 delete from public.meeting_transcript_segments where expires_at<=clock_timestamp();
 get diagnostics n=row_count;
 delete from aedrova_private.meeting_speech_jobs where created_at<clock_timestamp()-interval '30 days';
 return n;
end $$;
commit;
