begin;
-- Existing authenticated owner/admin RPC and RLS remain authoritative.
alter table public.workspace_agent_preferences
 drop constraint workspace_agent_preferences_provider_check;
alter table public.workspace_agent_preferences
 add constraint workspace_agent_preferences_provider_check
 check (provider in ('codex','claude_code','auto'));
commit;
