"""Exercise the actual vendored client and UI against an isolated HTTP API fixture.
All routes are intercepted. No requests reach Supabase, Zapier, or a live user account.
"""
from pathlib import Path
import base64
from email.parser import BytesParser
from email.policy import default as email_policy
import json
import mimetypes
import os
import shutil
import re
import time
import uuid
from urllib.parse import parse_qs, unquote, urlparse
from zipfile import ZipFile
from io import BytesIO
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://survey.test/property-survey/'
BACKEND = 'arnzqizcycesukplmvuc.supabase.co'
USER_ID = '00000000-0000-4000-8000-000000000001'
PHOTO = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=')

def jwt():
    enc = lambda obj: base64.urlsafe_b64encode(json.dumps(obj).encode()).rstrip(b'=').decode()
    return enc({'alg':'HS256','typ':'JWT'}) + '.' + enc({'sub':USER_ID,'aud':'authenticated','role':'authenticated',
        'exp':int(time.time())+3600,'email':'urbanfolduk@gmail.com'}) + '.test-signature'

class Fixture:
    def __init__(self):
        self.tables = {table:[] for table in ['properties','extensions','rooms','exterior_photos','extension_photos','sketch_photos','room_photos']}
        self.objects = {}
        self.emails = 0
        self.public_reads = 0
        self.signatures = 0
        self.unexpected = []
        self.fail = None
        self.corrupt_reads = False
        self.token = jwt()
        self.user = {'id':USER_ID,'aud':'authenticated','role':'authenticated','email':'urbanfolduk@gmail.com',
                     'email_confirmed_at':'2026-10-22T00:00:00Z','app_metadata':{'provider':'email'},'user_metadata':{},
                     'created_at':'2026-10-22T00:00:00Z','identities':[]}
    def route(self, route):
        req = route.request
        u = urlparse(req.url)
        headers = {'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*','Access-Control-Allow-Methods':'*'}
        def reply(data, status=200):
            route.fulfill(status=status,body=json.dumps(data),headers=headers,content_type='application/json')
        if req.method == 'OPTIONS':
            return reply({})
        if u.hostname == 'survey.test':
            relative = unquote(u.path.removeprefix('/property-survey/')) or 'index.html'
            path = (ROOT / relative).resolve()
            if ROOT not in path.parents or not path.is_file():
                return route.fulfill(status=404,body='Not found')
            return route.fulfill(body=path.read_bytes(),content_type=mimetypes.guess_type(str(path))[0] or 'application/octet-stream')
        if u.hostname == 'hooks.zapier.com':
            self.emails += 1
            return reply({'status':'success'})
        if u.hostname != BACKEND:
            self.unexpected.append(req.url)
            return route.abort()
        if u.path.startswith('/auth/v1/'):
            if u.path.endswith('/token'):
                return reply({'access_token':self.token,'token_type':'bearer','expires_in':3600,'expires_at':int(time.time())+3600,
                              'refresh_token':'fixture-refresh-token','user':self.user})
            if u.path.endswith('/user'):
                return reply(self.user)
            if u.path.endswith('/logout'):
                return reply({})
            self.unexpected.append(u.path)
            return reply({'message':'Unsupported fixture auth path'},404)
        signed_read = req.method == 'GET' and u.path.startswith('/storage/v1/object/sign/') and parse_qs(u.query).get('token') == ['fixture-signed']
        if not signed_read and req.headers.get('authorization') != 'Bearer '+self.token:
            return reply({'message':'not authenticated','code':'PGRST301'},401)
        if u.path.startswith('/storage/v1/object/public/'):
            self.public_reads += 1
            return reply({'message':'Bucket is private'},403)
        if u.path.startswith('/storage/v1/object/sign/'):
            rest = unquote(u.path.split('/storage/v1/object/sign/',1)[1])
            bucket, _, path = rest.partition('/')
            if req.method == 'POST':
                paths = req.post_data_json.get('paths', [path])
                results=[]
                for item in paths:
                    if (bucket,item) not in self.objects:
                        results.append({'path':item,'error':'Object not found'})
                    else:
                        self.signatures += 1
                        results.append({'path':item,'signedURL':f'/object/sign/{bucket}/{item}?token=fixture-signed'})
                return reply(results if 'paths' in req.post_data_json else {'signedURL':results[0].get('signedURL')})
            if req.method == 'GET' and (bucket,path) in self.objects:
                return route.fulfill(body=self.objects[(bucket,path)],content_type='image/jpeg',headers=headers)
            return reply({'message':'Object not found'},404)
        if u.path.startswith('/storage/v1/object/') and req.method == 'POST':
            rest=unquote(u.path.split('/storage/v1/object/',1)[1]);bucket,_,path=rest.partition('/')
            if self.fail == ('storage','POST'):
                return reply({'statusCode':'403','error':'Unauthorized','message':'upload denied'},403)
            if (bucket,path) in self.objects:
                return reply({'message':'Object already exists'},409)
            body = req.post_data_buffer or b''
            content_type = req.headers.get('content-type','')
            if content_type.startswith('multipart/form-data'):
                message = BytesParser(policy=email_policy).parsebytes(('Content-Type: '+content_type+'\r\nMIME-Version: 1.0\r\n\r\n').encode()+body)
                body = next(part.get_payload(decode=True) for part in message.iter_parts() if part.get_filename() is not None)
            assert body, 'upload had no image bytes'
            self.objects[(bucket,path)] = body
            return reply({'Key':bucket+'/'+path,'Id':str(uuid.uuid4())})
        if not u.path.startswith('/rest/v1/'):
            self.unexpected.append(u.path);return reply({'message':'Unsupported API path'},404)
        table=u.path.split('/rest/v1/',1)[1]
        if table not in self.tables:
            self.unexpected.append(table);return reply({'message':'Table missing'},404)
        if self.fail == ('properties','FINALIZE') and table=='properties' and req.method=='PATCH' and 'last_submitted_at' in req.post_data_json:
            return reply({'code':'42501','message':'completion marker denied'},403)
        if self.fail == (table,req.method):
            return reply({'code':'42501','message':'fixture permission denied'},403)
        params=parse_qs(u.query)
        def matches(row):
            for key,values in params.items():
                if key in ['select','order','limit','offset']:continue
                value=values[0]
                if value.startswith('eq.') and str(row.get(key)) != value[3:]:return False
                if value.startswith('in.(') and str(row.get(key)) not in value[4:-1].split(','):return False
            return True
        rows=[row for row in self.tables[table] if matches(row)]
        if req.method == 'POST':
            payload=req.post_data_json
            rows=[dict(row) for row in (payload if isinstance(payload,list) else [payload])]
            for row in rows:
                row.setdefault('id',str(uuid.uuid4()));row.setdefault('created_at', '2026-10-22T12:00:00Z')
                if table=='properties':row.setdefault('status','in_progress')
                if table=='extensions':
                    for field in ['width','length']:
                        if row.get(field) is not None:row[field]=float(row[field])
                if table=='properties' and row.get('user_id')!=USER_ID:return reply({'code':'42501','message':'owner mismatch'},403)
                self.tables[table].append(row)
        elif req.method == 'PATCH':
            for row in rows:row.update(req.post_data_json)
        elif req.method == 'DELETE':
            self.tables[table]=[row for row in self.tables[table] if row not in rows]
        rows=json.loads(json.dumps(rows))
        if self.corrupt_reads and table=='rooms' and req.method=='GET':
            for row in rows:row['dimensions']={}
        if 'order' in params:
            field,direction=params['order'][0].split('.')[:2]
            rows.sort(key=lambda row:row.get(field) or '',reverse=direction=='desc')
        if req.headers.get('accept') == 'application/vnd.pgrst.object+json':
            if len(rows)!=1:return reply({'code':'PGRST116','message':'Expected one row'},406)
            return reply(rows[0],201 if req.method=='POST' else 200)
        return reply(rows,201 if req.method=='POST' else 200)

def main():
    fixture=Fixture()
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium') or None,args=['--no-sandbox'])
        context=browser.new_context(accept_downloads=True)
        context.route('**/*',fixture.route)
        page=context.new_page()
        errors=[];dialogs=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.on('dialog',lambda dialog:(dialogs.append(dialog.message),print('Browser dialog:',dialog.message,flush=True),dialog.accept()))
        page.goto(ORIGIN)
        assert page.title()=='Urbanfold Property Survey'
        assert page.evaluate('!!window.supabase && !!window.JSZip && !!window.html2pdf')
        page.locator('#login-email').fill('urbanfolduk@gmail.com')
        page.locator('#login-password').fill('fixture-password-not-a-real-account')
        page.get_by_role('button',name='Log In',exact=True).click()
        expect(page.locator('#view-dashboard')).to_be_visible()
        page.get_by_role('button',name='+ Start New Survey').click()
        page.locator('#detail-name').fill('Browser test')
        page.locator('#detail-client-email').fill('fixture@example.test')
        page.locator('#detail-address').fill('TEST - automated fixture')
        page.locator('#detail-postcode').fill('AB1 2CD')
        page.get_by_role('button',name='Save & Continue',exact=True).click()
        expect(page.locator('#view-type')).to_be_visible()
        page.locator('#prop-type').select_option('detached')
        page.get_by_role('button',name='Continue to Exterior Photos',exact=True).click()
        expect(page.locator('#view-exterior')).to_be_visible(timeout=15000)
        assert fixture.emails==0
        photo={'name':'test.png','mimeType':'image/png','buffer':PHOTO}
        page.locator('#input-front').set_input_files(photo)
        expect(page.locator('#preview-front img')).to_have_count(1)
        page.get_by_role('button',name='Finish Existing Exterior',exact=False).click()
        expect(page.locator('#view-extension')).to_be_visible(timeout=15000)
        page.locator('input[name="ext-type"]').first.check()
        page.locator('#ext-description').fill('Test extension')
        page.locator('#ext-width').fill('3')
        page.locator('#ext-length').fill('4')
        page.locator('#input-extension-location').set_input_files(photo)
        expect(page.locator('#preview-extension-location img')).to_have_count(1)
        page.get_by_role('button',name='Continue to Interior',exact=False).click()
        expect(page.locator('#view-interior-sketch')).to_be_visible(timeout=15000)
        page.locator('#input-sketch').set_input_files(photo)
        expect(page.locator('#preview-sketch img')).to_have_count(1)
        page.get_by_role('button',name='Continue to Room Details',exact=False).click()
        expect(page.locator('#view-interior-rooms')).to_be_visible(timeout=15000)
        page.locator('.room-header').first.click()
        page.locator('#len-Porch').fill('4')
        page.locator('#wid-Porch').fill('3')
        page.locator('#hei-Porch').fill('2.4')
        page.locator('#input-Porch').set_input_files(photo)
        expect(page.locator('#preview-Porch img')).to_have_count(1)
        page.get_by_role('button',name='Save progress',exact=True).click()
        expect(page.locator('#loading')).to_be_hidden(timeout=15000)
        assert fixture.emails==0
        assert len(fixture.objects)==4
        assert len(fixture.tables['exterior_photos'])==1
        page.locator('#len-Porch').fill('4.5')
        page.reload()
        expect(page.locator('#view-dashboard')).to_be_visible()
        page.locator('.survey-item').first.click()
        expect(page.locator('#view-details')).to_be_visible(timeout=15000)
        assert page.locator('#len-Porch').input_value()=='4.5'
        assert 'Draft from this device' in page.locator('#survey-source').inner_text()
        page.evaluate("document.getElementById('len-Porch').value='4';document.getElementById('len-Porch').dispatchEvent(new Event('input',{bubbles:true}))")
        page.evaluate("showView('view-interior-rooms')")
        page.get_by_role('button',name='Save progress',exact=True).click()
        expect(page.locator('#loading')).to_be_hidden(timeout=15000)
        print('PASS newer device edits survive refresh even after earlier progress was saved to the cloud')
        # Verify all content without device state, as if opening from the GitHub Pages origin.
        page.evaluate('localStorage.clear()')
        page.reload()
        expect(page.locator('#view-auth')).to_be_visible()
        page.locator('#login-email').fill('urbanfolduk@gmail.com')
        page.locator('#login-password').fill('fixture-password-not-a-real-account')
        page.get_by_role('button',name='Log In',exact=True).click()
        expect(page.locator('#view-dashboard')).to_be_visible()
        page.locator('.survey-item').first.click()
        expect(page.locator('#view-details')).to_be_visible(timeout=15000)
        assert page.locator('#detail-address').input_value()=='TEST - automated fixture'
        assert page.locator('#ext-description').input_value()=='Test extension'
        assert page.locator('#ext-width').input_value()=='3'
        assert page.locator('#len-Porch').input_value()=='4'
        for section in ['front','extension-location','sketch','Porch']:
            assert page.locator('#preview-'+section+' img').count()==1
            page.wait_for_function('(id)=>document.querySelector("#preview-"+id+" img").complete && document.querySelector("#preview-"+id+" img").naturalWidth>0',arg=section)
        assert fixture.public_reads==0
        print('PASS real client login, per-section cloud saves, private photo rendering, recovery with all device state removed')
        # Legacy public URL references must still render through private signed URLs.
        row=fixture.tables['exterior_photos'][0]
        saved_reference=row['photo_url']
        bucket,path=saved_reference.removeprefix('storage://').split('/',1)
        row['photo_url']=f'https://{BACKEND}/storage/v1/object/public/{bucket}/{path}'
        page.get_by_role('button',name='Back to Dashboard',exact=True).click()
        page.locator('.survey-item').first.click()
        expect(page.locator('#view-details')).to_be_visible(timeout=15000)
        page.wait_for_function('document.querySelector("#preview-front img").naturalWidth>0')
        assert fixture.public_reads==0
        print('PASS existing public URL references are signed without changing or exposing private buckets')
        page.evaluate("showView('view-exterior')")
        page.get_by_role('button',name='Remove front photo 1',exact=True).click()
        page.get_by_role('button',name='Finish Existing Exterior',exact=False).click()
        expect(page.locator('#view-extension')).to_be_visible(timeout=15000)
        assert not fixture.tables['exterior_photos']
        page.evaluate("showView('view-exterior')")
        page.locator('#input-front').set_input_files(photo)
        expect(page.locator('#preview-front img')).to_have_count(1)
        page.get_by_role('button',name='Finish Existing Exterior',exact=False).click()
        expect(page.locator('#loading')).to_be_hidden(timeout=15000)
        assert len(fixture.tables['exterior_photos'])==1
        print('PASS deleting and replacing a saved photo updates cloud records')

        # Invalid responses and denied writes must never generate success/email.
        fixture.fail=('rooms','PATCH')
        page.evaluate("showView('view-interior-rooms')")
        page.get_by_role('button',name='Finish Survey & Submit to Cloud',exact=True).click()
        expect(page.locator('#loading')).to_be_hidden(timeout=15000)
        assert not page.locator('#view-success').is_visible()
        assert fixture.emails==0
        assert page.evaluate("!!localStorage.getItem('urbanfold_draft')")
        fixture.fail=('properties','FINALIZE')
        page.get_by_role('button',name='Finish Survey & Submit to Cloud',exact=True).click()
        expect(page.locator('#loading')).to_be_hidden(timeout=15000)
        assert not page.locator('#view-success').is_visible()
        assert fixture.emails==0
        assert page.evaluate("!!localStorage.getItem('urbanfold_draft')")
        fixture.fail=None
        fixture.corrupt_reads=True
        page.get_by_role('button',name='Finish Survey & Submit to Cloud',exact=True).click()
        expect(page.locator('#loading')).to_be_hidden(timeout=15000)
        assert not page.locator('#view-success').is_visible()
        assert fixture.emails==0
        fixture.corrupt_reads=False
        print('PASS actual-client permission errors and mismatching readback suppress success and email')
        page.get_by_role('button',name='Finish Survey & Submit to Cloud',exact=True).click()
        expect(page.locator('#view-success')).to_be_visible(timeout=15000)
        expect(page.locator('#notification-status')).to_contain_text('accepted')
        assert fixture.emails==1
        assert fixture.tables['properties'][0].get('last_submitted_at')
        assert not page.evaluate("localStorage.getItem('urbanfold_draft')")
        with page.expect_download(timeout=30000) as download:
            page.get_by_role('button',name='Download Measurements PDF',exact=True).click()
        pdf=Path(download.value.path()).read_bytes()
        assert pdf.startswith(b'%PDF-')
        page.get_by_role('button',name='Return to Dashboard',exact=True).click()
        with page.expect_download(timeout=15000) as download:
            page.get_by_role('button',name='Download Survey Pack (ZIP)',exact=True).first.click()
        with ZipFile(BytesIO(Path(download.value.path()).read_bytes())) as archive:
            assert len([name for name in archive.namelist() if name.endswith('.jpg')])==4
            report=next(name for name in archive.namelist() if name.endswith('survey_data.txt'))
            text = archive.read(report).decode()
            assert 'Test extension' in text
            assert 'PORCH' in text and 'Length: 4 m' in text and 'Height: 2.4 m' in text
            assert 'Bedroom-1' not in text and 'BEDROOM 1' not in text
            assert '{"shape"' not in text and '"len"' not in text
        assert len(fixture.objects)==5  # Removed photo bytes retained; its survey reference is deleted.
        assert not errors,errors
        assert not fixture.unexpected,fixture.unexpected
        print('PASS verified submission, one intercepted email, real PDF and ZIP containing all four photo categories')
        browser.close()

if __name__=='__main__':main()
