// Staging-only deletion completion notification CAPTURE. Does not deliver any email.
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";
const STAGING="https://hexhtduvqzleoazusskh.supabase.co";
const ADMIN="b83f87d8-abf2-4800-beab-8279917804c7";
const ORIGIN="https://urbanfold.github.io";
const answer=(data:unknown,status=200)=>new Response(JSON.stringify(data),{status,headers:{"Content-Type":"application/json","Cache-Control":"no-store","Access-Control-Allow-Origin":ORIGIN,"Access-Control-Allow-Headers":"authorization,apikey,content-type","Access-Control-Allow-Methods":"POST,OPTIONS","Vary":"Origin"}});
Deno.serve(async req=>{
 if(Deno.env.get("SUPABASE_URL")!==STAGING)return answer({error:"Staging only"},503);
 if(req.headers.get("origin")!==ORIGIN)return answer({error:"Origin denied"},403);
 if(req.method==="OPTIONS")return answer({});
 if(req.method!=="POST")return answer({error:"POST required"},405);
 const token=/^Bearer (.+)$/.exec(req.headers.get("authorization")||"")?.[1];
 if(!token)return answer({error:"Sign in required"},401);
 const auth=createClient(STAGING,Deno.env.get("SUPABASE_ANON_KEY")!,{auth:{persistSession:false,autoRefreshToken:false}});
 const {data:{user},error:authError}=await auth.auth.getUser(token);
 if(authError||user?.id!==ADMIN||!user?.email_confirmed_at)return answer({error:"Admin access required"},403);
 let payload:any;
 try{payload=await req.json();}catch{return answer({error:"Bad JSON"},400);}
 const email=String(payload.email||"").trim().toLowerCase();
 if(!email.endsWith("@example.invalid")||email.length>254)return answer({error:"Dummy test address required"},403);
 const db=createClient(STAGING,Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!,{auth:{persistSession:false,autoRefreshToken:false}});
 const {data:records,error:lookupError}=await db.from("staging_account_deletion_audit").select("id,target_email,property_count,removed_storage_files,completed_at,status")
  .eq("target_email",email).eq("status","completed").order("completed_at",{ascending:false}).limit(1);
 if(lookupError)return answer({error:"Audit lookup unavailable"},503);
 const a=records?.[0];if(!a?.completed_at)return answer({error:"No completed deletion"},404);
 const date=new Date(a.completed_at).toLocaleString("en-GB",{timeZone:"Europe/London",dateStyle:"long",timeStyle:"short"})+" UK time";
 const customerSubject="Urbanfold Property Survey — Account closure confirmation";
 const customerBody=[
 "We confirm that your Urbanfold Property Survey account was closed following your request.",
 "",
 "Account: "+a.target_email,
 "Completed: "+date,
 "Surveys removed: "+a.property_count,
 "Stored survey photographs removed: "+a.removed_storage_files,
 "",
 "This confirmation relates to the Property Survey account and associated survey information. Separate business or financial records may be retained where lawfully required, as explained in our Privacy Policy.",
 "",
 "If you have questions, contact survey@urbanfold.uk.",
 "",
 "Urbanfold"
 ].join("\n");
 const businessSubject="Urbanfold Survey — Deletion completion record (STAGING TEST)";
 const businessBody=[
 "STAGING TEST ONLY — no emails delivered.",
 "Account: "+a.target_email,
 "Completed: "+date,
 "Survey records: "+a.property_count,
 "Stored photographs: "+a.removed_storage_files,
 "Status: Completed",
 "Environment: STAGING",
 "",
 "Review original request, identity verification and any retained financial data before closing a real deletion case."
 ].join("\n");
 const entries=[
 {deletion_audit_id:a.id,recipient_kind:"customer",recipient_email:a.target_email,subject:customerSubject,body_text:customerBody,status:"captured_not_sent"},
 {deletion_audit_id:a.id,recipient_kind:"business",recipient_email:"urbanfolduk@gmail.com",subject:businessSubject,body_text:businessBody,status:"captured_not_sent"}
 ];
 const {error:saveError}=await db.from("staging_deletion_email_outbox").upsert(entries,{onConflict:"deletion_audit_id,recipient_kind",ignoreDuplicates:true});
 if(saveError)return answer({error:"Notification capture failed"},503);
 const {data:captured,error:readError}=await db.from("staging_deletion_email_outbox")
  .select("recipient_kind,recipient_email,status,subject,created_at").eq("deletion_audit_id",a.id).order("recipient_kind");
 if(readError||!captured||captured.length!==2)return answer({error:"Capture acknowledgement incomplete"},503);
 return answer({status:"captured_not_sent",delivery_enabled:false,records:captured,detail:"Two drafts captured idempotently. No SMTP, Brevo, or Mailtrap delivery attempted."});
});
