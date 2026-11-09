-- SELECT ONLY. Review in hexhtduvqzleoazusskh before approving installation.
-- No Auth users/emails, customer rows, credentials or secret values returned.
select jsonb_build_object(
 'execution_role',current_user,
 'session_auth_uid',auth.uid(),
 'session_jwt_role',auth.jwt()->>'role',
 'staging_marker_matches',obj_description(to_regclass('public.properties'),'pg_class')=
 'Urbanfold-Survey-Staging reconstructed baseline; prepared 2026-11-03; never production.',
 'registration_tables',coalesce((select jsonb_agg(jsonb_build_object(
  'table',c.relname,'rls',c.relrowsecurity,'owner',pg_get_userbyid(c.relowner)))
  from pg_class c join pg_namespace n on n.oid=c.relnamespace
  where n.nspname='public' and c.relname in
  ('newsletter_preferences','newsletter_consent_events','registration_notification_events')),'[]'::jsonb),
 'auth_triggers',coalesce((select jsonb_agg(jsonb_build_object(
  'name',t.tgname,'enabled',t.tgenabled,'trigger_type',t.tgtype,
  'argument_count',t.tgnargs,'function',t.tgfoid::regprocedure::text,
  'definition_sha256',encode(sha256(convert_to(replace(pg_get_triggerdef(t.oid,true),E'\r\n',E'\n'),'UTF8')),'hex')))
  from pg_trigger t
  where t.tgrelid='auth.users'::regclass and not t.tgisinternal),'[]'::jsonb),
 'registration_functions',coalesce((select jsonb_agg(jsonb_build_object(
  'signature',p.oid::regprocedure::text,'owner',pg_get_userbyid(p.proowner),
  'security_definer',p.prosecdef,'settings',p.proconfig,
  'body_sha256',encode(sha256(convert_to(replace(p.prosrc,E'\r\n',E'\n'),'UTF8')),'hex')))
  from pg_proc p join pg_namespace n on n.oid=p.pronamespace
  where n.nspname='public' and p.proname in
  ('record_auth_registration','get_newsletter_preference','set_newsletter_preference',
  'claim_registration_notification','finish_registration_notification','recover_stale_registration_notifications')),'[]'::jsonb),
 'installer_default_privileges',coalesce((select jsonb_agg(jsonb_build_object(
  'owner',pg_get_userbyid(d.defaclrole),'namespace',d.defaclnamespace::regnamespace::text,
  'object_type',d.defaclobjtype,'acl',d.defaclacl::text)) from pg_default_acl d
  where d.defaclrole=(select oid from pg_roles where rolname=current_user)),'[]'::jsonb)
) as registration_preflight;
-- Fresh installer requires NO existing registration objects. If present, review
-- definitions/schema/grants and prepare an exact upgrade; do not reset/drop them.
-- Definitions/trigger arguments are intentionally not returned: old hooks could
-- embed credentials. Review unexpected deployed source privately before approval.
