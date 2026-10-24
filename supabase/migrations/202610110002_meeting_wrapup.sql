begin;
-- End an empty room under the same lock used by joining. Leaving while others
-- remain never ends their meeting or offers a premature review.
create or replace function public.leave_meeting(p_meeting uuid) returns void
language plpgsql security definer set search_path='' as $$
declare m public.meetings; n integer;
begin
 m:=aedrova_private.lock_meeting(p_meeting);
 update public.meeting_participants set present_until=clock_timestamp(),
 transcription=false,ai_context=false where meeting_id=m.id and user_id=auth.uid();
 get diagnostics n=row_count;
 if n>0 then
  update public.meetings set revision=revision+1,
   ended_at=case when not exists(select 1 from public.meeting_participants
    where meeting_id=m.id and present_until>clock_timestamp())
    then coalesce(ended_at,clock_timestamp()) else ended_at end where id=m.id;
 end if;
end $$;

create function public.meeting_wrapup_status(p_meeting uuid) returns jsonb
language plpgsql security definer set search_path='' as $$
declare m public.meetings; u uuid:=aedrova_private.require_user(); w uuid; n integer;
 allowed boolean;
begin
 m:=aedrova_private.lock_meeting(p_meeting);
 select workspace_id into w from public.channels where id=m.channel_id;
 perform aedrova_private.check_user_budget('meeting-wrapup',30,60);
 select count(*) into n from public.meeting_transcript_segments
 where meeting_id=m.id and expires_at>clock_timestamp();
 allowed:=n>0 and coalesce(aedrova_private.member_role(w),'') in ('owner','admin')
  and exists(select 1 from public.meeting_participants where meeting_id=m.id and user_id=u);
 return jsonb_build_object('meeting',m.id,'title',m.title,'can_review',allowed,
  'ready',m.ended_at is not null and allowed);
end $$;

-- One explicit confirmation, one transaction. Stale, missing, duplicated or
-- cross-meeting edits roll everything back. Never changes participant AI consent.
create function public.confirm_meeting_transcript(p_meeting uuid,p_segments jsonb)
returns integer language plpgsql security definer set search_path='' as $$
declare m public.meetings; u uuid:=aedrova_private.require_user(); w uuid; n integer;
begin
 m:=aedrova_private.lock_meeting(p_meeting);
 select workspace_id into w from public.channels where id=m.channel_id;
 if m.ended_at is null or coalesce(aedrova_private.member_role(w),'') not in ('owner','admin')
 or not exists(select 1 from public.meeting_participants where meeting_id=m.id and user_id=u) then
  raise exception 'Ended meeting and participant admin access required' using errcode='42501';
 end if;
 perform aedrova_private.check_user_budget('meeting-confirm',5,60);
 if p_segments is null or jsonb_typeof(p_segments)<>'array' then
  raise exception 'Invalid transcript review';
 end if;
 n:=jsonb_array_length(p_segments);
 if n not between 1 and 10000 or octet_length(p_segments::text)>1500000
 or exists(select 1 from jsonb_array_elements(p_segments) x where
  jsonb_typeof(x)<>'object' or jsonb_typeof(x->'body') is distinct from 'string'
  or jsonb_typeof(x->'version') is distinct from 'number'
  or jsonb_typeof(x->'identifier') is distinct from 'string'
  or char_length(trim(x->>'body')) not between 1 and 2000
  or (x->>'version') !~ '^[0-9]{1,9}$') then
  raise exception 'Invalid transcript review';
 end if;
 if (select count(distinct (x->>'identifier')::uuid) from jsonb_array_elements(p_segments) x)<>n
 or (select count(*) from public.meeting_transcript_segments
     where meeting_id=m.id and expires_at>clock_timestamp())<>n
 or (select count(*) from jsonb_array_elements(p_segments) x
     join public.meeting_transcript_segments s on s.id=(x->>'identifier')::uuid
     where s.meeting_id=m.id and s.expires_at>clock_timestamp()
     and s.review_version=(x->>'version')::integer)<>n then
  raise exception 'Transcript changed. Refresh before confirming.' using errcode='40001';
 end if;
 update public.meeting_transcript_segments s set review_body=trim(x.body),
 reviewed_by=u,reviewed_at=clock_timestamp(),review_version=s.review_version+1
 from jsonb_to_recordset(p_segments) as x(identifier uuid,version integer,body text)
 where s.id=x.identifier and s.meeting_id=m.id;
 return n;
end $$;
revoke all on function public.meeting_wrapup_status(uuid),
 public.confirm_meeting_transcript(uuid,jsonb) from public,anon;
grant execute on function public.meeting_wrapup_status(uuid),
 public.confirm_meeting_transcript(uuid,jsonb) to authenticated;
commit;
