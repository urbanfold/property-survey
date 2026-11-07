-- REVIEW ONLY. Never execute without separate production approval. Source 5d434a78ac1f997c86b9c92646771de2018cad04.
-- Target arnzqizcycesukplmvuc; SQL acknowledgement is NOT independent proof of server identity.
-- Replace ONLY the two NOT_APPROVED/REVIEW_REQUIRED parameter literals after review/approval.
-- Confirm the actual Dashboard project independently; do not copy a staging fingerprint.
begin;
set local lock_timeout='5s';
set local statement_timeout='60s';
set local urbanfold.release_ack='NOT_APPROVED';
set local urbanfold.reviewed_baseline_sha256='REVIEW_REQUIRED';
do $$ declare baseline jsonb;functions jsonb;begin

 if not pg_try_advisory_xact_lock(hashtextextended('urbanfold.production.backend.release',0)) then raise exception 'Another reviewed installation is running.';end if;
 if current_user<>'postgres' or auth.uid() is not null or auth.jwt()->>'role' is not null then raise exception 'Trusted postgres/no simulated JWT session required.';end if;
 if current_setting('urbanfold.release_ack',true) is distinct from 'APPROVED arnzqizcycesukplmvuc 5d434a78ac1f997c86b9c92646771de2018cad04' then raise exception 'No production execution approval acknowledgement.';end if;
 if obj_description(to_regclass('public.properties'),'pg_class') like 'Urbanfold-Survey-Staging%' then raise exception 'Staging database rejected.';end if;
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
) into baseline;
 if current_setting('urbanfold.reviewed_baseline_sha256',true) is distinct from encode(sha256(convert_to(baseline::text,'UTF8')),'hex') then raise exception 'Reviewed production baseline fingerprint missing or changed. STOP; do not bypass.';end if;
 if (select count(*) from storage.buckets where id in('exterior-photos','sketch-photos','room-photos') and not public)<>3 then raise exception 'Private buckets required.';end if;
 if (select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relname in('properties','extensions','rooms','exterior_photos','extension_photos','sketch_photos','room_photos','survey_free_allocations','survey_credit_purchases','survey_credit_revocations') and c.relkind='r' and c.relrowsecurity)<>10 then raise exception 'Ten existing RLS-enabled app/credit tables required.';end if;
 if not exists(select 1 from pg_class where oid='storage.objects'::regclass and relrowsecurity) then raise exception 'Storage RLS required.';end if;
 select (select jsonb_agg(jsonb_build_object('signature',expected.signature,'exists',p.oid is not null,'identity_arguments',pg_get_function_identity_arguments(p.oid),'return_type',p.prorettype::regtype::text,'language',(select lanname from pg_language where oid=p.prolang),
 'body_matches_reviewed_source',coalesce(encode(sha256(convert_to(btrim(replace(p.prosrc,E'\r\n',E'\n'),E' \t\n\r'),'UTF8')),'hex')=expected.digest,false),
 'owner',pg_get_userbyid(p.proowner),'definer',p.prosecdef,'settings',p.proconfig,
 'anon_execute',coalesce(has_function_privilege('anon',p.oid,'EXECUTE'),false),
 'authenticated_execute',coalesce(has_function_privilege('authenticated',p.oid,'EXECUTE'),false),
 'service_execute',coalesce(has_function_privilege('service_role',p.oid,'EXECUTE'),false),
 'acl',p.proacl::text) order by expected.signature)
 from (values ('public.get_survey_allowance()','3b3b5e7c335a16a91c9f447b4ac8fd62b8f6e584273d9762c70c70a60be46ad5'),('public.enforce_survey_allowance()','2600d2e67866d1163846b11be2035a32dd0c6ea9e4116b36b1325308bbc7b368'),('public.protect_survey_address()','f2c82f9c423b45fa60fc191048b09c3645803847371cf03fbbf1a1ec391d3260'),('public.record_survey_purchase(text,text,uuid,integer,text,boolean)','5a054d2cae96b82d50cf390800fe4ac9aefaa23a71e961ae96e325eff461efed'),('public.revoke_survey_purchase(text,text)','09d97cbf0f492925affe2eca085eebdbaa12863269c6f7751be957678b77d433')) expected(signature,digest) left join pg_proc p on p.oid=to_regprocedure(expected.signature)) into functions;
 if exists(select 1 from jsonb_array_elements(functions) f where not (f->>'body_matches_reviewed_source')::boolean or f->>'owner'<>'postgres' or not (f->>'definer')::boolean or not ((f->'settings') ? 'search_path=""' or (f->'settings') ? 'search_path=')
 or (f->>'anon_execute')::boolean or (f->>'authenticated_execute')::boolean is distinct from (f->>'signature'='public.get_survey_allowance()')
 or (f->>'signature' like 'public.record_survey_purchase%' or f->>'signature' like 'public.revoke_survey_purchase%') and not (f->>'service_execute')::boolean) then raise exception 'Existing002 function source/ACL differs; review targeted correction first, never reinstall002 blindly.';end if;
 if (select count(*) from pg_trigger where tgrelid='public.properties'::regclass and tgname in('urbanfold_survey_allowance','urbanfold_protect_address') and tgenabled='O')<>2 then raise exception 'Existing credit/address triggers must be enabled.';end if;

 if (select jsonb_array_length(baseline->'billing_functions'))<>5 then raise exception 'Unexpected billing helper overloads.';end if;
 if exists(select 1 from jsonb_array_elements('[{"table": "extension_photos", "column": "id", "type": "uuid"}, {"table": "extension_photos", "column": "property_id", "type": "uuid"}, {"table": "extension_photos", "column": "photo_url", "type": "text"}, {"table": "extension_photos", "column": "created_at", "type": "timestamp with time zone"}, {"table": "extensions", "column": "id", "type": "uuid"}, {"table": "extensions", "column": "property_id", "type": "uuid"}, {"table": "extensions", "column": "extension_types", "type": "jsonb"}, {"table": "extensions", "column": "description", "type": "text"}, {"table": "extensions", "column": "width", "type": "numeric"}, {"table": "extensions", "column": "length", "type": "numeric"}, {"table": "extensions", "column": "created_at", "type": "timestamp with time zone"}, {"table": "exterior_photos", "column": "id", "type": "uuid"}, {"table": "exterior_photos", "column": "property_id", "type": "uuid"}, {"table": "exterior_photos", "column": "elevation_type", "type": "text"}, {"table": "exterior_photos", "column": "photo_url", "type": "text"}, {"table": "exterior_photos", "column": "created_at", "type": "timestamp with time zone"}, {"table": "properties", "column": "id", "type": "uuid"}, {"table": "properties", "column": "user_id", "type": "uuid"}, {"table": "properties", "column": "surveyor_name", "type": "text"}, {"table": "properties", "column": "address", "type": "text"}, {"table": "properties", "column": "postcode", "type": "text"}, {"table": "properties", "column": "property_type", "type": "text"}, {"table": "properties", "column": "notes", "type": "text"}, {"table": "properties", "column": "status", "type": "text"}, {"table": "properties", "column": "created_at", "type": "timestamp with time zone"}, {"table": "properties", "column": "client_email", "type": "text"}, {"table": "properties", "column": "last_submitted_at", "type": "timestamp with time zone"}, {"table": "properties", "column": "address_locked", "type": "boolean"}, {"table": "room_photos", "column": "id", "type": "uuid"}, {"table": "room_photos", "column": "room_id", "type": "uuid"}, {"table": "room_photos", "column": "photo_url", "type": "text"}, {"table": "room_photos", "column": "created_at", "type": "timestamp with time zone"}, {"table": "rooms", "column": "id", "type": "uuid"}, {"table": "rooms", "column": "property_id", "type": "uuid"}, {"table": "rooms", "column": "room_name", "type": "text"}, {"table": "rooms", "column": "shape", "type": "text"}, {"table": "rooms", "column": "dimensions", "type": "jsonb"}, {"table": "rooms", "column": "additional_measurements", "type": "text"}, {"table": "rooms", "column": "created_at", "type": "timestamp with time zone"}, {"table": "sketch_photos", "column": "id", "type": "uuid"}, {"table": "sketch_photos", "column": "property_id", "type": "uuid"}, {"table": "sketch_photos", "column": "photo_url", "type": "text"}, {"table": "sketch_photos", "column": "created_at", "type": "timestamp with time zone"}, {"table": "survey_credit_purchases", "column": "checkout_session_id", "type": "text"}, {"table": "survey_credit_purchases", "column": "payment_intent_id", "type": "text"}, {"table": "survey_credit_purchases", "column": "user_id", "type": "uuid"}, {"table": "survey_credit_purchases", "column": "amount_total", "type": "integer"}, {"table": "survey_credit_purchases", "column": "currency", "type": "text"}, {"table": "survey_credit_purchases", "column": "live_mode", "type": "boolean"}, {"table": "survey_credit_purchases", "column": "purchased_at", "type": "timestamp with time zone"}, {"table": "survey_credit_purchases", "column": "redeemed_property_id", "type": "uuid"}, {"table": "survey_credit_purchases", "column": "redeemed_at", "type": "timestamp with time zone"}, {"table": "survey_credit_revocations", "column": "payment_intent_id", "type": "text"}, {"table": "survey_credit_revocations", "column": "reason", "type": "text"}, {"table": "survey_credit_revocations", "column": "recorded_at", "type": "timestamp with time zone"}, {"table": "survey_free_allocations", "column": "user_id", "type": "uuid"}, {"table": "survey_free_allocations", "column": "property_id", "type": "uuid"}, {"table": "survey_free_allocations", "column": "allocated_at", "type": "timestamp with time zone"}]'::jsonb) required where not exists(select 1 from jsonb_array_elements(baseline->'columns') actual where actual->>'table'=required->>'table' and actual->>'column'=required->>'column' and (actual->>'type'=required->>'type' or (required->>'table'='extensions' and required->>'column' in('width','length') and required->>'type'='numeric' and actual->>'type'='numeric(5,2)')))) then raise exception 'Required application columns/types differ from reviewed source model. Review compatibility before proceeding.';end if;
 if (select policies from (select baseline->'policies' as policies) s) is distinct from '[{"cmd": "ALL", "name": "urbanfold_manage", "check": "(EXISTS ( SELECT 1\n   FROM properties p\n  WHERE ((p.id = extension_photos.property_id) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> ''email''::text) = ''urbanfolduk@gmail.com''::text)))))", "roles": ["authenticated"], "table": "extension_photos", "using": "(EXISTS ( SELECT 1\n   FROM properties p\n  WHERE ((p.id = extension_photos.property_id) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> ''email''::text) = ''urbanfolduk@gmail.com''::text)))))", "schema": "public", "permissive": "PERMISSIVE"}, {"cmd": "ALL", "name": "urbanfold_manage", "check": "(EXISTS ( SELECT 1\n   FROM properties p\n  WHERE ((p.id = extensions.property_id) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> ''email''::text) = ''urbanfolduk@gmail.com''::text)))))", "roles": ["authenticated"], "table": "extensions", "using": "(EXISTS ( SELECT 1\n   FROM properties p\n  WHERE ((p.id = extensions.property_id) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> ''email''::text) = ''urbanfolduk@gmail.com''::text)))))", "schema": "public", "permissive": "PERMISSIVE"}, {"cmd": "ALL", "name": "urbanfold_manage", "check": "(EXISTS ( SELECT 1\n   FROM properties p\n  WHERE ((p.id = exterior_photos.property_id) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> ''email''::text) = ''urbanfolduk@gmail.com''::text)))))", "roles": ["authenticated"], "table": "exterior_photos", "using": "(EXISTS ( SELECT 1\n   FROM properties p\n  WHERE ((p.id = exterior_photos.property_id) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> ''email''::text) = ''urbanfolduk@gmail.com''::text)))))", "schema": "public", "permissive": "PERMISSIVE"}, {"cmd": "INSERT", "name": "urbanfold_properties_insert", "check": "((user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> ''email''::text) = ''urbanfolduk@gmail.com''::text))", "roles": ["authenticated"], "table": "properties", "using": null, "schema": "public", "permissive": "PERMISSIVE"}, {"cmd": "SELECT", "name": "urbanfold_properties_select", "check": null, "roles": ["authenticated"], "table": "properties", "using": "((user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> ''email''::text) = ''urbanfolduk@gmail.com''::text))", "schema": "public", "permissive": "PERMISSIVE"}, {"cmd": "UPDATE", "name": "urbanfold_properties_update", "check": "((user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> ''email''::text) = ''urbanfolduk@gmail.com''::text))", "roles": ["authenticated"], "table": "properties", "using": "((user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> ''email''::text) = ''urbanfolduk@gmail.com''::text))", "schema": "public", "permissive": "PERMISSIVE"}, {"cmd": "ALL", "name": "urbanfold_manage", "check": "(EXISTS ( SELECT 1\n   FROM (rooms r\n     JOIN properties p ON ((p.id = r.property_id)))\n  WHERE ((r.id = room_photos.room_id) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> ''email''::text) = ''urbanfolduk@gmail.com''::text)))))", "roles": ["authenticated"], "table": "room_photos", "using": "(EXISTS ( SELECT 1\n   FROM (rooms r\n     JOIN properties p ON ((p.id = r.property_id)))\n  WHERE ((r.id = room_photos.room_id) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> ''email''::text) = ''urbanfolduk@gmail.com''::text)))))", "schema": "public", "permissive": "PERMISSIVE"}, {"cmd": "ALL", "name": "urbanfold_manage", "check": "(EXISTS ( SELECT 1\n   FROM properties p\n  WHERE ((p.id = rooms.property_id) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> ''email''::text) = ''urbanfolduk@gmail.com''::text)))))", "roles": ["authenticated"], "table": "rooms", "using": "(EXISTS ( SELECT 1\n   FROM properties p\n  WHERE ((p.id = rooms.property_id) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> ''email''::text) = ''urbanfolduk@gmail.com''::text)))))", "schema": "public", "permissive": "PERMISSIVE"}, {"cmd": "ALL", "name": "urbanfold_manage", "check": "(EXISTS ( SELECT 1\n   FROM properties p\n  WHERE ((p.id = sketch_photos.property_id) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> ''email''::text) = ''urbanfolduk@gmail.com''::text)))))", "roles": ["authenticated"], "table": "sketch_photos", "using": "(EXISTS ( SELECT 1\n   FROM properties p\n  WHERE ((p.id = sketch_photos.property_id) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> ''email''::text) = ''urbanfolduk@gmail.com''::text)))))", "schema": "public", "permissive": "PERMISSIVE"}, {"cmd": "SELECT", "name": "urbanfold_purchase_read", "check": null, "roles": ["authenticated"], "table": "survey_credit_purchases", "using": "((user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> ''email''::text) = ''urbanfolduk@gmail.com''::text))", "schema": "public", "permissive": "PERMISSIVE"}, {"cmd": "SELECT", "name": "urbanfold_free_read", "check": null, "roles": ["authenticated"], "table": "survey_free_allocations", "using": "((user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> ''email''::text) = ''urbanfolduk@gmail.com''::text))", "schema": "public", "permissive": "PERMISSIVE"}, {"cmd": "INSERT", "name": "urbanfold_storage_insert", "check": "((bucket_id = ANY (ARRAY[''exterior-photos''::text, ''sketch-photos''::text, ''room-photos''::text])) AND (EXISTS ( SELECT 1\n   FROM properties p\n  WHERE (((p.id)::text = (storage.foldername(objects.name))[1]) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> ''email''::text) = ''urbanfolduk@gmail.com''::text))))))", "roles": ["authenticated"], "table": "objects", "using": null, "schema": "storage", "permissive": "PERMISSIVE"}, {"cmd": "SELECT", "name": "urbanfold_storage_select", "check": null, "roles": ["authenticated"], "table": "objects", "using": "((bucket_id = ANY (ARRAY[''exterior-photos''::text, ''sketch-photos''::text, ''room-photos''::text])) AND (EXISTS ( SELECT 1\n   FROM properties p\n  WHERE (((p.id)::text = (storage.foldername(objects.name))[1]) AND ((p.user_id = ( SELECT auth.uid() AS uid)) OR ((( SELECT auth.jwt() AS jwt) ->> ''email''::text) = ''urbanfolduk@gmail.com''::text))))))", "schema": "storage", "permissive": "PERMISSIVE"}]'::jsonb then raise exception '001/002 policy mismatch/additional policy. Review exact differences; do not blanket replace policies.';end if;
if exists(select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relname in('newsletter_preferences','newsletter_consent_events','registration_notification_events'))
 or exists(select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname in('record_auth_registration','get_newsletter_preference','set_newsletter_preference','recover_stale_registration_notifications','claim_registration_notification','finish_registration_notification')) then raise exception 'Fresh-only target objects already exist. STOP and review; never reset/reapply.';end if;
 if to_regclass('public.survey_notification_events') is null then raise exception 'Install/review003 first.';end if;
 if exists(select 1 from pg_trigger where tgrelid='auth.users'::regclass and tgname in('urbanfold_auth_signup','urbanfold_auth_first_confirmation')) then raise exception 'Reserved Auth trigger already exists.';end if;
end $$;
-- BEGIN UNMODIFIED PINNED MIGRATION BODY supabase/004_verified_registration_notifications.sql

create table if not exists public.newsletter_preferences(
 user_id uuid primary key references auth.users(id) on delete cascade,
 signup_opt_in_requested boolean,
 opted_in boolean not null default false,
 verified_at timestamptz,
 consent_version text not null default '2026-10-23',
 updated_at timestamptz not null default clock_timestamp()
);
create table if not exists public.newsletter_consent_events(
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references auth.users(id) on delete cascade,
 choice boolean,
 action text not null check(action in('signup_request','email_verified','preference_change')),
 source text not null,
 consent_version text not null,
 consent_text text not null,
 occurred_at timestamptz not null default clock_timestamp()
);
create index if not exists newsletter_consent_user_time on public.newsletter_consent_events(user_id,occurred_at);
create table if not exists public.registration_notification_events(
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null unique references auth.users(id) on delete cascade,
 registration_email text not null,
 registered_at timestamptz not null,
 verified_at timestamptz not null,
 newsletter_signup_choice boolean,
 newsletter_opted_in_at_verification boolean not null,
 state text not null default 'pending' check(state in('pending','sending','accepted','uncertain')),
 created_at timestamptz not null default clock_timestamp(),
 finished_at timestamptz,
 claim_started_at timestamptz,
 completion_reason text
);
-- Support reapplying the candidate after a separately reviewed early-004 install.
alter table public.registration_notification_events add column if not exists claim_started_at timestamptz;
alter table public.registration_notification_events add column if not exists completion_reason text;
-- Legacy attempts have unknown claim times. Count them conservatively from this
-- migration, rather than exempting them from the new rolling limits.
update public.registration_notification_events set claim_started_at=clock_timestamp()
 where state<>'pending' and claim_started_at is null;
create index if not exists registration_notification_pending on public.registration_notification_events(created_at) where state='pending';
create index if not exists registration_notification_claim_time on public.registration_notification_events(claim_started_at)
 where claim_started_at is not null;
alter table public.newsletter_preferences enable row level security;
alter table public.newsletter_consent_events enable row level security;
alter table public.registration_notification_events enable row level security;
revoke all on public.newsletter_preferences,public.newsletter_consent_events,public.registration_notification_events from public,anon,authenticated;
grant select on public.newsletter_preferences,public.newsletter_consent_events to authenticated;
grant all on public.newsletter_preferences,public.registration_notification_events to service_role;
revoke all on public.newsletter_consent_events from service_role;
grant select on public.newsletter_consent_events to service_role;
drop policy if exists newsletter_preferences_own on public.newsletter_preferences;
create policy newsletter_preferences_own on public.newsletter_preferences for select to authenticated using(user_id=(select auth.uid()));
drop policy if exists newsletter_consent_own on public.newsletter_consent_events;
create policy newsletter_consent_own on public.newsletter_consent_events for select to authenticated using(user_id=(select auth.uid()));

create or replace function public.record_auth_registration()
returns trigger language plpgsql security definer set search_path='' as $$
declare requested boolean;prefs public.newsletter_preferences;
 wording constant text:='Email me Urbanfold newsletters and updates (optional)';
begin
 if tg_op='INSERT' then
  requested:=case when jsonb_typeof(new.raw_user_meta_data->'newsletter_subscribed')='boolean'
    then (new.raw_user_meta_data->>'newsletter_subscribed')::boolean else false end;
  insert into public.newsletter_preferences(user_id,signup_opt_in_requested) values(new.id,requested) on conflict(user_id) do nothing;
  insert into public.newsletter_consent_events(user_id,choice,action,source,consent_version,consent_text)
  values(new.id,requested,'signup_request','auth_signup_metadata_intent','2026-10-23',wording);
 end if;
 if new.email_confirmed_at is null then return new;end if;
 if tg_op='UPDATE' then
  if old.email_confirmed_at is not null then return new;end if;
  -- Do not enqueue historical accounts or infer their original checkbox after feature installation.
  if not exists(select 1 from public.newsletter_preferences where user_id=new.id and signup_opt_in_requested is not null) then return new;end if;
 end if;
 -- Only signup intent captured at account insertion is eligible; never trust later mutable metadata.
 insert into public.newsletter_preferences(user_id) values(new.id) on conflict(user_id) do nothing;
 select * into prefs from public.newsletter_preferences where user_id=new.id for update;
 update public.newsletter_preferences set verified_at=new.email_confirmed_at,
  opted_in=coalesce(prefs.signup_opt_in_requested,false),updated_at=clock_timestamp() where user_id=new.id and verified_at is null;
 -- A user can produce only one first-confirmation notification. Email changes/reconfirmation do not resend.
 insert into public.registration_notification_events(user_id,registration_email,registered_at,verified_at,
  newsletter_signup_choice,newsletter_opted_in_at_verification)
 values(new.id,new.email,new.created_at,new.email_confirmed_at,prefs.signup_opt_in_requested,coalesce(prefs.signup_opt_in_requested,false))
 on conflict(user_id) do nothing;
 if found then
  insert into public.newsletter_consent_events(user_id,choice,action,source,consent_version,consent_text)
  values(new.id,prefs.signup_opt_in_requested,'email_verified','auth_first_confirmation','2026-10-23',wording);
 end if;
 return new;
end $$;
revoke all on function public.record_auth_registration() from public,anon,authenticated;
drop trigger if exists urbanfold_auth_signup on auth.users;
create trigger urbanfold_auth_signup after insert on auth.users for each row execute function public.record_auth_registration();
drop trigger if exists urbanfold_auth_first_confirmation on auth.users;
create trigger urbanfold_auth_first_confirmation after update of email_confirmed_at on auth.users for each row execute function public.record_auth_registration();

create or replace function public.get_newsletter_preference()
returns jsonb language plpgsql security definer set search_path='' as $$
declare person uuid:=auth.uid();prefs public.newsletter_preferences;
begin
 if person is null then raise exception 'Sign in to view newsletter preferences.' using errcode='42501';end if;
 select * into prefs from public.newsletter_preferences where user_id=person;
 return jsonb_build_object('opted_in',coalesce(prefs.opted_in,false),'recorded',prefs.user_id is not null,'consent_version','2026-10-23');
end $$;
create or replace function public.set_newsletter_preference(subscribe boolean)
returns jsonb language plpgsql security definer set search_path='' as $$
declare person uuid:=auth.uid();previous boolean;created uuid;
begin
 if person is null or subscribe is null or not exists(select 1 from auth.users where id=person and email_confirmed_at is not null) then
  raise exception 'A verified account and explicit preference are required.' using errcode='42501';end if;
 -- Serialise preference creation/updates, never allow a caller-supplied user ID or timestamp.
 perform 1 from auth.users where id=person for update;
 insert into public.newsletter_preferences(user_id,verified_at) select person,email_confirmed_at from auth.users where id=person on conflict(user_id) do nothing returning user_id into created;
 select opted_in into previous from public.newsletter_preferences where user_id=person for update;
 if created is not null or previous is distinct from subscribe then
  update public.newsletter_preferences set opted_in=subscribe,updated_at=clock_timestamp() where user_id=person;
  insert into public.newsletter_consent_events(user_id,choice,action,source,consent_version,consent_text)
  values(person,subscribe,'preference_change','authenticated_preference_form','2026-10-23','Email me Urbanfold newsletters and updates (optional)');
 end if;
 return public.get_newsletter_preference();
end $$;
revoke all on function public.get_newsletter_preference() from public,anon;
revoke all on function public.set_newsletter_preference(boolean) from public,anon;
grant execute on function public.get_newsletter_preference(),public.set_newsletter_preference(boolean) to authenticated;

-- Five minutes exceeds the worker's bounded transport/finish waits. Interrupted
-- attempts are ambiguous, never safe to automatically requeue or resend.
create or replace function public.recover_stale_registration_notifications()
returns integer language plpgsql security definer set search_path='' as $$
declare recovered integer;
begin
 perform pg_advisory_xact_lock(hashtextextended('urbanfold.registration.dispatch',0));
 update public.registration_notification_events
 set state='uncertain',finished_at=clock_timestamp(),completion_reason='worker_interrupted'
 where state='sending' and (claim_started_at is null or claim_started_at<=clock_timestamp()-interval '5 minutes');
 get diagnostics recovered=row_count;
 return recovered;
end $$;
revoke all on function public.recover_stale_registration_notifications() from public,anon,authenticated;
grant execute on function public.recover_stale_registration_notifications() to service_role;

create or replace function public.claim_registration_notification()
returns jsonb language plpgsql security definer set search_path='' as $$
declare e public.registration_notification_events; claimed_at timestamptz;
 minute_count integer;hour_count integer;retry_seconds integer:=1;next_slot timestamptz;
begin
 -- Serialize ALL callers across rows: SKIP LOCKED alone cannot enforce a global cap.
 perform pg_advisory_xact_lock(hashtextextended('urbanfold.registration.dispatch',0));
 perform public.recover_stale_registration_notifications();
 select * into e from public.registration_notification_events where state='pending' order by created_at,id for update skip locked limit 1;
 if not found then return null;end if;
 claimed_at:=clock_timestamp();
 select count(*) filter(where claim_started_at>claimed_at-interval '1 minute'),count(*)
 into minute_count,hour_count from public.registration_notification_events
 where claim_started_at>claimed_at-interval '1 hour';
 if minute_count>=5 then
  select claim_started_at+interval '1 minute' into next_slot
  from public.registration_notification_events where claim_started_at>claimed_at-interval '1 minute'
  order by claim_started_at offset (minute_count-5) limit 1;
  retry_seconds:=greatest(retry_seconds,ceil(extract(epoch from next_slot-claimed_at))::integer);
 end if;
 if hour_count>=50 then
  select claim_started_at+interval '1 hour' into next_slot
  from public.registration_notification_events where claim_started_at>claimed_at-interval '1 hour'
  order by claim_started_at offset (hour_count-50) limit 1;
  retry_seconds:=greatest(retry_seconds,ceil(extract(epoch from next_slot-claimed_at))::integer);
 end if;
 if minute_count>=5 or hour_count>=50 then
  return jsonb_build_object('status','rate_limited','retry_after_seconds',retry_seconds);
 end if;
 update public.registration_notification_events set state='sending',claim_started_at=claimed_at,
  finished_at=null,completion_reason=null where id=e.id;
 return jsonb_build_object('id',e.id,'claim_started_at',claimed_at,'user_id',e.user_id,'registration_email',e.registration_email,
  'registered_at',e.registered_at,'verified_at',e.verified_at,'newsletter_signup_choice',e.newsletter_signup_choice,
  'newsletter_opted_in_at_verification',e.newsletter_opted_in_at_verification);
end $$;
create or replace function public.finish_registration_notification(event uuid,accepted boolean)
returns void language plpgsql security definer set search_path='' as $$
begin
 update public.registration_notification_events set state=case when accepted then 'accepted' else 'uncertain' end,
 finished_at=clock_timestamp(),completion_reason=case when accepted then 'transport_accepted' else 'transport_uncertain' end
 where id=event and state='sending';
end $$;
-- New workers finish against their exact claim and inspect the persisted state.
-- A delayed worker cannot turn an already recovered/uncertain attempt accepted.
-- Keep the two-argument early-candidate RPC for migration compatibility only.
create or replace function public.finish_registration_notification(event uuid,accepted boolean,claimed_at timestamptz)
returns jsonb language plpgsql security definer set search_path='' as $$
declare persisted_state text;
begin
 update public.registration_notification_events e
 set state=case when accepted then 'accepted' else 'uncertain' end,
 finished_at=clock_timestamp(),completion_reason=case when accepted then 'transport_accepted' else 'transport_uncertain' end
 where e.id=event and e.state='sending' and e.claim_started_at=claimed_at;
 select e.state into persisted_state from public.registration_notification_events e where e.id=event;
 return jsonb_build_object('state',coalesce(persisted_state,'uncertain'));
end $$;
revoke all on function public.claim_registration_notification(),public.finish_registration_notification(uuid,boolean) from public,anon,authenticated;
grant execute on function public.claim_registration_notification(),public.finish_registration_notification(uuid,boolean) to service_role;
revoke all on function public.finish_registration_notification(uuid,boolean,timestamptz) from public,anon,authenticated;
grant execute on function public.finish_registration_notification(uuid,boolean,timestamptz) to service_role;

-- END UNMODIFIED PINNED MIGRATION BODY
do $$ declare checks jsonb;baseline jsonb;begin
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
) into baseline;
 if current_setting('urbanfold.reviewed_baseline_sha256',true) is distinct from encode(sha256(convert_to(baseline::text,'UTF8')),'hex') then raise exception 'Existing baseline changed during installation; transaction rolled back.';end if;
 select (select jsonb_agg(jsonb_build_object('signature',expected.signature,'exists',p.oid is not null,'identity_arguments',pg_get_function_identity_arguments(p.oid),'return_type',p.prorettype::regtype::text,'language',(select lanname from pg_language where oid=p.prolang),
 'body_matches_reviewed_source',coalesce(encode(sha256(convert_to(btrim(replace(p.prosrc,E'\r\n',E'\n'),E' \t\n\r'),'UTF8')),'hex')=expected.digest,false),
 'owner',pg_get_userbyid(p.proowner),'definer',p.prosecdef,'settings',p.proconfig,
 'anon_execute',coalesce(has_function_privilege('anon',p.oid,'EXECUTE'),false),
 'authenticated_execute',coalesce(has_function_privilege('authenticated',p.oid,'EXECUTE'),false),
 'service_execute',coalesce(has_function_privilege('service_role',p.oid,'EXECUTE'),false),
 'acl',p.proacl::text) order by expected.signature)
 from (values ('public.claim_survey_notification(uuid,uuid,timestamptz)','835e5f5b72c24dea7c9d16f11ac7325c2127f9fe5003eb3321cad00a5debb624'),('public.finish_survey_notification(uuid,boolean)','b42ff776b1940ee8bd685a6eb547505f8c9b9b2d6f268998908bcfe4a92edc03'),('public.record_auth_registration()','80e273428f8ee6ec8a188445d74a579baeaddf7d73e26ccb6f05b45e278696bf'),('public.get_newsletter_preference()','fc4e8efe92594f8c04390286cc54debeca4ef170044419e920df7a6ef7e99362'),('public.set_newsletter_preference(boolean)','444919b10c66067288b457364d0fc49671fd9ca9c24fee315ba0029c92c16f32'),('public.recover_stale_registration_notifications()','fdebf598b2ac3fdfc3aa6b83b5d9c64a2df86bb032152f33720260cf09523c1b'),('public.claim_registration_notification()','a5a5e8223e299445928f58342eeb77f0069e840f786c1e18ed0f1a82dc54d072'),('public.finish_registration_notification(uuid,boolean)','fbdc1a1e12be5735936e934c9997ed823a61088424b3ecf0c66460deeede3668'),('public.finish_registration_notification(uuid,boolean,timestamptz)','cc58f7efefa6b569347ab55877667dbfd1f72fb80bd76d0f2ace2bf0cf547a28')) expected(signature,digest) left join pg_proc p on p.oid=to_regprocedure(expected.signature)) into checks;
 if exists(select 1 from jsonb_array_elements(checks) f where not (f->>'body_matches_reviewed_source')::boolean
 or f->>'owner'<>'postgres' or not (f->>'definer')::boolean or not ((f->'settings') ? 'search_path=""' or (f->'settings') ? 'search_path=')
 or (f->>'anon_execute')::boolean or (f->>'authenticated_execute')::boolean is distinct from (f->>'signature' in('public.get_newsletter_preference()','public.set_newsletter_preference(boolean)'))
 or (f->>'signature' not like 'public.record_auth_registration%' and f->>'signature' not like 'public.get_newsletter_preference%' and f->>'signature' not like 'public.set_newsletter_preference%') and not (f->>'service_execute')::boolean) then raise exception 'New function fingerprint/security checks failed; entire installation transaction rolled back.';end if;
 if exists(select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relname in('survey_notification_events','newsletter_preferences','newsletter_consent_events','registration_notification_events') and
 (not c.relrowsecurity or pg_get_userbyid(c.relowner)<>'postgres' or has_table_privilege('anon',c.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
 or has_table_privilege('authenticated',c.oid,'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
 or has_table_privilege('authenticated',c.oid,'SELECT') is distinct from (c.relname in('newsletter_preferences','newsletter_consent_events')))) then raise exception 'New table RLS/client access checks failed; transaction rolled back.';end if;
 if to_regclass('public.newsletter_consent_events') is not null then
  if has_table_privilege('service_role','public.newsletter_consent_events','INSERT,UPDATE,DELETE,TRUNCATE') then raise exception 'Consent audit must be read-only to service_role.';end if;
 end if;
end $$;
commit;
