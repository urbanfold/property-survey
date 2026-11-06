-- PREPARED ONLY: NOT EXECUTED. Run once in Urbanfold-Survey-Staging
-- Dashboard project hexhtduvqzleoazusskh, as postgres. Never production.
-- This is test-fixture maintenance, NOT an ordinary-user credit purchase/create test.
-- Adds six dedicated dummy properties using the EXISTING maintenance exemption.
-- Does not alter original A/B properties, Auth users, allocations, credits or photos.
-- No functions, policies, secrets, triggers or deployments are changed.
-- The comment/identity guards are not an independent project-reference check:
-- verify the Dashboard URL yourself before running. Stop on any error.
begin;
do $$
declare before_allocations jsonb; before_purchases jsonb; after_allocations jsonb; after_purchases jsonb;
begin
 if current_user <> 'postgres' or auth.uid() is not null
    or auth.jwt()->>'role' is not null then
  raise exception 'Use the staging SQL Editor as postgres without simulated JWT claims.';
 end if;
 if obj_description('public.properties'::regclass,'pg_class') is distinct from
 'Urbanfold-Survey-Staging reconstructed baseline; prepared 2026-11-03; never production.' then
  raise exception 'Reviewed staging baseline required.';
 end if;
 if not exists(select 1 from auth.users where id='9036b71c-4f09-4d1b-9dce-519533c4001e'
   and email='staging-owner-a@example.invalid' and email_confirmed_at is not null)
 or not exists(select 1 from auth.users where id='d72b4323-d71b-4b87-b78a-09896647fddf'
   and email='staging-owner-b@example.invalid' and email_confirmed_at is not null) then
  raise exception 'Confirmed dummy A/B identities do not match.';
 end if;
 if to_regclass('public.staging_notification_receipts') is null
 or to_regprocedure('public.capture_staging_notification(text,uuid,jsonb)') is null
 or to_regprocedure('public.claim_survey_notification(uuid,uuid,timestamp with time zone)') is null
 or to_regprocedure('public.finish_survey_notification(uuid,boolean)') is null then
  raise exception 'Required 003/005 prerequisites are missing.';
 end if;
 if exists(select 1 from public.properties where id::text like 'f0200000-0000-4000-8000-%') then
  raise exception 'Dedicated F02 fixtures already exist. Do not rerun or overwrite.';
 end if;
 select coalesce(jsonb_agg(to_jsonb(x) order by x.user_id),'[]'::jsonb)
 into before_allocations from public.survey_free_allocations x;
 select coalesce(jsonb_agg(to_jsonb(x) order by x.checkout_session_id),'[]'::jsonb)
 into before_purchases from public.survey_credit_purchases x;
 insert into public.properties(id,user_id,surveyor_name,address,postcode,client_email,
 property_type,notes,last_submitted_at)
 select ('f0200000-0000-4000-8000-'||lpad(n::text,12,'0'))::uuid,
 case when n<=5 then '9036b71c-4f09-4d1b-9dce-519533c4001e'::uuid
 else 'd72b4323-d71b-4b87-b78a-09896647fddf'::uuid end,
 'DUMMY F02 TEST SURVEYOR', 'DUMMY F02 FIXTURE '||n||' - NOT A REAL ADDRESS',
 'ZZ9 9ZZ', 'f02-fixture-'||n||'@example.invalid', 'detached',
 'DEDICATED F02 NOTIFICATION TEST ONLY; retain pending evidence review.', clock_timestamp()
 from generate_series(1,6) n;
 select coalesce(jsonb_agg(to_jsonb(x) order by x.user_id),'[]'::jsonb)
 into after_allocations from public.survey_free_allocations x;
 select coalesce(jsonb_agg(to_jsonb(x) order by x.checkout_session_id),'[]'::jsonb)
 into after_purchases from public.survey_credit_purchases x;
 if before_allocations is distinct from after_allocations
 or before_purchases is distinct from after_purchases then
  raise exception 'Entitlements changed unexpectedly; roll back all fixture inserts.';
 end if;
end $$;
commit;
-- Metadata counts only; no notifications are requested by this script.
select
 (select count(*) from public.properties where id::text like 'f0200000-0000-4000-8000-%') as dedicated_fixtures,
 (select count(*) from public.survey_notification_events) as notification_events,
 (select count(*) from public.staging_notification_receipts) as receipt_rows,
 (select coalesce(sum(attempts),0) from public.staging_notification_receipts) as capture_attempts;
