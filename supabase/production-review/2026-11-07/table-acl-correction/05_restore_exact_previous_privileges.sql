-- REVIEW ONLY. DO NOT EXECUTE WITHOUT INDEPENDENT REVIEW AND SEPARATE APPROVAL.
-- Target arnzqizcycesukplmvuc; SQL acknowledgements/hashes do NOT independently prove server identity.
-- Source review commit 1d1c934ce39650433a58ec70640d4f3671ad018f. No global defaults, RLS, Storage or credit changes.
-- SEPARATE approval needed: restores the old excessive rights, not a desirable steady state.
-- Requires the ORIGINAL saved02 ACL digest; never a guessed/current digest.
begin;
set local lock_timeout='5s';
set local statement_timeout='30s';
set local urbanfold.acl_ack='NOT_APPROVED';
set local urbanfold.acl_action='NOT_APPROVED';
set local urbanfold.reviewed_baseline_sha256='REVIEW_REQUIRED';
set local urbanfold.original_acl_sha256='REVIEW_REQUIRED';
do $$ declare baseline_before jsonb;baseline_after jsonb;before_acl jsonb;after_acl jsonb;expected_acl jsonb;effective jsonb;
begin

 if current_user<>'postgres' then raise exception 'Trusted postgres operator required; never change role to bypass.';end if;
 if current_setting('server_version_num')::integer<170000 then raise exception 'Reviewed MAINTAIN correction requires PostgreSQL17 or newer.';end if;
 if auth.uid() is not null or auth.jwt()->>'role' is not null then raise exception 'No simulated/customer JWT claims allowed.';end if;
 if obj_description(to_regclass('public.properties'),'pg_class') like 'Urbanfold-Survey-Staging%' then raise exception 'Staging rejected; independently verify production project.';end if;
 if current_setting('urbanfold.acl_ack',true) is distinct from 'APPROVED arnzqizcycesukplmvuc TABLE ACL REVIEW 1d1c934ce39650433a58ec70640d4f3671ad018f' then raise exception 'Separate permission-change approval required.';end if;
 if not pg_try_advisory_xact_lock(hashtextextended('urbanfold.production.backend.release',0)) then raise exception 'Another reviewed release operation is running.';end if;
 select jsonb_build_object(
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
) into baseline_before;
 if current_setting('urbanfold.reviewed_baseline_sha256',true) is distinct from encode(sha256(convert_to((baseline_before)::text,'UTF8')),'hex') then raise exception 'Reviewed baseline missing/changed; stop.';end if;
 select jsonb_build_object(
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
) into before_acl;
 if jsonb_array_length(before_acl->'tables')<>7 or jsonb_array_length(before_acl->'api_roles')<>2
 or exists(select 1 from jsonb_array_elements(before_acl->'tables') t where t->>'kind'<>'r' or t->>'owner'<>'postgres' or not (t->>'rls')::boolean)
 or exists(select 1 from jsonb_array_elements(before_acl->'api_roles') r where (r->>'superuser')::boolean or (r->>'bypass_rls')::boolean or (r->>'can_login')::boolean)
 or exists(select 1 from jsonb_array_elements(before_acl->'tables') t cross join lateral jsonb_array_elements(t->'api_crud') r
 where (r->>'inherits_owner')::boolean or not ((r->>'select')::boolean and (r->>'insert')::boolean and (r->>'update')::boolean and (r->>'delete')::boolean))
 then raise exception 'Unexpected target/role/RLS/CRUD state; no permissions changed.';end if;
 -- Column REFERENCES can survive or complicate table-level revocation/rollback.
 if exists(select 1 from jsonb_array_elements(before_acl->'tables') t cross join lateral jsonb_array_elements(t->'column_acls') col
 cross join lateral jsonb_array_elements(col->'acl') a where a->>'privilege'='REFERENCES' and a->>'grantee' in('PUBLIC','anon','authenticated')) then
 raise exception 'Explicit client/PUBLIC column REFERENCES needs separate review; not touched.';end if;

 if current_setting('urbanfold.acl_action',true) is distinct from 'APPROVED RESTORE56 ORIGINAL PRIVILEGES' then raise exception 'Separate specific rollback approval required.';end if;
 select (select jsonb_agg(jsonb_build_object('table',c.relname,'role',r.rolname,'privilege',privilege,
 'allowed',has_table_privilege(r.oid,c.oid,privilege)) order by c.relname,r.rolname,privilege)
 from pg_class c join pg_namespace n on n.oid=c.relnamespace cross join pg_roles r
 cross join unnest(array['TRUNCATE','REFERENCES','TRIGGER','MAINTAIN']) privilege
 where n.nspname='public' and c.relname in('properties','extensions','rooms','exterior_photos','extension_photos','sketch_photos','room_photos') and r.rolname in('anon','authenticated')) into effective;
 if coalesce(jsonb_array_length(effective),0)<>56 or exists(select 1 from jsonb_array_elements(effective) e where (e->>'allowed')::boolean is distinct from false) then
 raise exception 'Rollback needs the fully corrected state, not partial/already restored permissions.';end if;
 expected_acl:=jsonb_set(before_acl,'{tables}',coalesce((select jsonb_agg(
 jsonb_set(t,'{acl}',coalesce((select jsonb_agg(a order by (a->>'grantor') collate "C",(a->>'grantee') collate "C",(a->>'privilege') collate "C")
 from (select a from jsonb_array_elements(t->'acl') a
 union all select jsonb_build_object('grantor','postgres','grantee',role_name,'privilege',priv_name,'grantable',false)
 from unnest(array['anon','authenticated']) role_name cross join unnest(array['TRUNCATE','REFERENCES','TRIGGER','MAINTAIN']) priv_name) entries),'[]'::jsonb)) order by (t->>'table') collate "C")
 from jsonb_array_elements(before_acl->'tables') t),'[]'::jsonb));
 if current_setting('urbanfold.original_acl_sha256',true) is distinct from encode(sha256(convert_to((expected_acl)::text,'UTF8')),'hex') then
 raise exception 'Inverse snapshot does not match saved original ACL. Stop: unrelated changes or unsupported original grantor/options; never broaden rollback.';end if;
 -- THE ONLY ROLLBACK CHANGE: exact56 former entries, no grant options.
 grant truncate, references, trigger, maintain on table public.properties, public.extensions, public.rooms, public.exterior_photos, public.extension_photos, public.sketch_photos, public.room_photos to anon, authenticated;

 select jsonb_build_object(
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
) into after_acl;
 select jsonb_build_object(
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
) into baseline_after;
 if baseline_after is distinct from baseline_before or after_acl is distinct from expected_acl then
 raise exception 'Unrelated schema/grants/roles/CRUD/columns/Storage/credit ACL changed; transaction rolled back.';end if;

 if current_setting('urbanfold.original_acl_sha256',true) is distinct from encode(sha256(convert_to((after_acl)::text,'UTF8')),'hex') then raise exception 'Rollback ACL differs from original; transaction rolled back.';end if;
end $$;
commit;
