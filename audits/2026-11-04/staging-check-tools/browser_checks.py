"""Real staging browser checks via real HTTPS transport; no fake backend responses.
Local static assets are served in-process. No traces/screenshots/secrets persisted.
"""
from pathlib import Path
import os,json,urllib.request,urllib.error,mimetypes,shutil,sys,base64
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright,expect
import read_checks as read
import write_photo_checks as api
ROOT=Path('/workspace/urbanfold-staging-client')
STAGE='hexhtduvqzleoazusskh.supabase.co'
OUT=Path('/workspace/staging-tools/evidence');OUT.mkdir(exist_ok=True)
checks=[];blocked=[];objects=[];states={'offline':False}

def record(name,ok):
 checks.append({'check':name,'passed':bool(ok)});print(json.dumps(checks[-1]),flush=True)
 (OUT/'browser.json').write_text(json.dumps({'target':STAGE,'checks':checks,'transport':'real staging HTTPS via environment proxy; local static assets routed in-process'},indent=2))
 if not ok:raise RuntimeError(name)

def main():
 # Get a separate verified dummy session for cleanup; no tokens written to disk.
 uid,email,pid=read.USERS['A']
 status,login=api.call('/auth/v1/token?grant_type=password',body={'email':email,'password':os.environ['URBANFOLD_STAGING_A_PASSWORD']})
 record('Cleanup session belongs to dummy A',status==200 and login.get('user',{}).get('id')==uid)
 cleanup=login['access_token']
 status,props=api.call('/rest/v1/properties?select=*&id=eq.'+pid,cleanup)
 record('Browser target is seeded fictional A property',status==200 and len(props)==1 and props[0]['address'].startswith('DUMMY PROPERTY A'))
 backups={}
 for table in ('rooms','extensions','exterior_photos','extension_photos','sketch_photos'):
  status,data=api.call('/rest/v1/'+table+'?select=*&property_id=eq.'+pid,cleanup)
  if status!=200:raise RuntimeError('Backup failed')
  backups[table]=data
 property_before=props[0]
 def route(r):
  req=r.request;u=urlparse(req.url)
  if u.hostname=='localhost' and u.port==8794:
   path=(ROOT/(u.path.lstrip('/') or 'index.html')).resolve()
   if ROOT in path.parents and path.is_file():return r.fulfill(body=path.read_bytes(),content_type=mimetypes.guess_type(str(path))[0] or 'application/octet-stream')
   return r.fulfill(status=404,body='Not found')
  if u.scheme!='https' or u.hostname!=STAGE:
   blocked.append('external request refused');return r.abort()
  if states['offline'] and u.path.startswith('/rest/v1/'):
   return r.abort('internetdisconnected')
  headers={k:v for k,v in req.headers.items() if k.lower() not in ('host','content-length','connection','accept-encoding')}
  transport=urllib.request.Request(req.url,headers=headers,data=req.post_data_buffer,method=req.method)
  try:
   with urllib.request.urlopen(transport,timeout=30) as response:status=response.status;body=response.read();incoming=dict(response.headers)
  except urllib.error.HTTPError as e:status=e.code;body=e.read();incoming=dict(e.headers)
  except Exception:return r.abort()
  if req.method=='POST' and u.path.startswith('/storage/v1/object/') and not any(x in u.path for x in ('/sign/','/list/')) and status in(200,201):
   objects.append(u.path)
  incoming={k:v for k,v in incoming.items() if k.lower() not in ('content-length','transfer-encoding','content-encoding','connection')}
  r.fulfill(status=status,body=body,headers=incoming)
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
   context=browser.new_context();context.route('**/*',route)
   page=context.new_page();page.on('dialog',lambda d:d.dismiss() if d.type=='beforeunload' else d.accept())
   def configure():
    page.goto('http://localhost:8794/')
    page.locator('#staging-public-key').fill(os.environ['URBANFOLD_STAGING_PUBLIC_KEY'])
    page.locator('#staging-start').click();expect(page.locator('#view-auth')).to_be_visible()
   def signin(label):
    page.locator('#login-email').fill(read.USERS[label][1]);page.locator('#login-password').fill(os.environ['URBANFOLD_STAGING_'+label+'_PASSWORD'])
    page.get_by_role('button',name='Log In',exact=True).click()
   configure();signin('A');expect(page.locator('#view-dashboard')).to_be_visible(timeout=30000)
   page.get_by_role('button',name='Check account isolation (read only)').click()
   expect(page.locator('#staging-isolation-result')).to_contain_text('PASS — Account A',timeout=30000)
   record('Real staging browser A login and unfiltered/direct property-read check',True)
   page.locator('.survey-item').first.click();expect(page.locator('#view-details')).to_be_visible(timeout=30000)
   page.evaluate("showView('view-interior-rooms')")
   page.locator('#len-Living-Room').evaluate("el=>{if(!el.offsetParent)el.closest('.room-body').previousElementSibling.click();}")
   page.locator('#len-Living-Room').fill('4.5678')
   # Snapshot immediately, with no debounce wait.
   page.evaluate('sb.auth._removeSession()');expect(page.locator('#view-auth')).to_be_visible()
   record('Simulated local expiry locks live-staging UI and keeps immediate edit only in memory',page.evaluate("!!lockedSurveyRecovery && !localStorage.getItem('urbanfold_draft') && !document.getElementById('detail-address').value"))
   signin('A');expect(page.locator('#view-interior-rooms')).to_be_visible(timeout=30000)
   record('Same-user live Auth/property check restores temporary measurement',page.locator('#len-Living-Room').input_value()=='4.5678')
   page.evaluate('sb.auth.refreshSession()')
   record('Real staging token refresh keeps room measurement',page.locator('#len-Living-Room').input_value()=='4.5678')
   states['offline']=True
   page.evaluate('saveCloudProgress()')
   states['offline']=False
   record('Simulated disconnected REST save retains measurement/device draft',page.locator('#len-Living-Room').input_value()=='4.5678' and page.evaluate("!!localStorage.getItem('urbanfold_draft')"))
   # Use the actual UI photo compressor/uploader, then cloud readback verification.
   page.evaluate("showView('view-exterior')")
   photo=base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=')
   page.locator('#input-front').set_input_files({'name':'dummy-test.png','mimeType':'image/png','buffer':photo})
   expect(page.locator('#preview-front img')).to_have_count(1)
   page.wait_for_function('photoJobs.size===0')
   page.evaluate('saveCloudProgress()')
   record('Actual JPEG upload and full survey save verified in real staging',page.locator('#save-status').get_attribute('data-state')=='cloud')
   page.reload();page.locator('#staging-public-key').fill(os.environ['URBANFOLD_STAGING_PUBLIC_KEY']);page.locator('#staging-start').click()
   expect(page.locator('#view-dashboard')).to_be_visible(timeout=30000)
   page.locator('.survey-item').first.click();expect(page.locator('#view-details')).to_be_visible(timeout=30000)
   record('Fresh reload reopens actual saved measurements and signed photo',page.locator('#len-Living-Room').input_value()=='4.5678' and page.evaluate("appState.photos.front?.length===1"))
   with page.expect_download(timeout=30000) as dl:
    page.evaluate('generatePDF()')
   pdf=dl.value.path().read_bytes()
   record('Own-property PDF export creates actual PDF bytes',pdf.startswith(b'%PDF') and len(pdf)>1000)
   with page.expect_download(timeout=30000) as dl:
    page.evaluate('(pid)=>downloadSurveyPack(pid,"DUMMY PROPERTY A")',pid)
   zip_bytes=dl.value.path().read_bytes()
   record('Own-property ZIP export creates actual ZIP bytes',zip_bytes.startswith(b'PK') and len(zip_bytes)>100)
   page.evaluate("showView('view-interior-rooms')")
   page.locator('#len-Living-Room').evaluate("el=>{if(!el.offsetParent)el.closest('.room-body').previousElementSibling.click();}")
   page.locator('#len-Living-Room').fill('9.1111')
   page.evaluate('sb.auth._removeSession()');expect(page.locator('#view-auth')).to_be_visible()
   signin('B');expect(page.locator('#view-dashboard')).to_be_visible(timeout=30000)
   record('Different real dummy account cannot recover A measurements',page.evaluate("currentUser.id==='d72b4323-d71b-4b87-b78a-09896647fddf' && lockedSurveyRecovery===null && !document.getElementById('len-Living-Room').value"))
   page.get_by_role('button',name='Check account isolation (read only)').click()
   expect(page.locator('#staging-isolation-result')).to_contain_text('PASS — Account B',timeout=30000)
   record('Real staging browser B property-read check',True)
   page.evaluate('handleLogout()');expect(page.locator('#view-auth')).to_be_visible()
   record('Explicit logout clears current identity and private drafts',page.evaluate("currentUser===null && lockedSurveyRecovery===null && !localStorage.getItem('urbanfold_draft')"))
   record('No other external host contacted by the browser',not blocked)
   browser.close()
 finally:
  states['offline']=False
  # Restore only seeded property fields and rows; remove only rows this test added.
  for table in ('exterior_photos','extension_photos','sketch_photos','rooms','extensions'):
   status,current=api.call('/rest/v1/'+table+'?select=*&property_id=eq.'+pid,cleanup)
   if status!=200:raise RuntimeError('Cleanup read failed: '+table)
   before={row['id']:row for row in backups[table]}
   for row in current:
    if row['id'] not in before:
     code,_=api.call('/rest/v1/'+table+'?id=eq.'+row['id'],cleanup,method='DELETE')
     if code!=200:raise RuntimeError('Cleanup delete failed: '+table)
    elif row!=before[row['id']]:
     payload={k:v for k,v in before[row['id']].items() if k not in ('id','created_at')}
     code,_=api.call('/rest/v1/'+table+'?id=eq.'+row['id'],cleanup,payload,'PATCH')
     if code!=200:raise RuntimeError('Cleanup restore failed: '+table)
  restore={k:v for k,v in property_before.items() if k not in ('id','created_at','user_id','last_submitted_at','address_locked')}
  code,_=api.call('/rest/v1/properties?id=eq.'+pid,cleanup,restore,'PATCH')
  record('Seeded dummy property/rooms/references restored after browser test',code==200)
  (OUT/'browser-retained-objects.json').write_text(json.dumps({'tiny_private_dummy_upload_paths':objects},indent=2))

if __name__=='__main__':
 try:main()
 except Exception as e:
  print('STOP browser test:',type(e).__name__,'; last recorded check above identifies progress. No sensitive exception details printed.',flush=True)
  raise SystemExit(1)
