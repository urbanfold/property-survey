import {test} from 'node:test';
import assert from 'node:assert/strict';
import {buildSurveyMessages,sendSurveyBrevoEmails} from '../supabase/functions/_shared/survey_brevo.mjs';
const record={eventId:'00000000-0000-4000-8000-000000000003',propertyId:'00000000-0000-4000-8000-000000000002',address:'1 Test Street',surveyorName:'Fixture Person',clientEmail:'client@example.test'};
test('admin and customer receive separate, appropriately scoped messages',()=>{
 const a=buildSurveyMessages({...record,senderEmail:'survey@urbanfold.uk'});
 assert.equal(a.length,2);
 assert.deepEqual(a.map(x=>x.to),['urbanfolduk@gmail.com','client@example.test']);
 assert.notEqual(a[0].payload.headers.idempotencyKey,a[1].payload.headers.idempotencyKey);
 assert.equal(a[0].payload.headers.idempotencyKey,record.eventId);
 assert.match(a[0].payload.headers.idempotencyKey,/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i);
 assert.match(a[1].payload.headers.idempotencyKey,/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i);
 assert(a[0].payload.textContent.includes('Customer email: client@example.test'));
 assert(!a[1].payload.textContent.includes('Customer email:'));
 for(const x of a){assert.equal(x.payload.sender.email,'survey@urbanfold.uk');assert.equal(x.payload.to.length,1);}
});
test('tampered or invalid addresses and event references fail closed',()=>{
 for(const bad of [{clientEmail:'wrong\n@evil.com'},{senderEmail:'bad'}, {eventId:'not-uuid'}, {propertyId:'not-uuid'}])
 assert.throws(()=>buildSurveyMessages({...record,senderEmail:'survey@urbanfold.uk',...bad}));
});
test('provider outcomes tracked independently; no automatic retry',async()=>{
 const calls=[];
 const fetcher=async(url,init)=>{calls.push({url,body:JSON.parse(init.body)});return new Response('',{status:calls.length===1?201:500});};
 const r=await sendSurveyBrevoEmails(record,{key:'fixture-key',senderEmail:'survey@urbanfold.uk',fetcher});
 assert.deepEqual(r,[{kind:'admin',status:'accepted'},{kind:'customer',status:'uncertain'}]);
 assert.equal(calls.length,2);assert(calls.every(x=>x.url==='https://api.brevo.com/v3/smtp/email'));
});
test('timeout is uncertain and does not retry',async()=>{
 let calls=0;const r=await sendSurveyBrevoEmails(record,{key:'fixture-key',senderEmail:'survey@urbanfold.uk',fetcher:async()=>{calls++;throw Error('timeout');}});
 assert.equal(calls,2);assert.deepEqual(r,[{kind:'admin',status:'uncertain'},{kind:'customer',status:'uncertain'}]);
});
test('missing credentials cannot send',async()=>{
 let calls=0;await assert.rejects(sendSurveyBrevoEmails(record,{key:'',senderEmail:'survey@urbanfold.uk',fetcher:async()=>{calls++;}}));
 assert.equal(calls,0);
});
