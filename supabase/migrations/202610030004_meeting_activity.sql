begin;
-- Only workspace administrators choose the shared public announcement channel.
create table public.workspace_meeting_preferences (
 workspace_id uuid primary key references public.workspaces(id) on delete cascade,
 announcement_channel uuid not null references public.channels(id) on delete cascade
);
alter table public.workspace_meeting_preferences enable row level security;
revoke all on public.workspace_meeting_preferences from public,anon,authenticated;
grant select on public.workspace_meeting_preferences to authenticated;
create policy meeting_preferences_read on public.workspace_meeting_preferences for select
 to authenticated using(aedrova_private.member_role(workspace_id) in ('owner','admin','member'));
create function public.set_meeting_announcement_channel(p_workspace uuid,p_channel uuid)
returns void language plpgsql security definer set search_path='' as $$
begin
 perform aedrova_private.require_user();
 if coalesce(aedrova_private.member_role(p_workspace),'') not in ('owner','admin')
 or not exists(select 1 from public.channels where id=p_channel and workspace_id=p_workspace
 and not private and kind='channel') then
 raise exception 'Choose a public channel in a workspace you administer' using errcode='42501';
 end if;
 insert into public.workspace_meeting_preferences values(p_workspace,p_channel)
 on conflict(workspace_id) do update set announcement_channel=excluded.announcement_channel;
end $$;
create function public.meeting_activity() returns jsonb
language sql stable security definer set search_path='' as $$
 select jsonb_build_object('meetings',coalesce((select jsonb_agg(jsonb_build_object(
 'id',m.id,'channel_id',m.channel_id,'workspace_id',c.workspace_id,'title',m.title,
 'started_at',m.started_at,'private',c.private,'participants',coalesce((select jsonb_agg(
 jsonb_build_object('user_id',p.user_id,'display_name',coalesce(
 nullif(left(u.raw_user_meta_data->>'full_name',80),''),'Teammate'),
 'avatar_url',case when u.raw_user_meta_data->>'avatar_url' ~
 '^https://lh[0-9]+\.googleusercontent\.com/' then
 left(u.raw_user_meta_data->>'avatar_url',2048) else null end) order by p.user_id)
 from public.meeting_participants p join auth.users u on u.id=p.user_id
 where p.meeting_id=m.id and p.present_until>clock_timestamp()),'[]'::jsonb))
 order by m.started_at desc) from public.meetings m join public.channels c on c.id=m.channel_id
 where m.ended_at is null and aedrova_private.can_read_channel(m.channel_id)), '[]'::jsonb),
 'preferences',coalesce((select jsonb_agg(jsonb_build_object('workspace_id',workspace_id,
 'announcement_channel',announcement_channel)) from public.workspace_meeting_preferences
 where aedrova_private.member_role(workspace_id) in ('owner','admin','member')),'[]'::jsonb))
$$;
revoke all on function public.meeting_activity(),
 public.set_meeting_announcement_channel(uuid,uuid) from public,anon;
grant execute on function public.meeting_activity(),
 public.set_meeting_announcement_channel(uuid,uuid) to authenticated;
commit;
