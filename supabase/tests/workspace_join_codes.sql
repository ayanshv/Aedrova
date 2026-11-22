begin;

insert into auth.users (id, email, email_confirmed_at) values
    ('f1400000-0000-0000-0000-000000000001', 'code-owner@example.test', now()),
    ('f1400000-0000-0000-0000-000000000002', 'code-member@example.test', now()),
    ('f1400000-0000-0000-0000-000000000003', 'named@example.test', now());

set local role authenticated;
select set_config('request.jwt.claim.sub', 'f1400000-0000-0000-0000-000000000001', true);
do $$
declare workspace uuid; code text;
begin
    workspace := public.onboard_workspace('Join code fixture', 'Aedrova', 'auto');
    perform set_config('test.workspace', workspace::text, true);
    perform set_config('test.old_code', public.create_workspace_join_code(workspace), true);
    code := public.create_workspace_join_code(workspace);
    assert code ~ '^A2(-[0-9A-F]{4}){4}$';
    perform set_config('test.code', code, true);
    perform set_config('test.named', public.create_invitation(workspace, 'named@example.test', 'guest'), true);
end $$;

select set_config('request.jwt.claim.sub', 'f1400000-0000-0000-0000-000000000002', true);
do $$ begin
    perform public.accept_invitation(current_setting('test.old_code'));
    raise exception 'Rotated code was accepted';
exception when insufficient_privilege then null;
end $$;
do $$ begin
    assert public.accept_invitation(lower(current_setting('test.code'))) = current_setting('test.workspace')::uuid;
    assert public.accept_invitation(current_setting('test.code')) = current_setting('test.workspace')::uuid;
end $$;
do $$ begin
    perform public.create_workspace_join_code(current_setting('test.workspace')::uuid);
    raise exception 'Member issued a code';
exception when insufficient_privilege then null;
end $$;
select set_config('request.jwt.claim.sub', 'f1400000-0000-0000-0000-000000000003', true);
select public.accept_invitation(current_setting('test.named'));

reset role;
do $$ begin
    assert (select uses from aedrova_private.workspace_join_codes where workspace_id = current_setting('test.workspace')::uuid) = 1;
    assert (select role from public.workspace_members where workspace_id = current_setting('test.workspace')::uuid
            and user_id = 'f1400000-0000-0000-0000-000000000002') = 'member';
    assert (select role from public.workspace_members where workspace_id = current_setting('test.workspace')::uuid
            and user_id = 'f1400000-0000-0000-0000-000000000003') = 'guest';
end $$;

rollback;
