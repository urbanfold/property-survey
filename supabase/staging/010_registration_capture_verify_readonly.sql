-- SELECT ONLY. After separately approved installation, before any dispatcher call.
select jsonb_build_object(
 'allowlist_rls', (select relrowsecurity from pg_class where oid='public.staging_registration_capture_allowlist'::regclass),
 'one_exact_enabled_pair',(select count(*)=1 and bool_and(
  user_id='b83f87d8-abf2-4800-beab-8279917804c7'::uuid
  and registration_email='urbanfolduk+staging-reg-01@gmail.com' and enabled)
  from public.staging_registration_capture_allowlist),
 'no_client_table_access',not has_table_privilege('anon','public.staging_registration_capture_allowlist','SELECT,INSERT,UPDATE,DELETE')
 and not has_table_privilege('authenticated','public.staging_registration_capture_allowlist','SELECT,INSERT,UPDATE,DELETE'),
 'service_table_read_only',has_table_privilege('service_role','public.staging_registration_capture_allowlist','SELECT')
 and not has_table_privilege('service_role','public.staging_registration_capture_allowlist','INSERT,UPDATE,DELETE'),
 'capture_helper', (select jsonb_build_object('owner',pg_get_userbyid(p.proowner),
 'definer',p.prosecdef,'settings',p.proconfig,
 'normalized_body_sha256',encode(sha256(convert_to(btrim(replace(p.prosrc,E'\r\n',E'\n'),E' \t\n\r'),'UTF8')),'hex'),
 'anon_execute',has_function_privilege('anon',p.oid,'EXECUTE'),
 'authenticated_execute',has_function_privilege('authenticated',p.oid,'EXECUTE'),
 'service_execute',has_function_privilege('service_role',p.oid,'EXECUTE'))
 from pg_proc p where p.oid=to_regprocedure('public.capture_staging_notification(text,uuid,jsonb)')),
 'survey_events',(select count(*) from public.survey_notification_events),
 'survey_receipts',(select count(*) from public.staging_notification_receipts where kind='survey'),
 'survey_capture_attempts',(select coalesce(sum(attempts),0) from public.staging_notification_receipts where kind='survey'),
 'registration_receipts',(select count(*) from public.staging_notification_receipts where kind='registration_verified')
) as registration_capture_verification;
