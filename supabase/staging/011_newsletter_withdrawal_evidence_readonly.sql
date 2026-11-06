-- SELECT ONLY. Connected reviewer, exact staging project hexhtduvqzleoazusskh.
-- No Auth token/password or raw notification body returned. Save before/after.
with target as (select 'b83f87d8-abf2-4800-beab-8279917804c7'::uuid as id)
select jsonb_build_object(
 'test1_user_id',(select id from target),
 'auth_verified',exists(select 1 from auth.users u where u.id=(select id from target)
 and u.email='urbanfolduk+staging-reg-01@gmail.com' and u.email_confirmed_at is not null),
 'original_signup_choice',(select signup_opt_in_requested from public.newsletter_preferences where user_id=(select id from target)),
 'current_consent',(select opted_in from public.newsletter_preferences where user_id=(select id from target)),
 'preference_updated_at',(select updated_at from public.newsletter_preferences where user_id=(select id from target)),
 'signup_audits',(select count(*) from public.newsletter_consent_events where user_id=(select id from target) and action='signup_request'),
 'verification_audits',(select count(*) from public.newsletter_consent_events where user_id=(select id from target) and action='email_verified'),
 'preference_change_audits',(select count(*) from public.newsletter_consent_events where user_id=(select id from target) and action='preference_change'),
 'withdrawal_audits',(select count(*) from public.newsletter_consent_events where user_id=(select id from target) and action='preference_change' and choice is false),
 'registration_event_count',(select count(*) from public.registration_notification_events where user_id=(select id from target)),
 'registration_history_sha256',(select encode(sha256(convert_to(coalesce(jsonb_agg(to_jsonb(e) order by e.id),'[]'::jsonb)::text,'UTF8')),'hex')
 from public.registration_notification_events e where e.user_id=(select id from target)),
 'registration_receipt_count',(select count(*) from public.staging_notification_receipts r join public.registration_notification_events e on e.id=r.delivery_id
 where r.kind='registration_verified' and e.user_id=(select id from target)),
 'registration_receipts_sha256',(select encode(sha256(convert_to(coalesce(jsonb_agg(to_jsonb(r) order by r.delivery_id),'[]'::jsonb)::text,'UTF8')),'hex')
 from public.staging_notification_receipts r join public.registration_notification_events e on e.id=r.delivery_id
 where r.kind='registration_verified' and e.user_id=(select id from target)),
 'survey_events',(select count(*) from public.survey_notification_events),
 'survey_receipts',(select count(*) from public.staging_notification_receipts where kind='survey'),
 'survey_capture_attempts',(select coalesce(sum(attempts),0) from public.staging_notification_receipts where kind='survey')
) as withdrawal_evidence;
