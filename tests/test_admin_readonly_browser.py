"""Isolated browser regression: admin reviews customer-owned survey without writes.
All requests are intercepted by the local fixture; no live Supabase requests.
"""
import json
import os
import shutil
import uuid
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from test_browser_integration import Fixture, ORIGIN, USER_ID

def main():
    fixture = Fixture()
    other_id = str(uuid.uuid4())
    prop_id = str(uuid.uuid4())
    fixture.tables['properties'].append({
        'id': prop_id, 'user_id': other_id, 'address': 'Customer Property',
        'postcode': 'S00 0AA', 'surveyor_name': 'Customer B',
        'client_email': 'customer@example.invalid', 'property_type': 'detached',
        'notes': 'Read-only customer record', 'status': 'in_progress',
        'created_at': '2026-10-22T12:00:00Z'
    })
    fixture.tables['rooms'].append({
        'id': str(uuid.uuid4()), 'property_id': prop_id,
        'room_name': 'Kitchen', 'shape': 'Square/Rectangular',
        'dimensions': {'l':4.2, 'w':3.5, 'h':2.4},
        'additional_measurements': 'Existing kitchen',
        'created_at': '2026-10-22T12:00:00Z'
    })
    before = json.dumps(fixture.tables, sort_keys=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium') or None,
            args=['--no-sandbox']
        )
        context = browser.new_context(accept_downloads=True)
        context.route('**/*', fixture.route)
        page = context.new_page()
        errors = []
        page.on('pageerror', lambda err: errors.append(str(err)))
        page.goto(ORIGIN)
        page.locator('#login-email').fill('urbanfolduk@gmail.com')
        page.locator('#login-password').fill('fixture-login-only')
        page.get_by_role('button', name='Log In', exact=True).click()
        expect(page.locator('#view-dashboard')).to_be_visible()
        target = page.locator('.survey-item').filter(has_text='Customer Property')
        expect(target).to_be_visible()
        target.locator('h3').click()
        expect(page.locator('#view-admin-readonly')).to_be_visible()
        expect(page.locator('#admin-readonly-content')).to_contain_text('Customer Property')
        expect(page.locator('#admin-readonly-content')).to_contain_text('Length: 4.2 m')
        expect(page.locator('#admin-readonly-pdf')).to_be_enabled()
        expect(page.locator('#admin-readonly-zip')).to_be_enabled()
        assert page.evaluate('currentPropertyId') is None
        assert not page.locator('#view-details').is_visible()
        assert json.dumps(fixture.tables,sort_keys=True) == before
        page.evaluate(f"resumeSurvey('{prop_id}')")
        expect(page.locator('#view-admin-readonly')).to_be_visible()
        assert json.dumps(fixture.tables,sort_keys=True) == before
        # Previously a six-page all-white file passed merely because it was a PDF.
        # The application's canvas guard must reject a blank render before download.
        dialogs = []
        page.on('dialog', lambda dialog: (dialogs.append(dialog.message), dialog.accept()))
        with page.expect_download(timeout=12000) as download:
            page.locator('#admin-readonly-pdf').click()
        pdf_bytes = Path(download.value.path()).read_bytes()
        assert pdf_bytes.startswith(b'%PDF-')
        assert len(pdf_bytes) > 25000, 'Suspiciously small PDF report'
        assert json.dumps(fixture.tables,sort_keys=True) == before
        assert not errors, errors
        assert not fixture.unexpected,fixture.unexpected
        browser.close()
    print('PASS: administrator sees customer survey read-only without changing any records')

if __name__ == '__main__':
    main()
