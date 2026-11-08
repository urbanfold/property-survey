-- REVIEWED READ-ONLY production verification, NOT installation approval.
-- Target connector project: arnzqizcycesukplmvuc. Do not run against staging.
-- Original candidate verification logic retained; compare existing survey baseline
-- and production registration catalog before approving the installer.
with helpers as (
 select p.* from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='public' and p.proname in
 ('record_auth_registration','get_newsletter_preference','set_newsletter_preference',
  'claim_registration_notification','finish_registration_notification','recover_stale_registration_notifications')
)
select jsonb_build_object(
 'three_tables_with_rls',(select count(*)=3 and bool_and(c.relrowsecurity)
 from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public'
 and c.relname in('newsletter_preferences','newsletter_consent_events','registration_notification_events')),
 'seven_definer_helpers_owned_by_postgres_with_fixed_path',(select count(*)=7 and bool_and(
 p.prosecdef and pg_get_userbyid(p.proowner)='postgres' and exists(select 1 from unnest(p.proconfig) s where s in('search_path=""','search_path='))) from helpers p),
 'no_anonymous_helper_execute',(select bool_and(not has_function_privilege('anon',p.oid,'EXECUTE')) from helpers p),
 'authenticated_only_preference_helpers',(select bool_and(has_function_privilege('authenticated',p.oid,'EXECUTE')=
 (p.proname in('get_newsletter_preference','set_newsletter_preference'))) from helpers p),
 'service_only_dispatch_helpers',(select bool_and(has_function_privilege('service_role',p.oid,'EXECUTE')
 and not has_function_privilege('authenticated',p.oid,'EXECUTE') and not has_function_privilege('anon',p.oid,'EXECUTE'))
 from helpers p where p.proname in('claim_registration_notification','finish_registration_notification','recover_stale_registration_notifications')),
 'two_auth_triggers_enabled',(select count(*)=2 and bool_and(tgenabled='O') from pg_trigger
 where tgrelid='auth.users'::regclass and tgname in('urbanfold_auth_signup','urbanfold_auth_first_confirmation')),
 'no_client_queue_access',not has_table_privilege('authenticated','public.registration_notification_events','SELECT')
 and not has_table_privilege('anon','public.registration_notification_events','SELECT'),
 'no_client_consent_writes',not has_table_privilege('authenticated','public.newsletter_consent_events','INSERT,UPDATE,DELETE')
 and not has_table_privilege('authenticated','public.newsletter_preferences','INSERT,UPDATE,DELETE'),
 'service_audit_read_only',has_table_privilege('service_role','public.newsletter_consent_events','SELECT')
 and not has_table_privilege('service_role','public.newsletter_consent_events','INSERT,UPDATE,DELETE')
) as registration_security_checks;
