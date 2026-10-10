-- Bounded beta storage accounting and service-only orphan deletion leases.
-- Delete bytes through the Storage API, NEVER by deleting storage.objects in SQL.
begin;
create table aedrova_private.storage_usage (
 workspace_id uuid primary key,
 used_bytes bigint not null default 0 check(used_bytes>=0),
 limit_bytes bigint not null default 1073741824 check(limit_bytes>0)
);
create table aedrova_private.retired_storage_paths (
 object_path text primary key,
 retired_at timestamptz not null default now()
);
create table aedrova_private.storage_cleanup (
 object_path text primary key,
 workspace_id uuid not null,
 byte_size bigint not null check(byte_size>0),
 ready_at timestamptz not null default now()+interval '24 hours',
 lease uuid,
 lease_until timestamptz
);
create index storage_cleanup_ready on aedrova_private.storage_cleanup(ready_at,lease_until);
alter table public.attachments add column workspace_id uuid;
-- A caller's declared byte_size is untrusted until Storage verifies it at finalization.
-- Reserve the full per-object upload ceiling so undersized declarations cannot bypass quota.
alter table public.attachments add column charged_bytes bigint not null default 10485760;
update public.attachments set charged_bytes=byte_size where message_id is not null;
update public.attachments a set workspace_id=c.workspace_id from public.channels c where c.id=a.channel_id;
alter table public.attachments alter column workspace_id set not null;
create index attachments_pending_expiry on public.attachments(expires_at) where message_id is null;
insert into aedrova_private.storage_usage(workspace_id,used_bytes)
select workspace_id,sum(charged_bytes) from public.attachments group by workspace_id;

create function aedrova_private.account_storage() returns trigger
language plpgsql security definer set search_path='' as $$
declare used bigint; cap bigint; w uuid;
begin
 if TG_OP='DELETE' then
  insert into aedrova_private.retired_storage_paths(object_path) values(old.object_path) on conflict do nothing;
  insert into aedrova_private.storage_cleanup(object_path,workspace_id,byte_size)
  values(old.object_path,old.workspace_id,old.charged_bytes) on conflict do nothing;
  return old;
 end if;
 if TG_OP='UPDATE' then
  if old.message_id is null and new.message_id is not null then
   new.charged_bytes:=new.byte_size;
   update aedrova_private.storage_usage set used_bytes=used_bytes-old.charged_bytes+new.charged_bytes
   where workspace_id=old.workspace_id;
  end if;
  return new;
 end if;
 select workspace_id into w from public.channels where id=new.channel_id;
 if w is null then raise exception 'Channel unavailable' using errcode='42501'; end if;
 new.workspace_id:=w;
 new.charged_bytes:=10485760;
 if exists(select 1 from aedrova_private.retired_storage_paths where object_path=new.object_path)
 then raise exception 'Attachment identifier was retired; choose a new identifier' using errcode='42501'; end if;
 insert into aedrova_private.storage_usage(workspace_id) values(w) on conflict do nothing;
 select used_bytes,limit_bytes into used,cap from aedrova_private.storage_usage where workspace_id=w for update;
 if new.byte_size<=0 or new.byte_size>10485760 or used>cap-new.charged_bytes
 then raise exception 'Workspace storage limit reached. Contact your workspace owner.' using errcode='54000'; end if;
 update aedrova_private.storage_usage set used_bytes=used_bytes+new.charged_bytes where workspace_id=w;
 return new;
end $$;
create trigger attachment_storage_accounting before insert or delete or update on public.attachments
for each row execute function aedrova_private.account_storage();

create function public.claim_storage_cleanup(p_limit integer default 25)
returns table(object_path text,lease uuid) language plpgsql security definer set search_path='' as $$
begin
 if p_limit not between 1 and 50 then raise exception 'Invalid cleanup batch'; end if;
 -- Lock and retire expired pending reservations. Finalized files are never selected.
 delete from public.attachments where id in (
  select id from public.attachments where message_id is null
  and expires_at<now()-interval '24 hours' order by expires_at for update skip locked limit p_limit
 );
 return query with selected as (
  select q.object_path from aedrova_private.storage_cleanup q
  where q.ready_at<=now() and (q.lease_until is null or q.lease_until<=now())
  order by q.ready_at for update skip locked limit p_limit
 ) update aedrova_private.storage_cleanup q set lease=gen_random_uuid(),lease_until=now()+interval '10 minutes'
 from selected s where q.object_path=s.object_path returning q.object_path,q.lease;
end $$;
create function public.finish_storage_cleanup(p_path text,p_lease uuid) returns boolean
language plpgsql security definer set search_path='' as $$
declare item aedrova_private.storage_cleanup;
begin
 select * into item from aedrova_private.storage_cleanup where object_path=p_path for update;
 if p_lease is null or item.lease is null or item.lease_until is null
 or item.lease is distinct from p_lease or item.lease_until<=now() or item.object_path is null then return false; end if;
 if exists(select 1 from public.attachments where object_path=p_path)
 or exists(select 1 from storage.objects where bucket_id='aedrova-files' and name=p_path)
 then raise exception 'Object deletion has not completed'; end if;
 update aedrova_private.storage_usage set used_bytes=used_bytes-item.byte_size where workspace_id=item.workspace_id;
 delete from aedrova_private.storage_cleanup where object_path=p_path;
 return true;
end $$;
revoke all on aedrova_private.storage_usage,aedrova_private.storage_cleanup,
 aedrova_private.retired_storage_paths from public,anon,authenticated,service_role;
revoke all on function aedrova_private.account_storage(),public.claim_storage_cleanup(integer),
 public.finish_storage_cleanup(text,uuid) from public,anon,authenticated;
grant execute on function public.claim_storage_cleanup(integer),public.finish_storage_cleanup(text,uuid) to service_role;
commit;
