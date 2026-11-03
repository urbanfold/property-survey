"""Audit-only repros. All browser requests are intercepted; never contacts live services.
These assertions demonstrate findings in the existing code, not corrected behaviour.
Run: python audits/2026-11-03/reproduce_browser_findings.py
"""
from pathlib import Path
import json,os,shutil,sys,uuid
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tests'))
from test_browser_integration import Fixture,ORIGIN,PHOTO
from playwright.sync_api import sync_playwright,expect

def main():
    fixture=Fixture();findings=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium'),args=['--no-sandbox'])
        context=browser.new_context();context.route('**/*',fixture.route)
        page=context.new_page();page.on('dialog',lambda d:d.accept())
        page.goto(ORIGIN)
        page.locator('#login-email').fill(fixture.user['email']);page.locator('#login-password').fill('fixture-only-password')
        page.get_by_role('button',name='Log In',exact=True).click()
        expect(page.locator('#view-dashboard')).to_be_visible()
        page.get_by_role('button',name='+ Start New Survey').click()
        for key,value in [('name','Fixture private name'),('client-email','fixture-private@example.test'),('address','FIXTURE PRIVATE ADDRESS'),('postcode','AB1 2CD')]:
            page.locator('#detail-'+key).fill(value)
        page.get_by_role('button',name='Save & Continue',exact=True).click();expect(page.locator('#view-type')).to_be_visible()
        page.locator('#prop-type').select_option('detached');page.get_by_role('button',name='Continue to Exterior Photos',exact=True).click()
        expect(page.locator('#view-exterior')).to_be_visible(timeout=15000)
        page.locator('#input-front').set_input_files({'name':'fixture.png','mimeType':'image/png','buffer':PHOTO})
        expect(page.locator('#preview-front img')).to_have_count(1)
        page.wait_for_function("appState.photos.front?.[0]?.startsWith('data:')")
        awaitable='''async()=>{ await handleLogout();return {
          loggedOut:currentUser===null,
          retainedAddress:document.querySelector('#detail-address').value==='FIXTURE PRIVATE ADDRESS',
          retainedDraft:!!localStorage.getItem('urbanfold_draft'),
          retainedPhoto:!!appState.photos.front?.length,
          retainedImage:!!document.querySelector('#preview-front img')?.src
        }}'''
        result=page.evaluate(awaitable)
        assert all(result.values()),result
        findings.append({'id':'BROWSER-01','finding':'Logout retains prior user fields, photo data, DOM thumbnails and local draft','evidence':result})
        # No real email: fixture.route intercepts every request to the third party.
        before=fixture.emails
        page.evaluate('''async()=>{currentPropertyId='fixture-arbitrary-property';
          const forged={details:{clientEmail:'fixture-spoof@example.test',address:'FIXTURE FORGED',name:'Fixture'}};
          await notifySurveySaved(forged);
        }''')
        assert fixture.emails==before+1
        findings.append({'id':'BROWSER-02','finding':'Notification code creates an unsigned webhook request without a signed-in user or saved submission','evidence':{'requests_intercepted':1,'live_requests':0,'currentUser':page.evaluate('currentUser')}})
        # Stale identity after auth event in another tab: use real auth client event.
        fixture.user={**fixture.user,'id':str(uuid.uuid4()),'email':'fixture-second@example.test'}
        page.locator('#login-email').fill(fixture.user['email']);page.locator('#login-password').fill('fixture-second-password')
        page.get_by_role('button',name='Log In',exact=True).click();expect(page.locator('#view-dashboard')).to_be_visible()
        page.evaluate("sb.auth.signOut({scope:'local'})")
        signed_out=page.evaluate('''async()=>({authSession:(await sb.auth.getSession()).data.session,
          cachedUser:!!currentUser,dashboard:document.querySelector('#view-dashboard').classList.contains('active')})''')
        assert signed_out['authSession'] is None and signed_out['cachedUser'] and signed_out['dashboard'],signed_out
        findings.append({'id':'BROWSER-03','finding':'SIGNED_OUT event does not invalidate application identity/UI state','evidence':signed_out})
        # A stale async read resolves after logout and repopulates former user's data.
        page.evaluate('''() => {
          currentUser={id:'fixture-old-user',email:'old@example.test'};
          window.auditOriginalFetch=fetchSurveySnapshot;
          fetchSurveySnapshot=()=>new Promise(resolve=>{window.auditResolveSurvey=resolve;});
          window.auditPendingResume=resumeSurvey('fixture-old-property');
        }''')
        page.evaluate('handleLogout()')
        page.evaluate('''async()=>{
          auditResolveSurvey({snapshot:{propertyId:'fixture-old-property',userId:'fixture-old-user',view:'view-details',
            details:{name:'Old fixture',clientEmail:'old@example.test',address:'LATE PRIVATE FIXTURE',postcode:'AB1 2CD'},
            propType:'detached',extension:{types:[]},rooms:{},appState:{photos:{},roomPhotos:{}}},hasCloudProgress:true});
          await auditPendingResume;fetchSurveySnapshot=auditOriginalFetch;
        }''')
        race=page.evaluate('''()=>({loggedOut:currentUser===null,privateViewVisible:document.querySelector('#view-details').classList.contains('active'),
           oldAddressRestored:document.querySelector('#detail-address').value==='LATE PRIVATE FIXTURE'})''')
        assert all(race.values()),race
        findings.append({'id':'BROWSER-04','finding':'In-flight survey fetch can restore a private view after logout','evidence':race})
        assert not fixture.unexpected,fixture.unexpected
        browser.close()
    print(json.dumps({'live_requests':0,'results':findings},indent=2))

if __name__=='__main__':main()
