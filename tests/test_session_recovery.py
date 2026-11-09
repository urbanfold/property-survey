"""F01 expiry recovery with the real browser/client and intercepted HTTP only.
No live accounts or services; temporary snapshots must never persist while locked.
"""
from pathlib import Path
import json, os, shutil, sys, uuid
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_browser_integration import Fixture, ORIGIN, PHOTO
from playwright.sync_api import sync_playwright, expect


def main():
    fixture = Fixture()
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium'), args=['--no-sandbox'])
        context = browser.new_context()
        context.route('**/*', fixture.route)
        page = context.new_page()
        page.on('dialog', lambda d: d.dismiss() if d.type == 'beforeunload' else d.accept())
        page.goto(ORIGIN)

        def login():
            page.locator('#login-email').fill(fixture.user['email'])
            page.locator('#login-password').fill('fixture-password')
            page.get_by_role('button', name='Log In', exact=True).click()

        def pending(value='6.789'):
            page.evaluate('''value => {
                showView('view-interior-rooms');
                const el=document.querySelector('[id^="len-"]'); el.value=value;
                el.dispatchEvent(new Event('input',{bubbles:true}));
            }''', value)

        def expire():
            page.evaluate('sb.auth._removeSession()')
            expect(page.locator('#view-auth')).to_be_visible()

        login()
        expect(page.locator('#view-dashboard')).to_be_visible()
        page.get_by_role('button', name='+ Start New Survey').click()
        for key, value in [('name','Fixture'),('client-email','fixture-client@example.test'),('address','PRIVATE RECOVERY SITE'),('postcode','AB1 2CD')]:
            page.locator('#detail-'+key).fill(value)
        page.get_by_role('button', name='Save & Continue', exact=True).click()
        expect(page.locator('#view-type')).to_be_visible()
        property_id = page.evaluate('currentPropertyId')
        pending()
        assert page.locator('#save-status').get_attribute('data-state') == 'unsaved'
        expect(page.locator('#save-status')).to_have_attribute('data-state','device')
        assert 'device only' in page.locator('#save-status').inner_text()
        page.evaluate('''() => {
            window.originalDraftSetItem=Storage.prototype.setItem;
            Storage.prototype.setItem=function(key,value){if(key.startsWith('urbanfold_draft')) throw Error('fixture quota');return originalDraftSetItem.call(this,key,value);};
            saveDraft();
        }''')
        assert page.locator('#save-status').get_attribute('data-state') == 'unsaved'
        assert 'Unsaved changes' in page.locator('#save-status').inner_text()
        page.evaluate('Storage.prototype.setItem=originalDraftSetItem;saveDraft()')
        original = page.evaluate("localStorage.getItem('urbanfold_draft')")
        page.evaluate('sb.auth.refreshSession()')
        assert page.evaluate("localStorage.getItem('urbanfold_draft')") == original
        assert page.locator('[id^="len-"]').first.input_value() == '6.789'
        results.append('PASS real-client normal token refresh preserves pending measurements')

        # The real Auth client retries a temporary refresh failure without SIGNED_OUT.
        def unavailable(route):
            route.fulfill(status=503, body='{"message":"Temporarily unavailable"}', content_type='application/json', headers={'Access-Control-Allow-Origin':'*'})
        context.route('**/auth/v1/token?grant_type=refresh_token', unavailable)
        refresh = page.evaluate('''async()=>{const r=await sb.auth.refreshSession();return {error:!!r.error,user:currentUser?.id,draft:localStorage.getItem('urbanfold_draft')};}''')
        assert refresh['error'] and refresh['user'] == fixture.user['id'] and refresh['draft'] == original
        context.unroute('**/auth/v1/token?grant_type=refresh_token', unavailable)
        results.append('PASS temporary Auth refresh failure preserves identity, private view and draft')

        # Transport failure during save must leave both visible edits and a device draft.
        def offline(route):
            route.abort('internetdisconnected')
        context.route('**/rest/v1/**', offline)
        page.evaluate('saveCloudProgress()')
        assert page.locator('[id^="len-"]').first.input_value() == '6.789'
        assert page.evaluate("!!localStorage.getItem('urbanfold_draft')")
        assert 'failed' in page.locator('#save-status').inner_text()
        context.unroute('**/rest/v1/**', offline)
        results.append('PASS failed network save retains measurements and distinguishes cloud failure')

        # Same authenticated ID with an updated email must not clear or switch views.
        fixture.user = {**fixture.user, 'email':'updated-fixture@example.test'}
        page.evaluate('(user)=>sb.auth._notifyAllSubscribers("USER_UPDATED",{user},false)',fixture.user)
        assert page.evaluate('currentUser.email') == fixture.user['email']
        assert page.locator('[id^="len-"]').first.input_value() == '6.789'
        assert page.evaluate("!!localStorage.getItem('urbanfold_draft')")
        results.append('PASS same-ID email update preserves pending edits')

        # No debounce wait: capture the very latest value synchronously on expiry.
        pending('7.321')
        page.evaluate('''() => {
            document.getElementById('prop-type').value='detached';
            appState.photos.front=['data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII='];
        }''')
        expire()
        assert 'Do not close or refresh' in page.locator('#login-notice').inner_text()
        assert page.evaluate("(()=>{const e=new Event('beforeunload',{cancelable:true});window.dispatchEvent(e);return e.defaultPrevented;})()")
        assert page.locator('#detail-address').input_value() == ''
        assert page.locator('[id^="len-"]').first.input_value() == ''
        assert page.evaluate("!Object.keys(localStorage).some(k=>k.startsWith('urbanfold_draft'))")
        assert page.evaluate("lockedSurveyRecovery.snapshot.rooms[roomId(roomList[0])].len") == '7.321'
        page.evaluate("sb.auth._notifyAllSubscribers('SIGNED_OUT',null,false)")
        assert page.evaluate('!!lockedSurveyRecovery')
        results.append('PASS expiry hides private DOM, clears persistent drafts, captures immediate edit in memory only')

        # Deny property access on the new caller token: never show the memory draft.
        def denied(route):
            if 'select=id&' in route.request.url:
                route.fulfill(status=403,body='{"message":"denied"}',content_type='application/json',headers={'Access-Control-Allow-Origin':'*'})
            else:
                fixture.route(route)
        context.route('**/rest/v1/properties?*', denied)
        login()
        expect(page.get_by_role('button',name='Retry pending-work recovery')).to_be_visible()
        assert page.locator('#detail-address').input_value() == ''
        assert page.evaluate('!!lockedSurveyRecovery')
        assert page.evaluate("!localStorage.getItem('urbanfold_draft')")
        context.unroute('**/rest/v1/properties?*', denied)
        page.get_by_role('button',name='Retry pending-work recovery').click()
        expect(page.locator('#view-interior-rooms')).to_be_visible()
        assert page.locator('[id^="len-"]').first.input_value() == '7.321'
        assert page.locator('#detail-address').input_value() == 'PRIVATE RECOVERY SITE'
        assert page.evaluate('lockedSurveyRecovery===null')
        assert page.evaluate('currentPropertyId') == property_id
        assert page.evaluate("appState.photos.front[0].startsWith('data:')")
        results.append('PASS same-user recovery requires fresh property access; denied attempt remains hidden and retryable')
        page.evaluate('saveCloudProgress()')
        assert page.locator('#save-status').get_attribute('data-state') == 'cloud'
        assert 'verified' in page.locator('#save-status').inner_text()
        results.append('PASS recovered work saves and verifies in Supabase fixture')

        pending('8.123')
        expire()
        # Delay a same-user recovery, then switch accounts before verification completes.
        page.evaluate('''() => {
            window.originalRecoveryGetUser=sb.auth.getUser.bind(sb.auth);
            sb.auth.getUser=()=>new Promise(resolve=>window.resolveOldRecovery=resolve);
        }''')
        old_user = dict(fixture.user)
        login()
        page.wait_for_function('typeof resolveOldRecovery === "function"')
        fixture.user = {**fixture.user, 'id':str(uuid.uuid4()),'email':'other-user@example.test'}
        page.evaluate('(user)=>sb.auth.signInWithPassword({email:user.email,password:"fixture-other"})',fixture.user)
        expect(page.locator('#view-dashboard')).to_be_visible()
        page.evaluate('''async user => {
            resolveOldRecovery({data:{user},error:null});
            sb.auth.getUser=originalRecoveryGetUser;
        }''',old_user)
        page.wait_for_function('!recoveringLockedSurvey')
        assert page.evaluate('lockedSurveyRecovery===null')
        assert page.locator('[id^="len-"]').first.input_value() == ''
        results.append('PASS different-user login cannot recover former user measurements')

        # Explicit logout in another app tab discards an already locked snapshot too.
        fixture.user = {**fixture.user, 'id':fixture.tables['properties'][0]['user_id'],'email':'updated-fixture@example.test'}
        page.evaluate("sb.auth.signOut({scope:'local'})")
        login(); expect(page.locator('#view-dashboard')).to_be_visible()
        page.locator('.survey-item').first.click();expect(page.locator('#view-details')).to_be_visible()
        pending('9.123')
        second = context.new_page();second.on('dialog',lambda d:d.accept());second.goto(ORIGIN);expect(second.locator('#view-dashboard')).to_be_visible()
        second.evaluate('handleLogout()')
        page.wait_for_function('currentUser===null && lockedSurveyRecovery===null')
        assert page.locator('[id^="len-"]').first.input_value() == ''
        results.append('PASS deliberate logout broadcasts destructive cleanup across tabs')
        second.close()

        login();expect(page.locator('#view-dashboard')).to_be_visible()
        page.locator('.survey-item').first.click();expect(page.locator('#view-details')).to_be_visible()
        pending('10.123');expire()
        # Avoid dismissing a real reload prompt here; a fresh page demonstrates memory isolation.
        fresh = context.new_page();fresh.goto(ORIGIN);expect(fresh.locator('#view-auth')).to_be_visible()
        assert fresh.evaluate('lockedSurveyRecovery===null')
        assert fresh.locator('[id^="len-"]').first.input_value() == ''
        assert page.evaluate('!!lockedSurveyRecovery')
        results.append('PASS recovery is tab-memory-only, not a persistent/new-tab offline store')
        fresh.close()
        assert not fixture.unexpected,fixture.unexpected
        browser.close()
    print(json.dumps({'live_requests':0,'results':results},indent=2))

if __name__ == '__main__':
    main()
