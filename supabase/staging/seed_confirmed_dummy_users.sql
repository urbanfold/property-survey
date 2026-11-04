-- CONFIGURED DUMMY SEED: review and run ONCE in Urbanfold-Survey-Staging only.
-- Target Dashboard reference: hexhtduvqzleoazusskh. The settings below do NOT verify the server reference.
-- No SQL executed by this preparation. No Stripe call, paid credit, email or Storage object created.
set urbanfold.staging_setup = 'Urbanfold-Survey-Staging';
set urbanfold.dummy_a = 'd72b4323-d71b-4b87-b78a-09896647fddf';
set urbanfold.dummy_b = '9036b71c-4f09-4d1b-9dce-519533c4001e';

-- OPTIONAL, PREPARED ONLY. After approval and verified setup, not part of setup.sql.
-- Create TWO NEW staging Auth users through the staging Dashboard first. Never insert auth.users directly.
-- Supply their staging UUIDs in this same SQL session before running:
-- set urbanfold.staging_setup = 'Urbanfold-Survey-Staging';
-- set urbanfold.dummy_a = '<NEW_STAGING_AUTH_USER_A_UUID>';
-- set urbanfold.dummy_b = '<NEW_STAGING_AUTH_USER_B_UUID>';
-- No passwords/tokens/real contacts belong in this file. Run once, no cleanup/reset included.
begin;
do $$
declare a uuid := nullif(current_setting('urbanfold.dummy_a',true),'')::uuid;
 b uuid := nullif(current_setting('urbanfold.dummy_b',true),'')::uuid;
begin
 if current_setting('urbanfold.staging_setup',true) is distinct from 'Urbanfold-Survey-Staging'
 or obj_description('public.properties'::regclass,'pg_class') is distinct from
 'Urbanfold-Survey-Staging reconstructed baseline; prepared 2026-11-03; never production.' then
  raise exception 'Not an acknowledged reconstructed staging baseline.';
 end if;
 if a is null or b is null or a=b then raise exception 'Supply two distinct NEW staging Auth UUIDs.'; end if;
 if (select count(*) from auth.users where id in(a,b) and email like '%@example.invalid')<>2 then
  raise exception 'Both users must be new staging-only identities with @example.invalid emails.';
 end if;
 if not exists(select 1 from auth.users where id=a and email='staging-owner-a@example.invalid' and email_confirmed_at is not null)
 or not exists(select 1 from auth.users where id=b and email='staging-owner-b@example.invalid' and email_confirmed_at is not null) then
  raise exception 'A/B identity or email confirmation does not match. Stop and check staging Auth users.';
 end if;
 if exists(select 1 from public.properties where user_id in(a,b))
 or exists(select 1 from public.survey_free_allocations where user_id in(a,b)) then
  raise exception 'Dummy users already have surveys/allocations. Do not rerun or reset entitlements.';
 end if;
end $$;
-- Exercise the actual owner policies and free-allocation trigger, not maintenance bypass.
set local role authenticated;
select set_config('request.jwt.claims',jsonb_build_object('sub',current_setting('urbanfold.dummy_a'),
 'role','authenticated','email','staging-owner-a@example.invalid')::text,true);
insert into public.properties(id,user_id,surveyor_name,address,postcode,client_email,property_type,notes)
values('f0000000-0000-4000-8000-000000000001',current_setting('urbanfold.dummy_a')::uuid,
 'Dummy Surveyor A','DUMMY PROPERTY A - NOT A REAL ADDRESS','ZZ1 1ZZ','client-a@example.invalid','detached','STAGING DUMMY DATA ONLY');
insert into public.extensions(property_id,extension_types,description,width,length)
values('f0000000-0000-4000-8000-000000000001','["Single"]'::jsonb,'Dummy proposal',3,4);
insert into public.rooms(property_id,room_name,shape,dimensions,additional_measurements)
values('f0000000-0000-4000-8000-000000000001','Living Room','Square/Rectangular','{"l":"4","w":"3","h":"2.4"}'::jsonb,'Dummy chimney breast: 300 mm x 1200 mm');
select set_config('request.jwt.claims',jsonb_build_object('sub',current_setting('urbanfold.dummy_b'),
 'role','authenticated','email','staging-owner-b@example.invalid')::text,true);
insert into public.properties(id,user_id,surveyor_name,address,postcode,client_email,property_type)
values('f0000000-0000-4000-8000-000000000002',current_setting('urbanfold.dummy_b')::uuid,
 'Dummy Surveyor B','DUMMY PROPERTY B - NOT A REAL ADDRESS','ZZ2 2ZZ','client-b@example.invalid','semi-detached');
reset role;
commit;

-- Completion marker only. This does not prove real bearer-token API isolation.
select 'Dummy surveys A and B created; each used its initial free survey. No paid credits added.' as result;
