begin;

create function aedrova_private.wake_pin_peers() returns trigger
language plpgsql security definer set search_path='' as $$
declare
 channel uuid;
begin
 select m.channel_id into channel from public.messages m
 where m.id=case when tg_op='DELETE' then old.message_id else new.message_id end
 and m.unsent_at is null;

 if channel is not null then
  perform aedrova_private.wake_channel_peers(
   channel, coalesce(auth.uid(),'00000000-0000-0000-0000-000000000000'::uuid)
  );
 end if;
 return null;
end $$;
revoke all on function aedrova_private.wake_pin_peers() from public,anon,authenticated;
create trigger wake_pinned_message after insert on public.chat_marks
for each row when (new.kind='pinned') execute function aedrova_private.wake_pin_peers();
create trigger wake_unpinned_message after delete on public.chat_marks
for each row when (old.kind='pinned') execute function aedrova_private.wake_pin_peers();

commit;
