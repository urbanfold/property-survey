"""Execute exact03/05 logic ONLY in a disposable network-none PostgreSQL17 container.
No host SQL connection, HTTP client, Supabase credentials or real users are used.
Production originals are never written. Only four approval parameter values vary.
"""
from pathlib import Path
import difflib,hashlib,importlib.util,json,os,shutil,subprocess,tempfile,time,uuid

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'audits/2026-11-07/acl-runtime-rehearsal'
PIN='061bff14b887fa4ba03c785ccf2c82cf84a9158e'
IMAGE='postgres:17-alpine@sha256:eee6c6e1b0894fa4fe0075eb054af9fd1cf39a35321c2d4110626cfe506411fb'
DB='urbanfold_acl_rehearsal'
PROD_HASHES={'03_revoke_excess_table_privileges.sql':'625322c2f680faf0d0c8d2767519b71ab39fef0ed49999d7107bc99bfa5728cf','05_restore_exact_previous_privileges.sql':'a19ad6bedf6fc9f5e253ceff9c1682f471ae45bbd6be11f072f110c0d2e1f5c8'}
spec=importlib.util.spec_from_file_location('acl_review',ROOT/'scripts/build_table_acl_review.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
sha=lambda data:hashlib.sha256(data).hexdigest()

class Rehearsal:
 def __init__(self):
  self.name='urbanfold-acl-rehearsal-'+uuid.uuid4().hex[:10]
  self.cfg=tempfile.TemporaryDirectory(prefix='urbanfold-empty-docker-config-')
  self.env={'PATH':os.environ.get('PATH',os.defpath),'DOCKER_CONFIG':self.cfg.name}
  self.cli=[shutil.which('docker') or 'docker','--host','unix:///var/run/docker.sock']
  self.checks=[];self.params=[];self.started=False;self.isolation={};self.version=None
 def docker(self,args,**kw):
  return subprocess.run(self.cli+args,env=self.env,text=True,capture_output=True,timeout=kw.pop('timeout',60),**kw)
 def sql(self,text,error=None):
  p=self.docker(['exec','-i',self.name,'psql','-X','-q','-t','-A','-v','ON_ERROR_STOP=1','-v','VERBOSITY=verbose','-h','/var/run/postgresql','-U','postgres','-d',DB],input=text)
  if error:
   assert p.returncode and error in p.stderr,{'expected_error':error,'returncode':p.returncode,'stderr':p.stderr}
   return p.stderr.strip()
  assert p.returncode==0,p.stderr
  return p.stdout.strip()
 def record(self,name,**details):
  row={'test':name,'passed':True,**details};self.checks.append(row);print(json.dumps(row),flush=True)
 def start(self):
  if self.docker(['version','--format','{{.Server.Version}}']).returncode:raise RuntimeError('LOCAL_ENV_UNAVAILABLE: local Docker socket')
  image=self.docker(['image','inspect',IMAGE,'--format','{{.Id}}'])
  if image.returncode:raise RuntimeError('LOCAL_ENV_UNAVAILABLE: pinned image not cached; no pull attempted')
  p=self.docker(['run','--pull','never','--rm','-d','--name',self.name,'--network','none','--memory','512m','--cpus','1','--pids-limit','128','--tmpfs','/var/lib/postgresql/data','-e','POSTGRES_HOST_AUTH_METHOD=trust','-e','POSTGRES_DB='+DB,IMAGE])
  assert p.returncode==0,p.stderr;self.started=True
  inspection=json.loads(self.docker(['inspect',self.name]).stdout)[0]
  assert inspection['HostConfig']['NetworkMode']=='none'
  assert not inspection['HostConfig'].get('PortBindings')
  assert not any(m['Type'] in ['bind','volume'] for m in inspection['Mounts'])
  assert not any(k.startswith(('SUPABASE','URBANFOLD','STRIPE','BREVO')) for k in (e.split('=',1)[0] for e in inspection['Config']['Env']))
  self.isolation={'docker_endpoint':'unix:///var/run/docker.sock','network':'none','published_ports':False,'host_bind_or_volume_mounts':False,'data_mount':'tmpfs','image':IMAGE,'cached_image_id':image.stdout.strip(),'pull_policy':'never','database':DB,'host_secrets_forwarded':False}
  # pg_isready alone can report the temporary init server as ready before
  # POSTGRES_DB exists. Wait for init completion AND a real SELECT on final DB.
  for _ in range(150):
   logs=self.docker(['logs',self.name])
   if 'PostgreSQL init process complete; ready for start up.' in logs.stdout+logs.stderr:
    ready=self.docker(['exec',self.name,'psql','-X','-q','-t','-A','-h','/var/run/postgresql','-U','postgres','-d',DB,'-c','select 1;'])
    if ready.returncode==0 and ready.stdout.strip()=='1':break
   time.sleep(.1)
  else:raise AssertionError('Local PostgreSQL final dummy database did not become ready')
  identity=json.loads(self.sql("select jsonb_build_object('database',current_database(),'user',current_user,'server',current_setting('server_version_num'),'unix_socket',inet_server_addr() is null);"))
  assert identity['database']==DB and identity['user']=='postgres' and identity['unix_socket'] and int(identity['server'])>=170000
  self.version=self.sql('select version();');self.record('isolated_local_postgresql_available',**identity)
 def stop(self):
  if self.started:
   p=self.docker(['rm','--force','--volumes',self.name]);assert p.returncode==0,p.stderr
  self.cfg.cleanup()
 def hashes(self):
  return json.loads(self.sql('select jsonb_build_object(\'baseline\','+b.digest(b.b.metadata_expression())+',\'acl\','+b.digest(b.snapshot())+');'))
 def snapshot(self):return json.loads(self.sql('select '+b.snapshot()+';'))
 def data(self):
  tables=['public.'+t for t in b.TABLES]+['public.survey_free_allocations','public.survey_credit_purchases','public.survey_credit_revocations','storage.objects','storage.buckets','auth.users']
  bits=[]
  for t in tables:bits += [b.lit(t),f"(select coalesce(jsonb_agg(to_jsonb(t) order by to_jsonb(t)::text),'[]'::jsonb) from {t} t)"]
  return self.sql('select '+b.digest('jsonb_build_object('+','.join(bits)+')')+';')
 def effective(self):return json.loads(self.sql('select ('+b.effective_query()+');'))
 def parameterize(self,original,baseline,acl,action,label,ack=None):
  assert baseline not in ['10fa3ce6272648b31c662735e549b2e78b032a63cceb6e5f1d862f5d5052e4f6','fd7f49766854f09d849adee619f02054612ee1014aa63cbf6bfe3a53b7e6a861']
  assert acl not in ['10fa3ce6272648b31c662735e549b2e78b032a63cceb6e5f1d862f5d5052e4f6','fd7f49766854f09d849adee619f02054612ee1014aa63cbf6bfe3a53b7e6a861']
  changes={"urbanfold.acl_ack='NOT_APPROVED'":"urbanfold.acl_ack="+b.lit(ack or 'APPROVED '+b.PROJECT+' TABLE ACL REVIEW '+b.PIN),
  "urbanfold.acl_action='NOT_APPROVED'":"urbanfold.acl_action="+b.lit(action),
  "urbanfold.reviewed_baseline_sha256='REVIEW_REQUIRED'":"urbanfold.reviewed_baseline_sha256="+b.lit(baseline),
  "urbanfold.original_acl_sha256='REVIEW_REQUIRED'":"urbanfold.original_acl_sha256="+b.lit(acl)}
  copy=original
  for old,new in changes.items():assert copy.count(old)==1;copy=copy.replace(old,new,1)
  reverse=copy
  for old,new in changes.items():assert reverse.count(new)==1;reverse=reverse.replace(new,old,1)
  assert reverse==original
  self.params.append({'case':label,'only_four_parameter_literals_changed':True,'original_sha256':sha(original.encode()),'copy_sha256':sha(copy.encode()),'replacement_parameters':changes,'diff':list(difflib.unified_diff(original.splitlines(),copy.splitlines(),fromfile='UNCHANGED_REVIEW_SOURCE',tofile='ISOLATED_LOCAL_TEST_COPY',lineterm=''))})
  return copy

def setup(r):
 original=(ROOT/'tests/database_fixture.sql').read_text();fixture=original
 assert fixture.count('references auth.users(id),')==1
 fixture=fixture.replace('references auth.users(id),','references auth.users(id) on delete cascade,',1)
 assert fixture.count('references properties(id)')==5 and fixture.count('references rooms(id)')==1
 fixture=fixture.replace('references properties(id)','references public.properties(id) on delete cascade').replace('references rooms(id)','references public.rooms(id) on delete cascade')
 assert fixture.count('width numeric, length numeric')==1
 fixture=fixture.replace('width numeric, length numeric','width numeric(5,2), length numeric(5,2)',1)
 guard=f"do $$begin if current_database()<>{b.lit(DB)} or inet_server_addr() is not null then raise exception 'LOCAL REHEARSAL DATABASE ONLY';end if;end $$;\n"
 extra="""
-- LOCAL TEST DEFAULTS ONLY: model broad defaults so preservation is exercised.
alter default privileges for role postgres in schema public grant all on tables to anon,authenticated,service_role;
alter default privileges for role postgres in schema public grant execute on functions to anon,authenticated,service_role;
alter default privileges for role postgres in schema public grant all on sequences to anon,authenticated,service_role;
"""
 targets=', '.join('public.'+t for t in b.TABLES)
 tail=f"""
grant all on table {targets} to anon,authenticated,service_role;
grant usage on schema auth,storage,public to service_role;
grant all on storage.objects,storage.buckets to service_role;
create role acl_rehearsal_probe nologin;
create role acl_rehearsal_delegate nologin;
"""
 seed="""
insert into auth.users(id)values('e0000000-0000-4000-8000-000000000001'),('e0000000-0000-4000-8000-000000000002');
insert into public.properties(id,user_id,address,postcode,client_email)values
 ('e1000000-0000-4000-8000-000000000001','e0000000-0000-4000-8000-000000000001','DUMMY HOUSE A','ZZ1','a@unit.example.invalid'),
 ('e1000000-0000-4000-8000-000000000002','e0000000-0000-4000-8000-000000000002','DUMMY HOUSE B','ZZ2','b@unit.example.invalid');
insert into public.extensions(id,property_id,width,length)values('e2000000-0000-4000-8000-000000000001','e1000000-0000-4000-8000-000000000001',3.25,4.50);
insert into public.rooms(id,property_id,room_name,dimensions)values('e3000000-0000-4000-8000-000000000001','e1000000-0000-4000-8000-000000000001','DUMMY ROOM','{"l":"3.25","w":"4.50","h":"2.40"}');
insert into public.exterior_photos(property_id,elevation_type,photo_url)values('e1000000-0000-4000-8000-000000000001','front','storage://exterior-photos/e1000000-0000-4000-8000-000000000001/dummy.png');
insert into public.extension_photos(property_id,photo_url)values('e1000000-0000-4000-8000-000000000001','storage://exterior-photos/e1000000-0000-4000-8000-000000000001/dummy-extension.png');
insert into public.sketch_photos(property_id,photo_url)values('e1000000-0000-4000-8000-000000000001','storage://sketch-photos/e1000000-0000-4000-8000-000000000001/dummy.png');
insert into public.room_photos(room_id,photo_url)values('e3000000-0000-4000-8000-000000000001','storage://room-photos/e1000000-0000-4000-8000-000000000001/dummy.png');
insert into storage.objects(bucket_id,name)values('room-photos','e1000000-0000-4000-8000-000000000001/dummy.png');
insert into public.survey_free_allocations(user_id,property_id)values('e0000000-0000-4000-8000-000000000001','e1000000-0000-4000-8000-000000000001');
insert into public.survey_credit_purchases(checkout_session_id,payment_intent_id,user_id,amount_total,currency,live_mode)
 values('cs_live_LOCALDUMMY','pi_LOCALDUMMY','e0000000-0000-4000-8000-000000000001',600,'gbp',true);
"""
 text=guard+fixture+extra+(ROOT/'supabase/001_secure_access.sql').read_text()+(ROOT/'supabase/002_survey_purchases.sql').read_text()+tail+seed
 (OUT/'LOCAL_ONLY_fixture.sql').write_text('-- GENERATED DUMMY FIXTURE; NEVER EXECUTE ON SUPABASE\n'+text)
 r.sql(text)
 r.record('dummy_fixture_ready',original_fixture_sha256=sha(original.encode()),local_fixture_sha256=sha(text.encode()),foreign_keys_valid=r.sql("select count(*) from pg_constraint where contype='f' and convalidated and confdeltype='c' and connamespace='public'::regnamespace;"))

def run(r):
 original03=(b.OUT/'03_revoke_excess_table_privileges.sql').read_text();original05=(b.OUT/'05_restore_exact_previous_privileges.sql').read_text()
 for name,expected in PROD_HASHES.items():assert sha((b.OUT/name).read_bytes())==expected
 setup(r)
 baseline=r.hashes();before=r.snapshot();data=r.data()
 assert len(r.effective())==56 and all(x['allowed'] for x in r.effective())
 assert all(a['superuser'] is False and a['bypass_rls'] is False and a['can_login'] is False for a in before['api_roles'])
 apply=r.parameterize(original03,baseline['baseline'],baseline['acl'],'APPROVED REMOVE56 EXCESS PRIVILEGES','normal03')
 restore=r.parameterize(original05,baseline['baseline'],baseline['acl'],'APPROVED RESTORE56 ORIGINAL PRIVILEGES','normal05')
 def rejected(label,source,error):
  pre=r.snapshot();schema=r.hashes()['baseline'];rows=r.data()
  detail=r.sql(source,error)
  assert r.snapshot()==pre and r.hashes()['baseline']==schema and r.data()==rows
  r.record(label,expected_error=error,sqlstate=next((line.split(':')[1].strip() for line in detail.splitlines() if line.startswith('ERROR:')),None))
 rejected('unapproved03_rejected',original03,'Separate permission-change approval required')
 rejected('wrong_baseline_rejected',r.parameterize(original03,'0'*64,baseline['acl'],'APPROVED REMOVE56 EXCESS PRIVILEGES','wrong_baseline'),'Reviewed baseline missing/changed')
 rejected('wrong_acl_digest_rejected',r.parameterize(original03,baseline['baseline'],'0'*64,'APPROVED REMOVE56 EXCESS PRIVILEGES','wrong_acl'),'Original reviewed ACL fingerprint missing/changed')
 rejected('wrong_action_rejected',r.parameterize(original03,baseline['baseline'],baseline['acl'],'APPROVED RESTORE56 ORIGINAL PRIVILEGES','wrong_action'),'Specific removal approval required')
 r.sql("create table public.acl_restrict_probe(id integer primary key);insert into public.acl_restrict_probe values(1);grant trigger on public.acl_restrict_probe to anon with grant option;set role anon;grant trigger on public.acl_restrict_probe to acl_rehearsal_delegate;reset role;")
 probe=r.sql("select relacl::text from pg_class where oid='public.acl_restrict_probe'::regclass;")
 message=r.sql('revoke trigger on public.acl_restrict_probe from anon restrict;','dependent privileges exist')
 assert '2BP01' in message and probe==r.sql("select relacl::text from pg_class where oid='public.acl_restrict_probe'::regclass;")
 assert r.sql('select count(*) from public.acl_restrict_probe;')=='1'
 r.record('postgres_restrict_dependency_semantics',sqlstate='2BP01',scope='separate local probe table; exact03 supported state forbids delegated target grants')
 r.sql('grant trigger on public.properties to anon with grant option;set role anon;grant trigger on public.properties to acl_rehearsal_delegate;reset role;')
 changed=r.hashes()
 rejected('exact03_delegated_target_state_guard',r.parameterize(original03,changed['baseline'],changed['acl'],'APPROVED REMOVE56 EXCESS PRIVILEGES','delegated_state'),'Need56 exact direct owner-issued non-grantable entries')
 r.sql('set role anon;revoke trigger on public.properties from acl_rehearsal_delegate restrict;reset role;revoke grant option for trigger on public.properties from anon restrict;')
 assert r.hashes()==baseline and r.snapshot()==before
 # Artificial LOCAL watcher intentionally changes a target ACL after REVOKE.
 # It is not a Supabase/PostgREST watcher and has no external/network behaviour.
 r.sql("create function public.acl_rehearsal_tamper() returns event_trigger language plpgsql set search_path='' as $$begin grant select on public.properties to acl_rehearsal_probe;end $$;create event trigger acl_rehearsal_tamper on ddl_command_end when tag in('REVOKE') execute function public.acl_rehearsal_tamper();")
 changed=r.hashes()
 rejected('post_revoke_invariant_failure_rolls_back_all',r.parameterize(original03,changed['baseline'],changed['acl'],'APPROVED REMOVE56 EXCESS PRIVILEGES','synthetic_postcheck_failure'),'Unrelated schema/grants/roles/CRUD/columns/Storage/credit ACL changed')
 assert all(x['allowed'] for x in r.effective())
 assert r.sql("select has_table_privilege('acl_rehearsal_probe','public.properties','SELECT');")=='f'
 r.sql('drop event trigger acl_rehearsal_tamper;drop function public.acl_rehearsal_tamper();')
 assert r.hashes()==baseline
 r.sql(apply)
 after=r.snapshot();post=r.hashes()
 assert len(r.effective())==56 and not any(x['allowed'] for x in r.effective())
 assert post['baseline']==baseline['baseline'] and post['acl']!=baseline['acl']
 assert r.data()==data
 for x,y in zip(before['tables'],after['tables']):
  assert x['api_crud']==y['api_crud'] and x['column_acls']==y['column_acls']
  assert len(x['acl'])-len(y['acl'])==8
  assert [a for a in x['acl'] if not(a['grantee'] in b.ROLES and a['privilege'] in b.PRIVS)]==y['acl']
 assert before['untouched_tables']==after['untouched_tables'] and before['api_roles']==after['api_roles']
 r.record('exact03_success_removes56_and_preserves_state',original_baseline=baseline['baseline'],original_acl=baseline['acl'],corrected_acl=post['acl'],dummy_data_sha256=data)
 rejected('repeat03_same_parameters_rejected',apply,'Original reviewed ACL fingerprint missing/changed')
 rejected('unapproved05_rejected',original05,'Separate permission-change approval required')
 rejected('wrong_original_rollback_digest_rejected',r.parameterize(original05,baseline['baseline'],'0'*64,'APPROVED RESTORE56 ORIGINAL PRIVILEGES','wrong_rollback_hash'),'Inverse snapshot does not match saved original ACL')
 r.sql('grant select on storage.objects to acl_rehearsal_probe;')
 rejected('rollback_does_not_overwrite_unrelated_storage_acl',restore,'Inverse snapshot does not match saved original ACL')
 r.sql('revoke select on storage.objects from acl_rehearsal_probe restrict;')
 assert r.hashes()==post
 # Real local RLS/trigger DML, with synthetic claims and an explicit rollback.
 claims=json.dumps({'sub':'e0000000-0000-4000-8000-000000000001','role':'authenticated','email':'a@unit.example.invalid'})
 r.sql("begin;set local role authenticated;select set_config('request.jwt.claims',"+b.lit(claims)+",true);update properties set notes='LOCAL CRUD CHECK' where id='e1000000-0000-4000-8000-000000000001';insert into properties(id,user_id,address,postcode)values('e1000000-0000-4000-8000-000000000003','e0000000-0000-4000-8000-000000000001','LOCAL NEW PROPERTY','ZZ3');insert into rooms(id,property_id,room_name)values('e3000000-0000-4000-8000-000000000003','e1000000-0000-4000-8000-000000000003','LOCAL NEW ROOM');insert into room_photos(room_id,photo_url)values('e3000000-0000-4000-8000-000000000003','storage://room-photos/local-dummy');delete from room_photos where room_id='e3000000-0000-4000-8000-000000000003';rollback;")
 assert r.data()==data and r.hashes()==post
 assert r.sql('set role anon;select count(*) from properties;')=='0'
 assert r.sql("set role authenticated;select set_config('request.jwt.claims',"+b.lit(claims)+",false);select count(*) from properties;").splitlines()[-1]=='1'
 r.record('normal_authenticated_crud_rls_and_credit_trigger_preserved',scope='local synthetic claims only; DML rolled back, dummy data and credit ledger unchanged')
 r.sql(restore)
 assert r.snapshot()==before and r.hashes()==baseline and r.data()==data
 assert len(r.effective())==56 and all(x['allowed'] for x in r.effective())
 r.record('exact05_restores_original_grants_and_all_snapshots')
 rejected('repeat05_rejected',restore,'Rollback needs the fully corrected state')
 for name,expected in PROD_HASHES.items():assert sha((b.OUT/name).read_bytes())==expected
 r.record('production_originals_byte_identical_after_rehearsal',**PROD_HASHES)


def main():
 OUT.mkdir(parents=True,exist_ok=True);r=Rehearsal();status='FAILED';failure=None
 try:r.start();run(r);status='PASSED'
 except Exception as e:
  failure=str(e);print('REHEARSAL STOP:',failure,flush=True)
  if failure.startswith('LOCAL_ENV_UNAVAILABLE:'):status='NOT_RUN_ENV_UNAVAILABLE'
 finally:
  try:r.stop()
  except Exception as e:failure=(failure or '')+'; local cleanup: '+str(e);status='FAILED'
  (OUT/'parameterization.json').write_text(json.dumps(r.params,indent=2)+'\n')
  (OUT/'results.json').write_text(json.dumps({'status':status,'source_commit':PIN,'original_sql_sha256':PROD_HASHES,'isolation':r.isolation,'postgres_version':r.version,'checks':r.checks,'failure':failure,'only_local_dummy_database_sql_executed':True if r.started else False,'production_or_staging_connections':0,'real_customer_data_or_secrets_used':False,'watcher_full_body_review':'OPEN; native managed watcher bodies not supplied or executed','production_originals_modified':False,'local_container_removed':True if r.started else None},indent=2)+'\n')
 if status=='FAILED':raise SystemExit(1)
 if status=='NOT_RUN_ENV_UNAVAILABLE':print('Procedure prepared; no unsafe fallback attempted',flush=True)
if __name__=='__main__':main()
