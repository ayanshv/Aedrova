begin;
create table public.product_memory (
 id uuid primary key default gen_random_uuid(),
 workspace_id uuid not null references public.workspaces(id) on delete cascade,
 channel_id uuid not null references public.channels(id) on delete cascade,
 kind text not null check(kind in ('goal','requirement','constraint','decision','question')),
 title text not null check(char_length(title) between 1 and 160),
 body text not null check(char_length(body) between 1 and 8000),
 state text not null check(state in ('proposal','approved','conflict','retired','superseded')),
 sources jsonb not null check(jsonb_typeof(sources)='array' and jsonb_array_length(sources) between 1 and 16),
 conflict_id uuid references public.product_memory(id) on delete set null,
 supersedes uuid references public.product_memory(id) on delete set null,
 version integer not null default 1 check(version>0),
 updated_by uuid not null references auth.users(id),
 updated_at timestamptz not null default clock_timestamp()
);
create index memory_workspace on public.product_memory(workspace_id,updated_at desc,id);
create index memory_channel on public.product_memory(channel_id);
create index memory_search on public.product_memory using gin(to_tsvector('simple',title||' '||body));
create table public.product_memory_history (
 memory_id uuid not null references public.product_memory(id) on delete cascade,
 version integer not null,
 record jsonb not null,
 changed_at timestamptz not null default clock_timestamp(),
 primary key(memory_id,version)
);
alter table public.product_memory enable row level security;
alter table public.product_memory_history enable row level security;
revoke all on public.product_memory, public.product_memory_history from public,anon,authenticated;
grant select on public.product_memory, public.product_memory_history to authenticated;

-- Sources are resolved each time, not cached permission claims from an import/client.
create function aedrova_private.memory_source(p_kind text,p_id uuid) returns jsonb
language plpgsql stable security definer set search_path='' as $$
declare c uuid; b text; citation text; extra jsonb:='{}';
begin
 if p_kind='message' then
 select channel_id,body into c,b from public.messages where id=p_id and unsent_at is null;
 elsif p_kind='attachment' then
 select m.channel_id,a.filename||':'||a.byte_size::text||':'||a.sha256||':'||a.object_path,
 jsonb_build_object('filename',a.filename,'message_id',m.id) into c,b,extra
 from public.attachments a join public.messages m on m.id=a.message_id
 where a.id=p_id and m.unsent_at is null;
 elsif p_kind='meeting' then
 -- Meeting context is optional. Never expose unreviewed provider speech when
 -- the later speech-review migration has not been installed either.
 if to_regclass('public.meeting_transcript_segments') is null then return null; end if;
 select t.channel_id,coalesce(to_jsonb(t)->>'review_body',t.body),
 jsonb_build_object('meeting_id',t.meeting_id,'offset_ms',t.offset_ms)
 into c,b,extra from public.meeting_transcript_segments t
 where t.id=p_id and t.ai_allowed and t.expires_at>clock_timestamp()
 and (t.source='participant_text' or to_jsonb(t)->>'reviewed_at' is not null);
 else return null;
 end if;
 if c is null or not aedrova_private.can_read_channel(c) then return null; end if;
 citation:=p_kind||':'||p_id::text;
 return jsonb_build_object('kind',p_kind,'id',p_id,'channel_id',c,'fingerprint',encode(sha256(convert_to(b,'UTF8')),'hex'),
 'citation',citation,'body',b)||extra;
end $$;
revoke all on function aedrova_private.memory_source(text,uuid) from public,anon,authenticated;

create function aedrova_private.memory_visible(p_channel uuid,p_sources jsonb) returns boolean
language plpgsql stable security definer set search_path='' as $$
declare s jsonb;
begin
 if not aedrova_private.can_read_channel(p_channel) then return false; end if;
 for s in select value from jsonb_array_elements(p_sources) loop
 if aedrova_private.memory_source(s->>'kind',(s->>'id')::uuid) is null then return false; end if;
 end loop;
 return true;
end $$;
revoke all on function aedrova_private.memory_visible(uuid,jsonb) from public,anon;
grant execute on function aedrova_private.memory_visible(uuid,jsonb) to authenticated;
create policy memory_read on public.product_memory for select to authenticated
 using(aedrova_private.memory_visible(channel_id,sources));
create policy memory_history_read on public.product_memory_history for select to authenticated
 using(exists(select 1 from public.product_memory m where m.id=memory_id
 and aedrova_private.memory_visible(m.channel_id,m.sources))
 and aedrova_private.memory_visible((record->>'channel_id')::uuid,record->'sources'));

create function public.memory_source(p_kind text,p_id uuid) returns jsonb
language plpgsql stable security definer set search_path='' as $$
begin
 perform aedrova_private.require_user();
 return aedrova_private.memory_source(p_kind,p_id);
end $$;

create function public.memory_list(p_workspace uuid,p_query text default '',p_limit integer default 200,p_active boolean default false)
returns jsonb language plpgsql stable security definer set search_path='' as $$
declare results jsonb; total bigint;
begin
 perform aedrova_private.require_user();
 if coalesce(aedrova_private.member_role(p_workspace),'') not in ('owner','admin','member') then
 raise exception 'Workspace access required' using errcode='42501'; end if;
 select count(*) into total from public.product_memory m where workspace_id=p_workspace
 and aedrova_private.memory_visible(channel_id,sources)
 and (not coalesce(p_active,false) or state not in ('retired','superseded'))
 and (coalesce(trim(p_query),'')='' or to_tsvector('simple',title||' '||body) @@ plainto_tsquery('simple',left(p_query,1000)));
 select coalesce(jsonb_agg(item order by updated_at desc,id),'[]') into results from (
 select m.id,m.updated_at,to_jsonb(m)||jsonb_build_object('fresh',not exists(
 select 1 from jsonb_array_elements(m.sources) s where
 aedrova_private.memory_source(s->>'kind',(s->>'id')::uuid)->>'fingerprint' is distinct from s->>'fingerprint'),
 'resolved_sources',(select jsonb_agg(aedrova_private.memory_source(s->>'kind',(s->>'id')::uuid))
 from jsonb_array_elements(m.sources) s)) item from public.product_memory m
 where workspace_id=p_workspace and aedrova_private.memory_visible(channel_id,sources)
 and (not coalesce(p_active,false) or state not in ('retired','superseded'))
 and (coalesce(trim(p_query),'')='' or to_tsvector('simple',title||' '||body) @@ plainto_tsquery('simple',left(p_query,1000)))
 order by updated_at desc,id limit greatest(1,least(coalesce(p_limit,200),200))) x;
 return jsonb_build_object('items',results,'total',total,'truncated',total>jsonb_array_length(results));
end $$;

create function public.save_product_memory(p_id uuid,p_workspace uuid,p_channel uuid,p_version integer,
 p_kind text,p_title text,p_body text,p_state text,p_sources jsonb,p_conflict uuid default null,
 p_supersedes uuid default null,p_supersedes_version integer default null) returns uuid
language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); old public.product_memory;
 target public.product_memory; s jsonb; resolved jsonb; saved public.product_memory; clean jsonb:='[]';
begin
 perform aedrova_private.check_user_budget('memory-save',60,60);
 perform pg_advisory_xact_lock(hashtextextended(p_id::text,1));
 perform 1 from public.workspaces where id=p_workspace for update;
 if coalesce(aedrova_private.member_role(p_workspace),'') not in ('owner','admin','member')
 or not exists(select 1 from public.channels where id=p_channel and workspace_id=p_workspace)
 or not aedrova_private.can_read_channel(p_channel) then raise exception 'Not allowed' using errcode='42501'; end if;
 if p_state not in ('proposal','approved','conflict','retired') or p_kind not in
 ('goal','requirement','constraint','decision','question') or p_sources is null
 or jsonb_typeof(p_sources)<>'array' or jsonb_array_length(p_sources) not between 1 and 16
 or char_length(trim(p_title)) not between 1 and 160 or char_length(trim(p_body)) not between 1 and 8000 then
 raise exception 'Invalid memory entry' using errcode='22023'; end if;
 for s in select value from jsonb_array_elements(p_sources) loop
 if s->>'kind'='message' then
 perform 1 from public.messages where id=(s->>'id')::uuid for update;
 elsif s->>'kind'='attachment' then
 perform 1 from public.attachments where id=(s->>'id')::uuid for update;
 perform 1 from public.messages where id=(select message_id from public.attachments where id=(s->>'id')::uuid) for update;
 elsif s->>'kind'='meeting' then
 if to_regclass('public.meeting_transcript_segments') is null then
 raise exception 'Source access required' using errcode='42501'; end if;
 perform 1 from public.meeting_transcript_segments where id=(s->>'id')::uuid for update;
 end if;
 resolved:=aedrova_private.memory_source(s->>'kind',(s->>'id')::uuid);
 if resolved is null or resolved->>'channel_id'<>p_channel::text then raise exception 'Source access required' using errcode='42501'; end if;
 if resolved->>'fingerprint' is distinct from s->>'fingerprint' then
 raise exception 'Source changed. Review current evidence first.' using errcode='PT409'; end if;
 clean:=clean||jsonb_build_array(jsonb_build_object('kind',s->>'kind','id',s->>'id','fingerprint',s->>'fingerprint'));
 end loop;
 p_sources:=clean;
 if p_kind='question' and p_state='approved' then raise exception 'Resolve the question before approval'; end if;
 select * into old from public.product_memory where id=p_id for update;
 if old.id is not null then
 if old.workspace_id<>p_workspace or old.channel_id<>p_channel
 or not aedrova_private.memory_visible(old.channel_id,old.sources) then raise exception 'Not allowed' using errcode='42501'; end if;
 if old.version<>p_version then raise exception 'Memory changed. Refresh before saving.' using errcode='PT409'; end if;
 if old.state='superseded' then raise exception 'Create a new proposal for a superseded entry'; end if;
 elsif coalesce(p_version,0)<>0 then raise exception 'Memory entry no longer exists' using errcode='PT409'; end if;
 if p_conflict is not null then
 select * into target from public.product_memory where id=p_conflict;
 if target.id is null or target.id=p_id or target.workspace_id<>p_workspace
 or target.channel_id<>p_channel or not aedrova_private.memory_visible(target.channel_id,target.sources) then
 raise exception 'Conflict source not accessible' using errcode='42501'; end if;
 if p_state='approved' then raise exception 'Resolve the conflict before approval'; end if;
 elsif p_state='conflict' then raise exception 'Select the conflicting entry first'; end if;
 if p_supersedes is not null then
 select * into target from public.product_memory where id=p_supersedes for update;
 if target.id is null or target.id=p_id or target.workspace_id<>p_workspace or target.channel_id<>p_channel
 or not aedrova_private.memory_visible(target.channel_id,target.sources) then raise exception 'Superseded source not accessible' using errcode='42501'; end if;
 if target.version is distinct from p_supersedes_version or target.state='superseded' then
 raise exception 'Replacement target changed. Refresh first.' using errcode='PT409'; end if;
 if p_state<>'approved' then raise exception 'Approve the replacement before superseding'; end if;
 update public.product_memory set state='superseded',version=version+1,updated_by=u,updated_at=clock_timestamp()
 where id=target.id returning * into target;
 insert into public.product_memory_history(memory_id,version,record) values(target.id,target.version,to_jsonb(target));
 end if;
 insert into public.product_memory(id,workspace_id,channel_id,kind,title,body,state,sources,conflict_id,supersedes,updated_by)
 values(p_id,p_workspace,p_channel,p_kind,trim(p_title),trim(p_body),p_state,p_sources,p_conflict,p_supersedes,u)
 on conflict(id) do update set kind=excluded.kind,title=excluded.title,body=excluded.body,state=excluded.state,
 sources=excluded.sources,conflict_id=excluded.conflict_id,supersedes=coalesce(excluded.supersedes,product_memory.supersedes),
 version=product_memory.version+1,updated_by=u,updated_at=clock_timestamp() returning * into saved;
 insert into public.product_memory_history(memory_id,version,record) values(saved.id,saved.version,to_jsonb(saved));
 return saved.id;
end $$;
create trigger product_memory_revision after insert or update or delete on public.product_memory
 for each row execute function aedrova_private.bump_context_revision();
-- Remove derived copies/history when the user deletes or withdraws their source.
create function aedrova_private.purge_source_memory() returns trigger
language plpgsql security definer set search_path='' as $$
declare k text; identifier uuid;
begin
 if tg_table_name='messages' then
 k:='message'; identifier:=old.id;
 if tg_op='UPDATE' and new.unsent_at is null then return null; end if;
 elsif tg_table_name='attachments' then k:='attachment'; identifier:=old.id;
 else
 k:='meeting'; identifier:=old.id;
 if tg_op='UPDATE' and new.ai_allowed then return null; end if;
 end if;
 delete from public.product_memory m where exists(select 1 from jsonb_array_elements(m.sources) s
 where (s->>'kind'=k and s->>'id'=identifier::text) or
 (k='message' and s->>'kind'='attachment' and exists(select 1 from public.attachments a
 where a.id::text=s->>'id' and a.message_id=identifier)));
 return null;
end $$;
revoke all on function aedrova_private.purge_source_memory() from public,anon,authenticated;
create trigger memory_message_delete after delete or update of unsent_at on public.messages
 for each row execute function aedrova_private.purge_source_memory();
create trigger memory_attachment_delete after delete on public.attachments
 for each row execute function aedrova_private.purge_source_memory();
-- Attach only if optional meeting context is already installed. Its migration
-- also attaches this trigger when meeting context is installed after memory.
do $$ begin
 if to_regclass('public.meeting_transcript_segments') is not null then
 execute 'create trigger memory_meeting_withdrawal after delete or update of ai_allowed
 on public.meeting_transcript_segments for each row execute function aedrova_private.purge_source_memory()';
 end if;
end $$;
revoke all on function public.memory_source(text,uuid),public.memory_list(uuid,text,integer,boolean),
 public.save_product_memory(uuid,uuid,uuid,integer,text,text,text,text,jsonb,uuid,uuid,integer) from public,anon;
grant execute on function public.memory_source(text,uuid),public.memory_list(uuid,text,integer,boolean),
 public.save_product_memory(uuid,uuid,uuid,integer,text,text,text,text,jsonb,uuid,uuid,integer) to authenticated;
commit;
