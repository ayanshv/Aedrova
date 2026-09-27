begin;
-- Milestone 3. Apply to a fresh Supabase project using the migration runner.
create schema if not exists aedrova_private;
revoke all on schema aedrova_private from public;
grant usage on schema aedrova_private to authenticated;

create table public.workspaces (
 id uuid primary key default gen_random_uuid(),
 name text not null check (length(btrim(name)) between 1 and 80),
 created_at timestamptz not null default now()
);
create table public.workspace_members (
 workspace_id uuid not null references public.workspaces on delete cascade,
 user_id uuid not null references auth.users on delete cascade,
 role text not null check (role in ('owner','admin','member','guest')),
 primary key (workspace_id, user_id)
);
create unique index workspace_one_owner on public.workspace_members(workspace_id) where role='owner';
create index memberships_by_user on public.workspace_members(user_id, workspace_id);
create table public.channels (
 id uuid primary key default gen_random_uuid(),
 workspace_id uuid not null references public.workspaces on delete cascade,
 name text not null check (length(btrim(name)) between 1 and 80),
 private boolean not null default false,
 unique (workspace_id,id), unique (workspace_id,name)
);
create table public.channel_members (
 workspace_id uuid not null,
 channel_id uuid not null,
 user_id uuid not null,
 primary key(channel_id,user_id),
 foreign key(workspace_id,channel_id) references public.channels(workspace_id,id) on delete cascade,
 foreign key(workspace_id,user_id) references public.workspace_members(workspace_id,user_id) on delete cascade
);
create table public.workspace_invitations (
 id uuid primary key default gen_random_uuid(),
 workspace_id uuid not null references public.workspaces on delete cascade,
 email text not null check (length(email) between 3 and 320),
 role text not null check(role in ('admin','member','guest')),
 token_hash text not null unique,
 invited_by uuid not null references auth.users,
 expires_at timestamptz not null default now()+interval '7 days',
 accepted_at timestamptz,
 revoked_at timestamptz
);

create function aedrova_private.member_role(w uuid) returns text
language sql stable security definer set search_path='' as $$
 select role from public.workspace_members where workspace_id=w and user_id=(select auth.uid())
$$;
create function aedrova_private.can_read_channel(c uuid) returns boolean
language sql stable security definer set search_path='' as $$
 select exists(select 1 from public.channels ch
 join public.workspace_members m on m.workspace_id=ch.workspace_id and m.user_id=(select auth.uid())
 where ch.id=c and ((not ch.private and m.role <> 'guest') or exists(
 select 1 from public.channel_members cm where cm.channel_id=ch.id and cm.user_id=m.user_id)))
$$;
create function aedrova_private.require_user() returns uuid
language plpgsql stable security definer set search_path='' as $$
declare u uuid := auth.uid();
begin
 if u is null or not exists(select 1 from auth.users where id=u and email_confirmed_at is not null)
 then raise exception 'A confirmed account is required' using errcode='42501'; end if;
 return u;
end $$;

alter table public.workspaces enable row level security;
alter table public.workspace_members enable row level security;
alter table public.channels enable row level security;
alter table public.channel_members enable row level security;
alter table public.workspace_invitations enable row level security;
revoke all on public.workspaces, public.workspace_members, public.channels,
 public.channel_members, public.workspace_invitations from public,anon,authenticated;
grant select on public.workspaces, public.workspace_members, public.channels,
 public.channel_members to authenticated;
-- Invitation hashes never leave the database. Management uses an explicit projection.
grant select(id,workspace_id,email,role,invited_by,expires_at,accepted_at,revoked_at)
 on public.workspace_invitations to authenticated;
create policy workspace_read on public.workspaces for select to authenticated
 using (aedrova_private.member_role(id) is not null);
create policy membership_read on public.workspace_members for select to authenticated
 using (user_id=auth.uid() or aedrova_private.member_role(workspace_id) in ('owner','admin'));
create policy channel_read on public.channels for select to authenticated
 using (aedrova_private.can_read_channel(id));
create policy channel_members_read on public.channel_members for select to authenticated
 using (aedrova_private.can_read_channel(channel_id));
create policy invitation_read on public.workspace_invitations for select to authenticated
 using (aedrova_private.member_role(workspace_id) in ('owner','admin'));

create function public.create_workspace(p_name text) returns uuid
language plpgsql security definer set search_path='' as $$
declare u uuid := aedrova_private.require_user(); w uuid;
begin
 insert into public.workspaces(name) values(btrim(p_name)) returning id into w;
 insert into public.workspace_members values(w,u,'owner');
 insert into public.channels(workspace_id,name) values(w,'general');
 return w;
end $$;
create function public.create_channel(p_workspace uuid,p_name text,p_private boolean default false)
returns uuid language plpgsql security definer set search_path='' as $$
declare u uuid := aedrova_private.require_user(); c uuid;
begin
 perform 1 from public.workspaces where id=p_workspace for update;
 if coalesce(aedrova_private.member_role(p_workspace),'') not in ('owner','admin','member')
 or (p_private and aedrova_private.member_role(p_workspace) not in ('owner','admin'))
 then raise exception 'Not allowed' using errcode='42501'; end if;
 insert into public.channels(workspace_id,name,private) values(p_workspace,btrim(p_name),p_private)
 returning id into c;
 insert into public.channel_members values(p_workspace,c,u);
 return c;
end $$;
create function public.create_invitation(p_workspace uuid,p_email text,p_role text default 'member')
returns text language plpgsql security definer set search_path='' as $$
declare u uuid := aedrova_private.require_user(); r text; token text;
begin
 perform 1 from public.workspaces where id=p_workspace for update;
 r := aedrova_private.member_role(p_workspace);
 if coalesce(r,'') not in ('owner','admin') or p_role not in ('admin','member','guest')
 or (p_role='admin' and r <> 'owner') or p_email is null
 or p_email !~ '^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$'
 then raise exception 'Not allowed or invalid invitation' using errcode='42501'; end if;
 token := replace(gen_random_uuid()::text,'-','') || replace(gen_random_uuid()::text,'-','');
 insert into public.workspace_invitations(workspace_id,email,role,token_hash,invited_by)
 values(p_workspace,lower(btrim(p_email)),p_role,encode(sha256(convert_to(token,'UTF8')),'hex'),u);
 return token;
end $$;
create function public.accept_invitation(p_token text) returns uuid
language plpgsql security definer set search_path='' as $$
declare u uuid := aedrova_private.require_user(); inv public.workspace_invitations; mail text;
begin
 select * into inv from public.workspace_invitations
 where token_hash=encode(sha256(convert_to(p_token,'UTF8')),'hex');
 if inv.id is null then raise exception 'Invitation unavailable' using errcode='42501'; end if;
 -- Serialize all membership mutations for a workspace, then re-read the invitation.
 perform 1 from public.workspaces where id=inv.workspace_id for update;
 select * into inv from public.workspace_invitations where id=inv.id for update;
 select lower(email) into mail from auth.users where id=u;
 if mail is distinct from inv.email or inv.accepted_at is not null or inv.revoked_at is not null
 or inv.expires_at <= now() or not exists(select 1 from public.workspace_members
 where workspace_id=inv.workspace_id and user_id=inv.invited_by
 and (role='owner' or (role='admin' and inv.role in ('member','guest'))))
 then raise exception 'Invitation unavailable' using errcode='42501'; end if;
 -- A join cannot promote/demote an existing member.
 insert into public.workspace_members values(inv.workspace_id,u,inv.role) on conflict do nothing;
 update public.workspace_invitations set accepted_at=now() where id=inv.id;
 return inv.workspace_id;
end $$;
create function public.revoke_invitation(p_invitation uuid) returns void
language plpgsql security definer set search_path='' as $$
declare w uuid;
begin
 perform aedrova_private.require_user();
 select workspace_id into w from public.workspace_invitations where id=p_invitation;
 perform 1 from public.workspaces where id=w for update;
 if coalesce(aedrova_private.member_role(w),'') not in ('owner','admin')
 then raise exception 'Not allowed' using errcode='42501'; end if;
 update public.workspace_invitations set revoked_at=now() where id=p_invitation;
end $$;
create function public.set_member_role(p_workspace uuid,p_user uuid,p_role text) returns void
language plpgsql security definer set search_path='' as $$
begin
 perform aedrova_private.require_user();
 perform 1 from public.workspaces where id=p_workspace for update;
 if aedrova_private.member_role(p_workspace) is distinct from 'owner'
 or p_role not in ('admin','member','guest') or p_role is null
 then raise exception 'Only the owner can change roles' using errcode='42501'; end if;
 update public.workspace_members set role=p_role
 where workspace_id=p_workspace and user_id=p_user and role <> 'owner';
 if not found then raise exception 'Member unavailable' using errcode='42501'; end if;
end $$;
create function public.remove_member(p_workspace uuid,p_user uuid) returns void
language plpgsql security definer set search_path='' as $$
declare actor text; target text;
begin
 perform aedrova_private.require_user();
 perform 1 from public.workspaces where id=p_workspace for update;
 actor := coalesce(aedrova_private.member_role(p_workspace),'');
 select role into target from public.workspace_members where workspace_id=p_workspace and user_id=p_user;
 if target is null or target='owner' or not (coalesce(actor,'')='owner'
 or (actor='admin' and target in ('member','guest')) or p_user=auth.uid())
 then raise exception 'Not allowed' using errcode='42501'; end if;
 delete from public.workspace_members where workspace_id=p_workspace and user_id=p_user;
end $$;
create function public.set_channel_member(p_channel uuid,p_user uuid,p_allowed boolean) returns void
language plpgsql security definer set search_path='' as $$
declare w uuid;
begin
 perform aedrova_private.require_user();
 select workspace_id into w from public.channels where id=p_channel;
 perform 1 from public.workspaces where id=w for update;
 if coalesce(aedrova_private.member_role(w),'') not in ('owner','admin')
 or not aedrova_private.can_read_channel(p_channel)
 then raise exception 'Not allowed' using errcode='42501'; end if;
 if p_allowed then
 insert into public.channel_members values(w,p_channel,p_user) on conflict do nothing;
 else delete from public.channel_members where channel_id=p_channel and user_id=p_user;
 end if;
end $$;
-- Default PUBLIC function execution must never expose definer operations to anonymous users.
revoke all on all functions in schema aedrova_private from public,anon;
grant execute on all functions in schema aedrova_private to authenticated;
revoke all on function public.create_workspace(text), public.create_channel(uuid,text,boolean),
 public.create_invitation(uuid,text,text), public.accept_invitation(text),
 public.revoke_invitation(uuid),public.set_member_role(uuid,uuid,text),
 public.remove_member(uuid,uuid),public.set_channel_member(uuid,uuid,boolean) from public,anon;
grant execute on function public.create_workspace(text), public.create_channel(uuid,text,boolean),
 public.create_invitation(uuid,text,text), public.accept_invitation(text),
 public.revoke_invitation(uuid),public.set_member_role(uuid,uuid,text),
 public.remove_member(uuid,uuid),public.set_channel_member(uuid,uuid,boolean) to authenticated;

-- Object paths: <workspace UUID>/<channel UUID>/<unique object name>. Private bucket only.
insert into storage.buckets(id,name,public) values('aedrova-files','aedrova-files',false);
create function aedrova_private.can_read_object(path text) returns boolean
language sql stable security definer set search_path='' as $$
 select exists(select 1 from public.channels c where c.workspace_id::text=split_part(path,'/',1)
 and c.id::text=split_part(path,'/',2) and split_part(path,'/',3) <> ''
 and aedrova_private.can_read_channel(c.id))
$$;
revoke all on function aedrova_private.can_read_object(text) from public,anon;
grant execute on function aedrova_private.can_read_object(text) to authenticated;
create policy aedrova_files_read on storage.objects for select to authenticated
 using (bucket_id='aedrova-files' and aedrova_private.can_read_object(name));
-- No direct client upload/update/delete until the attachment validation milestone.
-- Only server broadcast; clients may subscribe to authorized channel UUID topics.
create policy aedrova_channel_events on realtime.messages for select to authenticated
 using (extension='broadcast' and exists(select 1 from public.channels c
 where 'channel:'||c.id::text = realtime.topic() and aedrova_private.can_read_channel(c.id)));

-- Human-readable roster without exposing the global auth.users table.
create function public.list_members()
returns table(workspace_id uuid,user_id uuid,role text,email text)
language sql stable security definer set search_path='' as $$
 select m.workspace_id,m.user_id,m.role,u.email::text
 from public.workspace_members m join auth.users u on u.id=m.user_id
 where m.user_id=auth.uid() or aedrova_private.member_role(m.workspace_id) in ('owner','admin')
$$;
revoke all on function public.list_members() from public,anon;
grant execute on function public.list_members() to authenticated;

commit;
