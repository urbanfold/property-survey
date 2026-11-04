"""Newsletter settings UI regressions with intercepted HTTP; no real users/email."""
import json,shutil,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from test_browser_integration import Fixture,ORIGIN
from playwright.sync_api import sync_playwright,expect

def main():
 f=Fixture();state={'opted_in':False,'fail':False,'hold':False};pending=[];writes=[]
 def route(r):
  url=r.request.url
  if '/rest/v1/rpc/get_newsletter_preference' in url:
   if state['hold']:pending.append(r);return
   return r.fulfill(status=404 if state['fail'] else 200,body=json.dumps({'opted_in':state['opted_in'],'recorded':True}),headers={'Access-Control-Allow-Origin':'*'},content_type='application/json')
  if '/rest/v1/rpc/set_newsletter_preference' in url:
   body=r.request.post_data_json;assert set(body)=={'subscribe'} and isinstance(body['subscribe'],bool);writes.append(body)
   if not state['fail']:state['opted_in']=body['subscribe']
   return r.fulfill(status=503 if state['fail'] else 200,body=json.dumps({'opted_in':state['opted_in']}),headers={'Access-Control-Allow-Origin':'*'},content_type='application/json')
  return f.route(r)
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox']);c=b.new_context();c.route('**/*',route)
  page=c.new_page();page.on('dialog',lambda d:d.accept());page.goto(ORIGIN)
  expect(page.locator('#signup-newsletter')).not_to_be_checked()
  page.locator('#login-email').fill(f.user['email']);page.locator('#login-password').fill('fixture-only-password');page.get_by_role('button',name='Log In',exact=True).click();expect(page.locator('#view-dashboard')).to_be_visible()
  page.get_by_role('button',name='Newsletter preferences',exact=True).click()
  expect(page.locator('#newsletter-save')).to_be_enabled();expect(page.locator('#newsletter-opt-in')).not_to_be_checked()
  page.locator('#newsletter-opt-in').check();page.locator('#newsletter-save').click();expect(page.locator('#newsletter-preference-status')).to_contain_text('subscription saved')
  assert state['opted_in'] is True
  page.locator('#newsletter-opt-in').uncheck();page.locator('#newsletter-save').click();expect(page.locator('#newsletter-preference-status')).to_contain_text('unsubscribed')
  assert state['opted_in'] is False
  state['fail']=True;page.locator('#newsletter-opt-in').check();page.locator('#newsletter-save').click();expect(page.locator('#newsletter-preference-status')).to_contain_text('could not be saved',timeout=30000)
  assert state['opted_in'] is False
  page.get_by_role('button',name='Close',exact=True).click();page.get_by_role('button',name='Newsletter preferences',exact=True).click()
  expect(page.locator('#newsletter-preference-status')).to_contain_text('not available');expect(page.locator('#newsletter-save')).to_be_disabled()
  state['fail']=False;page.get_by_role('button',name='Close',exact=True).click()
  state['hold']=True;page.get_by_role('button',name='Newsletter preferences',exact=True).click();page.wait_for_timeout(100)
  page.evaluate('handleLogout()');expect(page.locator('#view-auth')).to_be_visible()
  assert not page.locator('#newsletter-dialog').is_visible()
  for r in pending:r.fulfill(status=200,body='{"opted_in":true}',content_type='application/json',headers={'Access-Control-Allow-Origin':'*'})
  page.wait_for_timeout(100)
  expect(page.locator('#newsletter-opt-in')).not_to_be_checked()
  assert page.locator('#newsletter-preference-status').inner_text()==''
  assert not f.unexpected,f.unexpected
  assert f.emails==0
  b.close()
 print('PASS signup unchecked, preference read/opt-in/withdrawal, failure without false success, unavailable migration fallback, caller-only boolean payload, and delayed response cannot restore preference after logout; no email')
if __name__=='__main__':main()
