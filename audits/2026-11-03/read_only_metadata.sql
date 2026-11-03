-- OPTIONAL DIAGNOSTIC ONLY. Not executed against Supabase during this audit.
-- SELECT-only metadata; no survey records, auth users, keys or secret values.
-- Review results before sharing. Does not fix or reapply any policy/migration.
select jsonb_pretty(jsonb_build_object(
 'relations', (select jsonb_agg(jsonb_build_object('schema',n.nspname,'name',c.relname,
   'kind',c.relkind,'rls',c.relrowsecurity,'forced_rls',c.relforcerowsecurity,'owner',pg_get_userbyid(c.relowner),'options',c.reloptions))
   from pg_class c join pg_namespace n on n.oid=c.relnamespace
   where n.nspname='public' and c.relname in ('properties','extensions','rooms','exterior_photos','extension_photos','sketch_photos','room_photos','survey_free_allocations','survey_credit_purchases','survey_credit_revocations','get_survey_allowance')),
 'grants', (select jsonb_agg(to_jsonb(g)) from information_schema.role_table_grants g
   where g.table_schema='public' and g.table_name in ('properties','extensions','rooms','exterior_photos','extension_photos','sketch_photos','room_photos','survey_free_allocations','survey_credit_purchases','survey_credit_revocations')),
 'policies', (select jsonb_agg(to_jsonb(p)) from pg_policies p where
   (p.schemaname='storage' and p.tablename='objects') or
   (p.schemaname='public' and p.tablename in ('properties','extensions','rooms','exterior_photos','extension_photos','sketch_photos','room_photos','survey_free_allocations','survey_credit_purchases','survey_credit_revocations'))),
 'functions', (select jsonb_agg(jsonb_build_object('schema',n.nspname,'name',p.proname,
   'arguments',pg_get_function_identity_arguments(p.oid),'security_definer',p.prosecdef,
   'search_path_and_settings',p.proconfig,'owner',pg_get_userbyid(p.proowner),
   'acl',p.proacl,'definition_fingerprint',md5(pg_get_functiondef(p.oid))))
   from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public'
   and p.proname in ('get_survey_allowance','enforce_survey_allowance','protect_survey_address','record_survey_purchase','revoke_survey_purchase') and p.prokind='f'),
 'triggers', (select jsonb_agg(jsonb_build_object('name',t.tgname,'enabled',t.tgenabled,'definition',pg_get_triggerdef(t.oid)))
   from pg_trigger t join pg_class c on c.oid=t.tgrelid join pg_namespace n on n.oid=c.relnamespace
   where not t.tgisinternal and n.nspname='public' and c.relname='properties'),
 'buckets', (select jsonb_agg(jsonb_build_object('id',b.id,'public',b.public,'file_size_limit',b.file_size_limit,'allowed_mime_types',b.allowed_mime_types))
   from storage.buckets b where b.id in ('exterior-photos','sketch-photos','room-photos'))
)) as urbanfold_audit_metadata;
