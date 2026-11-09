// Urbanfold second controlled Brevo diagnostic — NOT DEPLOYED.
// Deploy only after explicit approval for another two-email test.
// Uses an existing private, one-attempt ledger table. Never reuses the first test key.
// Returns only HTTP status and broad diagnostic category; never provider body or secrets.
const LIVE='https://arnzqizcycesukplmvuc.supabase.co';
const ORIGIN='https://urbanfold.github.io';
const ADMIN='urbanfolduk@gmail.com';
const CUSTOMER='tycohdesign1+urbanfoldauto@gmail.com';
const KEY='urbanfold-brevo-controlled-diagnostic-2026-11-09-v2';
const json=(body,status=200,origin=null)=>new Response(JSON.stringify(body),{status,headers:{
 'Content-Type':'application/json','Cache-Control':'no-store',
 ...(origin?{'Access-Control-Allow-Origin':origin,'Vary':'Origin',
 'Access-Control-Allow-Headers':'authorization,apikey,content-type,x-client-info',
 'Access-Control-Allow-Methods':'POST,OPTIONS'}:{})
}});
export function classifyBrevoStatus(code){
 if(code===201 || code===202 || code===200)return 'accepted_by_provider';
 if(code===400 || code===422)return 'request_validation_rejected';
 if(code===401 || code===403)return 'authentication_or_permission_rejected';
 if(code===429)return 'rate_limited';
 if(Number.isInteger(code)&&code>=400&&code<500)return 'client_request_rejected';
 if(Number.isInteger(code)&&code>=500)return 'provider_error';
 return 'unconfirmed';
}
export async function controlledDiagnostic(req,{env=(name)=>Deno.env.get(name),fetcher=fetch}={}){
 const origin=req.headers.get('origin');
 if(origin && origin!==ORIGIN)return json({error:'Origin not permitted'},403);
 if(req.method==='OPTIONS')return json({},200,ORIGIN);
 if(req.method!=='POST')return json({error:'Method not allowed'},405,origin);
 const base=env('SUPABASE_URL');
 if(base!==LIVE)return json({error:'Wrong project'},503,origin);
 const authHeader=req.headers.get('authorization')||'';
 if(!/^Bearer \S+$/.test(authHeader))return json({error:'Login required'},401,origin);
 const anon=env('SUPABASE_ANON_KEY'),service=env('SUPABASE_SERVICE_ROLE_KEY');
 const brevoKey=env('BREVO_REGISTRATION_API_KEY'),sender=env('REGISTRATION_EMAIL_FROM');
 if(!anon||!service||!brevoKey||!sender||!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(sender))
   return json({error:'Configuration unavailable'},503,origin);
 try{
  const auth=await fetcher(base+'/auth/v1/user',{headers:{apikey:anon,authorization:authHeader},signal:AbortSignal.timeout(10000)});
  if(!auth.ok)return json({error:'Login required'},401,origin);
  const user=await auth.json();
  if(user.email!==ADMIN||!user.email_confirmed_at)return json({error:'Administrator required'},403,origin);
  let body;try{const raw=await req.text();if(raw.length>160)throw Error();body=JSON.parse(raw);}catch{return json({error:'Invalid confirmation'},400,origin);}
  if(!body||Object.keys(body).length!==1||body.confirm!==KEY)return json({error:'Explicit confirmation required'},400,origin);
  const serverHeaders={apikey:service,Authorization:'Bearer '+service,'Content-Type':'application/json','Prefer':'return=representation'};
  const attempt=await fetcher(base+'/rest/v1/survey_brevo_controlled_tests',{method:'POST',headers:serverHeaders,
    body:JSON.stringify({test_key:KEY,state:'started'}),signal:AbortSignal.timeout(10000)});
  if(!attempt.ok)return json({error:'Test already attempted or reservation unavailable. Do not retry.'},409,origin);
  const reserved=await attempt.json().catch(()=>null);
  if(!Array.isArray(reserved)||reserved.length!==1)return json({error:'Reservation uncertain. Do not retry.'},503,origin);
  const messages=[
   {kind:'admin',email:ADMIN,subject:'Urbanfold Brevo diagnostic — admin',
    text:'CONTROLLED TEST ONLY. Dummy survey notification. No real customer or property.'},
   {kind:'customer',email:CUSTOMER,subject:'Urbanfold Brevo diagnostic — customer',
    text:'CONTROLLED TEST ONLY. Dummy survey acknowledgement. No real customer or property.'}
  ];
  const results=[];
  for(const [index,message] of messages.entries()){
   let http_status=null,category='network_or_timeout_uncertain';
   try{
    const response=await fetcher('https://api.brevo.com/v3/smtp/email',{method:'POST',redirect:'error',
     headers:{'Content-Type':'application/json','api-key':brevoKey},
     body:JSON.stringify({sender:{email:sender,name:'Urbanfold'},to:[{email:message.email}],
      subject:message.subject,textContent:message.text,
      headers:{idempotencyKey:index===0?'d11abcca-f5a1-4eed-9b0e-9aa1054e26a1':'d11abcca-f5a1-5eed-9b0e-9aa1054e26a1'}}),
     signal:AbortSignal.timeout(10000)});
    http_status=response.status;
    category=classifyBrevoStatus(response.status);
   }catch{/* Never retry uncertain delivery automatically. */}
   results.push({recipient:message.kind,http_status,category});
  }
  const accepted=results.every(x=>x.category==='accepted_by_provider');
  const finished=await fetcher(base+'/rest/v1/survey_brevo_controlled_tests?test_key=eq.'+encodeURIComponent(KEY),{
   method:'PATCH',headers:serverHeaders,body:JSON.stringify({state:accepted?'completed':'uncertain',
   completed_at:new Date().toISOString()}),signal:AbortSignal.timeout(10000)}).catch(()=>null);
  return json({test:'attempted_once',results,
   record_updated:Boolean(finished?.ok),
   note:'Brevo HTTP acceptance is not proof of inbox delivery. Check Brevo logs. Do not retry.'},accepted?200:202,origin);
 }catch{return json({error:'Outcome uncertain; do not retry'},503,origin);}
}
// Supabase Edge Functions load the entrypoint as a module, not a CLI main script.
Deno.serve(req=>controlledDiagnostic(req));
