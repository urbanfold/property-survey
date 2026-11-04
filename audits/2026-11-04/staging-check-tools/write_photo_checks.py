"""Real dummy-only staging checks. Credentials/tokens remain in memory. No SMTP/Stripe/DDL."""
import json,uuid,urllib.request,urllib.error,base64
import read_checks as read
BASE=read.BASE;KEY=read.KEY;USERS=read.USERS
results=[];retained=[]
def call(path,token=None,body=None,method=None,binary=False,content_type='application/json'):
 assert path.startswith('/') and not path.startswith('//') and not ('://' in path)
 headers={'apikey':KEY,'Content-Type':content_type,'Prefer':'return=representation'}
 if token:headers['Authorization']='Bearer '+token
 payload=body if isinstance(body,bytes) else json.dumps(body).encode() if body is not None else None
 req=urllib.request.Request(BASE+path,headers=headers,data=payload,method=method or ('POST' if payload is not None else 'GET'))
 try:
  with urllib.request.urlopen(req,timeout=25) as r:status=r.status;raw=r.read()
 except urllib.error.HTTPError as e:status=e.code;raw=e.read()
 except urllib.error.URLError as e:raise RuntimeError('Network failure: '+type(e.reason).__name__) from None
 if binary:return status,raw
 try:return status,json.loads(raw)
 except Exception:return status,None

def check(name,ok,**details):
 result={'check':name,'passed':bool(ok),**details};results.append(result);print(json.dumps(result),flush=True)
 if not ok:raise RuntimeError('Check failed: '+name)

def denied(status,data):
 # Storage often wraps a row-security rejection in HTTP 400.
 text=json.dumps(data).lower()
 return status in (401,403) or (status==400 and any(x in text for x in ('row-level security','unauthorized','not authorized','access denied')))

def main():
 tokens={}
 for label,(uid,email,pid) in USERS.items():
  status,data=call('/auth/v1/token?grant_type=password',body={'email':email,'password':__import__('os').environ['URBANFOLD_STAGING_'+label+'_PASSWORD']})
  check(label+' write-test Auth identity',status==200 and data.get('user',{}).get('id')==uid,http_status=status)
  tokens[label]=data['access_token']
 a,b=tokens['A'],tokens['B'];pid=USERS['A'][2]
 status,props=call('/rest/v1/properties?select=id,user_id,address,notes&id=eq.'+pid,a)
 check('Only seeded fictional A record selected',status==200 and len(props)==1 and props[0]['user_id']==USERS['A'][0] and props[0]['address'].startswith('DUMMY PROPERTY A'))
 original_notes=props[0]['notes'];sentinel='STAGING AUTOMATED TEST '+uuid.uuid4().hex
 refs=[];room_id=None
 try:
  status,data=call('/rest/v1/properties?id=eq.'+pid,a,{'notes':sentinel},'PATCH')
  check('A can update own dummy notes',status==200 and len(data)==1 and data[0]['notes']==sentinel,http_status=status)
  status,data=call('/rest/v1/properties?id=eq.'+pid,b,{'notes':'STAGING FORBIDDEN B WRITE'},'PATCH')
  check('B cannot update A dummy property',status==200 and data==[] or denied(status,data),http_status=status)
  status,data=call('/rest/v1/properties?select=notes&id=eq.'+pid,a)
  check('Forbidden B write left A notes unchanged',status==200 and data[0]['notes']==sentinel)
  status,data=call('/rest/v1/properties?id=eq.'+pid,a,{'user_id':USERS['B'][0]},'PATCH')
  check('A cannot transfer ownership to B',denied(status,data),http_status=status)
  failed_id=str(uuid.uuid4())
  status,data=call('/rest/v1/properties',a,{'id':failed_id,'user_id':USERS['A'][0],'address':'DUMMY DENIED SECOND SURVEY','postcode':'ZZ9 9ZZ'})
  check('Second property denied without paid credit',status==400 and isinstance(data,dict) and data.get('message')=='URBANFOLD_SURVEY_LIMIT',http_status=status)
  status,data=call('/rest/v1/properties?select=id&id=eq.'+failed_id,a)
  check('Failed second-survey insert left no property',status==200 and data==[])
  status,rooms=call('/rest/v1/rooms?select=id&property_id=eq.'+pid,a)
  check('Seeded room available for dummy photo references',status==200 and len(rooms)==1)
  room_id=rooms[0]['id']
  status,data=call('/rest/v1/rooms?id=eq.'+room_id,b,{'additional_measurements':'STAGING FORBIDDEN ROOM WRITE'},'PATCH')
  check('B cannot update A room',status==200 and data==[] or denied(status,data),http_status=status)
  photo=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=')
  for bucket,table in [('exterior-photos','exterior_photos'),('sketch-photos','sketch_photos'),('room-photos','room_photos')]:
   name=pid+'/staging-test-'+uuid.uuid4().hex+'.png'
   status,data=call('/storage/v1/object/'+bucket+'/'+name,a,photo,content_type='image/png')
   check(bucket+' A own-prefix upload',status in (200,201),http_status=status)
   retained.append({'bucket':bucket,'path':name})
   status,_=call('/storage/v1/object/authenticated/'+bucket+'/'+name,a,binary=True)
   check(bucket+' A authenticated download',status==200,http_status=status)
   status,_=call('/storage/v1/object/authenticated/'+bucket+'/'+name,b,binary=True)
   check(bucket+' B foreign authenticated download denied',status in (400,401,403,404),http_status=status)
   for label,token,expected in [('A',a,True),('B',b,False)]:
    status,data=call('/storage/v1/object/sign/'+bucket+'/'+name,token,{'expiresIn':60})
    if expected:ok=status==200 and isinstance(data,dict) and bool(data.get('signedURL'))
    else:ok=status in (400,401,403,404) and not (isinstance(data,dict) and data.get('signedURL'))
    check(bucket+' '+label+' private signing '+('allowed' if expected else 'denied'),ok,http_status=status)
   for label,token,expected in [('A',a,True),('B',b,False)]:
    status,data=call('/storage/v1/object/list/'+bucket,token,{'prefix':pid+'/','limit':100,'offset':0})
    visible=isinstance(data,list) and any(row.get('name')==name.split('/')[-1] for row in data)
    check(bucket+' '+label+' owner-scoped listing',status==200 and visible==expected,http_status=status)
   status,data=call('/storage/v1/object/'+bucket+'/'+pid+'/staging-forbidden-'+uuid.uuid4().hex+'.png',b,photo,content_type='image/png')
   check(bucket+' B foreign-prefix upload denied',denied(status,data),http_status=status)
   status,_=call('/storage/v1/object/public/'+bucket+'/'+name,binary=True)
   check(bucket+' anonymous public download denied',status in (400,401,403,404),http_status=status)
   ref={'photo_url':'storage://'+bucket+'/'+name}
   ref.update({'room_id':room_id} if table=='room_photos' else {'property_id':pid})
   if table=='exterior_photos':ref['elevation_type']='front'
   status,data=call('/rest/v1/'+table,a,ref)
   check(table+' A reference insert',status==201 and len(data)==1,http_status=status)
   refs.append((table,data[0]['id']))
   if table=='exterior_photos':
    status,data=call('/rest/v1/extension_photos',a,{'property_id':pid,'photo_url':ref['photo_url']})
    check('extension_photos A reference insert',status==201 and len(data)==1,http_status=status)
    refs.append(('extension_photos',data[0]['id']))
   status,data=call('/rest/v1/'+table+'?select=id&id=eq.'+refs[-1 if table!='exterior_photos' else -2][1],b)
   check(table+' B cannot read A reference',status==200 and data==[],http_status=status)
   bad={'room_id':room_id,'photo_url':ref['photo_url']} if table=='room_photos' else {**ref,'property_id':pid}
   status,data=call('/rest/v1/'+table,b,bad)
   check(table+' B foreign-parent insert denied',denied(status,data),http_status=status)
 finally:
  for table,ref_id in reversed(refs):
   status,data=call('/rest/v1/'+table+'?id=eq.'+ref_id,a,method='DELETE')
   check(table+' temporary reference removed',status==200 and len(data)==1,http_status=status)
  status,data=call('/rest/v1/properties?id=eq.'+pid,a,{'notes':original_notes},'PATCH')
  check('A original dummy notes restored',status==200 and len(data)==1 and data[0]['notes']==original_notes,http_status=status)
 # No DELETE object policy: tiny dummy bytes deliberately remain in private staging buckets.
 print(json.dumps({'retained_private_dummy_objects':retained}),flush=True)
 print('PASS dummy-only edit/ownership/allowance/photo isolation checks; no production, credits, submissions, email or Stripe changes.',flush=True)

if __name__=='__main__':
 try:main()
 except Exception as e:
  print('STOP:',str(e),flush=True);raise SystemExit(1)
