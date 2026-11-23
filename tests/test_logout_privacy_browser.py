"""Real Chromium signout privacy acceptance against the isolated local API fixture.
No production Supabase, live user, or payment service is contacted.
"""
import os, shutil
from playwright.sync_api import sync_playwright,expect
from test_browser_integration import Fixture,ORIGIN

def main():
    fixture=Fixture()
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(executable_path=os.environ.get("CHROMIUM_PATH") or shutil.which("chromium") or None,args=["--no-sandbox"])
        context=browser.new_context()
        context.route("**/*",fixture.route)
        page=context.new_page()
        errors=[]
        decisions={"accept":False}
        page.on("pageerror",lambda error:errors.append(str(error)))
        page.on("dialog",lambda dialog:dialog.accept() if decisions["accept"] else dialog.dismiss())
        page.goto(ORIGIN)
        page.locator("#login-email").fill("urbanfolduk@gmail.com")
        page.locator("#login-password").fill("fixture-password-not-a-real-account")
        page.get_by_role("button",name="Log In",exact=True).click()
        expect(page.locator("#view-dashboard")).to_be_visible()
        page.get_by_role("button",name="+ Start New Survey").click()
        page.locator("#detail-name").fill("Offline logout security case")
        page.locator("#detail-client-email").fill("fixture@example.test")
        page.locator("#detail-address").fill("FIXTURE PRIVATE ADDRESS")
        page.locator("#detail-postcode").fill("AB1 2CD")
        page.get_by_role("button",name="Save & Continue",exact=True).click()
        expect(page.locator("#view-type")).to_be_visible()
        # Make private unsaved data, then cancel the deliberate signout.
        page.locator("#prop-type").select_option("detached")
        page.evaluate("saveDraft()")
        assert page.evaluate("!!localStorage.getItem('urbanfold_draft')")
        page.evaluate("handleLogout()")
        assert page.evaluate("!!currentUser")
        assert page.evaluate("!!localStorage.getItem('urbanfold_draft')")
        expect(page.locator("#view-type")).to_be_visible()
        # Confirm the same logout. It must clear the current page, local drafts and
        # any private state, while cloud-saved properties stay untouched.
        decisions["accept"]=True
        page.evaluate("handleLogout()")
        expect(page.locator("#view-auth")).to_be_visible(timeout=12000)
        assert not page.evaluate("currentUser"),"A signed-out user remained in page memory"
        assert page.evaluate("currentPropertyId === null && appState.photos && Object.keys(appState.photos).length===0")
        assert page.evaluate("Object.keys(localStorage).every(k=>k!=='urbanfold_draft' && !k.startsWith('urbanfold_draft_'))")
        assert page.locator("#detail-address").input_value()==""
        assert page.locator("#login-password").input_value()==""
        expect(page.locator("#login-notice")).to_contain_text("Private device drafts were cleared")
        # Previously saved cloud data must still be available when signing in again.
        page.locator("#login-email").fill("urbanfolduk@gmail.com")
        page.locator("#login-password").fill("fixture-password-not-a-real-account")
        page.get_by_role("button",name="Log In",exact=True).click()
        expect(page.locator("#view-dashboard")).to_be_visible(timeout=15000)
        expect(page.locator(".survey-item").first).to_be_visible()
        # Click the survey heading; the card also contains dedicated export buttons.
        page.locator(".survey-item").first.locator("h3").click()
        expect(page.locator("#view-details")).to_be_visible(timeout=15000)
        assert page.locator("#detail-address").input_value()=="FIXTURE PRIVATE ADDRESS"
        assert not errors, errors
        assert not fixture.unexpected, fixture.unexpected
        print("PASS browser: cancelled logout, confirmed cleanup, cleared device drafts, cloud data recovered")
        browser.close()

if __name__=="__main__":main()
