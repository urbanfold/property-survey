-- SELECT ONLY. Review project hexhtduvqzleoazusskh; no execution authorised here.
select jsonb_build_object(
 'staging_marker_matches',obj_description(to_regclass('public.properties'),'pg_class')=
 'Urbanfold-Survey-Staging reconstructed baseline; prepared 2026-11-03; never production.',
 'capture_helper', (select jsonb_build_object('owner',pg_get_userbyid(p.proowner),
 'definer',p.prosecdef,'settings',p.proconfig,
 'normalized_body_sha256',encode(sha256(convert_to(btrim(replace(p.prosrc,E'\r\n',E'\n'),E' \t\n\r'),'UTF8')),'hex'),
 'anon_execute',has_function_privilege('anon',p.oid,'EXECUTE'),
 'authenticated_execute',has_function_privilege('authenticated',p.oid,'EXECUTE'),
 'service_execute',has_function_privilege('service_role',p.oid,'EXECUTE'))
 from pg_proc p where p.oid=to_regprocedure('public.capture_staging_notification(text,uuid,jsonb)')),
 'allowlist_already_exists',to_regclass('public.staging_registration_capture_allowlist') is not null,
 'approved_verified_auth_identity',exists(select 1 from auth.users where id='b83f87d8-abf2-4800-beab-8279917804c7'
 and email='urbanfolduk+staging-reg-01@gmail.com' and email_confirmed_at is not null),
 'approved_pending_event_count',(select count(*) from public.registration_notification_events
 where user_id='b83f87d8-abf2-4800-beab-8279917804c7' and registration_email='urbanfolduk+staging-reg-01@gmail.com'
 and newsletter_signup_choice is true and state='pending'),
 'all_pending_registration_events',(select count(*) from public.registration_notification_events where state='pending'),
 'approved_registration_receipts',(select count(*) from public.staging_notification_receipts r
 join public.registration_notification_events e on e.id=r.delivery_id
 where r.kind='registration_verified' and e.user_id='b83f87d8-abf2-4800-beab-8279917804c7'),
 'survey_events',(select count(*) from public.survey_notification_events),
 'survey_receipts',(select count(*) from public.staging_notification_receipts where kind='survey'),
 'survey_capture_attempts',(select coalesce(sum(attempts),0) from public.staging_notification_receipts where kind='survey')
) as registration_capture_preflight;
