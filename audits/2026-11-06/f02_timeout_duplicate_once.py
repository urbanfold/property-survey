"""One authorised duplicate of the exact saved timeout revision; no mutations/retries."""
import os,json,datetime,time,hashlib,pathlib
from read_checks import BASE,USERS
from write_photo_checks import call
ROOT=pathlib.Path('/workspace/property-survey/audits/2026-11-06')
OUT=ROOT/'F02_TIMEOUT_DUPLICATE_EVIDENCE.json'
e={'project':'hexhtduvqzleoazusskh','phase':'single exact-revision duplicate','notification_request_attempts':0,'checks':[]}
def save():OUT.write_text(json.dumps(e,indent=2)+'\n')
def check(name,ok,**details):
 r={'check':name,'passed':bool(ok),**details};e['checks'].append(r);save();print(json.dumps(r),flush=True)
 if not ok:raise RuntimeError('STOP: '+name)
def digest(row):return hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest()
def get(pid,t):
 s,d=call('/rest/v1/properties?select=*&id=eq.'+pid,t)
 if s!=200 or not isinstance(d,list) or len(d)!=1:raise RuntimeError('Property read failed; HTTP '+str(s))
 return d[0]
def main():
 if OUT.exists():raise RuntimeError('Duplicate evidence already exists; no rerun permitted.')
 if BASE!='https://hexhtduvqzleoazusskh.supabase.co':raise RuntimeError('Wrong target')
 prior=json.loads((ROOT/'F02_DIAGNOSTIC_TIMEOUT_EVIDENCE.json').read_text())
 pid=prior['property_id'];assert pid=='f0200000-0000-4000-8000-000000000006'
 save();uid,email,original_id=USERS['B']
 s,d=call('/auth/v1/token?grant_type=password',body={'email':email,'password':os.environ['URBANFOLD_STAGING_B_PASSWORD']})
 check('Confirmed dummy B authentication',s==200 and d.get('user',{}).get('id')==uid and d.get('user',{}).get('email')==email and bool(d.get('user',{}).get('email_confirmed_at')),http_status=s)
 t=d['access_token'];saved=get(pid,t)
 check('Exact saved timeout revision unchanged before duplicate',saved['user_id']==uid and saved['notes']==prior['saved_notes'] and saved['last_submitted_at']==prior['submission_at'] and digest(saved)==prior['saved_row_hash'])
 original=get(original_id,t)
 check('Original B survey still matches timeout snapshot',digest(original)==prior['original_B_row_hash'])
 e.update({'property_id':pid,'submission_at':saved['last_submitted_at'],'saved_row_hash':digest(saved),'original_B_row_hash':digest(original),'request_started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'notification_request_attempts':1});save()
 started=time.monotonic()
 try:
  status,body=call('/functions/v1/request-survey-notification',t,{'property_id':pid})
 except Exception:
  e.update({'request_finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'response':{'transport_failure':True,'elapsed_seconds':round(time.monotonic()-started,3)}});save()
  raise RuntimeError('Request transport failed; no retry; reconcile before further action') from None
 e.update({'request_finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'response':{'http_status':status,'status':body.get('status') if isinstance(body,dict) else None,'elapsed_seconds':round(time.monotonic()-started,3)}});save()
 print(json.dumps({'started_at_utc':e['request_started_at_utc'],'finished_at_utc':e['request_finished_at_utc'],**e['response']}),flush=True)
 check('Fixture notes timestamp and entire row unchanged after duplicate',digest(get(pid,t))==prior['saved_row_hash'])
 check('Original B survey unchanged after duplicate',digest(get(original_id,t))==digest(original))
 check('Duplicate returns existing uncertain status',status==202 and isinstance(body,dict) and body.get('status')=='uncertain',http_status=status)
 e['verification_boundary']='Response and exact saved revision verified directly. No receiver access/log or private receipt-count access; owner reconciliation required to prove no new capture.';save()
 print('STOPPED: one duplicate only; no edits, settings changes, deployment or cleanup. Private receipt counters and logs pending.',flush=True)
if __name__=='__main__':
 try:main()
 except Exception as ex:
  print(str(ex),flush=True);raise SystemExit(1)
