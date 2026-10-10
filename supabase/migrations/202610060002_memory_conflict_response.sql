begin;
-- Explicit stale edits are HTTP conflicts, not retryable transaction failures.
create or replace function public.save_product_memory(p_id uuid,p_workspace uuid,p_channel uuid,p_version integer,
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
commit;
