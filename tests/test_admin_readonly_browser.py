"""Isolated browser regression: admin reviews customer-owned survey without writes.
All requests are intercepted by the local fixture; no live Supabase requests.
"""
import json
import os
import shutil
import uuid
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw
import pypdfium2 as pdfium
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
    # A real, visible photograph served only by the isolated private Storage fixture.
    photo_path = prop_id + '/regression-photo.jpg'
    photo = Image.new('RGB', (160, 110), (35, 75, 115))
    painter = ImageDraw.Draw(photo)
    painter.rectangle((20, 20, 140, 90), fill=(155, 55, 45))
    photo_bytes = BytesIO()
    photo.save(photo_bytes, format='JPEG')
    fixture.objects[('exterior-photos', photo_path)] = photo_bytes.getvalue()
    fixture.tables['exterior_photos'].append({
        'id': str(uuid.uuid4()), 'property_id': prop_id, 'elevation_type':'front',
        'photo_url': 'storage://exterior-photos/' + photo_path,
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
        print('PRE-PDF:', page.evaluate("({css: getComputedStyle(document.getElementById('pdf-content')).display, width:document.getElementById('pdf-content').offsetWidth, exists:!!window.html2pdf})"), flush=True)
        try:
            with page.expect_download(timeout=12000) as download:
                page.locator('#admin-readonly-pdf').click()
            pdf_bytes = Path(download.value.path()).read_bytes()
        except Exception:
            print('PDF DIAGNOSTIC DIALOGS:', dialogs, flush=True)
            print('PDF PREVIEW:', page.evaluate("({display:getComputedStyle(document.getElementById('pdf-content')).display, text:document.getElementById('pdf-content').innerText.slice(0,140)})"), flush=True)
            raise
        assert pdf_bytes.startswith(b'%PDF-')
        # Extract actual text and rasterize the finished PDF, not just the
        # JavaScript canvas. A valid six-page all-white PDF must fail this test.
        document = pdfium.PdfDocument(pdf_bytes)
        assert len(document) >= 1
        text = '\\n'.join(page.get_textpage().get_text_range() for page in document)
        assert 'Customer Property' in text, 'Address is not readable in generated PDF'
        assert '4.2 m' in text, 'Kitchen length is not readable in generated PDF'
        assert 'URBANFOLD' in text, 'Brand heading is not readable in generated PDF'
        assert 'Survey: front' in text, 'Photograph caption missing from report'
        first_page = document[0].render(scale=1.5).to_pil().convert('RGB')
        colors = first_page.getcolors(maxcolors=1000000)
        assert colors is None or len(colors) > 2, 'PDF first page has no visible report content'
        # A photo should be included as an image in the final PDF, not just a text caption.
        assert any(len(page.get_objects(filter=(pdfium.raw.FPDF_PAGEOBJ_IMAGE,))) > 0 for page in document), 'PDF has no embedded survey photograph'
        assert json.dumps(fixture.tables,sort_keys=True) == before
        assert not errors, errors
        assert not fixture.unexpected,fixture.unexpected
        browser.close()
    print('PASS: administrator sees customer survey read-only without changing any records')

if __name__ == '__main__':
    main()
