"""Proposed F02 outbox migration tests in disposable PostgreSQL, network disabled."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,time,uuid,json
from test_database_policies import IMAGE
ROOT=Path(__file__).resolve().parents[1]
def main():
 name='urbanfold-notification-test-'+uuid.uuid4().hex[:10]
 def sql(statement,error=None):
  p=subprocess.run(['docker','exec','-i',name,'psql','-X','-q','-t','-A','-v','ON_ERROR_STOP=1','-U','postgres'],input=statement,text=True,capture_output=True)
  if error:assert p.returncode and error in p.stderr,(error,p.stdout,p.stderr)
  else:assert p.returncode==0,p.stderr
  return p.stdout.strip()
 def claim(actor,prop,rev):return f"set role service_role;select claim_survey_notification('{actor}','{prop}','{rev}');"
 try:
  subprocess.run(['docker','run','--rm','-d','--name',name,'--network','none','-e','POSTGRES_HOST_AUTH_METHOD=trust',IMAGE],check=True,capture_output=True)
  for _ in range(150):
   if subprocess.run(['docker','exec',name,'pg_isready','-h','127.0.0.1','-U','postgres'],capture_output=True).returncode==0:break
   time.sleep(.1)
  else:raise AssertionError('PostgreSQL did not start')
  sql((ROOT/'tests/database_fixture.sql').read_text())
  sql('alter table auth.users add column email text,add column email_confirmed_at timestamptz;')
  for filename in ['001_secure_access.sql','002_survey_purchases.sql','003_survey_notifications.sql']:sql((ROOT/'supabase'/filename).read_text())
  sql((ROOT/'supabase/003_survey_notifications.sql').read_text())
  a,b,admin,c,unconfirmed=[str(uuid.uuid4()) for _ in range(5)]
  for uid,email,confirmed in [(a,'professional@example.test',True),(b,'other@example.test',True),(admin,'urbanfolduk@gmail.com',True),(c,'bulk@example.test',True),(unconfirmed,'pending@example.test',False)]:
   sql(f"insert into auth.users(id,email,email_confirmed_at)values('{uid}','{email}',{'now()' if confirmed else 'null'});")
  p1,p2=str(uuid.uuid4()),str(uuid.uuid4());rev='2026-11-03T12:00:00Z'
  for pid,owner in [(p1,a),(p2,b)]:
   sql(f"insert into properties(id,user_id,address,postcode,client_email,last_submitted_at)values('{pid}','{owner}','Fixture','AA1','client@example.test','{rev}');")
  for role in ['anon','authenticated']:
   sql(f'set role {role};select * from survey_notification_events;','permission denied')
   sql(f"set role {role};select claim_survey_notification('{a}','{p1}','{rev}');",'permission denied')
   sql(f"set role {role};select finish_survey_notification('{uuid.uuid4()}',true);",'permission denied')
  sql(claim(b,p1,rev),'NOTIFICATION_NOT_ALLOWED')
  sql(claim(unconfirmed,p1,rev),'NOTIFICATION_AUTH_REQUIRED')
  sql(claim(a,p1,'2026-11-02T12:00:00Z'),'NOTIFICATION_SUBMISSION_CHANGED')
  with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(lambda _:json.loads(sql(claim(a,p1,rev))),range(2)))
  assert sum(r['claimed'] for r in results)==1
  event=next(r for r in results if r['claimed'])
  assert event['payload']['client_email']=='client@example.test'
  assert event['payload']['client_email']!='professional@example.test'
  sql(f"set role service_role;select finish_survey_notification('{event['id']}',true);select finish_survey_notification('{event['id']}',false);")
  duplicate=json.loads(sql(claim(a,p1,rev)));assert duplicate['state']=='accepted' and not duplicate['claimed']
  assert sql('select count(*) from survey_notification_events;')=='1'
  repeated='2026-11-03T12:30:00Z';sql(f"update properties set last_submitted_at='{repeated}' where id='{p1}';")
  same=json.loads(sql(claim(a,p1,repeated)));assert not same['claimed'] and same['id']==event['id']
  # Existing admin workflow is retained; actor is rechecked against Auth records.
  assert json.loads(sql(claim(admin,p2,rev)))['claimed']
  # Uncertain sends never become a new claim for the same revision.
  newer='2026-11-03T13:00:00Z';sql(f"update properties set last_submitted_at='{newer}',notes='new revision' where id='{p1}';")
  second=json.loads(sql(claim(a,p1,newer)))
  sql(f"set role service_role;select finish_survey_notification('{second['id']}',false);")
  again=json.loads(sql(claim(a,p1,newer)));assert again['state']=='uncertain' and not again['claimed']
  for hour in range(14,17):
   timestamp=f'2026-11-03T{hour}:00:00Z';sql(f"update properties set last_submitted_at='{timestamp}',notes='{timestamp}' where id='{p1}';");assert json.loads(sql(claim(a,p1,timestamp)))['claimed']
  sql(f"update properties set last_submitted_at='2026-11-03T17:00:00Z',notes='over limit' where id='{p1}';")
  sql(claim(a,p1,'2026-11-03T17:00:00Z'),'NOTIFICATION_RATE_LIMIT')
  for n in range(21):
   pid=str(uuid.uuid4());sql(f"insert into properties(id,user_id,address,postcode,client_email,last_submitted_at)values('{pid}','{c}','Fixture','AA1','client@example.test','{rev}');")
   sql(claim(c,pid,rev),'NOTIFICATION_RATE_LIMIT' if n==20 else None)
  # Credit price and purchase contract are untouched.
  assert sql("select count(*) from information_schema.check_constraints where constraint_name='survey_credit_purchases_amount_total_check' and check_clause like '%600%';")=='1'
  print('PASS service-only claims/completion, ownership/confirmation, professional-client recipients, concurrent idempotency, admin access, uncertain delivery, rolling caps, repeatable migration and unchanged £6 constraint')
 finally:subprocess.run(['docker','rm','-f',name],capture_output=True)
if __name__=='__main__':main()
