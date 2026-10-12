-- Server-inspected immutable uploads; existing published attachments remain readable.
begin;
alter table public.attachments add column verified_type text;
revoke execute on function public.finish_attachment(uuid,uuid) from public,anon,authenticated;
create function public.finish_verified_attachment(p_user uuid,p_id uuid,p_sha256 text,p_type text,
 p_parent uuid default null) returns uuid language plpgsql security definer set search_path='' as $$
declare a public.attachments; result uuid;
begin
 select * into a from public.attachments where id=p_id for update;
 if a.id is null or a.uploader_id is distinct from p_user or a.sha256 is distinct from p_sha256
 or p_type not in ('text/plain','image/png','image/jpeg','application/pdf',
 'application/vnd.openxmlformats-officedocument') or p_type is null
 then raise exception 'Upload verification failed' using errcode='42501'; end if;
 perform set_config('request.jwt.claims',json_build_object('sub',p_user,'role','authenticated')::text,true);
 perform set_config('request.jwt.claim.sub',p_user::text,true);
 -- Original finalization rechecks channel access, actual stored size, expiry and reply scope.
 result:=public.finish_attachment(p_id,p_parent);
 update public.attachments set verified_type=p_type where id=p_id;
 return result;
end $$;
revoke all on function public.finish_verified_attachment(uuid,uuid,text,text,uuid)
 from public,anon,authenticated,service_role;
do $$ begin
 if exists(select 1 from pg_roles where rolname='aedrova_website') then
  grant execute on function public.finish_verified_attachment(uuid,uuid,text,text,uuid) to aedrova_website;
 end if;
end $$;
create function public.abandon_attachment(p_id uuid) returns void
language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); a public.attachments;
begin
 select * into a from public.attachments where id=p_id for update;
 if a.id is null then return; end if;
 if a.uploader_id is distinct from u or a.message_id is not null
 then raise exception 'Upload cannot be cancelled' using errcode='42501'; end if;
 -- Storage accounting retains the charge until the existing cleanup lease deletes bytes.
 delete from public.attachments where id=p_id;
end $$;
revoke all on function public.abandon_attachment(uuid) from public,anon;
grant execute on function public.abandon_attachment(uuid) to authenticated;
commit;
