"""Static/source and Python ACL-model checks ONLY. No SQL/database/Docker execution."""
from pathlib import Path
import copy,hashlib,importlib.util,json,re,subprocess
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('acl_builder',ROOT/'scripts/build_table_acl_review.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
PRIVS=set(b.PRIVS)
def ordered(entries):return sorted(entries,key=lambda a:(a['grantor'],a['grantee'],a['privilege']))
def project(snapshot,restore=False):
 value=copy.deepcopy(snapshot)
 for table in value['tables']:
  if restore:
   table['acl']+= [dict(grantor='postgres',grantee=r,privilege=p,grantable=False) for r in b.ROLES for p in b.PRIVS]
  else:table['acl']=[a for a in table['acl'] if not(a['grantor']=='postgres' and a['grantee'] in b.ROLES and a['privilege'] in PRIVS and a['grantable'] is False)]
  table['acl']=ordered(table['acl'])
 return value

def main():
 output=b.generate()
 for name,source in output.items():assert (b.OUT/name).read_text()==source,name
 apply=output['03_revoke_excess_table_privileges.sql'];rollback=output['05_restore_exact_previous_privileges.sql']
 target=', '.join('public.'+t for t in b.TABLES)
 revoke='revoke truncate, references, trigger, maintain on table '+target+' from anon, authenticated restrict;'
 grant='grant truncate, references, trigger, maintain on table '+target+' to anon, authenticated;'
 assert apply.count(revoke)==1 and grant not in apply
 assert rollback.count(grant)==1 and revoke not in rollback
 for name,source in output.items():
  if not name.endswith('.sql'):continue
  active=re.sub(r'--[^\n]*','',source);active=re.sub(r"'(?:''|[^'])*'", "''",active)
  assert not re.search(r'(?im)^\s*(alter|create|drop|insert|update|delete|truncate)\s+',active),name
  assert not re.search(r'\b(net\.http_post|http_get|set\s+role|alter\s+default\s+privileges|execute)\b',active,re.I),name
  if 'readonly' in name:
   assert active.lstrip().lower().startswith('with ')
   assert not re.search(r'\b(revoke|grant|do|set_config|pg_try_advisory_xact_lock)\b',active,re.I),name
 for source in [apply,rollback]:
  for parameter in ['acl_ack','acl_action']:assert 'urbanfold.'+parameter+"='NOT_APPROVED'" in source
  for parameter in ['reviewed_baseline_sha256','original_acl_sha256']:assert 'urbanfold.'+parameter+"='REVIEW_REQUIRED'" in source
  assert 'grantable' in source and 'column REFERENCES needs separate review' in source
  assert 'baseline_after is distinct from baseline_before' in source and 'after_acl is distinct from expected_acl' in source
 assert 'APPROVED REMOVE56 EXCESS PRIVILEGES' in apply
 assert 'APPROVED RESTORE56 ORIGINAL PRIVILEGES' in rollback
 assert 'grantor' in output['02_acl_preflight_readonly.sql'] and 'column_acls' in output['02_acl_preflight_readonly.sql']
 assert 'MAINTAIN' in output['02_acl_preflight_readonly.sql']
 assert b.snapshot().count('survey_credit_purchases')==1
 assert 'storage' in b.snapshot() and 'untouched_tables' in b.snapshot()
 print('PASS exact seven-table/two-role/four-privilege statements, RESTRICT removal, no grant options/default changes/SQL data DML, fail-closed parameters, inverse/snapshot/role/column-ACL/Storage/credit guards, generated parity; SQL NOT executed')
 privileges=['SELECT','INSERT','UPDATE','DELETE']+b.PRIVS
 initial={'api_roles':[{'role':r,'superuser':False,'bypass_rls':False,'can_login':False} for r in b.ROLES],
 'tables':[{'table':t,'owner':'postgres','rls':True,'force_rls':False,'column_acls':[],
 'api_crud':[{'role':r,'select':True,'insert':True,'update':True,'delete':True} for r in b.ROLES],
 'acl':ordered([dict(grantor='postgres',grantee=r,privilege=p,grantable=False) for r in ['postgres','anon','authenticated','service_role'] for p in privileges])} for t in b.TABLES],
 'untouched_tables':[{'table':'survey_credit_purchases','opaque_acl':'preserve'},{'schema':'storage','table':'objects','opaque_acl':'preserve'}]}
 original=copy.deepcopy(initial);corrected=project(initial)
 assert initial==original
 assert sum(len(t['acl']) for t in initial['tables'])-sum(len(t['acl']) for t in corrected['tables'])==56
 for before,after in zip(initial['tables'],corrected['tables']):
  assert before['api_crud']==after['api_crud'] and before['column_acls']==after['column_acls']
  assert all(a in after['acl'] for a in before['acl'] if a['grantee'] in ['postgres','service_role'] or a['privilege'] not in PRIVS)
 assert corrected['untouched_tables']==initial['untouched_tables'] and corrected['api_roles']==initial['api_roles']
 assert project(corrected,True)==initial
 changed=copy.deepcopy(corrected);changed['tables'][0]['api_crud'][0]['select']=False
 assert project(changed,True)!=initial
 changed=copy.deepcopy(corrected);changed['tables'][0]['acl'][0]['grantable']=True
 assert project(changed,True)!=initial
 altered_original=copy.deepcopy(initial)
 for a in altered_original['tables'][0]['acl']:
  if a['grantee']=='anon' and a['privilege']=='TRUNCATE':a['grantor']='different_grantor'
 assert project(project(altered_original),True)!=altered_original
 for path in ['app.js','index.html','supabase/001_secure_access.sql','supabase/002_survey_purchases.sql','supabase/003_survey_notifications.sql','supabase/004_verified_registration_notifications.sql','scripts/build_production_backend_review.py','.github/workflows/pages.yml']:
  assert (ROOT/path).read_bytes()==subprocess.check_output(['git','show',b.PIN+':'+path]),path
 print('PASS Python ACL-model removes exactly56 entries and restores original snapshot; unrelated changes/unsupported grantors fail inverse equality; canonical application/SQL/workflow unchanged. This is NOT a PostgreSQL runtime test.')
if __name__=='__main__':main()
