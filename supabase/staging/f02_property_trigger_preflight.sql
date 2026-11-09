-- SELECT ONLY. Staging Dashboard reference must be hexhtduvqzleoazusskh.
-- Inspect definitions, not just names. Includes cleanup targets for later review.
with targets as (
 select c.oid from pg_class c join pg_namespace n on n.oid=c.relnamespace
 where n.nspname='public' and c.relname in
 ('properties','survey_notification_events','staging_notification_receipts')
), trigger_functions as (
 select distinct t.tgfoid as oid from pg_trigger t
 where t.tgrelid in(select oid from targets) and not t.tgisinternal
), reviewed_functions as (
 select oid from trigger_functions
 union
 select p.oid from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where (n.nspname='public' and p.proname in
 ('enforce_survey_allowance','protect_survey_address',
 'claim_survey_notification','finish_survey_notification','capture_staging_notification'))
 or (n.nspname='auth' and p.proname in ('uid','jwt'))
)
select jsonb_build_object(
 'execution_role',current_user,
 'session_auth_uid',auth.uid(),
 'session_jwt_role',auth.jwt()->>'role',
 'staging_comment_matches',obj_description('public.properties'::regclass,'pg_class') =
 'Urbanfold-Survey-Staging reconstructed baseline; prepared 2026-11-03; never production.',
 'triggers',coalesce((select jsonb_agg(jsonb_build_object(
   'table',t.tgrelid::regclass::text,'name',t.tgname,'enabled',t.tgenabled,
   'internal',t.tgisinternal,'definition',pg_get_triggerdef(t.oid,true),
   'function',t.tgfoid::regprocedure::text) order by t.tgrelid,t.tgname)
   from pg_trigger t where t.tgrelid in(select oid from targets)),'[]'::jsonb),
 'function_definitions',coalesce((select jsonb_agg(jsonb_build_object(
   'signature',p.oid::regprocedure::text,'owner',pg_get_userbyid(p.proowner),
   'security_definer',p.prosecdef,'settings',p.proconfig,
   'definition',pg_get_functiondef(p.oid)) order by p.oid)
   from pg_proc p where p.oid in(select oid from reviewed_functions)),'[]'::jsonb),
 'rewrite_rules',coalesce((select jsonb_agg(jsonb_build_object(
   'table',r.ev_class::regclass::text,'name',r.rulename,
   'definition',pg_get_ruledef(r.oid,true)))
   from pg_rewrite r where r.ev_class in(select oid from targets)),'[]'::jsonb),
 'column_defaults',coalesce((select jsonb_agg(jsonb_build_object(
   'table',d.adrelid::regclass::text,'column',a.attname,
   'expression',pg_get_expr(d.adbin,d.adrelid)))
   from pg_attrdef d join pg_attribute a on a.attrelid=d.adrelid and a.attnum=d.adnum
   where d.adrelid in(select oid from targets)),'[]'::jsonb),
 'constraints',coalesce((select jsonb_agg(jsonb_build_object(
   'table',c.conrelid::regclass::text,'name',c.conname,
   'definition',pg_get_constraintdef(c.oid,true)))
   from pg_constraint c where c.conrelid in(select oid from targets)
   or c.confrelid in(select oid from targets)),'[]'::jsonb),
 'policies',coalesce((select jsonb_agg(to_jsonb(p)) from pg_policies p
   where schemaname='public' and tablename in
   ('properties','survey_notification_events','staging_notification_receipts')),'[]'::jsonb),
 'recorded_function_dependencies',coalesce((select jsonb_agg(jsonb_build_object(
   'function',p.oid::regprocedure::text,
   'dependency',pg_describe_object(d.refclassid,d.refobjid,d.refobjsubid)))
   from pg_depend d join pg_proc p on d.classid='pg_proc'::regclass and d.objid=p.oid
   where p.oid in(select oid from reviewed_functions)),'[]'::jsonb)
) as preflight;
-- PostgreSQL does not record every PL/pgSQL/dynamic SQL dependency.
-- Review function bodies and any additional helpers they call before approval.
