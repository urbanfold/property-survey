"""Isolated Chromium check for late survey results after deliberate signout."""
import os,shutil
from playwright.sync_api import sync_playwright,expect
from test_browser_integration import Fixture,ORIGIN

def main():
    fixture=Fixture()
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium') or None,args=['--no-sandbox'])
        context=browser.new_context()
        context.route('**/*',fixture.route)
        page=context.new_page()
        page.on('dialog',lambda dialog:dialog.accept())
        errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(ORIGIN)
        page.locator('#login-email').fill(fixture.user['email'])
        page.locator('#login-password').fill('fixture-only-password')
        page.get_by_role('button',name='Log In',exact=True).click()
        expect(page.locator('#view-dashboard')).to_be_visible(timeout=15000)
        page.get_by_role('button',name='+ Start New Survey').click()
        for field,value in [('name','Fixture'),('client-email','fixture@example.test'),('address','PRIVATE RACE CASE'),('postcode','AB1 2CD')]:
            page.locator('#detail-'+field).fill(value)
        page.get_by_role('button',name='Save & Continue',exact=True).click()
        expect(page.locator('#view-type')).to_be_visible(timeout=15000)
        # The survey creation wizard has no Back to Dashboard button on this view.
        # Save the actual fixture property ID, then use the app's dashboard function.
        property_id=page.evaluate('currentPropertyId')
        page.evaluate('loadDashboard()')
        expect(page.locator('#view-dashboard')).to_be_visible(timeout=15000)

        # Suspend the cloud snapshot resolution while the original user signs out.
        page.evaluate("""propertyId => {
            window._oldFetchSnapshot = fetchSurveySnapshot;
            window._resolveStaleSurvey = null;
            fetchSurveySnapshot = () => new Promise(resolve => { window._resolveStaleSurvey=resolve; });
            window._staleResume = resumeSurvey(propertyId);
        }""",property_id)
        page.wait_for_function('typeof window._resolveStaleSurvey === "function"')
        page.evaluate('handleLogout()')
        expect(page.locator('#view-auth')).to_be_visible(timeout=12000)
        page.evaluate("""() => {
            window._resolveStaleSurvey({snapshot:{
                propertyId:'fake-property',userId:'old-user',view:'view-details',
                details:{name:'STALE PRIVATE DATA',address:'STALE PRIVATE ADDRESS',clientEmail:'x@example.test',postcode:'AA1 1AA',notes:''},
                appState:{photos:{},roomPhotos:{}},rooms:{},extension:{types:[],description:'',width:'',length:''},propType:''
            },hasCloudProgress:true});
            fetchSurveySnapshot = window._oldFetchSnapshot;
        }""")
        page.evaluate('window._staleResume')
        assert page.locator('#detail-address').input_value()==''
        assert page.locator('#view-auth').is_visible()
        assert page.evaluate('currentUser===null && currentPropertyId===null')
        assert not errors,errors
        assert not fixture.unexpected,fixture.unexpected
        print('PASS late survey result does not restore private address after deliberate logout')
        browser.close()

if __name__=='__main__':main()
