"""Fail closed if the Urbanfold staging acceptance bundle targets the live project.

This test does not authenticate, call an API, or publish a website.
"""
from pathlib import Path
from urllib.parse import urlparse
import re
import base64
import json

ROOT = Path(__file__).resolve().parents[1]
STAGING_REF = "hexhtduvqzleoazusskh"
LIVE_REF = "arnzqizcycesukplmvuc"
EXPECTED_URL = f"https://{STAGING_REF}.supabase.co"

app = (ROOT / "app.js").read_text(encoding="utf-8")
html = (ROOT / "index.html").read_text(encoding="utf-8")
assert LIVE_REF not in app and LIVE_REF not in html, "FAIL: live Supabase project reference found"
assert "STAGING TEST ONLY" in html and "No live surveys or payments" in html, "FAIL: staging warning absent"
assert "f01-staging-acceptance-2026-11-19" in html, "FAIL: staging asset version absent"

matches = re.findall(
    r"window\.supabase\.createClient\(\s*['\"]([^'\"]+)['\"],\s*['\"]([^'\"]+)['\"]\s*\)",
    app
)
assert len(matches) == 1, "FAIL: unexpected Supabase client configuration count"
url, key = matches[0]
assert url == EXPECTED_URL, "FAIL: Supabase client does not target staging"
assert urlparse(url).hostname == f"{STAGING_REF}.supabase.co", "FAIL: wrong Supabase hostname"
# The staging legacy ANON token is a public browser credential, never a service-role key.
parts = key.split(".")
assert len(parts) == 3, "FAIL: staging key is not the expected legacy anon JWT"
payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4)))
assert payload.get("role") == "anon", "FAIL: browser credential is not an anon key"
assert "service_role" not in app and "sb_secret_" not in app, "FAIL: privileged key marker present"

for asset in ("vendor/supabase.js","vendor/jszip.min.js","vendor/html2pdf.bundle.min.js"):
    assert (ROOT / asset).is_file(), f"FAIL: bundled dependency missing: {asset}"
assert re.search(r'<script\s+src="app\.js\?v=f01-staging-acceptance-2026-11-19"', html), "FAIL: stale entrypoint"
print("PASS staging-only bundle: staging project and anon key, visible warning, vendor scripts present; no live project target")
