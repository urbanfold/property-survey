-- SELECT ONLY. Urbanfold-Survey-Staging hexhtduvqzleoazusskh, as postgres.
-- No payload values, customer contacts, tokens or credentials returned.
with fixtures as (
 select ('f0200000-0000-4000-8000-'||lpad(n::text,12,'0'))::uuid as id,n
 from generate_series(1,6) n
), per_fixture as (
 select f.n as fixture,
 (select count(*) from public.properties p where p.id=f.id) as property_rows,
 (select count(*) from public.survey_notification_events e where e.property_id=f.id) as events,
 (select count(*) from public.survey_notification_events e where e.property_id=f.id and state='accepted') as accepted,
 (select count(*) from public.survey_notification_events e where e.property_id=f.id and state='uncertain') as uncertain,
 (select count(*) from public.survey_notification_events e where e.property_id=f.id and state='sending') as sending,
 (select count(*) from public.staging_notification_receipts r
 join public.survey_notification_events e on r.delivery_id=e.id
 where r.kind='survey' and e.property_id=f.id) as receipts,
 (select coalesce(sum(r.attempts),0) from public.staging_notification_receipts r
 join public.survey_notification_events e on r.delivery_id=e.id
 where r.kind='survey' and e.property_id=f.id) as capture_attempts
 from fixtures f
)
select jsonb_build_object(
 'staging_comment_matches',obj_description('public.properties'::regclass,'pg_class') =
 'Urbanfold-Survey-Staging reconstructed baseline; prepared 2026-11-03; never production.',
 'totals',jsonb_build_object(
   'events',(select count(*) from public.survey_notification_events),
   'receipts',(select count(*) from public.staging_notification_receipts),
   'capture_attempts',(select coalesce(sum(attempts),0) from public.staging_notification_receipts)),
 'per_fixture',(select jsonb_agg(to_jsonb(p) order by fixture) from per_fixture p),
 'all_receipts_have_matching_fixture_events',not exists(
   select 1 from public.staging_notification_receipts r
   where not exists(select 1 from public.survey_notification_events e
     join fixtures f on f.id=e.property_id
     where r.kind='survey' and r.delivery_id=e.id
       and r.payload->>'property_id'=e.property_id::text)),
 'all_receipt_payloads_are_dummy',not exists(
   select 1 from public.staging_notification_receipts r
   where r.kind<>'survey'
     or coalesce(r.payload->>'client_email','') not like '%@example.invalid'
     or coalesce(r.payload->>'address','') not like 'DUMMY F02 FIXTURE %'),
 'all_capture_attempt_counts_are_one',not exists(
   select 1 from public.staging_notification_receipts where attempts<>1)
) as f02_evidence;
