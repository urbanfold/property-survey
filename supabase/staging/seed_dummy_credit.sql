-- OPTIONAL SYNTHETIC LEDGER TEST ONLY, PREPARED, NOT EXECUTED. Never use in production.
-- No Stripe payment is created/verified by this SQL. Do not represent this as paid revenue.
-- Same staging acknowledgement and dummy_a UUID settings as seed_dummy_surveys.sql are required.
-- Intentionally insert a NEW synthetic live-flagged event for testing the UNCHANGED live-credit rule.
-- Never flip a genuine test purchase to live; sandbox webhook events must stay live_mode=false.
begin;
do $$
declare a uuid := nullif(current_setting('urbanfold.dummy_a',true),'')::uuid;
begin
 if current_setting('urbanfold.staging_setup',true) is distinct from 'Urbanfold-Survey-Staging'
 or obj_description('public.properties'::regclass,'pg_class') is distinct from
 'Urbanfold-Survey-Staging reconstructed baseline; prepared 2026-11-03; never production.' then
  raise exception 'Not an acknowledged reconstructed staging baseline.';
 end if;
 if not exists(select 1 from auth.users where id=a and email like '%@example.invalid')
 or not exists(select 1 from public.properties where id='f0000000-0000-4000-8000-000000000001' and user_id=a) then
  raise exception 'Expected seeded dummy A only.';
 end if;
end $$;
set local role service_role;
select public.record_survey_purchase('cs_test_UrbanfoldStagingDummyA','pi_UrbanfoldStagingTestA',
 current_setting('urbanfold.dummy_a')::uuid,600,'gbp',false);
select public.record_survey_purchase('cs_live_UrbanfoldStagingDummyA','pi_UrbanfoldStagingLiveA',
 current_setting('urbanfold.dummy_a')::uuid,600,'gbp',true);
reset role;
commit;
-- Separately sign in as dummy A and verify only the synthetic live-mode row grants one credit.
-- Do not execute these server-only ledger calls from browser code or relax their grants.
