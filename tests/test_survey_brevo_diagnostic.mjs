import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';

const path=new URL('../supabase/functions/test-survey-brevo-diagnostic/index.ts',import.meta.url);
const source=(await readFile(path,'utf8')).replace(/^Deno\.serve\(req=>controlledDiagnostic\(req\)\);\s*$/m,'');
assert(!source.includes('Deno.serve('),'Standalone test must remove the runtime listener');
const {controlledDiagnostic,classifyBrevoStatus}=await import('data:text/javascript;base64,'+Buffer.from(source).toString('base64'));
const LIVE='https://arnzqizcycesukplmvuc.supabase.co';
const KEY='urbanfold-brevo-controlled-diagnostic-2026-11-09-v2';
const env=(name)=>({
 SUPABASE_URL:LIVE,SUPABASE_ANON_KEY:'fixture-public-key',SUPABASE_SERVICE_ROLE_KEY:'fixture-service-key',
 BREVO_REGISTRATION_API_KEY:'fixture-provider-key',REGISTRATION_EMAIL_FROM:'survey@urbanfold.uk'
})[name];
function request(body={confirm:KEY},token='fixture-session',origin='https://urbanfold.github.io'){
 return new Request('https://example.test/run',{method:'POST',headers:{origin,authorization:'Bearer '+token,'content-type':'application/json'},body:JSON.stringify(body)});
}
function mockFetch({userEmail='urbanfolduk@gmail.com',claimed=true,brevoStatuses=[201,422]}={}){
 const calls=[];
 const fetcher=async(url,opts)=>{
  calls.push({url,opts});
  if(url.endsWith('/auth/v1/user'))return new Response(JSON.stringify({email:userEmail,email_confirmed_at:'2026-11-06T12:00:00Z'}),{status:200});
  if(url.endsWith('/rest/v1/survey_brevo_controlled_tests'))return new Response(JSON.stringify(claimed?[{test_key:KEY}]:{message:'duplicate'}),{status:claimed?201:409});
  if(url.includes('/rest/v1/survey_brevo_controlled_tests?'))return new Response(null,{status:204});
  if(url==='https://api.brevo.com/v3/smtp/email')return new Response('',{status:brevoStatuses[calls.filter(c=>c.url===url).length-1]});
  throw Error('Unexpected URL '+url);
 };
 return {calls,fetcher};
}
test('classifies representative provider statuses without exposing bodies',()=>{
 assert.equal(classifyBrevoStatus(201),'accepted_by_provider');
 assert.equal(classifyBrevoStatus(422),'request_validation_rejected');
 assert.equal(classifyBrevoStatus(403),'authentication_or_permission_rejected');
 assert.equal(classifyBrevoStatus(429),'rate_limited');
 assert.equal(classifyBrevoStatus(503),'provider_error');
});
test('unverified visitor cannot call Brevo',async()=>{
 const m=mockFetch({userEmail:'someone@example.test'});
 const result=await controlledDiagnostic(request(),{env,fetcher:m.fetcher});
 assert.equal(result.status,403);
 assert.equal(m.calls.filter(c=>c.url.includes('api.brevo.com')).length,0);
});
test('disallowed origin is rejected before network access',async()=>{
 const m=mockFetch();
 const result=await controlledDiagnostic(request({confirm:KEY},'fixture','https://attacker.example'),{env,fetcher:m.fetcher});
 assert.equal(result.status,403);assert.equal(m.calls.length,0);
});
test('invalid confirmation cannot reserve or send',async()=>{
 const m=mockFetch();
 const result=await controlledDiagnostic(request({confirm:'incorrect'}),{env,fetcher:m.fetcher});
 assert.equal(result.status,400);assert.equal(m.calls.length,1);
});
test('duplicate reservation prevents any email',async()=>{
 const m=mockFetch({claimed:false});
 const result=await controlledDiagnostic(request(),{env,fetcher:m.fetcher});
 assert.equal(result.status,409);
 assert.equal(m.calls.filter(c=>c.url.includes('api.brevo.com')).length,0);
});
test('different outcomes are recorded with distinct valid UUID keys; no retries',async()=>{
 const m=mockFetch({brevoStatuses:[201,422]});
 const result=await controlledDiagnostic(request(),{env,fetcher:m.fetcher});
 assert.equal(result.status,202);
 const body=await result.json();
 assert.deepEqual(body.results.map(x=>x.category),['accepted_by_provider','request_validation_rejected']);
 const sends=m.calls.filter(c=>c.url==='https://api.brevo.com/v3/smtp/email');
 assert.equal(sends.length,2);
 const messages=sends.map(x=>JSON.parse(x.opts.body));
 assert.deepEqual(messages.map(x=>x.to[0].email),['urbanfolduk@gmail.com','tycohdesign1+urbanfoldauto@gmail.com']);
 const keys=messages.map(x=>x.headers.idempotencyKey);
 assert.notEqual(keys[0],keys[1]);
 for(const k of keys) assert.match(k,/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i);
 assert.equal(m.calls.filter(c=>c.url.includes('/survey_brevo_controlled_tests?')).length,1);
 assert(!JSON.stringify(body).includes('fixture-provider-key'));
});
