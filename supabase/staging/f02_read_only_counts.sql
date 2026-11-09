-- SELECT ONLY. Run in hexhtduvqzleoazusskh staging SQL Editor as postgres.
-- No credentials, recipients or payload content are returned.
select
 obj_description('public.properties'::regclass,'pg_class') =
 'Urbanfold-Survey-Staging reconstructed baseline; prepared 2026-11-03; never production.' as staging_comment_matches,
 (select count(*) from public.staging_notification_receipts) as receipt_rows,
 (select coalesce(sum(attempts),0) from public.staging_notification_receipts) as capture_attempts,
 (select count(*) from public.survey_notification_events) as notification_events,
 (select count(*) from public.survey_notification_events where state='accepted') as accepted_events,
 (select count(*) from public.survey_notification_events where state='uncertain') as uncertain_events,
 (select count(*) from public.survey_notification_events where state='sending') as sending_events;
