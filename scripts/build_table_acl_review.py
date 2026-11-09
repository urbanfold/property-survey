"""Generate review-only ACL SQL. No database connection, SQL execution or deployment."""
from pathlib import Path
import argparse,hashlib,importlib.util,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'supabase/production-review/2026-11-07/table-acl-correction'
PIN='1d1c934ce39650433a58ec70640d4f3671ad018f'
PROJECT='arnzqizcycesukplmvuc'
TABLES=['properties','extensions','rooms','exterior_photos','extension_photos','sketch_photos','room_photos']
ROLES=['anon','authenticated']
PRIVS=['TRUNCATE','REFERENCES','TRIGGER','MAINTAIN']
spec=importlib.util.spec_from_file_location('baseline_review',ROOT/'scripts/build_production_backend_review.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
def lit(s):return "'"+s.replace("'","''")+"'"
def seq(items):return ','.join(map(lit,items))
def digest(expr):return "encode(sha256(convert_to(("+expr+")::text,'UTF8')),'hex')"
def acl_entries(alias):
 return f'''coalesce((select jsonb_agg(jsonb_build_object('grantor',pg_get_userbyid(a.grantor),
 'grantee',case when a.grantee=0 then 'PUBLIC' else pg_get_userbyid(a.grantee) end,
 'privilege',a.privilege_type,'grantable',a.is_grantable)
 order by pg_get_userbyid(a.grantor)::text collate "C",(case when a.grantee=0 then 'PUBLIC' else pg_get_userbyid(a.grantee) end)::text collate "C",a.privilege_type collate "C")
 from aclexplode(coalesce({alias}.relacl,acldefault('r',{alias}.relowner))) a),'[]'::jsonb)'''
def table_snapshot(alias):
 return f'''jsonb_build_object('schema',n.nspname,'table',{alias}.relname,'kind',{alias}.relkind,
 'owner',pg_get_userbyid({alias}.relowner),'rls',{alias}.relrowsecurity,'force_rls',{alias}.relforcerowsecurity,
 'acl',{acl_entries(alias)},
 'column_acls',coalesce((select jsonb_agg(jsonb_build_object('column',att.attname,'acl',
 coalesce((select jsonb_agg(jsonb_build_object('grantor',pg_get_userbyid(x.grantor),
 'grantee',case when x.grantee=0 then 'PUBLIC' else pg_get_userbyid(x.grantee) end,
 'privilege',x.privilege_type,'grantable',x.is_grantable)
 order by pg_get_userbyid(x.grantor)::text collate "C",(case when x.grantee=0 then 'PUBLIC' else pg_get_userbyid(x.grantee) end)::text collate "C",x.privilege_type collate "C")
 from aclexplode(att.attacl) x),'[]'::jsonb)) order by att.attnum) from pg_attribute att
 where att.attrelid={alias}.oid and att.attnum>0 and not att.attisdropped and att.attacl is not null),'[]'::jsonb),
 'api_crud',coalesce((select jsonb_agg(jsonb_build_object('role',r.rolname,
 'select',has_table_privilege(r.oid,{alias}.oid,'SELECT'),'insert',has_table_privilege(r.oid,{alias}.oid,'INSERT'),
 'update',has_table_privilege(r.oid,{alias}.oid,'UPDATE'),'delete',has_table_privilege(r.oid,{alias}.oid,'DELETE'),
 'inherits_owner',pg_has_role(r.oid,{alias}.relowner,'USAGE')) order by r.rolname)
 from pg_roles r where r.rolname in({seq(ROLES)})),'[]'::jsonb))'''
def snapshot():
 return f'''jsonb_build_object(
 'api_roles',coalesce((select jsonb_agg(jsonb_build_object('role',rolname,'superuser',rolsuper,
 'bypass_rls',rolbypassrls,'can_login',rolcanlogin,'inherit',rolinherit) order by rolname)
 from pg_roles where rolname in({seq(ROLES)})),'[]'::jsonb),
 'tables',coalesce((select jsonb_agg({table_snapshot('c')} order by c.relname::text collate "C")
 from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relname in({seq(TABLES)})),'[]'::jsonb),
 'untouched_tables',coalesce((select jsonb_agg({table_snapshot('c')} order by n.nspname,c.relname)
 from pg_class c join pg_namespace n on n.oid=c.relnamespace where
 (n.nspname='public' and c.relname in('survey_free_allocations','survey_credit_purchases','survey_credit_revocations'))
 or (n.nspname='storage' and c.relname='objects')),'[]'::jsonb)
)'''
def project_acl(variable,restore=False):
 # Alter ONLY 56 exact direct non-grantable owner-issued privileges in the
 # expected snapshot. All roles/CRUD/column ACLs/unrelated ACL entries retained.
 if restore:
  rows=f'''select a from jsonb_array_elements(t->'acl') a
 union all select jsonb_build_object('grantor','postgres','grantee',role_name,'privilege',priv_name,'grantable',false)
 from unnest(array[{seq(ROLES)}]) role_name cross join unnest(array[{seq(PRIVS)}]) priv_name'''
 else:
  rows=f'''select a from jsonb_array_elements(t->'acl') a where not
 (a->>'grantor'='postgres' and a->>'grantee' in({seq(ROLES)}) and a->>'privilege' in({seq(PRIVS)}) and a->>'grantable'='false')'''
 return f'''jsonb_set({variable},'{{tables}}',coalesce((select jsonb_agg(
 jsonb_set(t,'{{acl}}',coalesce((select jsonb_agg(a order by (a->>'grantor') collate "C",(a->>'grantee') collate "C",(a->>'privilege') collate "C")
 from ({rows}) entries),'[]'::jsonb)) order by (t->>'table') collate "C")
 from jsonb_array_elements({variable}->'tables') t),'[]'::jsonb))'''
def effective_query():
 return f'''select jsonb_agg(jsonb_build_object('table',c.relname,'role',r.rolname,'privilege',privilege,
 'allowed',has_table_privilege(r.oid,c.oid,privilege)) order by c.relname,r.rolname,privilege)
 from pg_class c join pg_namespace n on n.oid=c.relnamespace cross join pg_roles r
 cross join unnest(array[{seq(PRIVS)}]) privilege
 where n.nspname='public' and c.relname in({seq(TABLES)}) and r.rolname in({seq(ROLES)})'''
def invariant_guard():
 return f'''
 if current_user<>'postgres' then raise exception 'Trusted postgres operator required; never change role to bypass.';end if;
 if current_setting('server_version_num')::integer<170000 then raise exception 'Reviewed MAINTAIN correction requires PostgreSQL17 or newer.';end if;
 if auth.uid() is not null or auth.jwt()->>'role' is not null then raise exception 'No simulated/customer JWT claims allowed.';end if;
 if obj_description(to_regclass('public.properties'),'pg_class') like 'Urbanfold-Survey-Staging%' then raise exception 'Staging rejected; independently verify production project.';end if;
 if current_setting('urbanfold.acl_ack',true) is distinct from 'APPROVED {PROJECT} TABLE ACL REVIEW {PIN}' then raise exception 'Separate permission-change approval required.';end if;
 if not pg_try_advisory_xact_lock(hashtextextended('urbanfold.production.backend.release',0)) then raise exception 'Another reviewed release operation is running.';end if;
 select {b.metadata_expression()} into baseline_before;
 if current_setting('urbanfold.reviewed_baseline_sha256',true) is distinct from {digest('baseline_before')} then raise exception 'Reviewed baseline missing/changed; stop.';end if;
 select {snapshot()} into before_acl;
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
'''
def after_guards(expected):
 return f'''
 select {snapshot()} into after_acl;
 select {b.metadata_expression()} into baseline_after;
 if baseline_after is distinct from baseline_before or after_acl is distinct from {expected} then
 raise exception 'Unrelated schema/grants/roles/CRUD/columns/Storage/credit ACL changed; transaction rolled back.';end if;
'''

def generate():
 assert (ROOT/'scripts/build_production_backend_review.py').read_bytes()==subprocess.check_output(['git','show',PIN+':scripts/build_production_backend_review.py'],cwd=ROOT)
 header=f'''-- REVIEW ONLY. DO NOT EXECUTE WITHOUT INDEPENDENT REVIEW AND SEPARATE APPROVAL.
-- Target {PROJECT}; SQL acknowledgements/hashes do NOT independently prove server identity.
-- Source review commit {PIN}. No global defaults, RLS, Storage or credit changes.
'''
 pre=header+f'''-- SELECT-only, no data rows/credentials/function source returned.
with baseline as(select {b.metadata_expression()} as metadata), permissions as(select {snapshot()} as state)
select jsonb_build_object('expected_project',{lit(PROJECT)},'execution_role',current_user,
 'server_version_num',current_setting('server_version_num'),
 'baseline_sha256',{digest('metadata')},'baseline_matches_last_report',{digest('metadata')}='10fa3ce6272648b31c662735e549b2e78b032a63cceb6e5f1d862f5d5052e4f6',
 'acl_sha256',{digest('state')},'acl_snapshot',state,
 'effective_excess_privileges',({effective_query()}),
 'watchers',coalesce((select jsonb_agg(jsonb_build_object('schema',n.nspname,'name',p.proname,'owner',pg_get_userbyid(p.proowner),
 'return_type',p.prorettype::regtype::text,'definer',p.prosecdef,'settings',p.proconfig,
 'body_sha256',encode(sha256(convert_to(replace(p.prosrc,E'\\r\\n',E'\\n'),'UTF8')),'hex')) order by p.proname)
 from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='extensions' and p.proname in('pgrst_ddl_watch','pgrst_drop_watch')),'[]'::jsonb)
) as table_acl_preflight from baseline,permissions;
-- Inspect each target grantor/grant option and column ACL before installation approval.
-- Snapshot hashes attest reviewed metadata/state, not historical who/when provenance.
'''
 params='''begin;
set local lock_timeout='5s';
set local statement_timeout='30s';
set local urbanfold.acl_ack='NOT_APPROVED';
set local urbanfold.acl_action='NOT_APPROVED';
set local urbanfold.reviewed_baseline_sha256='REVIEW_REQUIRED';
set local urbanfold.original_acl_sha256='REVIEW_REQUIRED';
do $$ declare baseline_before jsonb;baseline_after jsonb;before_acl jsonb;after_acl jsonb;expected_acl jsonb;effective jsonb;
begin
'''
 target_list=', '.join('public.'+t for t in TABLES)
 apply=header+'''-- Fresh correction only; repeated execution stops rather than changing another state.
-- Replace ONLY approval/baseline/original-ACL parameter literals after approval.
'''+params+invariant_guard()+f'''
 if current_setting('urbanfold.acl_action',true) is distinct from 'APPROVED REMOVE56 EXCESS PRIVILEGES' then raise exception 'Specific removal approval required.';end if;
 if current_setting('urbanfold.original_acl_sha256',true) is distinct from {digest('before_acl')} then raise exception 'Original reviewed ACL fingerprint missing/changed.';end if;
 if (select count(*) from jsonb_array_elements(before_acl->'tables') t cross join lateral jsonb_array_elements(t->'acl') a
 where a->>'grantee' in({seq(ROLES)}) and a->>'privilege' in({seq(PRIVS)}) and a->>'grantor'='postgres' and a->>'grantable'='false')<>56
 or exists(select 1 from jsonb_array_elements(before_acl->'tables') t cross join lateral jsonb_array_elements(t->'acl') a
 where a->>'privilege' in({seq(PRIVS)}) and (a->>'grantee'='PUBLIC'
 or (a->>'grantee' in({seq(ROLES)}) and (a->>'grantor'<>'postgres' or a->>'grantable'<>'false'))
 or a->>'grantor' in({seq(ROLES)}))) then
 raise exception 'Need56 exact direct owner-issued non-grantable entries; PUBLIC/other grantor/delegation/partial correction unsupported. No SET ROLE or CASCADE fallback.';end if;
 expected_acl:={project_acl('before_acl')};
 -- THE ONLY PERMISSION CHANGE. Restrict dependency handling; never CASCADE.
 revoke truncate, references, trigger, maintain on table {target_list} from anon, authenticated restrict;
'''+after_guards('expected_acl')+f'''
 select ({effective_query()}) into effective;
 if coalesce(jsonb_array_length(effective),0)<>56 or exists(select 1 from jsonb_array_elements(effective) e where (e->>'allowed')::boolean is distinct from false) then
 raise exception 'Effective excess access remains (PUBLIC/inherited/owner path); entire correction rolled back.';end if;
end $$;
commit;
-- Save separately approved postflight metadata/hashes. No rows were selected/updated/deleted.
'''
 rollback=header+'''-- SEPARATE approval needed: restores the old excessive rights, not a desirable steady state.
-- Requires the ORIGINAL saved02 ACL digest; never a guessed/current digest.
'''+params+invariant_guard()+f'''
 if current_setting('urbanfold.acl_action',true) is distinct from 'APPROVED RESTORE56 ORIGINAL PRIVILEGES' then raise exception 'Separate specific rollback approval required.';end if;
 select ({effective_query()}) into effective;
 if coalesce(jsonb_array_length(effective),0)<>56 or exists(select 1 from jsonb_array_elements(effective) e where (e->>'allowed')::boolean is distinct from false) then
 raise exception 'Rollback needs the fully corrected state, not partial/already restored permissions.';end if;
 expected_acl:={project_acl('before_acl',True)};
 if current_setting('urbanfold.original_acl_sha256',true) is distinct from {digest('expected_acl')} then
 raise exception 'Inverse snapshot does not match saved original ACL. Stop: unrelated changes or unsupported original grantor/options; never broaden rollback.';end if;
 -- THE ONLY ROLLBACK CHANGE: exact56 former entries, no grant options.
 grant truncate, references, trigger, maintain on table {target_list} to anon, authenticated;
'''+after_guards('expected_acl')+f'''
 if current_setting('urbanfold.original_acl_sha256',true) is distinct from {digest('after_acl')} then raise exception 'Rollback ACL differs from original; transaction rolled back.';end if;
end $$;
commit;
'''
 post=pre.replace('as table_acl_preflight','as table_acl_postflight')+'''-- Expected corrected result: exactly56 effective privilege rows, ALL allowed=false.
-- Compare entire baseline digest unchanged, all CRUD/roles/RLS/column/untouched-table
-- entries unchanged and target ACLs differ ONLY by removal of the56 approved entries.
-- The old baseline digest may remain10fa...: it contains CRUD, not these table non-row ACLs.
'''
 source={'source_review_commit':PIN,'project':PROJECT,'tables':TABLES,'roles':ROLES,'privileges':PRIVS,
 'expected_removed_direct_entries':56,'required_owner_and_grantor':'postgres','grant_options_supported':False,
 'known_production_baseline_observed_not_approved':'10fa3ce6272648b31c662735e549b2e78b032a63cceb6e5f1d862f5d5052e4f6',
 'baseline_builder_sha256':hashlib.sha256((ROOT/'scripts/build_production_backend_review.py').read_bytes()).hexdigest(),
 'new_preflight_required':'grantor/grant-option/column-ACL snapshot digest and private watcher source review'}
 return {'02_acl_preflight_readonly.sql':pre,'03_revoke_excess_table_privileges.sql':apply,
 '04_acl_postflight_readonly.sql':post,'05_restore_exact_previous_privileges.sql':rollback,
 'SOURCE_SPEC.json':json.dumps(source,indent=2)+'\n'}

def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 for name,content in generate().items():
  path=OUT/name
  if a.check:assert path.read_text()==content,name
  else:path.write_text(content)
 print('PASS ACL review source/output parity; SQL NOT executed' if a.check else 'Prepared review-only ACL SQL; no database access or SQL execution')
if __name__=='__main__':main()
