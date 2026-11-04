import {test} from 'node:test';
import assert from 'node:assert/strict';
import {requestSurveyNotification} from '../supabase/functions/_shared/notifications.mjs';
import {stagingNotificationReceiver} from '../supabase/functions/_shared/staging_receiver.mjs';
import {dispatchRegistrationNotifications} from '../supabase/functions/_shared/registration.mjs';
const BASE='https://hexhtduvqzleoazusskh.supabase.co',UID='00000000-0000-4000-8000-000000000001',PID='00000000-0000-4000-8000-000000000002',ID='00000000-0000-4000-8000-000000000003';
const settings={SUPABASE_URL:BASE,SUPABASE_SERVICE_ROLE_KEY:'fixture-server',REGISTRATION_DISPATCH_SECRET:'fixture-dispatch-token-32-characters',SUPABASE_ANON_KEY:'fixture-anon',APP_URL:'http://localhost:8794/',NOTIFICATION_TRANSPORT:'staging_capture',REGISTRATION_NOTIFICATION_TRANSPORT:'staging_capture'};
const env=n=>settings[n];const json=(d,status=200)=>new Response(JSON.stringify(d),{status});
const serverRequest=()=>new Request(BASE+'/worker',{method:'POST',headers:{Authorization:'Bearer fixture-dispatch'}});
const surveyRequest=()=>new Request(BASE+'/notify',{method:'POST',headers:{Authorization:'Bearer fixture-user',Origin:'http://localhost:8794'},body:JSON.stringify({property_id:PID})});
const event={id:ID,user_id:UID,registration_email:'dummy@example.invalid',registered_at:'2026-11-04T10:00:00Z',verified_at:'2026-11-04T10:01:00Z',newsletter_signup_choice:true,newsletter_opted_in_at_verification:true};

test('staging capture never permits production targets or a Zapier fallback',async()=>{
 let calls=0;const fetcher=async()=>{calls++;throw Error();};
 for(const overrides of [{SUPABASE_URL:'https://other.test'},{NOTIFICATION_TRANSPORT:'zapier'},{APP_URL:undefined}]){
  const r=await requestSurveyNotification(surveyRequest(),{env:n=>({...settings,...overrides})[n],fetcher});assert.equal(r.status,503);
 }
 assert.equal(calls,0);
});
test('F02 staging transport preserves auth/property checks and sends only to fixed server-authorised sink',async()=>{
 const calls=[];
 const fetcher=async(url,init)=>{
  calls.push(url);
  if(url.endsWith('/user'))return json({id:UID,email_confirmed_at:'2026-11-04'});
  if(url.includes('/properties?'))return json([{id:PID,last_submitted_at:'2026-11-04T10:00:00Z'}]);
  if(url.endsWith('/claim_survey_notification'))return json({id:ID,claimed:true,payload:{property_id:PID,client_email:'client@example.invalid',address:'DUMMY',surveyor_name:'Dummy'}});
  if(url.endsWith('/staging-notification-receiver')){assert.equal(init.headers.Authorization,'Bearer fixture-server');assert.equal(init.headers['X-Urbanfold-Notification-Type'],'survey');return json({captured:true,email_sent:false});}
  if(url.endsWith('/finish_survey_notification'))return json(null);
  throw Error('Unexpected destination');
 };
 assert.equal((await requestSurveyNotification(surveyRequest(),{env,fetcher})).status,200);
 assert(calls.every(url=>url.startsWith(BASE+'/')));
});
test('dummy receiver requires exact project/server auth and never contacts an email provider',async()=>{
 let calls=0;
 const req=new Request(BASE+'/sink',{method:'POST',headers:{Authorization:'Bearer fixture-server','Idempotency-Key':ID,'X-Urbanfold-Notification-Type':'registration_verified'},body:JSON.stringify(event)});
 const fetcher=async(url,init)=>{calls++;assert.equal(url,BASE+'/rest/v1/rpc/capture_staging_notification');assert.equal(JSON.parse(init.body).kind,'registration_verified');return json(null);};
 assert.equal((await stagingNotificationReceiver(req.clone(),{env:n=>n==='SUPABASE_URL'?'https://production.test':env(n),fetcher})).status,503);
 const bad=new Request(BASE+'/sink',{method:'POST',headers:{Authorization:'Bearer fixture-user'},body:'{}'});
 assert.equal((await stagingNotificationReceiver(bad,{env,fetcher})).status,401);
 assert.equal((await stagingNotificationReceiver(req.clone(),{env,fetcher})).status,200);
 assert.equal(calls,1);
 assert.equal((await stagingNotificationReceiver(req.clone(),{env:n=>n==='STAGING_RECEIVER_BEHAVIOUR'?'reject':env(n),fetcher})).status,503);
 assert.equal(calls,1);
 let slept;
 const r=await stagingNotificationReceiver(req.clone(),{env:n=>n==='STAGING_RECEIVER_BEHAVIOUR'?'timeout_after_capture':env(n),fetcher,sleep:async ms=>slept=ms});
 assert.equal(r.status,200);assert.equal(slept,12000);assert.equal(calls,2);
 const rejected=await stagingNotificationReceiver(req.clone(),{env,fetcher:async()=>json({},400)});assert.equal(rejected.status,422);
});
function registrationFixture({reject=false,timeout=false,finishFailure=false}={}){
 let queued=true,sends=0;const calls=[];
 return {calls,sends:()=>sends,fetcher:async(url,init)=>{
  calls.push([url,init]);
  if(url.endsWith('/claim_registration_notification')){if(!queued)return json(null);queued=false;return json(event);}
  if(url.includes('/staging-notification-receiver')){sends++;const payload=JSON.parse(init.body);assert.equal(payload.recipient,'urbanfolduk@gmail.com');assert.equal(payload.registration_email,event.registration_email);assert.equal(payload.newsletter_signup_choice,true);if(timeout)throw Error();return json({},reject?503:200);}
  if(url.endsWith('/finish_registration_notification'))return json(null,finishFailure?500:200);
  throw Error('Unexpected route');
 }};
}
test('registration server-only worker captures exact admin payload once; browser body cannot override recipient',async()=>{
 const f=registrationFixture();
 const browser=new Request(BASE+'/worker',{method:'POST',headers:{Authorization:'Bearer fixture-user'},body:JSON.stringify({recipient:'forged@example.com'})});
 assert.equal((await dispatchRegistrationNotifications(browser,{env,fetcher:f.fetcher})).status,401);assert.equal(f.calls.length,0);
 const forgedServer=new Request(BASE+'/worker',{method:'POST',headers:{Authorization:'Bearer fixture-dispatch'},body:JSON.stringify({recipient:'forged@example.com'})});
 assert.equal((await dispatchRegistrationNotifications(forgedServer,{env,fetcher:f.fetcher})).status,200);
 assert.equal((await dispatchRegistrationNotifications(serverRequest(),{env,fetcher:f.fetcher})).status,200);
 assert.equal(f.sends(),1);assert(f.calls.every(([url])=>url.startsWith(BASE+'/')));
});
test('registration rejection/timeout/receipt failure records uncertainty, never automatic duplicate delivery',async()=>{
 for(const options of [{reject:true},{timeout:true},{finishFailure:true}]){const f=registrationFixture(options);assert.equal((await dispatchRegistrationNotifications(serverRequest(),{env,fetcher:f.fetcher})).status,202);await dispatchRegistrationNotifications(serverRequest(),{env,fetcher:f.fetcher});assert.equal(f.sends(),1);}
});
test('registration delivery disabled/missing config fails before claim; staging cannot use real email',async()=>{
 let calls=0;const fetcher=async()=>{calls++;throw Error();};
 for(const overrides of [{REGISTRATION_NOTIFICATION_TRANSPORT:'disabled'},{REGISTRATION_NOTIFICATION_TRANSPORT:'brevo'},{SUPABASE_URL:'https://other.test'}])assert.equal((await dispatchRegistrationNotifications(serverRequest(),{env:n=>({...settings,...overrides})[n],fetcher})).status,503);
 assert.equal(calls,0);
});
test('future Brevo delivery uses fixed admin, text payload, no marketing action and no staging credentials',async()=>{
 const cfg={...settings,SUPABASE_URL:'https://future-production.test',REGISTRATION_NOTIFICATION_TRANSPORT:'brevo',BREVO_REGISTRATION_API_KEY:'fixture-api-key',REGISTRATION_EMAIL_FROM:'verified-sender@example.test'};
 let sent;
 const fetcher=async(url,init)=>{
  if(url.endsWith('/claim_registration_notification'))return json({...event,newsletter_signup_choice:false});
  if(url==='https://api.brevo.com/v3/smtp/email'){sent=JSON.parse(init.body);assert.equal(init.headers['api-key'],'fixture-api-key');return json({messageId:'fixture'},201);}
  if(url.endsWith('/finish_registration_notification'))return json(null);
  throw Error('Unexpected route');
 };
 assert.equal((await dispatchRegistrationNotifications(serverRequest(),{env:n=>cfg[n],fetcher})).status,200);
 assert.deepEqual(sent.to,[{email:'urbanfolduk@gmail.com'}]);assert(sent.textContent.includes('Newsletter checkbox at registration: No'));assert(sent.textContent.includes(event.registered_at));assert(!sent.htmlContent);
});
test('new dashboard wrappers register and deny requests without server configuration',async()=>{
 const {readFile}=await import('node:fs/promises');const previous=globalThis.Deno;
 try{
  for(const slug of ['staging-notification-receiver','dispatch-registration-notifications']){
   let registered;globalThis.Deno={env:{get:()=>undefined},serve:handler=>registered=handler};
   const source=await readFile(new URL('../supabase/dashboard/'+slug+'.ts',import.meta.url),'utf8');
   await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
   assert.equal(typeof registered,'function');assert.notEqual((await registered(serverRequest())).status,200);
  }
 }finally{if(previous===undefined)delete globalThis.Deno;else globalThis.Deno=previous;}
});
