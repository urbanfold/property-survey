"""One authorised dummy-only timeout request. Never retries or restores configuration."""
import os,json,time,datetime,hashlib,pathlib
from read_checks import USERS,BASE
from write_photo_checks import call
OUT=pathlib.Path('/workspace/property-survey/audits/2026-11-06/F02_TIMEOUT_EVIDENCE.json')
PID='f0200000-0000-4000-8000-000000000006'
evidence={'project':'hexhtduvqzleoazusskh','source_commit':'ac15c68d4f9d7521744eea2f062f9eff88ad6773','phase':'first_timeout_request_only','checks':[]}
def save():OUT.write_text(json.dumps(evidence,indent=2)+'\n')
def check(name,ok,**details):
 r={'check':name,'passed':bool(ok),**details};evidence['checks'].append(r);save();print(json.dumps(r),flush=True)
 if not ok:raise RuntimeError('Precondition/result failed: '+name)
def get(pid,t):
 s,d=call('/rest/v1/properties?select=*&id=eq.'+pid,t)
 if s!=200 or not isinstance(d,list) or len(d)!=1:raise RuntimeError('Property read failed; HTTP '+str(s))
 return d[0]
def digest(row):return hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest()
def main():
 if OUT.exists():raise RuntimeError('Prior timeout evidence exists. Stop; no automatic repeat permitted.')
 if BASE!='https://hexhtduvqzleoazusskh.supabase.co':raise RuntimeError('Wrong target')
 save();uid,email,original_id=USERS['B']
 s,d=call('/auth/v1/token?grant_type=password',body={'email':email,'password':os.environ['URBANFOLD_STAGING_B_PASSWORD']})
 check('Confirmed dummy B identity',s==200 and d.get('user',{}).get('id')==uid and d.get('user',{}).get('email')==email and bool(d.get('user',{}).get('email_confirmed_at')),http=s)
 t=d['access_token'];original=digest(get(original_id,t));p=get(PID,t)
 check('Exact submitted dummy fixture 6',p['user_id']==uid and p['address']=='DUMMY F02 FIXTURE 6 - NOT A REAL ADDRESS' and p['client_email']=='f02-fixture-6@example.invalid' and p['notes']=='DUMMY F02 fixture 6 malformed recipient' and p['last_submitted_at']=='2026-11-04T18:18:13.582957+00:00')
 notes='DUMMY F02 fixture 6 timeout test 2026-11-06';stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 s,d=call('/rest/v1/properties?id=eq.'+PID,t,{'notes':notes,'last_submitted_at':stamp},'PATCH')
 check('Only fixture 6 new dummy revision saved',s==200 and isinstance(d,list) and len(d)==1,http=s)
 saved=get(PID,t)
 check('Cloud readback before notification',saved['notes']==notes and datetime.datetime.fromisoformat(saved['last_submitted_at'])==datetime.datetime.fromisoformat(stamp) and saved['client_email']=='f02-fixture-6@example.invalid')
 evidence.update({'property_id':PID,'saved_notes':notes,'submission_at':saved['last_submitted_at'],'saved_row_hash':digest(saved),'original_B_row_hash':original,'request_started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'request_attempts':1});save()
 started=time.monotonic()
 try:
  status,body=call('/functions/v1/request-survey-notification',t,{'property_id':PID})
  elapsed=round(time.monotonic()-started,3)
  evidence['gateway_result']={'http_status':status,'elapsed_seconds':elapsed,'status':body.get('status') if isinstance(body,dict) else None};save()
  print(json.dumps(evidence['gateway_result']),flush=True)
 except Exception:
  evidence['gateway_result']={'transport_error':True,'elapsed_seconds':round(time.monotonic()-started,3),'no_retry':True};save();raise RuntimeError('Request transport failed: no retry; restore accept and reconcile counts') from None
 after=get(PID,t)
 check('Complete saved fixture row unchanged after request',digest(after)==digest(saved))
 check('Original B survey unchanged',digest(get(original_id,t))==original)
 # Record unexpected response before stopping. No second notification request.
 check('Gateway records uncertain outcome',status==202 and isinstance(body,dict) and body.get('status')=='uncertain',http=status)
 check('Response timing consistent with 10-second gateway timeout',elapsed>=9,elapsed_seconds=elapsed)
 time.sleep(20)
 check('Saved fixture still intact after receiver settling period',digest(get(PID,t))==digest(saved))
 evidence['next_step']='Operator restores STAGING_RECEIVER_BEHAVIOUR=accept; no retry until confirmation. Privileged receipt reconciliation pending.';save()
 print('STOPPED AS PLANNED: one request only. Restore staging receiver to accept before retry phase.',flush=True)
if __name__=='__main__':
 try:main()
 except Exception as e:
  print('STOP: '+str(e),flush=True)
  raise SystemExit(1)
