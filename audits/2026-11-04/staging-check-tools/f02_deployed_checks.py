"""Dummy-only deployed F02 negative tests; no survey or notification writes."""
import os,json,urllib.request,urllib.error
from read_checks import BASE,KEY,USERS,call,rows
results=[]
def request(name,path,expected,token=None,body=None,method='POST',extra=None):
 headers={'apikey':KEY,'Content-Type':'application/json',**(extra or {})}
 if token: headers['Authorization']='Bearer '+token
 raw=json.dumps(body).encode() if body is not None else None
 req=urllib.request.Request(BASE+path,headers=headers,data=raw,method=method)
 try:
  with urllib.request.urlopen(req,timeout=30) as r: status=r.status; data=r.read()
 except urllib.error.HTTPError as e: status=e.code;data=e.read()
 try: reply=json.loads(data)
 except Exception: reply={}
 item={'check':name,'passed':status==expected,'http_status':status,'expected_status':expected}
 # Responses contain only generic application status/error; do not persist unknown bodies.
 if isinstance(reply,dict) and isinstance(reply.get('error'),str) and len(reply['error'])<180:item['error']=reply['error']
 results.append(item);print(json.dumps(item),flush=True)
 if status!=expected:raise RuntimeError('Unexpected status; stopped at '+name)
G='/functions/v1/request-survey-notification';R='/functions/v1/staging-notification-receiver'
def main():
 sessions={}
 for label,(uid,email,pid) in USERS.items():
  status,data=call('/auth/v1/token?grant_type=password',body={'email':email,'password':os.environ['URBANFOLD_STAGING_'+label+'_PASSWORD']})
  if status!=200 or data.get('user',{}).get('id')!=uid:raise RuntimeError('Staging dummy '+label+' authentication failed; HTTP '+str(status))
  sessions[label]=data['access_token']
  props=rows('/rest/v1/properties?select=id,last_submitted_at,user_id',sessions[label])
  if len(props)!=1 or props[0]['id']!=pid or props[0]['last_submitted_at'] is not None:raise RuntimeError('Original dummy fixture changed; stop before requests')
  print(json.dumps({'check':label+' confirmed dummy login and unchanged unsubmitted fixture','passed':True,'visible_properties':len(props)}),flush=True)
 request('Unauthenticated request rejected',G,401,body={'property_id':USERS['A'][2]})
 request('Invalid bearer rejected',G,401,token='invalid-staging-test-token',body={'property_id':USERS['A'][2]})
 request('B cannot notify A property',G,403,sessions['B'],{'property_id':USERS['A'][2]})
 request('A cannot notify B property',G,403,sessions['A'],{'property_id':USERS['B'][2]})
 for label in USERS:request(label+' own saved but unsubmitted survey rejected',G,409,sessions[label],{'property_id':USERS[label][2]})
 request('Nonexistent unsaved property rejected',G,403,sessions['A'],{'property_id':'f0000000-0000-4000-8000-000000000099'})
 request('Caller cannot supply recipient',G,400,sessions['A'],{'property_id':USERS['A'][2],'client_email':'test@example.invalid'})
 request('Caller cannot impersonate actor',G,400,sessions['B'],{'property_id':USERS['A'][2],'actor':USERS['A'][0]})
 request('Oversized body rejected',G,400,sessions['A'],{'property_id':USERS['A'][2],'padding':'x'*4200})
 request('Unapproved browser origin rejected',G,403,sessions['A'],{'property_id':USERS['A'][2]},extra={'Origin':'https://unapproved.example.invalid'})
 request('Configured localhost preflight succeeds',G,200,method='OPTIONS',extra={'Origin':'http://localhost:8794'})
 request('Unsupported method rejected',G,405,method='GET')
 request('A cannot invoke server-only receiver',R,401,sessions['A'],{})
 request('B cannot invoke server-only receiver',R,401,sessions['B'],{})
 request('Anonymous receiver rejected',R,401,body={})
 for label in USERS:
  request(label+' cannot read receiver receipts', '/rest/v1/staging_notification_receipts?select=kind,delivery_id,attempts',403,sessions[label],method='GET')
  request(label+' cannot read private outbox','/rest/v1/survey_notification_events?select=id,state',403,sessions[label],method='GET')
  status,allowance=call('/rest/v1/rpc/get_survey_allowance',sessions[label],{})
  if status!=200 or allowance.get('can_create') is not False or allowance.get('price_pence')!=600 or allowance.get('paid_credits')!=0:raise RuntimeError('Allowance differs from expected; stop')
  print(json.dumps({'check':label+' original 600-pence allowance unchanged; dedicated property creation unavailable','passed':True}),flush=True)
 print('PASS: negative requests tested against staging only. No survey updates, successful claims, fixture inserts, payments or external notification requests were attempted. Private receipt counts require authorised server/SQL access.')
if __name__=='__main__':main()
