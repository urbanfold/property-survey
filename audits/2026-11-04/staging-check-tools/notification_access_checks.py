import os,json
import read_checks as r
import write_photo_checks as api
results=[]
def record(name,ok,status):
 row={'check':name,'passed':bool(ok),'http_status':status};results.append(row);print(json.dumps(row),flush=True)
 if not ok:raise RuntimeError(name)
uid,email,pid=r.USERS['A']
s,d=api.call('/auth/v1/token?grant_type=password',body={'email':email,'password':os.environ['URBANFOLD_STAGING_A_PASSWORD']})
record('Notification access probe uses verified dummy A',s==200 and d.get('user',{}).get('id')==uid,s)
token=d['access_token']
for table in ('survey_notification_events','survey_credit_revocations'):
 s,d=api.call('/rest/v1/'+table+'?select=*',token)
 record('Dummy user cannot read '+table,s in (401,403),s)
s,d=api.call('/rest/v1/rpc/record_survey_purchase',token,{'session_id':'INVALID_STAGING_PERMISSION_PROBE','intent_id':'INVALID','buyer_id':uid,'paid_amount':1,'paid_currency':'invalid','is_live':False})
record('Dummy user cannot execute purchase recorder',s in(401,403,404),s)
s,d=api.call('/rest/v1/rpc/claim_survey_notification',token,{'actor':uid,'property':pid,'revision':'2026-11-04T00:00:00Z'})
record('Dummy user cannot execute notification claim',s in(401,403,404),s)
s,d=api.call('/rest/v1/rpc/finish_survey_notification',token,{'event':'f0000000-0000-4000-8000-999999999999','accepted':False})
record('Dummy user cannot execute notification completion',s in(401,403,404),s)
s,d=api.call('/functions/v1/request-survey-notification',token)
print(json.dumps({'check':'F02 Edge Function availability (GET only, no notification sent)','http_status':s,'status':'not deployed' if s==404 else 'requires configuration/behaviour review'}),flush=True)
from pathlib import Path
out=Path('/workspace/staging-tools/evidence');out.mkdir(exist_ok=True)
(out/'notification-access.json').write_text(json.dumps({'target':r.BASE,'checks':results,'gateway_get_http_status':s,'no_notification_sent':True},indent=2))
