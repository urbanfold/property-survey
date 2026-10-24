"""Exercise real browser UI with simulated Web Bluetooth; no physical-device claim."""
import os
import re
import shutil
from playwright.sync_api import sync_playwright, expect
from test_browser_integration import Fixture, ORIGIN

FAKE_BLUETOOTH = r"""() => {
 class Channel extends EventTarget {
  constructor(uuid) { super(); this.uuid=uuid; this.properties={notify:true}; this.started=0; this.stopped=0; }
  async startNotifications() {
   if (bluetoothFixture.mode==='no-notifications') throw new DOMException('Not supported','NotSupportedError');
   this.started++; return this;
  }
  async stopNotifications() { this.stopped++; return this; }
  send(bytes) { this.value=new DataView(Uint8Array.from(bytes).buffer); this.dispatchEvent(new Event('characteristicvaluechanged')); }
 }
 class Device extends EventTarget {
  constructor() {
   super(); this.name='DISTO test device';
   this.channels=[new Channel('3ab10101-f831-4395-b29d-570977d5bf94'),new Channel('3ab10102-f831-4395-b29d-570977d5bf94')];
   this.gatt={connected:false,
    connect:async()=>{
     if(bluetoothFixture.mode==='pending') await new Promise(resolve=>{bluetoothFixture.release=resolve;});
     this.gatt.connected=true; return this.gatt;
    },
    disconnect:()=>{this.gatt.connected=false;this.dispatchEvent(new Event('gattserverdisconnected'));},
    getPrimaryService:async()=>{
     if(bluetoothFixture.mode==='wrong-service')throw new DOMException('Missing service','NotFoundError');
     return {getCharacteristics:async()=>this.channels};
    }
   };
  }
 }
 window.bluetoothFixture={mode:'ok',requests:[],devices:[]};
 Object.defineProperty(navigator,'bluetooth',{configurable:true,value:{
  requestDevice:async options=>{
   bluetoothFixture.requests.push(options);
   if(bluetoothFixture.mode==='cancel') throw new DOMException('Cancelled','NotFoundError');
   if(bluetoothFixture.mode==='blocked') throw new DOMException('Denied','NotAllowedError');
   const device=new Device();bluetoothFixture.devices.push(device);return device;
  }
 }});
}"""

def main():
    fixture=Fixture()
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or shutil.which('chromium') or None,args=['--no-sandbox'])
        context=browser.new_context(viewport={'width':800,'height':1100})
        context.route('**/*',fixture.route)
        page=context.new_page();errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(ORIGIN)
        page.evaluate("showView('view-interior-rooms');document.getElementById('len-Porch').value='7.25'")
        page.evaluate("Object.defineProperty(navigator,'bluetooth',{configurable:true,value:undefined})")
        page.get_by_role('button',name='Test Leica connection',exact=True).click()
        expect(page.locator('#leica-test-status')).to_contain_text('This browser cannot access Bluetooth')
        expect(page.locator('#leica-test-connect')).to_be_disabled()
        page.get_by_role('button',name='Close test',exact=True).click()
        page.evaluate(FAKE_BLUETOOTH)
        for mode, text in [('cancel','No device selected'),('blocked','Bluetooth permission was blocked'),('wrong-service','Could not read the DISTO Bluetooth service'),('no-notifications','no readable notification channel')]:
            page.evaluate('(mode)=>bluetoothFixture.mode=mode',mode)
            page.get_by_role('button',name='Test Leica connection',exact=True).click()
            page.get_by_role('button',name='Choose Leica device',exact=True).click()
            expect(page.locator('#leica-test-status')).to_contain_text(text)
            expect(page.locator('#leica-test-connect')).to_be_enabled()
            assert page.locator('#len-Porch').input_value()=='7.25'
            page.get_by_role('button',name='Close test',exact=True).click()
        print('PASS unsupported browser, chooser cancellation, blocked permissions, unavailable service and notification failure retain manual measurements')
        page.evaluate("bluetoothFixture.mode='ok'")
        page.get_by_role('button',name='Test Leica connection',exact=True).click()
        page.get_by_role('button',name='Choose Leica device',exact=True).click()
        expect(page.locator('#leica-test-status')).to_contain_text('Connected and listening')
        assert page.evaluate("bluetoothFixture.requests.at(-1).optionalServices[0]")=='3ab10100-f831-4395-b29d-570977d5bf94'
        assert page.evaluate("bluetoothFixture.devices.at(-1).channels.every(c=>c.started===1)")
        page.evaluate("bluetoothFixture.devices.at(-1).channels[0].send([0,0,128,63])")
        expect(page.locator('#leica-test-status')).to_contain_text('Data received (1 packet(s))')
        expect(page.locator('#leica-test-details')).to_have_value(re.compile(r'Packets received: 1.*00 00 80 3f',re.S))
        assert page.locator('#len-Porch').input_value()=='7.25'
        assert page.locator('#wid-Porch').input_value()==''
        assert page.locator('#hei-Porch').input_value()==''
        page.evaluate("for(let i=0;i<20;i++)bluetoothFixture.devices.at(-1).channels[0].send([i])")
        assert len(page.locator('#leica-test-details').input_value().splitlines())==13
        page.get_by_role('button',name='Disconnect',exact=True).click()
        expect(page.locator('#leica-test-status')).to_contain_text('Disconnected')
        before=page.locator('#leica-test-details').input_value()
        page.evaluate("bluetoothFixture.devices.at(-1).channels[0].send([255])")
        assert page.locator('#leica-test-details').input_value()==before
        assert page.evaluate("bluetoothFixture.devices.at(-1).channels.every(c=>c.stopped===1)")
        assert not page.evaluate("bluetoothFixture.devices.at(-1).gatt.connected")
        print('PASS notifications show bounded raw diagnostics without decoding or writing survey fields; disconnect removes listeners')
        page.get_by_role('button',name='Choose Leica device',exact=True).click()
        expect(page.locator('#leica-test-status')).to_contain_text('Connected and listening')
        page.evaluate("bluetoothFixture.devices.at(-1).gatt.disconnect()")
        expect(page.locator('#leica-test-status')).to_contain_text('The laser disconnected')
        page.get_by_role('button',name='Choose Leica device',exact=True).click()
        expect(page.locator('#leica-test-status')).to_contain_text('Connected and listening')
        page.keyboard.press('Escape')
        expect(page.locator('#leica-test-dialog')).not_to_be_visible()
        page.wait_for_function('!bluetoothFixture.devices.at(-1).gatt.connected')
        page.evaluate("bluetoothFixture.mode='pending'")
        page.get_by_role('button',name='Test Leica connection',exact=True).click()
        page.get_by_role('button',name='Choose Leica device',exact=True).click()
        expect(page.locator('#leica-test-status')).to_contain_text('Connecting to the DISTO')
        page.get_by_role('button',name='Close test',exact=True).click()
        page.evaluate('bluetoothFixture.release()')
        page.wait_for_function('!bluetoothFixture.devices.at(-1).gatt.connected')
        assert page.locator('#len-Porch').input_value()=='7.25'
        assert not errors,errors
        assert not fixture.unexpected,fixture.unexpected
        assert fixture.emails==0
        print('PASS device loss, Escape and closing during connection clean up Bluetooth without changing survey data or sending notifications')
        browser.close()

if __name__=='__main__':main()
