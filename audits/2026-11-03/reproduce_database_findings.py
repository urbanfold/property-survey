"""Audit-only PostgreSQL tests, in a disposable --network none Docker container.
Never connect this script to Supabase. Finding assertions describe existing code.
"""
from pathlib import Path
import json,subprocess,sys,time,uuid
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tests'))
from test_database_policies import IMAGE

def main():
 name='urbanfold-audit-'+uuid.uuid4().hex[:10];results=[]
 def sql(statement,error=None,database='postgres'):
  p=subprocess.run(['docker','exec','-i',name,'psql','-X','-q','-t','-A','-v','ON_ERROR_STOP=1','-U','postgres','-d',database],input=statement,text=True,capture_output=True)
  if error:assert p.returncode and error in p.stderr,(error,p.stdout,p.stderr)
  else:assert p.returncode==0,p.stderr
  return p.stdout.strip()
 def user(uid,body,email='fixture@example.test'):
  claims=json.dumps({'sub':uid,'role':'authenticated','email':email,'aal':'aal1'})
  return f"set role authenticated;set request.jwt.claims='{claims}';{body}"
 try:
  subprocess.run(['docker','run','--rm','-d','--name',name,'--network','none','-e','POSTGRES_HOST_AUTH_METHOD=trust',IMAGE],check=True,capture_output=True)
  for _ in range(150):
   if subprocess.run(['docker','exec',name,'pg_isready','-h','127.0.0.1','-U','postgres'],capture_output=True).returncode==0:break
   time.sleep(.1)
  else:raise AssertionError('Offline PostgreSQL unavailable')
  sql((ROOT/'tests/database_fixture.sql').read_text())
  m1=(ROOT/'supabase/001_secure_access.sql').read_text();m2=(ROOT/'supabase/002_survey_purchases.sql').read_text()
  sql(m1);sql(m2)
  a,b,admin,p1,p2,r1,r2=[str(uuid.uuid4()) for _ in range(7)]
  sql(f"insert into auth.users values('{a}'),('{b}'),('{admin}');insert into properties(id,user_id,address,postcode)values('{p1}','{a}','FIXTURE A','AA1'),('{p2}','{b}','FIXTURE B','BB2');insert into rooms(id,property_id,room_name)values('{r1}','{p1}','Kitchen'),('{r2}','{p2}','Kitchen');")
  for table in ['extensions','exterior_photos','extension_photos','sketch_photos']:
   extra,vals=('','') if table=='extensions' else (',photo_url',",'storage://exterior-photos/fixture.jpg'")
   if table=='exterior_photos':extra+=',elevation_type';vals+=",'front'"
   sql(f"insert into {table}(property_id{extra})values('{p1}'{vals}),('{p2}'{vals});")
  sql(f"insert into room_photos(room_id,photo_url)values('{r1}','storage://room-photos/{p1}/a.jpg'),('{r2}','storage://room-photos/{p2}/b.jpg');")
  tables=['properties','extensions','rooms','exterior_photos','extension_photos','sketch_photos','room_photos']
  for table in tables:
   condition=f"id='{p2}'" if table=='properties' else f"room_id='{r2}'" if table=='room_photos' else f"property_id='{p2}'"
   assert sql(user(a,f'select count(*) from {table};'))=='1'
   assert sql('set role anon;select count(*) from '+table+';')=='0'
   assert sql(user(a,f'with gone as(delete from {table} where {condition} returning *)select count(*) from gone;'))=='0'
   field='notes' if table=='properties' else 'additional_measurements' if table=='rooms' else 'description' if table=='extensions' else 'photo_url'
   assert sql(user(a,f"with changed as(update {table} set {field}='INJECTED' where {condition} returning *)select count(*) from changed;"))=='0'
  for bucket in ['exterior-photos','sketch-photos','room-photos']:
   sql(f"insert into storage.objects(bucket_id,name)values('{bucket}','{p1}/a.jpg'),('{bucket}','{p2}/b.jpg');")
   assert sql(user(a,f"select count(*) from storage.objects where bucket_id='{bucket}';"))=='1'
   assert sql(user(a,f"select count(*) from storage.objects where bucket_id='{bucket}' and name='{p2}/b.jpg';"))=='0'
   sql(user(a,f"insert into storage.objects(bucket_id,name)values('{bucket}','{p2}/forged.jpg');"),'row-level security')
   assert sql(user(a,f"with d as(delete from storage.objects where bucket_id='{bucket}' and name='{p2}/b.jpg' returning *)select count(*) from d;"))=='0'
   assert sql(user(a,f"with u as(update storage.objects set name='forged' where bucket_id='{bucket}' and name='{p2}/b.jpg' returning *)select count(*) from u;"))=='0'
  # Child inserts using another owner's foreign key must fail as well.
  for table in ['extensions','rooms','exterior_photos','extension_photos','sketch_photos','room_photos']:
   parent='room_id' if table=='room_photos' else 'property_id'
   target=r2 if table=='room_photos' else p2
   cols,values='', ''
   if table=='rooms':cols+=',room_name';values+=",'Forged'"
   elif table!='extensions':cols+=',photo_url';values+=",'storage://room-photos/fixture.jpg'"
   if table=='exterior_photos':cols+=',elevation_type';values+=",'front'"
   sql(user(a,f"insert into {table}({parent}{cols})values('{target}'{values});"),'row-level security')
  results.append({'id':'DB-PASS-01','result':'PASS: other-owner read/update/delete denied across seven tables and three storage buckets; other-owner storage insert denied'})
  info=json.loads(sql("select json_build_object('security_definer',p.prosecdef,'config',p.proconfig,'owner',pg_get_userbyid(p.proowner),'authenticated_execute',has_function_privilege('authenticated',p.oid,'execute'),'anon_execute',has_function_privilege('anon',p.oid,'execute')) from pg_proc p join pg_namespace n on n.oid=p.pronamespace where n.nspname='public' and p.proname='get_survey_allowance';"))
  assert info['security_definer'] and info['config']==['search_path=""'] and info['authenticated_execute'] and not info['anon_execute'],info
  assert json.loads(sql(user(a,'select get_survey_allowance();')))['free_available']  # Admin-created fixture rows not allocated until backfill.
  sql('set role authenticated;select get_survey_allowance();','Sign in to check')
  denied_functions=['enforce_survey_allowance()','protect_survey_address()',
   'record_survey_purchase(text,text,uuid,integer,text,boolean)','revoke_survey_purchase(text,text)']
  for function in denied_functions:
   assert sql(f"select has_function_privilege('authenticated','public.{function}','execute');")=='f'
   assert sql(f"select has_function_privilege('anon','public.{function}','execute');")=='f'
  sql('alter table storage.buckets add column file_size_limit bigint, add column allowed_mime_types text[];')
  diagnostic=json.loads(sql((ROOT/'audits/2026-11-03/read_only_metadata.sql').read_text()))
  assert len(diagnostic['functions'])==5 and len(diagnostic['buckets'])==3
  results.append({'id':'DB-PASS-02','result':'PASS: supplied allowance function fixes search_path, checks identity, permits authenticated and denies anon','metadata':info})
  # Authorised owner can forge a cross-property photo reference, but not fetch its object.
  sql(user(a,f"insert into exterior_photos(property_id,elevation_type,photo_url)values('{p1}','rear','storage://exterior-photos/{p2}/b.jpg');"))
  assert sql(user(a,f"select count(*) from exterior_photos where property_id='{p1}' and photo_url like '%{p2}%';"))=='1'
  assert sql(user(a,f"select count(*) from storage.objects where name='{p2}/b.jpg';"))=='0'
  results.append({'id':'DB-FINDING-01','result':'CONFIRMED: photo metadata accepts another property storage reference; direct object read remains denied'})
  assert sql(user(admin,'select count(*) from properties;',email='urbanfolduk@gmail.com'))=='2'
  results.append({'id':'DB-FINDING-02','result':'CONFIRMED: admin email claim grants cross-owner access at aal1; no aal2 requirement in SQL. This does not demonstrate JWT forgery.'})
  # Simulate newly created tables without old implicit grants, as of platform change.
  sql('revoke select,insert,update,delete on '+','.join('public.'+t for t in tables)+' from anon,authenticated;')
  sql(m1);sql(m2)
  sql(user(a,'select count(*) from properties;'),'permission denied for table properties')
  results.append({'id':'DB-FINDING-03','result':'CONFIRMED: 001/002 do not restore explicit application-table grants when legacy grants are absent; test fixture grants masked this dependency'})
  subprocess.run(['docker','exec',name,'createdb','-U','postgres','audit_empty'],check=True,capture_output=True)
  sql(m1,'relation "public.properties" does not exist',database='audit_empty')
  results.append({'id':'DB-FINDING-04','result':'CONFIRMED: production migrations do not bootstrap an empty database; baseline schema is only in a test fixture'})
  print(json.dumps({'environment':'disposable PostgreSQL, network disabled; simulated JWT claims, not live Auth','results':results},indent=2))
 finally:subprocess.run(['docker','rm','-f',name],capture_output=True)
if __name__=='__main__':main()
