-- PREPARED, NOT EXECUTED. Metadata only, suitable for reviewed staging/production comparison.
-- No survey rows, auth users, photos, secrets, or full function bodies are selected.
-- Historical diagnostic did NOT include all of this metadata. Review before sharing.
with wanted(name) as (values
 ('properties'),('extensions'),('rooms'),('exterior_photos'),('extension_photos'),('sketch_photos'),('room_photos'),
 ('survey_free_allocations'),('survey_credit_purchases'),('survey_credit_revocations'),('survey_notification_events')),
funcs(name) as (values ('get_survey_allowance'),('enforce_survey_allowance'),('protect_survey_address'),
 ('record_survey_purchase'),('revoke_survey_purchase'),('claim_survey_notification'),('finish_survey_notification'))
select jsonb_pretty(jsonb_build_object(
 'postgres_version',current_setting('server_version'),
 'columns',(select jsonb_agg(to_jsonb(x) order by x.table_name,x.ordinal_position) from
   (select table_name,column_name,ordinal_position,data_type,udt_name,is_nullable,column_default,is_identity,is_generated
    from information_schema.columns where table_schema='public' and table_name in(select name from wanted)) x),
 'relations',(select jsonb_agg(jsonb_build_object('name',c.relname,'kind',c.relkind,'rls',c.relrowsecurity,
   'force_rls',c.relforcerowsecurity,'owner',pg_get_userbyid(c.relowner),'acl',c.relacl,'comment',obj_description(c.oid,'pg_class')))
   from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relname in(select name from wanted)),
 'constraints',(select jsonb_agg(jsonb_build_object('table',r.relname,'name',c.conname,'type',c.contype,
   'definition',pg_get_constraintdef(c.oid),'validated',c.convalidated,'deferrable',c.condeferrable))
   from pg_constraint c join pg_class r on r.oid=c.conrelid join pg_namespace n on n.oid=r.relnamespace
   where n.nspname='public' and r.relname in(select name from wanted)),
 'indexes',(select jsonb_agg(to_jsonb(i)) from pg_indexes i where i.schemaname='public' and i.tablename in(select name from wanted)),
 'policies',(select jsonb_agg(to_jsonb(p)) from pg_policies p where
   (p.schemaname='public' and p.tablename in(select name from wanted)) or (p.schemaname='storage' and p.tablename='objects')),
 'triggers',(select jsonb_agg(jsonb_build_object('table',r.relname,'name',t.tgname,'enabled',t.tgenabled,
   'definition',pg_get_triggerdef(t.oid))) from pg_trigger t join pg_class r on r.oid=t.tgrelid
   join pg_namespace n on n.oid=r.relnamespace where not t.tgisinternal and n.nspname='public' and r.relname in(select name from wanted)),
 'functions',(select jsonb_agg(jsonb_build_object('name',p.proname,'arguments',pg_get_function_identity_arguments(p.oid),
   'result',pg_get_function_result(p.oid),'security_definer',p.prosecdef,'settings',p.proconfig,'owner',pg_get_userbyid(p.proowner),
   'acl',p.proacl,'definition_md5',md5(pg_get_functiondef(p.oid)))) from pg_proc p join pg_namespace n on n.oid=p.pronamespace
   where n.nspname='public' and p.proname in(select name from funcs) and p.prokind='f'),
 'table_grants',(select jsonb_agg(to_jsonb(g)) from information_schema.table_privileges g where
   (g.table_schema='public' and g.table_name in(select name from wanted)) or
   (g.table_schema='storage' and g.table_name in ('buckets','objects'))),
 'column_grants',(select jsonb_agg(to_jsonb(g)) from information_schema.column_privileges g where
   g.table_schema='public' and g.table_name in(select name from wanted)),
 'routine_grants',(select jsonb_agg(to_jsonb(g)) from information_schema.routine_privileges g
   where g.routine_schema='public' and g.routine_name in(select name from funcs)),
 'default_privileges',(select jsonb_agg(jsonb_build_object('role',pg_get_userbyid(d.defaclrole),'schema',n.nspname,
   'kind',d.defaclobjtype,'acl',d.defaclacl)) from pg_default_acl d left join pg_namespace n on n.oid=d.defaclnamespace
   where n.nspname='public' or d.defaclnamespace=0),
 'buckets',(select jsonb_agg(jsonb_build_object('id',b.id,'name',b.name,'public',b.public,
   'file_size_limit',b.file_size_limit,'allowed_mime_types',b.allowed_mime_types)) from storage.buckets b
   where b.id in ('exterior-photos','sketch-photos','room-photos'))
)) as urbanfold_schema_metadata;
