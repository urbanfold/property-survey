// Local only: every HTTP operation is replaced by an in-memory fetcher.
import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {performance} from 'node:perf_hooks';
import {stagingNotificationReceiver as shared} from '../supabase/functions/_shared/staging_receiver.mjs';
import {requestSurveyNotification as gateway} from '../supabase/functions/_shared/notifications.mjs';
const BASE='https://hexhtduvqzleoazusskh.supabase.co';
const BUILD='urbanfold-staging-receiver-diag-1';
const UID='00000000-0000-4000-8000-000000000001';
const PID='00000000-0000-4000-8000-000000000002';
const ID='00000000-0000-4000-8000-000000000003';
const payload={property_id:PID,client_email:'sensitive-recipient@example.invalid',address:'DUMMY SENSITIVE ADDRESS',surveyor_name:'SENSITIVE NAME',notes:'SENSITIVE PAYLOAD'};
const settings={SUPABASE_URL:BASE,SUPABASE_SERVICE_ROLE_KEY:'SENSITIVE-SERVER-KEY',SUPABASE_ANON_KEY:'SENSITIVE-ANON-KEY',APP_URL:'http://localhost:8794/',NOTIFICATION_TRANSPORT:'staging_capture',STAGING_RECEIVER_BEHAVIOUR:'accept'};
const json=(body,status=200)=>new Response(JSON.stringify(body),{status});
const req=(options={})=>new Request(BASE+'/functions/v1/staging-notification-receiver',{
 method:options.method||'POST',headers:{Authorization:'Bearer '+settings.SUPABASE_SERVICE_ROLE_KEY,'Idempotency-Key':ID,'X-Urbanfold-Notification-Type':'survey',...options.headers},
 ...(options.method==='GET'?{}:{body:JSON.stringify(options.payload||payload)})});
function fixture(overrides={}){
 const config={...settings,...overrides},logs=[],calls=[];
 return {config,logs,calls,env:n=>config[n],logger:entry=>logs.push(entry),fetcher:async(url,init)=>{
  assert.equal(url,BASE+'/rest/v1/rpc/capture_staging_notification');
  assert.equal(init.headers.Authorization,'Bearer '+settings.SUPABASE_SERVICE_ROLE_KEY);
  calls.push(JSON.parse(init.body));return json(null);
 }};
}
function safeLogs(logs){
 for(const log of logs){
  assert.deepEqual(Object.keys(log).sort(),['build','component','event','mode']);
  assert.equal(log.build,BUILD);assert.equal(log.component,'staging_notification_receiver');
  assert(['accept','reject','timeout_after_capture','missing','invalid'].includes(log.mode));
  assert(['mode_selected','capture_committed','timeout_wait_started','timeout_wait_finished'].includes(log.event));
 }
 const text=JSON.stringify(logs);
 for(const value of [...Object.values(payload),settings.SUPABASE_SERVICE_ROLE_KEY,settings.SUPABASE_ANON_KEY,ID,'SENSITIVE-INVALID-CONFIG\nvalue'])assert(!text.includes(value));
}
const generatedSource=await readFile(new URL('../supabase/dashboard/staging-notification-receiver.ts',import.meta.url),'utf8');
let registered;
const oldDeno=globalThis.Deno;
let generated;
try{
 globalThis.Deno={env:{get:()=>undefined},serve:handler=>{registered=handler;}};
 generated=await import('data:text/javascript;base64,'+Buffer.from(generatedSource).toString('base64'));
}finally{if(oldDeno===undefined)delete globalThis.Deno;else globalThis.Deno=oldDeno;}
const variants=[['shared',shared],['dashboard',generated.stagingNotificationReceiver]];

test('generated receiver matches shared source and preserves the exact dashboard entry point',async()=>{
 const source=await readFile(new URL('../supabase/functions/_shared/staging_receiver.mjs',import.meta.url),'utf8');
 assert(generatedSource.endsWith(source+'\nDeno.serve((request) => stagingNotificationReceiver(request, { env: (name) => Deno.env.get(name) }));\n'));
 assert.equal(typeof registered,'function');
});

for(const [name,handler] of variants){
 test(name+': missing/invalid mode fails closed without capture or sleep and never logs raw values',async()=>{
  for(const mode of [undefined,null,'',' ','ACCEPT','accept ','SENSITIVE-INVALID-CONFIG\nvalue']){
   const f=fixture({STAGING_RECEIVER_BEHAVIOUR:mode});let sleeps=0;
   const r=await handler(req(),{...f,sleep:async()=>sleeps++});
   assert.equal(r.status,503);assert.equal(f.calls.length,0);assert.equal(sleeps,0);
   assert.equal(f.logs.length,1);assert.equal(f.logs[0].mode,[undefined,null,''].includes(mode)?'missing':'invalid');safeLogs(f.logs);
   assert(!JSON.stringify(await r.json()).includes('SENSITIVE'));
  }
 });
 test(name+': project/auth/method guards execute before diagnostic logging',async()=>{
  for(const [overrides,request,status] of [
   [{SUPABASE_URL:'https://production.invalid'},req(),503],
   [{SUPABASE_SERVICE_ROLE_KEY:undefined},req(),401],
   [{},req({headers:{Authorization:'Bearer SENSITIVE-USER-TOKEN'}}),401],
   [{},req({headers:{Authorization:''}}),401],
   [{},req({method:'GET'}),405]
  ]){
   const f=fixture(overrides);assert.equal((await handler(request,f)).status,status);assert.equal(f.calls.length,0);assert.equal(f.logs.length,0);
  }
 });
 test(name+': explicit accept captures exact original payload once without sleeping',async()=>{
  const f=fixture();const r=await handler(req(),{...f,sleep:async()=>assert.fail('accept must not sleep')});
  assert.equal(r.status,200);assert.deepEqual(await r.json(),{captured:true,email_sent:false});
  assert.equal(f.calls.length,1);assert.deepEqual(f.calls[0],{kind:'survey',delivery_id:ID,payload});
  assert.deepEqual(f.logs.map(x=>x.event),['mode_selected','capture_committed']);safeLogs(f.logs);
 });
 test(name+': explicit reject does not capture or sleep',async()=>{
  const f=fixture({STAGING_RECEIVER_BEHAVIOUR:'reject'});
  assert.equal((await handler(req(),{...f,sleep:async()=>assert.fail('reject must not sleep')})).status,503);
  assert.equal(f.calls.length,0);assert.deepEqual(f.logs.map(x=>x.event),['mode_selected']);safeLogs(f.logs);
 });
 test(name+': mode is loaded on each invocation, not cached',async()=>{
  const f=fixture();assert.equal((await handler(req(),f)).status,200);
  f.config.STAGING_RECEIVER_BEHAVIOUR='reject';assert.equal((await handler(req(),f)).status,503);
  delete f.config.STAGING_RECEIVER_BEHAVIOUR;assert.equal((await handler(req(),f)).status,503);
  assert.equal(f.calls.length,1);safeLogs(f.logs);
 });
 test(name+': receiver SQL rejection or exception never records capture success or starts delay',async()=>{
  for(const fail of [async()=>json({},422),async()=>{throw Error('SENSITIVE-SERVER-KEY');}]){
   const f=fixture({STAGING_RECEIVER_BEHAVIOUR:'timeout_after_capture'});
   const r=await handler(req(),{...f,fetcher:fail,sleep:async()=>assert.fail('failed capture must not sleep')});
   assert([422,503].includes(r.status));assert.deepEqual(f.logs.map(x=>x.event),['mode_selected']);safeLogs(f.logs);
  }
 });
 test(name+': malformed capture metadata remains rejected before RPC',async()=>{
  for(const headers of [{'Idempotency-Key':'invalid'},{'X-Urbanfold-Notification-Type':'invalid'}]){
   const f=fixture();assert.equal((await handler(req({headers}),f)).status,400);assert.equal(f.calls.length,0);safeLogs(f.logs);
  }
 });
 test(name+': logging failure cannot break successful capture',async()=>{
  const f=fixture();const r=await handler(req(),{...f,logger:()=>{throw Error('log sink unavailable');}});
  assert.equal(r.status,200);assert.equal(f.calls.length,1);
 });
 test(name+': timeout waits only AFTER capture and cannot complete before delay resolves',async()=>{
  const f=fixture({STAGING_RECEIVER_BEHAVIOUR:'timeout_after_capture'});let release,entered;
  const waiting=new Promise(resolve=>entered=resolve);const gate=new Promise(resolve=>release=resolve);let finished=false;
  const pending=handler(req(),{...f,sleep:async ms=>{assert.equal(ms,12000);assert.equal(f.calls.length,1);entered();await gate;}}).then(r=>{finished=true;return r;});
  await waiting;assert.equal(finished,false);assert.deepEqual(f.logs.map(x=>x.event),['mode_selected','capture_committed','timeout_wait_started']);
  release();assert.equal((await pending).status,200);assert.equal(f.logs.at(-1).event,'timeout_wait_finished');safeLogs(f.logs);
 });
}

test('actual dashboard Deno entry point reads current env and uses safe default JSON logger',async()=>{
 const priorDeno=globalThis.Deno,priorFetch=globalThis.fetch,priorInfo=console.info;
 const f=fixture();const emitted=[];
 try{
  globalThis.Deno={env:{get:f.env}};globalThis.fetch=f.fetcher;console.info=text=>emitted.push(JSON.parse(text));
  assert.equal((await registered(req())).status,200);
  f.config.STAGING_RECEIVER_BEHAVIOUR='SENSITIVE-INVALID-CONFIG\nvalue';
  assert.equal((await registered(req())).status,503);assert.equal(f.calls.length,1);safeLogs(emitted);
 }finally{
  if(priorDeno===undefined)delete globalThis.Deno;else globalThis.Deno=priorDeno;
  globalThis.fetch=priorFetch;console.info=priorInfo;
 }
});

test('real 12-second receiver delay and real 10-second gateway timeout, both source variants, capture exactly once', {timeout:30000},async()=>{
 await Promise.all(variants.map(async([name,handler])=>{
  const f=fixture({STAGING_RECEIVER_BEHAVIOUR:'timeout_after_capture'});
  const saved={id:PID,last_submitted_at:'2026-11-06T12:00:00Z',notes:'DUMMY SAVED SURVEY'};
  const snapshot=JSON.stringify(saved);let state=null,claims=0;const pending=[];
  const fetcher=async(url,init)=>{
   if(url===BASE+'/auth/v1/user')return json({id:UID,email_confirmed_at:'2026-11-01'});
   if(url.startsWith(BASE+'/rest/v1/properties?'))return json([saved]);
   if(url.endsWith('/claim_survey_notification')){const claimed=state===null;if(claimed){state='sending';claims++;}return json({id:ID,claimed,state,payload});}
   if(url.endsWith('/finish_survey_notification')){state=JSON.parse(init.body).accepted?'accepted':'uncertain';return json(null);}
   if(url===BASE+'/functions/v1/staging-notification-receiver'){
    const started=performance.now();const actual=handler(new Request(url,init),f).then(r=>{
     const ms=performance.now()-started;assert(ms>=11900,name+' real delay too short');assert.equal(r.status,200);return ms;
    });pending.push(actual);
    return new Promise((resolve,reject)=>{
     const abort=()=>reject(init.signal.reason);
     init.signal.addEventListener('abort',abort,{once:true});
     if(init.signal.aborted)abort();
     actual.then(resolve,reject).finally(()=>init.signal.removeEventListener('abort',abort));
    });
   }
   assert.fail('Unexpected outbound route');
  };
  const request=()=>new Request(BASE+'/functions/v1/request-survey-notification',{method:'POST',headers:{Authorization:'Bearer SENSITIVE-USER-TOKEN'},body:JSON.stringify({property_id:PID})});
  const start=performance.now();const r=await gateway(request(),{env:f.env,fetcher});const gatewayMs=performance.now()-start;
  assert.equal(r.status,202);assert.equal((await r.json()).status,'uncertain');assert.equal(state,'uncertain');assert(gatewayMs>=9900);assert.equal(f.calls.length,1);
  // Restore the in-memory mode before retry: duplicate must bypass the receiver.
  f.config.STAGING_RECEIVER_BEHAVIOUR='accept';
  const retry=await gateway(request(),{env:f.env,fetcher});assert.equal(retry.status,202);assert.equal((await retry.json()).status,'uncertain');
  assert.equal(pending.length,1);assert.equal(claims,1);assert.equal(f.calls.length,1);assert.equal(JSON.stringify(saved),snapshot);
  const [receiverMs]=await Promise.all(pending);safeLogs(f.logs);assert.equal(f.logs.at(-1).event,'timeout_wait_finished');
  console.info(JSON.stringify({local_test:name,gateway_ms:Math.round(gatewayMs),receiver_ms:Math.round(receiverMs),captures:f.calls.length}));
 }));
});
