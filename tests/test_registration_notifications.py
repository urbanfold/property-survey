"""Local network-disabled PostgreSQL: consent, Auth confirmation queue, dummy sink.
Never connects to Supabase. No email provider or real users.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,time,uuid,json
from test_database_policies import IMAGE
ROOT=Path(__file__).resolve().parents[1]
def main():
 name='urbanfold-registration-'+uuid.uuid4().hex[:8]
 def sql(statement,error=None):
  p=subprocess.run(['docker','exec','-i',name,'psql','-X','-q','-t','-A','-v','ON_ERROR_STOP=1','-U','postgres'],input=statement,text=True,capture_output=True)
  if error:assert p.returncode and error in p.stderr,(error,p.stdout,p.stderr)
  else:assert p.returncode==0,p.stderr
  return p.stdout.strip()
 def user(uid,statement):return "set role authenticated;select set_config('request.jwt.claims','"+json.dumps({'sub':uid,'role':'authenticated','email':'dummy@example.invalid'})+"',false);"+statement
 try:
  subprocess.run(['docker','run','--rm','-d','--name',name,'--network','none','-e','POSTGRES_HOST_AUTH_METHOD=trust',IMAGE],check=True,capture_output=True)
  for _ in range(150):
   if subprocess.run(['docker','exec',name,'pg_isready','-h','127.0.0.1','-U','postgres'],capture_output=True).returncode==0:break
   time.sleep(.1)
  else:raise AssertionError('Postgres unavailable')
  sql((ROOT/'tests/database_fixture.sql').read_text())
  sql("alter table auth.users add column email text,add column email_confirmed_at timestamptz,add column created_at timestamptz not null default now(),add column raw_user_meta_data jsonb default '{}'::jsonb;")
  old=str(uuid.uuid4());sql(f"insert into auth.users(id,email) values('{old}','old@example.invalid');")
  for f in ['001_secure_access.sql','002_survey_purchases.sql','003_survey_notifications.sql','004_verified_registration_notifications.sql']:sql((ROOT/'supabase'/f).read_text())
  sql((ROOT/'supabase/004_verified_registration_notifications.sql').read_text())
  a,b,unconfirmed=[str(uuid.uuid4()) for _ in range(3)]
  sql(f'''insert into auth.users(id,email,raw_user_meta_data)values('{a}','a@example.invalid','{{"newsletter_subscribed":true,"newsletter_consent_at":"1900-01-01","newsletter_consent_version":"forged"}}');''')
  assert sql('select count(*) from registration_notification_events;')=='0'
  assert sql(f"select opted_in from newsletter_preferences where user_id='{a}';")=='f'
  assert sql(f"select consent_version from newsletter_consent_events where user_id='{a}';")=='2026-10-23'
  assert sql(f"select count(*) from newsletter_consent_events where user_id='{a}' and occurred_at > '2020-01-01';")=='1'
  sql(f'''update auth.users set raw_user_meta_data='{{"newsletter_subscribed":false}}' where id='{a}';''')
  sql(f"update auth.users set email_confirmed_at=now() where id='{a}';")
  assert sql(f"select opted_in from newsletter_preferences where user_id='{a}';")=='t'
  assert sql('select count(*) from registration_notification_events;')=='1'
  sql(f"update auth.users set email='new-a@example.invalid',email_confirmed_at=now() where id='{a}';")
  assert sql('select count(*) from registration_notification_events;')=='1'
  assert sql("select registration_email from registration_notification_events;")=='a@example.invalid'
  # String 'true' is not an explicit boolean opt-in.
  sql(f'''insert into auth.users(id,email,email_confirmed_at,raw_user_meta_data)values('{b}','b@example.invalid',now(),'{{"newsletter_subscribed":"true"}}');''')
  assert sql(f"select opted_in from newsletter_preferences where user_id='{b}';")=='f'
  assert sql(f"select newsletter_signup_choice from registration_notification_events where user_id='{b}';")=='f'
  sql(f"update auth.users set email_confirmed_at=now() where id='{old}';")
  assert sql(f"select count(*) from registration_notification_events where user_id='{old}';")=='0'
  # Real recipient snapshot/registration timestamp come from Auth, not browser claims.
  assert sql(f"select registered_at=(select created_at from auth.users where id='{a}') from registration_notification_events where user_id='{a}';")=='t'
  sql(user(a,"select set_newsletter_preference(false);"))
  assert sql(f"select opted_in from newsletter_preferences where user_id='{a}';")=='f'
  assert sql(f"select newsletter_signup_choice from registration_notification_events where user_id='{a}';")=='t'
  before=sql(f"select count(*) from newsletter_consent_events where user_id='{a}';")
  sql(user(a,"select set_newsletter_preference(false);"))
  assert sql(f"select count(*) from newsletter_consent_events where user_id='{a}';")==before
  sql(user(a,"select set_newsletter_preference(true);"))
  assert sql(f"select opted_in from newsletter_preferences where user_id='{a}';")=='t'
  assert sql(user(b,'select count(*) from newsletter_preferences;')).splitlines()[-1]=='1'
  assert sql(user(b,f"select count(*) from newsletter_consent_events where user_id='{a}';")).splitlines()[-1]=='0'
  for statement in ['update newsletter_preferences set opted_in=true;',"insert into newsletter_consent_events(user_id,action,source,consent_version,consent_text)values('"+a+"','preference_change','forged','forged','forged');",'select * from registration_notification_events;','select claim_registration_notification();']:
   sql(user(b,statement),'permission denied')
  sql('set role service_role;update newsletter_consent_events set choice=true;','permission denied')
  sql('set role service_role;delete from newsletter_consent_events;','permission denied')
  sql('set role anon;select get_newsletter_preference();','permission denied')
  sql('select get_newsletter_preference();','Sign in')
  sql(f"insert into auth.users(id,email)values('{unconfirmed}','pending@example.invalid');")
  sql(user(unconfirmed,'select set_newsletter_preference(true);'),'verified account')
  # Two concurrently claimed events must differ, followed by no claim.
  def claim(_):return json.loads(sql('set role service_role;select claim_registration_notification();'))
  with ThreadPoolExecutor(max_workers=2) as pool:claimed=list(pool.map(claim,range(2)))
  assert len({e['id'] for e in claimed})==2
  assert sql('set role service_role;select claim_registration_notification();')==''
  for event in claimed:
   sql(f"set role service_role;select finish_registration_notification('{event['id']}',false);select finish_registration_notification('{event['id']}',true);")
  assert sql("select count(*) from registration_notification_events where state='uncertain';")=='2'
  assert sql('set role service_role;select claim_registration_notification();')==''
  # Dummy sink independent of message type cannot accept real email/property data.
  sql("comment on table public.properties is 'Urbanfold-Survey-Staging reconstructed baseline; prepared 2026-11-03; never production.';")
  sql((ROOT/'supabase/staging/005_dummy_notification_receiver.sql').read_text())
  event=claimed[0]
  payload=json.dumps({**event,'recipient':'urbanfolduk@gmail.com'})
  for _ in range(2):sql(f"set role service_role;select capture_staging_notification('registration_verified','{event['id']}','{payload}');")
  assert sql('select attempts from staging_notification_receipts;')=='2'
  sql(f"set role service_role;select capture_staging_notification('registration_verified','{uuid.uuid4()}','{{\"user_id\":\"{a}\",\"registration_email\":\"real@example.com\"}}');",'DUMMY_REGISTRATION_REQUIRED')
  sql(user(a,'select * from staging_notification_receipts;'),'permission denied')
  assert sql("select count(*) from information_schema.check_constraints where constraint_name='survey_credit_purchases_amount_total_check' and check_clause like '%600%';")=='1'
  print('PASS optional strict signup intent, server audit timestamp/version, confirmation-only unique registration queue, no historic backfill, ownership/ACLs, opt-in/withdrawal, concurrency/uncertain no-retry, dummy-only capture and unchanged £6 constraint')
 finally:subprocess.run(['docker','rm','-f',name],capture_output=True)
if __name__=='__main__':main()
