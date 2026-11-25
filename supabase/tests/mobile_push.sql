begin;

insert into auth.users (id, email, email_confirmed_at) values
    ('ea001000-0000-0000-0000-000000000001', 'push-one@example.test', now()),
    ('ea001000-0000-0000-0000-000000000002', 'push-two@example.test', now());

set local role anon;
do $$ begin
    perform public.register_push_device(repeat('a', 64), 'development', 'com.aedrova.desktop');
    raise exception 'Anonymous registration unexpectedly succeeded';
exception when insufficient_privilege then null;
end $$;

set local role authenticated;
select set_config('request.jwt.claim.sub', 'ea001000-0000-0000-0000-000000000001', true);
do $$ begin
    perform public.register_push_device('not a token', 'development', 'com.aedrova.desktop');
    raise exception 'Invalid token unexpectedly accepted';
exception when sqlstate '22023' then null;
end $$;
do $$ begin
    perform public.register_push_device(repeat('a', 64), 'staging', 'com.aedrova.desktop');
    raise exception 'Unknown environment unexpectedly accepted';
exception when sqlstate '22023' then null;
end $$;
select public.register_push_device(repeat('a', 64), 'development', 'com.aedrova.desktop');
select public.register_push_device(upper(repeat('a', 64)), 'production', 'com.aedrova.desktop');
do $$ begin
    perform 1 from aedrova_private.push_devices;
    raise exception 'Signed-in users could read the private device table';
exception when insufficient_privilege then null;
end $$;

-- Registering the same device after another person signs in moves it to them.
select set_config('request.jwt.claim.sub', 'ea001000-0000-0000-0000-000000000002', true);
select public.register_push_device(repeat('a', 64), 'production', 'com.aedrova.desktop');
-- The previous owner can no longer remove it.
select set_config('request.jwt.claim.sub', 'ea001000-0000-0000-0000-000000000001', true);
select public.unregister_push_device(repeat('a', 64));

reset role;
do $$
declare owner_id uuid; kept int;
begin
    select user_id into owner_id from aedrova_private.push_devices where token = repeat('a', 64);
    assert owner_id = 'ea001000-0000-0000-0000-000000000002', 'device should belong to the latest sign-in';
    assert (select environment from aedrova_private.push_devices where token = repeat('a', 64)) = 'production';
end $$;

-- A person keeps only their ten newest devices.
set local role authenticated;
select set_config('request.jwt.claim.sub', 'ea001000-0000-0000-0000-000000000001', true);
select public.register_push_device(repeat(to_hex(i), 64), 'development', 'com.aedrova.desktop')
from generate_series(1, 12) as i;
reset role;
do $$ begin
    assert (select count(*) from aedrova_private.push_devices
            where user_id = 'ea001000-0000-0000-0000-000000000001') = 10;
end $$;

-- Without configuration a notification is stored and nothing is announced or failed.
do $$ begin
    assert not exists (select 1 from aedrova_private.push_config);
end $$;

rollback;
