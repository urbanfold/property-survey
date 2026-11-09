-- SELECT ONLY: supplementary production reconciliation; no DDL, mutations or external calls.
-- Target arnzqizcycesukplmvuc must be independently confirmed by the connected reviewer.
-- The observed digest is NOT approved for installation by this query.
-- Function bodies, trigger arguments, passwords and secret values are NOT returned.
with baseline as (select jsonb_build_object(
 'tables',coalesce((select jsonb_agg(jsonb_build_object('schema',n.nspname,'name',c.relname,'kind',c.relkind,'rls',c.relrowsecurity,'owner',pg_get_userbyid(c.relowner)) order by n.nspname,c.relname)
 from pg_class c join pg_namespace n on n.oid=c.relnamespace where (n.nspname='public' and c.relname in('properties','extensions','rooms','exterior_photos','extension_photos','sketch_photos','room_photos','survey_free_allocations','survey_credit_purchases','survey_credit_revocations')) or (n.nspname='storage' and c.relname='objects')),'[]'::jsonb),
 'columns',coalesce((select jsonb_agg(jsonb_build_object('table',c.relname,'column',a.attname,'type',format_type(a.atttypid,a.atttypmod),'not_null',a.attnotnull,'default',pg_get_expr(d.adbin,d.adrelid)) order by c.relname,a.attnum)
 from pg_class c join pg_namespace n on n.oid=c.relnamespace join pg_attribute a on a.attrelid=c.oid and a.attnum>0 and not a.attisdropped
 left join pg_attrdef d on d.adrelid=c.oid and d.adnum=a.attnum where n.nspname='public' and c.relname in('properties','extensions','rooms','exterior_photos','extension_photos','sketch_photos','room_photos','survey_free_allocations','survey_credit_purchases','survey_credit_revocations')),'[]'::jsonb),
 'constraints',coalesce((select jsonb_agg(jsonb_build_object('table',c.conrelid::regclass::text,'name',c.conname,'type',c.contype,'validated',c.convalidated,'definition',pg_get_constraintdef(c.oid,true)) order by c.conrelid::regclass::text,c.conname)
 from pg_constraint c join pg_class r on r.oid=c.conrelid join pg_namespace n on n.oid=r.relnamespace where n.nspname='public' and r.relname in('properties','extensions','rooms','exterior_photos','extension_photos','sketch_photos','room_photos','survey_free_allocations','survey_credit_purchases','survey_credit_revocations')),'[]'::jsonb),
 'indexes',coalesce((select jsonb_agg(jsonb_build_object('table',r.relname,'name',i.relname,'valid',x.indisvalid,'definition',pg_get_indexdef(i.oid)) order by r.relname,i.relname)
 from pg_index x join pg_class i on i.oid=x.indexrelid join pg_class r on r.oid=x.indrelid join pg_namespace n on n.oid=r.relnamespace where n.nspname='public' and r.relname in('properties','extensions','rooms','exterior_photos','extension_photos','sketch_photos','room_photos','survey_free_allocations','survey_credit_purchases','survey_credit_revocations')),'[]'::jsonb),
 'policies',coalesce((select jsonb_agg(jsonb_build_object('schema',schemaname,'table',tablename,'name',policyname,'roles',roles,'cmd',cmd,'permissive',permissive,'using',qual,'check',with_check) order by schemaname,tablename,policyname)
 from pg_policies where (schemaname='public' and tablename in('properties','extensions','rooms','exterior_photos','extension_photos','sketch_photos','room_photos','survey_free_allocations','survey_credit_purchases','survey_credit_revocations')) or (schemaname='storage' and tablename='objects')),'[]'::jsonb),
 'effective_table_grants',coalesce((select jsonb_agg(jsonb_build_object('role',role_name,'table',table_name,'select',has_table_privilege(role_name,'public.'||table_name,'SELECT'),'insert',has_table_privilege(role_name,'public.'||table_name,'INSERT'),'update',has_table_privilege(role_name,'public.'||table_name,'UPDATE'),'delete',has_table_privilege(role_name,'public.'||table_name,'DELETE')) order by role_name,table_name)
 from unnest(array['anon','authenticated','service_role']) role_name cross join unnest(array['properties','extensions','rooms','exterior_photos','extension_photos','sketch_photos','room_photos','survey_free_allocations','survey_credit_purchases','survey_credit_revocations']) table_name where to_regclass('public.'||table_name) is not null),'[]'::jsonb),
 'billing_functions',coalesce((select jsonb_agg(jsonb_build_object('signature',p.oid::regprocedure::text,'name',p.proname,'identity_arguments',pg_get_function_identity_arguments(p.oid),'return_type',p.prorettype::regtype::text,'language',(select lanname from pg_language where oid=p.prolang),'body_sha256',encode(sha256(convert_to(btrim(replace(p.prosrc,E'\r\n',E'\n'),E' \t\n\r'),'UTF8')),'hex'),'owner',pg_get_userbyid(p.proowner),'definer',p.prosecdef,'settings',p.proconfig,'acl',p.proacl::text) order by p.oid::regprocedure::text)
 from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname in('get_survey_allowance','enforce_survey_allowance','protect_survey_address','record_survey_purchase','revoke_survey_purchase')),'[]'::jsonb),
 'existing_triggers',coalesce((select jsonb_agg(jsonb_build_object('table',t.tgrelid::regclass::text,'name',t.tgname,'enabled',t.tgenabled,'definition_sha256',encode(sha256(convert_to(pg_get_triggerdef(t.oid,true),'UTF8')),'hex'),'function',t.tgfoid::regprocedure::text,'body_sha256',encode(sha256(convert_to(replace(p.prosrc,E'\r\n',E'\n'),'UTF8')),'hex')) order by t.tgrelid::regclass::text,t.tgname)
 from pg_trigger t join pg_proc p on p.oid=t.tgfoid where not t.tgisinternal and t.tgrelid in(to_regclass('public.properties'),to_regclass('auth.users')) and t.tgname not in('urbanfold_auth_signup','urbanfold_auth_first_confirmation')),'[]'::jsonb),
 'ddl_event_triggers',coalesce((select jsonb_agg(jsonb_build_object('name',e.evtname,'event',e.evtevent,'enabled',e.evtenabled,'tags',e.evttags,'function',e.evtfoid::regprocedure::text,'owner',pg_get_userbyid(p.proowner),'definer',p.prosecdef,'settings',p.proconfig,'body_sha256',encode(sha256(convert_to(replace(p.prosrc,E'\r\n',E'\n'),'UTF8')),'hex')) order by e.evtname)
 from pg_event_trigger e join pg_proc p on p.oid=e.evtfoid),'[]'::jsonb),
 'defaults',coalesce((select jsonb_agg(jsonb_build_object('owner',pg_get_userbyid(defaclrole),'schema',defaclnamespace::regnamespace::text,'type',defaclobjtype,'acl',defaclacl::text) order by defaclrole,defaclnamespace,defaclobjtype) from pg_default_acl),'[]'::jsonb),
 'existing_definer_helpers',coalesce((select jsonb_agg(jsonb_build_object('signature',p.oid::regprocedure::text,'return_type',p.prorettype::regtype::text,'owner',pg_get_userbyid(p.proowner),'settings',p.proconfig,'acl',p.proacl::text,'anon_execute',has_function_privilege('anon',p.oid,'EXECUTE'),'authenticated_execute',has_function_privilege('authenticated',p.oid,'EXECUTE'),'body_sha256',encode(sha256(convert_to(replace(p.prosrc,E'\r\n',E'\n'),'UTF8')),'hex')) order by p.oid::regprocedure::text) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.prosecdef and p.proname not in('claim_survey_notification','finish_survey_notification','record_auth_registration','get_newsletter_preference','set_newsletter_preference','recover_stale_registration_notifications','claim_registration_notification','finish_registration_notification')),'[]'::jsonb),
 'client_memberships',coalesce((select jsonb_agg(jsonb_build_object('role',pg_get_userbyid(roleid),'member',pg_get_userbyid(member)) order by roleid,member) from pg_auth_members where pg_get_userbyid(member) in('anon','authenticated')),'[]'::jsonb),
 'buckets',coalesce((select jsonb_agg(jsonb_build_object('id',id,'public',public) order by id) from storage.buckets where id in('exterior-photos','sketch-photos','room-photos')),'[]'::jsonb)
) as metadata)
select jsonb_build_object(
 'expected_project','arnzqizcycesukplmvuc',
 'execution_role',current_user,
 'baseline_sha256',encode(sha256(convert_to(metadata::text,'UTF8')),'hex'),
 'baseline_matches_reported',encode(sha256(convert_to(metadata::text,'UTF8')),'hex')='10fa3ce6272648b31c662735e549b2e78b032a63cceb6e5f1d862f5d5052e4f6',
 'api_roles',coalesce((select jsonb_agg(jsonb_build_object('role',rolname,'superuser',rolsuper,'bypass_rls',rolbypassrls,'can_login',rolcanlogin) order by rolname) from pg_roles where rolname in('anon','authenticated','service_role')),'[]'::jsonb),
 'existing_table_privileges',coalesce((select jsonb_agg(jsonb_build_object(
 'role',r.rolname,'schema',n.nspname,'table',c.relname,'owner',pg_get_userbyid(c.relowner),
 'rls',c.relrowsecurity,'force_rls',c.relforcerowsecurity,'inherits_owner',pg_has_role(r.rolname,c.relowner,'USAGE'),
 'select',has_table_privilege(r.rolname,c.oid,'SELECT'),'insert',has_table_privilege(r.rolname,c.oid,'INSERT'),
 'update',has_table_privilege(r.rolname,c.oid,'UPDATE'),'delete',has_table_privilege(r.rolname,c.oid,'DELETE'),
 'truncate',has_table_privilege(r.rolname,c.oid,'TRUNCATE'),'references',has_table_privilege(r.rolname,c.oid,'REFERENCES'),
 'trigger',has_table_privilege(r.rolname,c.oid,'TRIGGER'),
 'acl', (select jsonb_agg(jsonb_build_object('grantee',case when a.grantee=0 then 'PUBLIC' else pg_get_userbyid(a.grantee) end,
 'privilege',a.privilege_type,'grantable',a.is_grantable) order by a.grantee,a.privilege_type) from aclexplode(coalesce(c.relacl,acldefault('r',c.relowner))) a)) order by n.nspname,c.relname,r.rolname)
 from pg_class c join pg_namespace n on n.oid=c.relnamespace cross join pg_roles r
 where r.rolname in('anon','authenticated') and c.relkind='r' and ((n.nspname='public' and c.relname in('properties','extensions','rooms','exterior_photos','extension_photos','sketch_photos','room_photos','survey_free_allocations','survey_credit_purchases','survey_credit_revocations')) or (n.nspname='storage' and c.relname='objects'))),'[]'::jsonb),
 'foreign_keys',coalesce((select jsonb_agg(jsonb_build_object('schema',n.nspname,'table',t.relname,'constraint',c.conname,
 'columns',(select jsonb_agg(a.attname order by k.ordinality) from unnest(c.conkey) with ordinality k(attnum,ordinality) join pg_attribute a on a.attrelid=c.conrelid and a.attnum=k.attnum),
 'references',c.confrelid::regclass::text,'delete_action',case c.confdeltype when 'c' then 'CASCADE' when 'a' then 'NO ACTION' when 'r' then 'RESTRICT' when 'n' then 'SET NULL' when 'd' then 'SET DEFAULT' else c.confdeltype::text end,
 'validated',c.convalidated,'definition',pg_get_constraintdef(c.oid,true)) order by n.nspname,t.relname,c.conname)
 from pg_constraint c join pg_class t on t.oid=c.conrelid join pg_namespace n on n.oid=t.relnamespace
 where n.nspname='public' and c.contype='f' and t.relname in('properties','extensions','rooms','exterior_photos','extension_photos','sketch_photos','room_photos','survey_free_allocations','survey_credit_purchases','survey_credit_revocations')),'[]'::jsonb),
 'billing_function_comparison',(select jsonb_agg(jsonb_build_object('signature',expected.signature,'exists',p.oid is not null,'identity_arguments',pg_get_function_identity_arguments(p.oid),'return_type',p.prorettype::regtype::text,'language',(select lanname from pg_language where oid=p.prolang),
 'body_matches_reviewed_source',coalesce(encode(sha256(convert_to(btrim(replace(p.prosrc,E'\r\n',E'\n'),E' \t\n\r'),'UTF8')),'hex')=expected.digest,false),
 'owner',pg_get_userbyid(p.proowner),'definer',p.prosecdef,'settings',p.proconfig,
 'anon_execute',coalesce(has_function_privilege('anon',p.oid,'EXECUTE'),false),
 'authenticated_execute',coalesce(has_function_privilege('authenticated',p.oid,'EXECUTE'),false),
 'service_execute',coalesce(has_function_privilege('service_role',p.oid,'EXECUTE'),false),
 'acl',p.proacl::text) order by expected.signature)
 from (values ('public.get_survey_allowance()','3b3b5e7c335a16a91c9f447b4ac8fd62b8f6e584273d9762c70c70a60be46ad5'),('public.enforce_survey_allowance()','2600d2e67866d1163846b11be2035a32dd0c6ea9e4116b36b1325308bbc7b368'),('public.protect_survey_address()','f2c82f9c423b45fa60fc191048b09c3645803847371cf03fbbf1a1ec391d3260'),('public.record_survey_purchase(text,text,uuid,integer,text,boolean)','5a054d2cae96b82d50cf390800fe4ac9aefaa23a71e961ae96e325eff461efed'),('public.revoke_survey_purchase(text,text)','09d97cbf0f492925affe2eca085eebdbaa12863269c6f7751be957678b77d433')) expected(signature,digest) left join pg_proc p on p.oid=to_regprocedure(expected.signature)),
 'rls_auto_enable',(select jsonb_build_object('present',p.oid is not null,'return_type',p.prorettype::regtype::text,
 'owner',pg_get_userbyid(p.proowner),'definer',p.prosecdef,'settings',p.proconfig,'acl',p.proacl::text,
 'anon_execute',coalesce(has_function_privilege('anon',p.oid,'EXECUTE'),false),
 'authenticated_execute',coalesce(has_function_privilege('authenticated',p.oid,'EXECUTE'),false),
 'body_sha256',encode(sha256(convert_to(replace(p.prosrc,E'\r\n',E'\n'),'UTF8')),'hex'),
 'extension_membership',(select jsonb_agg(e.extname) from pg_depend d join pg_extension e on e.oid=d.refobjid where d.classid='pg_proc'::regclass and d.objid=p.oid and d.refclassid='pg_extension'::regclass and d.deptype='e'))
 from (select to_regprocedure('public.rls_auto_enable()') as oid) target left join pg_proc p on p.oid=target.oid),
 'ddl_handlers',coalesce((select jsonb_agg(jsonb_build_object('trigger',e.evtname,'event',e.evtevent,'enabled',e.evtenabled,'tags',e.evttags,
 'function_schema',n.nspname,'function',p.proname,'owner',pg_get_userbyid(p.proowner),'definer',p.prosecdef,'settings',p.proconfig,
 'body_sha256',encode(sha256(convert_to(replace(p.prosrc,E'\r\n',E'\n'),'UTF8')),'hex'),
 'references_network_related_names',coalesce(lower(p.prosrc) ~ '(http_(post|get)|net[.]|pg_net|dblink|curl|smtp)',false)) order by e.evtname)
 from pg_event_trigger e join pg_proc p on p.oid=e.evtfoid join pg_namespace n on n.oid=p.pronamespace),'[]'::jsonb),
 'default_privileges_expanded',coalesce((select jsonb_agg(jsonb_build_object('owner',pg_get_userbyid(d.defaclrole),
 'schema',d.defaclnamespace::regnamespace::text,'object_type',d.defaclobjtype,
 'grantee',case when a.grantee=0 then 'PUBLIC' else pg_get_userbyid(a.grantee) end,'privilege',a.privilege_type,'grantable',a.is_grantable)
 order by d.defaclrole,d.defaclnamespace,d.defaclobjtype,a.grantee,a.privilege_type)
 from pg_default_acl d cross join lateral aclexplode(d.defaclacl) a),'[]'::jsonb)
) as production_reconciliation from baseline;
-- RLS does not protect TRUNCATE/REFERENCES. ACL output also exposes MAINTAIN
-- where that server version supports it. Defaults do not prove current table grants.
-- Network-name flags can be false positives; absence is NOT proof of no dynamic calls.
-- Validate any unfamiliar provider handler source PRIVATELY; never publish embedded secrets.
