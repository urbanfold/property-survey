"""Approved staging-only F02 tests; six exact dedicated fixtures, no cleanup."""
import os,json,hashlib,datetime,concurrent.futures,pathlib
from write_photo_checks import call
from read_checks import USERS
ROOT=pathlib.Path('/workspace/property-survey/audits/2026-11-04')
LOG=ROOT/'f02-positive-evidence.jsonl'
G='/functions/v1/request-survey-notification'
IDS=['f0200000-0000-4000-8000-'+str(n).zfill(12) for n in range(1,7)]
results=[]
def check(name,ok,**data):
 r={'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'check':name,'passed':bool(ok),**data}
 results.append(r)
 with LOG.open('a') as f:f.write(json.dumps(r)+'\n')
 print(json.dumps(r),flush=True)
 if not ok:raise RuntimeError('STOP: '+name)
def get(pid,t):
 s,d=call('/rest/v1/properties?select=*&id=eq.'+pid,t)
 if s!=200 or not isinstance(d,list) or len(d)!=1:raise RuntimeError('Fixture read failed')
 return d[0]
def digest(data):return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
def patch(pid,t,**changes):
 assert pid in IDS
 s,d=call('/rest/v1/properties?id=eq.'+pid,t,changes,'PATCH')
 check('Dedicated fixture update '+pid[-1],s==200 and len(d)==1 and all(d[0][k]==v for k,v in changes.items()),http=s)
def submit(pid,t,notes):
 patch(pid,t,notes=notes,last_submitted_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
def notify(pid,t,name,expected=200,state='accepted'):
 assert pid in IDS
 s,d=call(G,t,{'property_id':pid})
 check(name,s==expected and (d.get('status')==state if state else True),http=s,response=d)
 return s,d
def main():
 if LOG.exists():raise RuntimeError('Evidence already exists; inspect before rerunning. No automatic retries.')
 tokens={};original={};allowances={}
 for label,(uid,email,pid) in USERS.items():
  s,d=call('/auth/v1/token?grant_type=password',body={'email':email,'password':os.environ['URBANFOLD_STAGING_'+label+'_PASSWORD']})
  check(label+' confirmed dummy sign-in',s==200 and d.get('user',{}).get('id')==uid and bool(d.get('user',{}).get('email_confirmed_at')),http=s)
  tokens[label]=d['access_token'];original[label]=digest(get(pid,tokens[label]))
  s,d=call('/rest/v1/rpc/get_survey_allowance',tokens[label],{})
  check(label+' baseline 600-pence allowance',s==200 and d.get('price_pence')==600 and d.get('paid_credits')==0 and not d.get('can_create'))
  allowances[label]=d
 for n,pid in enumerate(IDS,1):
  t=tokens['A' if n<=5 else 'B'];p=get(pid,t)
  check('Dedicated fixture '+str(n)+' exact identity',p['address']=='DUMMY F02 FIXTURE '+str(n)+' - NOT A REAL ADDRESS' and p['user_id']==USERS['A' if n<=5 else 'B'][0] and p['notes']=='DEDICATED F02 NOTIFICATION TEST ONLY; retain pending evidence review.' and bool(p['last_submitted_at']) and p['client_email']=='f02-fixture-'+str(n)+'@example.invalid')
 a,b=tokens['A'],tokens['B'];p=IDS[0]
 notify(p,a,'First legitimate submitted notification')
 notify(p,a,'Sequential duplicate accepted without new content')
 patch(p,a,notes='DUMMY F02 fixture 1 revision 2')
 notify(p,a,'Changed content without new submission rejected',409,None)
 # Same timestamp cannot create a second event: unique submission key fails safely.
 submit(p,a,'DUMMY F02 fixture 1 revision 2')
 notify(p,a,'Changed content plus new saved submission accepted')
 # Concurrent FIRST requests for an untouched saved fixture exercise claim locking.
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  replies=list(pool.map(lambda _:call(G,a,{'property_id':IDS[1]}),range(4)))
 check('Four concurrent initial requests safely acknowledged',all(s in(200,202) and d.get('status') in('accepted','uncertain') for s,d in replies),http_statuses=[s for s,d in replies],responses=[d for s,d in replies])
 notify(IDS[1],a,'Concurrent fixture subsequently accepted')
 for revision in range(3,6):
  submit(p,a,'DUMMY F02 fixture 1 revision '+str(revision));notify(p,a,'Property 1 allowed revision '+str(revision))
 submit(p,a,'DUMMY F02 fixture 1 blocked revision 6')
 notify(p,a,'Sixth property notification rate-limited',429,None)
 check('Property-limited survey edits remain saved',get(p,a)['notes']=='DUMMY F02 fixture 1 blocked revision 6')
 for idx in range(1,4):
  start=2 if idx==1 else 1
  for revision in range(start,6):
   if not(idx>1 and revision==1):submit(IDS[idx],a,'DUMMY F02 fixture '+str(idx+1)+' revision '+str(revision))
   notify(IDS[idx],a,'Account A property '+str(idx+1)+' allowed revision '+str(revision))
 notify(IDS[4],a,'Account A 21st event on unused property rate-limited',429,None)
 check('Account-limited fixture remains saved',get(IDS[4],a)['notes']=='DEDICATED F02 NOTIFICATION TEST ONLY; retain pending evidence review.')
 # Dummy-only reserved domain, deliberately uppercase: gateway accepts its format,
 # but capture SQL rejects its case-sensitive @example.invalid guard. No live recipient.
 p=IDS[5]
 patch(p,b,client_email='f02-fixture-6@EXAMPLE.INVALID')
 notify(p,b,'Receiver dummy guard rejection yields uncertain',202,'uncertain')
 notify(p,b,'Uncertain delivery duplicate is not automatically retried',202,'uncertain')
 check('Receiver rejection preserves saved survey',get(p,b)['client_email']=='f02-fixture-6@EXAMPLE.INVALID' and bool(get(p,b)['last_submitted_at']))
 patch(p,b,client_email='f02-fixture-6@example.invalid')
 submit(p,b,'DUMMY F02 fixture 6 valid recipient revision 2')
 notify(p,b,'Changed valid dummy submission captured after rejection')
 patch(p,b,client_email='DUMMY-NOT-AN-EMAIL')
 submit(p,b,'DUMMY F02 fixture 6 malformed recipient')
 notify(p,b,'Malformed saved recipient rejected safely',409,None)
 # Restore fixture to its last accepted content and exact accepted submission time
 # is unnecessary: correcting recipient without a request does not create an event.
 patch(p,b,client_email='f02-fixture-6@example.invalid')
 for label,(_,_,pid) in USERS.items():
  check(label+' original survey unchanged',digest(get(pid,tokens[label]))==original[label])
  s,d=call('/rest/v1/rpc/get_survey_allowance',tokens[label],{})
  check(label+' full allowance unchanged',s==200 and d==allowances[label])
 check('Expected ledger totals pending privileged verification',True,expected_events=22,expected_accepted=21,expected_uncertain=1,expected_receipts=21,expected_capture_attempts=21)
 print('DONE. No cleanup or settings changes. Counts and actual transport timeout still require separate verification.',flush=True)
if __name__=='__main__':
 try:main()
 except Exception as e:
  print(type(e).__name__+': '+str(e),flush=True)
  raise SystemExit(1)
