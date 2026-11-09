import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const source=readFileSync(new URL('../app.js',import.meta.url),'utf8');

test('browser notification code never exposes the old Zapier hook',()=>{
 assert(!source.includes('hooks.zapier.com'));
 assert(!source.includes('/hooks/catch/'));
});

test('authenticated Supabase notification uses only the property reference',()=>{
 const begin=source.indexOf('async function notifySurveySaved(');
 const end=source.indexOf('async function openSurveyReview(',begin);
 assert(begin>=0 && end>begin);
 const body=source.slice(begin,end);
 assert.match(body,/sb\.functions\.invoke\('request-survey-notification'/);
 assert.match(body,/body:\s*\{\s*property_id:\s*submittedPropertyId\s*\}/);
 assert(!/client_email|surveyor_name|address:|api-key|fetch\('https:\/\//.test(body));
 assert.match(body,/Your survey is saved, but the email request could not be confirmed/);
});

test('survey is persisted and marked submitted before notification request',()=>{
 const begin=source.indexOf('async function finishSurvey(');
 const end=source.indexOf('function dataURLtoFile(',begin);
 assert(begin>=0 && end>begin);
 const body=source.slice(begin,end);
 const persist=body.indexOf('await persistSurvey()');
 const mark=body.indexOf('last_submitted_at');
 const notify=body.indexOf('await notifySurveySaved(');
 assert(persist>=0 && mark>persist && notify>mark);
});
