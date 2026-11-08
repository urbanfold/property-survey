// DEVELOPMENT ONLY. Separate, server-side Brevo deliveries for survey submissions.
// Not wired into production gateway. No client may supply recipients or API keys.
export const SURVEY_ADMIN='urbanfolduk@gmail.com';
const EMAIL=/^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const UUID=/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const safe=value=>String(value??'').replace(/[\r\n\x00-\x1f\x7f]/g,' ').slice(0,300);
const validEmail=value=>typeof value==='string'&&value.length<=254&&EMAIL.test(value);
export function buildSurveyMessages({eventId,propertyId,address,surveyorName,clientEmail,senderEmail}){
 if(!UUID.test(eventId)||!UUID.test(propertyId)||!validEmail(clientEmail)||!validEmail(senderEmail))
  throw Error('Invalid trusted notification data.');
 const addr=safe(address),surveyor=safe(surveyorName),client=clientEmail.trim();
 const root={sender:{email:senderEmail,name:'Urbanfold'}};
 return [
  {kind:'admin',to:SURVEY_ADMIN,payload:{...root,to:[{email:SURVEY_ADMIN}],
   subject:'Urbanfold survey submitted',
   textContent:['A saved Urbanfold property survey has been submitted.',
    'Property: '+addr,'Surveyor: '+surveyor,'Customer email: '+client,
    'Survey reference: '+propertyId,
    'This is an administrative notification, not permission to use the customer address for marketing.'].join('\n'),
   headers:{idempotencyKey:eventId+'-admin'}}},
  {kind:'customer',to:client,payload:{...root,to:[{email:client}],
   subject:'Urbanfold — your survey has been received',
   textContent:['Thank you. Your Urbanfold property survey has been received.',
    'Property: '+addr,'Survey reference: '+propertyId,
    'We will review the information supplied and contact you about the next steps.',
    'If you did not submit or authorise this survey, please contact Urbanfold.'].join('\n'),
   headers:{idempotencyKey:eventId+'-customer'}}}
 ];
}
// The caller must first verify Auth, property ownership, saved-submission revision,
// and derive all payload fields server-side. Never auto-retry uncertain deliveries.
export async function sendSurveyBrevoEmails(record,{key,senderEmail,fetcher=fetch,timeoutMs=10000}={}){
 if(typeof key!=='string'||!key||!validEmail(senderEmail))throw Error('Brevo not configured.');
 const messages=buildSurveyMessages({...record,senderEmail});
 const results=[];
 for(const message of messages){
  try{
   const res=await fetcher('https://api.brevo.com/v3/smtp/email',{
    method:'POST',redirect:'error',
    headers:{'Content-Type':'application/json','api-key':key},
    body:JSON.stringify(message.payload),signal:AbortSignal.timeout(timeoutMs)});
   results.push({kind:message.kind,status:res.ok?'accepted':'uncertain'});
  }catch{
   // A timeout can mean email was delivered; do not automatically repeat.
   results.push({kind:message.kind,status:'uncertain'});
  }
 }
 return results;
}
