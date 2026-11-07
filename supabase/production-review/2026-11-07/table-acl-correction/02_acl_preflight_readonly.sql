-- REVIEW ONLY. DO NOT EXECUTE WITHOUT INDEPENDENT REVIEW AND SEPARATE APPROVAL.
-- Target arnzqizcycesukplmvuc; SQL acknowledgements/hashes do NOT independently prove server identity.
-- Source review commit 1d1c934ce39650433a58ec70640d4f3671ad018f. No global defaults, RLS, Storage or credit changes.
-- SELECT-only, no data rows/credentials/function source returned.
with baseline as(select jsonb_build_object(
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
) as metadata), permissions as(select jsonb_build_object(
 'api_roles',coalesce((select jsonb_agg(jsonb_build_object('role',rolname,'superuser',rolsuper,
 'bypass_rls',rolbypassrls,'can_login',rolcanlogin,'inherit',rolinherit) order by rolname)
 from pg_roles where rolname in('anon','authenticated')),'[]'::jsonb),
 'tables',coalesce((select jsonb_agg(jsonb_build_object('schema',n.nspname,'table',c.relname,'kind',c.relkind,
 'owner',pg_get_userbyid(c.relowner),'rls',c.relrowsecurity,'force_rls',c.relforcerowsecurity,
 'acl',coalesce((select jsonb_agg(jsonb_build_object('grantor',pg_get_userbyid(a.grantor),
 'grantee',case when a.grantee=0 then 'PUBLIC' else pg_get_userbyid(a.grantee) end,
 'privilege',a.privilege_type,'grantable',a.is_grantable)
 order by pg_get_userbyid(a.grantor)::text collate "C",(case when a.grantee=0 then 'PUBLIC' else pg_get_userbyid(a.grantee) end)::text collate "C",a.privilege_type collate "C")
 from aclexplode(coalesce(c.relacl,acldefault('r',c.relowner))) a),'[]'::jsonb),
 'column_acls',coalesce((select jsonb_agg(jsonb_build_object('column',att.attname,'acl',
 coalesce((select jsonb_agg(jsonb_build_object('grantor',pg_get_userbyid(x.grantor),
 'grantee',case when x.grantee=0 then 'PUBLIC' else pg_get_userbyid(x.grantee) end,
 'privilege',x.privilege_type,'grantable',x.is_grantable)
 order by pg_get_userbyid(x.grantor)::text collate "C",(case when x.grantee=0 then 'PUBLIC' else pg_get_userbyid(x.grantee) end)::text collate "C",x.privilege_type collate "C")
 from aclexplode(att.attacl) x),'[]'::jsonb)) order by att.attnum) from pg_attribute att
 where att.attrelid=c.oid and att.attnum>0 and not att.attisdropped and att.attacl is not null),'[]'::jsonb),
 'api_crud',coalesce((select jsonb_agg(jsonb_build_object('role',r.rolname,
 'select',has_table_privilege(r.oid,c.oid,'SELECT'),'insert',has_table_privilege(r.oid,c.oid,'INSERT'),
 'update',has_table_privilege(r.oid,c.oid,'UPDATE'),'delete',has_table_privilege(r.oid,c.oid,'DELETE'),
 'inherits_owner',pg_has_role(r.oid,c.relowner,'USAGE')) order by r.rolname)
 from pg_roles r where r.rolname in('anon','authenticated')),'[]'::jsonb)) order by c.relname::text collate "C")
 from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relname in('properties','extensions','rooms','exterior_photos','extension_photos','sketch_photos','room_photos')),'[]'::jsonb),
 'untouched_tables',coalesce((select jsonb_agg(jsonb_build_object('schema',n.nspname,'table',c.relname,'kind',c.relkind,
 'owner',pg_get_userbyid(c.relowner),'rls',c.relrowsecurity,'force_rls',c.relforcerowsecurity,
 'acl',coalesce((select jsonb_agg(jsonb_build_object('grantor',pg_get_userbyid(a.grantor),
 'grantee',case when a.grantee=0 then 'PUBLIC' else pg_get_userbyid(a.grantee) end,
 'privilege',a.privilege_type,'grantable',a.is_grantable)
 order by pg_get_userbyid(a.grantor)::text collate "C",(case when a.grantee=0 then 'PUBLIC' else pg_get_userbyid(a.grantee) end)::text collate "C",a.privilege_type collate "C")
 from aclexplode(coalesce(c.relacl,acldefault('r',c.relowner))) a),'[]'::jsonb),
 'column_acls',coalesce((select jsonb_agg(jsonb_build_object('column',att.attname,'acl',
 coalesce((select jsonb_agg(jsonb_build_object('grantor',pg_get_userbyid(x.grantor),
 'grantee',case when x.grantee=0 then 'PUBLIC' else pg_get_userbyid(x.grantee) end,
 'privilege',x.privilege_type,'grantable',x.is_grantable)
 order by pg_get_userbyid(x.grantor)::text collate "C",(case when x.grantee=0 then 'PUBLIC' else pg_get_userbyid(x.grantee) end)::text collate "C",x.privilege_type collate "C")
 from aclexplode(att.attacl) x),'[]'::jsonb)) order by att.attnum) from pg_attribute att
 where att.attrelid=c.oid and att.attnum>0 and not att.attisdropped and att.attacl is not null),'[]'::jsonb),
 'api_crud',coalesce((select jsonb_agg(jsonb_build_object('role',r.rolname,
 'select',has_table_privilege(r.oid,c.oid,'SELECT'),'insert',has_table_privilege(r.oid,c.oid,'INSERT'),
 'update',has_table_privilege(r.oid,c.oid,'UPDATE'),'delete',has_table_privilege(r.oid,c.oid,'DELETE'),
 'inherits_owner',pg_has_role(r.oid,c.relowner,'USAGE')) order by r.rolname)
 from pg_roles r where r.rolname in('anon','authenticated')),'[]'::jsonb)) order by n.nspname,c.relname)
 from pg_class c join pg_namespace n on n.oid=c.relnamespace where
 (n.nspname='public' and c.relname in('survey_free_allocations','survey_credit_purchases','survey_credit_revocations'))
 or (n.nspname='storage' and c.relname='objects')),'[]'::jsonb)
) as state)
select jsonb_build_object('expected_project','arnzqizcycesukplmvuc','execution_role',current_user,
 'server_version_num',current_setting('server_version_num'),
 'baseline_sha256',encode(sha256(convert_to((metadata)::text,'UTF8')),'hex'),'baseline_matches_last_report',encode(sha256(convert_to((metadata)::text,'UTF8')),'hex')='10fa3ce6272648b31c662735e549b2e78b032a63cceb6e5f1d862f5d5052e4f6',
 'acl_sha256',encode(sha256(convert_to((state)::text,'UTF8')),'hex'),'acl_snapshot',state,
 'effective_excess_privileges',(select jsonb_agg(jsonb_build_object('table',c.relname,'role',r.rolname,'privilege',privilege,
 'allowed',has_table_privilege(r.oid,c.oid,privilege)) order by c.relname,r.rolname,privilege)
 from pg_class c join pg_namespace n on n.oid=c.relnamespace cross join pg_roles r
 cross join unnest(array['TRUNCATE','REFERENCES','TRIGGER','MAINTAIN']) privilege
 where n.nspname='public' and c.relname in('properties','extensions','rooms','exterior_photos','extension_photos','sketch_photos','room_photos') and r.rolname in('anon','authenticated')),
 'watchers',coalesce((select jsonb_agg(jsonb_build_object('schema',n.nspname,'name',p.proname,'owner',pg_get_userbyid(p.proowner),
 'return_type',p.prorettype::regtype::text,'definer',p.prosecdef,'settings',p.proconfig,
 'body_sha256',encode(sha256(convert_to(replace(p.prosrc,E'\r\n',E'\n'),'UTF8')),'hex')) order by p.proname)
 from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='extensions' and p.proname in('pgrst_ddl_watch','pgrst_drop_watch')),'[]'::jsonb)
) as table_acl_preflight from baseline,permissions;
-- Inspect each target grantor/grant option and column ACL before installation approval.
-- Snapshot hashes attest reviewed metadata/state, not historical who/when provenance.
