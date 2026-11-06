from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import subprocess,json,time
root=Path(__file__).resolve().parents[3];out=root/'audits/2026-11-06/registration-implementation/tests';out.mkdir(exist_ok=True)
cases=[('syntax',['node','--input-type=module','--check']),('dashboard',['python','scripts/build_dashboard_functions.py','--check']),('billing',['node','--test','tests/test_billing_handlers.mjs']),('notifications',['node','--test','tests/test_notification_handlers.mjs']),('registration-handlers',['node','--test','tests/test_registration_handlers.mjs']),('registration-sql',['python','tests/test_registration_notifications.py']),('newsletter-ui',['python','tests/test_newsletter_ui.py']),('session-security',['python','tests/test_session_security.py']),('session-recovery',['python','tests/test_session_recovery.py']),('survey-flow',['python','tests/test_survey_flow.py']),('browser',['python','tests/test_browser_integration.py']),('allowance',['python','tests/test_client_allowance.py']),('leica',['python','tests/test_leica_connection.py']),('rls',['python','tests/test_database_policies.py']),('credits',['python','tests/test_survey_purchases.py']),('notification-database',['python','tests/test_survey_notifications.py']),('product-isolation',['node','audits/2026-11-03/check_payment_product_isolation.mjs']),('staging-setup',['python','tests/test_staging_setup_files.py'])]
def run(case):
 name,cmd=case;t=time.time();p=subprocess.run(cmd,cwd=root,input=(root/'app.js').read_text() if name=='syntax' else None,text=True,capture_output=True,timeout=240)
 (out/(name+'.log')).write_text(p.stdout+p.stderr)
 result={'case':name,'exit_code':p.returncode,'seconds':round(time.time()-t,2),'log':name+'.log'};print(json.dumps(result),flush=True);return result
with ThreadPoolExecutor(max_workers=1) as pool:results=list(pool.map(run,cases))
(out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
raise SystemExit(any(r['exit_code'] for r in results))
