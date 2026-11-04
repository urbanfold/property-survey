"""Prepare a local-only staging client/ZIP. No credentials, server, SQL or deployment."""
from pathlib import Path
import hashlib
import re
import shutil
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
OUT = Path('/workspace/urbanfold-staging-client')
ZIP = Path('/workspace/urbanfold-staging-client.zip')
STAGING = 'hexhtduvqzleoazusskh'

def build():
    source = (ROOT/'app.js').read_text()
    app, count = re.subn(r"window\.supabase\.createClient\('[^']+', '[^']+'\)", 'window.urbanfoldStagingClient()', source)
    assert count == 1, 'Review changed app initialization before building'
    assert 'arnzqizcycesukplmvuc' not in app
    version = 'STAGING-' + hashlib.sha256(source.encode()).hexdigest()[:12]
    html = (ROOT/'index.html').read_text()
    html = html.replace('<title>Urbanfold Property Survey</title>', '<title>STAGING — Urbanfold Property Survey</title>')
    csp = f"default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https://{STAGING}.supabase.co; connect-src 'self' https://{STAGING}.supabase.co wss://{STAGING}.supabase.co; font-src 'self' data:; worker-src 'self' blob:; frame-src 'self' about: blob:; object-src 'none'; base-uri 'none'; form-action 'none'"
    html = html.replace('<meta charset="UTF-8">', '<meta charset="UTF-8">\n    <meta http-equiv="Content-Security-Policy" content="'+csp+'">')
    html = re.sub(r'\s*<script src="app\.js[^\"]*"></script>', '', html)
    html = html.replace('stabilisation-1', version)
    banner = '''
    <aside style="background:#7f1d1d;color:white;padding:14px;text-align:center;margin-bottom:20px" role="note">
      <strong>STAGING ONLY — dummy users and fictional surveys</strong><br>
      Project: hexhtduvqzleoazusskh · Never enter production passwords, keys or customer data.
    </aside>
    <section id="staging-config" class="container">
      <h1>Configure the isolated test app</h1>
      <p>Paste the public key from Urbanfold-Survey-Staging here. Use a publishable key or legacy anon/public key. Never use a secret or service-role key.</p>
      <label for="staging-public-key">Staging public key</label>
      <input id="staging-public-key" type="password" autocomplete="off" spellcheck="false" style="width:100%;padding:12px;margin:16px 0">
      <button id="staging-start" class="btn" type="button">Open staging app</button>
      <p id="staging-config-status" role="status" style="margin-top:16px"></p>
      <p>Enter the key again after reloading. Auth sessions and drafts use this separate localhost origin. Do not submit, buy credits or configure email until the staging backend is ready.</p>
    </section>
    <div id="staging-app" hidden>
'''
    html = html.replace('<body>', '<body>'+banner)
    html = html.replace('</body>', '</div><script src="configure.js"></script></body>')
    assert 'arnzqizcycesukplmvuc' not in html
    OUT.mkdir(exist_ok=True)
    (OUT/'vendor').mkdir(exist_ok=True)
    (OUT/'app.js').write_text(app)
    (OUT/'index.html').write_text(html)
    for name in ['html2pdf.bundle.min.js','jszip.min.js','supabase.js']:
        shutil.copy2(ROOT/'vendor'/name,OUT/'vendor'/name)
    for name in ['configure.js','START-STAGING.cmd','Serve-Staging.ps1']:
        shutil.copy2(ROOT/'supabase/staging/client-tools'/name,OUT/name)
    shutil.copy2(ROOT/'supabase/staging/test-photo.svg', OUT/'test-photo.svg')
    (OUT/'READ-ME.txt').write_text('''URBANFOLD LOCAL STAGING APP — NO PUBLICATION

1. Extract ALL files from the ZIP to a new folder on your Windows laptop.
2. Open START-STAGING.cmd. It starts a local-only server using built-in Windows PowerShell. No installation/admin access is requested. Leave its window open.
3. In Chrome open http://localhost:8794/ (the launcher may open your default browser).
4. Paste ONLY the public/publishable or legacy anon key from Urbanfold-Survey-Staging into the configuration box; click Open staging app. Never send a key or password in chat.
5. Log in with staging-owner-a@example.invalid and its staging-only password. Open DUMMY PROPERTY A. Record what appears, then use the app's Log Out and test B separately.

Fixed project: hexhtduvqzleoazusskh. CSP blocks fetch/WebSocket/image connections to other external backends, including production. No production anon key is packaged. This is a development test copy, not a deployment or exact production artifact.

Do not use the live github.io app for staging. Do not click Buy, Submit or reset/signup email flows until separately configured/tested. There are no paid credits or notification functions assumed installed. Dummy accounts were created manually and confirmed in staging.

The public key is not stored by this launcher and is cleared from its input after startup; Supabase's normal session tokens and existing app drafts may persist in this localhost browser origin. Use a separate test browser profile and only dummy records. After a page reload, enter the public key again. Unexpected-expiry recovery is tab-memory only and can be lost on reload.

Closing the server window stops local serving. Chrome may retain existing local test session/drafts. Auth signing, RLS, storage and all API access still need real test evidence. A simple successful login/list is not proof of cross-account API isolation.

If Windows/organisation policy blocks the launcher, stop and share the error text without keys/passwords; do not disable system security settings. You can alternatively serve this extracted folder with an installed Python: python -m http.server 8794 --bind 127.0.0.1

Localhost is laptop-only. Tablet/Leica testing requires a separately approved HTTPS staging origin. Real admin exports require an approved admin identity strategy. Production SMTP/Stripe settings are not used.
''')
    files = [OUT/'index.html',OUT/'app.js',OUT/'configure.js',OUT/'START-STAGING.cmd',OUT/'Serve-Staging.ps1',OUT/'READ-ME.txt',OUT/'test-photo.svg'] + list((OUT/'vendor').glob('*.js'))
    with ZipFile(ZIP,'w',ZIP_DEFLATED) as archive:
        for file in files: archive.write(file, 'urbanfold-staging-client/'+str(file.relative_to(OUT)))
    print(f'Prepared {ZIP}; no server, SQL, API call or deployment executed')

if __name__ == '__main__': build()
