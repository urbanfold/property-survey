"""Preparation guards in local PostgreSQL --network none only. Never Supabase."""
from pathlib import Path
import importlib.util,json,subprocess,sys,time,uuid,hashlib
sys.path.insert(0,str(Path(__file__).parent))
from test_database_policies import IMAGE
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'supabase/production-review/2026-11-07'
spec=importlib.util.spec_from_file_location('production_review',ROOT/'scripts/build_production_backend_review.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)

def main():
 name='urbanfold-production-review-'+uuid.uuid4().hex[:8]
 def sql(text,error=None):
  p=subprocess.run(['docker','exec','-i',name,'psql','-X','-q','-t','-A','-v','ON_ERROR_STOP=1','-U','postgres'],input=text,text=True,capture_output=True)
  if error:assert p.returncode and error in p.stderr,(error,p.stderr)
  else:assert p.returncode==0,p.stderr
  return p.stdout.strip()
 try:
  subprocess.run(['docker','run','--rm','-d','--name',name,'--network','none','-e','POSTGRES_HOST_AUTH_METHOD=trust',IMAGE],check=True,capture_output=True)
  for _ in range(150):
   if subprocess.run(['docker','exec',name,'pg_isready','-h','127.0.0.1','-U','postgres'],capture_output=True).returncode==0:break
   time.sleep(.1)
  else:raise AssertionError('Local PostgreSQL unavailable')
  sql((ROOT/'tests/database_fixture.sql').read_text())
  sql("alter table auth.users add column email text,add column email_confirmed_at timestamptz,add column created_at timestamptz not null default now(),add column raw_user_meta_data jsonb default '{}'::jsonb;")
  for f in ['001_secure_access.sql','002_survey_purchases.sql']:sql((ROOT/'supabase'/f).read_text())
  metadata=json.loads(sql('select '+builder.metadata_expression()+';'))
  reference={'origin':'SOURCE MODEL ONLY, isolated PostgreSQL17 fixture + pinned001/002; NOT production metadata or grant recommendations',
  'policies':metadata['policies'],'required_columns':[{k:c[k] for k in ['table','column','type']} for c in metadata['columns']],
  'constraint_index_model':{'constraints':metadata['constraints'],'indexes':metadata['indexes']}}
  # Preparation-only explicit opt-in writes reference + review scripts; never runs in CI.
  if '--prepare-reference' in sys.argv:
   (OUT/'reference_001_002.json').write_text(json.dumps(reference,indent=2)+'\n')
   for path,source in builder.generate().items():(OUT/path).write_text(source)
  assert json.loads((OUT/'reference_001_002.json').read_text())==reference
  pre=json.loads(sql((OUT/'00_preflight_readonly.sql').read_text()))
  assert not pre['new_objects'] and not pre['new_function_overloads'] and not pre['reserved_auth_triggers']
  existing=[f for f in pre['reviewed_function_comparison'] if f['exists']]
  assert len(existing)==5 and all(f['body_matches_reviewed_source'] for f in existing)
  fingerprint=pre['baseline_sha256']
  # Existing fake records/credits must survive. No real customer/accounts in this container.
  uid=str(uuid.uuid4());pid=str(uuid.uuid4())
  sql(f"insert into auth.users(id,email)values('{uid}','existing@example.invalid'); insert into public.properties(id,user_id,address,postcode)values('{pid}','{uid}','DUMMY','ZZ1');set role service_role;select public.record_survey_purchase('cs_live_localdummy','pi_localdummy','{uid}',600,'gbp',true);")
  snapshot=sql("select jsonb_build_object('p',(select jsonb_agg(to_jsonb(t)) from properties t),'free',(select jsonb_agg(to_jsonb(t)) from survey_free_allocations t),'credits',(select jsonb_agg(to_jsonb(t)) from survey_credit_purchases t));")
  def approved(text,digest=fingerprint):
   return text.replace("urbanfold.release_ack='NOT_APPROVED'","urbanfold.release_ack='APPROVED "+builder.PROJECT+' '+builder.PIN+"'").replace("urbanfold.reviewed_baseline_sha256='REVIEW_REQUIRED'","urbanfold.reviewed_baseline_sha256='"+digest+"'")
  for file in ['10_install_003_fresh.sql','20_install_004_fresh.sql']:
   source=(OUT/file).read_text()
   sql(source,'No production execution approval')
   sql(approved(source,'0'*64),'baseline fingerprint missing or changed')
   if file.startswith('10'):
    sql("create policy unexpected_allow on properties for select using(true);")
    altered=json.loads(sql((OUT/'00_preflight_readonly.sql').read_text()))
    sql(approved(source,altered['baseline_sha256']),'policy mismatch')
    sql('drop policy unexpected_allow on properties;')
    # Even an operator-approved baseline cannot allow inherited client reads
    # on new server-only outboxes: fail inside transaction before commit.
    sql('create role release_untrusted nologin;grant release_untrusted to authenticated;alter default privileges for role postgres in schema public grant select on tables to release_untrusted;')
    altered=json.loads(sql((OUT/'00_preflight_readonly.sql').read_text()))
    sql(approved(source,altered['baseline_sha256']),'New table RLS/client access checks failed')
    assert sql("select to_regclass('public.survey_notification_events') is null;")=='t'
    sql('alter default privileges for role postgres in schema public revoke select on tables from release_untrusted;revoke release_untrusted from authenticated;drop role release_untrusted;')
    sql('grant execute on function public.record_survey_purchase(text,text,uuid,integer,text,boolean) to authenticated;')
    altered=json.loads(sql((OUT/'00_preflight_readonly.sql').read_text()))
    sql(approved(source,altered['baseline_sha256']),'Existing002 function source/ACL differs')
    sql('revoke execute on function public.record_survey_purchase(text,text,uuid,integer,text,boolean) from authenticated;')
    sql("comment on table public.properties is 'Urbanfold-Survey-Staging reconstructed baseline; prepared 2026-11-03; never production.';")
    sql(approved(source),'Staging database rejected')
    sql('comment on table public.properties is null;')
   sql(approved(source))
   sql(approved(source),'Fresh-only target objects already exist')
  after=json.loads(sql((OUT/'30_postinstall_readonly.sql').read_text()))
  assert after['baseline_sha256']==fingerprint
  assert len(after['functions'])==14 and all(f['body_matches_reviewed_source'] for f in after['functions'])
  assert len(after['new_tables'])==4 and all(t['rls'] and not t['anon_any'] and not t['authenticated_write'] for t in after['new_tables'])
  assert len(after['auth_triggers'])==2 and all(t['enabled']=='O' for t in after['auth_triggers'])
  assert snapshot==sql("select jsonb_build_object('p',(select jsonb_agg(to_jsonb(t)) from properties t),'free',(select jsonb_agg(to_jsonb(t)) from survey_free_allocations t),'credits',(select jsonb_agg(to_jsonb(t)) from survey_credit_purchases t));")
  # Review rollback and scheduler in this OFFLINE DB only. No real cron/net extensions.
  for action in ['disable','enable']:
   file='40_disable_auth_recording.sql' if action=='disable' else '41_enable_auth_recording.sql'
   source=(OUT/file).read_text()
   sql(source,'No production execution approval')
   source=approved(source).replace("urbanfold.auth_recording_action='NOT_APPROVED'", "urbanfold.auth_recording_action='APPROVED "+action.upper()+" REGISTRATION RECORDING'")
   sql(source)
   assert sql("select count(*) from pg_trigger where tgrelid='auth.users'::regclass and tgname in('urbanfold_auth_signup','urbanfold_auth_first_confirmation') and tgenabled='"+('D' if action=='disable' else 'O')+"';")=='2'
  schedule=(OUT/'50_registration_schedule_review.sql').read_text()
  sql(schedule,'No production execution approval')
  schedule=approved(schedule).replace("urbanfold.schedule_ack='NOT_APPROVED'", "urbanfold.schedule_ack='APPROVED PRODUCTION BREVO DELIVERY AND SCHEDULER'")
  sql(schedule,'Review Cron, pg_net and Vault')
  sql("""create schema cron;create schema net;create schema vault;
   create table cron.job(jobid bigserial primary key,jobname text,schedule text,command text,active boolean default true);
   create table vault.decrypted_secrets(name text primary key,decrypted_secret text);
   create function net.http_post(text,jsonb,jsonb,jsonb,integer)returns bigint language plpgsql as $$begin raise exception 'HTTP STUB MUST NEVER EXECUTE';end $$;
   create function cron.schedule(jobname text,schedule text,command text)returns bigint language plpgsql as $$declare n bigint;begin insert into cron.job(jobname,schedule,command)values($1,$2,$3)returning jobid into n;return n;end $$;
  """)
  sql(schedule,'Vault settings missing')
  sql("insert into vault.decrypted_secrets values('urbanfold_production_registration_dispatch',repeat('x',40)),('urbanfold_production_public_key',repeat('x',40));")
  sql(schedule)
  sql(schedule,'existing registration schedule')
  job=sql((OUT/'51_schedule_verify_readonly.sql').read_text())
  assert 'urbanfold-production-verified-registration' in job and job.count('|t')==4,job
  assert snapshot==sql("select jsonb_build_object('p',(select jsonb_agg(to_jsonb(t)) from properties t),'free',(select jsonb_agg(to_jsonb(t)) from survey_free_allocations t),'credits',(select jsonb_agg(to_jsonb(t)) from survey_credit_purchases t));")
  print('PASS guarded exact-trigger pause/resume and scheduler review SQL parsing/extension/Vault/duplicate gates with inert LOCAL cron/net stubs; HTTP stub never executed, no background job runner')
  print('PASS offline reference/preflight parsing, pinned source body hashes, missing-approval/fingerprint/staging/wrong-policy/inherited-default-grant/billing-RPC-ACL/repeated-install denial, fresh003 then004 with inside-transaction security checks, unchanged baseline and existing dummy surveys/free allocation/600-pence purchase; no cloud/database/provider access')
 finally:subprocess.run(['docker','rm','-f',name],capture_output=True)
if __name__=='__main__':main()
