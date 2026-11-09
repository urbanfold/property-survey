"""Generate/check a static-only staging client. No serving, network or ZIP creation."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'supabase/staging/static-client'
PROJECT = 'hexhtduvqzleoazusskh'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def render(commit):
    source = (ROOT / 'app.js').read_text()
    reviewed = subprocess.check_output(['git','show',commit+':app.js'],cwd=ROOT).decode()
    if source != reviewed:
        raise ValueError('Application differs from recorded reviewed source commit')
    app, count = re.subn(r"window\.supabase\.createClient\('[^']+', '[^']+'\)", 'window.urbanfoldStagingClient()', source)
    assert count == 1
    intent = "const authReturn = new URLSearchParams(location.hash.slice(1));"
    assert app.count(intent) == 1
    app = app.replace(intent, "const authReturn = window.urbanfoldStagingAuthReturn || new URLSearchParams(location.hash.slice(1));\n        delete window.urbanfoldStagingAuthReturn;")
    start = app.index('        async function buyAdditionalSurvey() {')
    end = app.index('        let checkingPurchasedCredit = false;', start)
    app = app[:start] + '''        async function buyAdditionalSurvey() {
            document.getElementById('checkout-status').textContent = 'Payments are disabled in this staging client.';
        }

''' + app[end:]
    assert 'create-survey-checkout' not in app and 'checkout.stripe.com' not in app
    config = (ROOT / 'supabase/staging/client-tools/configure.js').read_text()
    config = config.replace('client = window.supabase.createClient(STAGING_URL, key);', '''// A second boundary independent of the disabled payment UI.
            const stagingFetch = (input, init) => {
                const url = new URL(input instanceof Request ? input.url : input, location.href);
                if (url.origin !== STAGING_URL || (url.pathname.startsWith('/functions/v1/') && url.pathname !== '/functions/v1/request-survey-notification')) {
                    return Promise.reject(new Error('This staging client blocks payments and other backends.'));
                }
                return fetch(input, init);
            };
            // Preserve only routing flags before the SDK consumes the recovery URL.
            // No access/refresh token is copied into this bridge.
            const incoming = new URLSearchParams(location.hash.slice(1));
            window.urbanfoldStagingAuthReturn = new URLSearchParams();
            for (const name of ['type', 'error', 'error_code']) {
                if (incoming.has(name)) window.urbanfoldStagingAuthReturn.set(name, incoming.get(name));
            }
            client = window.supabase.createClient(STAGING_URL, key, { global: { fetch: stagingFetch } });''')
    assert 'global: { fetch: stagingFetch }' in config
    html = (ROOT / 'index.html').read_text()
    html = html.replace('<title>Urbanfold Property Survey</title>', '<title>STAGING ONLY — Urbanfold Property Survey</title>')
    csp = f"default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https://{PROJECT}.supabase.co; connect-src 'self' https://{PROJECT}.supabase.co wss://{PROJECT}.supabase.co; font-src 'self' data:; worker-src 'self' blob:; frame-src 'self' about: blob:; object-src 'none'; base-uri 'none'; form-action 'none'"
    html = html.replace('<meta charset="UTF-8">','<meta charset="UTF-8">\n    <meta http-equiv="Content-Security-Policy" content="'+csp+'">')
    html, count = re.subn(r'\s*<script src="app\.js[^\"]*"></script>', '', html)
    assert count == 1
    html = html.replace('stabilisation-1', 'SAFE-STAGING-' + sha(source.encode())[:12])
    html, count = re.subn(r'(<button[^>]+id="buy-additional-survey"[^>]*)(>).*?</button>',r'\1 disabled\2Payments disabled in staging</button>',html)
    assert count == 1
    banner = f'''
    <aside role="note" style="background:#7f1d1d;color:white;padding:16px;text-align:center;margin-bottom:20px">
      <strong>STAGING ONLY — dummy users and fictional surveys</strong><br>
      Project: {PROJECT} · Static-only client · Payments disabled<br>
      Source: {commit[:12]}. Never enter production credentials or customer information.
    </aside>
    <section id="staging-config" class="container">
      <h1>Configure isolated staging</h1>
      <label for="staging-public-key">Staging publishable or anon/public key only</label>
      <input id="staging-public-key" type="password" autocomplete="off" spellcheck="false">
      <button id="staging-start" type="button" class="btn">Open staging app</button>
      <p id="staging-config-status" role="status"></p>
      <p>Enter the public key again in each new/reloaded tab. Auth sessions can persist in this browser profile. Keep the local server running. Recovery and email requests require separate approval.</p>
    </section>
    <section id="staging-checks" class="container" hidden>
      <h2>Dummy A/B account isolation</h2>
      <button id="staging-isolation-check" type="button" class="btn">Check account isolation (read only)</button>
      <pre id="staging-isolation-result" role="status">Sign in, then run this check.</pre>
    </section>
    <div id="staging-app" hidden>
'''
    html = html.replace('<body>','<body>'+banner).replace('</body>','</div><script src="configure.js"></script></body>')
    files = {'index.html':html.encode(),'app.js':app.encode(),'configure.js':config.encode()}
    for name in ['html2pdf.bundle.min.js','jszip.min.js','supabase.js']:
        files['vendor/'+name] = (ROOT / 'vendor' / name).read_bytes()
    for data in [files['app.js'],files['index.html'],files['configure.js']]:
        assert b'arnzqizcycesukplmvuc' not in data
        assert not re.search(rb'eyJ[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+|sb_secret_|sk_live_|whsec_',data)
    manifest = {'source_commit':commit,'source_app_sha256':sha(source.encode()),'staging_project':PROJECT,
                'transformations':['Replace Supabase initialization with fixed staging bootstrap','Replace purchase function with no-network refusal','Preserve non-secret recovery routing flags across delayed bootstrap','Disable purchase button','Add staging CSP/banner/bootstrap; block SDK payment/foreign-backend fetches'],
                'files':{name:sha(data) for name,data in sorted(files.items())}}
    files['MANIFEST.json'] = (json.dumps(manifest,indent=2)+'\n').encode()
    files['SHA256SUMS.txt'] = ''.join(sha(data)+'  '+name+'\n' for name,data in sorted(files.items())).encode()
    return files

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    if args.check:
        commit=json.loads((OUT/'MANIFEST.json').read_text())['source_commit']
    else:
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    expected=render(commit)
    if args.check:
        actual={str(p.relative_to(OUT)):p.read_bytes() for p in OUT.rglob('*') if p.is_file()}
        assert actual==expected, 'Static output drift/unexpected files; inspect rather than overwriting'
        print('PASS exact static output/source/manifest parity; no launcher, server or network invoked')
    else:
        if OUT.exists() and any(str(p.relative_to(OUT)) not in expected for p in OUT.rglob('*') if p.is_file()):
            raise ValueError('Unexpected output files; inspect without deleting')
        for name,data in expected.items():
            path=OUT/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
        print('Prepared static-only folder '+str(OUT)+'; no ZIP, server or API request')

if __name__=='__main__':main()
