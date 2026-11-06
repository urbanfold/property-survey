// Server-only worker. No browser can choose the admin recipient or enqueue itself.
const STAGING='https://hexhtduvqzleoazusskh.supabase.co';
const ADMIN='urbanfolduk@gmail.com';
const BUILD='urbanfold-registration-dispatch-1';
const reply=(data,status=200,headers={})=>new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json','Cache-Control':'no-store',...headers}});
export async function dispatchRegistrationNotifications(request,{env,fetcher=fetch,logger=entry=>console.info(JSON.stringify(entry))}){
 const base=env('SUPABASE_URL'),service=env('SUPABASE_SERVICE_ROLE_KEY'),dispatch=env('REGISTRATION_DISPATCH_SECRET');
 if(!service||!dispatch||dispatch.length<32||request.headers.get('authorization')!=='Bearer '+dispatch)return reply({error:'Server authorisation required.'},401);
 if(request.method!=='POST')return reply({error:'POST required.'},405);
 const mode=env('REGISTRATION_NOTIFICATION_TRANSPORT')||'disabled';
 if(!['staging_capture','brevo'].includes(mode))return reply({error:'Registration notifications are disabled.'},503);
 if(mode==='staging_capture'&&base!==STAGING)return reply({error:'Staging project required.'},503);
 if(base===STAGING&&mode!=='staging_capture')return reply({error:'Staging can capture only; email is forbidden.'},503);
 const sender=env('REGISTRATION_EMAIL_FROM'),key=env('BREVO_REGISTRATION_API_KEY');
 if(mode==='brevo'&&(!key||!sender||!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(sender)))return reply({error:'Registration email delivery is not configured.'},503);
 if(!base)return reply({error:'Database configuration missing.'},503);
 const diagnostic=event=>{try{logger({component:'registration_dispatcher',build:BUILD,event,mode});}catch{/* Logs must not change delivery state. */}};
 const headers={apikey:service,Authorization:'Bearer '+service,'Content-Type':'application/json'};
 try{
  const claim=await fetcher(base+'/rest/v1/rpc/claim_registration_notification',{method:'POST',headers,body:'{}',signal:AbortSignal.timeout(10000)});
  if(!claim.ok){diagnostic('claim_failed');return reply({error:'Registration queue unavailable.'},503);}
  const event=await claim.json();if(!event){diagnostic('idle');return reply({status:'idle'});}
  if(event.status==='rate_limited'){
   const seconds=Number.isInteger(event.retry_after_seconds)&&event.retry_after_seconds>=1&&event.retry_after_seconds<=3600?event.retry_after_seconds:60;
   diagnostic('rate_limited');return reply({status:'rate_limited'},429,{'Retry-After':String(seconds)});
  }
  if(!/^[0-9a-f-]{36}$/.test(event.id||'')||typeof event.claim_started_at!=='string'||!Number.isFinite(Date.parse(event.claim_started_at)))return reply({error:'Invalid registration event.'},503);
  diagnostic('claimed');
  const {claim_started_at,...registration}=event;
  const payload={...registration,notification_type:'registration_verified',recipient:ADMIN};
  let accepted=false;
  try{
   if(mode==='staging_capture'){
    const r=await fetcher(STAGING+'/functions/v1/staging-notification-receiver',{method:'POST',redirect:'error',
     headers:{...headers,'Idempotency-Key':event.id,'X-Urbanfold-Notification-Type':'registration_verified'},body:JSON.stringify(payload),signal:AbortSignal.timeout(10000)});
    accepted=r.ok;
   }else{
    const choice=event.newsletter_signup_choice===true?'Yes':event.newsletter_signup_choice===false?'No':'Not recorded';
    const text=['A user has verified their Urbanfold registration.',
     'Registration email: '+event.registration_email,'Registration date (UTC): '+event.registered_at,
     'Email verified (UTC): '+event.verified_at,'Newsletter checkbox at registration: '+choice,
     'An unticked checkbox is not newsletter consent.',
     'This service notification does not subscribe the recipient or user to marketing.',
     'The checkbox is a historical signup choice. Check current saved consent before sending marketing.'].join('\n');
    const r=await fetcher('https://api.brevo.com/v3/smtp/email',{method:'POST',redirect:'error',headers:{'Content-Type':'application/json','api-key':key},
     body:JSON.stringify({sender:{email:sender,name:'Urbanfold'},to:[{email:ADMIN}],subject:'New verified Urbanfold registration',textContent:text,
      headers:{'idempotencyKey':event.id}}),signal:AbortSignal.timeout(10000)});
    accepted=r.ok;
   }
  }catch{/* Sending may have happened: never blindly re-send an ambiguous event. */}
  const done=await fetcher(base+'/rest/v1/rpc/finish_registration_notification',{method:'POST',headers,
   body:JSON.stringify({event:event.id,accepted,claimed_at:claim_started_at}),signal:AbortSignal.timeout(10000)});
  let persisted;try{persisted=await done.json();}catch{/* Missing completion acknowledgement is uncertain. */}
  const confirmed=accepted&&done.ok&&persisted?.state==='accepted';
  diagnostic(confirmed?'accepted':'uncertain');
  return reply({status:confirmed?'accepted':'uncertain'},confirmed?200:202);
 }catch{diagnostic('worker_interrupted');return reply({error:'Registration dispatch could not be confirmed; reconcile before retrying.'},503);}
}
