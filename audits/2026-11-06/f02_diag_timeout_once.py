"""Approved diagnostic timeout: one initial request only, no automatic retries."""
import os,json,time,datetime,hashlib,pathlib
from read_checks import BASE,USERS
from write_photo_checks import call
OUT=pathlib.Path('/workspace/property-survey/audits/2026-11-06/F02_DIAGNOSTIC_TIMEOUT_EVIDENCE.json')
PRIOR=pathlib.Path('/workspace/property-survey/audits/2026-11-06/F02_DIAGNOSTIC_ACCEPT_EVIDENCE.json')
PID='f0200000-0000-4000-8000-000000000006'
NOTES='DUMMY F02 fixture 6 diagnostic timeout check diag-1'
e={'project':'hexhtduvqzleoazusskh','receiver_build_owner_confirmed':'urbanfold-staging-receiver-diag-1','phase':'initial diagnostic timeout request only','checks':[],'notification_request_attempts':0,'owner_reported_pretest':{'events':24,'accepted':23,'uncertain':1,'sending':0,'receipts':23,'capture_attempts':23,'repeat_captures':0,'property_last24':2,'account_last24':2}}
def save():OUT.write_text(json.dumps(e,indent=2)+'\n')
def check(name,ok,**details):
 item={'check':name,'passed':bool(ok),**details};e['checks'].append(item);save();print(json.dumps(item),flush=True)
 if not ok:raise RuntimeError('STOP: '+name)
def get(pid,t):
 s,d=call('/rest/v1/properties?select=*&id=eq.'+pid,t)
 if s!=200 or not isinstance(d,list) or len(d)!=1:raise RuntimeError('Property read failed: HTTP '+str(s))
 return d[0]
def digest(p):return hashlib.sha256(json.dumps(p,sort_keys=True).encode()).hexdigest()
def main():
 if OUT.exists():raise RuntimeError('Evidence already exists; do not repeat a potentially captured request.')
 if BASE!='https://hexhtduvqzleoazusskh.supabase.co':raise RuntimeError('Wrong target')
 prior=json.loads(PRIOR.read_text());save()
 uid,email,original_id=USERS['B']
 s,d=call('/auth/v1/token?grant_type=password',body={'email':email,'password':os.environ['URBANFOLD_STAGING_B_PASSWORD']})
 check('Confirmed dummy B authentication',s==200 and d.get('user',{}).get('id')==uid and d.get('user',{}).get('email')==email and bool(d.get('user',{}).get('email_confirmed_at')),http_status=s)
 t=d['access_token'];original=get(original_id,t);p=get(PID,t)
 check('Exact owned dummy fixture 6',p['user_id']==uid and p['address']=='DUMMY F02 FIXTURE 6 - NOT A REAL ADDRESS' and p['client_email']=='f02-fixture-6@example.invalid')
 check('Prior accepted diagnostic submission unchanged',p['notes']==prior['saved_notes'] and p['last_submitted_at']==prior['submission_at'])
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
 s,d=call('/rest/v1/properties?id=eq.'+PID,t,{'notes':NOTES,'last_submitted_at':stamp},'PATCH')
 check('Only approved fixture revision saved',s==200 and isinstance(d,list) and len(d)==1 and d[0]['id']==PID,http_status=s)
 saved=get(PID,t)
 check('Fresh notes and timestamp read back before notification',saved['notes']==NOTES and datetime.datetime.fromisoformat(saved['last_submitted_at'])==datetime.datetime.fromisoformat(stamp) and saved['last_submitted_at']!=p['last_submitted_at'] and saved['client_email']=='f02-fixture-6@example.invalid')
 e.update({'property_id':PID,'saved_notes':NOTES,'submission_at':saved['last_submitted_at'],'saved_row_hash':digest(saved),'original_B_row_hash':digest(original),'request_started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'notification_request_attempts':1});save()
 started=time.monotonic()
 try:
  status,body=call('/functions/v1/request-survey-notification',t,{'property_id':PID})
 except Exception:
  e.update({'request_finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'response':{'transport_failure':True,'elapsed_seconds':round(time.monotonic()-started,3)}});save()
  raise RuntimeError('Transport failure: do not retry; restore accept and reconcile') from None
 e.update({'request_finished_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'response':{'http_status':status,'status':body.get('status') if isinstance(body,dict) else None,'elapsed_seconds':round(time.monotonic()-started,3)}});save()
 print(json.dumps({'started_at_utc':e['request_started_at_utc'],'finished_at_utc':e['request_finished_at_utc'],**e['response']}),flush=True)
 check('Saved fixture row unchanged after request',digest(get(PID,t))==digest(saved))
 check('Original B property unchanged',digest(get(original_id,t))==digest(original))
 check('Expected uncertain gateway response',status==202 and isinstance(body,dict) and body.get('status')=='uncertain',http_status=status)
 check('Duration consistent with gateway timeout',e['response']['elapsed_seconds']>=9,elapsed_seconds=e['response']['elapsed_seconds'])
 e['next_step']='Owner verifies diagnostic timeout mode logs and restores accept. No duplicate authorised until restoration confirmed. Private counts pending.';save()
 print('STOPPED AS PLANNED. One initial request only. Restore accept; no duplicate yet.',flush=True)
if __name__=='__main__':
 try:main()
 except Exception as ex:
  print(str(ex),flush=True);raise SystemExit(1)
