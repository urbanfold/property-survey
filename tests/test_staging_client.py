"""Generated local staging copy, intercepted HTTP only. Does not test live RLS."""
from pathlib import Path
import base64, json, mimetypes, shutil, sys
from urllib.parse import urlparse
sys.path.insert(0,str(Path(__file__).resolve().parent))
import test_browser_integration as fixture_module
from playwright.sync_api import sync_playwright, expect

ROOT=Path('/workspace/urbanfold-staging-client')
STAGING='hexhtduvqzleoazusskh'

def anon_key(ref=STAGING,role='anon'):
    encode=lambda data:base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b'=').decode()
    return encode({'alg':'HS256'})+'.'+encode({'ref':ref,'role':role})+'.fixture-only'

def main():
    fixture_module.BACKEND=STAGING+'.supabase.co'
    f=fixture_module.Fixture()
    f.user={**f.user,'id':'9036b71c-4f09-4d1b-9dce-519533c4001e','email':'staging-owner-a@example.invalid'}
    f.tables['properties']=[{'id':'f0000000-0000-4000-8000-000000000001','user_id':f.user['id'],
       'address':'DUMMY PROPERTY A - NOT A REAL ADDRESS','postcode':'ZZ1 1ZZ','created_at':'2026-11-04T00:00:00Z'}]
    requests=[]
    def route(r):
        u=urlparse(r.request.url)
        if u.hostname=='localhost':
            path=ROOT/(u.path.lstrip('/') or 'index.html')
            if path.is_file() and ROOT in path.resolve().parents:
                return r.fulfill(body=path.read_bytes(),content_type=mimetypes.guess_type(str(path))[0] or 'application/octet-stream')
            return r.fulfill(status=404,body='Not found')
        requests.append(u.hostname)
        return f.route(r)
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
        context=browser.new_context();context.route('**/*',route)
        page=context.new_page();page.on('dialog',lambda d:d.accept())
        page.goto('http://localhost:8794/')
        assert page.locator('#staging-app').is_hidden()
        for key in [anon_key('wrong-project'),anon_key(role='service_role'),'sb_secret_fixture']:
            page.locator('#staging-public-key').fill(key);page.locator('#staging-start').click()
            assert page.locator('#staging-app').is_hidden()
            assert page.locator('#staging-config-status').inner_text()
        assert not requests
        page.locator('#staging-public-key').fill(anon_key());page.locator('#staging-start').click()
        expect(page.locator('#view-auth')).to_be_visible()
        assert page.locator('#staging-public-key').input_value()==''
        page.locator('#login-email').fill(f.user['email']);page.locator('#login-password').fill('dummy-fixture-password')
        page.get_by_role('button',name='Log In',exact=True).click()
        expect(page.locator('#view-dashboard')).to_be_visible()
        expect(page.locator('.survey-item')).to_have_count(1)
        page.locator('.survey-item').click();expect(page.locator('#view-details')).to_be_visible()
        assert page.locator('#detail-address').input_value()=='DUMMY PROPERTY A - NOT A REAL ADDRESS'
        # CSP must reject accidental network calls to another project before any HTTP route receives them.
        blocked=page.evaluate("async()=>{try{await fetch('https://wrong-project.supabase.co/auth/v1/user');return false;}catch{return true;}}")
        assert blocked and 'wrong-project.supabase.co' not in requests
        assert set(requests)=={STAGING+'.supabase.co'},requests
        assert not f.unexpected,f.unexpected
        browser.close()
    assert 'arnzqizcycesukplmvuc' not in (ROOT/'app.js').read_text()
    print('PASS generated local staging key/role/project guards, key-field clearing, staging-only Auth/login/survey opening, and CSP external-backend denial; all HTTP intercepted')
    print('No live login, SQL, API or deployment. Windows PowerShell launcher not executed on this Linux host; real-service account isolation remains unverified.')

if __name__=='__main__':main()
