import {test} from 'node:test';
import assert from 'node:assert/strict';
import {requestSurveyNotification} from '../supabase/functions/_shared/notifications.mjs';
const uid='00000000-0000-4000-8000-000000000001',pid='00000000-0000-4000-8000-000000000002',event='00000000-0000-4000-8000-000000000003';
const config={APP_URL:'https://urbanfold.github.io/property-survey/',SUPABASE_URL:'https://production.fixture.test',
 SUPABASE_ANON_KEY:'anon-fixture',SUPABASE_SERVICE_ROLE_KEY:'service-fixture',
 NOTIFICATION_TRANSPORT:'brevo',BREVO_REGISTRATION_API_KEY:'brevo-fixture',REGISTRATION_EMAIL_FROM:'survey@urbanfold.uk'};
const req=(body={property_id:pid})=>new Request('https://fixture.test/functions/v1/request-survey-notification',{
 method:'POST',headers:{authorization:'Bearer authenticated-fixture',origin:'https://urbanfold.github.io','content-type':'application/json'},body:JSON.stringify(body)});
const json=(value,status=200)=>new Response(JSON.stringify(value),{status});
function harness({customerFails=false,adminFinishFails=false,invalidEmail=false,unconfirmed=false,staging=false}={}){
 const calls=[],deliveryStates=[],secrets=new Set();
 let eventState='sending',prepared=false;
 const env=name=>name==='SUPABASE_URL'&&staging?'https://hexhtduvqzleoazusskh.supabase.co':config[name];
 const fetcher=async(url,init)=>{
  calls.push({url,init});
  if(url.endsWith('/auth/v1/user'))return json({id:uid,email:'professional@example.test',email_confirmed_at:unconfirmed?null:'2026-11-03T12:00:00Z'});
  if(url.includes('/rest/v1/properties?'))return json([{id:pid,last_submitted_at:'2026-11-03T12:00:00Z'}]);
  if(url.endsWith('/rpc/claim_survey_notification'))return json({id:event,claimed:true,payload:{property_id:pid,client_email:invalidEmail?'bad\n@example.test':'client@example.test',address:'Fixture House',surveyor_name:'Professional'}});
  if(url.endsWith('/rpc/prepare_survey_brevo_deliveries')){prepared=true;return json(true);}
  if(url.endsWith('/rpc/finish_survey_brevo_delivery')){
   const p=JSON.parse(init.body);
   if(p.kind==='admin'&&adminFinishFails)return json({error:'persist failed'},503);
   deliveryStates.push({kind:p.kind,accepted:p.accepted});
   return json({recipient_kind:p.kind,state:p.accepted?'accepted':'uncertain',overall_state:deliveryStates.length===2&&deliveryStates.every(x=>x.accepted)?'accepted':'sending'});
  }
  if(url==='https://api.brevo.com/v3/smtp/email'){
   assert(prepared,'must prepare durable ledger before sending');
   assert.equal(init.headers['api-key'],'brevo-fixture');
   const payload=JSON.parse(init.body);assert.equal(payload.to.length,1);
   secrets.add(payload.to[0].email);
   if(customerFails&&payload.to[0].email==='client@example.test')return json({message:'rejected'},500);
   return json({messageId:'fixture'},201);
  }
  throw Error('Unexpected call '+url);
 };
 return {env,fetcher,calls,deliveryStates,secrets};
}
test('two independent Brevo messages, both accepted',async()=>{
 const x=harness(),r=await requestSurveyNotification(req(),x);
 assert.equal(r.status,200);assert.equal((await r.json()).status,'accepted');
 assert.deepEqual([...x.secrets],['urbanfolduk@gmail.com','client@example.test']);
 assert.deepEqual(x.deliveryStates,[{kind:'admin',accepted:true},{kind:'customer',accepted:true}]);
});
test('one recipient failing never causes a retry of the successful recipient',async()=>{
 const x=harness({customerFails:true}),r=await requestSurveyNotification(req(),x);
 assert.equal(r.status,202);assert.equal((await r.json()).status,'uncertain');
 assert.deepEqual(x.deliveryStates,[{kind:'admin',accepted:true},{kind:'customer',accepted:false}]);
 assert.equal(x.calls.filter(c=>c.url==='https://api.brevo.com/v3/smtp/email').length,2);
});
test('failure to save first delivery result stops the second email',async()=>{
 const x=harness({adminFinishFails:true}),r=await requestSurveyNotification(req(),x);
 assert.equal(r.status,202);
 assert.deepEqual([...x.secrets],['urbanfolduk@gmail.com']);
});
test('invalid recipient never sends',async()=>{
 const x=harness({invalidEmail:true}),r=await requestSurveyNotification(req(),x);
 assert.equal(r.status,202);assert.equal(x.secrets.size,0);
});
test('staging and unverified users never send Brevo emails',async()=>{
 for(const x of [harness({staging:true}),harness({unconfirmed:true})]){
  const r=await requestSurveyNotification(req(),x);
  assert.notEqual(r.status,200);assert.equal(x.secrets.size,0);
 }
});
test('Brevo key missing does not claim or send',async()=>{
 const x=harness(),r=await requestSurveyNotification(req(),{...x,env:n=>n==='BREVO_REGISTRATION_API_KEY'?undefined:x.env(n)});
 assert.equal(r.status,503);assert.equal(x.calls.length,0);
});

test('staging Brevo simulation captures two emails without calling real Brevo',async()=>{
 const calls=[],deliveries=[];let prepared=false;
 const env=n=>n==='NOTIFICATION_TRANSPORT'?'staging_brevo_capture':n==='SUPABASE_URL'?'https://hexhtduvqzleoazusskh.supabase.co':config[n];
 const fetcher=async(url,init)=>{
  calls.push(url);
  if(url.endsWith('/auth/v1/user'))return json({id:uid,email:'professional@example.test',email_confirmed_at:'2026-11-03'});
  if(url.includes('/rest/v1/properties?'))return json([{id:pid,last_submitted_at:'2026-11-03T12:00:00Z'}]);
  if(url.endsWith('/rpc/claim_survey_notification'))return json({id:event,claimed:true,payload:{property_id:pid,client_email:'client@example.test',address:'Fixture House',surveyor_name:'Professional'}});
  if(url.endsWith('/rpc/prepare_survey_brevo_deliveries')){prepared=true;return json(true);}
  if(url.endsWith('/rpc/finish_survey_brevo_delivery')){const p=JSON.parse(init.body);deliveries.push(p);return json({recipient_kind:p.kind,state:p.accepted?'accepted':'uncertain'});}
  if(url.endsWith('/functions/v1/staging-notification-receiver')){
   assert(prepared);assert.equal(init.headers['X-Urbanfold-Notification-Type'],'survey');
   assert.equal(init.headers.Authorization,'Bearer service-fixture');
   const p=JSON.parse(init.body);
   assert.equal(p.test_mode,'staging_brevo_capture');
   assert(['admin','customer'].includes(p.recipient_kind));
   assert.equal(p.to.length,1);
   return json({captured:true,email_sent:false});
  }
  throw Error('unexpected call '+url);
 };
 const r=await requestSurveyNotification(req(),{env,fetcher});
 assert.equal(r.status,200);assert.equal(deliveries.length,2);
 assert(!calls.some(url=>url.includes('api.brevo.com')));
});
