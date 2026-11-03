"""Generate/review SQL text only. Never connects to a database or executes SQL."""
from pathlib import Path
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[1]
PARTS = [
    'supabase/staging/000_fresh_baseline.sql',
    'supabase/001_secure_access.sql',
    'supabase/002_survey_purchases.sql',
    'supabase/003_survey_notifications.sql',
]

def build():
    parts = ['''-- GENERATED, PREPARED ONLY. NOT AUTHORISED FOR EXECUTION.
-- Source: scripts/build_staging_setup.py. Fresh staging only; do not use on production.
-- BEFORE APPROVED EXECUTION: manually verify the project URL/reference in Dashboard.
-- This acknowledgement is an operator interlock, NOT project-identity verification.
-- Each source migration has its own transaction. Stop on the first error.
set urbanfold.staging_setup = 'Urbanfold-Survey-Staging';
''']
    for name in PARTS:
        content = (ROOT / name).read_text()
        digest = hashlib.sha256(content.encode()).hexdigest()
        parts.append(f'\n-- BEGIN SOURCE {name}\n-- SHA256 {digest}\n{content}\n-- END SOURCE {name}\n')
    parts.append("\n-- Metadata-only completion marker; run verification queries separately.\nselect 'Prepared staging sequence completed; verify before dummy-user tests.' as result;\n")
    return ''.join(parts)

if __name__ == '__main__':
    output = ROOT / 'supabase/staging/setup.sql'
    expected = build()
    if '--check' in sys.argv:
        if not output.exists() or output.read_text() != expected:
            raise SystemExit('Staging SQL bundle differs from its reviewed sources. Regenerate locally.')
        print('PASS staging bundle matches all four migration sources; no SQL executed')
    else:
        output.write_text(expected)
        print('Prepared staging SQL text only; no SQL executed')
