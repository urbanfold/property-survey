"""Isolated Chromium checks for different-user recovery and deliberate cross-tab logout."""
import os,shutil,uuid
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

        def login(tab=page):
            tab.locator('#login-email').fill(fixture.user['email'])
            tab.locator('#login-password').fill('fixture-only-password')
            tab.get_by_role('button',name='Log In',exact=True).click()
            expect(tab.locator('#view-dashboard')).to_be_visible(timeout=15000)

        login()
        page.get_by_role('button',name='+ Start New Survey').click()
        for field,value in [('name','Fixture'),('client-email','fixture@example.test'),('address','CONFIDENTIAL SITE'),('postcode','AB1 2CD')]:
            page.locator('#detail-'+field).fill(value)
        page.get_by_role('button',name='Save & Continue',exact=True).click()
        expect(page.locator('#view-type')).to_be_visible(timeout=15000)
        page.evaluate("showView('view-interior-rooms')")
        page.locator('.room-header').first.click()
        page.locator('#len-Porch').fill('9.876')
        page.evaluate("sb.auth._removeSession()")
        expect(page.locator('#view-auth')).to_be_visible(timeout=15000)
        assert page.evaluate('lockedSessionSurvey?.userId')==fixture.user['id']

        # Switch to a genuinely different identity: no recovery must be possible.
        original=dict(fixture.user)
        fixture.user={**fixture.user,'id':str(uuid.uuid4()),'email':'different-fixture@example.test'}
        login()
        assert page.evaluate('lockedSessionSurvey===null')
        assert page.locator('#detail-address').input_value()==''
        assert page.locator('#len-Porch').input_value()==''
        print('PASS different-user login discards previous account locked snapshot')

        # Return to original account (after deliberate signout), then open an active
        # survey in the first tab and sign out deliberately from a second tab.
        page.evaluate('handleLogout()')
        expect(page.locator('#view-auth')).to_be_visible(timeout=15000)
        fixture.user=original
        login()
        page.locator('.survey-item').first.click()
        expect(page.locator('#view-details')).to_be_visible(timeout=15000)
        page.evaluate("showView('view-interior-rooms')")
        page.locator('.room-header').first.click()
        page.locator('#len-Porch').fill('4.321')
        second=context.new_page()
        second.on('dialog',lambda dialog:dialog.accept())
        second.on('pageerror',lambda error:errors.append(str(error)))
        second.goto(ORIGIN)
        expect(second.locator('#view-dashboard')).to_be_visible(timeout=15000)
        second.evaluate('handleLogout()')
        expect(second.locator('#view-auth')).to_be_visible(timeout=15000)
        page.wait_for_function('currentUser===null && lockedSessionSurvey===null',timeout=15000)
        assert page.locator('#detail-address').input_value()==''
        assert page.locator('#len-Porch').input_value()==''
        assert not page.evaluate("Object.keys(localStorage).some(k=>k==='urbanfold_draft'||k.startsWith('urbanfold_draft_'))")
        assert not errors,errors
        assert not fixture.unexpected,fixture.unexpected
        print('PASS deliberate logout from another tab clears private UI and locked recovery')
        browser.close()

if __name__=='__main__':main()
