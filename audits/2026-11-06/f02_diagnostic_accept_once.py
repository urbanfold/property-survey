"""One approved staging diagnostic accept request. No retry, config or deployment."""
import os,json,datetime,time,hashlib,pathlib
from read_checks import BASE,USERS
from write_photo_checks import call
OUT=pathlib.Path('/workspace/property-survey/audits/2026-11-06/F02_DIAGNOSTIC_ACCEPT_EVIDENCE.json')
PID='f0200000-0000-4000-8000-000000000006'
NOTES='DUMMY F02 fixture 6 diagnostics accept check diag-1'
e={'project':'hexhtduvqzleoazusskh','receiver_build_owner_confirmed':'urbanfold-staging-receiver-diag-1','phase':'single diagnostic accept request','checks':[],'notification_request_attempts':0}
def save():OUT.write_text(json.dumps(e,indent=2)+'\n')
def check(name,ok,**details):
 item={'check':name,'passed':bool(ok),**details};e['checks'].append(item);save();print(json.dumps(item),flush=True)
 if not ok:raise RuntimeError('STOP: '+name)
def get(pid,token):
 s,d=call('/rest/v1/properties?select=*&id=eq.'+pid,token)
 if s!=200 or not isinstance(d,list) or len(d)!=1:raise RuntimeError('Property read failed; HTTP '+str(s))
 return d[0]
def digest(row):return hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest()
def main():
 if OUT.exists():raise RuntimeError('Existing evidence found; no automatic rerun permitted.')
 if BASE!='https://hexhtduvqzleoazusskh.supabase.co':raise RuntimeError('Wrong project target')
 save();uid,email,original_id=USERS['B']
 s,d=call('/auth/v1/token?grant_type=password',body={'email':email,'password':os.environ['URBANFOLD_STAGING_B_PASSWORD']})
 check('Confirmed dummy B authentication',s==200 and d.get('user',{}).get('id')==uid and d.get('user',{}).get('email')==email and bool(d.get('user',{}).get('email_confirmed_at')),http_status=s)
 t=d['access_token'];original=get(original_id,t);p=get(PID,t)
 check('Exact owned dedicated fixture 6',p['user_id']==uid and p['address']=='DUMMY F02 FIXTURE 6 - NOT A REAL ADDRESS' and p['client_email']=='f02-fixture-6@example.invalid')
 check('Previous accepted submission still unchanged',p['notes']=='DUMMY F02 fixture 6 timeout test 2026-11-06' and p['last_submitted_at']=='2026-11-06T11:09:39.552512+00:00')
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 s,d=call('/rest/v1/properties?id=eq.'+PID,t,{'notes':NOTES,'last_submitted_at':stamp},'PATCH')
 check('Only approved fixture 6 revision saved',s==200 and isinstance(d,list) and len(d)==1 and d[0]['id']==PID,http_status=s)
 saved=get(PID,t)
 check('Cloud readback matches approved notes and fresh timestamp',saved['notes']==NOTES and datetime.datetime.fromisoformat(saved['last_submitted_at'])==datetime.datetime.fromisoformat(stamp) and saved['last_submitted_at']!=p['last_submitted_at'] and saved['client_email']=='f02-fixture-6@example.invalid')
 e.update({'property_id':PID,'saved_notes':NOTES,'submission_at':saved['last_submitted_at'],'saved_row_hash':digest(saved),'original_B_row_hash':digest(original),'request_started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'notification_request_attempts':1});save()
 started=time.monotonic()
 try:
  status,body=call('/functions/v1/request-survey-notification',t,{'property_id':PID})
 except Exception:
  e['response']={'transport_failure':True,'elapsed_seconds':round(time.monotonic()-started,3)};e['request_finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
  raise RuntimeError('Request transport failed; no retry performed; reconcile before further activity') from None
 e['request_finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 e['response']={'http_status':status,'status':body.get('status') if isinstance(body,dict) else None,'elapsed_seconds':round(time.monotonic()-started,3)};save()
 print(json.dumps({'started_at_utc':e['request_started_at_utc'],'finished_at_utc':e['request_finished_at_utc'],**e['response']}),flush=True)
 check('Complete saved fixture row unchanged after notification',digest(get(PID,t))==digest(saved))
 check('Original B survey unchanged',digest(get(original_id,t))==digest(original))
 check('Exactly one request accepted',status==200 and isinstance(body,dict) and body.get('status')=='accepted',http_status=status)
 e['next_step']='Owner inspects receiver diagnostics at recorded request time and reconciles private event/receipt counts. No retry.';save()
 print('COMPLETE: exactly one notification request; no retries, secret changes, deployment or cleanup.',flush=True)
if __name__=='__main__':
 try:main()
 except Exception as ex:
  print(str(ex),flush=True);raise SystemExit(1)
