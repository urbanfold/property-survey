"""Row-only011 + consent withdrawal tests in disposable PostgreSQL --network none.
Authenticated roles/claims here model RPC/RLS; they are NOT genuine staging sessions.
"""
from pathlib import Path
import json,subprocess,time,uuid,re
from test_database_policies import IMAGE
ROOT=Path(__file__).resolve().parents[1]
IDS=['b83f87d8-abf2-4800-beab-8279917804c7','d2598ebf-d44c-4e11-81a5-d82f3d06ada1','3a4e8d72-bf58-468a-b24f-0417c4a64f5b']
EMAILS=[f'urbanfolduk+staging-reg-0{n}@gmail.com' for n in range(1,4)]
MARKER='Urbanfold-Survey-Staging reconstructed baseline; prepared 2026-11-03; never production.'
def main():
 subprocess.run(['python','scripts/build_registration_capture_extension_sql.py','--check'],cwd=ROOT,check=True)
 name='urbanfold-extension-'+uuid.uuid4().hex[:8]
 def sql(stmt,error=None):
  p=subprocess.run(['docker','exec','-i',name,'psql','-X','-q','-t','-A','-v','ON_ERROR_STOP=1','-U','postgres'],input=stmt,text=True,capture_output=True)
  if error:assert p.returncode and error in p.stderr,(error,p.stdout,p.stderr)
  else:assert p.returncode==0,p.stderr
  return p.stdout.strip()
 def snap(table):return sql(f"select coalesce(jsonb_agg(to_jsonb(t) order by to_jsonb(t)::text),'[]'::jsonb) from {table} t;")
 def actor(n,stmt):
  claims=json.dumps({'sub':IDS[n-1],'role':'authenticated','email':EMAILS[n-1]})
  return sql(f"set role authenticated;set request.jwt.claims='{claims}';"+stmt)
 def capture_claim():
  event=json.loads(sql('set role service_role;select claim_registration_notification();'))
  body={k:v for k,v in event.items() if k!='claim_started_at'}
  body.update(recipient='urbanfolduk@gmail.com',notification_type='registration_verified')
  literal=json.dumps(body).replace("'","''")
  sql(f"set role service_role;select capture_staging_notification('registration_verified','{event['id']}','{literal}');")
  result=json.loads(sql(f"set role service_role;select finish_registration_notification('{event['id']}',true,'{event['claim_started_at']}');"))
  assert result['state']=='accepted';return event
 try:
  subprocess.run(['docker','run','--rm','-d','--name',name,'--network','none','-e','POSTGRES_HOST_AUTH_METHOD=trust',IMAGE],check=True,capture_output=True)
  for _ in range(150):
   if subprocess.run(['docker','exec',name,'pg_isready','-h','127.0.0.1','-U','postgres'],capture_output=True).returncode==0:break
   time.sleep(.1)
  else:raise AssertionError('Postgres unavailable')
  sql((ROOT/'tests/database_fixture.sql').read_text())
  sql("alter table auth.users add column email text,add column email_confirmed_at timestamptz,add column created_at timestamptz not null default now(),add column raw_user_meta_data jsonb default '{}'::jsonb;")
  for f in ['001_secure_access.sql','002_survey_purchases.sql','003_survey_notifications.sql']:sql((ROOT/'supabase'/f).read_text())
  legacy,property_id=str(uuid.uuid4()),str(uuid.uuid4())
  sql(f"insert into auth.users(id,email,email_confirmed_at)values('{legacy}','legacy@example.invalid',now());")
  sql((ROOT/'supabase/004_verified_registration_notifications.sql').read_text())
  sql(f"comment on table properties is '{MARKER}';")
  sql((ROOT/'supabase/staging/005_dummy_notification_receiver.sql').read_text())
  # Nonempty F02 evidence must survive the upgrade and rollback, not just counts0.
  sql(f"insert into properties(id,user_id,address,postcode,client_email,last_submitted_at)values('{property_id}','{legacy}','DUMMY EXTENSION F02','ZZ9','legacy@example.invalid',now());")
  revision=sql(f"select last_submitted_at::text from properties where id='{property_id}';")
  survey=json.loads(sql(f"set role service_role;select claim_survey_notification('{legacy}','{property_id}','{revision}');"))
  survey_payload=json.dumps(survey['payload']).replace("'","''")
  sql(f"set role service_role;select capture_staging_notification('survey','{survey['id']}','{survey_payload}');select finish_survey_notification('{survey['id']}',true);")
  sql(f"insert into auth.users(id,email,email_confirmed_at,raw_user_meta_data)values('{IDS[0]}','{EMAILS[0]}',now(),'{{\"newsletter_subscribed\":true}}');")
  sql((ROOT/'supabase/staging/010_registration_capture_allowlist.sql').read_text())
  first_event=capture_claim();assert first_event['user_id']==IDS[0] and first_event['newsletter_signup_choice'] is True
  for n,raw in [(2,'false'),(3,'"true"')]:
   sql(f'''insert into auth.users(id,email,raw_user_meta_data)values('{IDS[n-1]}','{EMAILS[n-1]}','{{"newsletter_subscribed":{raw}}}');''')
   sql(f"update auth.users set email_confirmed_at=now() where id='{IDS[n-1]}';")
  upgrade=(ROOT/'supabase/staging/011_registration_capture_extend.sql').read_text()
  rollback=(ROOT/'supabase/staging/011_registration_capture_rollback.sql').read_text()
  readcheck=(ROOT/'supabase/staging/011_registration_capture_preflight_readonly.sql').read_text()
  pre=json.loads(sql(readcheck));assert pre['allowlist_entries']==1 and pre['all_pending_registration_events']==2
  assert [x['allowlisted'] for x in pre['identities']]==[True,False,False]
  before_first=snap('staging_registration_capture_allowlist')
  fn_before=sql("select pg_get_functiondef('public.capture_staging_notification(text,uuid,jsonb)'::regprocedure);")
  stable_tables=['auth.users','properties','newsletter_preferences','newsletter_consent_events','registration_notification_events','staging_notification_receipts','survey_notification_events','survey_credit_purchases','survey_free_allocations','survey_credit_revocations']
  before={t:snap(t) for t in stable_tables}
  # Fail closed on wrong project marker, unexpected source/entry or unverified Auth.
  sql("comment on table properties is 'WRONG';");sql(upgrade,'Reviewed staging baseline required');sql(f"comment on table properties is '{MARKER}';")
  sql(f"update auth.users set email_confirmed_at=null where id='{IDS[2]}';");sql(upgrade,'Exact verified false-consent identities')
  stamp=sql(f"select verified_at::text from registration_notification_events where user_id='{IDS[2]}';")
  sql(f"update auth.users set email_confirmed_at='{stamp}' where id='{IDS[2]}';")
  # Auth row transition is test-fixture-only; reset baseline for row snapshot check.
  before={t:snap(t) for t in stable_tables}
  sql('update staging_registration_capture_allowlist set enabled=false;');sql(upgrade,'Test1 exact enabled entry');sql('update staging_registration_capture_allowlist set enabled=true;')
  sql('grant update on staging_registration_capture_allowlist to service_role;');sql(upgrade,'Unexpected allowlist trigger/rule/policy/grants');sql('revoke update on staging_registration_capture_allowlist from service_role;')
  # Unknown function source must not be accepted or replaced.
  fn=fn_before.replace('declare person uuid;','declare person uuid; /* unexpected source */')
  sql(fn);sql(upgrade,'Capture source/owner/path/permissions differ');sql(fn_before)
  sql(upgrade);sql(upgrade,'Expected Test1 only')
  for t,v in before.items():assert snap(t)==v,t
  first_now=sql(f"select to_jsonb(t) from staging_registration_capture_allowlist t where user_id='{IDS[0]}';")
  assert json.loads(first_now)==json.loads(before_first)[0]
  assert sql("select pg_get_functiondef('public.capture_staging_notification(text,uuid,jsonb)'::regprocedure);")==fn_before
  post=json.loads(sql((ROOT/'supabase/staging/011_registration_capture_verify_readonly.sql').read_text()))
  assert post['allowlist_entries']==3 and all(x['allowlisted'] for x in post['identities'])
  assert post['capture_body_sha256']==pre['capture_body_sha256']
  for role in ['anon','authenticated']:
   sql(f'set role {role};select * from staging_registration_capture_allowlist;','permission denied')
   sql(f'set role {role};update staging_registration_capture_allowlist set enabled=true;','permission denied')
  sql('set role service_role;update staging_registration_capture_allowlist set enabled=true;','permission denied')
  # Both false-choice accounts can use unchanged rate-limited claim/capture path.
  events=[capture_claim(),capture_claim()]
  assert {e['user_id'] for e in events}==set(IDS[1:])
  assert all(e['newsletter_signup_choice'] is False and e['newsletter_opted_in_at_verification'] is False for e in events)
  assert sql('set role service_role;select claim_registration_notification();')==''
  # Model own authenticated withdrawal; no privileged preferences UPDATE.
  historical_before=snap('registration_notification_events');receipts_before=snap('staging_notification_receipts')
  evidence_sql=(ROOT/'supabase/staging/011_newsletter_withdrawal_evidence_readonly.sql').read_text()
  evidence_before=json.loads(sql(evidence_sql))
  assert evidence_before['original_signup_choice'] is True and evidence_before['current_consent'] is True
  audit_before=int(sql(f"select count(*) from newsletter_consent_events where user_id='{IDS[0]}';"))
  assert json.loads(actor(1,'select get_newsletter_preference();'))['opted_in'] is True
  result=json.loads(actor(1,'select set_newsletter_preference(false);'));assert result['opted_in'] is False
  evidence_after=json.loads(sql(evidence_sql))
  assert evidence_after['original_signup_choice'] is True and evidence_after['current_consent'] is False
  assert evidence_after['registration_history_sha256']==evidence_before['registration_history_sha256']
  assert evidence_after['registration_receipts_sha256']==evidence_before['registration_receipts_sha256']
  assert evidence_after['withdrawal_audits']==evidence_before['withdrawal_audits']+1
  assert sql(f"select signup_opt_in_requested from newsletter_preferences where user_id='{IDS[0]}';")=='t'
  assert int(sql(f"select count(*) from newsletter_consent_events where user_id='{IDS[0]}';"))==audit_before+1
  assert sql(f"select count(*) from newsletter_consent_events where user_id='{IDS[0]}' and action='preference_change' and choice is false;")=='1'
  after_first_withdrawal=sql(f"select to_jsonb(t) from newsletter_preferences t where user_id='{IDS[0]}';")
  actor(1,'select set_newsletter_preference(false);')
  assert sql(f"select to_jsonb(t) from newsletter_preferences t where user_id='{IDS[0]}';")==after_first_withdrawal
  assert int(sql(f"select count(*) from newsletter_consent_events where user_id='{IDS[0]}';"))==audit_before+1
  # A second user's call is identity-bound to themselves, cannot change Test1.
  test1_pref=sql(f"select to_jsonb(t) from newsletter_preferences t where user_id='{IDS[0]}';")
  actor(2,'select set_newsletter_preference(true);')
  assert sql(f"select to_jsonb(t) from newsletter_preferences t where user_id='{IDS[0]}';")==test1_pref
  claims=json.dumps({'sub':IDS[1],'role':'authenticated','email':EMAILS[1]})
  sql(f"set role authenticated;set request.jwt.claims='{claims}';select set_newsletter_preference(true,'{IDS[0]}'::uuid);",'does not exist')
  sql(f"set role authenticated;update newsletter_preferences set opted_in=true where user_id='{IDS[0]}';",'permission denied')
  assert sql(f"select to_jsonb(t) from newsletter_preferences t where user_id='{IDS[0]}';")==test1_pref
  assert snap('registration_notification_events')==historical_before and snap('staging_notification_receipts')==receipts_before
  history={t:snap(t) for t in stable_tables}
  sql(rollback);sql(rollback)
  for t,v in history.items():assert snap(t)==v,t
  assert sql('select count(*) from staging_registration_capture_allowlist;')=='3'
  assert sql('select count(*) from staging_registration_capture_allowlist where enabled;')=='1'
  assert json.loads(sql(f"select to_jsonb(t) from staging_registration_capture_allowlist t where user_id='{IDS[0]}';"))==json.loads(before_first)[0]
  print('PASS row-only011 exact false-choice identities; known010/schema/grant/marker guards; Test1 and all history/consent/credit/function snapshots preserved; no reinstall; private grants unchanged; captures use existing rate-limited path; rollback only disables added entries without deleting evidence')
  print('PASS LOCAL MODEL own authenticated preference RPC withdrawal true-to-false, original true/history unchanged, one audit, repeated false idempotent, other-user scope/forged target/direct DML denial. No real Test1 staging session used.')
 finally:subprocess.run(['docker','rm','-f',name],capture_output=True)
if __name__=='__main__':main()
