"""Static and intercepted-browser checks. No live Auth, email, payment or SQL calls."""
from pathlib import Path
from urllib.parse import urlparse
import hashlib, importlib.util, json, mimetypes, re, shutil, sys
from playwright.sync_api import sync_playwright, expect
sys.path.insert(0,str(Path(__file__).parent))
import test_browser_integration as fixture
import test_staging_client as legacy_checks

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'supabase/staging/static-client'
PROJECT='hexhtduvqzleoazusskh'
ORIGIN='http://localhost:8794/'

def main():
 spec=importlib.util.spec_from_file_location('safe_builder',ROOT/'scripts/build_safe_staging_client.py')
 builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
 manifest=json.loads((OUT/'MANIFEST.json').read_text())
 actual={str(p.relative_to(OUT)):p.read_bytes() for p in OUT.rglob('*') if p.is_file()}
 assert actual==builder.render(manifest['source_commit'])
 assert set(actual)=={'index.html','app.js','configure.js','vendor/supabase.js','vendor/jszip.min.js','vendor/html2pdf.bundle.min.js','MANIFEST.json','SHA256SUMS.txt'}
 for name,digest in manifest['files'].items(): assert hashlib.sha256(actual[name]).hexdigest()==digest
 for line in actual['SHA256SUMS.txt'].decode().splitlines():
  digest,name=line.split('  ',1);assert hashlib.sha256(actual[name]).hexdigest()==digest
 for name in actual: assert Path(name).suffix.lower() not in {'.cmd','.bat','.ps1','.exe','.com','.dll','.msi','.sh','.py'}
 for name in ['index.html','app.js','configure.js']:
  text=actual[name].decode()
  assert 'arnzqizcycesukplmvuc' not in text and 'hooks.zapier.com' not in text
  assert not re.search(r'\beval\s*\(|new\s+Function\s*\(|import\s*\(\s*[\x27\"]https?://',text)
  assert not re.search(r'src\s*=\s*[\x27\"]https?://',text)
 for name in ['supabase.js','jszip.min.js','html2pdf.bundle.min.js']:
  assert actual['vendor/'+name]==(ROOT/'vendor'/name).read_bytes()
 print('PASS exact eight-file static inventory, source parity/checksums, no launcher/production credentials/webhook/payment implementation/remote script references; bundled vendor parity')
 # Reuse isolation/role/project/CSP tests against the new output, not old ZIP.
 legacy_checks.ROOT=OUT;legacy_checks.main()
 fixture.BACKEND=PROJECT+'.supabase.co'
 f=fixture.Fixture();requests=[];errors=[]
 def route(r):
  u=urlparse(r.request.url);requests.append((u.hostname,u.path,r.request.method))
  if u.hostname=='localhost':
   p=OUT/(u.path.lstrip('/') or 'index.html')
   if p.is_file() and OUT in p.resolve().parents:return r.fulfill(body=p.read_bytes(),content_type=mimetypes.guess_type(str(p))[0] or 'application/octet-stream')
   return r.fulfill(status=404,body='Not found')
  return f.route(r)
 def configure(page):
  page.locator('#staging-public-key').fill(legacy_checks.anon_key())
  page.locator('#staging-start').click()
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path=shutil.which('chromium'),args=['--no-sandbox'])
  c=b.new_context();c.route('**/*',route);page=c.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(ORIGIN);expect(page.get_by_text('STAGING ONLY — dummy users and fictional surveys',exact=True)).to_be_visible()
  configure(page);expect(page.locator('#view-auth')).to_be_visible()
  page.locator('#login-email').fill(f.user['email']);page.locator('#login-password').fill('fixture-only-password')
  page.get_by_role('button',name='Log In',exact=True).click();expect(page.locator('#view-dashboard')).to_be_visible()
  page.wait_for_load_state('networkidle')
  page.evaluate('showAdditionalSurveyDialog()')
  expect(page.locator('#buy-additional-survey')).to_be_disabled()
  page.evaluate('buyAdditionalSurvey()');expect(page.locator('#checkout-status')).to_contain_text('disabled')
  assert not any('create-survey-checkout' in path for host,path,method in requests)
  result=page.evaluate("async()=>{const r=await window.urbanfoldStagingClient().functions.invoke('create-survey-checkout',{body:{}});return !!r.error;}")
  assert result and not any('create-survey-checkout' in path for host,path,method in requests)
  assert page.evaluate("async()=>{const r=await window.urbanfoldStagingClient().functions.invoke('create%2Dsurvey%2Dcheckout',{body:{}});return !!r.error;}")
  assert not any('checkout' in path for host,path,method in requests)
  result=page.evaluate("async()=>{try{await window.urbanfoldStagingClient().rest.fetch('https://other-backend.test/x');return false;}catch{return true;}}")
  assert result and not any(host=='other-backend.test' for host,path,method in requests)
  # External script loading must fail under CSP; intercepted routes must see no request.
  assert page.evaluate("()=>new Promise(resolve=>{let s=document.createElement('script');s.src='https://unapproved.test/code.js';s.onerror=()=>resolve(true);s.onload=()=>resolve(false);document.head.appendChild(s);})")
  assert not any(host=='unapproved.test' for host,path,method in requests)
  c.close()
  c=b.new_context();c.route('**/*',route);page=c.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(ORIGIN);configure(page);expect(page.locator('#view-auth')).to_be_visible()
  page.get_by_role('button',name='Forgot password?',exact=True).click()
  page.locator('#reset-email').fill(f.user['email']);page.get_by_role('button',name='Send reset email',exact=True).click()
  expect(page.locator('#reset-request-title')).to_have_text('Check your email')
  assert len(f.recoveries)==1 and f.recoveries[0]['query']['redirect_to']==[ORIGIN]
  fragment='#access_token='+f.token+'&refresh_token=fixture-refresh-token&expires_in=3600&token_type=bearer&type=recovery'
  recovery=c.new_page();recovery.on('pageerror',lambda e:errors.append(str(e)))
  recovery.goto(ORIGIN+fragment);configure(recovery)
  expect(recovery.locator('#view-reset-password')).to_be_visible()
  assert recovery.evaluate('typeof window.urbanfoldStagingAuthReturn')=='undefined'
  recovery.reload();configure(recovery);expect(recovery.locator('#view-reset-password')).to_be_visible()
  recovery.locator('#reset-password').fill('fixture-new-password');recovery.locator('#reset-confirm-password').fill('fixture-new-password')
  recovery.get_by_role('button',name='Save new password',exact=True).click()
  expect(recovery.locator('#login-notice')).to_contain_text('password has been updated')
  assert len(f.password_updates)==1 and not f.emails
  assert not f.unexpected and not errors,(f.unexpected,errors)
  assert {host for host,path,method in requests}=={'localhost',PROJECT+'.supabase.co'}
  b.close()
 print('PASS generated current app login, disabled purchase/direct SDK payment denial, foreign SDK/CSP script denial, recovery redirect/fresh-tab/reload/password form; all HTTP mocked, no actual emails or password changes')

if __name__=='__main__':main()
