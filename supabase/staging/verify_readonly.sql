-- PREPARED, NOT EXECUTED. All rows should read true after the full sequence.
-- Catalog assertions are necessary but do NOT prove real Auth/Storage/API isolation.
with expected(name) as (values ('properties'),('extensions'),('rooms'),('exterior_photos'),('extension_photos'),
 ('sketch_photos'),('room_photos'),('survey_free_allocations'),('survey_credit_purchases'),('survey_credit_revocations'),('survey_notification_events'))
select 'all_11_app_tables_with_rls' as check_name,
 (select count(*)=11 and bool_and(c.relrowsecurity) from pg_class c join pg_namespace n on n.oid=c.relnamespace
  where n.nspname='public' and c.relkind='r' and c.relname in(select name from expected)) as passed
union all select 'three_private_buckets',
 (select count(*)=3 and bool_and(not public) from storage.buckets where id in ('exterior-photos','sketch-photos','room-photos'))
union all select 'storage_objects_rls',
 (select relrowsecurity from pg_class where oid='storage.objects'::regclass)
union all select 'auth_storage_upload_and_sign_acl',
 has_table_privilege('authenticated','storage.objects','SELECT') and has_table_privilege('authenticated','storage.objects','INSERT')
union all select 'no_anonymous_app_table_grants',
 not exists(select 1 from expected where to_regclass('public.'||name) is not null and
  (has_table_privilege('anon','public.'||name,'SELECT') or has_table_privilege('anon','public.'||name,'INSERT')
   or has_table_privilege('anon','public.'||name,'UPDATE') or has_table_privilege('anon','public.'||name,'DELETE')))
union all select 'no_authenticated_outbox_dml',
 not (has_table_privilege('authenticated','public.survey_notification_events','SELECT')
 or has_table_privilege('authenticated','public.survey_notification_events','INSERT')
 or has_table_privilege('authenticated','public.survey_notification_events','UPDATE')
 or has_table_privilege('authenticated','public.survey_notification_events','DELETE'))
union all select 'allowance_authenticated_only',
 has_function_privilege('authenticated','public.get_survey_allowance()','EXECUTE')
 and not has_function_privilege('anon','public.get_survey_allowance()','EXECUTE')
union all select 'service_only_purchase_recording',
 has_function_privilege('service_role','public.record_survey_purchase(text,text,uuid,integer,text,boolean)','EXECUTE')
 and not has_function_privilege('authenticated','public.record_survey_purchase(text,text,uuid,integer,text,boolean)','EXECUTE')
 and not has_function_privilege('anon','public.record_survey_purchase(text,text,uuid,integer,text,boolean)','EXECUTE')
union all select 'service_only_notification_claim',
 has_function_privilege('service_role','public.claim_survey_notification(uuid,uuid,timestamptz)','EXECUTE')
 and not has_function_privilege('authenticated','public.claim_survey_notification(uuid,uuid,timestamptz)','EXECUTE')
 and not has_function_privilege('anon','public.claim_survey_notification(uuid,uuid,timestamptz)','EXECUTE')
union all select 'all_7_helpers_fixed_search_path',
 (select count(*)=7 and bool_and(p.prosecdef and exists(select 1 from unnest(p.proconfig) x where x in ('search_path=""','search_path=')))
 from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname in
 ('get_survey_allowance','enforce_survey_allowance','protect_survey_address','record_survey_purchase','revoke_survey_purchase','claim_survey_notification','finish_survey_notification'))
union all select 'both_property_triggers_enabled',
 (select count(*)=2 and bool_and(tgenabled='O') from pg_trigger where tgrelid='public.properties'::regclass
 and tgname in ('urbanfold_survey_allowance','urbanfold_protect_address'))
union all select 'original_600_pence_constraint',
 exists(select 1 from pg_constraint where conrelid='public.survey_credit_purchases'::regclass
 and contype='c' and pg_get_constraintdef(oid) ~ 'amount_total = 600');
