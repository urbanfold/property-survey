"""Browser regression checks with an in-memory Supabase; no live requests or emails.
Run: python3 tests/test_survey_flow.py (requires playwright and Chromium).
"""
from pathlib import Path
import os
import shutil
import re
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
STUB = r"""
window.fixture = {tables: {properties:[{id:'p1', address:'Initial'}], extensions:[],
 rooms:[], exterior_photos:[], extension_photos:[], sketch_photos:[], room_photos:[]},
 fail:null, uploads:[], emails:0};
window.fetch=async()=>{fixture.emails++; return {ok:true}};
window.supabase={createClient:()=>({supabaseUrl:'https://arnzqizcycesukplmvuc.supabase.co',
 auth:{getSession:async()=>({data:{session:null}})},
 storage:{from:bucket=>({
  upload:async(path)=>{if(fixture.fail==='upload:'+bucket)return {error:{message:'upload denied'}};
   fixture.uploads.push([bucket,path]);return {data:{path}}},
  createSignedUrls:async paths=>({data:paths.map(path=>({path,signedUrl:'https://photos.test/'+bucket+'/'+path}))})
 })},
 from:table=>{
  let op='select', payload, filters=[], single=false;
  const q={select(){return q},eq(k,v){filters.push(row=>row[k]===v);return q},
   in(k,v){filters.push(row=>v.includes(row[k]));return q},
   order(){return q}, single(){single=true;return q},
   delete(){op='delete';return q},insert(v){op='insert';payload=v;return q}, update(v){op='update';payload=v;return q},
   then(resolve,reject){return Promise.resolve().then(()=>{
    if(fixture.fail===table+':'+op)return {error:{message:'database denied'}};
    let rows=fixture.tables[table].filter(row=>filters.every(f=>f(row)));
    if(op==='insert'){
     rows=(Array.isArray(payload)?payload:[payload]).map(row=>({...row,id:crypto.randomUUID()}));
     fixture.tables[table].push(...rows);
    }
    if(op==='update')rows.forEach(row=>Object.assign(row,payload));
    if(op==='delete')fixture.tables[table]=fixture.tables[table].filter(row=>!rows.includes(row));
    return {data:single?(rows[0]||null):rows,error:null};
   }).then(resolve,reject)}
  };return q;
 }
})};
"""
SETUP = r"""() => {
 currentUser={id:'u1'};currentPropertyId='p1';showView('view-interior-rooms');
 const values={'detail-name':'Test surveyor','detail-client-email':'test@example.test',
  'detail-address':'Test property','detail-postcode':'AB1 2CD','detail-notes':'Notes',
  'prop-type':'detached','ext-description':'Extension notes','ext-width':'3','ext-length':'4'};
 for(const [id,val] of Object.entries(values))document.getElementById(id).value=val;
 document.querySelector('input[name="ext-type"]').checked=true;
 updateExteriorRequirements();
 const first=roomId(roomList[0]);
 document.getElementById('len-'+first).value='4';
 document.getElementById('wid-'+first).value='3';
 document.getElementById('hei-'+first).value='2.4';
 document.getElementById('add-'+first).value='Room notes';
 const second=roomId(roomList[1]);
 const shape=document.getElementById('shape-'+second);shape.value='L-shaped room';toggleLShapedDimensions(shape);
 for(const key of ['len1','wid1','len2','wid2','len3','wid3'])document.getElementById(key+'-'+second).value='2';
 document.getElementById('hei-'+second).value='2.5';
 const photo='data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=';
 appState.photos={front:[photo],rear:[photo],'extension-location':[photo],sketch:[photo]};
 appState.roomPhotos={[roomList[0]]:[photo]};saveDraft();
}"""

def main():
    html = ROOT.joinpath('index.html').read_text()
    html = re.sub(r'<script src="[^"]+"></script>', '', html)
    html = html.replace('<head>', '<head><script>' + STUB + '</script>')
    html = html.replace('</body>', '<script>' + ROOT.joinpath('app.js').read_text() + '</script></body>')
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium') or None, args=['--no-sandbox'])
        errors = []
        dialogs = []
        page = browser.new_page()
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('dialog', lambda d: (dialogs.append(d.message), d.accept()))
        page.route('https://survey.test/**', lambda route: route.fulfill(body=html, content_type='text/html'))
        # Stored photo bytes are unnecessary for these checks; don't issue network requests.
        page.route('https://photos.test/**', lambda route: route.fulfill(status=204))
        def reset():
            page.goto('https://survey.test/')
            page.evaluate('localStorage.clear()')
            page.evaluate(SETUP)
            assert page.evaluate("new Set(Array.from(document.querySelectorAll('[id]'), e=>e.id)).size === document.querySelectorAll('[id]').length"), 'duplicate element IDs'
        reset()
        # An immediate refresh must flush the debounce without losing the edit.
        page.evaluate("document.querySelector('[id^=len-]').value='4.5';document.querySelector('[id^=len-]').dispatchEvent(new Event('input',{bubbles:true}))")
        page.reload()
        page.evaluate("currentUser={id:'u1'};showView('view-auth');saveDraft();resumeSurvey('p1')")
        assert page.locator('[id^="len-"]').first.input_value() == '4.5'
        assert page.locator('#preview-front img').count() == 1
        print('PASS immediate refresh, auth-screen protection, matching draft restoration')
        reset()
        page.evaluate('finishSurvey()')
        assert page.locator('#view-success').is_visible(), dialogs
        assert page.evaluate('fixture.emails') == 1
        assert page.evaluate('fixture.tables.exterior_photos.length') == 2
        assert page.evaluate('fixture.uploads.length') == 5
        assert page.evaluate("localStorage.getItem('urbanfold_draft_p1')") is None
        cloud = page.evaluate('fixture.tables')
        page.reload()
        page.evaluate('(tables)=>{fixture.tables=tables;currentUser={id:"u1"}}', cloud)
        page.evaluate("resumeSurvey('p1')")
        assert page.locator('#detail-address').input_value() == 'Test property'
        assert page.locator('#prop-type').input_value() == 'detached'
        assert page.locator('#ext-description').input_value() == 'Extension notes'
        assert page.locator('#ext-width').input_value() == '3'
        assert page.locator('input[name="ext-type"]').first.is_checked()
        assert page.locator('#preview-front img').count() == 1
        assert page.locator('#preview-rear img').count() == 1
        assert page.locator('#preview-extension-location img').count() == 1
        assert page.locator('#preview-sketch img').count() == 1
        assert page.locator('[id^="len-"]').first.input_value() == '4'
        assert page.locator('[id^="hei-"]').first.input_value() == '2.4'
        assert page.locator('[id^="hei-"]').nth(1).input_value() == '2.5'
        assert page.locator('[id^="len1-"]').nth(1).input_value() == '2'
        assert page.evaluate('appState.roomPhotos[roomList[0]].length') == 1
        print('PASS full submission, fresh-page cloud recovery of all sections and photos')
        # Reproduce the reported failure: an old blank room-screen draft masks a submission.
        stale = {'propertyId':'p1', 'userId':'u1', 'view':'view-interior-rooms',
                 'details':{'address':'Stale device draft'}, 'propType':'',
                 'extension':{}, 'rooms':{}, 'appState':{'photos':{},'roomPhotos':{}}}
        page.evaluate('(draft)=>localStorage.setItem("urbanfold_draft_p1",JSON.stringify(draft))', stale)
        page.evaluate("resumeSurvey('p1')")
        assert page.locator('#view-details').is_visible()
        assert page.locator('#detail-address').input_value() == 'Test property'
        assert page.locator('[id^="len-"]').first.input_value() == '4'
        assert page.locator('#preview-front img').count() == 1
        assert 'database' in page.locator('#survey-source').inner_text()
        page.evaluate('saveDraft()')
        assert page.evaluate('JSON.parse(localStorage.getItem("urbanfold_draft_p1")).details.address') == 'Stale device draft'
        page.locator('#restore-device-draft').click()
        assert page.locator('#view-details').is_visible()
        assert page.locator('#detail-address').input_value() == 'Stale device draft'
        assert page.locator('#preview-front img').count() == 0
        assert page.locator('#preview-sketch img').count() == 0
        page.evaluate("resumeSurvey('p1')")
        assert page.locator('#detail-address').input_value() == 'Test property'
        print('PASS stale room-screen draft cannot hide cloud data; preserved draft can be opened explicitly')

        page.evaluate('finishSurvey()')
        assert page.locator('#view-success').is_visible()
        assert page.evaluate('fixture.uploads.length') == 0
        assert page.evaluate('fixture.tables.rooms.length') == len(cloud['rooms'])
        assert page.evaluate('fixture.tables.extensions.length') == 1
        assert page.evaluate('fixture.tables.exterior_photos.length') == 2
        print('PASS reopening and resubmitting does not duplicate room/extension records or photos')
        failures = ['properties:update','upload:exterior-photos','exterior_photos:insert',
                    'extensions:select','extensions:insert','extension_photos:insert',
                    'upload:sketch-photos','sketch_photos:insert','rooms:select',
                    'rooms:insert','upload:room-photos','room_photos:insert']
        for failure in failures:
            reset()
            page.evaluate('(failure)=>fixture.fail=failure', failure)
            page.evaluate('finishSurvey()')
            assert not page.locator('#view-success').is_visible(), failure
            assert page.evaluate('fixture.emails') == 0, failure
            assert page.evaluate("!!localStorage.getItem('urbanfold_draft_p1')"), failure
            assert page.locator('#loading').is_hidden(), failure
            page.evaluate('fixture.fail=null;finishSurvey()')
            assert page.locator('#view-success').is_visible(), (failure, dialogs[-1:])
            assert page.evaluate('fixture.tables.extensions.length') == 1, failure
            assert page.evaluate('fixture.tables.exterior_photos.length') == 2, failure
            assert page.evaluate('fixture.tables.rooms.length') == len(cloud['rooms']), failure
        print('PASS 12 injected save/upload failures retain drafts, suppress success/email, and support retry')
        reset()
        page.evaluate("localStorage.clear();fixture.fail='rooms:select';resumeSurvey('p1')")
        assert not page.locator('#view-details').is_visible()
        assert 'rooms:' in dialogs[-1]
        assert not errors, errors
        print('PASS cloud read failures reported; no browser JavaScript errors')
        browser.close()

if __name__ == '__main__':
    main()
