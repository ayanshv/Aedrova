-- Invited-beta allowlist. While the gate is on, only emails on the list can use the product.
-- The list stays empty here: load emails with the statements in docs/beta-allowlist.md.
-- Safe to run more than once. Run after 202611220001_slack_channels.sql.
begin;

create table if not exists aedrova_private.beta_gate (
    only_row boolean primary key default true check (only_row),
    enabled boolean not null default false
);
insert into aedrova_private.beta_gate (only_row, enabled) values (true, false)
on conflict do nothing;

create table if not exists aedrova_private.beta_access (
    email text primary key,
    note text not null default '' check (length(note) <= 200),
    added_at timestamptz not null default now()
);

alter table aedrova_private.beta_gate enable row level security;
alter table aedrova_private.beta_access enable row level security;
revoke all on aedrova_private.beta_gate, aedrova_private.beta_access
    from public, anon, authenticated;

-- One spelling per inbox: lower case, and for Gmail no dots and no +tag.
create or replace function aedrova_private.beta_email(p_email text)
returns text
language sql
immutable
set search_path = ''
as $$
    select case
        when split_part(lower(trim(p_email)), '@', 2) in ('gmail.com', 'googlemail.com') then
            replace(split_part(split_part(lower(trim(p_email)), '@', 1), '+', 1), '.', '')
            || '@gmail.com'
        else lower(trim(p_email))
    end
$$;

create or replace function aedrova_private.beta_allowed(p_user uuid)
returns boolean
language sql
stable
security definer
set search_path = ''
as $$
    select not coalesce((select enabled from aedrova_private.beta_gate), false)
        or exists (
            select 1
            from auth.users u
            join aedrova_private.beta_access a
              on a.email = aedrova_private.beta_email(u.email)
            where u.id = p_user
        )
$$;

create or replace function aedrova_private.require_user() returns uuid
language plpgsql stable security definer set search_path='' as $$
declare u uuid := auth.uid();
begin
 if u is null or not exists(select 1 from auth.users where id=u and email_confirmed_at is not null)
 then raise exception 'A confirmed account is required' using errcode='42501'; end if;
 if not aedrova_private.beta_allowed(u)
 then raise exception 'Aedrova is in a private beta and this email is not on the list yet'
   using errcode='42501'; end if;
 return u;
end $$;

-- The app asks this right after sign-in so it can explain, instead of failing later.
create or replace function public.beta_access_status()
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare u uuid := auth.uid();
begin
    if u is null then
        raise exception 'Sign in first' using errcode = '42501';
    end if;
    return jsonb_build_object(
        'gate', coalesce((select enabled from aedrova_private.beta_gate), false),
        'allowed', aedrova_private.beta_allowed(u)
    );
end;
$$;

revoke all on function public.beta_access_status() from public, anon, authenticated;
grant execute on function public.beta_access_status() to authenticated;

-- Stored emails are always normalised, so a mixed-case or dotted entry still matches.
create or replace function aedrova_private.beta_access_normalise() returns trigger
language plpgsql set search_path = '' as $$
begin
    new.email := aedrova_private.beta_email(new.email);
    return new;
end $$;

drop trigger if exists beta_access_normalise on aedrova_private.beta_access;
create trigger beta_access_normalise
    before insert or update on aedrova_private.beta_access
    for each row execute function aedrova_private.beta_access_normalise();

notify pgrst, 'reload schema';

commit;
