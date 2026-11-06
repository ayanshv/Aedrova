begin;
create or replace function public.save_shared_agent_work(p_id uuid,p_workspace uuid,p_channel uuid,
 p_agent text,p_body text,p_sources uuid[]) returns uuid
language plpgsql security definer set search_path='' as $$
declare existing public.shared_agent_work; sources uuid[];
begin
 perform aedrova_private.require_user();
 perform 1 from public.workspaces where id=p_workspace for update;
 if coalesce(aedrova_private.member_role(p_workspace),'') not in ('owner','admin','member')
 or not exists(select 1 from public.channels c where c.id=p_channel
 and c.workspace_id=p_workspace and c.kind='channel'
 and aedrova_private.can_read_channel(c.id)) then
 raise exception 'Shared work requires channel access' using errcode='42501'; end if;
 if p_id is null or p_body is null or length(btrim(p_body)) not between 1 and 20000
 or p_agent is null or length(btrim(p_agent)) not between 1 and 80
 or p_sources is null or cardinality(p_sources)>500 then
 raise exception 'Invalid shared work' using errcode='22023'; end if;
 select array_agg(distinct x order by x) into sources
 from unnest(p_sources||array[p_channel]) x;
 if exists(select 1 from unnest(sources) s(id) where s.id is null or not exists(
 select 1 from public.channels c where c.id=s.id and c.workspace_id=p_workspace
 and aedrova_private.can_read_channel(c.id))) then
 raise exception 'Shared work source access changed' using errcode='42501'; end if;
 if p_body ~ '(sb_secret_|sk-(proj-|ant-)|[sr]k_(live|test)_|whsec_|gh[pousr]_)[A-Za-z0-9_-]{20,}|-----BEGIN .*PRIVATE KEY-----' then
 raise exception 'Remove credentials before sharing work' using errcode='22023'; end if;
 perform pg_advisory_xact_lock(hashtextextended('shared-agent-work:'||p_id::text,0));
 select * into existing from public.shared_agent_work where id=p_id;
 if found then
 if existing.author_id<>auth.uid() or existing.workspace_id<>p_workspace
 or existing.channel_id<>p_channel or existing.agent_name<>p_agent
 or existing.body<>p_body or existing.source_channels<>sources then
 raise exception 'Shared work identity conflict' using errcode='42501'; end if;
 return existing.id;
 end if;
 perform aedrova_private.check_user_budget('shared-agent-work',30,60);
 insert into public.shared_agent_work(id,workspace_id,channel_id,author_id,agent_name,body,source_channels)
 values(p_id,p_workspace,p_channel,auth.uid(),p_agent,p_body,sources);
 return p_id;
end $$;
commit;
