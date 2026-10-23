"""Exercise the real allowance/payment SQL in a disposable, offline database."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import json
import subprocess
import time
import uuid
from test_database_policies import IMAGE

ROOT = Path(__file__).resolve().parents[1]

def main():
    name = 'urbanfold-billing-test-' + uuid.uuid4().hex[:10]
    def sql(statement, error=None):
        result = subprocess.run(['docker','exec','-i',name,'psql','-X','-q','-t','-A','-v','ON_ERROR_STOP=1','-U','postgres'],input=statement,text=True,capture_output=True)
        if error:
            assert result.returncode and error in result.stderr, (error,result.stdout,result.stderr)
        else:
            assert result.returncode == 0, result.stderr
        return result.stdout.strip()
    def user(identity, body, admin=False):
        claims = json.dumps({'sub':identity,'role':'authenticated','email':'urbanfolduk@gmail.com' if admin else 'client@example.test'})
        return f"set role authenticated; set request.jwt.claims = '{claims}'; {body}"
    def prop(identity, pid=None, address='One Street'):
        pid = pid or str(uuid.uuid4())
        return f"insert into properties(id,user_id,address,postcode) values('{pid}','{identity}','{address}','AB1 2CD')"
    def purchase(identity, suffix, live=True):
        return f"set role service_role; select public.record_survey_purchase('cs_{'live' if live else 'test'}_{suffix}','pi_{suffix}','{identity}',600,'gbp',{str(live).lower()});"
    try:
        subprocess.run(['docker','run','--rm','-d','--name',name,'--network','none','-e','POSTGRES_HOST_AUTH_METHOD=trust',IMAGE],check=True,capture_output=True)
        for _ in range(100):
            if subprocess.run(['docker','exec',name,'pg_isready','-h','127.0.0.1','-U','postgres'],capture_output=True).returncode == 0: break
            time.sleep(.1)
        else: raise AssertionError('PostgreSQL did not start')
        sql(ROOT.joinpath('tests/database_fixture.sql').read_text())
        sql(ROOT.joinpath('supabase/001_secure_access.sql').read_text())
        owner, other, admin, legacy, racer, rollback = [str(uuid.uuid4()) for _ in range(6)]
        sql('insert into auth.users values ' + ','.join(f"('{x}')" for x in [owner,other,admin,legacy,racer,rollback]) + ';')
        sql(prop(legacy)+';'+prop(legacy)+';')
        migration=ROOT.joinpath('supabase/002_survey_purchases.sql').read_text()
        sql(migration)
        sql(migration)
        assert sql(user(legacy,'select count(*) from properties;')) == '2'
        sql(user(legacy,prop(legacy)+';'),'URBANFOLD_SURVEY_LIMIT')
        assert json.loads(sql(user(owner,'select get_survey_allowance();')))['free_available']
        first=str(uuid.uuid4())
        sql(user(owner,prop(owner,first)+';'))
        sql(user(owner,prop(owner)+';'),'URBANFOLD_SURVEY_LIMIT')
        # HTTP retries use the same UUID and must not spend a second credit.
        sql(user(owner,prop(owner,first)+" on conflict(id) do update set notes='retry';"))
        assert sql(user(owner,'select count(*) from properties;')) == '1'
        sql(user(admin,prop(admin)+';'+prop(admin)+';',True))
        assert json.loads(sql(user(admin,'select get_survey_allowance();',True)))['unlimited']
        print('PASS lifetime free limit, existing survey preservation, admin exemption, idempotent retries')

        sql(user(owner,"select record_survey_purchase('cs_live_forged','pi_forged',auth.uid(),600,'gbp',true);"),'permission denied')
        sql(user(owner,"insert into survey_credit_purchases values ('cs_live_fake','pi_fake',auth.uid(),600,'gbp',true,now(),null,null);"),'permission denied')
        sql('set role anon; select get_survey_allowance();','permission denied')
        sql(f"set role service_role; select record_survey_purchase('cs_live_wrong','pi_wrong','{owner}',1,'gbp',true);",'Invalid survey payment')
        sql(purchase(owner,'sandbox',False))
        sql(user(owner,prop(owner)+';'),'URBANFOLD_SURVEY_LIMIT')
        sql(purchase(owner,'paidone'))
        sql(purchase(owner,'paidone'))
        sql(f"set role service_role; select record_survey_purchase('cs_live_paidone','pi_paidone','{other}',600,'gbp',true);",'Payment identity does not match')
        assert json.loads(sql(user(owner,'select get_survey_allowance();')))['paid_credits']==1
        assert sql(user(other,'select count(*) from survey_credit_purchases;'))=='0'
        second=str(uuid.uuid4())
        sql(user(owner,prop(owner,second)+';'))
        sql(user(owner,prop(owner)+';'),'URBANFOLD_SURVEY_LIMIT')
        assert json.loads(sql(user(owner,'select get_survey_allowance();')))['paid_credits']==0
        print('PASS service-only verified payment writes, exact £6, duplicate webhook handling, test/live separation, single redemption')

        sql(purchase(owner,'refund'))
        sql("set role service_role; select revoke_survey_purchase('pi_refund','refund'); select revoke_survey_purchase('pi_refund','refund retry');")
        sql(user(owner,prop(owner)+';'),'URBANFOLD_SURVEY_LIMIT')
        sql("set role service_role; select revoke_survey_purchase('pi_early','refund before checkout webhook');")
        sql(purchase(owner,'early'))
        sql(user(owner,prop(owner)+';'),'URBANFOLD_SURVEY_LIMIT')
        sql("set role service_role; select revoke_survey_purchase('pi_paidone','dispute after use');")
        assert sql(user(owner,'select count(*) from properties;'))=='2'
        print('PASS refunds/disputes revoke unused credit, out-of-order events stay revoked, existing paid surveys preserved')

        sql(user(owner,f"update properties set last_submitted_at=now() where id='{first}';"))
        sql(user(owner,f"update properties set address='Different Street' where id='{first}';"),'URBANFOLD_ADDRESS_LOCKED')
        sql(user(owner,f"update properties set last_submitted_at=null,address_locked=false where id='{first}';"))
        sql(user(owner,f"update properties set postcode='XY9 9ZZ' where id='{first}';"),'URBANFOLD_ADDRESS_LOCKED')
        sql(user(owner,f"update properties set address='  ONE   Street ',postcode='ab12cd',notes='editable' where id='{first}';"))
        sql(user(admin,f"update properties set address='Corrected Street' where id='{first}';",True))
        # An unsuccessful insert rolls back its allocation; a client can retry safely.
        bad=prop(rollback).replace("'AB1 2CD'",'null')+';'
        sql(user(rollback,bad),'not-null constraint')
        assert json.loads(sql(user(rollback,'select get_survey_allowance();')))['free_available']
        sql(user(rollback,prop(rollback)+';'))
        sql(purchase(rollback,'rollbackpaid'))
        sql(user(rollback,bad),'not-null constraint')
        assert json.loads(sql(user(rollback,'select get_survey_allowance();')))['paid_credits']==1
        sql(user(rollback,prop(rollback)+';'))
        print('PASS submitted addresses remain locked, admin corrections, failed insert does not lose free allocation or paid credit')

        def race(_):
            statement=user(racer,prop(racer)+';')
            result=subprocess.run(['docker','exec','-i',name,'psql','-X','-q','-v','ON_ERROR_STOP=1','-U','postgres'],input=statement,text=True,capture_output=True)
            return result
        with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(race,range(2)))
        assert sorted(r.returncode==0 for r in results)==[False,True],[(r.returncode,r.stderr) for r in results]
        assert 'URBANFOLD_SURVEY_LIMIT' in next(r.stderr for r in results if r.returncode)
        sql(purchase(racer,'concurrentpaid'))
        with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(race,range(2)))
        assert sorted(r.returncode==0 for r in results)==[False,True],[(r.returncode,r.stderr) for r in results]
        assert sql(user(racer,'select count(*) from properties;'))=='2'
        sql(migration)
        assert sql(user(owner,'select count(*) from properties;'))=='2'
        assert sql(user(owner,'select count(*) from survey_credit_purchases;'))=='4'
        sql(user(owner,prop(owner)+';'),'URBANFOLD_SURVEY_LIMIT')
        print('PASS simultaneous requests cannot double-spend free allowance; reapplying migration preserves payment history')
    finally:
        subprocess.run(['docker','rm','-f',name],capture_output=True)

if __name__=='__main__': main()
