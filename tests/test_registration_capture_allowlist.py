"""Exact identity staging-capture tests. Disposable PostgreSQL, network disabled.
No Auth API, SMTP, email, Supabase project or dispatcher is contacted.
"""
from pathlib import Path
import json,subprocess,time,uuid,re
from test_database_policies import IMAGE
ROOT=Path(__file__).resolve().parents[1]
UID='b83f87d8-abf2-4800-beab-8279917804c7'
EMAIL='urbanfolduk+staging-reg-01@gmail.com'
MARKER='Urbanfold-Survey-Staging reconstructed baseline; prepared 2026-11-03; never production.'
def main():
 subprocess.run(['python','scripts/build_registration_capture_sql.py','--check'],cwd=ROOT,check=True)
 name='urbanfold-allowlist-'+uuid.uuid4().hex[:8]
 def sql(stmt,error=None):
  p=subprocess.run(['docker','exec','-i',name,'psql','-X','-q','-t','-A','-v','ON_ERROR_STOP=1','-U','postgres'],input=stmt,text=True,capture_output=True)
  if error:assert p.returncode and error in p.stderr,(error,p.stdout,p.stderr)
  else:assert p.returncode==0,p.stderr
  return p.stdout.strip()
 def capture(payload,delivery,kind='registration_verified',error=None,role='service_role'):
  body=json.dumps(payload).replace("'","''")
  return sql(f"set role {role};select capture_staging_notification('{kind}','{delivery}','{body}'::jsonb);",error)
 def table_snapshot(table):return sql(f"select coalesce(jsonb_agg(to_jsonb(t) order by to_jsonb(t)::text),'[]'::jsonb) from {table} t;")
 try:
  subprocess.run(['docker','run','--rm','-d','--name',name,'--network','none','-e','POSTGRES_HOST_AUTH_METHOD=trust',IMAGE],check=True,capture_output=True)
  for _ in range(150):
   if subprocess.run(['docker','exec',name,'pg_isready','-h','127.0.0.1','-U','postgres'],capture_output=True).returncode==0:break
   time.sleep(.1)
  else:raise AssertionError('PostgreSQL unavailable')
  sql((ROOT/'tests/database_fixture.sql').read_text())
  sql("alter table auth.users add column email text,add column email_confirmed_at timestamptz,add column created_at timestamptz not null default now(),add column raw_user_meta_data jsonb default '{}'::jsonb;")
  legacy,other,prop=[str(uuid.uuid4()) for _ in range(3)]
  sql(f"insert into auth.users(id,email,email_confirmed_at)values('{legacy}','legacy@example.invalid',now()),('{other}','urbanfolduk+not-approved@gmail.com',now());")
  for f in ['001_secure_access.sql','002_survey_purchases.sql','003_survey_notifications.sql','004_verified_registration_notifications.sql']:sql((ROOT/'supabase'/f).read_text())
  sql(f"comment on table properties is '{MARKER}';")
  sql((ROOT/'supabase/staging/005_dummy_notification_receiver.sql').read_text())
  sql(f"insert into auth.users(id,email,email_confirmed_at,raw_user_meta_data)values('{UID}','{EMAIL}',now(),'{{\"newsletter_subscribed\":true}}');")
  sql(f"insert into properties(id,user_id,address,postcode,client_email,last_submitted_at)values('{prop}','{legacy}','DUMMY ALLOWLIST F02','ZZ9','legacy@example.invalid',now());")
  capture({'property_id':prop,'client_email':'legacy@example.invalid'},str(uuid.uuid4()),'survey')
  capture({'user_id':legacy,'registration_email':'legacy@example.invalid'},str(uuid.uuid4()))
  old_survey=sql("select jsonb_agg(to_jsonb(t)) from staging_notification_receipts t where kind='survey';")
  stable={t:table_snapshot(t) for t in ['properties','auth.users','newsletter_preferences','newsletter_consent_events','registration_notification_events','survey_credit_purchases','survey_free_allocations']}
  install=(ROOT/'supabase/staging/010_registration_capture_allowlist.sql').read_text()
  rollback=(ROOT/'supabase/staging/010_registration_capture_rollback.sql').read_text()
  pre=json.loads(sql((ROOT/'supabase/staging/010_registration_capture_preflight_readonly.sql').read_text()))
  assert pre['staging_marker_matches'] and pre['approved_verified_auth_identity'] and pre['approved_pending_event_count']==1
  assert pre['all_pending_registration_events']==1 and not pre['allowlist_already_exists']
  # Fails before any allowlist change outside the reviewed baseline.
  sql("comment on table properties is 'WRONG PROJECT MARKER';");sql(install,'Reviewed staging baseline required')
  assert sql("select to_regclass('public.staging_registration_capture_allowlist') is null;")=='t'
  sql(f"comment on table properties is '{MARKER}';")
  # Unknown deployed source must not be silently replaced.
  original=(ROOT/'supabase/staging/005_dummy_notification_receiver.sql').read_text()
  changed=original.replace('declare person uuid;','declare person uuid; -- changed helper')
  sql(changed);sql(install,'Capture helper differs from reviewed source');sql(original)
  sql(install);sql(install,'Capture helper differs from reviewed source')
  verified=json.loads(sql((ROOT/'supabase/staging/010_registration_capture_verify_readonly.sql').read_text()))
  assert all(verified[k] for k in ['allowlist_rls','one_exact_enabled_pair','no_client_table_access','service_table_read_only'])
  assert sql('select count(*) from staging_registration_capture_allowlist;')=='1'
  assert sql(f"select enabled from staging_registration_capture_allowlist where user_id='{UID}' and registration_email='{EMAIL}';")=='t'
  assert sql("select relrowsecurity from pg_class where oid='public.staging_registration_capture_allowlist'::regclass;")=='t'
  for t,before in stable.items():assert table_snapshot(t)==before,t
  for role in ['anon','authenticated']:
   sql(f'set role {role};select * from staging_registration_capture_allowlist;','permission denied')
   sql(f'set role {role};update staging_registration_capture_allowlist set enabled=true;','permission denied')
   sql(f'set role {role};select * from staging_notification_receipts;','permission denied')
   capture({},str(uuid.uuid4()),role=role,error='permission denied')
  for action in ["update staging_registration_capture_allowlist set enabled=true","delete from staging_registration_capture_allowlist",f"insert into staging_registration_capture_allowlist(user_id,registration_email)values('{other}','urbanfolduk+not-approved@gmail.com')"]:
   sql('set role service_role;'+action+';','permission denied')
  assert sql('set role service_role;select count(*) from staging_registration_capture_allowlist;')=='1'
  pending=json.loads(sql("select jsonb_build_object('id',id,'user_id',user_id,'registration_email',registration_email,'registered_at',registered_at,'verified_at',verified_at,'newsletter_signup_choice',newsletter_signup_choice,'newsletter_opted_in_at_verification',newsletter_opted_in_at_verification) from registration_notification_events;"))
  payload={**pending,'notification_type':'registration_verified','recipient':'urbanfolduk@gmail.com'}
  # A pending event has not passed the rate-limited claim path.
  capture(payload,payload['id'],error='DUMMY_REGISTRATION_REQUIRED')
  claimed=json.loads(sql('set role service_role;select claim_registration_notification();'))
  payload={k:v for k,v in claimed.items() if k!='claim_started_at'}
  payload.update(notification_type='registration_verified',recipient='urbanfolduk@gmail.com')
  for overrides in [
   {'user_id':other},{'registration_email':'urbanfolduk+not-approved@gmail.com'},
   {'registration_email':'urbanfolduk@gmail.com'},{'registration_email':'another@gmail.com'},
   {'recipient':'urbanfolduk+not-approved@gmail.com'},{'newsletter_signup_choice':False},
   {'newsletter_signup_choice':'true'},{'verified_at':'2000-01-01T00:00:00Z'},
   {'registered_at':'2000-01-01T00:00:00Z'},{'notification_type':'survey'},{'id':str(uuid.uuid4())}
  ]:capture({**payload,**overrides},payload['id'],error='DUMMY_REGISTRATION_REQUIRED')
  capture(payload,str(uuid.uuid4()),error='DUMMY_REGISTRATION_REQUIRED')
  sql('update staging_registration_capture_allowlist set enabled=false;');capture(payload,payload['id'],error='DUMMY_REGISTRATION_REQUIRED');sql('update staging_registration_capture_allowlist set enabled=true;')
  sql(f"update auth.users set email_confirmed_at=null where id='{UID}';");capture(payload,payload['id'],error='DUMMY_REGISTRATION_REQUIRED')
  sql(f"update auth.users set email_confirmed_at='{payload['verified_at']}' where id='{UID}';")
  sql(f"update auth.users set email='urbanfolduk+not-approved@gmail.com' where id='{UID}';");capture(payload,payload['id'],error='DUMMY_REGISTRATION_REQUIRED');sql(f"update auth.users set email='{EMAIL}' where id='{UID}';")
  capture({**payload,'registration_email':'forged@example.invalid'},payload['id'],error='DUMMY_USER_REQUIRED')
  # Allowlisting a registration never permits a Gmail owner's survey capture.
  prop2=str(uuid.uuid4());sql(f"insert into properties(id,user_id,address,postcode)values('{prop2}','{UID}','DUMMY DENIED GMAIL SURVEY','ZZ9');")
  capture({'property_id':prop2,'client_email':'legacy@example.invalid'},str(uuid.uuid4()),'survey',error='DUMMY_USER_REQUIRED')
  capture({'property_id':prop,'client_email':EMAIL},str(uuid.uuid4()),'survey',error='DUMMY_RECIPIENT_REQUIRED')
  # An operational notice is historical, not a subscription requirement. A
  # withdrawal changes current consent without rewriting the signup snapshot.
  claims=json.dumps({'sub':UID,'role':'authenticated','email':EMAIL})
  sql(f"set role authenticated;set request.jwt.claims='{claims}';select set_newsletter_preference(false);")
  assert sql(f"select opted_in from newsletter_preferences where user_id='{UID}';")=='f'
  assert sql(f"select newsletter_signup_choice from registration_notification_events where user_id='{UID}';")=='t'
  capture(payload,payload['id'])
  sql(f"set role service_role;select finish_registration_notification('{payload['id']}',true,'{claimed['claim_started_at']}');")
  assert sql('set role service_role;select claim_registration_notification();')==''
  # Direct server retries retain one receipt; attempts counter records retries.
  capture(payload,payload['id'])
  assert sql(f"select count(*)||':'||max(attempts) from staging_notification_receipts where kind='registration_verified' and delivery_id='{payload['id']}';")=='1:2'
  assert sql("select jsonb_agg(to_jsonb(t)) from staging_notification_receipts t where kind='survey';")==old_survey
  assert sql("select count(*) from pg_constraint where conrelid='survey_credit_purchases'::regclass and conname='survey_credit_purchases_amount_total_check' and pg_get_constraintdef(oid) like '%600%';")=='1'
  before=table_snapshot('staging_notification_receipts');sql(rollback)
  capture(payload,payload['id'],error='DUMMY_REGISTRATION_REQUIRED')
  assert table_snapshot('staging_notification_receipts')==before
  assert sql('select count(*) from staging_registration_capture_allowlist;')=='1'
  capture({'property_id':prop,'client_email':'legacy@example.invalid'},str(uuid.uuid4()),'survey')
  # Source-level survey branch equality guards against accidental F02 drift.
  def branch(s):return s.split("if kind='survey' then",1)[1].split("elsif kind='registration_verified'",1)[0]
  assert branch(install)==branch(original)
  print('PASS exact identity + confirmed Auth + claimed queue/snapshot binding; no Gmail/domain wildcard; private owner-write/service-read allowlist; client/service mutation denials; pending/forged/disabled/unconfirmed/wrong-ID failures; original consent/credits/F02 preserved; one-row receipt idempotency; guarded source/marker install and data-preserving rollback')
 finally:subprocess.run(['docker','rm','-f',name],capture_output=True)
if __name__=='__main__':main()
