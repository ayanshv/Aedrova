begin;

create table if not exists aedrova_private.slack_imports (
    workspace_id uuid not null references public.workspaces on delete cascade,
    id uuid not null,
    created_at timestamptz not null default now(),
    next_batch integer not null default 0,
    published_at timestamptz,
    primary key (workspace_id, id)
);

create table if not exists aedrova_private.slack_messages (
    workspace_id uuid not null,
    import_id uuid not null,
    channel_id text not null check (channel_id ~ '^C[A-Z0-9]{1,39}$'),
    channel_name text not null check (length(channel_name) between 1 and 80),
    source_ts numeric(16,6) not null check (source_ts >= 0),
    thread_ts numeric(16,6) check (thread_ts >= 0),
    author text not null check (length(author) between 1 and 160),
    body text not null check (length(body) <= 8000),
    links jsonb not null check (
        jsonb_typeof(links) = 'array'
        and octet_length(links::text) <= 9000
    ),
    reactions jsonb not null check (
        jsonb_typeof(reactions) = 'object'
        and octet_length(reactions::text) <= 3000
    ),
    primary key (workspace_id, import_id, channel_id, source_ts),
    foreign key (workspace_id, import_id)
        references aedrova_private.slack_imports on delete cascade
);

create index if not exists slack_message_key
    on aedrova_private.slack_messages (workspace_id, channel_id, source_ts);

create index if not exists slack_message_search
    on aedrova_private.slack_messages using gin
    (to_tsvector('simple'::regconfig, channel_name || ' ' || author || ' ' || body));

alter table aedrova_private.slack_imports enable row level security;
alter table aedrova_private.slack_messages enable row level security;

revoke all on aedrova_private.slack_imports, aedrova_private.slack_messages
    from public, anon, authenticated;

create or replace function public.write_slack_history(
    p_workspace uuid,
    p_import uuid,
    p_batch integer,
    p_rows jsonb,
    p_finish boolean
)
returns integer
language plpgsql
security definer
set search_path = ''
as $$
declare
    n integer;
    expected integer;
begin
    perform aedrova_private.require_user();
    perform pg_advisory_xact_lock(hashtextextended(p_workspace::text, 126923));

    if coalesce(aedrova_private.member_role(p_workspace), '') not in ('owner', 'admin') then
        raise exception 'Workspace owner or admin required' using errcode = '42501';
    end if;

    perform aedrova_private.check_user_budget('slack-import-write', 120, 60);

    if p_batch is null
       or p_batch < 0
       or p_rows is null
       or p_finish is null then
        raise exception 'Invalid Slack import batch' using errcode = '22023';
    end if;

    if jsonb_typeof(p_rows) is distinct from 'array'
       or octet_length(p_rows::text) > 400000 then
        raise exception 'Invalid Slack import batch' using errcode = '22023';
    end if;

    if jsonb_array_length(p_rows) > 250 then
        raise exception 'Invalid Slack import batch' using errcode = '22023';
    end if;

    delete from aedrova_private.slack_imports
    where workspace_id = p_workspace
      and published_at is null
      and created_at < now() - interval '1 day';

    if exists (
        select 1
        from aedrova_private.slack_imports
        where workspace_id = p_workspace
          and id = p_import
          and published_at is not null
    ) then
        return (
            select count(*)
            from aedrova_private.slack_messages
            where workspace_id = p_workspace
              and import_id = p_import
        );
    end if;

    if not exists (
        select 1
        from aedrova_private.slack_imports
        where workspace_id = p_workspace
          and id = p_import
    )
    and (
        select count(*)
        from aedrova_private.slack_imports
        where workspace_id = p_workspace
    ) >= 100 then
        raise exception 'Workspace import limit reached' using errcode = '22023';
    end if;

    insert into aedrova_private.slack_imports (workspace_id, id)
    values (p_workspace, p_import)
    on conflict do nothing;

    select next_batch
    into expected
    from aedrova_private.slack_imports
    where workspace_id = p_workspace
      and id = p_import;

    if p_batch < expected then
        return 0;
    elsif p_batch > expected then
        raise exception 'Slack import checkpoint changed. Retry the same export'
            using errcode = '22023';
    end if;

    insert into aedrova_private.slack_messages (
        workspace_id,
        import_id,
        channel_id,
        channel_name,
        source_ts,
        thread_ts,
        author,
        body,
        links,
        reactions
    )
    select
        p_workspace,
        p_import,
        r.channel_id,
        r.channel_name,
        r.source_ts,
        r.thread_ts,
        r.author,
        r.body,
        r.links,
        r.reactions
    from jsonb_to_recordset(p_rows) as r(
        channel_id text,
        channel_name text,
        source_ts numeric,
        thread_ts numeric,
        author text,
        body text,
        links jsonb,
        reactions jsonb
    )
    on conflict do nothing;

    if (
        select count(*)
        from aedrova_private.slack_messages
        where workspace_id = p_workspace
    ) > 100000 then
        raise exception 'Workspace history limit reached' using errcode = '22023';
    end if;

    update aedrova_private.slack_imports
    set next_batch = expected + 1
    where workspace_id = p_workspace
      and id = p_import;

    if p_finish then
        delete from aedrova_private.slack_messages m
        using aedrova_private.slack_messages old,
              aedrova_private.slack_imports i
        where m.workspace_id = p_workspace
          and m.import_id = p_import
          and old.workspace_id = m.workspace_id
          and old.channel_id = m.channel_id
          and old.source_ts = m.source_ts
          and old.import_id <> p_import
          and i.workspace_id = old.workspace_id
          and i.id = old.import_id
          and i.published_at is not null;

        update aedrova_private.slack_imports
        set published_at = now()
        where workspace_id = p_workspace
          and id = p_import;
    end if;

    select count(*)
    into n
    from aedrova_private.slack_messages
    where workspace_id = p_workspace
      and import_id = p_import;

    return n;
end;
$$;

create or replace function public.slack_history(
    p_workspace uuid,
    p_query text default '',
    p_limit integer default 50
)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
declare
    q tsquery;
begin
    perform aedrova_private.require_user();

    if coalesce(aedrova_private.member_role(p_workspace), '')
       not in ('owner', 'admin', 'member') then
        raise exception 'Workspace membership required' using errcode = '42501';
    end if;

    q := websearch_to_tsquery('simple', left(coalesce(p_query, ''), 1400));

    return coalesce((
        select jsonb_agg(to_jsonb(r))
        from (
            select
                'slack:' || m.channel_id || ':' || m.source_ts as id,
                m.channel_name,
                m.author,
                m.body,
                m.source_ts::text,
                m.thread_ts::text,
                m.import_id,
                m.links,
                m.reactions
            from aedrova_private.slack_messages m
            join aedrova_private.slack_imports i
              on i.workspace_id = m.workspace_id
             and i.id = m.import_id
            where m.workspace_id = p_workspace
              and i.published_at is not null
              and case
                  when left(coalesce(p_query, ''), 6) = 'slack:' then
                      ('slack:' || m.channel_id || ':' || m.source_ts)
                      = any(string_to_array(left(p_query, 1400), ' '))
                  else
                      numnode(q) = 0
                      or to_tsvector(
                          'simple',
                          m.channel_name || ' ' || m.author || ' ' || m.body
                      ) @@ q
              end
            order by m.source_ts desc, m.channel_id
            limit least(greatest(coalesce(p_limit, 50), 1), 100)
        ) r
    ), '[]'::jsonb);
end;
$$;

create or replace function public.list_slack_imports(p_workspace uuid)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
begin
    perform aedrova_private.require_user();

    if coalesce(aedrova_private.member_role(p_workspace), '') not in ('owner', 'admin') then
        raise exception 'Workspace owner or admin required' using errcode = '42501';
    end if;

    return coalesce((
        select jsonb_agg(to_jsonb(r))
        from (
            select
                i.id,
                i.created_at,
                i.published_at,
                i.next_batch,
                (
                    select count(*)
                    from aedrova_private.slack_messages m
                    where m.workspace_id = i.workspace_id
                      and m.import_id = i.id
                ) as message_count
            from aedrova_private.slack_imports i
            where i.workspace_id = p_workspace
              and (
                  i.published_at is not null
                  or i.created_at >= now() - interval '1 day'
              )
            order by i.created_at desc
        ) r
    ), '[]'::jsonb);
end;
$$;

create or replace function public.remove_slack_import(
    p_workspace uuid,
    p_import uuid
)
returns boolean
language plpgsql
security definer
set search_path = ''
as $$
begin
    perform aedrova_private.require_user();
    perform pg_advisory_xact_lock(hashtextextended(p_workspace::text, 126923));

    if coalesce(aedrova_private.member_role(p_workspace), '') not in ('owner', 'admin') then
        raise exception 'Workspace owner or admin required' using errcode = '42501';
    end if;

    delete from aedrova_private.slack_imports
    where workspace_id = p_workspace
      and id = p_import;

    return found;
end;
$$;

revoke all on function public.write_slack_history(uuid, uuid, integer, jsonb, boolean),
    public.slack_history(uuid, text, integer),
    public.list_slack_imports(uuid),
    public.remove_slack_import(uuid, uuid)
from public, anon, authenticated;

grant execute on function public.write_slack_history(uuid, uuid, integer, jsonb, boolean),
    public.slack_history(uuid, text, integer),
    public.list_slack_imports(uuid),
    public.remove_slack_import(uuid, uuid)
to authenticated;

notify pgrst, 'reload schema';

commit;
