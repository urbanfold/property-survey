-- SELECT ONLY. Verify project hexhtduvqzleoazusskh. No secrets or raw Auth data.
with wanted(n,user_id,email) as (values (1,'b83f87d8-abf2-4800-beab-8279917804c7'::uuid,'urbanfolduk+staging-reg-01@gmail.com'::text),
 (2,'d2598ebf-d44c-4e11-81a5-d82f3d06ada1'::uuid,'urbanfolduk+staging-reg-02@gmail.com'::text),
 (3,'3a4e8d72-bf58-468a-b24f-0417c4a64f5b'::uuid,'urbanfolduk+staging-reg-03@gmail.com'::text))
select jsonb_build_object(
 'staging_marker_matches',obj_description(to_regclass('public.properties'),'pg_class')=
 'Urbanfold-Survey-Staging reconstructed baseline; prepared 2026-11-03; never production.',
 'capture_body_sha256',(select encode(sha256(convert_to(btrim(replace(p.prosrc,E'\r\n',E'\n'),E' \t\n\r'),'UTF8')),'hex') from pg_proc p where p.oid=to_regprocedure('public.capture_staging_notification(text,uuid,jsonb)')),
 'capture_security',(select jsonb_build_object('owner',pg_get_userbyid(p.proowner),'definer',p.prosecdef,'settings',p.proconfig,
  'anon_execute',has_function_privilege('anon',p.oid,'EXECUTE'),'authenticated_execute',has_function_privilege('authenticated',p.oid,'EXECUTE'),
  'service_execute',has_function_privilege('service_role',p.oid,'EXECUTE')) from pg_proc p where p.oid=to_regprocedure('public.capture_staging_notification(text,uuid,jsonb)')),
 'allowlist_entries',(select count(*) from public.staging_registration_capture_allowlist),
 'allowlist_owner',(select pg_get_userbyid(relowner) from pg_class where oid='public.staging_registration_capture_allowlist'::regclass),
 'allowlist_rls',(select relrowsecurity from pg_class where oid='public.staging_registration_capture_allowlist'::regclass),
 'allowlist_columns',(select jsonb_agg(jsonb_build_object('name',attname,'type',atttypid::regtype::text,'not_null',attnotnull,'generated',attgenerated,'identity',attidentity) order by attnum)
  from pg_attribute where attrelid='public.staging_registration_capture_allowlist'::regclass and attnum>0 and not attisdropped),
 'allowlist_custom_triggers',(select count(*) from pg_trigger where tgrelid='public.staging_registration_capture_allowlist'::regclass and not tgisinternal),
 'allowlist_rules',(select count(*) from pg_rewrite where ev_class='public.staging_registration_capture_allowlist'::regclass),
 'allowlist_policies',(select count(*) from pg_policy where polrelid='public.staging_registration_capture_allowlist'::regclass),
 'no_client_table_access',not has_table_privilege('anon','public.staging_registration_capture_allowlist','SELECT,INSERT,UPDATE,DELETE') and not has_table_privilege('authenticated','public.staging_registration_capture_allowlist','SELECT,INSERT,UPDATE,DELETE'),
 'service_table_read_only',has_table_privilege('service_role','public.staging_registration_capture_allowlist','SELECT') and not has_table_privilege('service_role','public.staging_registration_capture_allowlist','INSERT,UPDATE,DELETE'),
 'identities',(select jsonb_agg(jsonb_build_object('test',w.n,'user_id',w.user_id,
  'auth_verified',exists(select 1 from auth.users u where u.id=w.user_id and u.email=w.email and u.email_confirmed_at is not null),
  'allowlisted',exists(select 1 from public.staging_registration_capture_allowlist a where a.user_id=w.user_id and a.registration_email=w.email and a.enabled),
  'original_choice',(select signup_opt_in_requested from public.newsletter_preferences where user_id=w.user_id),
  'current_consent',(select opted_in from public.newsletter_preferences where user_id=w.user_id),
  'signup_audits',(select count(*) from public.newsletter_consent_events where user_id=w.user_id and action='signup_request'),
  'verification_audits',(select count(*) from public.newsletter_consent_events where user_id=w.user_id and action='email_verified'),
  'withdrawal_audits',(select count(*) from public.newsletter_consent_events where user_id=w.user_id and action='preference_change' and choice is false),
  'pending_events',(select count(*) from public.registration_notification_events where user_id=w.user_id and state='pending'),
  'accepted_events',(select count(*) from public.registration_notification_events where user_id=w.user_id and state='accepted'),
  'receipts',(select count(*) from public.staging_notification_receipts r join public.registration_notification_events e on e.id=r.delivery_id where r.kind='registration_verified' and e.user_id=w.user_id)
 ) order by w.n) from wanted w),
 'all_pending_registration_events',(select count(*) from public.registration_notification_events where state='pending'),
 'survey_events',(select count(*) from public.survey_notification_events),
 'survey_receipts',(select count(*) from public.staging_notification_receipts where kind='survey'),
 'survey_capture_attempts',(select coalesce(sum(attempts),0) from public.staging_notification_receipts where kind='survey')
) as registration_extension_metadata;
