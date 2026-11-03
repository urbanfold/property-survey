"""F01 regressions using real client with intercepted Auth/REST; no live requests.
Default draft policy proposed for approval: logout/session loss clears device drafts.
"""
from pathlib import Path
import json,os,shutil,sys,uuid
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_browser_integration import Fixture,ORIGIN,PHOTO,USER_ID
from playwright.sync_api import sync_playwright,expect

def main():
    fixture=Fixture();findings=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium'),args=['--no-sandbox'])
        context=browser.new_context();context.route('**/*',fixture.route)
        page=context.new_page();decisions={'accept':True};page.on('dialog',lambda d:d.accept() if decisions['accept'] else d.dismiss())
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
        decisions['accept']=False
        page.evaluate('handleLogout()')
        assert page.evaluate('!!currentUser && !!localStorage.getItem("urbanfold_draft")')
        decisions['accept']=True
        awaitable='''async()=>{ await handleLogout();return {
          loggedOut:currentUser===null,
          retainedAddress:document.querySelector('#detail-address').value==='FIXTURE PRIVATE ADDRESS',
          retainedDraft:!!localStorage.getItem('urbanfold_draft'),
          retainedPhoto:!!appState.photos.front?.length,
          retainedImage:!!document.querySelector('#preview-front img')?.src
        }}'''
        result=page.evaluate(awaitable)
        assert result['loggedOut'] and not any(value for key,value in result.items() if key!='loggedOut'),result
        findings.append({'id':'BROWSER-01','result':'PASS: logout clears prior fields, photos, thumbnails and drafts','evidence':result})
        # Stale identity after auth event in another tab: use real auth client event.
        fixture.user={**fixture.user,'id':str(uuid.uuid4()),'email':'fixture-second@example.test'}
        page.locator('#login-email').fill(fixture.user['email']);page.locator('#login-password').fill('fixture-second-password')
        page.get_by_role('button',name='Log In',exact=True).click();expect(page.locator('#view-dashboard')).to_be_visible()
        page.evaluate("sb.auth.signOut({scope:'local'})")
        signed_out=page.evaluate('''async()=>({authSession:(await sb.auth.getSession()).data.session,
          cachedUser:!!currentUser,dashboard:document.querySelector('#view-dashboard').classList.contains('active')})''')
        assert signed_out['authSession'] is None and not signed_out['cachedUser'] and not signed_out['dashboard'],signed_out
        findings.append({'id':'BROWSER-03','result':'PASS: SIGNED_OUT invalidates application identity/UI state','evidence':signed_out})
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
        assert race['loggedOut'] and not race['privateViewVisible'] and not race['oldAddressRestored'],race
        findings.append({'id':'BROWSER-04','result':'PASS: in-flight survey fetch cannot restore a view after logout','evidence':race})
        # A signed-photo response that arrives after logout cannot refill caches.
        page.evaluate('''()=>{
          currentUser={id:'fixture-owner',email:'fixture@example.test'};
          window.auditOriginalStorage=sb.storage.from.bind(sb.storage);
          sb.storage.from=()=>({createSignedUrls:()=>new Promise(resolve=>window.auditResolveSign=resolve)});
          window.auditPendingSign=preparePhotoLinks({appState:{photos:{front:['storage://exterior-photos/fixture/photo.jpg']},roomPhotos:{}}}).catch(()=>{});
        }''')
        page.evaluate('handleLogout()')
        page.evaluate('''async()=>{
          auditResolveSign({data:[{path:'fixture/photo.jpg',signedUrl:'https://fixture.test/private.jpg'}],error:null});
          await auditPendingSign;sb.storage.from=auditOriginalStorage;
        }''')
        assert page.evaluate('signedPhotoUrls.size')==0
        # Account switch in another actual browser tab uses the client's Auth broadcast.
        fixture.user={**fixture.user,'id':USER_ID,'email':'urbanfolduk@gmail.com'}
        page.locator('#login-email').fill(fixture.user['email']);page.locator('#login-password').fill('fixture-only-password')
        page.get_by_role('button',name='Log In',exact=True).click()
        expect(page.locator('#view-dashboard')).to_be_visible()
        second=context.new_page();second.goto(ORIGIN)
        expect(second.locator('#view-dashboard')).to_be_visible()
        page.locator('.survey-item').first.click()
        expect(page.locator('#view-details')).to_be_visible()
        assert page.locator('#detail-address').input_value()=='FIXTURE PRIVATE ADDRESS'
        second_user=str(uuid.uuid4())
        fixture.user={**fixture.user,'id':second_user,'email':'professional-b@example.test'}
        second.evaluate("sb.auth.signInWithPassword({email:'professional-b@example.test',password:'fixture-b-password'})")
        page.wait_for_function('(id)=>currentUser?.id===id',arg=second_user)
        expect(page.locator('#view-dashboard')).to_be_visible()
        assert page.locator('#detail-address').input_value()==''
        assert not page.evaluate("loadDraft(JSON.stringify({propertyId:'fixture-other',userId:'fixture-old-user',details:{address:'FORGED'},rooms:{},appState:{photos:{},roomPhotos:{}}}))")
        second.close()
        assert not fixture.unexpected,fixture.unexpected
        browser.close()
    print(json.dumps({'live_requests':0,'results':findings},indent=2))

if __name__=='__main__':main()
