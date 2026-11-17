// Urbanfold STAGING ONLY. Deliver one captured deletion notification to Mailtrap SANDBOX.
// Deliberately no production email endpoint, no retries of uncertain outcomes.
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
const STAGING_URL="https://hexhtduvqzleoazusskh.supabase.co";
const ADMIN_UID="b83f87d8-abf2-4800-beab-8279917804c7";
const ALLOWED_ORIGIN="https://urbanfold.github.io";
const MAILTRAP_INBOX_ID="5006771"; // Existing "My Sandbox" from user's Mailtrap testing URL.
const response=(data:unknown,status=200)=>new Response(JSON.stringify(data),{status,headers:{
 "Content-Type":"application/json; charset=utf-8","Cache-Control":"no-store",
 "Access-Control-Allow-Origin":ALLOWED_ORIGIN,
 "Access-Control-Allow-Headers":"authorization, apikey, content-type",
 "Access-Control-Allow-Methods":"POST, OPTIONS","Vary":"Origin"}});
Deno.serve(async request=>{
 if(Deno.env.get("SUPABASE_URL")!==STAGING_URL)return response({error:"Staging project required"},503);
 if(request.headers.get("origin")!==ALLOWED_ORIGIN)return response({error:"Origin not allowed"},403);
 if(request.method==="OPTIONS")return response({});
 if(request.method!=="POST")return response({error:"POST only"},405);
 const jwt=/^Bearer (.+)$/.exec(request.headers.get("authorization")||"")?.[1];
 if(!jwt)return response({error:"Sign in required"},401);
 const auth=createClient(STAGING_URL,Deno.env.get("SUPABASE_ANON_KEY")!,{auth:{persistSession:false,autoRefreshToken:false}});
 const {data:{user},error:authError}=await auth.auth.getUser(jwt);
 if(authError||!user||user.id!==ADMIN_UID||!user.email_confirmed_at)return response({error:"Administrator permission required"},403);
 let requestBody:any;
 try{requestBody=await request.json();}catch{return response({error:"Invalid request"},400);}
 const email=String(requestBody.email||"").trim().toLowerCase();
 const kind=String(requestBody.kind||"");
 if(!email.endsWith("@example.invalid")||email.length>254||!["customer","business"].includes(kind))
  return response({error:"Test account and recipient type required"},403);
 const token=Deno.env.get("MAILTRAP_SANDBOX_API_TOKEN");
 if(!token||token.length<20)return response({error:"Mailtrap sandbox API token has not been configured in staging."},503);
 const db=createClient(STAGING_URL,Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,{auth:{persistSession:false,autoRefreshToken:false}});
 const {data:audits,error:auditError}=await db.from("staging_account_deletion_audit")
  .select("id,status").eq("target_email",email).eq("status","completed")
  .order("completed_at",{ascending:false}).limit(1);
 if(auditError)return response({error:"Completed deletion lookup failed"},503);
 if(!audits?.length)return response({error:"Completed deletion not found"},404);
 const {data:mail,error:mailError}=await db.from("staging_deletion_email_outbox")
  .select("id,recipient_kind,recipient_email,subject,body_text,status")
  .eq("deletion_audit_id",audits[0].id).eq("recipient_kind",kind).maybeSingle();
 if(mailError||!mail||mail.status!=="captured_not_sent")return response({error:"Captured notification unavailable"},404);
 if(kind==="customer"&&mail.recipient_email.toLowerCase()!==email)return response({error:"Customer destination mismatch"},409);
 if(kind==="business"&&mail.recipient_email.toLowerCase()!=="urbanfolduk@gmail.com")return response({error:"Business destination mismatch"},409);
 // Sandbox API never delivers to external recipients: provider captures any To address in the sandbox inbox.
 // Durable unique reservation is made *before* calling Mailtrap, preventing duplicate sends.
 const {error:reserveError}=await db.from("staging_deletion_email_delivery_attempts")
  .insert({outbox_id:mail.id,status:"reserved"});
 if(reserveError){
  if(reserveError.code==="23505")return response({error:"This notification already has a delivery attempt. Inspect its status; no automatic retry."},409);
  return response({error:"Could not reserve delivery attempt"},503);
 }
 let status="uncertain",httpStatus:number|null=null;
 try{
  const sent=await fetch("https://sandbox.api.mailtrap.io/api/send/"+MAILTRAP_INBOX_ID,{
   method:"POST",redirect:"error",headers:{"Api-Token":token,"Content-Type":"application/json"},
   body:JSON.stringify({
    from:{email:"no-reply@urbanfold.uk",name:"Urbanfold Staging"},
    to:[{email:mail.recipient_email}],
    subject:mail.subject, text:mail.body_text
   }),signal:AbortSignal.timeout(10000)
  });
  httpStatus=sent.status;
  // Only HTTP 200 is considered accepted; all other statuses are uncertain/no retry.
  if(sent.status===200)status="accepted";
 }catch{/* Could have delivered before timeout. Do not retry. */}
 const {error:updateError}=await db.from("staging_deletion_email_delivery_attempts").update({
  status,response_status:httpStatus,confirmed_at:status==="accepted"?new Date().toISOString():null
 }).eq("outbox_id",mail.id).eq("status","reserved");
 if(updateError)return response({error:"Delivery outcome needs manual reconciliation. Never retry blindly."},202);
 if(status!=="accepted")return response({status:"uncertain",delivery_target:"mailtrap_sandbox",message:"Check Mailtrap before considering another test. No automatic retry."},202);
 return response({status:"accepted",recipient_kind:kind,delivery_target:"mailtrap_sandbox",email_delivered_to_real_recipient:false});
});
