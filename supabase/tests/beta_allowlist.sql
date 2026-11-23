begin;
insert into auth.users(id,email,email_confirmed_at) values
 ('b3100000-0000-0000-0000-000000000001','Listed.Person+tag@gmail.com',now()),
 ('b3100000-0000-0000-0000-000000000002','other@example.test',now());

do $$
declare
 listed text := 'b3100000-0000-0000-0000-000000000001';
 other text := 'b3100000-0000-0000-0000-000000000002';
begin
 -- Gate off: everyone confirmed passes, and the status says so.
 perform set_config('request.jwt.claim.sub', other, true);
 set local role authenticated;
 assert aedrova_private.require_user() = other::uuid;
 assert public.beta_access_status() = '{"gate": false, "allowed": true}'::jsonb;
 reset role;

 -- Gate on with one listed address, entered with different dots, case and a tag.
 insert into aedrova_private.beta_access(email,note) values ('LISTED.person@gmail.com','test');
 assert (select email from aedrova_private.beta_access) = 'listedperson@gmail.com';
 update aedrova_private.beta_gate set enabled = true;

 perform set_config('request.jwt.claim.sub', listed, true);
 set local role authenticated;
 assert aedrova_private.require_user() = listed::uuid;
 assert public.beta_access_status() = '{"gate": true, "allowed": true}'::jsonb;
 reset role;

 perform set_config('request.jwt.claim.sub', other, true);
 set local role authenticated;
 assert public.beta_access_status() = '{"gate": true, "allowed": false}'::jsonb;
 begin
   perform public.onboard_workspace('Blocked','Aedrova','codex');
   raise exception 'unlisted email created a workspace';
 exception when insufficient_privilege then null;
 end;
 -- Nobody can read or edit the list from the client.
 begin
   perform count(*) from aedrova_private.beta_access;
   raise exception 'client could read the allowlist';
 exception when insufficient_privilege then null;
 end;
 reset role;

 -- Turning the gate off restores access without touching the list.
 update aedrova_private.beta_gate set enabled = false;
 perform set_config('request.jwt.claim.sub', other, true);
 set local role authenticated;
 assert aedrova_private.require_user() = other::uuid;
 reset role;
end $$;
rollback;
