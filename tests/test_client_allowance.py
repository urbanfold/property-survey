"""Real browser/Supabase client for free allowance, purchase popup and review.
All requests intercepted; never creates a real checkout or takes a payment.
"""
import json
import os
import shutil
import uuid
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect
from test_browser_integration import Fixture, USER_ID, ORIGIN

class ClientFixture(Fixture):
    def __init__(self):
        super().__init__()
        self.user['email']='client@example.test'
        self.free_used=False
        self.credits=0
        self.checkouts=[]
        self.checkout_disabled=True
        self.migration_pending=False
    def route(self, route):
        req=route.request
        path=urlparse(req.url).path
        if urlparse(req.url).hostname=='checkout.stripe.com':
            return route.fulfill(body='<h1>Intercepted sandbox Checkout</h1>',content_type='text/html')
        def reply(body,status=200):
            return route.fulfill(status=status,body=json.dumps(body),content_type='application/json',headers={'Access-Control-Allow-Origin':'*'})
        if req.method!='OPTIONS' and path.endswith('/rpc/get_survey_allowance'):
            if self.migration_pending:return reply({'code':'PGRST202','message':'function not installed'},404)
            return reply({'can_create':not self.free_used or self.credits>0,'free_available':not self.free_used,'paid_credits':self.credits})
        if req.method!='OPTIONS' and path.endswith('/functions/v1/create-survey-checkout'):
            self.checkouts.append(req.post_data_json)
            if self.checkout_disabled:return reply({'error':'Payments are not available yet. Please contact survey@urbanfold.uk.'},503)
            return reply({'url':'https://checkout.stripe.com/c/pay/cs_test_Fixture','test_mode':True})
        if req.method=='POST' and path.endswith('/rest/v1/properties'):
            payload=req.post_data_json
            exists=any(row['id']==payload['id'] for row in self.tables['properties'])
            if not exists:
                if self.free_used and not self.credits:return reply({'code':'P0001','message':'URBANFOLD_SURVEY_LIMIT'},400)
                if self.free_used:self.credits-=1
                else:self.free_used=True
        return super().route(route)

def main():
    fixture=ClientFixture()
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium') or None,args=['--no-sandbox'])
        context=browser.new_context(viewport={'width':390,'height':844})
        context.route('**/*',fixture.route)
        errors=[]
        page=context.new_page()
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('dialog',lambda d:d.accept())
        page.goto(ORIGIN)
        page.locator('#login-email').fill('client@example.test')
        page.locator('#login-password').fill('fixture-password')
        page.get_by_role('button',name='Log In',exact=True).click()
        expect(page.locator('#view-dashboard')).to_be_visible()
        page.get_by_role('button',name='+ Start New Survey').click()
        expect(page.locator('#view-details')).to_be_visible()
        expect(page.locator('#additional-survey-dialog')).not_to_be_visible()
        page.locator('#detail-name').fill('Client Test')
        page.locator('#detail-client-email').fill('client@example.test')
        page.locator('#detail-address').fill('One Test Street')
        page.locator('#detail-postcode').fill('AB1 2CD')
        page.get_by_role('button',name='Save & Continue',exact=True).click()
        expect(page.locator('#view-type')).to_be_visible()
        assert len(fixture.tables['properties'])==1
        page.evaluate('loadDashboard()')
        page.get_by_role('button',name='+ Start New Survey').click()
        expect(page.locator('#additional-survey-dialog')).to_be_visible()
        expect(page.locator('#additional-survey-dialog')).to_contain_text('£6 once')
        expect(page.locator('#additional-survey-dialog')).to_contain_text('no recurring subscription')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.get_by_role('button',name='Buy one additional survey — £6',exact=True).click()
        expect(page.locator('#checkout-status')).to_contain_text('Payments are not available yet')
        assert len(fixture.checkouts)==1
        assert set(fixture.checkouts[0])=={'attempt_id'}
        assert uuid.UUID(fixture.checkouts[0]['attempt_id'])
        page.get_by_role('button',name='Continue existing surveys',exact=True).click()
        page.locator('.survey-item').first.click()
        expect(page.locator('#view-details')).to_be_visible()
        expect(page.locator('#detail-address')).to_have_value('One Test Street')
        print('PASS first survey has no paywall, second shows £6 one-off popup, unavailable payments are honest, existing survey remains accessible on mobile')

        # This is merely a navigation URL, not evidence of a real payment.
        page.goto(ORIGIN+'?payment=success&checkout_session_id=cs_live_Forged')
        expect(page.locator('#view-dashboard')).to_be_visible()
        expect(page.locator('#payment-notice')).to_contain_text('No additional survey credit')
        page.get_by_role('button',name='+ Start New Survey').click()
        expect(page.locator('#additional-survey-dialog')).to_be_visible()
        page.get_by_role('button',name='Continue existing surveys',exact=True).click()
        assert len(fixture.tables['properties'])==1
        fixture.checkout_disabled=False
        page.get_by_role('button',name='+ Start New Survey').click()
        page.get_by_role('button',name='Buy one additional survey — £6',exact=True).click()
        page.wait_for_url('https://checkout.stripe.com/**')
        expect(page.get_by_role('heading',name='Intercepted sandbox Checkout')).to_be_visible()
        page.goto(ORIGIN+'?payment=cancelled')
        expect(page.locator('#payment-notice')).to_contain_text('Checkout was cancelled')
        assert fixture.credits==0
        page.goto(ORIGIN+'?payment=success&checkout_session_id=cs_test_Fixture')
        expect(page.locator('#payment-notice')).to_contain_text('Test payments do not unlock live survey credits')
        assert fixture.credits==0
        page.evaluate('checkPurchasedCredit()')
        expect(page.locator('#payment-notice')).to_contain_text('No additional survey credit')
        fixture.credits=1  # Only the separate, tested server webhook may do this in production.
        page.get_by_role('button',name='Check payment confirmation',exact=True).click()
        expect(page.locator('#payment-notice')).to_contain_text('Payment confirmed')
        page.get_by_role('button',name='+ Start New Survey').click()
        expect(page.locator('#view-details')).to_be_visible()
        page.locator('#detail-name').fill('Client Test')
        page.locator('#detail-client-email').fill('client@example.test')
        page.locator('#detail-address').fill('Two Test Street')
        page.locator('#detail-postcode').fill('AB1 2CD')
        page.get_by_role('button',name='Save & Continue',exact=True).click()
        expect(page.locator('#view-type')).to_be_visible()
        assert fixture.credits==0 and len(fixture.tables['properties'])==2
        page.locator('#prop-type').select_option('detached')
        page.evaluate("document.querySelector('#len-Porch').value='4.37';document.querySelector('#wid-Porch').value='2.18';document.querySelector('#hei-Porch').value='2.4'")
        page.evaluate('openSurveyReview()')
        expect(page.locator('#view-review')).to_be_visible()
        expect(page.locator('#survey-review-content')).to_contain_text('Porch: 3 of 3 measurements recorded')
        expect(page.locator('#survey-review-content')).not_to_contain_text('4.37')
        assert fixture.emails==0
        assert not page.get_by_role('button',name='Download Measurements PDF',exact=True).is_visible()
        page.get_by_role('button',name='Edit rooms',exact=True).click()
        expect(page.locator('#view-interior-rooms')).to_be_visible()
        print('PASS forged success URL grants no credit; confirmed credit unlocks exactly one new property; client review shows completeness without measurement export')

        page.evaluate('loadDashboard()')
        # Rollout fallback allows genuinely new clients, but does not pretend a SQL limit is installed.
        fixture.migration_pending=True
        page.get_by_role('button',name='+ Start New Survey').click()
        expect(page.locator('#additional-survey-dialog')).to_be_visible()
        page.get_by_role('button',name='Continue existing surveys',exact=True).click()
        fixture.tables['properties']=[];fixture.free_used=False
        page.get_by_role('button',name='+ Start New Survey').click()
        expect(page.locator('#view-details')).to_be_visible()
        assert not errors,errors
        assert not fixture.unexpected,fixture.unexpected
        print('PASS staged SQL rollout preserves first-time client access')
        browser.close()

if __name__=='__main__':main()
