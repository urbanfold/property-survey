"""Read-only SELECT tests of a narrow review guard; never runs an installer/migration.
Only an offline disposable PostgreSQL cluster is started. No cloud/API credentials.
"""
from pathlib import Path
import importlib.util,json,subprocess,sys,time,uuid,hashlib
sys.path.insert(0,str(Path(__file__).parent))
from test_database_policies import IMAGE
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'supabase/production-review/2026-11-07'
BASE='d42263a8fb10e44136564a5224c956bcc47c89c7'
spec=importlib.util.spec_from_file_location('review_builder',ROOT/'scripts/build_production_backend_review.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

def main():
 for name in ['00_preflight_readonly.sql','30_postinstall_readonly.sql','reference_001_002.json','source_spec.json','40_disable_auth_recording.sql','41_enable_auth_recording.sql','50_registration_schedule_review.sql','51_schedule_verify_readonly.sql']:
  path='supabase/production-review/2026-11-07/'+name
  assert (ROOT/path).read_bytes()==subprocess.check_output(['git','show',BASE+':'+path]),name
 before="and actual->>'column'=required->>'column' and actual->>'type'=required->>'type'"
 after="and actual->>'column'=required->>'column' and "+b.column_type_match_sql()
 for name in ['10_install_003_fresh.sql','20_install_004_fresh.sql']:
  path='supabase/production-review/2026-11-07/'+name
  original=subprocess.check_output(['git','show',BASE+':'+path],text=True)
  assert original.count(before)==1
  assert (ROOT/path).read_text()==original.replace(before,after)
  assert "urbanfold.release_ack='NOT_APPROVED'" in original and "urbanfold.reviewed_baseline_sha256='REVIEW_REQUIRED'" in original
  assert '10fa3ce6272648b31c662735e549b2e78b032a63cceb6e5f1d862f5d5052e4f6' not in (ROOT/path).read_text()
 for path,text in b.generate().items():assert (OUT/path).read_text()==text
 print('PASS only exact two-column type predicate changed; all canonical bodies, baseline query/reference, policy/ACL/fingerprint guards and approval placeholders preserved')
 rows=[]
 def case(name,rt,rc,req_type,at,ac,actual_type,expected):
  rows.append((name,{'table':rt,'column':rc,'type':req_type},{'table':at,'column':ac,'type':actual_type},expected))
 for col in ['width','length']:
  for typ,expected in [('numeric',True),('numeric(5,2)',True),('numeric(6,2)',False),('numeric(5,3)',False),('numeric(5,1)',False),('integer',False),('double precision',False),('text',False)]:case(col+'_'+typ,'extensions',col,'numeric','extensions',col,typ,expected)
 case('unrelated_table','rooms','width','numeric','rooms','width','numeric(5,2)',False)
 case('unrelated_column','extensions','height','numeric','extensions','height','numeric(5,2)',False)
 case('wrong_target_table','extensions','width','numeric','rooms','width','numeric(5,2)',False)
 case('wrong_target_column','extensions','width','numeric','extensions','length','numeric(5,2)',False)
 case('different_reference_type','extensions','width','text','extensions','width','numeric(5,2)',False)
 case('ordinary_exact_type','properties','address','text','properties','address','text',True)
 case('missing_type','extensions','width','numeric','extensions','width',None,False)
 values=','.join('('+b.lit(name)+','+b.lit(json.dumps(required))+'::jsonb,'+b.lit(json.dumps(actual))+'::jsonb,'+str(expected).lower()+')' for name,required,actual,expected in rows)
 statement="select case_id from (values "+values+") cases(case_id,required,actual,expected) where coalesce((actual->>'table'=required->>'table' and actual->>'column'=required->>'column' and "+b.column_type_match_sql()+"),false) is distinct from expected;"
 assert statement.lower().startswith('select ')
 name='urbanfold-reconciliation-select-'+uuid.uuid4().hex[:8]
 try:
  subprocess.run(['docker','run','--rm','-d','--name',name,'--network','none','-e','POSTGRES_HOST_AUTH_METHOD=trust',IMAGE],check=True,capture_output=True)
  for _ in range(150):
   if subprocess.run(['docker','exec',name,'pg_isready','-h','127.0.0.1','-U','postgres'],capture_output=True).returncode==0:break
   time.sleep(.1)
  else:raise AssertionError('Offline SELECT test server unavailable')
  def select(sql):
   assert sql.lstrip().lower().startswith(('select ','with '))
   result=subprocess.run(['docker','exec','-i',name,'psql','-X','-q','-t','-A','-v','ON_ERROR_STOP=1','-U','postgres'],input=sql,text=True,capture_output=True)
   assert result.returncode==0,result.stderr
   return result.stdout.strip()
  assert select(statement)==''
  assert select('select 3.25::numeric(5,2)=3.25 and 999.99::numeric(5,2)=999.99 and 3.272::numeric(5,2)=3.27;')=='t'
  # The supplemental catalog-only query can be parsed/evaluated on an empty
  # cluster with ONLY its unchanged app-baseline subexpression replaced by {}.
  # No Auth/Storage fixture, schema DDL, migrations or source function executions.
  query=(OUT/'01_reconciliation_readonly.sql').read_text()
  assert query.count(b.metadata_expression())==1
  isolated=query.replace(b.metadata_expression(),"'{}'::jsonb")
  isolated='\n'.join(line for line in isolated.splitlines() if not line.lstrip().startswith('--')).strip()
  result=json.loads(select(isolated))
  assert result['rls_auto_enable']['present'] is False
  assert result['baseline_matches_reported'] is False
  assert result['existing_table_privileges']==[] and result['foreign_keys']==[]
  print('PASS '+str(len(rows))+' PostgreSQL SELECT-only type cases, numeric precision behaviour, supplemental catalog query with app-baseline stub; no application DDL/migrations, Supabase requests or payments')
 finally:subprocess.run(['docker','rm','-f',name],capture_output=True)
if __name__=='__main__':main()
