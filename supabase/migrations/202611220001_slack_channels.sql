-- Adds the "From Slack" channel list and read-only channel pages, and ranks Slack search
-- results by relevance. Safe to run more than once. Run after 202611210001_slack_history.sql.
begin;

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
            order by
                case when numnode(q) = 0 then 0 else ts_rank(
                    to_tsvector('simple', m.channel_name || ' ' || m.author || ' ' || m.body), q
                ) end desc,
                m.source_ts desc,
                m.channel_id
            limit least(greatest(coalesce(p_limit, 50), 1), 100)
        ) r
    ), '[]'::jsonb);
end;
$$;

create or replace function public.slack_channels(p_workspace uuid)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
begin
    perform aedrova_private.require_user();

    if coalesce(aedrova_private.member_role(p_workspace), '')
       not in ('owner', 'admin', 'member') then
        raise exception 'Workspace membership required' using errcode = '42501';
    end if;

    return coalesce((
        select jsonb_agg(to_jsonb(r) order by r.channel_name)
        from (
            select
                m.channel_id,
                min(m.channel_name) as channel_name,
                count(*) as message_count,
                min(m.source_ts)::text as oldest,
                max(m.source_ts)::text as newest
            from aedrova_private.slack_messages m
            join aedrova_private.slack_imports i
              on i.workspace_id = m.workspace_id
             and i.id = m.import_id
            where m.workspace_id = p_workspace
              and i.published_at is not null
            group by m.channel_id
        ) r
    ), '[]'::jsonb);
end;
$$;

create or replace function public.slack_channel_messages(
    p_workspace uuid,
    p_channel text,
    p_before numeric default null,
    p_limit integer default 100
)
returns jsonb
language plpgsql
stable
security definer
set search_path = ''
as $$
begin
    perform aedrova_private.require_user();

    if coalesce(aedrova_private.member_role(p_workspace), '')
       not in ('owner', 'admin', 'member') then
        raise exception 'Workspace membership required' using errcode = '42501';
    end if;

    if p_channel is null or p_channel !~ '^C[A-Z0-9]{1,39}$' then
        raise exception 'Invalid Slack channel' using errcode = '22023';
    end if;

    return coalesce((
        select jsonb_agg(to_jsonb(r) order by r.source_ts::numeric, r.id)
        from (
            select
                'slack:' || m.channel_id || ':' || m.source_ts as id,
                m.channel_name,
                m.author,
                m.body,
                m.source_ts::text,
                m.thread_ts::text,
                m.links,
                m.reactions
            from aedrova_private.slack_messages m
            join aedrova_private.slack_imports i
              on i.workspace_id = m.workspace_id
             and i.id = m.import_id
            where m.workspace_id = p_workspace
              and i.published_at is not null
              and m.channel_id = p_channel
              and (p_before is null or m.source_ts < p_before)
            order by m.source_ts desc
            limit least(greatest(coalesce(p_limit, 100), 1), 200)
        ) r
    ), '[]'::jsonb);
end;
$$;

revoke all on function public.slack_history(uuid, text, integer),
    public.slack_channels(uuid),
    public.slack_channel_messages(uuid, text, numeric, integer)
from public, anon, authenticated;

grant execute on function public.slack_history(uuid, text, integer),
    public.slack_channels(uuid),
    public.slack_channel_messages(uuid, text, numeric, integer)
to authenticated;

notify pgrst, 'reload schema';

commit;
