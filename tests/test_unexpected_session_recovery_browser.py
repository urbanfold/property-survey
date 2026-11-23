"""Verify tab-only recovery after unexpected session loss with a fully isolated browser fixture."""
import os,shutil
from playwright.sync_api import sync_playwright,expect
from test_browser_integration import Fixture,ORIGIN

def main():
    fixture=Fixture()
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium') or None,args=['--no-sandbox'])
        context=browser.new_context()
        context.route('**/*',fixture.route)
        page=context.new_page()
        page.on('dialog',lambda dialog:dialog.accept())
        errors=[]
        page.on('pageerror',lambda error:errors.append(str(error)))
        page.goto(ORIGIN)
        def sign_in():
            page.locator('#login-email').fill(fixture.user['email'])
            page.locator('#login-password').fill('fixture-only-password')
            page.get_by_role('button',name='Log In',exact=True).click()
            expect(page.locator('#view-dashboard')).to_be_visible(timeout=15000)
        sign_in()
        page.get_by_role('button',name='+ Start New Survey').click()
        for field,value in [('name','Fixture'),('client-email','fixture@example.test'),('address','FIXTURE PRIVATE RECOVERY'),('postcode','AB1 2CD')]:
            page.locator('#detail-'+field).fill(value)
        page.get_by_role('button',name='Save & Continue',exact=True).click()
        expect(page.locator('#view-type')).to_be_visible()
        page.locator('#prop-type').select_option('detached')
        page.evaluate("showView('view-interior-rooms')")
        page.locator('.room-header').first.click()
        page.locator('#len-Porch').fill('7.321')
        property_id=page.evaluate('currentPropertyId')
        assert page.evaluate("!!localStorage.getItem('urbanfold_draft')")
        page.evaluate("sb.auth._removeSession()")
        expect(page.locator('#view-auth')).to_be_visible(timeout=15000)
        assert page.locator('#len-Porch').input_value()==''
        assert page.locator('#detail-address').input_value()==''
        assert page.evaluate("lockedSessionSurvey?.draft.rooms?.Porch?.len")=='7.321'
        assert not page.evaluate("Object.keys(localStorage).some(k=>k==='urbanfold_draft'||k.startsWith('urbanfold_draft_'))")
        assert 'same account' in page.locator('#login-notice').inner_text()

        # Deny access to the saved property on the newly authenticated token.
        def blocked(route):
            if 'select=id&' in route.request.url:
                route.fulfill(status=403,body='{"message":"Access denied"}',content_type='application/json',headers={'Access-Control-Allow-Origin':'*'})
            else:fixture.route(route)
        context.route('**/rest/v1/properties?*',blocked)
        page.locator('#login-email').fill(fixture.user['email'])
        page.locator('#login-password').fill('fixture-only-password')
        page.get_by_role('button',name='Log In',exact=True).click()
        expect(page.get_by_role('button',name='Retry pending-work recovery')).to_be_visible(timeout=15000)
        assert page.locator('#len-Porch').input_value()==''
        assert page.evaluate('!!lockedSessionSurvey')
        context.unroute('**/rest/v1/properties?*',blocked)
        page.get_by_role('button',name='Retry pending-work recovery').click()
        expect(page.locator('#view-interior-rooms')).to_be_visible(timeout=15000)
        assert page.locator('#len-Porch').input_value()=='7.321'
        assert page.evaluate('lockedSessionSurvey===null')
        assert page.evaluate('currentPropertyId')==property_id
        assert 'Pending edits recovered' in page.locator('#survey-source').inner_text()
        page.get_by_role('button',name='Save progress',exact=True).click()
        expect(page.locator('#loading')).to_be_hidden(timeout=15000)
        assert not errors,errors
        assert not fixture.unexpected,fixture.unexpected
        print('PASS isolated browser: expired session hides private data; denied same-user access blocks; reverified same-user recovers latest measurement')
        browser.close()

if __name__=='__main__':main()
