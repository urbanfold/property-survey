import {test} from 'node:test';
import assert from 'node:assert/strict';
import {requestSurveyNotification} from '../supabase/functions/_shared/notifications.mjs';
const uid='00000000-0000-4000-8000-000000000001',pid='00000000-0000-4000-8000-000000000002',event='00000000-0000-4000-8000-000000000003';
const cfg={APP_URL:'https://urbanfold.github.io/property-survey/',SUPABASE_URL:'https://fixture.test',SUPABASE_ANON_KEY:'fixture-anon',SUPABASE_SERVICE_ROLE_KEY:'fixture-service',SURVEY_NOTIFICATION_WEBHOOK_URL:'https://hooks.zapier.com/hooks/catch/fixture/fixture/'};
const env=n=>cfg[n];const json=(data,status=200)=>new Response(JSON.stringify(data),{status});
const req=(body={property_id:pid},headers={})=>new Request('https://fixture.test/notification',{method:'POST',headers:{authorization:'Bearer fixture-user',origin:'https://urbanfold.github.io','content-type':'application/json',...headers},body:JSON.stringify(body)});
function fixture(options={}){
 const calls=[];let state;
 const fetcher=async(url,init)=>{
  calls.push([url,init]);
  if(url.endsWith('/auth/v1/user'))return json({id:uid,email:'professional@example.test',email_confirmed_at:options.unconfirmed?null:'2026-01-01'});
  if(url.includes('/rest/v1/properties?')){assert.equal(init.headers.authorization,'Bearer fixture-user');return json(options.foreign?[]:[{id:pid,last_submitted_at:options.unsubmitted?null:'2026-11-03T12:00:00Z'}]);}
  if(url.endsWith('/claim_survey_notification')){
   assert.equal(init.headers.Authorization,'Bearer fixture-service');assert.deepEqual(JSON.parse(init.body),{actor:uid,property:pid,revision:'2026-11-03T12:00:00Z'});
   if(options.rate)return json({message:'NOTIFICATION_RATE_LIMIT'},400);
   if(state)return json({id:event,state,claimed:false});
   state='sending';return json({id:event,state,claimed:true,payload:{property_id:pid,client_email:'client@example.test',address:'Fixture property',surveyor_name:'Fixture professional'}});
  }
  if(url.startsWith('https://hooks.zapier.com/')){
   assert(!init.headers.Authorization);assert(!init.headers.apikey);
   const p=JSON.parse(init.body);assert.equal(p.client_email,'client@example.test');assert.equal(p.property_id,pid);assert.match(p.submission_id,/^[0-9a-f]{64}$/);
   if(options.timeout)throw Error('simulated timeout');return json({accepted:true},options.reject?500:200);
  }
  if(url.endsWith('/finish_survey_notification')){
   if(options.finishFailure)return json({},500);
   state=JSON.parse(init.body).accepted?'accepted':'uncertain';return json(null);
  }
  throw Error('Unexpected request');
 };
 return {calls,fetcher,hooks:()=>calls.filter(([url])=>url.startsWith('https://hooks.zapier.com/')).length};
}
test('missing Auth/config and hostile origins never send a notification',async()=>{
 const f=fixture();assert.equal((await requestSurveyNotification(req({}, {authorization:''}),{env,fetcher:f.fetcher})).status,401);
 assert.equal((await requestSurveyNotification(req({}, {origin:'https://wrong.test'}),{env,fetcher:f.fetcher})).status,403);
 assert.equal((await requestSurveyNotification(req(),{env:()=>undefined,fetcher:f.fetcher})).status,503);assert.equal(f.calls.length,0);
});
test('confirmed account, RLS-visible property and submitted marker are required',async()=>{
 for(const [options,status] of [[{unconfirmed:true},401],[{foreign:true},403],[{unsubmitted:true},409]]){const f=fixture(options);assert.equal((await requestSurveyNotification(req(),{env,fetcher:f.fetcher})).status,status);assert.equal(f.hooks(),0);}
});
test('browser recipient/payload tampering and oversized bodies are rejected',async()=>{
 for(const body of [{property_id:pid,client_email:'forged@example.test'},{property_id:pid,actor_id:uid},{property_id:'invalid'},{property_id:[pid]},{property_id:pid,extra:'x'.repeat(5000)}]){const f=fixture();assert.equal((await requestSurveyNotification(req(body),{env,fetcher:f.fetcher})).status,400);assert.equal(f.hooks(),0);}
});
test('professional can notify saved client contact; duplicate requests reuse one durable event',async()=>{
 const f=fixture();for(let i=0;i<2;i++){const r=await requestSurveyNotification(req(),{env,fetcher:f.fetcher});assert.equal(r.status,200);assert.equal((await r.json()).status,'accepted');}assert.equal(f.hooks(),1);
});
test('timeouts/rejections remain uncertain and are not automatically resent',async()=>{
 for(const options of [{timeout:true},{reject:true},{finishFailure:true}]){const f=fixture(options);for(let i=0;i<2;i++){const r=await requestSurveyNotification(req(),{env,fetcher:f.fetcher});assert.equal(r.status,202);assert.equal((await r.json()).status,'uncertain');}assert.equal(f.hooks(),1);}
});
test('durable rate limit rejects without contacting the receiver',async()=>{
 const f=fixture({rate:true});assert.equal((await requestSurveyNotification(req(),{env,fetcher:f.fetcher})).status,429);assert.equal(f.hooks(),0);
});

test('generated dashboard gateway registers and fails closed without configured secrets',async()=>{
 const {readFile}=await import('node:fs/promises');const previous=globalThis.Deno;let registered;
 try{
  globalThis.Deno={env:{get:()=>undefined},serve:handler=>registered=handler};
  const source=await readFile(new URL('../supabase/dashboard/request-survey-notification.ts',import.meta.url),'utf8');
  await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
  assert.equal(typeof registered,'function');assert.equal((await registered(req())).status,503);
 }finally{if(previous===undefined)delete globalThis.Deno;else globalThis.Deno=previous;}
});

test('trusted browser OPTIONS preflight succeeds while delivery activation remains disabled',async()=>{
 const blockedEnv=name=>name==='SURVEY_NOTIFICATIONS_LIVE_ENABLED'?undefined:cfg[name];
 const preflight=new Request('https://fixture.test/notification',{method:'OPTIONS',headers:{origin:'https://urbanfold.github.io','access-control-request-method':'POST','access-control-request-headers':'authorization,apikey,content-type'}});
 const f=fixture();
 const result=await requestSurveyNotification(preflight,{env:blockedEnv,fetcher:f.fetcher});
 assert.equal(result.status,200);
 assert.equal(result.headers.get('access-control-allow-origin'),'https://urbanfold.github.io');
 assert.equal(f.calls.length,0);
 const wrong=new Request('https://fixture.test/notification',{method:'OPTIONS',headers:{origin:'https://untrusted.example'}});
 assert.equal((await requestSurveyNotification(wrong,{env:blockedEnv,fetcher:f.fetcher})).status,403);
 assert.equal(f.calls.length,0);
});
