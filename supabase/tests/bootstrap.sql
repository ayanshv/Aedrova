-- Test-only Supabase schema facsimile for embedded PostgreSQL. NEVER apply to Supabase.
create role anon nologin;
create role authenticated nologin;
create schema auth;
create table auth.users(id uuid primary key,email text,email_confirmed_at timestamptz);
create function auth.uid() returns uuid language sql stable as $$
 select nullif(current_setting('request.jwt.claim.sub',true),'')::uuid
$$;
grant usage on schema auth to authenticated,anon;
grant execute on function auth.uid() to authenticated,anon;
create schema storage;
create table storage.buckets(id text primary key,name text,public boolean);
create table storage.objects(id uuid primary key default gen_random_uuid(),bucket_id text,name text);
alter table storage.objects enable row level security;
grant usage on schema storage to authenticated,anon;
grant select,insert,update,delete on storage.objects to authenticated;
create schema realtime;
create table realtime.messages(id bigint,extension text);
alter table realtime.messages enable row level security;
create function realtime.topic() returns text language sql stable as $$
 select current_setting('realtime.topic',true)
$$;
grant usage on schema realtime to authenticated;
grant select,insert on realtime.messages to authenticated;
