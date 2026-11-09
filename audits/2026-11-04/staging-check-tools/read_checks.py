"""Staging-only authenticated read checks. No credentials/tokens written or printed."""
import os,json,urllib.request,urllib.error
BASE='https://hexhtduvqzleoazusskh.supabase.co'
KEY=os.environ.get('URBANFOLD_STAGING_PUBLIC_KEY','')
USERS={
 'A':('9036b71c-4f09-4d1b-9dce-519533c4001e','staging-owner-a@example.invalid','f0000000-0000-4000-8000-000000000001'),
 'B':('d72b4323-d71b-4b87-b78a-09896647fddf','staging-owner-b@example.invalid','f0000000-0000-4000-8000-000000000002')}
results=[]
def call(path,token=None,body=None):
 assert path.startswith('/') and not path.startswith('//')
 headers={'apikey':KEY,'Content-Type':'application/json'}
 if token:headers['Authorization']='Bearer '+token
 req=urllib.request.Request(BASE+path,headers=headers,data=json.dumps(body).encode() if body is not None else None)
 try:
  with urllib.request.urlopen(req,timeout=25) as response:status=response.status;raw=response.read()
 except urllib.error.HTTPError as e:status=e.code;raw=e.read()
 except urllib.error.URLError as e:raise RuntimeError('Staging network request failed: '+type(e.reason).__name__) from None
 try:data=json.loads(raw)
 except Exception:data=None
 return status,data

def check(label,ok,**evidence):
 results.append({'check':label,'passed':bool(ok),**evidence})
 print(json.dumps(results[-1]),flush=True)
 if not ok:raise RuntimeError('Check failed: '+label)

def rows(path,token):
 status,data=call(path,token)
 if status!=200 or not isinstance(data,list):raise RuntimeError('Staging read failed for '+path.split('?')[0]+'; HTTP '+str(status))
 return data

def main():
 if not KEY or any(not os.environ.get('URBANFOLD_STAGING_'+a+'_PASSWORD') for a in USERS):raise RuntimeError('Required staging settings unavailable')
 sessions={}
 for label,(uid,email,pid) in USERS.items():
  status,data=call('/auth/v1/token?grant_type=password',body={'email':email,'password':os.environ['URBANFOLD_STAGING_'+label+'_PASSWORD']})
  check(label+' sign-in',status==200 and isinstance(data,dict) and data.get('user',{}).get('id')==uid and bool(data.get('access_token')),http_status=status)
  token=data['access_token'];sessions[label]=token
  status,user=call('/auth/v1/user',token)
  check(label+' verified Auth identity',status==200 and user.get('id')==uid and user.get('email')==email and bool(user.get('email_confirmed_at')),http_status=status)
  all_props=rows('/rest/v1/properties?select=id,user_id',token)
  check(label+' unfiltered property read',any(r['id']==pid for r in all_props) and all(r['user_id']==uid for r in all_props),visible_count=len(all_props))
  other='B' if label=='A' else 'A';other_pid=USERS[other][2]
  foreign=rows('/rest/v1/properties?select=id&id=eq.'+other_pid,token)
  check(label+' direct foreign property read denied',len(foreign)==0,visible_count=len(foreign))
  allocations=rows('/rest/v1/survey_free_allocations?select=user_id,property_id',token)
  check(label+' own free allocation only',len(allocations)==1 and allocations[0]['user_id']==uid and allocations[0]['property_id']==pid,visible_count=len(allocations))
  purchases=rows('/rest/v1/survey_credit_purchases?select=checkout_session_id,user_id',token)
  check(label+' no paid credits seeded',len(purchases)==0,visible_count=len(purchases))
  status,allowance=call('/rest/v1/rpc/get_survey_allowance',token,body={})
  check(label+' unchanged free/600-pence allowance',status==200 and isinstance(allowance,dict) and allowance.get('price_pence')==600 and allowance.get('currency')=='GBP' and allowance.get('paid_credits')==0 and allowance.get('free_available') is False and allowance.get('can_create') is False and allowance.get('unlimited') is False,http_status=status)
 a_rooms=rows('/rest/v1/rooms?select=id,property_id&property_id=eq.'+USERS['A'][2],sessions['A'])
 check('A can read seeded own room',len(a_rooms)>=1,visible_count=len(a_rooms))
 b_reads_a=rows('/rest/v1/rooms?select=id&property_id=eq.'+USERS['A'][2],sessions['B'])
 check('B cannot read A seeded room',len(b_reads_a)==0,visible_count=len(b_reads_a))
 status,_=call('/rest/v1/properties?select=id')
 check('Anonymous property API access denied',status in (401,403),http_status=status)
 print('PASS staging authenticated property/room/free-allocation read isolation and unchanged allowance. No application records, SQL, Stripe, email, Storage objects or production endpoints modified.',flush=True)

if __name__=='__main__':
 try:main()
 except Exception as e:
  print('STOP:',str(e),flush=True)
  raise SystemExit(1)
