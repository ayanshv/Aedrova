begin;
-- Shared local-build evidence, never a grant to execute/publish code.
create table public.build_reviews (
 id uuid primary key,
 workspace_id uuid not null references public.workspaces(id) on delete cascade,
 channel_id uuid not null references public.channels(id) on delete cascade,
 author_id uuid not null references auth.users(id),
 source_channels uuid[] not null,
 evidence jsonb not null,
 version integer not null default 1,
 created_at timestamptz not null default clock_timestamp(),
 updated_at timestamptz not null default clock_timestamp(),
 check(cardinality(source_channels) between 1 and 500),
 check(octet_length(evidence::text)<=300000)
);
create index build_review_workspace on public.build_reviews(workspace_id,updated_at desc);
create table public.build_review_decisions (
 id uuid primary key, build_id uuid not null references public.build_reviews(id) on delete cascade,
 reviewer_id uuid not null references auth.users(id), build_version integer not null,
 decision text not null check(decision in ('comment','approved','changes_requested')),
 note text not null check(char_length(note) between 1 and 4000),
 created_at timestamptz not null default clock_timestamp()
);
create table public.build_delivery_receipts (
 id uuid primary key, build_id uuid not null references public.build_reviews(id) on delete cascade,
 actor_id uuid not null references auth.users(id), kind text not null,
 reference text not null, review_digest text not null, created_at timestamptz not null default clock_timestamp(),
 unique(build_id,kind,reference)
);
alter table public.build_delivery_receipts enable row level security;
revoke all on public.build_delivery_receipts from public,anon,authenticated;
grant select on public.build_delivery_receipts to authenticated;
alter table public.build_reviews enable row level security;
alter table public.build_review_decisions enable row level security;
revoke all on public.build_reviews,public.build_review_decisions from public,anon,authenticated;
grant select on public.build_reviews,public.build_review_decisions to authenticated;

create function aedrova_private.can_read_build(p_workspace uuid,p_channels uuid[],p_evidence jsonb)
returns boolean language plpgsql stable security definer set search_path='' as $$
declare c uuid; r jsonb;
begin
 if coalesce(aedrova_private.member_role(p_workspace),'') not in ('owner','admin','member') then return false; end if;
 foreach c in array p_channels loop
 if not exists(select 1 from public.channels where id=c and workspace_id=p_workspace)
 or not aedrova_private.can_read_channel(c) then return false; end if;
 end loop;
 for r in select value from jsonb_array_elements(p_evidence->'requirements') loop
 if not exists(select 1 from public.product_memory m where m.id=(r->>'id')::uuid
 and m.workspace_id=p_workspace and m.channel_id=any(p_channels)
 and aedrova_private.memory_visible(m.channel_id,m.sources)) then return false; end if;
 end loop;
 return true;
end $$;
revoke all on function aedrova_private.can_read_build(uuid,uuid[],jsonb) from public,anon;
grant execute on function aedrova_private.can_read_build(uuid,uuid[],jsonb) to authenticated;
create policy build_review_read on public.build_reviews for select to authenticated
 using(aedrova_private.can_read_build(workspace_id,source_channels,evidence));
create policy build_decision_read on public.build_review_decisions for select to authenticated
 using(exists(select 1 from public.build_reviews b where b.id=build_id));

create policy build_receipt_read on public.build_delivery_receipts for select to authenticated
 using(exists(select 1 from public.build_reviews b where b.id=build_id));

create function public.save_build_review(p_id uuid,p_workspace uuid,p_channel uuid,
 p_sources uuid[],p_version integer,p_evidence jsonb) returns integer
language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); old public.build_reviews; r jsonb; f jsonb; k jsonb;
 m public.product_memory; next_version integer;
begin
 perform aedrova_private.check_user_budget('build-evidence',30,60);
 perform 1 from public.workspaces where id=p_workspace for update;
 if p_sources is null or cardinality(p_sources) not between 1 and 500
 or array_position(p_sources,null) is not null or not p_channel=any(p_sources)
 or not aedrova_private.can_read_build(p_workspace,p_sources,p_evidence) then
 raise exception 'Build source access required' using errcode='42501'; end if;
 if jsonb_typeof(p_evidence)<>'object' or octet_length(p_evidence::text)>300000
 or coalesce(char_length(trim(p_evidence->>'task')),0) not between 1 and 20000
 or coalesce(jsonb_typeof(p_evidence->'requirements'),'')<>'array'
 or coalesce(jsonb_typeof(p_evidence->'files'),'')<>'array'
 or coalesce(jsonb_typeof(p_evidence->'checks'),'')<>'array'
 or coalesce(jsonb_typeof(p_evidence->'acceptance_criteria'),'')<>'array'
 or jsonb_array_length(p_evidence->'requirements')>200
 or jsonb_array_length(p_evidence->'files')>200 or jsonb_array_length(p_evidence->'checks')>100
 or jsonb_array_length(p_evidence->'acceptance_criteria')>50
 or coalesce(p_evidence->>'review_digest','') !~ '^[a-f0-9]{64}$'
 or coalesce(p_evidence->>'project_fingerprint','') !~ '^[a-f0-9]{64}$'
 or p_evidence::text ~ '(sb_secret_|sk-(proj-|ant-)|[sr]k_(live|test)_|whsec_|gh[pousr]_)[A-Za-z0-9_-]{20,}|-----BEGIN .*PRIVATE KEY-----'
 then raise exception 'Invalid or unsafe build evidence' using errcode='22023'; end if;
 if exists(select 1 from jsonb_array_elements(p_evidence->'acceptance_criteria') c
 where jsonb_typeof(c)<>'string' or char_length(c #>> '{}') not between 1 and 2000)
 or (select count(*) from jsonb_array_elements(p_evidence->'files')) <>
 (select count(distinct file_item->>'path') from jsonb_array_elements(p_evidence->'files') file_item)
 or (select count(*) from jsonb_array_elements(p_evidence->'checks')) <>
 (select count(distinct check_item->>'id') from jsonb_array_elements(p_evidence->'checks') check_item)
 then raise exception 'Invalid criteria or duplicate evidence' using errcode='22023'; end if;
 for f in select value from jsonb_array_elements(p_evidence->'files') loop
 if coalesce(f->>'path','')='' or f->>'path' ~ '(^/|(^|/)\.\.(/|$)|\\)'
 or char_length(f->>'path')>1000 or char_length(f->>'diff')>10000 then
 raise exception 'Invalid file evidence' using errcode='22023'; end if;
 end loop;
 for k in select value from jsonb_array_elements(p_evidence->'checks') loop
 if coalesce(k->>'id','') !~ '^[a-f0-9]{64}$'
 or coalesce(k->>'state','') not in ('passed','failed','unverified')
 or char_length(k->>'command')>2000 or char_length(k->>'output')>8000
 or coalesce(jsonb_typeof(k->'exit_code'),'null') not in ('number','null')
 or (k->>'state'='unverified' and coalesce(jsonb_typeof(k->'exit_code'),'null')<>'null')
 or (k->>'state'='passed' and (k->>'exit_code') is distinct from '0')
 or (k->>'state'='failed' and ((k->>'exit_code') is null or k->>'exit_code'='0'))
 then raise exception 'Invalid command evidence' using errcode='22023'; end if;
 end loop;
 for r in select value from jsonb_array_elements(p_evidence->'requirements') loop
 select * into m from public.product_memory where id=(r->>'id')::uuid for update;
 if m.id is null or m.version is distinct from (r->>'version')::integer or m.state<>'approved'
 or m.title is distinct from r->>'title' or m.body is distinct from r->>'body'
 or m.sources is distinct from r->'sources' or m.channel_id is distinct from (r->>'channel_id')::uuid
 or m.kind is distinct from r->>'kind'
 or exists(select 1 from jsonb_array_elements(m.sources) s where
 aedrova_private.memory_source(s->>'kind',(s->>'id')::uuid)->>'fingerprint' is distinct from s->>'fingerprint')
 then raise exception 'Requirement changed. Gather fresh evidence.' using errcode='PT409'; end if;
 if coalesce(r->>'assessment','') not in ('not_assessed','needs_work','reviewer_verified')
 or coalesce(jsonb_typeof(r->'files'),'')<>'array' or coalesce(jsonb_typeof(r->'checks'),'')<>'array'
 or exists(select 1 from jsonb_array_elements_text(r->'files') path where not exists(
 select 1 from jsonb_array_elements(p_evidence->'files') file where file->>'path'=path))
 or exists(select 1 from jsonb_array_elements_text(r->'checks') cid where not exists(
 select 1 from jsonb_array_elements(p_evidence->'checks') ck where ck->>'id'=cid))
 then raise exception 'Invalid requirement evidence links' using errcode='22023'; end if;
 if r->>'assessment'='reviewer_verified' and (jsonb_array_length(r->'files')=0
 or jsonb_array_length(r->'checks')=0 or exists(select 1 from jsonb_array_elements_text(r->'checks') cid
 join jsonb_array_elements(p_evidence->'checks') ck on ck->>'id'=cid where ck->>'state'<>'passed' or ck->>'project_fingerprint' is distinct from p_evidence->>'project_fingerprint'))
 then raise exception 'Verification needs changed files and passed linked checks' using errcode='22023'; end if;
 end loop;
 select * into old from public.build_reviews where id=p_id for update;
 if old.id is not null and (old.workspace_id<>p_workspace or old.channel_id<>p_channel
 or old.author_id<>u) then raise exception 'Only the original author can revise evidence' using errcode='42501'; end if;
 if old.id is not null and old.version=p_version+1 and old.evidence=p_evidence
 and old.source_channels=p_sources then return old.version; end if;
 if coalesce(old.version,0) is distinct from p_version then
 raise exception 'Build review changed. Refresh first.' using errcode='PT409'; end if;
 next_version:=coalesce(old.version,0)+1;
 insert into public.build_reviews(id,workspace_id,channel_id,author_id,source_channels,evidence,version)
 values(p_id,p_workspace,p_channel,u,p_sources,p_evidence,next_version)
 on conflict(id) do update set evidence=excluded.evidence,source_channels=excluded.source_channels,
 version=excluded.version,updated_at=clock_timestamp();
 if old.id is null and cardinality(p_sources)=1 then
 perform public.send_message(p_id,p_channel,
 'Build evidence is ready for review. Open Builds → Shared build reviews.');
 end if;
 return next_version;
end $$;

create function public.decide_build_review(p_id uuid,p_build uuid,p_version integer,p_decision text,p_note text)
returns uuid language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); b public.build_reviews; old public.build_review_decisions;
begin
 perform aedrova_private.check_user_budget('build-review-decision',60,60);
 select * into b from public.build_reviews where id=p_build for update;
 if b.id is null or not aedrova_private.can_read_build(b.workspace_id,b.source_channels,b.evidence) then
 raise exception 'Build access required' using errcode='42501'; end if;
 if b.version is distinct from p_version then raise exception 'Review changed. Refresh first.' using errcode='PT409'; end if;
 if p_note ~ '(sb_secret_|sk-(proj-|ant-)|[sr]k_(live|test)_|whsec_|gh[pousr]_)[A-Za-z0-9_-]{20,}|-----BEGIN .*PRIVATE KEY-----' then
 raise exception 'Remove credentials from review notes' using errcode='22023'; end if;
 if p_decision not in ('comment','approved','changes_requested') or char_length(trim(p_note)) not between 1 and 4000 then
 raise exception 'A review note is required' using errcode='22023'; end if;
 if p_decision='approved' and (jsonb_array_length(b.evidence->'requirements')=0
 or exists(select 1 from jsonb_array_elements(b.evidence->'requirements') r where r->>'assessment'<>'reviewer_verified')
 or exists(select 1 from jsonb_array_elements(b.evidence->'requirements') r join public.product_memory m on m.id=(r->>'id')::uuid
 where m.version<>(r->>'version')::integer or m.state<>'approved'
 or exists(select 1 from jsonb_array_elements(m.sources) s where
 aedrova_private.memory_source(s->>'kind',(s->>'id')::uuid)->>'fingerprint' is distinct from s->>'fingerprint')))
 then raise exception 'Review current requirements and link real evidence before approval' using errcode='PT409'; end if;
 select * into old from public.build_review_decisions where id=p_id;
 if old.id is not null then
 if old.build_id<>p_build or old.reviewer_id<>u or old.build_version<>p_version
 or old.decision<>p_decision or old.note<>trim(p_note) then
 raise exception 'Review action identifier already used' using errcode='PT409'; end if;
 return p_id; end if;
 insert into public.build_review_decisions(id,build_id,reviewer_id,build_version,decision,note)
 values(p_id,p_build,u,p_version,p_decision,trim(p_note));
 return p_id;
end $$;
create function public.record_build_delivery(p_id uuid,p_build uuid,p_digest text,p_kind text,p_reference text)
returns uuid language plpgsql security definer set search_path='' as $$
declare u uuid:=aedrova_private.require_user(); b public.build_reviews; saved uuid;
begin
 perform aedrova_private.check_user_budget('build-delivery-receipt',30,60);
 select * into b from public.build_reviews where id=p_build for update;
 if b.id is null or b.author_id<>u or not aedrova_private.can_read_build(b.workspace_id,b.source_channels,b.evidence) then
 raise exception 'Original build author access required' using errcode='42501'; end if;
 if b.evidence->>'review_digest' is distinct from p_digest then
 raise exception 'Delivery does not match shared evidence' using errcode='PT409'; end if;
 if p_kind not in ('local_apply','draft_pr','branch')
 or (p_kind='local_apply' and p_reference<>'Reviewed changes applied locally')
 or (p_kind='draft_pr' and p_reference !~ '^https://github.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/pull/[1-9][0-9]*$')
 or (p_kind='branch' and p_reference !~ '^https://github.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/tree/[A-Za-z0-9_./-]+$')
 or char_length(p_reference)>1000 then raise exception 'Invalid delivery receipt' using errcode='22023'; end if;
 if p_kind<>'local_apply' and aedrova_private.member_role(b.workspace_id) not in ('owner','admin') then
 raise exception 'Owner or admin publication receipt required' using errcode='42501'; end if;
 insert into public.build_delivery_receipts(id,build_id,actor_id,kind,reference,review_digest)
 values(p_id,p_build,u,p_kind,p_reference,p_digest)
 on conflict(build_id,kind,reference) do nothing;
 select id into saved from public.build_delivery_receipts where build_id=p_build and kind=p_kind and reference=p_reference;
 return saved;
end $$;
revoke all on function public.record_build_delivery(uuid,uuid,text,text,text) from public,anon;
grant execute on function public.record_build_delivery(uuid,uuid,text,text,text) to authenticated;

-- Withdrawn memory removes its derived shared evidence, including review notes.
create function aedrova_private.purge_memory_build_reviews() returns trigger
language plpgsql security definer set search_path='' as $$
begin
 delete from public.build_reviews b where exists(select 1 from jsonb_array_elements(b.evidence->'requirements') r
 where r->>'id'=old.id::text);
 return null;
end $$;
create trigger memory_build_withdrawal after delete on public.product_memory
 for each row execute function aedrova_private.purge_memory_build_reviews();
revoke all on function aedrova_private.purge_memory_build_reviews() from public,anon,authenticated;
revoke all on function public.save_build_review(uuid,uuid,uuid,uuid[],integer,jsonb),
 public.decide_build_review(uuid,uuid,integer,text,text) from public,anon;
grant execute on function public.save_build_review(uuid,uuid,uuid,uuid[],integer,jsonb),
 public.decide_build_review(uuid,uuid,integer,text,text) to authenticated;
commit;
