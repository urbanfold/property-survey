// STAGING ONLY. This receiver stores dummy receipts. It has no email-delivery code.
const STAGING='https://hexhtduvqzleoazusskh.supabase.co';
const BUILD='urbanfold-staging-receiver-diag-1';
const reply=(data,status=200)=>new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json','Cache-Control':'no-store'}});
export async function stagingNotificationReceiver(request,{
 env,
 fetcher=fetch,
 sleep=ms=>new Promise(r=>setTimeout(r,ms)),
 logger=entry=>console.info(JSON.stringify(entry))
}){
 if(env('SUPABASE_URL')!==STAGING)return reply({error:'Staging project required.'},503);
 const key=env('SUPABASE_SERVICE_ROLE_KEY');
 if(!key||request.headers.get('authorization')!=='Bearer '+key)return reply({error:'Server authorisation required.'},401);
 if(request.method!=='POST')return reply({error:'POST required.'},405);
 const mode=env('STAGING_RECEIVER_BEHAVIOUR');
 const validMode=['accept','reject','timeout_after_capture'].includes(mode);
 const loggedMode=validMode?mode:
   (mode===undefined||mode===null||mode===''?'missing':'invalid');
 const diagnostic=event=>{
  try{
   logger({
    component:'staging_notification_receiver',
    build:BUILD,
    event,
    mode:loggedMode
   });
  }catch{
   // Diagnostic logging must not change notification behaviour.
  }
 };
 diagnostic('mode_selected');
 if(!validMode){
  return reply({error:'Capture mode must be explicitly configured.'},503);
 }
 if(mode==='reject')return reply({error:'Simulated receiver rejection; no delivery.'},503);
 try{
  const text=await request.text();if(new TextEncoder().encode(text).length>8192)return reply({error:'Too large.'},413);
  const payload=JSON.parse(text),kind=request.headers.get('X-Urbanfold-Notification-Type');
  const id=request.headers.get('Idempotency-Key');
  if(!['survey','registration_verified'].includes(kind)||!id||!/^[0-9a-f-]{36}$/.test(id))return reply({error:'Invalid capture request.'},400);
  const r=await fetcher(STAGING+'/rest/v1/rpc/capture_staging_notification',{method:'POST',headers:{apikey:key,Authorization:'Bearer '+key,'Content-Type':'application/json'},
   body:JSON.stringify({kind,delivery_id:id,payload}),signal:AbortSignal.timeout(10000)});
  if(!r.ok)return reply({error:'Dummy capture rejected.'},422);
  diagnostic('capture_committed');
  if(mode==='timeout_after_capture'){
   diagnostic('timeout_wait_started');
   await sleep(12000);
   diagnostic('timeout_wait_finished');
  }
  return reply({captured:true,email_sent:false});
 }catch{return reply({error:'Capture failed; no email delivery is implemented.'},503);}
}
