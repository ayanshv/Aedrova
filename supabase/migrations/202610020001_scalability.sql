begin;
-- Incremental hardening; preserve existing RPCs, RLS and committed-message cursors.
create index if not exists message_text_search on public.messages
 using gin(to_tsvector('simple'::regconfig,body));
create index if not exists message_thread_sequence on public.messages(channel_id,parent_id,sequence);
create index if not exists attachment_pending_uploader on public.attachments(uploader_id,expires_at)
 where message_id is null;

create or replace function public.message_page(p_channel uuid,p_before bigint default null,p_after bigint default null,
 p_parent uuid default null,p_threads boolean default false,p_limit integer default 100)
returns setof public.messages language plpgsql stable security definer set search_path='' as $$
begin
 perform aedrova_private.require_user();
 if not aedrova_private.can_read_channel(p_channel)
 then raise exception 'Not allowed' using errcode='42501'; end if;
 if p_after is not null then
 return query select * from public.messages where channel_id=p_channel
 and sequence>p_after and (p_threads or
 ((p_parent is null and parent_id is null) or parent_id=p_parent))
 order by sequence asc limit greatest(1,least(coalesce(p_limit,100),200));
 else
 return query select * from public.messages where channel_id=p_channel
 and (p_before is null or sequence<p_before) and (p_threads or
 ((p_parent is null and parent_id is null) or parent_id=p_parent))
 order by sequence desc limit greatest(1,least(coalesce(p_limit,100),200));
 end if;
end $$;


create table if not exists aedrova_private.write_budgets (
 user_id uuid not null references auth.users on delete cascade,
 bucket text not null, window_start bigint not null, count integer not null,
 primary key(user_id,bucket,window_start)
);
create index if not exists write_budget_expiry on aedrova_private.write_budgets(window_start);
revoke all on aedrova_private.write_budgets from public,anon,authenticated;
create function aedrova_private.check_user_budget(p_bucket text,p_limit integer,p_seconds integer)
returns void language plpgsql security definer set search_path='' as $$
declare u uuid:=auth.uid(); w bigint; n integer;
begin
 if u is null then return; end if;
 w:=floor(extract(epoch from clock_timestamp())/p_seconds)::bigint*p_seconds;
 insert into aedrova_private.write_budgets values(u,p_bucket,w,1)
 on conflict(user_id,bucket,window_start) do update set count=write_budgets.count+1
 returning count into n;
 if n>p_limit then raise exception 'Too many requests. Wait before retrying.' using errcode='P0001'; end if;
end $$;
revoke all on function aedrova_private.check_user_budget(text,integer,integer) from public,anon,authenticated;
create function aedrova_private.limit_user_insert() returns trigger
language plpgsql security definer set search_path='' as $$
begin
 -- Replays do not add a message; existing send_message verifies its immutable contents.
 if tg_table_name='messages' and exists(select 1 from public.messages where id=new.id)
 then return new; end if;
 perform aedrova_private.check_user_budget(tg_argv[0],tg_argv[1]::integer,tg_argv[2]::integer);
 return new;
end $$;
revoke all on function aedrova_private.limit_user_insert() from public,anon,authenticated;
create trigger rate_message before insert on public.messages for each row
 execute function aedrova_private.limit_user_insert('message','120','60');
create trigger rate_attachment before insert on public.attachments for each row
 execute function aedrova_private.limit_user_insert('attachment','20','3600');
create trigger rate_workspace before insert on public.workspaces for each row
 execute function aedrova_private.limit_user_insert('workspace','10','3600');
create trigger rate_channel before insert on public.channels for each row
 execute function aedrova_private.limit_user_insert('channel','30','60');
create trigger rate_invitation before insert on public.workspace_invitations for each row
 execute function aedrova_private.limit_user_insert('invitation','20','60');
create function public.search_workspace_context(p_workspace uuid,p_query text,p_limit integer default 100)
returns setof public.messages language plpgsql volatile security definer set search_path='' as $$
declare q tsquery;
begin
 perform aedrova_private.require_user();
 if coalesce(aedrova_private.member_role(p_workspace),'') not in ('owner','admin','member')
 then raise exception 'Not allowed' using errcode='42501'; end if;
 if length(p_query)>1000 then raise exception 'Search is too long' using errcode='22023'; end if;
 perform aedrova_private.check_user_budget('context-search',20,60);
 q:=websearch_to_tsquery('simple'::regconfig,coalesce(p_query,''));
 return query select m.* from public.messages m join public.channels c on c.id=m.channel_id
 where c.workspace_id=p_workspace and aedrova_private.can_read_channel(c.id)
 and to_tsvector('simple'::regconfig,m.body)@@q
 order by ts_rank_cd(to_tsvector('simple'::regconfig,m.body),q) desc,m.sequence desc
 limit greatest(1,least(coalesce(p_limit,100),200));
end $$;
revoke all on function public.search_workspace_context(uuid,text,integer) from public,anon;
grant execute on function public.search_workspace_context(uuid,text,integer) to authenticated;

commit;
