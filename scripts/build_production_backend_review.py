"""Prepare pinned production REVIEW SQL only. Never connects to a database or deploys."""
from pathlib import Path
import argparse,hashlib,json,re,subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'supabase/production-review/2026-11-07'
PIN='5d434a78ac1f997c86b9c92646771de2018cad04'
PROJECT='arnzqizcycesukplmvuc'
PARTS=['supabase/003_survey_notifications.sql','supabase/004_verified_registration_notifications.sql']
BASE=['properties','extensions','rooms','exterior_photos','extension_photos','sketch_photos','room_photos','survey_free_allocations','survey_credit_purchases','survey_credit_revocations']
NEW=['survey_notification_events','newsletter_preferences','newsletter_consent_events','registration_notification_events']
NAMES=['claim_survey_notification','finish_survey_notification','record_auth_registration','get_newsletter_preference','set_newsletter_preference','recover_stale_registration_notifications','claim_registration_notification','finish_registration_notification']
def lit(value):return "'"+value.replace("'","''")+"'"
def seq(values):return ','.join(map(lit,values))
def sha(b):return hashlib.sha256(b).hexdigest()
def source_functions():
 result=[]
 for name in ['supabase/002_survey_purchases.sql']+PARTS:
  source=(ROOT/name).read_text()
  assert source.encode()==subprocess.check_output(['git','show',PIN+':'+name],cwd=ROOT)
  for m in re.finditer(r'create or replace function public\.(\w+)\((.*?)\)\s*returns (.*?)\s+language plpgsql security definer set search_path\s*=\s*\'\' as \$\$(.*?)\$\$;',source,re.S|re.I):
   args=m[2].strip();types=[]
   if args:
    for a in args.split(','):types.append(a.strip().split(None,1)[1])
   signature='public.'+m[1]+'('+','.join(types)+')'
   result.append({'signature':signature,'name':m[1],'source':name,'body_sha256':sha(m[4].replace('\r\n','\n').strip().encode()),'return_type':m[3].strip()})
 assert len(result)==14, result
 return result

def metadata_expression():
 # Deliberately exclude new003/004 objects so the before/after digest is stable.
 # Function bodies/trigger arguments never leave the server: hashes only.
 return f'''jsonb_build_object(
 'tables',coalesce((select jsonb_agg(jsonb_build_object('schema',n.nspname,'name',c.relname,'kind',c.relkind,'rls',c.relrowsecurity,'owner',pg_get_userbyid(c.relowner)) order by n.nspname,c.relname)
 from pg_class c join pg_namespace n on n.oid=c.relnamespace where (n.nspname='public' and c.relname in({seq(BASE)})) or (n.nspname='storage' and c.relname='objects')),'[]'::jsonb),
 'columns',coalesce((select jsonb_agg(jsonb_build_object('table',c.relname,'column',a.attname,'type',format_type(a.atttypid,a.atttypmod),'not_null',a.attnotnull,'default',pg_get_expr(d.adbin,d.adrelid)) order by c.relname,a.attnum)
 from pg_class c join pg_namespace n on n.oid=c.relnamespace join pg_attribute a on a.attrelid=c.oid and a.attnum>0 and not a.attisdropped
 left join pg_attrdef d on d.adrelid=c.oid and d.adnum=a.attnum where n.nspname='public' and c.relname in({seq(BASE)})),'[]'::jsonb),
 'constraints',coalesce((select jsonb_agg(jsonb_build_object('table',c.conrelid::regclass::text,'name',c.conname,'type',c.contype,'validated',c.convalidated,'definition',pg_get_constraintdef(c.oid,true)) order by c.conrelid::regclass::text,c.conname)
 from pg_constraint c join pg_class r on r.oid=c.conrelid join pg_namespace n on n.oid=r.relnamespace where n.nspname='public' and r.relname in({seq(BASE)})),'[]'::jsonb),
 'indexes',coalesce((select jsonb_agg(jsonb_build_object('table',r.relname,'name',i.relname,'valid',x.indisvalid,'definition',pg_get_indexdef(i.oid)) order by r.relname,i.relname)
 from pg_index x join pg_class i on i.oid=x.indexrelid join pg_class r on r.oid=x.indrelid join pg_namespace n on n.oid=r.relnamespace where n.nspname='public' and r.relname in({seq(BASE)})),'[]'::jsonb),
 'policies',coalesce((select jsonb_agg(jsonb_build_object('schema',schemaname,'table',tablename,'name',policyname,'roles',roles,'cmd',cmd,'permissive',permissive,'using',qual,'check',with_check) order by schemaname,tablename,policyname)
 from pg_policies where (schemaname='public' and tablename in({seq(BASE)})) or (schemaname='storage' and tablename='objects')),'[]'::jsonb),
 'effective_table_grants',coalesce((select jsonb_agg(jsonb_build_object('role',role_name,'table',table_name,'select',has_table_privilege(role_name,'public.'||table_name,'SELECT'),'insert',has_table_privilege(role_name,'public.'||table_name,'INSERT'),'update',has_table_privilege(role_name,'public.'||table_name,'UPDATE'),'delete',has_table_privilege(role_name,'public.'||table_name,'DELETE')) order by role_name,table_name)
 from unnest(array['anon','authenticated','service_role']) role_name cross join unnest(array[{seq(BASE)}]) table_name where to_regclass('public.'||table_name) is not null),'[]'::jsonb),
 'billing_functions',coalesce((select jsonb_agg(jsonb_build_object('signature',p.oid::regprocedure::text,'name',p.proname,'identity_arguments',pg_get_function_identity_arguments(p.oid),'return_type',p.prorettype::regtype::text,'language',(select lanname from pg_language where oid=p.prolang),'body_sha256',encode(sha256(convert_to(btrim(replace(p.prosrc,E'\\r\\n',E'\\n'),E' \\t\\n\\r'),'UTF8')),'hex'),'owner',pg_get_userbyid(p.proowner),'definer',p.prosecdef,'settings',p.proconfig,'acl',p.proacl::text) order by p.oid::regprocedure::text)
 from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname in('get_survey_allowance','enforce_survey_allowance','protect_survey_address','record_survey_purchase','revoke_survey_purchase')),'[]'::jsonb),
 'existing_triggers',coalesce((select jsonb_agg(jsonb_build_object('table',t.tgrelid::regclass::text,'name',t.tgname,'enabled',t.tgenabled,'definition_sha256',encode(sha256(convert_to(pg_get_triggerdef(t.oid,true),'UTF8')),'hex'),'function',t.tgfoid::regprocedure::text,'body_sha256',encode(sha256(convert_to(replace(p.prosrc,E'\\r\\n',E'\\n'),'UTF8')),'hex')) order by t.tgrelid::regclass::text,t.tgname)
 from pg_trigger t join pg_proc p on p.oid=t.tgfoid where not t.tgisinternal and t.tgrelid in(to_regclass('public.properties'),to_regclass('auth.users')) and t.tgname not in('urbanfold_auth_signup','urbanfold_auth_first_confirmation')),'[]'::jsonb),
 'ddl_event_triggers',coalesce((select jsonb_agg(jsonb_build_object('name',e.evtname,'event',e.evtevent,'enabled',e.evtenabled,'tags',e.evttags,'function',e.evtfoid::regprocedure::text,'owner',pg_get_userbyid(p.proowner),'definer',p.prosecdef,'settings',p.proconfig,'body_sha256',encode(sha256(convert_to(replace(p.prosrc,E'\\r\\n',E'\\n'),'UTF8')),'hex')) order by e.evtname)
 from pg_event_trigger e join pg_proc p on p.oid=e.evtfoid),'[]'::jsonb),
 'defaults',coalesce((select jsonb_agg(jsonb_build_object('owner',pg_get_userbyid(defaclrole),'schema',defaclnamespace::regnamespace::text,'type',defaclobjtype,'acl',defaclacl::text) order by defaclrole,defaclnamespace,defaclobjtype) from pg_default_acl),'[]'::jsonb),
 'existing_definer_helpers',coalesce((select jsonb_agg(jsonb_build_object('signature',p.oid::regprocedure::text,'return_type',p.prorettype::regtype::text,'owner',pg_get_userbyid(p.proowner),'settings',p.proconfig,'acl',p.proacl::text,'anon_execute',has_function_privilege('anon',p.oid,'EXECUTE'),'authenticated_execute',has_function_privilege('authenticated',p.oid,'EXECUTE'),'body_sha256',encode(sha256(convert_to(replace(p.prosrc,E'\\r\\n',E'\\n'),'UTF8')),'hex')) order by p.oid::regprocedure::text) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.prosecdef and p.proname not in({seq(NAMES)})),'[]'::jsonb),
 'client_memberships',coalesce((select jsonb_agg(jsonb_build_object('role',pg_get_userbyid(roleid),'member',pg_get_userbyid(member)) order by roleid,member) from pg_auth_members where pg_get_userbyid(member) in('anon','authenticated')),'[]'::jsonb),
 'buckets',coalesce((select jsonb_agg(jsonb_build_object('id',id,'public',public) order by id) from storage.buckets where id in('exterior-photos','sketch-photos','room-photos')),'[]'::jsonb)
)'''

def function_comparison(functions):
 values=','.join('('+lit(f['signature'])+','+lit(f['body_sha256'])+')' for f in functions)
 return f'''select jsonb_agg(jsonb_build_object('signature',expected.signature,'exists',p.oid is not null,'identity_arguments',pg_get_function_identity_arguments(p.oid),'return_type',p.prorettype::regtype::text,'language',(select lanname from pg_language where oid=p.prolang),
 'body_matches_reviewed_source',coalesce(encode(sha256(convert_to(btrim(replace(p.prosrc,E'\\r\\n',E'\\n'),E' \\t\\n\\r'),'UTF8')),'hex')=expected.digest,false),
 'owner',pg_get_userbyid(p.proowner),'definer',p.prosecdef,'settings',p.proconfig,
 'anon_execute',coalesce(has_function_privilege('anon',p.oid,'EXECUTE'),false),
 'authenticated_execute',coalesce(has_function_privilege('authenticated',p.oid,'EXECUTE'),false),
 'service_execute',coalesce(has_function_privilege('service_role',p.oid,'EXECUTE'),false),
 'acl',p.proacl::text) order by expected.signature)
 from (values {values}) expected(signature,digest) left join pg_proc p on p.oid=to_regprocedure(expected.signature)'''

def shared_guard(functions):
 return f'''
 if not pg_try_advisory_xact_lock(hashtextextended('urbanfold.production.backend.release',0)) then raise exception 'Another reviewed installation is running.';end if;
 if current_user<>'postgres' or auth.uid() is not null or auth.jwt()->>'role' is not null then raise exception 'Trusted postgres/no simulated JWT session required.';end if;
 if current_setting('urbanfold.release_ack',true) is distinct from 'APPROVED {PROJECT} {PIN}' then raise exception 'No production execution approval acknowledgement.';end if;
 if obj_description(to_regclass('public.properties'),'pg_class') like 'Urbanfold-Survey-Staging%' then raise exception 'Staging database rejected.';end if;
 select {metadata_expression()} into baseline;
 if current_setting('urbanfold.reviewed_baseline_sha256',true) is distinct from encode(sha256(convert_to(baseline::text,'UTF8')),'hex') then raise exception 'Reviewed production baseline fingerprint missing or changed. STOP; do not bypass.';end if;
 if (select count(*) from storage.buckets where id in('exterior-photos','sketch-photos','room-photos') and not public)<>3 then raise exception 'Private buckets required.';end if;
 if (select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relname in({seq(BASE)}) and c.relkind='r' and c.relrowsecurity)<>10 then raise exception 'Ten existing RLS-enabled app/credit tables required.';end if;
 if not exists(select 1 from pg_class where oid='storage.objects'::regclass and relrowsecurity) then raise exception 'Storage RLS required.';end if;
 select ({function_comparison(functions[:5])}) into functions;
 if exists(select 1 from jsonb_array_elements(functions) f where not (f->>'body_matches_reviewed_source')::boolean or f->>'owner'<>'postgres' or not (f->>'definer')::boolean or not ((f->'settings') ? 'search_path=""' or (f->'settings') ? 'search_path=')
 or (f->>'anon_execute')::boolean or (f->>'authenticated_execute')::boolean is distinct from (f->>'signature'='public.get_survey_allowance()')
 or (f->>'signature' like 'public.record_survey_purchase%' or f->>'signature' like 'public.revoke_survey_purchase%') and not (f->>'service_execute')::boolean) then raise exception 'Existing002 function source/ACL differs; review targeted correction first, never reinstall002 blindly.';end if;
 if (select count(*) from pg_trigger where tgrelid='public.properties'::regclass and tgname in('urbanfold_survey_allowance','urbanfold_protect_address') and tgenabled='O')<>2 then raise exception 'Existing credit/address triggers must be enabled.';end if;
'''

def post_guard(functions,tables):
 return f'''do $$ declare checks jsonb;baseline jsonb;begin
 select {metadata_expression()} into baseline;
 if current_setting('urbanfold.reviewed_baseline_sha256',true) is distinct from encode(sha256(convert_to(baseline::text,'UTF8')),'hex') then raise exception 'Existing baseline changed during installation; transaction rolled back.';end if;
 select ({function_comparison(functions)}) into checks;
 if exists(select 1 from jsonb_array_elements(checks) f where not (f->>'body_matches_reviewed_source')::boolean
 or f->>'owner'<>'postgres' or not (f->>'definer')::boolean or not ((f->'settings') ? 'search_path=""' or (f->'settings') ? 'search_path=')
 or (f->>'anon_execute')::boolean or (f->>'authenticated_execute')::boolean is distinct from (f->>'signature' in('public.get_newsletter_preference()','public.set_newsletter_preference(boolean)'))
 or (f->>'signature' not like 'public.record_auth_registration%' and f->>'signature' not like 'public.get_newsletter_preference%' and f->>'signature' not like 'public.set_newsletter_preference%') and not (f->>'service_execute')::boolean) then raise exception 'New function fingerprint/security checks failed; entire installation transaction rolled back.';end if;
 if exists(select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relname in({seq(tables)}) and
 (not c.relrowsecurity or pg_get_userbyid(c.relowner)<>'postgres' or has_table_privilege('anon',c.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
 or has_table_privilege('authenticated',c.oid,'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
 or has_table_privilege('authenticated',c.oid,'SELECT') is distinct from (c.relname in('newsletter_preferences','newsletter_consent_events')))) then raise exception 'New table RLS/client access checks failed; transaction rolled back.';end if;
 if to_regclass('public.newsletter_consent_events') is not null then
  if has_table_privilege('service_role','public.newsletter_consent_events','INSERT,UPDATE,DELETE,TRUNCATE') then raise exception 'Consent audit must be read-only to service_role.';end if;
 end if;
end $$;
'''

def generate():
 for part in ['supabase/001_secure_access.sql','supabase/002_survey_purchases.sql']+PARTS:
  assert (ROOT/part).read_bytes()==subprocess.check_output(['git','show',PIN+':'+part],cwd=ROOT)
 functions=source_functions();reference=json.loads((OUT/'reference_001_002.json').read_text())
 header=f'-- REVIEW ONLY. Never execute without separate production approval. Source {PIN}.\n-- Target {PROJECT}; SQL acknowledgement is NOT independent proof of server identity.\n'
 pre=header+f'''-- SELECT-only catalogs/bucket flags. No customer rows, Auth users, secret values or email calls.
with baseline as (select {metadata_expression()} as metadata)
select jsonb_build_object('expected_project',{lit(PROJECT)},'execution_role',current_user,
 'jwt_context_present',auth.uid() is not null or auth.jwt()->>'role' is not null,
 'staging_marker_detected',coalesce(obj_description(to_regclass('public.properties'),'pg_class') like 'Urbanfold-Survey-Staging%',false),
 'baseline_sha256',encode(sha256(convert_to(metadata::text,'UTF8')),'hex'),'deployed_001_002_metadata',metadata,
 'reviewed_reference_001_002',{lit(json.dumps(reference))}::jsonb,
 'reviewed_function_comparison',({function_comparison(functions)}),
 'existing_function_dependencies',coalesce((select jsonb_agg(jsonb_build_object('signature',p.oid::regprocedure::text,
 'extension_membership',(select jsonb_agg(e.extname) from pg_depend d join pg_extension e on e.oid=d.refobjid where d.classid='pg_proc'::regclass and d.objid=p.oid and d.refclassid='pg_extension'::regclass and d.deptype='e'),
 'catalog_dependents',(select jsonb_agg(pg_describe_object(d.classid,d.objid,d.objsubid)) from pg_depend d where d.refclassid='pg_proc'::regclass and d.refobjid=p.oid)) order by p.oid::regprocedure::text) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname in('rls_auto_enable','get_survey_allowance','enforce_survey_allowance','protect_survey_address','record_survey_purchase','revoke_survey_purchase')),'[]'::jsonb),
 'new_objects',coalesce((select jsonb_agg(jsonb_build_object('name',relname,'kind',relkind,'rls',relrowsecurity)) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and relname in({seq(NEW)})),'[]'::jsonb),
 'new_function_overloads',coalesce((select jsonb_agg(p.oid::regprocedure::text) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname in({seq(NAMES)})),'[]'::jsonb),
 'reserved_auth_triggers',coalesce((select jsonb_agg(tgname) from pg_trigger where tgrelid='auth.users'::regclass and tgname in('urbanfold_auth_signup','urbanfold_auth_first_confirmation')),'[]'::jsonb)
) as production_backend_preflight from baseline;
-- Reference is an offline SOURCE model, not a claim about production. Compare every policy,
-- constraint, grant and enabled trigger before approving the returned baseline digest.
-- Empty migration history is not permission to replay001/002 or create a fresh baseline.
'''
 files={'00_preflight_readonly.sql':pre}
 guard=shared_guard(functions)
 for n,part in enumerate(PARTS):
  source=(ROOT/part).read_text();assert source.count('\nbegin;')==1 and source.rstrip().endswith('commit;')
  body=source[source.index('\nbegin;')+len('\nbegin;'):source.rfind('commit;')]
  target=NEW[:1] if n==0 else NEW[1:];target_names=NAMES[:2] if n==0 else NAMES[2:]
  presence=f'''if exists(select 1 from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relname in({seq(target)}))
 or exists(select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname in({seq(target_names)})) then raise exception 'Fresh-only target objects already exist. STOP and review; never reset/reapply.';end if;'''
  if n==1:
   presence+="\n if to_regclass('public.survey_notification_events') is null then raise exception 'Install/review003 first.';end if;\n if exists(select 1 from pg_trigger where tgrelid='auth.users'::regclass and tgname in('urbanfold_auth_signup','urbanfold_auth_first_confirmation')) then raise exception 'Reserved Auth trigger already exists.';end if;"
  safety=f'''\n if (select jsonb_array_length(baseline->'billing_functions'))<>5 then raise exception 'Unexpected billing helper overloads.';end if;\n if exists(select 1 from jsonb_array_elements({lit(json.dumps(reference['required_columns']))}::jsonb) required where not exists(select 1 from jsonb_array_elements(baseline->'columns') actual where actual->>'table'=required->>'table' and actual->>'column'=required->>'column' and actual->>'type'=required->>'type')) then raise exception 'Required application columns/types differ from reviewed source model. Review compatibility before proceeding.';end if;\n if (select policies from (select baseline->'policies' as policies) s) is distinct from {lit(json.dumps(reference['policies']))}::jsonb then raise exception '001/002 policy mismatch/additional policy. Review exact differences; do not blanket replace policies.';end if;
'''
  files[('10_install_003_fresh.sql' if n==0 else '20_install_004_fresh.sql')]=header+'''-- Replace ONLY the two NOT_APPROVED/REVIEW_REQUIRED parameter literals after review/approval.
-- Confirm the actual Dashboard project independently; do not copy a staging fingerprint.
begin;
set local lock_timeout='5s';
set local statement_timeout='60s';
set local urbanfold.release_ack='NOT_APPROVED';
set local urbanfold.reviewed_baseline_sha256='REVIEW_REQUIRED';
do $$ declare baseline jsonb;functions jsonb;begin
'''+guard+safety+presence+'\nend $$;\n-- BEGIN UNMODIFIED PINNED MIGRATION BODY '+part+'\n'+body+'\n-- END UNMODIFIED PINNED MIGRATION BODY\n'+post_guard(functions[5:7] if n==0 else functions[5:], NEW[:1] if n==0 else NEW)+'commit;\n'
 post=header+f'''-- SELECT-only. Compare baseline SHA256 with approved preflight; no record payloads returned.
with baseline as(select {metadata_expression()} as metadata)
select jsonb_build_object('baseline_sha256',encode(sha256(convert_to(metadata::text,'UTF8')),'hex'),
 'functions',({function_comparison(functions)}),
 'new_tables',coalesce((select jsonb_agg(jsonb_build_object('table',c.relname,'rls',c.relrowsecurity,'owner',pg_get_userbyid(c.relowner),'acl',c.relacl::text,
 'anon_any',has_table_privilege('anon',c.oid,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER'),
 'authenticated_select',has_table_privilege('authenticated',c.oid,'SELECT'),
 'authenticated_write',has_table_privilege('authenticated',c.oid,'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER'),
 'service_select',has_table_privilege('service_role',c.oid,'SELECT'),'service_write',has_table_privilege('service_role',c.oid,'INSERT,UPDATE,DELETE')) order by c.relname)
 from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relname in({seq(NEW)})),'[]'::jsonb),
 'new_policies',coalesce((select jsonb_agg(to_jsonb(p)) from pg_policies p where schemaname='public' and tablename in({seq(NEW)})),'[]'::jsonb),
 'new_constraints',coalesce((select jsonb_agg(jsonb_build_object('table',r.relname,'name',c.conname,'definition',pg_get_constraintdef(c.oid,true),'validated',c.convalidated)) from pg_constraint c join pg_class r on r.oid=c.conrelid join pg_namespace n on n.oid=r.relnamespace where n.nspname='public' and r.relname in({seq(NEW)})),'[]'::jsonb),
 'new_indexes',coalesce((select jsonb_agg(jsonb_build_object('table',r.relname,'index',i.relname,'valid',x.indisvalid)) from pg_index x join pg_class i on i.oid=x.indexrelid join pg_class r on r.oid=x.indrelid join pg_namespace n on n.oid=r.relnamespace where n.nspname='public' and r.relname in({seq(NEW)})),'[]'::jsonb),
 'auth_triggers',coalesce((select jsonb_agg(jsonb_build_object('name',tgname,'enabled',tgenabled,'function',tgfoid::regprocedure::text,'definition',pg_get_triggerdef(oid,true))) from pg_trigger where tgrelid='auth.users'::regclass and tgname in('urbanfold_auth_signup','urbanfold_auth_first_confirmation')),'[]'::jsonb)
) as production_backend_postcheck from baseline;
'''
 files['30_postinstall_readonly.sql']=post
 spec={'pinned_commit':PIN,'production_project':PROJECT,'migration_sources':{p:sha((ROOT/p).read_bytes()) for p in ['supabase/001_secure_access.sql','supabase/002_survey_purchases.sql']+PARTS},'functions':functions}
 files['source_spec.json']=json.dumps(spec,indent=2)+'\n'
 return files

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
 for name,source in generate().items():
  p=OUT/name
  if args.check:assert p.read_text()==source, 'Generated review drift: '+name
  else:p.write_text(source)
 print('PASS production review generation parity' if args.check else 'Prepared review SQL only; no database connection or deployment')
if __name__=='__main__':main()
